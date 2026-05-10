"""
Akkadian Prosody Toolkit — Accent Printer IPA/Text Rendering

Internal submodule for IPA rendering, transliteration, accent markup,
and text conversion. Imported by print.py (facade) and _print_pho.py.
"""

import logging
import re
import unicodedata
from pathlib import Path
from typing import Tuple

from akkapros.lib.constants import (
    SYL_SEPARATOR,
    WORD_LINKER,
    INTERNAL_WORD_LINKER,
    MERGE_LINKERS,
    DIPH_SEPARATOR,
    HIATUS_MARKER,
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    OPEN_ESCAPE,
    CLOSE_ESCAPE,
    OPEN_PRESERVE,
    CLOSE_PRESERVE,
    TAG_PRESERVE_RE,
)
from akkapros.lib.syllabify import split_by_escape_segments
from akkapros.lib.utils import (
    format_selftest_label,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
)

ACUTE_MARK = '´'
WORD_LINKER_OUT = '‿'
TILDE = '~'
HYPHEN = '-'
IPA_LENGTH = 'ː'
IPA_STRESS = 'ˈ'
GLOTTAL_STOP = 'ʾ'
IPA_PROSODY_WEAK = '|'
IPA_PROSODY_STRONG = '‖'

ALL_VOWELS = set('aeiuāēīûâêîû')
EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}

# The phonetizer already handles the preserve/replace distinction via
# replace_proto_semitic. The printer uses a single IPA mapping that
# directly translates realization codes to IPA symbols.
IPA_MAP = {
    'b': 'b', 'd': 'd', 'g': 'g', 'k': 'k', 'p': 'p',
    'q': 'q', 'ṭ': 'tˤ', 'ṣ': 'sˤ', 'š': 'ʃ',
    's': 's', 'z': 'z', 'l': 'l', 'm': 'm', 'n': 'n',
    'r': 'r', 'ḥ': 'ʔ', 'ḫ': 'χ', 'ʿ': 'ʔ', 'ʾ': 'ʔ',
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
    'r': 'r', 'ḥ': "'", 'ḫ': 'ḫ', 'ʿ': "'", 'ʾ': "'",
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


def _render_visible_merge_connector(text: str, *, print_merger: bool) -> str:
    """Render visible merge connectors per output policy."""
    if print_merger:
        return text
    return re.sub(r'\s*' + re.escape(WORD_LINKER_OUT) + r'\s*', ' ', text)


def _insert_glottal_stops(word: str) -> str:
    """Insert ʾ before vowel-initial segments (start, after +, after -)."""
    out = []

    for idx, char in enumerate(word):
        if char == HIATUS_MARKER:
            out.append(GLOTTAL_STOP)
            continue
        boundary = idx == 0 or word[idx - 1] in MERGE_LINKERS | {HYPHEN}
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
        if char == HIATUS_MARKER:
            out.append(GLOTTAL_STOP)
            out_indices.append(-1)
            continue
        boundary = idx == 0 or word[idx - 1] in MERGE_LINKERS | {HYPHEN}
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
    """Fallback text-context emphatic check for standalone text conversion."""
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
    return left in EMPHATIC_CONSONANTS


def _row_vowel_is_emphatic(row: dict[str, str]) -> bool:
    return row['category'] == 'V' and row['realization'] in {'AO', 'EO', 'IO', 'UO'}


def _to_ipa_vowel(vowel: str, emphatic_context: bool) -> str:
    if emphatic_context:
        return IPA_VOWELS_EMPHATIC.get(vowel, vowel)
    return IPA_VOWELS_DEFAULT.get(vowel, vowel)


def _to_xar_vowel(vowel: str, emphatic_context: bool) -> str:
    if emphatic_context:
        return XAR_VOWELS_EMPHATIC.get(vowel, vowel)
    return XAR_VOWELS_DEFAULT.get(vowel, vowel)


def _convert_word_xar(word: str, emphatic_by_source_index: dict[int, bool] | None = None) -> str:
    """Convert one Akkadian word token to XAR with ordered transforms."""
    emphatic_flags = []
    for idx, char in enumerate(word):
        if char in ALL_VOWELS:
            if emphatic_by_source_index is not None and idx in emphatic_by_source_index:
                emphatic_flags.append(emphatic_by_source_index[idx])
            else:
                emphatic_flags.append(_is_emphatic_adjacent(word, idx, {TILDE, SYL_SEPARATOR, DIPH_SEPARATOR}))

    step = ''.join(XAR_CONSONANT_MAP.get(char, char) for char in word)

    out = []
    vowel_idx = 0
    for char in step:
        if char in ALL_VOWELS:
            emphatic_context = emphatic_flags[vowel_idx] if vowel_idx < len(emphatic_flags) else False
            out.append(_to_xar_vowel(char, emphatic_context))
            vowel_idx += 1
        elif char in MERGE_LINKERS:
            out.append(WORD_LINKER_OUT)
        elif char == SYL_SEPARATOR:
            continue
        elif char == DIPH_SEPARATOR:
            continue
        elif char == HIATUS_MARKER:
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


def _is_strong_ipa_tag(tag: str) -> bool:
    return tag in {'period', 'question', 'exclamation', 'linebreak'}


def _append_ipa_tag_cluster(out: list, tags: list) -> None:
    for tag in tags:
        _append_ipa_tag(out, tag)
    if tags:
        marker = IPA_PROSODY_STRONG if any(_is_strong_ipa_tag(t) for t in tags) else IPA_PROSODY_WEAK
        out.append(f' {marker} ')


def _append_ipa_escape(out: list, escaped_text: str) -> None:
    out.append(f' ⟨escape:{escaped_text}⟩ ')


def _normalize_ipa_spacing(text: str) -> str:
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\s*\.\s*', '.', text)
    text = re.sub(r'\.{2,}', '.', text)
    return text.strip()


def _flush_syllable(
    syllable_text: str,
    mode: str,
    source_text: str = '',
    source_indices=None,
    emphatic_by_source_index: dict[int, bool] | None = None,
    ipa_ultraheavy_hiatus: bool = False,
) -> str:
    if not syllable_text:
        return ''

    if mode == 'acute':
        return syllable_text.replace(HIATUS_MARKER, '').replace(TILDE, ACUTE_MARK)

    if mode == 'ipa':
        accentuated = TILDE in syllable_text
        converted = []
        ipa_map = IPA_MAP

        context_text = source_text if source_text else syllable_text
        context_skip_chars = {TILDE, SYL_SEPARATOR, DIPH_SEPARATOR} if source_text else {TILDE}

        for idx, char in enumerate(syllable_text):
            if char in ALL_VOWELS:
                context_index = source_indices[idx] if source_indices else idx
                if (
                    emphatic_by_source_index is not None
                    and context_index >= 0
                    and context_index in emphatic_by_source_index
                ):
                    emphatic = emphatic_by_source_index[context_index]
                else:
                    emphatic = _is_emphatic_adjacent(context_text, context_index, context_skip_chars)
                if ipa_ultraheavy_hiatus and char in {'â', 'î', 'û', 'ê'}:
                    short_base = {
                        'â': 'a',
                        'î': 'i',
                        'û': 'u',
                        'ê': 'e',
                    }[char]
                    converted.append(_to_ipa_vowel(short_base, emphatic))
                    converted.append('.')
                    converted.append(_to_ipa_vowel(short_base, emphatic))
                else:
                    converted.append(_to_ipa_vowel(char, emphatic))
            elif char in ipa_map:
                if (
                    char == GLOTTAL_STOP
                    and source_indices is not None
                    and source_indices[idx] == -1
                    and not accentuated
                ):
                    continue
                converted.append(ipa_map[char])
            elif char == HIATUS_MARKER:
                continue
            elif char == TILDE:
                converted.append(IPA_LENGTH)
            else:
                converted.append(char)

        ipa_syllable = ''.join(converted)
        if accentuated and ipa_syllable:
            ipa_syllable = re.sub(r'^ː+(ʔ)([aeiouɑɨʊɛ])(.*)$',
                                  r'\1\2' + IPA_LENGTH + r'\3', ipa_syllable)
            ipa_syllable = re.sub(r'^ː+([aeiouɑɨʊɛ])(.*)$',
                                  r'\1' + IPA_LENGTH + r'\2', ipa_syllable)
            return f"{IPA_STRESS}{ipa_syllable}"
        return ipa_syllable

    if mode == 'xar':
        converted = []

        context_text = source_text if source_text else syllable_text
        context_skip_chars = {TILDE, SYL_SEPARATOR, DIPH_SEPARATOR} if source_text else {TILDE}

        for idx, char in enumerate(syllable_text):
            if char in ALL_VOWELS:
                context_index = source_indices[idx] if source_indices else idx
                if (
                    emphatic_by_source_index is not None
                    and context_index >= 0
                    and context_index in emphatic_by_source_index
                ):
                    emphatic = emphatic_by_source_index[context_index]
                else:
                    emphatic = _is_emphatic_adjacent(context_text, context_index, context_skip_chars)
                converted.append(
                    _to_xar_vowel(
                        char,
                        emphatic,
                    )
                )
            elif char in XAR_CONSONANT_MAP:
                converted.append(XAR_CONSONANT_MAP[char])
            elif char == HIATUS_MARKER:
                continue
            elif char == TILDE:
                converted.append(ACUTE_MARK)
            else:
                converted.append(char)

        return ''.join(converted)

    clean = syllable_text.replace(HIATUS_MARKER, '').replace(TILDE, '')
    if TILDE in syllable_text and clean:
        return f"**{clean}**"
    return clean


def _convert_word(
    word: str,
    mode: str,
    ipa_ultraheavy_hiatus: bool = False,
    emphatic_by_source_index: dict[int, bool] | None = None,
) -> str:
    """Convert one Akkadian word token."""
    if mode == 'xar':
        return _convert_word_xar(word, emphatic_by_source_index=emphatic_by_source_index)

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
                    emphatic_by_source_index=emphatic_by_source_index,
                    ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
                )
            )
            current_syllable.clear()
            current_indices.clear()

    for idx, char in enumerate(word):
        if char in MERGE_LINKERS:
            flush_current()
            if mode == 'ipa':
                out.append('.')
            elif mode == 'mbrola':
                out.append(' ')
            else:
                out.append(WORD_LINKER_OUT)
        elif char == TILDE:
            current_syllable.append(char)
            current_indices.append(idx)
        elif char in {SYL_SEPARATOR, DIPH_SEPARATOR}:
            flush_current()
            if mode == 'ipa':
                out.append('.')
            elif mode == 'mbrola':
                out.append(' ')
        elif char == HYPHEN:
            flush_current()
            out.append(HYPHEN)
        else:
            current_syllable.append(char)
            current_indices.append(idx)

    flush_current()
    return ''.join(out)


def _is_word_char(char: str) -> bool:
    """Return True for characters that belong to processable Akkadian word chunks."""
    if char in AKKADIAN_VOWELS or char in AKKADIAN_CONSONANTS or char in ALL_VOWELS:
        return True
    return char in MERGE_LINKERS | {SYL_SEPARATOR, HYPHEN, TILDE}


def _convert_non_bracket_part(
    part: str,
    mode: str,
    ipa_ultraheavy_hiatus: bool = False,
    emphatic_by_source_index: dict[int, bool] | None = None,
    source_offset: int = 0,
) -> str:
    """Convert a string part that is outside square brackets."""
    if mode == 'ipa':
        return _convert_non_bracket_part_ipa(
            part,
            ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
            emphatic_by_source_index=emphatic_by_source_index,
            source_offset=source_offset,
        )

    out = []
    current_word = []
    current_start: int | None = None

    def flush_word() -> None:
        nonlocal current_start
        if current_word:
            word_map = None
            if emphatic_by_source_index is not None and current_start is not None:
                word_map = {
                    index - current_start: value
                    for index, value in emphatic_by_source_index.items()
                    if current_start <= index < current_start + len(current_word)
                }
            out.append(
                _convert_word(
                    ''.join(current_word),
                    mode,
                    ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
                    emphatic_by_source_index=word_map,
                )
            )
            current_word.clear()
            current_start = None

    for index, char in enumerate(part):
        if _is_word_char(char):
            if current_start is None:
                current_start = source_offset + index
            current_word.append(char)
        else:
            flush_word()
            _append_non_word_char(out, char, mode)

    flush_word()
    return ''.join(out)


def _convert_non_bracket_part_ipa(
    part: str,
    ipa_ultraheavy_hiatus: bool = False,
    emphatic_by_source_index: dict[int, bool] | None = None,
    source_offset: int = 0,
) -> str:
    tokens = []
    index = 0

    while index < len(part):
        char = part[index]
        if _is_word_char(char):
            start = index
            while index < len(part) and _is_word_char(part[index]):
                index += 1
            tokens.append({'type': 'word', 'text': part[start:index], 'start': start, 'end': index})
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
            word_map = None
            if emphatic_by_source_index is not None:
                absolute_start = source_offset + token['start']
                absolute_end = source_offset + token['end']
                word_map = {
                    index - absolute_start: value
                    for index, value in emphatic_by_source_index.items()
                    if absolute_start <= index < absolute_end
                }
            out.append(
                _convert_word(
                    token['text'],
                    'ipa',
                    ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
                    emphatic_by_source_index=word_map,
                )
            )

            j = i + 1
            while j < token_count and tokens[j]['type'] in {'space', 'linker'}:
                j += 1

            punct_tags = []
            k = j
            while k < token_count and tokens[k]['type'] == 'punct':
                punct_tags.append(tokens[k]['tag'])
                k += 1
                while k < token_count and tokens[k]['type'] in {'space', 'linker'}:
                    k += 1

            if punct_tags:
                _append_ipa_tag_cluster(out, punct_tags)
                i = k
                continue

            if j < token_count and tokens[j]['type'] == 'word':
                out.append('.')
                i = j
                continue

            i += 1
            continue

        if token_type in {'space', 'linker'}:
            i += 1
            continue

        if token_type == 'punct':
            punct_tags = [token['tag']]
            j = i + 1
            while j < token_count:
                next_type = tokens[j]['type']
                if next_type in {'space', 'linker'}:
                    j += 1
                    continue
                if next_type == 'punct':
                    punct_tags.append(tokens[j]['tag'])
                    j += 1
                    continue
                break
            _append_ipa_tag_cluster(out, punct_tags)
            i = j
            continue

        out.append(token['text'])
        i += 1

    return ''.join(out)


def _append_non_word_char(out: list, char: str, mode: str) -> None:
    if mode == 'ipa':
        if char == ' ':
            return
        elif char == WORD_LINKER_OUT:
            return
        else:
            tag, _ = _detect_ipa_tag(char, 0)
            if tag:
                _append_ipa_tag_cluster(out, [tag])
            else:
                out.append(char)
        return

    out.append(char)


def _is_escape_segment(segment: str) -> bool:
    """Return True when segment matches one supported CR-005 escape form."""
    if segment.startswith(OPEN_PRESERVE) and segment.endswith(CLOSE_PRESERVE):
        return True
    if re.fullmatch(rf'\{{{TAG_PRESERVE_RE}\{{[^{{}}]*\}}\}}', segment):
        return True
    return False


def _convert_escape_segment(segment: str, mode: str) -> str:
    """Convert one recognized escape segment for a target mode."""
    if mode == 'ipa':
        out = []
        _append_ipa_escape(out, segment)
        return ''.join(out)
    return segment


def _dearmor_pivot_punctuation(text: str) -> str:
    """Restore visible punctuation from armored _tilde chunks for rendering only."""
    return re.sub(
        re.escape(OPEN_ESCAPE) + r'(.*?)' + re.escape(CLOSE_ESCAPE),
        lambda match: match.group(1),
        text,
    )


def convert_line(
    line: str,
    mode: str,
    ipa_ultraheavy_hiatus: bool = False,
    print_merger: bool = False,
    emphatic_by_source_index: dict[int, bool] | None = None,
) -> str:
    """Convert one line to accent_acute, accent_bold, accent_ipa, or accent_xar format."""
    if mode not in {'acute', 'bold', 'ipa', 'xar'}:
        raise ValueError("mode must be 'acute', 'bold', 'ipa', or 'xar'")

    had_newline = line.endswith('\n')
    core_line = line[:-1] if had_newline else line
    core_line = _dearmor_pivot_punctuation(core_line)

    parts = split_by_escape_segments(core_line)
    if len(parts) > 1 or (parts and parts[0][0]):
        converted = []
        source_offset = 0
        for is_escape, part in parts:
            if is_escape and _is_escape_segment(part):
                converted.append(_convert_escape_segment(part, mode))
            else:
                converted.append(
                    _convert_non_bracket_part(
                        part,
                        mode,
                        ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
                        emphatic_by_source_index=emphatic_by_source_index,
                        source_offset=source_offset,
                    )
                )
            source_offset += len(part)
        result = ''.join(converted)
    else:
        result = _convert_non_bracket_part(
            core_line,
            mode,
            ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
            emphatic_by_source_index=emphatic_by_source_index,
        )

    if mode == 'ipa':
        result = _normalize_ipa_spacing(result)
        if had_newline and not re.search(rf'{IPA_PROSODY_STRONG}\s*$', result):
            result = _normalize_ipa_spacing(result + ' ⟨linebreak⟩ ‖')
        if had_newline:
            result += '\n'
        return result

    if mode in {'acute', 'bold', 'xar'}:
        result = _render_visible_merge_connector(result, print_merger=print_merger)

    if had_newline:
        result += '\n'
    return result


def convert_text(text: str, print_merger: bool = False) -> Tuple[str, str]:
    """Convert full text and return (accent_acute_text, accent_bold_markdown)."""
    acute_text, bold_text, _ = convert_text_with_ipa(text, print_merger=print_merger)
    return acute_text, bold_text


def convert_text_with_ipa(
    text: str,
    ipa_ultraheavy_hiatus: bool = False,
    print_merger: bool = False,
) -> Tuple[str, str, str]:
    """Convert full text and return (accent_acute_text, accent_bold_text, accent_ipa_text)."""
    acute_text, bold_text, ipa_text, _ = convert_text_with_ipa_xar(
        text,
        ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
        print_merger=print_merger,
    )
    return acute_text, bold_text, ipa_text


def convert_text_with_ipa_xar(
    text: str,
    ipa_ultraheavy_hiatus: bool = False,
    print_merger: bool = False,
) -> Tuple[str, str, str, str]:
    """Convert full text and return (accent_acute_text, accent_bold_text, accent_ipa_text, accent_xar_text)."""
    lines = text.splitlines(keepends=True)
    acute_lines = [
        convert_line(line, mode='acute', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=print_merger)
        for line in lines
    ]
    bold_lines = _convert_bold_markdown_lines(
        lines,
        ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
        print_merger=print_merger,
    )
    ipa_lines = [convert_line(line, mode='ipa', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus) for line in lines]
    xar_lines = [
        convert_line(line, mode='xar', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=print_merger)
        for line in lines
    ]
    return ''.join(acute_lines), ''.join(bold_lines), ''.join(ipa_lines), ''.join(xar_lines)


def _convert_bold_markdown_lines(
    lines: list[str],
    ipa_ultraheavy_hiatus: bool = False,
    print_merger: bool = False,
) -> list[str]:
    """Convert lines to bold Markdown and preserve non-blank lineation for renderers."""
    bold_lines = [
        convert_line(line, mode='bold', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=print_merger)
        for line in lines
    ]
    return _preserve_markdown_lineation(bold_lines)


def _preserve_markdown_lineation(lines: list[str]) -> list[str]:
    rendered_lines = list(lines)

    for index, rendered in enumerate(rendered_lines[:-1]):
        current_line = rendered[:-1] if rendered.endswith('\n') else rendered
        next_line = rendered_lines[index + 1][:-1] if rendered_lines[index + 1].endswith('\n') else rendered_lines[index + 1]
        if rendered.endswith('\n') and current_line and next_line:
            rendered_lines[index] = current_line + '\\' + '\n'

    return rendered_lines
