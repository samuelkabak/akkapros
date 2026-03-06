#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Accent Printer (Library)
Version: 1.0.0

Transforms *_tilde text into three reading-friendly outputs:
- accent_acute text: ~ -> ´
- accent_bold markdown: syllable containing ~ is bold, ~ removed
- accent_ipa text: IPA transliteration with stress/length markers

Core marker handling:
- WORD_LINKER '+' -> '‿'
- SYL_SEPARATOR '·' removed in final outputs
- Hyphen '-' preserved as boundary marker
"""

from pathlib import Path
from typing import Tuple
import tempfile
import unicodedata
import re

from akkapros.lib.constants import (
    SYL_SEPARATOR,
    WORD_LINKER,
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
)
from akkapros.lib.syllabify import split_by_brackets_level3

__version__ = "1.0.0"
__author__ = "Samuel KABAK"
__license__ = "MIT"
__project__ = "Akkadian Prosody"
__repo__ = "akkapros"

ACUTE_MARK = '´'
WORD_LINKER_OUT = '‿'
TILDE = '~'
HYPHEN = '-'
IPA_LENGTH = 'ː'
IPA_STRESS = 'ˈ'
GLOTTAL_STOP = 'ʾ'

ALL_VOWELS = set('aeiuāēīūâêîû')
EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}

IPA_MAP = {
    'b': 'b', 'd': 'd', 'g': 'g', 'k': 'k', 'p': 'p',
    'q': 'q', 'ṭ': 'tˤ', 'ṣ': 'sˤ', 'š': 'ʃ',
    's': 's', 'z': 'z', 'l': 'l', 'm': 'm', 'n': 'n',
    'r': 'r', 'ḥ': 'χ', 'ḫ': 'χ', 'ʿ': 'ʔ', 'ʾ': 'ʔ',
    'w': 'w', 'y': 'j', 't': 't',
}

IPA_VOWELS_DEFAULT = {
    'a': 'a', 'i': 'i', 'u': 'u', 'e': 'e',
    'ā': 'aː', 'ī': 'iː', 'ū': 'uː', 'ē': 'eː',
    'â': 'aː', 'î': 'iː', 'û': 'uː', 'ê': 'eː',
}

IPA_VOWELS_EMPHATIC = {
    'a': 'ɑ', 'i': 'ɨ', 'u': 'ʊ', 'e': 'ɛ',
    'ā': 'ɑː', 'ī': 'ɨː', 'ū': 'ʊː', 'ē': 'ɛː',
    'â': 'ɑː', 'î': 'ɨː', 'û': 'ʊː', 'ê': 'ɛː',
}

XAR_CONSONANT_MAP = {
    'b': 'b', 'd': 'd', 'g': 'g', 'k': 'k', 'p': 'p',
    'q': 'ꝗ', 'ṭ': 'ꞓ', 'ṣ': 'ɉ', 'š': 'x̌',
    's': 's', 'z': 'z', 'l': 'l', 'm': 'm', 'n': 'n',
    'r': 'r', 'ḥ': 'ḫ', 'ḫ': 'ḫ', 'ʿ': "'", 'ʾ': "'",
    'w': 'w', 'y': 'j', 't': 't',
}

XAR_VOWELS_DEFAULT = {
    'a': 'a', 'i': 'i', 'u': 'u', 'e': 'e',
    'ā': 'aa', 'ī': 'ii', 'ū': 'uu', 'ē': 'ee',
    'â': 'eâ', 'î': 'eî', 'û': 'iû', 'ê': 'aê',
}

XAR_VOWELS_EMPHATIC = {
    'a': 'à', 'i': 'ì', 'u': 'ù', 'e': 'è',
    'ā': 'àa', 'ī': 'ìi', 'ū': 'ùu', 'ē': 'èe',
    'â': 'èâ', 'î': 'èî', 'û': 'ìû', 'ê': 'àê',
}

IPA_SYMBOL_TAGS = {
    '.': 'period',
    ',': 'comma',
    '?': 'question',
    '!': 'exclamation',
    ':': 'colon',
    ';': 'semicolon',
    '—': 'emdash',
    '–': 'endash',
    '-': 'hyphen',
    "'": 'apostrophe',
    '“': 'opening-dblquote',
    '”': 'closing-dblquote',
    '‘': 'opening-squote',
    '’': 'closing-squote',
    '(': 'opening-parenthese',
    ')': 'closing-parenthese',
    '[': 'opening-bracket',
    ']': 'closing-bracket',
    '{': 'opening-brace',
    '}': 'closing-brace',
    '/': 'slash',
    '*': 'asterisk',
    '†': 'dagger',
    '‡': 'doubledagger',
    '¶': 'pilcrow',
    '§': 'section',
    '&': 'ampersand',
    '#': 'hash',
    '%': 'percent',
    '$': 'dollar',
    '€': 'euro',
    '£': 'pound',
    '¥': 'yen',
    '₹': 'rupee',
    '₽': 'ruble',
    '₩': 'won',
    '₪': 'shekel',
    '₫': 'dong',
    '₴': 'hryvnia',
    '₦': 'naira',
    '₱': 'peso',
    '₡': 'colon-currency',
    '₲': 'guarani',
    '₵': 'cedi',
    '₭': 'kip',
    '₮': 'tugrik',
    '₼': 'manat',
    '₺': 'lira',
}

IPA_TAG_ALIASES = {
    '…': 'ellipsis',
    '⋯': 'ellipsis',
    '−': 'hyphen',
    '―': 'emdash',
    '«': 'opening-dblquote',
    '»': 'closing-dblquote',
    '‹': 'opening-squote',
    '›': 'closing-squote',
    '＄': 'dollar',
    '％': 'percent',
    '＃': 'hash',
}


def _insert_glottal_stops(word: str) -> str:
    """Insert ʾ before vowel-initial segments (start, after +, after -)."""
    out = []

    for idx, char in enumerate(word):
        boundary = idx == 0 or word[idx - 1] in {WORD_LINKER, HYPHEN}
        if boundary and char != GLOTTAL_STOP:
            if char in ALL_VOWELS:
                out.append(GLOTTAL_STOP)
            elif char == TILDE and idx + 1 < len(word) and word[idx + 1] in ALL_VOWELS:
                out.append(GLOTTAL_STOP)
        out.append(char)

    return ''.join(out)


def _insert_glottal_stops_with_indices(word: str) -> Tuple[str, list]:
    """Insert ʾ before vowel-initial segments and map each output char to source index (-1 for inserted)."""
    out = []
    out_indices = []

    for idx, char in enumerate(word):
        boundary = idx == 0 or word[idx - 1] in {WORD_LINKER, HYPHEN}
        if boundary and char != GLOTTAL_STOP:
            if char in ALL_VOWELS:
                out.append(GLOTTAL_STOP)
                out_indices.append(-1)
            elif char == TILDE and idx + 1 < len(word) and word[idx + 1] in ALL_VOWELS:
                out.append(GLOTTAL_STOP)
                out_indices.append(-1)
        out.append(char)
        out_indices.append(idx)

    return ''.join(out), out_indices


def _is_emphatic_adjacent(text: str, index: int, skip_chars=None) -> bool:
    """True when a vowel has adjacent q/ṣ/ṭ (optionally skipping separators)."""

    if skip_chars is None:
        skip_chars = {TILDE}

    def get_neighbor(step: int) -> str:
        pos = index + step
        while 0 <= pos < len(text) and text[pos] in skip_chars:
            pos += step
        if 0 <= pos < len(text):
            return text[pos]
        return ''

    left = get_neighbor(-1)
    right = get_neighbor(1)
    return left in EMPHATIC_CONSONANTS or right in EMPHATIC_CONSONANTS


def _to_ipa_vowel(vowel: str, emphatic_context: bool) -> str:
    if emphatic_context:
        return IPA_VOWELS_EMPHATIC.get(vowel, vowel)
    return IPA_VOWELS_DEFAULT.get(vowel, vowel)


def _to_xar_vowel(vowel: str, emphatic_context: bool) -> str:
    if emphatic_context:
        return XAR_VOWELS_EMPHATIC.get(vowel, vowel)
    return XAR_VOWELS_DEFAULT.get(vowel, vowel)


def remove_glottals_ipa(text: str) -> str:
    """Legacy IPA cleanup for non-canonical merged glottal symbols in ipa-ob mode.

    Canonical glottal stop ʔ is handled upstream with source-aware logic:
    - remove letter glottals (ʾ/ʿ from input text)
    - keep inserted implied glottals (including stressed/repaired ones)
    """
    text = re.sub(r'ʕː([aeiouɑɨʊɛ])', r'\1ː', text)
    text = re.sub(r'ʕ([aeiouɑɨʊɛ])', r'\1', text)
    return text.replace('ʕ', '')


def remove_glottals(text: str) -> str:
    """Remove mapped glottal apostrophes in XAR using diphthong-preserving replacements."""
    short_to_circumflex = {'a': 'â', 'i': 'î', 'u': 'û', 'e': 'ê'}

    replacements = [
        (r"u'a", 'ua'),
        (r"u'ā", 'uā'),
        (r"u'â", 'uâ'),
        (r"u'ā~", 'uā~'),
        (r"u'â~", 'uâ~'),
        (r"ū'a", 'uā'),
        (r"û'a", 'uâ'),
        (r"ū'ā", 'uā~'),
        (r"û'ā", 'uâ~'),
        (r"ū'â", 'uâ~'),
        (r"û'â", 'uâ~'),
        (r"ū'ā~", 'uā'),
        (r"û'ā~", 'uâ'),
        (r"ū'â~", 'uâ'),
        (r"û'â~", 'uâ'),
        (r"ū~'a", 'uā~'),
        (r"û~'a", 'uâ~'),
        (r"ū~'ā", 'uā'),
        (r"û~'ā", 'uâ'),
        (r"ū~'â", 'uâ'),
        (r"û~'â", 'uâ'),
        (r"ū~'ā~", 'uā~'),
        (r"û~'ā~", 'uâ~'),
        (r"ū~'â~", 'uâ~'),
        (r"û~'â~", 'uâ~'),
        (r"([^aeiu]?)u'a", r"\1ua"),
        (r"([^aeiu]?)u'ā", r"\1uā"),
        (r"([^aeiu]?)u'â", r"\1uâ"),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    # Residual glottals near consonants:
    # (C|start) [aiue] ' (C|end) -> (C|start) [âîûê] (C|end)
    text = re.sub(
        r"(^|(?<=[^aeiuāēīūâêîû]))([aiue])'(?=[^aeiuāēīūâêîû]|$)",
        lambda m: f"{m.group(1)}{short_to_circumflex[m.group(2)]}",
        text,
    )

    # (C|start) [aiue] C ' -> (C|start) [âîûê] C
    text = re.sub(
        r"(^|(?<=[^aeiuāēīūâêîû]))([aiue])([^aeiuāēīūâêîû'])'",
        lambda m: f"{m.group(1)}{short_to_circumflex[m.group(2)]}{m.group(3)}",
        text,
    )

    return text.replace("'", "")


def _convert_word_xar(word: str) -> str:
    """Convert one Akkadian word token to XAR with ordered transforms."""
    emphatic_flags = []
    for idx, char in enumerate(word):
        if char in ALL_VOWELS:
            emphatic_flags.append(_is_emphatic_adjacent(word, idx, {TILDE, SYL_SEPARATOR}))

    step1 = ''.join(XAR_CONSONANT_MAP.get(char, char) for char in word)
    step2 = remove_glottals(step1)

    out = []
    vowel_idx = 0
    for char in step2:
        if char in ALL_VOWELS:
            emphatic_context = emphatic_flags[vowel_idx] if vowel_idx < len(emphatic_flags) else False
            out.append(_to_xar_vowel(char, emphatic_context))
            vowel_idx += 1
        elif char == WORD_LINKER:
            out.append(WORD_LINKER_OUT)
        elif char == SYL_SEPARATOR:
            continue
        elif char == HYPHEN:
            out.append(HYPHEN)
        elif char == TILDE:
            out.append(ACUTE_MARK)
        else:
            out.append(char)

    return ''.join(out)


def _is_punctuation(char: str) -> bool:
    return unicodedata.category(char).startswith('P')


def _detect_ipa_tag(text: str, index: int) -> Tuple[str, int]:
    """Detect IPA tag token at a non-word position and return (tag, next_index)."""
    if text.startswith('...', index):
        return 'ellipsis', index + 3

    char = text[index]
    alias_tag = IPA_TAG_ALIASES.get(char)
    if alias_tag:
        return alias_tag, index + 1

    if char.isdigit():
        pos = index
        while pos < len(text) and text[pos].isdigit():
            pos += 1
        return 'number', pos

    tag = IPA_SYMBOL_TAGS.get(char)
    if tag:
        return tag, index + 1

    if _is_punctuation(char):
        return 'punct', index + 1

    return '', index + 1


def _append_ipa_tag(out: list, tag: str) -> None:
    if tag:
        out.append(f' ⟨{tag}⟩ ')


def _append_ipa_tag_cluster(out: list, tags: list) -> None:
    for tag in tags:
        _append_ipa_tag(out, tag)
    if tags:
        out.append('(..) ')


def _append_ipa_pause(out: list) -> None:
    out.append(' ⟨pause⟩ (.) ')


def _append_ipa_escape(out: list, escaped_text: str) -> None:
    out.append(f' ⟨escape:{escaped_text}⟩ ')


def _normalize_ipa_spacing(text: str) -> str:
    text = re.sub(r'\(\.\.\)\s+⟨pause⟩ \(\.\)\s+', '(..) ', text)
    return re.sub(r' {2,}', ' ', text)


def _flush_syllable(
    syllable_text: str,
    mode: str,
    source_text: str = '',
    source_indices=None,
    ipa_mode: str = 'ipa-ob',
) -> str:
    if not syllable_text:
        return ''

    if mode == 'acute':
        return syllable_text.replace(TILDE, ACUTE_MARK)

    if mode == 'ipa':
        repaired = TILDE in syllable_text
        converted = []

        context_text = source_text if source_text else syllable_text
        context_skip_chars = {TILDE, SYL_SEPARATOR} if source_text else {TILDE}

        for idx, char in enumerate(syllable_text):
            if char in ALL_VOWELS:
                context_index = source_indices[idx] if source_indices else idx
                converted.append(
                    _to_ipa_vowel(
                        char,
                        _is_emphatic_adjacent(context_text, context_index, context_skip_chars),
                    )
                )
            elif char in IPA_MAP:
                if char in {'ʾ', 'ʿ'} and ipa_mode == 'ipa-ob':
                    # Remove only letter glottals in ipa-ob.
                    # Inserted implied glottals carry source index -1.
                    # Keep them only for repaired/stressed syllables.
                    if source_indices is not None and source_indices[idx] == -1 and repaired:
                        converted.append(IPA_MAP[char])
                    else:
                        continue
                else:
                    converted.append(IPA_MAP[char])
            elif char == TILDE:
                converted.append(IPA_LENGTH)
            else:
                converted.append(char)

        ipa_syllable = ''.join(converted)
        if repaired and ipa_syllable:
            # For stressed vowel-initial syllables, reorder so glottal comes first
            # ːʔa → ʔaː (length marker moves to end, after vowel)
            ipa_syllable = re.sub(r'^ː+(\u0294)([aeiou\u0251\u0268\u028a\u025b])(.*)$', 
                                  r'\1\2' + IPA_LENGTH + r'\3', ipa_syllable)
            # For stressed vowel-initial syllables without onset glottal (e.g.,
            # letter glottal removed in ipa-ob): ːa -> aː
            ipa_syllable = re.sub(r'^ː+([aeiou\u0251\u0268\u028a\u025b])(.*)$',
                                  r'\1' + IPA_LENGTH + r'\2', ipa_syllable)
            return f"{IPA_STRESS}{ipa_syllable}"
        return ipa_syllable

    if mode == 'xar':
        converted = []

        context_text = source_text if source_text else syllable_text
        context_skip_chars = {TILDE, SYL_SEPARATOR} if source_text else {TILDE}

        for idx, char in enumerate(syllable_text):
            if char in ALL_VOWELS:
                context_index = source_indices[idx] if source_indices else idx
                converted.append(
                    _to_xar_vowel(
                        char,
                        _is_emphatic_adjacent(context_text, context_index, context_skip_chars),
                    )
                )
            elif char in XAR_CONSONANT_MAP:
                converted.append(XAR_CONSONANT_MAP[char])
            elif char == TILDE:
                converted.append(ACUTE_MARK)
            else:
                converted.append(char)

        return ''.join(converted)

    clean = syllable_text.replace(TILDE, '')
    if TILDE in syllable_text and clean:
        return f"**{clean}**"
    return clean


def _convert_word(word: str, mode: str, ipa_mode: str = 'ipa-ob') -> str:
    """Convert one Akkadian word token."""
    if mode == 'xar':
        return _convert_word_xar(word)

    source_word = word
    source_index_map = None

    if mode == 'ipa':
        word, source_index_map = _insert_glottal_stops_with_indices(word)

    out = []
    current_syllable = []
    current_indices = []

    def flush_current() -> None:
        if current_syllable:
            source_indices = current_indices
            source_text = word
            if source_index_map is not None:
                source_text = source_word
                source_indices = [
                    source_index_map[idx]
                    for idx in current_indices
                ]
            out.append(
                _flush_syllable(
                    ''.join(current_syllable),
                    mode,
                    source_text=source_text,
                    source_indices=source_indices,
                    ipa_mode=ipa_mode,
                )
            )
            current_syllable.clear()
            current_indices.clear()

    for idx, char in enumerate(word):
        if char == WORD_LINKER:
            flush_current()
            if mode == 'ipa':
                out.append(' ')
            else:
                out.append(WORD_LINKER_OUT)
        elif char == TILDE:
            current_syllable.append(char)
            current_indices.append(idx)
        elif char == SYL_SEPARATOR:
            flush_current()
            if mode == 'ipa':
                out.append('.')
        elif char == HYPHEN:
            flush_current()
            out.append(HYPHEN)
        else:
            current_syllable.append(char)
            current_indices.append(idx)

    flush_current()
    result = ''.join(out)
    if mode == 'ipa' and ipa_mode == 'ipa-ob':
        return remove_glottals_ipa(result)
    return result


def _is_word_char(char: str) -> bool:
    """Return True for characters that belong to processable Akkadian word chunks."""
    if char in AKKADIAN_VOWELS or char in AKKADIAN_CONSONANTS or char in ALL_VOWELS:
        return True
    return char in {WORD_LINKER, SYL_SEPARATOR, HYPHEN, TILDE}


def _convert_non_bracket_part(part: str, mode: str, ipa_mode: str = 'ipa-ob') -> str:
    """Convert a string part that is outside square brackets."""
    if mode == 'ipa':
        return _convert_non_bracket_part_ipa(part, ipa_mode)

    out = []
    current_word = []

    def flush_word() -> None:
        if current_word:
            out.append(_convert_word(''.join(current_word), mode, ipa_mode))
            current_word.clear()

    for char in part:
        if _is_word_char(char):
            current_word.append(char)
        else:
            flush_word()
            _append_non_word_char(out, char, mode)

    flush_word()
    return ''.join(out)


def _convert_non_bracket_part_ipa(part: str, ipa_mode: str = 'ipa-ob') -> str:
    tokens = []
    index = 0

    while index < len(part):
        char = part[index]
        if _is_word_char(char):
            start = index
            while index < len(part) and _is_word_char(part[index]):
                index += 1
            tokens.append({'type': 'word', 'text': part[start:index]})
            continue

        if char == ' ':
            start = index
            while index < len(part) and part[index] == ' ':
                index += 1
            tokens.append({'type': 'space', 'text': part[start:index]})
            continue

        if char == WORD_LINKER_OUT:
            tokens.append({'type': 'linker', 'text': char})
            index += 1
            continue

        tag, next_index = _detect_ipa_tag(part, index)
        if tag:
            tokens.append({'type': 'punct', 'tag': tag})
            index = next_index
        else:
            tokens.append({'type': 'char', 'text': char})
            index += 1

    out = []
    token_count = len(tokens)
    i = 0

    while i < token_count:
        token = tokens[i]
        token_type = token['type']

        if token_type == 'word':
            out.append(_convert_word(token['text'], 'ipa', ipa_mode))

            j = i + 1
            while j < token_count and tokens[j]['type'] == 'space':
                j += 1

            punctuation_tags = []
            k = j
            while k < token_count and tokens[k]['type'] == 'punct':
                punctuation_tags.append(tokens[k]['tag'])
                k += 1
                while k < token_count and tokens[k]['type'] == 'space':
                    k += 1

            if punctuation_tags and k < token_count and tokens[k]['type'] == 'word':
                _append_ipa_tag_cluster(out, punctuation_tags)
                i = k
                continue

            i += 1
            continue

        if token_type == 'space':
            j = i + 1
            while j < token_count and tokens[j]['type'] == 'space':
                j += 1
            if j < token_count and tokens[j]['type'] == 'punct':
                i += 1
                continue
            _append_ipa_pause(out)
            i += 1
            continue

        if token_type == 'linker':
            out.append(' ')
            i += 1
            continue

        if token_type == 'punct':
            punctuation_tags = [token['tag']]
            j = i + 1
            while j < token_count:
                next_type = tokens[j]['type']
                if next_type == 'space':
                    j += 1
                    continue
                if next_type == 'punct':
                    punctuation_tags.append(tokens[j]['tag'])
                    j += 1
                    continue
                break

            _append_ipa_tag_cluster(out, punctuation_tags)
            i = j
            continue

        out.append(token['text'])
        i += 1

    return ''.join(out)


def _append_non_word_char(out: list, char: str, mode: str) -> None:
    if mode == 'ipa':
        if char == ' ':
            _append_ipa_pause(out)
        elif char == WORD_LINKER_OUT:
            out.append(' ')
        else:
            tag, _ = _detect_ipa_tag(char, 0)
            if tag:
                _append_ipa_tag(out, tag)
            else:
                out.append(char)
        return

    out.append(char)


def _convert_mixed_bracket_part_ipa(part: str, ipa_mode: str = 'ipa-ob') -> str:
    """Convert IPA in mixed parts: emit [ ... ] content as escale tags, process outside text."""
    out = []
    current_word = []
    inside_brackets = False
    bracket_content = []

    def flush_word() -> None:
        if current_word:
            out.append(_convert_word(''.join(current_word), 'ipa', ipa_mode))
            current_word.clear()

    for char in part:
        if char == '[':
            flush_word()
            inside_brackets = True
            bracket_content = ['[']
            continue
        if char == ']':
            flush_word()
            if inside_brackets:
                bracket_content.append(']')
                _append_ipa_escape(out, ''.join(bracket_content))
                bracket_content = []
                inside_brackets = False
            else:
                out.append(char)
            continue

        if inside_brackets:
            bracket_content.append(char)
        elif _is_word_char(char):
            current_word.append(char)
        else:
            flush_word()
            _append_non_word_char(out, char, 'ipa')

    flush_word()
    return ''.join(out)


def convert_line(line: str, mode: str, ipa_mode: str = 'ipa-ob') -> str:
    """Convert one line to accent_acute, accent_bold, accent_ipa, or accent_xar format.
    
    Args:
        line: Input line in *_tilde format
        mode: 'acute', 'bold', 'ipa', or 'xar'
        ipa_mode: 'ipa-ob' (cleanup glottals for TTS) or 'ipa-strict' (preserve all IPA symbols)
    """
    if mode not in {'acute', 'bold', 'ipa', 'xar'}:
        raise ValueError("mode must be 'acute', 'bold', 'ipa' or 'xar'")

    had_newline = line.endswith('\n')
    core_line = line[:-1] if had_newline else line

    parts = split_by_brackets_level3(core_line)
    if len(parts) > 1:
        converted = []
        for part in parts:
            if '[' in part and ']' in part:
                if mode == 'ipa':
                    converted.append(_convert_mixed_bracket_part_ipa(part, ipa_mode))
                else:
                    converted.append(part)
            else:
                converted.append(_convert_non_bracket_part(part, mode, ipa_mode))
        result = ''.join(converted)
    else:
        result = _convert_non_bracket_part(core_line, mode, ipa_mode)

    if mode == 'ipa':
        result = _normalize_ipa_spacing(result)
        if had_newline and not re.search(r'\(\.\.\)\s*$', result):
            result = _normalize_ipa_spacing(result + ' ⟨linebreak⟩ (..)')
        if had_newline:
            result += '\n'
        return result

    if had_newline:
        result += '\n'
    return result


def convert_text(text: str) -> Tuple[str, str]:
    """Convert full text and return (accent_acute_text, accent_bold_markdown)."""
    acute_text, bold_text, _ = convert_text_with_ipa(text)
    return acute_text, bold_text


def convert_text_with_ipa(text: str, ipa_mode: str = 'ipa-ob') -> Tuple[str, str, str]:
    """Convert full text and return (accent_acute_text, accent_bold_text, accent_ipa_text).
    
    Args:
        text: Full text in *_tilde format
        ipa_mode: 'ipa-ob' (cleanup glottals for TTS) or 'ipa-strict' (preserve all IPA symbols)
    """
    acute_text, bold_text, ipa_text, _ = convert_text_with_ipa_xar(text, ipa_mode)
    return acute_text, bold_text, ipa_text


def convert_text_with_ipa_xar(text: str, ipa_mode: str = 'ipa-ob') -> Tuple[str, str, str, str]:
    """Convert full text and return (accent_acute_text, accent_bold_text, accent_ipa_text, accent_xar_text).
    
    Args:
        text: Full text in *_tilde format
        ipa_mode: 'ipa-ob' (cleanup glottals for TTS) or 'ipa-strict' (preserve all IPA symbols)
    """
    lines = text.splitlines(keepends=True)
    acute_lines = [convert_line(line, mode='acute', ipa_mode=ipa_mode) for line in lines]
    bold_lines = [convert_line(line, mode='bold', ipa_mode=ipa_mode) for line in lines]
    ipa_lines = [convert_line(line, mode='ipa', ipa_mode=ipa_mode) for line in lines]
    xar_lines = [convert_line(line, mode='xar', ipa_mode=ipa_mode) for line in lines]
    return ''.join(acute_lines), ''.join(bold_lines), ''.join(ipa_lines), ''.join(xar_lines)


def process_file(
    input_file: str,
    output_acute_file: str,
    output_bold_file: str,
    output_ipa_file: str = '',
    output_xar_file: str = '',
    write_acute: bool = True,
    write_bold: bool = True,
    write_ipa: bool = False,
    write_xar: bool = False,
    ipa_mode: str = 'ipa-ob',
) -> None:
    """Read *_tilde input and write selected output files.
    
    Args:
        input_file: Path to *_tilde.txt file
        output_acute_file: Path for accent_acute.txt output
        output_bold_file: Path for accent_bold.md output
        output_ipa_file: Path for accent_ipa.txt output
        output_xar_file: Path for accent_xar.txt output
        write_acute: Whether to write acute output
        write_bold: Whether to write bold output
        write_ipa: Whether to write IPA output
        write_xar: Whether to write XAR output
        ipa_mode: 'ipa-ob' (cleanup glottals for TTS) or 'ipa-strict' (preserve all IPA symbols)
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    acute_text, bold_text, ipa_text, xar_text = convert_text_with_ipa_xar(text, ipa_mode)

    if write_acute:
        Path(output_acute_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_acute_file, 'w', encoding='utf-8') as f:
            f.write(acute_text)

    if write_bold:
        Path(output_bold_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_bold_file, 'w', encoding='utf-8') as f:
            f.write(bold_text)

    if write_ipa:
        if not output_ipa_file:
            raise ValueError("output_ipa_file is required when write_ipa is True")
        Path(output_ipa_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_ipa_file, 'w', encoding='utf-8') as f:
            f.write(ipa_text)

    if write_xar:
        if not output_xar_file:
            raise ValueError("output_xar_file is required when write_xar is True")
        Path(output_xar_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_xar_file, 'w', encoding='utf-8') as f:
            f.write(xar_text)


def run_tests() -> bool:
    """Lightweight self-tests for conversion rules."""
    tests = [
        ("nû~", "acute", "nû´"),
        ("nû~", "bold", "**nû**"),
        ("nû~k", "acute", "nû´k"),
        ("nû~k", "bold", "**nûk**"),
        ("šar~·ri", "acute", "šar´ri"),
        ("šar~·ri", "bold", "**šar**ri"),
        ("k~a·pin", "acute", "k´apin"),
        ("k~a·pin", "bold", "**ka**pin"),
        ("k~a", "acute", "k´a"),
        ("k~a", "bold", "**ka**"),
        ("~a·pil", "acute", "´apil"),
        ("~a·pil", "bold", "**a**pil"),
        ("~a", "acute", "´a"),
        ("~a", "bold", "**a**"),
        ("nû~", "ipa", "ˈnuːː"),
        ("nû~k", "ipa", "ˈnuːːk"),
        ("šar~·ri", "ipa", "ˈʃarː.ri"),
        ("k~a·pin", "ipa", "ˈkːa.pin"),
        ("~a·pil", "ipa", "ˈʔːa.pil"),
        ("k~a", "ipa", "ˈkːa"),
        ("~a", "ipa", "ˈʔːa"),
        ("gi·mir+dad~·mē", "acute", "gimir‿dad´mē"),
        ("gi·mir+dad~·mē", "bold", "gimir‿**dad**mē"),
        ("gi·mir+dad~·mē", "ipa", "gi.mir ˈdadː.meː"),
        ("qa", "xar", "ꝗà"),
        ("qi", "xar", "ꝗì"),
        ("qu", "xar", "ꝗù"),
        ("qe", "xar", "ꝗè"),
        ("ṭa", "xar", "ꞓà"),
        ("ṣa", "xar", "ɉà"),
        ("ša", "xar", "x̌a"),
        ("ḥa", "xar", "ḫa"),
        ("ya", "xar", "ja"),
        ("ʿa", "xar", "a"),
        ("qā~", "xar", "ꝗàa´"),
        ("šar~", "xar", "x̌ar´"),
        ("q~a", "xar", "ꝗ´à"),
        ("ʾa ʿa", "xar", "a a"),
        ("ʾa", "xar", "a"),
        ("uʾa", "xar", "ua"),
        ("kūʾa", "xar", "kuaa"),
        ("baʾk", "xar", "beâk"),
        ("abʿd", "xar", "eâbd"),
        ("ʾka", "xar", "ka"),
        ("bakʾ", "xar", "beâk"),
        ("bākʾ", "xar", "baak"),
        ("biʾd", "xar", "beîd"),
        ("buʾd", "xar", "biûd"),
        ("beʾd", "xar", "baêd"),
        ("takʾ", "xar", "teâk"),
        ("tikʾ", "xar", "teîk"),
        ("tukʾ", "xar", "tiûk"),
        ("tekʾ", "xar", "taêk"),
        ("tīkʾ", "xar", "tiik"),
        ("bā", "xar", "baa"),
        ("bī", "xar", "bii"),
        ("bū", "xar", "buu"),
        ("bē", "xar", "bee"),
        ("bâ", "xar", "beâ"),
        ("bî", "xar", "beî"),
        ("bû", "xar", "biû"),
        ("bê", "xar", "baê"),
        ("qā", "xar", "ꝗàa"),
        ("qī", "xar", "ꝗìi"),
        ("qū", "xar", "ꝗùu"),
        ("qē", "xar", "ꝗèe"),
        ("qâ", "xar", "ꝗèâ"),
        ("qî", "xar", "ꝗèî"),
        ("qû", "xar", "ꝗìû"),
        ("qê", "xar", "ꝗàê"),
        ("qa", "ipa", "qɑ"),
        ("qi", "ipa", "qɨ"),
        ("qu", "ipa", "qʊ"),
        ("qe", "ipa", "qɛ"),
        ("ṭe", "ipa", "tˤɛ"),
        ("iṣ", "ipa", "ɨsˤ"),
        ("a", "ipa", "a"),
        ("i", "ipa", "i"),
        ("u", "ipa", "u"),
        ("e", "ipa", "e"),
        ("ā", "ipa", "aː"),
        ("ī", "ipa", "iː"),
        ("ū", "ipa", "uː"),
        ("ē", "ipa", "eː"),
        ("â", "ipa", "aː"),
        ("î", "ipa", "iː"),
        ("û", "ipa", "uː"),
        ("ê", "ipa", "eː"),
        ("ā~", "ipa", "ˈʔaːː"),
        ("ī~", "ipa", "ˈʔiːː"),
        ("ū~", "ipa", "ˈʔuːː"),
        ("ē~", "ipa", "ˈʔeːː"),
        ("â~", "ipa", "ˈʔaːː"),
        ("î~", "ipa", "ˈʔiːː"),
        ("û~", "ipa", "ˈʔuːː"),
        ("ê~", "ipa", "ˈʔeːː"),
        ("qa~", "ipa", "ˈqɑː"),
        ("qi~", "ipa", "ˈqɨː"),
        ("qu~", "ipa", "ˈqʊː"),
        ("qe~", "ipa", "ˈqɛː"),
        ("qā~", "ipa", "ˈqɑːː"),
        ("qī~", "ipa", "ˈqɨːː"),
        ("qū~", "ipa", "ˈqʊːː"),
        ("qē~", "ipa", "ˈqɛːː"),
        ("qâ~", "ipa", "ˈqɑːː"),
        ("qî~", "ipa", "ˈqɨːː"),
        ("qû~", "ipa", "ˈqʊːː"),
        ("qê~", "ipa", "ˈqɛːː"),
        ("ʾa", "ipa", "a"),
        ("ʿa", "ipa", "a"),
        ("ʾi", "ipa", "i"),
        ("ʿu", "ipa", "u"),
        ("ʿē", "ipa", "eː"),
        ("ʾ~a", "ipa", "ˈaː"),
        ("ʿ~a", "ipa", "ˈaː"),
        ("a+ē", "ipa", "a eː"),
        ("a-ē", "ipa", "a-eː"),
        ("ḫa", "ipa", "χa"),
        ("ḥa", "ipa", "χa"),
        ("ʿa+ʾi", "ipa", "a i"),
        ("ʾa-ʿi", "ipa", "a-i"),
        (
            "ana+se·bet·ti qar·rā~d lā+ša·nān — nan~·di·qā kak·kī·kun",
            "ipa",
            "ana se.bet.ti ⟨pause⟩ (.) qɑr.ˈraːːd ⟨pause⟩ (.) laː ʃa.naːn ⟨emdash⟩ (..) ˈnanː.dɨ.qɑː ⟨pause⟩ (.) kak.kiː.kun",
        ),
        (
            "ṣal·mā~t qaq·qa·di ana+šu·mut·ti — šum·qu·tu bū~l šak·kan",
            "ipa",
            "sˤɑl.ˈmaːːt ⟨pause⟩ (.) qɑq.qɑ.di ⟨pause⟩ (.) ana ʃu.mut.ti ⟨emdash⟩ (..) ʃum.qʊ.tu ⟨pause⟩ (.) ˈbuːːl ⟨pause⟩ (.) ʃak.kan",
        ),
        ("ba", "ipa", "ba"),
        ("bā", "ipa", "baː"),
        ("baq", "ipa", "bɑq"),
        ("qab", "ipa", "qɑb"),
        ("qaq", "ipa", "qɑq"),
        ("qā", "ipa", "qɑː"),
        ("ṭeṭ", "ipa", "tˤɛtˤ"),
        ("q~a", "ipa", "ˈqːɑ"),
        ("q~a", "acute", "q´a"),
        ("q~a", "bold", "**qa**"),
        ("~aq", "acute", "´aq"),
        ("~aq", "bold", "**aq**"),
        ("~aq", "ipa", "ˈʔːɑq"),
        ("qaq·qa·di", "ipa", "qɑq.qɑ.di"),
        ("ṣal·mā~t", "ipa", "sˤɑl.ˈmaːːt"),
        ("ḫaṭ~·ṭi", "ipa", "ˈχɑtˤː.tˤɨ"),
        ("qā·tā~·šu", "ipa", "qɑː.ˈtaːː.ʃu"),
        ("a·na+ē·kal·lim", "ipa", "a.na eː.kal.lim"),
        ("bēl-ē·riš", "ipa", "beːl-eː.riʃ"),
        ("šar gi·mir", "ipa", "ʃar ⟨pause⟩ (.) gi.mir"),
        ("šar, gi·mir", "ipa", "ʃar ⟨comma⟩ (..) gi.mir"),
        ("šar. gi·mir", "ipa", "ʃar ⟨period⟩ (..) gi.mir"),
        ("šar\n", "ipa", "ʃar ⟨linebreak⟩ (..)\n"),
        ("šar.\n", "ipa", "ʃar ⟨period⟩ (..) \n"),
        ("šar? gi·mir", "ipa", "ʃar ⟨question⟩ (..) gi.mir"),
        ("šar! gi·mir", "ipa", "ʃar ⟨exclamation⟩ (..) gi.mir"),
        ("šar: gi·mir", "ipa", "ʃar ⟨colon⟩ (..) gi.mir"),
        ("šar; gi·mir", "ipa", "ʃar ⟨semicolon⟩ (..) gi.mir"),
        ("šar—gi·mir", "ipa", "ʃar ⟨emdash⟩ (..) gi.mir"),
        ("šar–gi·mir", "ipa", "ʃar ⟨endash⟩ (..) gi.mir"),
        ("“šar,” gi·mir", "ipa", " ⟨opening-dblquote⟩ (..) ʃar ⟨comma⟩ ⟨closing-dblquote⟩ (..) gi.mir"),
        ("(šar) [gi·mir]", "ipa", " ⟨opening-parenthese⟩ (..) ʃar ⟨closing-parenthese⟩ (..) ⟨escape:[gi·mir]⟩ "),
        ("§ 42%", "ipa", " ⟨section⟩ ⟨number⟩ ⟨percent⟩ (..) "),
        ("šar... gi·mir", "ipa", "ʃar ⟨ellipsis⟩ (..) gi.mir"),
        ("šar… gi·mir", "ipa", "ʃar ⟨ellipsis⟩ (..) gi.mir"),
        ("123 gi·mir", "ipa", " ⟨number⟩ (..) gi.mir"),
        ("$€£", "ipa", " ⟨dollar⟩ ⟨euro⟩ ⟨pound⟩ (..) "),
        ("er~·ra", "acute", "er´ra"),
        ("er~·ra", "bold", "**er**ra"),
        ("nā~š", "bold", "**nāš**"),
        ("ša+ana+na·šê", "acute", "ša‿ana‿našê"),
        ("ī·ris·sū~-ma", "bold", "īris**sū**-ma"),
        ("šar [https://ex.am/ple+uri] gi·mir+dad~·mē", "bold", "šar [https://ex.am/ple+uri] gimir‿**dad**mē"),
        ("šar, 123 gi·mir+dad~·mē", "acute", "šar, 123 gimir‿dad´mē"),
    ]

    passed = 0
    for inp, mode, expected in tests:
        got = convert_line(inp, mode)
        if got == expected:
            passed += 1
        else:
            print(f"FAILED [{mode}]\n  in : {inp}\n  got: {got}\n  exp: {expected}")

    text_in = "šar [https://ex.am/ple+uri] gi·mir+dad~·mē\n~a·pil\n"
    expected_acute = "šar [https://ex.am/ple+uri] gimir‿dad´mē\n´apil\n"
    expected_bold = "šar [https://ex.am/ple+uri] gimir‿**dad**mē\n**a**pil\n"
    expected_ipa = "ʃar ⟨pause⟩ (.) ⟨escape:[https://ex.am/ple+uri]⟩ ⟨pause⟩ (.) gi.mir ˈdadː.meː ⟨linebreak⟩ (..)\nˈʔːa.pil ⟨linebreak⟩ (..)\n"
    expected_xar = "x̌ar [https://ex.am/ple+uri] gimir‿dad´mee\n´apil\n"
    got_acute, got_bold, got_ipa, got_xar = convert_text_with_ipa_xar(text_in)
    total_extra = 7
    extra_passed = 0

    if got_acute == expected_acute:
        extra_passed += 1
    else:
        print(
            "FAILED [convert_text acute]"
            f"\n  in : {text_in}"
            f"\n  got: {got_acute}"
            f"\n  exp: {expected_acute}"
        )

    if got_bold == expected_bold:
        extra_passed += 1
    else:
        print(
            "FAILED [convert_text bold]"
            f"\n  in : {text_in}"
            f"\n  got: {got_bold}"
            f"\n  exp: {expected_bold}"
        )

    if got_ipa == expected_ipa:
        extra_passed += 1
    else:
        print(
            "FAILED [convert_text ipa]"
            f"\n  in : {text_in}"
            f"\n  got: {got_ipa}"
            f"\n  exp: {expected_ipa}"
        )

    if got_xar == expected_xar:
        extra_passed += 1
    else:
        print(
            "FAILED [convert_text xar]"
            f"\n  in : {text_in}"
            f"\n  got: {got_xar}"
            f"\n  exp: {expected_xar}"
        )

    forbidden_ipa = {'ħ', 'ʕ'}
    ipa_inventory_ok = True
    for inp, mode, _ in tests:
        if mode != 'ipa':
            continue
        ipa_out = convert_line(inp, 'ipa')
        bad = sorted(ch for ch in forbidden_ipa if ch in ipa_out)
        if bad:
            ipa_inventory_ok = False
            print(
                "FAILED [ipa inventory]"
                f"\n  in : {inp}"
                f"\n  got: {ipa_out}"
                f"\n  forbidden: {''.join(bad)}"
            )

    if ipa_inventory_ok:
        extra_passed += 1

    text_inventory_ok = not any(ch in got_ipa for ch in forbidden_ipa)
    if text_inventory_ok:
        extra_passed += 1
    else:
        print(
            "FAILED [convert_text ipa inventory]"
            f"\n  in : {text_in}"
            f"\n  got: {got_ipa}"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = Path(tmpdir) / "sample_tilde.txt"
        out_acute = Path(tmpdir) / "sample_accent_acute.txt"
        out_bold = Path(tmpdir) / "sample_accent_bold.md"
        out_ipa = Path(tmpdir) / "sample_accent_ipa.txt"
        in_path.write_text("k~a·pin + ~a·pil", encoding='utf-8')

        process_file(
            input_file=str(in_path),
            output_acute_file=str(out_acute),
            output_bold_file=str(out_bold),
            output_ipa_file=str(out_ipa),
            write_acute=True,
            write_bold=False,
            write_ipa=True,
        )

        file_ok = (
            out_acute.exists()
            and out_acute.read_text(encoding='utf-8') == "k´apin ‿ ´apil"
            and out_ipa.exists()
            and out_ipa.read_text(encoding='utf-8') == "ˈkːa.pin ⟨pause⟩ (.) ⟨pause⟩ (.) ˈʔːa.pil"
            and not out_bold.exists()
        )
        if file_ok:
            extra_passed += 1
        else:
            print(
                "FAILED [process_file selective write]"
                f"\n  acute_exists: {out_acute.exists()}"
                f"\n  acute_text: {out_acute.read_text(encoding='utf-8') if out_acute.exists() else ''}"
                f"\n  ipa_exists: {out_ipa.exists()}"
                f"\n  ipa_text: {out_ipa.read_text(encoding='utf-8') if out_ipa.exists() else ''}"
                f"\n  bold_exists: {out_bold.exists()}"
            )

    # IPA mode switch checks: ipa-ob vs ipa-strict.
    ipa_mode_cases = [
        ("ʾa", "a", "ʔa"),
        ("ʿa", "a", "ʔa"),
        ("ʾ~a", "ˈaː", "ˈʔːa"),
        ("ʿa+ʾi", "a i", "ʔa ʔi"),
    ]

    for inp, exp_ob, exp_strict in ipa_mode_cases:
        got_ob = convert_line(inp, 'ipa', ipa_mode='ipa-ob')
        if got_ob == exp_ob:
            extra_passed += 1
        else:
            print(
                "FAILED [ipa mode ob]"
                f"\n  in : {inp}"
                f"\n  got: {got_ob}"
                f"\n  exp: {exp_ob}"
            )

        got_strict = convert_line(inp, 'ipa', ipa_mode='ipa-strict')
        if got_strict == exp_strict:
            extra_passed += 1
        else:
            print(
                "FAILED [ipa mode strict]"
                f"\n  in : {inp}"
                f"\n  got: {got_strict}"
                f"\n  exp: {exp_strict}"
            )

    _, _, got_ipa_ob, _ = convert_text_with_ipa_xar("ʾa ʿa\n", ipa_mode='ipa-ob')
    if got_ipa_ob == "a ⟨pause⟩ (.) a ⟨linebreak⟩ (..)\n":
        extra_passed += 1
    else:
        print(
            "FAILED [convert_text ipa mode ob]"
            f"\n  got: {got_ipa_ob}"
            "\n  exp: a ⟨pause⟩ (.) a ⟨linebreak⟩ (..)"
        )

    _, _, got_ipa_strict, _ = convert_text_with_ipa_xar("ʾa ʿa\n", ipa_mode='ipa-strict')
    if got_ipa_strict == "ʔa ⟨pause⟩ (.) ʔa ⟨linebreak⟩ (..)\n":
        extra_passed += 1
    else:
        print(
            "FAILED [convert_text ipa mode strict]"
            f"\n  got: {got_ipa_strict}"
            "\n  exp: ʔa ⟨pause⟩ (.) ʔa ⟨linebreak⟩ (..)"
        )

    total_extra += (len(ipa_mode_cases) * 2) + 2
    total = len(tests) + total_extra
    passed += extra_passed
    print(f"print.py tests: {passed}/{total} passed")
    return passed == total
