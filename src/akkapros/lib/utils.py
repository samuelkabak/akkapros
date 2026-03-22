#!/usr/bin/env python3
"""
Utility helpers shared across akkapros modules.

This file contains small, generic functions that are used in multiple
command‑line tools.  The goal is to avoid duplication and provide a
single place for commonly useful routines.  By default there are no
external dependencies beyond the Python standard library.

Currently defined:

* ``simple_safe_filename`` – convert arbitrary text into a filesystem-
  safe filename fragment.

The module also provides a small test harness for its routines; running
``utils.run_tests()`` should return ``True`` when everything is working.
"""

import argparse
import re
import unicodedata
from pathlib import Path
from typing import Any

from akkapros.lib.constants import (
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    SYL_SEPARATOR,
    SYL_WORD_ENDING,
    REGEX_TOKEN_BOL,
    REGEX_TOKEN_EOL,
    REGEX_TOKEN_EOF,
    REGEX_SENTINEL_SOL,
    REGEX_SENTINEL_EOL,
)

from akkapros import get_version_display

__version__ = "1.0.1"
__author__ = "Samuel KABAK"
__license__ = "MIT"


class RawDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Help formatter that keeps epilog formatting and always shows defaults."""


def print_startup_banner(program_title: str, version: str, args: argparse.Namespace) -> None:
    """Print a stable startup banner with effective runtime parameters."""
    print("=" * 78)
    print(program_title)
    print(f"Version: {version}")
    print("Running with:")

    for key in sorted(vars(args)):
        value: Any = getattr(args, key)
        print(f"  {key} = {value!r}")

    print("=" * 78)


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
        expected_kind: One of ``atf``, ``proc``, ``syl``, or ``tilde``.

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

    if expected_kind not in {"atf", "proc", "syl", "tilde"}:
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


def run_tests() -> bool:
    """Simple self-test suite.

    The tests here are deliberately minimal; they exist primarily to
    ensure that the behaviour of ``simple_safe_filename`` is stable.
    Calling ``run_tests`` from a higher‑level test harness (for example,
    ``parse.run_tests``) is sufficient for our purposes.
    """
    passed = 0
    failed = 0

    # basic conversion
    if simple_safe_filename('foo/bar baz?') == 'foo_bar_baz':
        passed += 1
    else:
        failed += 1

    # empty string returns placeholder
    if simple_safe_filename('') == 'unnamed':
        passed += 1
    else:
        failed += 1

    print(f"utils tests: {passed} passed, {failed} failed")
    return failed == 0
