#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Syllabification (Library)
Version: 1.2.0

This module contains the core syllabification logic extracted from the
command-line tool.  It exposes a simple API that can be used programmatically
or invoked by the CLI wrapper in ``akkapros.cli.syllabifier``.

The library functions mirror the behaviour of the original script, including
comprehensive self-tests.  The command-line interface (in the ``cli``
package) is responsible only for file I/O and argument parsing.

Part of the Akkadian Prosody project (akkapros)
https://github.com/samuelkabak/akkapros

MIT License
Copyright (c) 2026 Samuel KABAK
"""

import re
import sys
from typing import List, Optional, Tuple

__version__ = "1.2.0"
__author__ = "Samuel KABAK"
__license__ = "MIT"
__project__ = "Akkadian Prosody"
__repo__ = "akkapros"

# ---------------------------------------------------------------------------
# Internal state and helper sets
# ---------------------------------------------------------------------------
# The character sets below may be updated dynamically by
# ``text_preprocess_boundaries`` when the user supplies extra vowels or
# consonants via command-line options.  They mirror the globals that existed
# in the original script.

# shared constants
from akkapros.lib.constants import (
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    GLOTTAL,
    SYL_WORD_ENDING,
    SYL_SEPARATOR,
    HYPHEN,
    WORD_LINKER,
    OPEN_ESCAPE,
    CLOSE_ESCAPE,
    OPEN_PRESERVE,
    CLOSE_PRESERVE,
    OPEN_PRESERVE_CHAR,
    CLOSE_PRESERVE_CHAR,
    TAG_PRESERVE_RE,
    DIPH_SEPARATOR
)


FOREIGN_VOWELS = set()
FOREIGN_CONSONANTS = set()
EXTRA_VOWELS = set()
EXTRA_CONSONANTS = set()

ALL_VOWELS = AKKADIAN_VOWELS | FOREIGN_VOWELS | EXTRA_VOWELS 
ALL_CONSONANTS = AKKADIAN_CONSONANTS | FOREIGN_CONSONANTS | EXTRA_CONSONANTS
ALL_AKKADIAN = ALL_VOWELS | ALL_CONSONANTS

# ---------------------------------------------------------------------------
# Character classification utilities
# ---------------------------------------------------------------------------

def is_vowel(c: str) -> bool:
    """Return ``True`` if the character is currently recognised as a vowel."""
    return c in ALL_VOWELS


def is_consonant(c: str) -> bool:
    """Return ``True`` if the character is currently recognised as a consonant."""
    return c in ALL_CONSONANTS


def is_akkadian_letter(c: str) -> bool:
    """Return ``True`` if the character belongs to the Akkadian inventory."""
    return c in ALL_AKKADIAN


def is_hyphen(c: str, before: str = "", after: str = "") -> bool:
    """Determine whether ``c`` is a hyphen/two-part word separator.

    Hyphens attached to letters are treated as syllable boundaries, whereas
    a dash surrounded by spaces counts as punctuation.  We rely on the
    neighbouring characters to make this distinction.
    """
    if c != HYPHEN:
        return False
    before_is_letter = before and is_akkadian_letter(before)
    after_is_letter = after and is_akkadian_letter(after)
    return bool(before_is_letter and after_is_letter)


def is_linker(c: str, before: str = "", after: str = "") -> bool:
    """Determine whether ``c`` is a word-linker connecting two words (+)."""
    if c != WORD_LINKER:
        return False
    before_is_letter = before and is_akkadian_letter(before)
    after_is_letter = after and is_akkadian_letter(after)
    return bool(before_is_letter and after_is_letter)


def is_word_char(c: str, extra: str = '', before: str = '', after: str = '') -> bool:
    """True if character can form part of an Akkadian word token."""
    if is_akkadian_letter(c):
        return True
    if c == HYPHEN:
        return is_hyphen(c, before, after)
    if c == WORD_LINKER:
        return is_linker(c, before, after)
    return False

# ---------------------------------------------------------------------------
# Preprocessing helpers
# ---------------------------------------------------------------------------

ESCAPE_TAG_RE = re.compile(rf'^{TAG_PRESERVE_RE}$')


def parse_escape_at(text: str, start: int) -> Optional[Tuple[str, int]]:
    """Parse one escape token at ``start`` and return ``(token, next_index)``.

    Supported forms:
    - ``{{text}}``
    - ``{tag{text}}`` where ``tag`` matches ``[0-9a-z_]{1,16}``

    Nested escapes are intentionally unsupported.
    """
    n = len(text)
    if start >= n:
        return None

    if text.startswith(OPEN_PRESERVE, start):
        close_idx = text.find(CLOSE_PRESERVE, start + len(OPEN_PRESERVE))
        if close_idx == -1:
            return None
        payload = text[start + len(OPEN_PRESERVE):close_idx]
        if OPEN_PRESERVE_CHAR in payload or CLOSE_PRESERVE_CHAR in payload:
            return None
        payload = payload.strip()
        return f"{OPEN_PRESERVE}{payload}{CLOSE_PRESERVE}", close_idx + len(CLOSE_PRESERVE)

    if text[start] != OPEN_PRESERVE_CHAR:
        return None

    tag_end = text.find(OPEN_PRESERVE_CHAR, start + 1)
    if tag_end == -1:
        return None

    tag = text[start + 1:tag_end]
    if not ESCAPE_TAG_RE.fullmatch(tag):
        return None

    close_idx = text.find(CLOSE_PRESERVE, tag_end + 1)
    if close_idx == -1:
        return None

    payload = text[tag_end + 1:close_idx]
    if OPEN_PRESERVE_CHAR in payload or CLOSE_PRESERVE_CHAR in payload:
        return None
    payload = payload.strip()
    return (
        f"{OPEN_PRESERVE_CHAR}{tag}{OPEN_PRESERVE_CHAR}{payload}{CLOSE_PRESERVE}",
        close_idx + len(CLOSE_PRESERVE),
    )


def split_by_escape_segments(text: str) -> List[Tuple[bool, str]]:
    """Split text into ``(is_escape, segment)`` tuples.

    This intentionally supports only ``{{...}}`` and ``{tag{...}}`` forms.
    """
    segments: List[Tuple[bool, str]] = []
    i = 0
    last = 0
    n = len(text)

    while i < n:
        parsed = parse_escape_at(text, i)
        if parsed is None:
            i += 1
            continue

        token, next_i = parsed
        if last < i:
            segments.append((False, text[last:i]))
        segments.append((True, token))
        i = next_i
        last = i

    if last < n:
        segments.append((False, text[last:]))

    if not segments:
        return [(False, text)]
    return segments


def split_by_brackets_level3(text):
    """Deprecated compatibility alias.

    CR-005 removes nested square-bracket parsing; this helper now delegates
    to the simple escape splitter and returns only segment text.
    """
    return [seg for _, seg in split_by_escape_segments(text)]


def preprocess_diphthongs(text: str) -> str:
    """Insert DIPH_SEPARATOR between adjacent vowels (diphthong expansion).

    Warnings are printed to ``stderr`` when diphthongs are detected to help
    users spot them in their input data.  The function is idempotent in the
    sense that once a DIPH_SEPARATOR has been inserted it will no longer match
    the regex pattern.
    """

    segments = split_by_escape_segments(text)
    if len(segments) > 1 or (segments and segments[0][0]):
        prep = []
        for is_escape, part in segments:
            if is_escape:
                prep.append(part)
            else:
                prep.append(preprocess_diphthongs(part))
        return ''.join(prep)

    vowels_pattern = f'([{re.escape("".join(ALL_VOWELS))}])([{re.escape("".join(ALL_VOWELS))}])'
    matches = list(re.finditer(vowels_pattern, text))
    if matches:
        print("\n⚠️  DIPHTHONG WARNINGS:", file=sys.stderr)
        for match in matches:
            diphthong = match.group(0)
            pos = match.start()
            start = max(0, pos - 10)
            end = min(len(text), pos + 10)
            context = text[start:end]
            print(f"   Diphthong '{diphthong}' at position {pos}: ...{context}...", file=sys.stderr)
            print(f"     → Inserting DIPH_SEPARATOR: {diphthong[0]}{DIPH_SEPARATOR}{diphthong[1]}", file=sys.stderr)
        text = re.sub(vowels_pattern, r'\1' + DIPH_SEPARATOR + r'\2', text)
        print(f"   Total diphthongs processed: {len(matches)}", file=sys.stderr)
        print(file=sys.stderr)
    return text


def text_preprocess_boundaries(
    text: str,
    warnings: List[str],
    extra_vowels: str = '',
    extra_consonants: str = '',
    preserve_lines: bool = False,
) -> str:
    """Preprocess text prior to syllabification.

    The function performs the following steps:

    1. Update the global character sets with ``extra_vowels``/``extra_consonants``.
    2. Expand diphthongs by inserting ``DIPH_SEPARATOR`` between adjacent vowels.
    3. Trim trailing whitespace on each line (preserve leading spaces).
    4. Merge words split across lines by hyphenation.
    5. Normalize line breaks by default: single newline -> space, 2+ newlines -> one newline.
    6. Preserve line breaks exactly when ``preserve_lines=True``.
    7. Warn about tabs occurring between Akkadian words.
    """
    if not isinstance(warnings, list):
        raise TypeError("Expected a list in text_preprocess_boundaries")

    global ALL_VOWELS, ALL_CONSONANTS, ALL_AKKADIAN
    ALL_VOWELS = AKKADIAN_VOWELS | set(extra_vowels)
    ALL_CONSONANTS = AKKADIAN_CONSONANTS | set(extra_consonants)
    ALL_AKKADIAN = ALL_VOWELS | ALL_CONSONANTS

    text = preprocess_diphthongs(text)
    lines = text.split('\n')
    processed_lines = []
    tab_warning_issued = False
    i = 0

    markdown_header_re = re.compile(r'^\s{0,3}#{1,6}\s+\S')
    markdown_list_re = re.compile(r'^\s{0,3}(?:[*+-]|\d+[.)])\s+\S')
    markdown_blockquote_re = re.compile(r'^\s{0,3}>\s?\S?')
    markdown_hr_re = re.compile(r'^\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})\s*$')
    markdown_table_sep_re = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$')

    def _is_markdown_fence(line: str) -> bool:
        stripped = line.lstrip()
        return stripped.startswith('```') or stripped.startswith('~~~')

    def _is_markdown_table_row(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if markdown_table_sep_re.match(stripped):
            return True
        return stripped.startswith('|') and stripped.endswith('|') and stripped.count('|') >= 2

    def _is_markdown_structural_line(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        return bool(
            markdown_header_re.match(stripped)
            or markdown_list_re.match(stripped)
            or markdown_blockquote_re.match(stripped)
            or markdown_hr_re.match(stripped)
            or _is_markdown_table_row(stripped)
        )

    def _is_markdown_boundary(prev_text: str, curr_text: str, in_fence: bool) -> bool:
        if in_fence:
            return True
        if _is_markdown_fence(prev_text) or _is_markdown_fence(curr_text):
            return True
        if _is_markdown_structural_line(prev_text) or _is_markdown_structural_line(curr_text):
            return True
        return False

    def _line_has_attached_trailing_connector(raw_line: str, connector: str) -> bool:
        """Return True when a line ends with an attached '-' or '+'."""
        stripped = raw_line.rstrip()
        if not stripped.endswith(connector):
            return False
        if len(stripped) < 2:
            return False
        return is_akkadian_letter(stripped[-2])

    while i < len(lines):
        line = lines[i].rstrip('\n')
        original_line = line
        line = line.rstrip()
        if _line_has_attached_trailing_connector(original_line, HYPHEN) and i + 1 < len(lines):
            next_line = lines[i + 1]
            next_line_stripped = next_line.lstrip()
            if next_line_stripped and is_word_char(next_line_stripped[0]):
                base = original_line.rstrip().rstrip(HYPHEN)
                merged = base + HYPHEN + next_line_stripped
                warnings.append(f"Hyphen split across lines merged: '{original_line.rstrip()}' + '{next_line}' → '{merged}'")
                processed_lines.append(merged)
                rest = next_line[len(next_line_stripped):]
                processed_lines.append(rest or '')
                i += 2
                continue
        if _line_has_attached_trailing_connector(original_line, WORD_LINKER) and i + 1 < len(lines):
            next_line = lines[i + 1]
            next_line_stripped = next_line.lstrip()
            if next_line_stripped and is_word_char(next_line_stripped[0]):
                base = original_line.rstrip().rstrip(WORD_LINKER)
                merged = base + WORD_LINKER + next_line_stripped
                warnings.append(f"Word linker split across lines merged: '{original_line.rstrip()}' + '{next_line}' → '{merged}'")
                processed_lines.append(merged)
                rest = next_line[len(next_line_stripped):]
                processed_lines.append(rest or '')
                i += 2
                continue
        processed_lines.append(line)
        i += 1
    if '\t' in text and not tab_warning_issued:
        warnings.append("Tabs detected: tabs between Akkadian words are treated as spaces and eliminated")

    if preserve_lines:
        return '\n'.join(processed_lines)

    # Default behavior treats a single newline as visual line-wrap continuation,
    # while 2+ newlines keep a paragraph boundary.
    nonblank_entries = [(idx, line.strip()) for idx, line in enumerate(processed_lines) if line.strip()]
    if not nonblank_entries:
        return ''

    normalized = nonblank_entries[0][1]
    prev_idx, prev_text = nonblank_entries[0]
    in_fence = _is_markdown_fence(prev_text)
    for curr_idx, curr_text in nonblank_entries[1:]:
        same_paragraph_gap = (curr_idx - prev_idx) == 1
        markdown_boundary = _is_markdown_boundary(prev_text, curr_text, in_fence)
        separator = ' ' if (same_paragraph_gap and not markdown_boundary) else '\n'
        normalized += separator + curr_text
        if _is_markdown_fence(curr_text):
            in_fence = not in_fence
        prev_idx, prev_text = curr_idx, curr_text
    return normalized

# ---------------------------------------------------------------------------
# Syllabification logic
# ---------------------------------------------------------------------------

def syllabify_word(word: str, merge_hyphen: bool = False) -> str:
    """Return the syllabified representation of a single word."""
    if HYPHEN not in word and WORD_LINKER not in word:
        segs = [c for c in word if is_akkadian_letter(c)]
        if not segs:
            return word
        if not any(is_vowel(c) for c in segs):
            return word
        syllables = []
        i, n = 0, len(segs)
        first = True
        while i < n:
            if first and is_vowel(segs[i]):
                first = False
                syl = [segs[i]]
                i += 1
                if i < n and not is_vowel(segs[i]) and (i+1 >= n or not is_vowel(segs[i+1])):
                    syl.append(segs[i]); i += 1
                syllables.append(''.join(syl))
                continue
            first = False
            onset = []
            while i < n and not is_vowel(segs[i]):
                onset.append(segs[i]); i += 1
            if i < n and is_vowel(segs[i]):
                syl = onset + [segs[i]]
                i += 1
                if i < n and not is_vowel(segs[i]):
                    if i+1 >= n or not is_vowel(segs[i+1]):
                        syl.append(segs[i]); i += 1
                syllables.append(''.join(syl))
        return SYL_SEPARATOR.join(syllables)

    parts = []
    separators = []
    current = []
    for c in word:
        if c in (HYPHEN, WORD_LINKER):
            parts.append(''.join(current))
            separators.append(c)
            current = []
        else:
            current.append(c)
    parts.append(''.join(current))

    result_parts = [syllabify_word(p, merge_hyphen) for p in parts]
    result = [result_parts[0]]
    for idx, sep in enumerate(separators):
        out_sep = SYL_SEPARATOR if (sep == HYPHEN and merge_hyphen) else sep
        result.append(out_sep)
        result.append(result_parts[idx + 1])
    return ''.join(result)


def tokenize_line(line: str, extra: str = '') -> List[tuple]:
    """Split a line of text into word/punctuation tokens."""
    tokens = []

    i = 0
    n = len(line)
    while i < n:
        parsed_escape = parse_escape_at(line, i)
        if parsed_escape is not None:
            token, next_i = parsed_escape
            tokens.append(('escape', token))
            i = next_i
            continue

        before = line[i-1] if i > 0 else ''
        after = line[i+1] if i+1 < n else ''
        if is_word_char(line[i], extra, before, after):
            start = i
            while i < n:
                before_inner = line[i-1] if i > start else ''
                after_inner = line[i+1] if i+1 < n else ''
                if not is_word_char(line[i], extra, before_inner, after_inner):
                    break
                i += 1
            word = line[start:i]
            tokens.append(('word', word))
        else:
            start = i
            while i < n:
                if i > start and parse_escape_at(line, i) is not None:
                    break
                before_inner = line[i-1] if i > start else ''
                after_inner = line[i+1] if i+1 < n else ''
                if is_word_char(line[i], extra, before_inner, after_inner):
                    break
                i += 1
            punct = line[start:i]
            if punct.isspace():
                prev_is_word = tokens and tokens[-1][0] in ('word', 'escape')
                next_is_word = i < n and is_word_char(line[i], extra)
                next_is_escape = i < n and parse_escape_at(line, i) is not None
                if prev_is_word and (next_is_word or next_is_escape):
                    continue
            if punct:
                tokens.append(('punct', punct))
    return tokens


def syllabify_text(
    text: str,
    extra_vowels: str = '',
    extra_consonants: str = '',
    merge_hyphen: bool = False,
    preserve_lines: bool = False,
) -> str:
    """Return the fully syllabified version of ``text``.

    The returned string uses the global ``SYL_WORD_ENDING`` marker at the end
    of every word and preserves line breaks.
    """
    warnings: List[str] = []
    text = text_preprocess_boundaries(
        text,
        warnings,
        extra_vowels,
        extra_consonants,
        preserve_lines=preserve_lines,
    )
    lines = text.split('\n')
    result_lines: List[str] = []
    for line in lines:
        line = line.rstrip('\n')
        if not line:
            result_lines.append('')
            continue
        tokens = tokenize_line(line, '')
        current_line_parts: List[str] = []
        for i in range(len(tokens)):
            typ, token_text = tokens[i]
            if typ == 'word':
                syllabified = syllabify_word(token_text, merge_hyphen)
                current_line_parts.append(syllabified + SYL_WORD_ENDING)
            elif typ == 'escape':
                current_line_parts.append(f"{OPEN_ESCAPE} {token_text} {CLOSE_ESCAPE}")
            else:
                # Treat "- " / "+ " as suffix boundary marker attached to previous word.
                if (
                    token_text in (f"{HYPHEN} ", f"{WORD_LINKER} ")
                    and current_line_parts
                    and current_line_parts[-1].endswith(SYL_WORD_ENDING)
                    and i + 1 < len(tokens)
                    and tokens[i + 1][0] == 'word'
                ):
                    previous = current_line_parts.pop()
                    current_line_parts.append(previous[:-1] + token_text[0] + SYL_WORD_ENDING)
                    continue

                # Treat " -" / " +" as prefix boundary marker attached to next word.
                if (
                    token_text in (f" {HYPHEN}", f" {WORD_LINKER}")
                    and i + 1 < len(tokens)
                    and tokens[i + 1][0] == 'word'
                ):
                    current_line_parts.append(token_text[1])
                    continue

                # If trailing hyphen/linker is punctuation at line end, keep it before final ¦
                if (
                    i == len(tokens) - 1
                    and token_text in (HYPHEN, WORD_LINKER)
                    and current_line_parts
                    and current_line_parts[-1].endswith(SYL_WORD_ENDING)
                ):
                    previous = current_line_parts.pop()
                    current_line_parts.append(previous[:-1])
                    current_line_parts.append(f"{OPEN_ESCAPE}{token_text}{CLOSE_ESCAPE}")
                    current_line_parts.append(SYL_WORD_ENDING)
                    continue
                current_line_parts.append(f"{OPEN_ESCAPE}{token_text}{CLOSE_ESCAPE}")
                punct_not_final = i+1 < len(tokens)
                if punct_not_final and ' ' not in token_text:
                    warnings.append(f"Punctuation part does not contain a space: '{token_text}' line '{line}")
        if current_line_parts:
            result_lines.append(''.join(current_line_parts))
    if warnings:
        print("\n⚠️  WARNINGS:", file=sys.stderr)
        for w in warnings:
            print(f"   {w}", file=sys.stderr)
        print(file=sys.stderr)
    return '\n'.join(result_lines)

# ---------------------------------------------------------------------------
# Self-test suite
# ---------------------------------------------------------------------------


def run_tests() -> bool:
    """Execute the comprehensive syllabifier tests.

    Returns ``True`` if all tests pass, ``False`` otherwise.
    """
    print("\n" + "="*80)
    print("AKKADIAN SYLLABIFIER - COMPREHENSIVE TESTS")
    print("="*80)
    preprocess_tests = [
        ("Preprocess single newline", "šar\ngimir", "šar gimir", False),
        ("Preprocess double newline", "šar\n\ngimir", "šar\ngimir", False),
        ("Preprocess markdown heading", "šar\n# Title\ngimir", "šar\n# Title\ngimir", False),
        ("Preprocess markdown numbered list", "šar\n1. item one\n2. item two", "šar\n1. item one\n2. item two", False),
        ("Preprocess markdown bullets", "šar\n- item one\n* item two", "šar\n- item one\n* item two", False),
        ("Preprocess markdown table", "| A | B |\n| --- | --- |\n| šar | gimir |", "| A | B |\n| --- | --- |\n| šar | gimir |", False),
        ("Preprocess markdown fence", "```\na\nb\n```\nšar", "```\na\nb\n```\nšar", False),
        ("Preprocess preserve lines", "šar\ngimir", "šar\ngimir", True),
        ("Preprocess hyphen before markdown", "šar-\nma\n# Title", "šar-ma\n# Title", False),
        ("Preprocess plus before markdown", "šar+\nma\n# Title", "šar+ma\n# Title", False),
    ]

    tests = [
        # ===== SYLLABLE TYPES =====
        ("CV", "ša", "ša¦"),
        ("CVC", "šar", "šar¦"),
        ("CVV", "bā", "bā¦"),
        ("CVVC", "nāš", "nāš¦"),
        ("#VC", "ap", "ap¦"),
        ("#V", "a", "a¦"),
        ("#VV", "ī", "ī¦"),
        ("#VVC", "ān", "ān¦"),
        
        # ===== WORD COMBINATIONS =====
        ("CV-CVC", "gimir", "gi·mir¦"),
        ("CVC-CVV", "dadmē", "dad·mē¦"),
        ("CVV-CVV", "bānû", "bā·nû¦"),
        ("CVC-CVV-CV", "kibrāti", "kib·rā·ti¦"),
        ("CVC-CVC-CVC-CV", "ḫendursanga", "ḫen·dur·san·ga¦"),
        ("V-CVC", "apil", "a·pil¦"),
        ("VC-CVC", "ellil", "el·lil¦"),
        ("CVVC-CVV", "rēštû", "rēš·tû¦"),
        ("CVC-CV-geminate", "ḫaṭṭi", "ḫaṭ·ṭi¦"),
        ("CVVC-CV", "ṣīrti", "ṣīr·ti¦"),
        ("CVV-CVC", "nāqid", "nā·qid¦"),
        ("CVC-CVVC", "ṣalmāt", "ṣal·māt¦"),
        ("CVC-CV-CV", "qaqqadi", "qaq·qa·di¦"),
        ("CVV-CVV", "rēʾû", "rē·ʾû¦"),
        ("CV-CVV-CVV-CV", "tenēšēti", "te·nē·šē·ti¦"),
        ("VV-CVC", "īšum", "ī·šum¦"),
        ("CVV-CV-CV", "ṭābiḫu", "ṭā·bi·ḫu¦"),
        ("CVC-CV", "naʾdu", "naʾ·du¦"),
        ("V-CV", "ana", "a·na¦"),
        ("CV-CVV", "našê", "na·šê¦"),
        ("CVC-CVV-CV", "kakkīšu", "kak·kī·šu¦"),
        ("VC-CVV-CV", "ezzūti", "ez·zū·ti¦"),
        ("CVV-CVV-CV", "qātāšu", "qā·tā·šu¦"),
        ("VC-CVV", "asmā", "as·mā¦"),
        
        # ===== HYPHEN TESTS =====
        ("Hyphenated word - preserve", "ḫendur-sanga", "ḫen·dur-san·ga¦"),
        ("Hyphenated word - merge", "ḫendur-sanga", "ḫen·dur·san·ga¦", True),
        ("Multiple hyphens - preserve", "amēlu-ša-īšum", "a·mē·lu-ša-ī·šum¦"),
        ("Multiple hyphens - merge", "amēlu-ša-īšum", "a·mē·lu·ša·ī·šum¦", True),
        ("Word linker + preserve", "apilellil+gimirdadmē", "a·pi·lel·lil+gi·mir·dad·mē¦"),
        ("Word linker + with syllabic words", "apil+ellil", "a·pil+el·lil¦"),
        ("Mixed + and - separators", "apil+el-lil", "a·pil+el-lil¦"),
        ("Hyphen at beginning", "-šar", "⟦-⟧šar¦"),
        ("Hyphen at end", "šar-", "šar⟦-⟧¦"),
        ("Linker at beginning", "+šar", "⟦+⟧šar¦"),
        ("Linker at end", "šar+", "šar⟦+⟧¦"),
        
        # ===== DASH VS HYPHEN =====
        ("Dash with spaces", "ḫendur - sanga", "ḫen·dur¦⟦ - ⟧san·ga¦"),
        ("Hyphen+space", "ḫendur- sanga", "ḫen·dur-¦san·ga¦"),
        ("Space+hyphen", "ḫendur -sanga", "ḫen·dur¦-san·ga¦"),
        
        # ===== WHITESPACE BETWEEN WORDS =====
        ("Single space between words", "šar gimir", "šar¦gi·mir¦"),
        ("Multiple spaces between words", "šar   gimir", "šar¦gi·mir¦"),
        ("Tab between words", "šar\tgimir", "šar¦gi·mir¦"),
        ("Newline between words", "šar\ngimir", "šar¦gi·mir¦"),
        ("Hyphen split across lines merge", "ḫendur-\nsanga", "ḫen·dur·san·ga¦", True),
        ("Spaced hyphen across lines no merge", "ḫendur -\nsanga", "ḫen·dur¦⟦ - ⟧san·ga¦"),
        ("Word linker split across lines", "apil+\nellil", "a·pil+el·lil¦"),
        ("Spaced linker across lines no merge", "apil +\nellil", "a·pil¦⟦ + ⟧el·lil¦"),
        ("Double newline", "šar\n\ngimir", "šar¦\ngi·mir¦"),
        ("Preserve lines single newline", "šar\ngimir", "šar¦\ngi·mir¦", False, True),
        
        # ===== NUMBERS AND NON-AKKADIAN =====
        ("Number between words", "šar 123 gimir", "šar¦⟦ 123 ⟧gi·mir¦"),
        ("Number with commas", "šar 12,345 gimir", "šar¦⟦ 12,345 ⟧gi·mir¦"),
        ("Number with newline", "šar 123\n456 gimir", "šar¦⟦ 123 456 ⟧gi·mir¦"),
        ("Number with spaces and newline", "šar 123\n  456 gimir", "šar¦⟦ 123 456 ⟧gi·mir¦"),
        ("Number with tab and dash", "šar 123  \t-  456 gimir", "šar¦⟦ 123  \t-  456 ⟧gi·mir¦"),
        
        # ===== PUNCTUATION =====
        ("Comma after word", "šar, gimir", "šar¦⟦, ⟧gi·mir¦"),
        ("Period after word", "šar· gimir", "šar¦⟦· ⟧gi·mir¦"),
        ("Em-dash", "šar — gimir", "šar¦⟦ — ⟧gi·mir¦"),
        ("Ellipsis", "šar … gimir", "šar¦⟦ … ⟧gi·mir¦"),
        
        # ===== FOREIGN CHARACTERS =====
        ("Chinese characters", "šar 国王 gimir", "šar¦⟦ 国王 ⟧gi·mir¦"),
        ("Foreign character in word", "šar? gimir[test]done", "šar¦⟦? ⟧gi·mir¦⟦[test]⟧d¦⟦o⟧ne¦"),
        ("Mixed with brackets", "šar gimir [jamal@gmail·com] muḫḫi.", "šar¦gi·mir¦⟦ [jamal@gmail·com] ⟧muḫ·ḫi¦⟦.⟧"),

        # ===== CR-005 ESCAPE SYNTAX =====
        ("Double-brace escape", "šar {{English word}} gimir", "šar¦⟦ {{English word}} ⟧gi·mir¦"),
        ("Tagged escape", "šar {url{https://ex.am/ple}} gimir", "šar¦⟦ {url{https://ex.am/ple}} ⟧gi·mir¦"),
        ("Internal tagged escape", "šar {_mdf{---}} gimir", "šar¦⟦ {_mdf{---}} ⟧gi·mir¦"),
        ("Trim whitespace inside escape", "šar {{  hello world  }} gimir", "šar¦⟦ {{hello world}} ⟧gi·mir¦"),
        ("Escape spacing like punctuation", "šar {{x}} gimir", "šar¦⟦ {{x}} ⟧gi·mir¦"),
        
        # ===== REAL EXAMPLES =====
        ("Complex line", "ikkaru ina muḫḫi … — ibakki ṣarpiš", 
         "ik·ka·ru¦i·na¦muḫ·ḫi¦⟦ … — ⟧i·bak·ki¦ṣar·piš¦"),
        
        # ===== DIPHTHONG TESTS =====
        ("Diphthong ua", "ua", "u·ʾa¦"),
        ("Diphthong ai", "ai", "a·ʾi¦"),
        ("Diphthong iā", "iā", "i·ʾā¦"),
        ("Multiple diphthongs", "ua iā", "u·ʾa¦i·ʾā¦"),
        ("Diphthong with consonant", "šar ua", "šar¦u·ʾa¦"),
    ]
    
    passed = 0
    total = len(preprocess_tests) + len(tests)
    print(f"\nRunning {total} tests...\n")

    for name, inp, expected, preserve in preprocess_tests:
        result = text_preprocess_boundaries(inp, [], preserve_lines=preserve)
        if result == expected:
            print(f"PASS {name}")
            passed += 1
        else:
            print(f"FAIL {name}")
            print(f"   Input: '{inp}'\n   Expected: '{expected}'\n   Got: '{result}'")

    for test in tests:
        if len(test) == 3:
            name, inp, expected = test
            merge = False
            preserve_lines = False
        elif len(test) == 4:
            name, inp, expected, merge = test
            preserve_lines = False
        else:
            name, inp, expected, merge, preserve_lines = test
        result = syllabify_text(inp, merge_hyphen=merge, preserve_lines=preserve_lines)
        if result == expected:
            print(f"PASS {name}")
            passed += 1
        else:
            print(f"FAIL {name}")
            print(f"   Input: '{inp}'\n   Expected: '{expected}'\n   Got: '{result}'")

    nested = parse_escape_at("{{a{{b}}}}", 0)
    if nested is None:
        print("PASS Nested escapes are unsupported")
        passed += 1
        total += 1
    else:
        print("FAIL Nested escapes are unsupported")
        print(f"   Expected: None\n   Got: {nested}")
        total += 1

    print(f"\nPassed: {passed}/{total}")
    return passed == total
