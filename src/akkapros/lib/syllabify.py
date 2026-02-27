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
from typing import List

# shared constants
from akkapros.lib.constants import (
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    GLOTTAL,
    SYL_WORD_ENDING,
)

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
    if c != '-':
        return False
    if before == '' and after == '':
        return True
    before_is_letter = before and is_akkadian_letter(before)
    after_is_letter = after and is_akkadian_letter(after)
    return before_is_letter or after_is_letter


def is_word_char(c: str, extra: str = '', before: str = '', after: str = '') -> bool:
    """True if character can form part of an Akkadian word token."""
    if is_akkadian_letter(c):
        return True
    if c == '-':
        return is_hyphen(c, before, after)
    return False

# ---------------------------------------------------------------------------
# Preprocessing helpers
# ---------------------------------------------------------------------------

def preprocess_diphthongs(text: str) -> str:
    """Insert glottal stops between adjacent vowels (diphthong expansion).

    Warnings are printed to ``stderr`` when diphthongs are detected to help
    users spot them in their input data.  The function is idempotent in the
    sense that once a glottal stop has been inserted it will no longer match
    the regex pattern.
    """
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
            print(f"     → Inserting glottal stop: {diphthong[0]}ʾ{diphthong[1]}", file=sys.stderr)
        text = re.sub(vowels_pattern, r'\1' + GLOTTAL + r'\2', text)
        print(f"   Total diphthongs processed: {len(matches)}", file=sys.stderr)
        print(file=sys.stderr)
    return text


def text_preprocess_boundaries(text: str, warnings: List[str], extra_vowels: str = '', extra_consonants: str = '') -> str:
    """Preprocess text prior to syllabification.

    The function performs the following steps:

    1. Update the global character sets with ``extra_vowels``/``extra_consonants``.
    2. Expand diphthongs by inserting glottal stops.
    3. Trim trailing whitespace on each line (preserve leading spaces).
    4. Merge words split across lines by hyphenation.
    5. Preserve paragraph structure (newlines).
    6. Warn about tabs occurring between Akkadian words.
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
    while i < len(lines):
        line = lines[i].rstrip('\n')
        original_line = line
        line = line.rstrip()
        if original_line.rstrip().endswith('-') and i + 1 < len(lines):
            next_line = lines[i + 1]
            next_line_stripped = next_line.lstrip()
            if next_line_stripped and is_word_char(next_line_stripped[0]):
                base = original_line.rstrip().rstrip('-')
                merged = base + '-' + next_line_stripped
                warnings.append(f"Hyphen split across lines merged: '{original_line.rstrip()}' + '{next_line}' → '{merged}'")
                processed_lines.append(merged)
                rest = next_line[len(next_line_stripped):]
                processed_lines.append(rest or '')
                i += 2
                continue
        processed_lines.append(line)
        i += 1
    if '\t' in text and not tab_warning_issued:
        warnings.append("Tabs detected: tabs between Akkadian words are treated as spaces and eliminated")
    return '\n'.join(processed_lines)

# ---------------------------------------------------------------------------
# Syllabification logic
# ---------------------------------------------------------------------------

def syllabify_word(word: str, merge_hyphen: bool = False) -> str:
    """Return the syllabified representation of a single word."""
    if '-' not in word:
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
        return '.'.join(syllables)
    parts = word.split('-')
    result_parts = [syllabify_word(p, merge_hyphen) for p in parts]
    separator = '-' if not merge_hyphen else '.'
    return separator.join(result_parts)


def tokenize_line(line: str, extra: str = '') -> List[tuple]:
    """Split a line of text into word/punctuation tokens."""
    tokens = []
    i = 0
    n = len(line)
    while i < n:
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
                before_inner = line[i-1] if i > start else ''
                after_inner = line[i+1] if i+1 < n else ''
                if is_word_char(line[i], extra, before_inner, after_inner):
                    break
                i += 1
            punct = line[start:i]
            if punct.isspace():
                prev_is_word = tokens and tokens[-1][0] == 'word'
                next_is_word = i < n and is_word_char(line[i], extra)
                if prev_is_word and next_is_word:
                    continue
            if punct:
                tokens.append(('punct', punct))
    return tokens


def syllabify_text(text: str, extra_vowels: str = '', extra_consonants: str = '', merge_hyphen: bool = False) -> str:
    """Return the fully syllabified version of ``text``.

    The returned string uses the global ``SYL_WORD_ENDING`` marker at the end
    of every word and preserves line breaks.
    """
    warnings: List[str] = []
    text = text_preprocess_boundaries(text, warnings, extra_vowels, extra_consonants)
    lines = text.split('\n')
    result_lines: List[str] = []
    for line in lines:
        line = line.rstrip('\n')
        if not line:
            result_lines.append('')
            continue
        tokens = tokenize_line(line, '')
        current_line_parts: List[str] = []
        in_brackets = False
        for typ, token_text in tokens:
            if typ == 'word':
                if in_brackets:
                    current_line_parts.append(token_text + SYL_WORD_ENDING)
                else:
                    syllabified = syllabify_word(token_text, merge_hyphen)
                    current_line_parts.append(syllabified + SYL_WORD_ENDING)
            else:
                if '[' in token_text:
                    in_brackets = True
                if ']' in token_text:
                    in_brackets = False
                current_line_parts.append(f"[{token_text}]")
                if not ' ' in token_text and not '\t' in token_text:
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
    print("AKKADIAN SYLLABIFIER — COMPREHENSIVE TESTS")
    print("="*80)
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
        ("CV-CVC", "gimir", "gi.mir¦"),
        ("CVC-CVV", "dadmē", "dad.mē¦"),
        ("CVV-CVV", "bānû", "bā.nû¦"),
        ("CVC-CVV-CV", "kibrāti", "kib.rā.ti¦"),
        ("CVC-CVC-CVC-CV", "ḫendursanga", "ḫen.dur.san.ga¦"),
        ("V-CVC", "apil", "a.pil¦"),
        ("VC-CVC", "ellil", "el.lil¦"),
        ("CVVC-CVV", "rēštû", "rēš.tû¦"),
        ("CVC-CV-geminate", "ḫaṭṭi", "ḫaṭ.ṭi¦"),
        ("CVVC-CV", "ṣīrti", "ṣīr.ti¦"),
        ("CVV-CVC", "nāqid", "nā.qid¦"),
        ("CVC-CVVC", "ṣalmāt", "ṣal.māt¦"),
        ("CVC-CV-CV", "qaqqadi", "qaq.qa.di¦"),
        ("CVV-CVV", "rēʾû", "rē.ʾû¦"),
        ("CV-CVV-CVV-CV", "tenēšēti", "te.nē.šē.ti¦"),
        ("VV-CVC", "īšum", "ī.šum¦"),
        ("CVV-CV-CV", "ṭābiḫu", "ṭā.bi.ḫu¦"),
        ("CVC-CV", "naʾdu", "naʾ.du¦"),
        ("V-CV", "ana", "a.na¦"),
        ("CV-CVV", "našê", "na.šê¦"),
        ("CVC-CVV-CV", "kakkīšu", "kak.kī.šu¦"),
        ("VC-CVV-CV", "ezzūti", "ez.zū.ti¦"),
        ("CVV-CVV-CV", "qātāšu", "qā.tā.šu¦"),
        ("VC-CVV", "asmā", "as.mā¦"),
        
        # ===== HYPHEN TESTS =====
        ("Hyphenated word - preserve", "ḫendur-sanga", "ḫen.dur-san.ga¦"),
        ("Hyphenated word - merge", "ḫendur-sanga", "ḫen.dur.san.ga¦", True),
        ("Multiple hyphens - preserve", "amēlu-ša-īšum", "a.mē.lu-ša-ī.šum¦"),
        ("Multiple hyphens - merge", "amēlu-ša-īšum", "a.mē.lu.ša.ī.šum¦", True),
        ("Hyphen at beginning", "-šar", "-šar¦"),
        ("Hyphen at end", "šar-", "šar-¦"),
        
        # ===== DASH VS HYPHEN =====
        ("Dash with spaces", "ḫendur - sanga", "ḫen.dur¦[ - ]san.ga¦"),
        ("Hyphen+space", "ḫendur- sanga", "ḫen.dur-¦san.ga¦"),
        ("Space+hyphen", "ḫendur -sanga", "ḫen.dur¦-san.ga¦"),
        
        # ===== WHITESPACE BETWEEN WORDS =====
        ("Single space between words", "šar gimir", "šar¦gi.mir¦"),
        ("Multiple spaces between words", "šar   gimir", "šar¦gi.mir¦"),
        ("Tab between words", "šar\tgimir", "šar¦gi.mir¦"),
        ("Newline between words", "šar\ngimir", "šar¦\ngi.mir¦"),
        ("Double newline", "šar\n\ngimir", "šar¦\n\ngi.mir¦"),
        
        # ===== NUMBERS AND NON-AKKADIAN =====
        ("Number between words", "šar 123 gimir", "šar¦[ 123 ]gi.mir¦"),
        ("Number with commas", "šar 12,345 gimir", "šar¦[ 12,345 ]gi.mir¦"),
        ("Number with newline", "šar 123\n456 gimir", "šar¦[ 123]\n[456 ]gi.mir¦"),
        ("Number with spaces and newline", "šar 123\n  456 gimir", "šar¦[ 123]\n[  456 ]gi.mir¦"),
        ("Number with tab and dash", "šar 123  \t-  456 gimir", "šar¦[ 123  \t-  456 ]gi.mir¦"),
        
        # ===== PUNCTUATION =====
        ("Comma after word", "šar, gimir", "šar¦[, ]gi.mir¦"),
        ("Period after word", "šar. gimir", "šar¦[. ]gi.mir¦"),
        ("Em-dash", "šar — gimir", "šar¦[ — ]gi.mir¦"),
        ("Ellipsis", "šar … gimir", "šar¦[ … ]gi.mir¦"),
        
        # ===== FOREIGN CHARACTERS =====
        ("Chinese characters", "šar 国王 gimir", "šar¦[ 国王 ]gi.mir¦"),
        ("Mixed with brackets", "šar gimir[test]done", "šar¦gi.mir¦[[]test¦[]]d¦[o]ne¦"),
        
        # ===== REAL EXAMPLES =====
        ("Complex line", "ikkaru ina muḫḫi … — ibakki ṣarpiš", 
         "ik.ka.ru¦i.na¦muḫ.ḫi¦[ … — ]i.bak.ki¦ṣar.piš¦"),
        
        # ===== DIPHTHONG TESTS =====
        ("Diphthong ua", "ua", "u.ʾa¦"),
        ("Diphthong ai", "ai", "a.ʾi¦"),
        ("Diphthong iā", "iā", "i.ʾā¦"),
        ("Multiple diphthongs", "ua iā", "u.ʾa¦i.ʾā¦"),
        ("Diphthong with consonant", "šar ua", "šar¦u.ʾa¦"),
    ]
    passed = 0
    total = len(tests)
    print(f"\nRunning {total} tests...\n")
    for test in tests:
        if len(test) == 3:
            name, inp, expected = test
            merge = False
        else:
            name, inp, expected, merge = test
        result = syllabify_text(inp, merge_hyphen=merge)
        if result == expected:
            print(f"✅ {name}")
            passed += 1
        else:
            print(f"❌ {name}")
            print(f"   Input: '{inp}'\n   Expected: '{expected}'\n   Got: '{result}'")
    print(f"\nPassed: {passed}/{total}")
    return passed == total
