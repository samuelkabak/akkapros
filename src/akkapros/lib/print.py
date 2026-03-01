#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Accent Printer (Library)
Version: 1.0.0

Transforms *_tilde text into two reading-friendly outputs:
- accent_accute text: ~ -> ´
- accent_bold markdown: syllable containing ~ is bold, ~ removed

Core marker handling:
- TIL_WORD_LINKER '+' -> '‿'
- SYL_SEPARATOR '·' removed in final outputs
- Hyphen '-' preserved as boundary marker
"""

from pathlib import Path
from typing import Tuple

from akkapros.lib.constants import (
    SYL_SEPARATOR,
    TIL_WORD_LINKER,
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
)
from akkapros.lib.syllabify import split_by_brackets_level3

__version__ = "1.0.0"
__author__ = "Samuel KABAK"
__license__ = "MIT"
__project__ = "Akkadian Prosody"
__repo__ = "akkapros"

ACCUTE_MARK = '´'
WORD_LINKER_OUT = '‿'
TILDE = '~'
HYPHEN = '-'


def _flush_syllable(syllable_text: str, mode: str) -> str:
    if not syllable_text:
        return ''

    if mode == 'accute':
        return syllable_text.replace(TILDE, ACCUTE_MARK)

    clean = syllable_text.replace(TILDE, '')
    if TILDE in syllable_text and clean:
        return f"**{clean}**"
    return clean


def _convert_word(word: str, mode: str) -> str:
    """Convert one Akkadian word token."""
    out = []
    current_syllable = []

    def flush_current() -> None:
        if current_syllable:
            out.append(_flush_syllable(''.join(current_syllable), mode))
            current_syllable.clear()

    for char in word:
        if char == TIL_WORD_LINKER:
            flush_current()
            out.append(WORD_LINKER_OUT)
        elif char == TILDE:
            current_syllable.append(char)
        elif char == SYL_SEPARATOR:
            flush_current()
        elif char == HYPHEN:
            flush_current()
            out.append(HYPHEN)
        else:
            current_syllable.append(char)

    flush_current()
    return ''.join(out)


def _is_word_char(char: str) -> bool:
    """Return True for characters that belong to processable Akkadian word chunks."""
    if char in AKKADIAN_VOWELS or char in AKKADIAN_CONSONANTS:
        return True
    return char in {TIL_WORD_LINKER, SYL_SEPARATOR, HYPHEN, TILDE}


def _convert_non_bracket_part(part: str, mode: str) -> str:
    """Convert a string part that is outside square brackets."""
    out = []
    current_word = []

    def flush_word() -> None:
        if current_word:
            out.append(_convert_word(''.join(current_word), mode))
            current_word.clear()

    for char in part:
        if _is_word_char(char):
            current_word.append(char)
        else:
            flush_word()
            out.append(char)

    flush_word()
    return ''.join(out)


def convert_line(line: str, mode: str) -> str:
    """Convert one line to either accent_accute or accent_bold format."""
    if mode not in {'accute', 'bold'}:
        raise ValueError("mode must be 'accute' or 'bold'")

    parts = split_by_brackets_level3(line)
    if len(parts) > 1:
        converted = []
        for part in parts:
            if '[' in part and ']' in part:
                converted.append(part)
            else:
                converted.append(_convert_non_bracket_part(part, mode))
        return ''.join(converted)

    return _convert_non_bracket_part(line, mode)


def convert_text(text: str) -> Tuple[str, str]:
    """Convert full text and return (accent_accute_text, accent_bold_markdown)."""
    lines = text.splitlines(keepends=True)
    accute_lines = [convert_line(line, mode='accute') for line in lines]
    bold_lines = [convert_line(line, mode='bold') for line in lines]
    return ''.join(accute_lines), ''.join(bold_lines)


def process_file(
    input_file: str,
    output_accute_file: str,
    output_bold_file: str,
    write_accute: bool = True,
    write_bold: bool = True,
) -> None:
    """Read *_tilde input and write selected output files."""
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    accute_text, bold_text = convert_text(text)

    if write_accute:
        Path(output_accute_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_accute_file, 'w', encoding='utf-8') as f:
            f.write(accute_text)

    if write_bold:
        Path(output_bold_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_bold_file, 'w', encoding='utf-8') as f:
            f.write(bold_text)


def run_tests() -> bool:
    """Lightweight self-tests for conversion rules."""
    tests = [
        ("gi·mir+dad~·mē", "accute", "gimir‿dad´mē"),
        ("gi·mir+dad~·mē", "bold", "gimir‿**dad**mē"),
        ("er~·ra", "accute", "er´ra"),
        ("er~·ra", "bold", "**er**ra"),
        ("nā~š", "bold", "**nāš**"),
        ("ša+ana+na·šê", "accute", "ša‿ana‿našê"),
        ("ī·ris·sū~-ma", "bold", "īris**sū**-ma"),
        ("šar [https://ex.am/ple+uri] gi·mir+dad~·mē", "bold", "šar [https://ex.am/ple+uri] gimir‿**dad**mē"),
        ("šar, 123 gi·mir+dad~·mē", "accute", "šar, 123 gimir‿dad´mē"),
    ]

    passed = 0
    for inp, mode, expected in tests:
        got = convert_line(inp, mode)
        if got == expected:
            passed += 1
        else:
            print(f"FAILED [{mode}]\n  in : {inp}\n  got: {got}\n  exp: {expected}")

    total = len(tests)
    print(f"print.py tests: {passed}/{total} passed")
    return passed == total
