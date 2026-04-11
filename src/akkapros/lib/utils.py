#!/usr/bin/env python3
"""
Utility helpers shared across akkapros modules.

This file contains small, generic functions that are used in multiple
command-line tools.  The goal is to avoid duplication and provide a
single place for commonly useful routines.  By default there are no
external dependencies beyond the Python standard library.

Currently defined:

* ``simple_safe_filename`` – convert arbitrary text into a filesystem-
  safe filename fragment.
* ``compile_contextual_regex`` / ``contextualize_for_regex`` /
  ``strip_regex_sentinels`` – helpers for the ``[:bol:]``/``[:eol:]``
  pseudo-token system used in punctuation matching.
* ``build_numeric_currency_pattern`` – compiled numeric/currency regex.
* ``FormatValidationError`` / ``validate_intermediate_format`` – validate
  pipeline input files before processing.
* ``akkadian_likelihood`` – compute a 0–1 likelihood that a text is
  Akkadian transliteration; returns ``(score, details)``.
* ``classify_text`` – return a human-readable classification string
  based on the likelihood score.

The module also provides a small test harness; running
``utils.run_tests()`` should return ``True`` when everything is working.
"""

import argparse
import logging
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from akkapros.lib.frontmatter import FORMAT_VERSIONS, read_text_file

from akkapros.lib.constants import (
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    AKKADIAN_DISTINCTIVE,
    NON_AKKADIAN_CHARS,
    AKKADIAN_ENCLITICS,
    FUNCTION_WORDS,
    SYL_SEPARATOR,
    SYL_WORD_ENDING,
    REGEX_TOKEN_BOL,
    REGEX_TOKEN_EOL,
    REGEX_TOKEN_EOF,
    REGEX_SENTINEL_SOL,
    REGEX_SENTINEL_EOL,
)

from akkapros import get_version_display

__author__ = "Samuel KABAK"
__license__ = "MIT"


# ============================================================================
# AKKADIAN LIKELIHOOD SCORING CONSTANTS
# (implementation details; not part of the public API)
# ============================================================================

# Weights for the four scoring components (must sum to 1.0).
_AKKASCORE_WEIGHTS: dict = {
    'distinctive':     0.40,   # Distinctive Akkadian diacritics (š, ṭ, ḫ …)
    'vowel_consonant': 0.20,   # Phonetic V/C balance
    'function_words':  0.30,   # Function-word / enclitic frequency
    'length':          0.10,   # Length confidence bonus
}

# Ideal and acceptable vowel/consonant ratio ranges.
_AKKASCORE_VOWEL_IDEAL       = (0.3, 0.8)
_AKKASCORE_VOWEL_ACCEPTABLE  = (0.2, 1.0)

# Ideal and acceptable function-word ratio ranges.
_AKKASCORE_FW_IDEAL          = (0.25, 0.6)
_AKKASCORE_FW_ACCEPTABLE     = (0.15, 0.7)

_AKKASCORE_DISTINCTIVE_MUL   = 3.0    # Scale factor for distinctive-char ratio
_AKKASCORE_FW_BONUS_DENOM    = 15.0   # Denominator for raw function-word count bonus
_AKKASCORE_FW_BONUS_MAX      = 0.2    # Cap on function-word count bonus
_AKKASCORE_LEN_BONUS_DENOM   = 500.0  # Denominator for length bonus
_AKKASCORE_LEN_BONUS_MAX     = 0.2    # Cap on length bonus
_AKKASCORE_MIN_LENGTH        = 10     # Min chars before giving full analysis
_AKKASCORE_BASE_SHORT        = 0.5    # Base score for texts shorter than min_length


class _MaxLevelFilter(logging.Filter):
    """Allow records up to and including ``max_level``."""

    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


class _MinLevelFilter(logging.Filter):
    """Allow records at or above ``min_level``."""

    def __init__(self, min_level: int) -> None:
        super().__init__()
        self.min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno >= self.min_level


LOG_RECORD_FORMAT = '%(levelname)s:%(name)s:%(message)s'


def _logger_has_effective_handler(logger: logging.Logger) -> bool:
    """Return True when *logger* or one of its parents will emit records."""
    current: logging.Logger | None = logger
    while current is not None:
        if current.handlers:
            return True
        if not current.propagate:
            return False
        current = current.parent
    return False


def get_logger_with_fallback(name: str) -> logging.Logger:
    """Return a logger that can emit records even outside CLI setup paths."""
    logger = logging.getLogger(name)
    if _logger_has_effective_handler(logger):
        return logger

    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_RECORD_FORMAT))
    logger.addHandler(handler)
    return logger


def format_selftest_label(index: int, total: int, label: str) -> str:
    """Return a zero-padded self-test label such as ``01: Tokenizer``."""
    width = max(2, len(str(total)))
    return f'{index:0{width}d}: {_normalize_selftest_text(label)}'


def _normalize_selftest_text(text: str) -> str:
    """Normalize self-test fields so one record always stays on one line."""
    return text.strip().replace('\r', '\\r').replace('\n', '\\n')


def _format_selftest_detail(detail: str) -> str:
    """Normalize self-test detail payloads for single-line logging."""
    return _normalize_selftest_text(detail)


def log_selftest_result(
    logger: logging.Logger,
    passed: bool,
    category: str,
    label: str,
    details: list[str] | None = None,
) -> None:
    """Emit one structured self-test record through the shared logger."""
    status = 'PASS' if passed else 'FAIL'
    safe_category = _normalize_selftest_text(category)
    safe_label = _normalize_selftest_text(label)
    message = f'Test: {status} [{safe_category}] {safe_label}'
    if details:
        message = ' | '.join([message, *(_format_selftest_detail(detail) for detail in details)])
    logger.log(logging.INFO if passed else logging.ERROR, message)


def log_selftest_summary(logger: logging.Logger, category: str, passed: int, total: int) -> None:
    """Emit one structured summary record for a self-test category."""
    log_selftest_result(
        logger,
        passed == total,
        category,
        f'Summary {passed}/{total}',
    )


def run_simple_selftest_suite(
    logger: logging.Logger,
    category: str,
    suites: list[tuple[str, Any]],
) -> bool:
    """Run a sequence of ``(label, callable)`` tests with structured logging."""
    total = len(suites)
    passed = 0

    for index, (label, callback) in enumerate(suites, start=1):
        case_label = format_selftest_label(index, total, label)
        try:
            ok = bool(callback())
            details = None
        except Exception as exc:
            ok = False
            details = [f'error={exc!r}']

        if ok:
            passed += 1
        log_selftest_result(logger, ok, category, case_label, details=details)

    log_selftest_summary(logger, category, passed, total)
    return passed == total


def format_path_for_logging(path_like: str | Path) -> str:
    """Return a path display limited to the leaf and one parent segment."""
    path_str = str(path_like)
    if not path_str:
        return path_str

    normalized = path_str.replace('/', '\\')
    drive_match = re.match(r'^[A-Za-z]:\\', normalized)
    is_unc = normalized.startswith('\\\\')

    if '\\' not in normalized:
        return normalized

    parts = [part for part in normalized.split('\\') if part]

    if drive_match:
        anchor = normalized[:3]
        if len(parts) <= 1:
            return normalized
        if len(parts) == 2:
            return f'{anchor}{parts[-1]}'
        return f'...\\{parts[-2]}\\{parts[-1]}'

    if is_unc:
        if len(parts) <= 2:
            return normalized
        if len(parts) == 3:
            return f'\\\\{parts[0]}\\{parts[1]}\\{parts[2]}'
        return f'...\\{parts[-2]}\\{parts[-1]}'

    if len(parts) == 1:
        return normalized
    return f'...\\{parts[-2]}\\{parts[-1]}'


def _format_log_value(value: Any) -> Any:
    """Normalize path-like startup values to the safe logging display form."""
    if isinstance(value, Path):
        return format_path_for_logging(value)
    if isinstance(value, str):
        if '\\' in value or '/' in value or re.match(r'^[A-Za-z]:$', value):
            return format_path_for_logging(value)
        return value
    if isinstance(value, list):
        return [_format_log_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_format_log_value(item) for item in value)
    if isinstance(value, dict):
        return {key: _format_log_value(item) for key, item in value.items()}
    return value

# Pre-compiled regex patterns used by akkadian_likelihood.
_AKKASCORE_CLEAN_RE  = re.compile(r'[^\w\-]')
_AKKASCORE_WORD_RE   = re.compile(r'[a-zāēīūâêîûṭṣšḥḫʿʾ\-]+')
_AKKASCORE_STRIP_RE  = re.compile(r'[^a-zāēīūâêîûṭṣšḥḫʿʾ]')

# Public classification thresholds.
AKKASCORE_THRESHOLDS: dict = {
    'highly_likely': 0.75,
    'likely':        0.50,
    'possibly':      0.25,
}

# Minimum file length (stripped chars) before the likelihood guard in
# validate_intermediate_format fires; prevents false negatives on stub files.
_VALIDATE_PROC_MIN_CHARS   = 50
_VALIDATE_PROC_THRESHOLD   = 0.25


class RawDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Help formatter that keeps epilog formatting and always shows defaults."""


def print_startup_banner(program_title: str, version: str, args: argparse.Namespace) -> None:
    """Backward-compatible wrapper that now routes through logging."""
    log_startup_banner(_build_bootstrap_logger(), program_title, version, args)


def log_startup_banner(
    logger: logging.Logger,
    program_title: str,
    version: str,
    args: argparse.Namespace,
) -> None:
    """Emit structured startup facts through the shared logger."""
    logger.info('Program: %s', program_title)
    logger.info('Version: %s', version)

    for key in sorted(vars(args)):
        if key.startswith('_'):
            continue
        value: Any = _format_log_value(getattr(args, key))
        logger.info('Arg %s=%r', key, value)


def add_standard_logging_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the shared CLI logging controls mandated across runtime CLIs."""
    from akkapros.lib.helpmsg import help_for

    parser.add_argument(
        '--quiet',
        action='store_true',
        help=help_for('logging.quiet'),
    )
    parser.add_argument(
        '--no-console',
        action='store_true',
        help=help_for('logging.no_console'),
    )
    parser.add_argument(
        '--log',
        help=help_for('logging.log'),
    )
    parser.add_argument(
        '--log-append',
        action='store_true',
        help=help_for('logging.log_append'),
    )


def _build_bootstrap_logger() -> logging.Logger:
    """Return a minimal logger for configuration-time failures."""
    logger = logging.getLogger('akkapros.bootstrap')
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(LOG_RECORD_FORMAT))
    logger.addHandler(handler)
    return logger


def setup_cli_logging(args: argparse.Namespace, logger_name: str) -> logging.Logger:
    """Configure the shared ``akkapros`` logger and return a child logger."""
    if getattr(args, 'log_append', False) and not getattr(args, 'log', None):
        bootstrap = _build_bootstrap_logger()
        bootstrap.error('--log-append requires --log')
        raise SystemExit(2)

    shared_logger = logging.getLogger('akkapros')
    shared_logger.handlers.clear()
    shared_logger.setLevel(logging.DEBUG)
    shared_logger.propagate = False

    console_enabled = not getattr(args, 'no_console', False)
    console_level = logging.WARNING if getattr(args, 'quiet', False) else logging.INFO

    if console_enabled:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(console_level)
        stdout_handler.addFilter(_MaxLevelFilter(logging.INFO))
        stdout_handler.setFormatter(logging.Formatter(LOG_RECORD_FORMAT))
        shared_logger.addHandler(stdout_handler)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.WARNING)
        stderr_handler.addFilter(_MinLevelFilter(logging.WARNING))
        stderr_handler.setFormatter(logging.Formatter(LOG_RECORD_FORMAT))
        shared_logger.addHandler(stderr_handler)

    log_path = getattr(args, 'log', None)
    if log_path:
        file_handler = logging.FileHandler(
            log_path,
            mode='a' if getattr(args, 'log_append', False) else 'w',
            encoding='utf-8',
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_RECORD_FORMAT))
        shared_logger.addHandler(file_handler)

    return logging.getLogger(logger_name)


def add_standard_version_argument(parser: argparse.ArgumentParser, tool_name: str) -> None:
    """Add a standardized multi-line --version/-v option to a CLI parser."""
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=get_version_display(tool_name),
    )


def simple_safe_filename(text: str) -> str:
    """Return a minimal filename-safe version of ``text``.

    The function performs the same sequence of operations that were
    previously duplicated across several CLI modules:

    1. Normalize to ``NFKD`` and strip accent marks.
    2. Replace characters that are illegal in filenames (``<>:"/\\|?*``)
       or whitespace with underscores.
    3. Remove any other non-word characters, keeping ``-`` and ``.``.
    4. Collapse consecutive underscores, then strip leading or trailing
       ``._-`` characters.
    5. Guarantee a non-empty result by returning ``"unnamed"`` if the
       cleaned string is empty.

    >>> simple_safe_filename('foo/bar baz?')
    'foo_bar_baz'
    >>> simple_safe_filename('')
    'unnamed'
    """
    if not text:
        import argparse
        return "unnamed"

    # Remove accents
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')

    # Replace invalid chars and spaces with underscores
    text = re.sub(r'[<>:"/\\|?*\s]', '_', text)

    # Keep only safe characters
    text = re.sub(r'[^\w\-\.]', '_', text)

    # Clean up
    text = re.sub(r'_+', '_', text)
    text = text.strip('._-')

    return text or "unnamed"


def compile_contextual_regex(pattern: str, option_name: str, item_index: int) -> re.Pattern:
    """Compile regex supporting line/file pseudo-tokens.

    Supported pseudo-tokens in ``pattern``:
    - ``[:bol:]`` line start
    - ``[:eol:]`` line end
    - ``[:eof:]`` accepted as internal alias of line end
    """
    prepared = (
        pattern
        .replace(REGEX_TOKEN_BOL, REGEX_SENTINEL_SOL)
        .replace(REGEX_TOKEN_EOL, REGEX_SENTINEL_EOL)
        .replace(REGEX_TOKEN_EOF, REGEX_SENTINEL_EOL)
    )

    try:
        return re.compile(prepared)
    except re.error as exc:
        raise ValueError(
            f"Invalid regex for {option_name} (item {item_index}): {pattern!r}. Error: {exc}"
        ) from exc


def contextualize_for_regex(text: str, *, at_sol: bool, at_eol: bool, at_eof: bool) -> str:
    """Attach boundary sentinels around text for contextual regex matching."""
    prefix = REGEX_SENTINEL_SOL if at_sol else ''
    # EOF is normalized to EOL semantics for punctuation matching.
    suffix = REGEX_SENTINEL_EOL if (at_eof or at_eol) else ''
    return f"{prefix}{text}{suffix}"


def strip_regex_sentinels(text: str) -> str:
    """Remove contextual boundary sentinels from text."""
    return (
        text
        .replace(REGEX_SENTINEL_SOL, '')
        .replace(REGEX_SENTINEL_EOL, '')
    )


def build_numeric_currency_pattern(
    *,
    number_pattern: str,
    currency_symbols: str,
) -> re.Pattern:
    """Return compiled numeric/currency suite regex used by punctuation parsing."""
    try:
        re.compile(number_pattern)
    except re.error as exc:
        raise ValueError(f"Invalid number regex {number_pattern!r}. Error: {exc}") from exc

    core = rf"(?:{number_pattern})"
    pattern = (
        rf"(?:[{re.escape(currency_symbols)}]\s*{core}"
        rf"|{core}\s*[{re.escape(currency_symbols)}]"
        rf"|{core})"
    )
    return re.compile(pattern)


class FormatValidationError(ValueError):
    """Structured input-format validation error with source and line details."""

    def __init__(
        self,
        *,
        source: str,
        reason: str,
        line_number: int | None = None,
        line_text: str | None = None,
        # Public classification thresholds.
    ) -> None:
        self.source = source
        self.reason = reason
        self.line_number = line_number
        self.line_text = line_text

        if line_number is None:
            msg = f"{source}: {reason}"
        else:
            excerpt = ""
            if line_text is not None:
                excerpt = f" | line content: {line_text!r}"
            msg = f"{source}: line {line_number}: {reason}{excerpt}"
        super().__init__(msg)


def validate_intermediate_format(file_path: str | Path, expected_kind: str) -> None:
    """Validate obvious corruption in pipeline input files.

    Args:
        file_path: Input path.
        expected_kind: One of ``atf``, ``proc``, ``syl``, ``tilde``, or ``phone``.

    Raises:
        FormatValidationError: When obvious corruption/partial content is found.
        ValueError: For unknown kind values.
    """

    def fail(reason: str, line_number: int | None = None, line_text: str | None = None) -> None:
        raise FormatValidationError(
            source=str(path),
            reason=reason,
            line_number=line_number,
            line_text=line_text,
        )

    if expected_kind not in {"atf", "proc", "syl", "tilde", "phone"}:
        raise ValueError(f"Unknown expected_kind: {expected_kind!r}")

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        fail("file not found")

    raw = path.read_bytes()
    if not raw:
        fail("file is empty")
    if b"\x00" in raw:
        fail("file contains NUL bytes (likely binary/corrupted)")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"file is not valid UTF-8 ({exc})")

    try:
        frontmatter, text = read_text_file(path)
    except ValueError as exc:
        fail(f"invalid front matter ({exc})")

    if frontmatter is not None and expected_kind in {"proc", "syl", "tilde", "phone"}:
        file_info = frontmatter.get("file", {})
        declared_format = file_info.get("format")
        expected_format = expected_kind
        if declared_format != expected_format:
            fail(f"front matter format mismatch: expected {expected_format!r}, got {declared_format!r}")
        declared_version = file_info.get("version")
        if declared_version != FORMAT_VERSIONS.get(expected_format):
            fail(
                "front matter version mismatch: "
                f"expected {FORMAT_VERSIONS.get(expected_format)!r}, got {declared_version!r}"
            )

    # Accept files without a trailing newline by normalizing to the canonical
    # in-memory shape used by downstream line-based processing.
    if not text.endswith("\n"):
        text = text + "\n"

    if not text.strip():
        fail("file contains only whitespace")

    lines = text.splitlines()
    if not lines:
        fail("file has no readable lines")

    # Fast sanity check for unprintable control characters.
    for idx, line in enumerate(lines, start=1):
        for ch in line:
            if ord(ch) < 32 and ch not in ('\t',):

                fail("contains unprintable control character", idx, line)

    non_empty = [(idx, ln) for idx, ln in enumerate(lines, start=1) if ln.strip()]
    if not non_empty:
        fail("file has no non-empty content lines")

    akkad_letters = (
        set(AKKADIAN_VOWELS)
        | set(AKKADIAN_CONSONANTS)
        | {c.upper() for c in AKKADIAN_VOWELS}
        | {c.upper() for c in AKKADIAN_CONSONANTS}
    )
    has_akkadian_letter = any(ch in akkad_letters for ch in text)

    if not has_akkadian_letter:
        fail("file does not contain Akkadian letters")

    if expected_kind == "atf":
        if not any("%n" in ln for _, ln in non_empty):
            idx, ln = non_empty[0]
            fail("missing %n Akkadian content lines", idx, ln)

    elif expected_kind == "proc":
        if any("%n" in ln or ln.startswith("#tr.en:") for _, ln in non_empty):
            idx, ln = next((i, l) for i, l in non_empty if "%n" in l or l.startswith("#tr.en:"))
            fail("appears to be raw ATF content, expected cleaned *_proc.txt text", idx, ln)
        # Secondary sanity check: the file should look like Akkadian transliteration.
        # Guard is only applied when text is long enough (>= _VALIDATE_PROC_MIN_CHARS)
        # to avoid false negatives on stub or fragment files.
        if len(text.strip()) >= _VALIDATE_PROC_MIN_CHARS:
            score, _ = akkadian_likelihood(text, min_length=10)
            if score < _VALIDATE_PROC_THRESHOLD:
                fail(
                    f"text does not appear to be Akkadian transliteration "
                    f"(likelihood score: {score:.2f}, threshold: {_VALIDATE_PROC_THRESHOLD:.2f})"
                )

    elif expected_kind == "syl":
        # Syllabified stage must contain explicit end-of-word markers.
        has_word_endings = any(SYL_WORD_ENDING in ln for _, ln in non_empty)
        if not has_word_endings:
            idx, ln = non_empty[0]
            fail("missing SYL_WORD_ENDING markers for *_syl.txt input", idx, ln)

    elif expected_kind == "tilde":
        # Tilde input can be a short plain sequence; only guard against
        # accidentally passing a syllabified file.
        if any(SYL_WORD_ENDING in ln for _, ln in non_empty):
            idx, ln = next((i, l) for i, l in non_empty if SYL_WORD_ENDING in l)
            fail("appears to be syllabified *_syl.txt content, expected *_tilde.txt", idx, ln)
    elif expected_kind == "phone":
        saw_phone_row = False
        for idx, ln in non_empty:
            head, sep, _tail = ln.partition(':')
            if not sep:
                fail("invalid phone-row content: missing ':' separator", idx, ln)
            parts = head.split('-')
            if len(parts) != 10:
                fail("invalid phone-row content: expected 10 head fields", idx, ln)
            if parts[1] not in {'C', 'V', 'S'}:
                fail("invalid phone-row content: unknown category field", idx, ln)
            if not re.fullmatch(r'\d{4}', parts[8]):
                fail("invalid phone-row content: duration must be four digits", idx, ln)
            if not re.fullmatch(r'[HLMRFPV][0-9][CLE]', parts[9]):
                fail("invalid phone-row content: intonation must be a canonical three-character token", idx, ln)
            saw_phone_row = True
        if not saw_phone_row:
            fail("file has no valid phone rows")


# ============================================================================
# AKKADIAN LIKELIHOOD FUNCTIONS
# ============================================================================


def akkadian_likelihood(text: str, min_length: int = _AKKASCORE_MIN_LENGTH) -> tuple:
    """Compute the likelihood that *text* is Akkadian transliteration.

    Uses four components weighted according to ``_AKKASCORE_WEIGHTS``:

    1. **Distinctive-character score** – ratio of diacritically Akkadian
       characters (š, ṭ, ṣ, ḥ, ḫ, ʿ, ʾ) to total phonetic characters, scaled by
       ``_AKKASCORE_DISTINCTIVE_MUL`` and capped at 1.
    2. **Vowel/Consonant-ratio score** – based on whether the V/C ratio
       falls in the ideal (0.3–0.8) or acceptable (0.2–1.0) range.
    3. **Function-word score** – fraction of recognised Akkadian function
       words and enclitic-bearing tokens among all word tokens.
    4. **Length-confidence bonus** – small bonus for longer texts (more
       reliable estimates).

    Args:
        text:       The text to analyse (any pipeline stage, but most
                    meaningful for clean ``*_proc.txt`` content).
        min_length: Minimum character count (after stripping punctuation)
                    for a full analysis.  Texts below this length return a
                    low-confidence score of ``_AKKASCORE_BASE_SHORT * (len/min)``.

    Returns:
        ``(score, details)`` where *score* is in ``[0.0, 1.0]`` and
        *details* is a :class:`dict` with diagnostic fields:
        ``length``, ``has_non_akkadian``, ``distinctive_count``,
        ``vowel_count``, ``consonant_count``, ``function_word_matches``,
        ``total_words``, ``scores``, ``function_word_ratio``,
        ``text_sample``.

    Note:
        A score of 0.0 is only returned when a character from
        ``NON_AKKADIAN_CHARS`` (``'o'``, ``'f'``, ``'x'``, ``'v'``,
        ``'j'``, ``'c'``) is found; such characters cannot appear in
        standard Akkadian transliteration.  See also
        :data:`AKKASCORE_THRESHOLDS` for classification cut-offs.
    """
    text = text.strip().lower()
    clean_text = _AKKASCORE_CLEAN_RE.sub('', text)

    details: dict = {
        'length': len(clean_text),
        'has_non_akkadian': False,
        'distinctive_count': 0,
        'vowel_count': 0,
        'consonant_count': 0,
        'function_word_matches': 0.0,
        'total_words': 0,
        'total_function_word_candidates': 0.0,
        'text_sample': text[:100],
    }

    # 1. Characters that make Akkadian identification impossible.
    for char in clean_text:
        if char in NON_AKKADIAN_CHARS:
            details['has_non_akkadian'] = True
            return 0.0, details

    # 2. Character-category counts.
    for char in clean_text:
        if char in AKKADIAN_VOWELS:
            details['vowel_count'] += 1
        elif char in AKKADIAN_CONSONANTS:
            details['consonant_count'] += 1
        if char in AKKADIAN_DISTINCTIVE:
            details['distinctive_count'] += 1

    total_chars = details['vowel_count'] + details['consonant_count']

    # 3. Short-text early return: low confidence, but non-zero.
    if details['length'] < min_length:
        details['confidence_penalty'] = details['length'] / min_length
        return _AKKASCORE_BASE_SHORT * details['confidence_penalty'], details

    # 4. Tokenise words; check for function words and enclitics.
    words = _AKKASCORE_WORD_RE.findall(text)
    details['total_words'] = len(words)

    for word in words:
        clean_word = _AKKASCORE_STRIP_RE.sub('', word)
        if clean_word in FUNCTION_WORDS:
            details['function_word_matches'] += 1
            details['total_function_word_candidates'] += 1
        else:
            for enclitic in AKKADIAN_ENCLITICS:
                if clean_word.endswith(enclitic) and len(clean_word) > len(enclitic):
                    details['function_word_matches'] += 0.5
                    details['total_function_word_candidates'] += 0.5
                    break

    # 5. Compute per-component scores.
    if total_chars > 0:
        distinctive_score = min(1.0, (details['distinctive_count'] / total_chars)
                                     * _AKKASCORE_DISTINCTIVE_MUL)
    else:
        distinctive_score = 0.0

    if details['consonant_count'] > 0:
        v_ratio = details['vowel_count'] / details['consonant_count']
        if _AKKASCORE_VOWEL_IDEAL[0] <= v_ratio <= _AKKASCORE_VOWEL_IDEAL[1]:
            vowel_score = 1.0
        elif _AKKASCORE_VOWEL_ACCEPTABLE[0] <= v_ratio <= _AKKASCORE_VOWEL_ACCEPTABLE[1]:
            vowel_score = 0.7
        else:
            vowel_score = 0.3
    else:
        vowel_score = 0.7

    if details['total_words'] > 0:
        fw_ratio = details['function_word_matches'] / details['total_words']
        if _AKKASCORE_FW_IDEAL[0] <= fw_ratio <= _AKKASCORE_FW_IDEAL[1]:
            function_score = 1.0
        elif _AKKASCORE_FW_ACCEPTABLE[0] <= fw_ratio <= _AKKASCORE_FW_ACCEPTABLE[1]:
            function_score = 0.7
        else:
            function_score = 0.3
        bonus = min(_AKKASCORE_FW_BONUS_MAX,
                    details['function_word_matches'] / _AKKASCORE_FW_BONUS_DENOM)
        function_score = min(1.0, function_score + bonus)
    else:
        function_score = 0.0

    length_bonus = min(_AKKASCORE_LEN_BONUS_MAX,
                       details['length'] / _AKKASCORE_LEN_BONUS_DENOM)

    # 6. Weighted combination, clamped to [0, 1].
    w = _AKKASCORE_WEIGHTS
    score = (
        w['distinctive']     * distinctive_score
        + w['vowel_consonant'] * vowel_score
        + w['function_words']  * function_score
        + w['length']          * length_bonus
    )
    score = min(1.0, max(0.0, score))

    details['scores'] = {
        'distinctive':     distinctive_score,
        'vowel_consonant': vowel_score,
        'function_words':  function_score,
        'length_bonus':    length_bonus,
    }
    details['function_word_ratio'] = (
        details['function_word_matches'] / max(1, details['total_words'])
    )

    return score, details


def classify_text(text: str) -> str:
    """Return a human-readable Akkadian classification string for *text*.

    Uses :func:`akkadian_likelihood` with default parameters and maps
    the score to one of five labels (matching :data:`AKKASCORE_THRESHOLDS`):

    - score == 0.0  → ``"NOT AKKADIAN (contains forbidden characters)"``
    - score ≥ 0.75  → ``"HIGHLY LIKELY AKKADIAN (xx.xx%)"``
    - score ≥ 0.50  → ``"LIKELY AKKADIAN (xx.xx%)"``
    - score ≥ 0.25  → ``"POSSIBLY AKKADIAN (xx.xx%)"``
    - score <  0.25  → ``"UNLIKELY AKKADIAN (xx.xx%)"``
    """
    score, _ = akkadian_likelihood(text)
    if score == 0.0:
        return "NOT AKKADIAN (contains forbidden characters)"
    elif score >= AKKASCORE_THRESHOLDS['highly_likely']:
        return f"HIGHLY LIKELY AKKADIAN ({score:.2%})"
    elif score >= AKKASCORE_THRESHOLDS['likely']:
        return f"LIKELY AKKADIAN ({score:.2%})"
    elif score >= AKKASCORE_THRESHOLDS['possibly']:
        return f"POSSIBLY AKKADIAN ({score:.2%})"
    else:
        return f"UNLIKELY AKKADIAN ({score:.2%})"


def run_tests() -> bool:
    """Self-test suite for :mod:`akkapros.lib.utils`.

    Tests ``simple_safe_filename`` and basic smoke-tests for
    ``akkadian_likelihood``.
    """
    logger = get_logger_with_fallback('akkapros.lib.utils')

    proc_with_frontmatter = (
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"atfparse\"\n"
        "file:\n"
        "  id: \"abc\"\n"
        "  title: \"demo\"\n"
        "  format: \"proc\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-27\"\n"
        "metadata:\n"
        "  input_file_id: \"src\"\n"
        "  options:\n"
        "  data:\n"
        "---\n\n"
        "šar gi-mir dadmē\n"
    )

    def _validate_frontmatter_case() -> bool:
        tmp_frontmatter = Path('.tmp_utils_frontmatter_proc.txt')
        tmp_frontmatter.write_text(proc_with_frontmatter, encoding='utf-8')
        try:
            try:
                validate_intermediate_format(tmp_frontmatter, 'proc')
                return True
            except FormatValidationError:
                return False
        finally:
            if tmp_frontmatter.exists():
                tmp_frontmatter.unlink()

    suites = [
        ('Safe filename basic', lambda: simple_safe_filename('foo/bar baz?') == 'foo_bar_baz'),
        ('Safe filename empty', lambda: simple_safe_filename('') == 'unnamed'),
        (
            'Akkadian likelihood threshold',
            lambda: akkadian_likelihood('īpūš-ma pâšu izakkar ana rubê marūtuk')[0] >= 0.40,
        ),
        (
            'Akkadian forbidden chars',
            lambda: not akkadian_likelihood('īpūš-ma pâšu izakkar ana rubê marūtuk')[1]['has_non_akkadian'],
        ),
        (
            'English score zero',
            lambda: akkadian_likelihood(
                'This is clearly English text with no Akkadian characters whatsoever'
            )[0] == 0.0,
        ),
        (
            'English flags non-Akkadian',
            lambda: akkadian_likelihood(
                'This is clearly English text with no Akkadian characters whatsoever'
            )[1]['has_non_akkadian'],
        ),
        (
            'Function words matched',
            lambda: akkadian_likelihood('ana šamê ellī-ma ana igīgī anaddin ûrta')[1]['function_word_matches'] >= 2,
        ),
        (
            'Short text confidence',
            lambda: 0.0 < akkadian_likelihood('a', min_length=10)[0] <= 0.5,
        ),
        (
            'Short text penalty',
            lambda: 'confidence_penalty' in akkadian_likelihood('a', min_length=10)[1],
        ),
        ('Proc frontmatter accepted', _validate_frontmatter_case),
        (
            'Classify text non-empty',
            lambda: bool(classify_text('īpūš-ma pâšu izakkar ana rubê marūtuk')),
        ),
    ]

    return run_simple_selftest_suite(logger, 'Utils', suites)
