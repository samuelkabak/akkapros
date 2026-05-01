from __future__ import annotations

import math
import re
from typing import Any

from akkapros.lib import constants as lib_constants
from akkapros.lib.constants import (
    CLOSE_ESCAPE,
    HIATUS_MARKER,
    OPEN_ESCAPE,
    SYL_SEPARATOR,
    WORD_LINKER,
)
from akkapros.lib.frontmatter import resolve_inherited_punctuation_options
from akkapros.lib.utils import compile_contextual_regex
from akkapros.lib._phonetize_config import (
    ACCENTUATION_DISTRIBUTION_CHOICES,
    ACCENTUATION_DISTRIBUTION_SHARES,
    PHONETIZE_SECTION,
    PHONETIZE_SECTION_HELP,
    PHONETIZE_SCHEMA,
    PROCESS_KEYS,
    PhonetizeField,
    PhonetizeVerificationResult,
    VerificationIssue,
    _derive_effective_durations,
    _field,
    _is_field,
    _iter_numeric_leaves,
    _make_issue,
    _merge_phonetize_config,
    _nearest_multiple_gap,
    _normalize_intonation_token,
    _resolve_mora_mode,
    _resolve_synchronization_basis,
    _round_sync_precision,
    _runtime_intonation_config,
    _runtime_view_phonetize_config,
    _scale_duration_values,
    _supported_synchronization_bases,
    apply_timing_override,
    build_default_phonetize_config,
    build_default_phonetize_verification_config,
    get_phonetize_field,
    get_relative_value,
    iter_phonetize_fields,
    normalize_phonetize_config,
    render_documented_phonetize_section,
    render_phonetize_verification_lines,
    set_relative_value,
    validate_phonetize_source,
    verify_phonetize_config,
)
from akkapros.lib.tests.phonetize_tests import run_tests

PHONE_ROW_FIELDS = (
    'label',
    'category',
    'type',
    'length',
    'position',
    'boundary',
    'accent',
    'realization',
    'duration',
    'drift',
    'intonation',
    'text',
)
EOL_TEXT = '<EOL>'
RESYNC_PAUSE_LABEL = 'MEN'
RESYNC_PAUSE_TYPE = 'M'
RESYNC_PAUSE_REALIZATION = 'MP'
RESYNC_PAUSE_TEXT = ' '


def _is_resync_pause_row(row: dict[str, str]) -> bool:
    return (
        row['category'] == 'S'
        and row['label'] == RESYNC_PAUSE_LABEL
        and row['type'] == RESYNC_PAUSE_TYPE
        and row['realization'] == RESYNC_PAUSE_REALIZATION
    )


def _pause_row_triggers_final_anchors(row: dict[str, str] | None) -> bool:
    return bool(
        row
        and row['category'] == 'S'
        and not _is_resync_pause_row(row)
        and row['length'] in {'S', 'L'}
    )


def serialize_mbrola_rows(rows: list[dict[str, str]], phonetize_config: dict[str, object] | None = None, *, accentuated: bool) -> str:
    return '\n'.join(
        ' '.join([symbol, str(duration)] + [str(target) for target in targets])
        for symbol, duration, targets in _mbrola_rows(rows, phonetize_config, accentuated=accentuated)
    ) + '\n'


def serialize_phone_row(row: dict[str, str]) -> str:
    return '|'.join(row[field] for field in PHONE_ROW_FIELDS)


def serialize_phone_rows(rows: list[dict[str, str]]) -> str:
    return '\n'.join(serialize_phone_row(row) for row in rows) + '\n'


def parse_phone_row(line: str) -> dict[str, str]:
    stripped = line.rstrip('\r\n')
    if not stripped:
        raise ValueError('Phone row is empty')
    parts = stripped.split('|', len(PHONE_ROW_FIELDS) - 1)
    if len(parts) != len(PHONE_ROW_FIELDS):
        raise ValueError(f'Invalid phone row: {line!r}')
    if not re.fullmatch(r'\d{4}', parts[8]):
        raise ValueError(f'Invalid phone row duration token: {parts[8]!r}')
    if not re.fullmatch(r'[+-]\d{3}', parts[9]):
        raise ValueError(f'Invalid phone row drift token: {parts[9]!r}')
    if not re.fullmatch(r'[HLMRFPV][0-9][CLE]', parts[10]):
        raise ValueError(f'Invalid phone row intonation token: {parts[10]!r}')
    return dict(zip(PHONE_ROW_FIELDS, parts))


def reconstruct_tilde_from_phone_rows(rows: list[dict[str, str]]) -> str:
    pieces: list[str] = []
    previous_boundary = ''
    for row in rows:
        if row['category'] != 'S' and previous_boundary == 'F':
            pieces.append(' ')
        if row['category'] == 'S':
            if row['text'] and set(row['text'].replace(EOL_TEXT, '')) == set() and EOL_TEXT in row['text']:
                pieces.append('\n' * row['text'].count(EOL_TEXT))
                previous_boundary = ''
            elif not _is_resync_pause_row(row):
                pieces.append(row['text'])
                previous_boundary = ''
            continue
        pieces.append(row['text'])
        if row['accent'] == 'A':
            pieces.append('~')
        boundary = row['boundary']
        if boundary == 'I':
            pieces.append(SYL_SEPARATOR)
        elif boundary == 'E':
            pieces.append('-')
        elif boundary == 'L':
            pieces.append('&')
        elif boundary == 'X':
            pieces.append(WORD_LINKER)
        previous_boundary = boundary
    return ''.join(pieces)

PHONE_ROW_DURATION_PLACEHOLDER = '0000'
PHONE_ROW_DRIFT_NEUTRAL = '+000'
PHONE_ROW_INTONATION_NEUTRAL = 'M0C'
INNER_PUNCT_TEXT = ':inner-punct:'
PHRASAL_PUNCT_TEXT = ':phrasal-punct:'

CONSONANT_HIATUS = set('˙')
CONSONANT_VOWEL_TRANSITION = set('¨')
CONSONANT_CLOSURE = set('bdgkptṭqʾ')
CONSONANT_FRICATIVE = set('szšṣḥḫʿ')
CONSONANT_SONORANT = set('lrmnwy')
EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}
EMPHATIC_COLORING_BLOCKERS = {'t', 's', 'k'}

SHORT_VOWELS = set('aeiu')
LONG_VOWELS = set('āēīūâêîû')
LOW_VOWELS = set('aāâ')
MID_VOWELS = set('eēê')
HIGH_VOWELS = set('iuīūîû')

SHORT_PAUSE_PUNCTUATION_CHARS = {',', ';', ':', '—', '–', '…', '(', ')', '«', '»', '“', '”', '‘', '’', '"', "'", '/', '\\', '|', '†', '‡'}
LONG_PAUSE_PUNCTUATION_CHARS = {'.', '?', '!', '[', ']', '{', '}', '<', '>', '*', '#'}
INTERNAL_MERGE_CHARS = {'&', '_'}
DEFAULT_SHORT_PAUSE_PUNCTUATION_PATTERNS: tuple[str, ...] = ()
DEFAULT_LONG_PAUSE_PUNCTUATION_PATTERNS: tuple[str, ...] = ()
PRIMARY_CONTINUATION_PUNCTUATION_CHARS = {',', ';', ':', '—', '–', '…'}
QUESTION_PUNCTUATION_CHARS = {'?'}
EXCLAMATION_PUNCTUATION_CHARS = {'!'}
STATEMENT_PUNCTUATION_CHARS = {'.'}
PAUSE_TYPE_TO_INTONATION_KEY = {
    'Q': 'question',
    'S': 'statement',
    'E': 'exclamation',
    'C': 'continuation',
}

INPUT_CHARACTER_ROWS = (
    ('b', 'BET', 'S'),
    ('d', 'DAL', 'S'),
    ('g', 'GIM', 'S'),
    ('k', 'KAP', 'S'),
    ('p', 'PAY', 'S'),
    ('ṭ', 'TUT', 'S'),
    ('q', 'QUP', 'S'),
    ('ṣ', 'SUD', 'S'),
    ('s', 'SAM', 'S'),
    ('z', 'ZIN', 'S'),
    ('š', 'SIN', 'S'),
    ('l', 'LAM', 'S'),
    ('m', 'MIM', 'S'),
    ('n', 'NAN', 'S'),
    ('r', 'RES', 'S'),
    ('ḥ', 'ETE', 'S'),
    ('ḫ', 'HET', 'S'),
    ('ʿ', 'AIN', 'S'),
    ('ʾ', 'ALE', 'S'),
    ('w', 'WAW', 'S'),
    ('y', 'YID', 'S'),
    ('t', 'TAW', 'S'),
    (HIATUS_MARKER, 'ARU', 'S'),
    ('¨', 'ENA', 'S'),
    ('a', 'AYA', 'S'),
    ('e', 'EYA', 'S'),
    ('i', 'IYA', 'S'),
    ('u', 'UYA', 'S'),
    ('ā', 'AWA', 'L'),
    ('ē', 'EWA', 'L'),
    ('ī', 'IWA', 'L'),
    ('ū', 'UWA', 'L'),
    ('â', 'AWI', 'L'),
    ('ê', 'EWI', 'L'),
    ('î', 'IWI', 'L'),
    ('û', 'UWI', 'L'),
    (INNER_PUNCT_TEXT, 'SES', 'S'),
    (PHRASAL_PUNCT_TEXT, 'ZEN', 'L'),
)

INPUT_CHARACTER_LABELS = {text: label for text, label, _length in INPUT_CHARACTER_ROWS}
INPUT_CHARACTER_LENGTHS = {text: length for text, _label, length in INPUT_CHARACTER_ROWS}

REALIZATION_CODE_ROWS = (
    ('BE', 'b', 'b', 'C', 'C', 'P'),
    ('DA', 'd', 'd', 'C', 'C', 'P'),
    ('GI', 'ɡ', 'g', 'C', 'C', 'P'),
    ('KA', 'k', 'k', 'C', 'C', 'P'),
    ('PA', 'p', 'p', 'C', 'C', 'P'),
    ('TU', 'tˤ', 't.', 'C', 'C', 'E'),
    ('QU', 'q', 'q', 'C', 'C', 'E'),
    ('SU', 'sˤ', 's.', 'C', 'F', 'E'),
    ('SA', 's', 's', 'C', 'F', 'P'),
    ('ZI', 'z', 'z', 'C', 'F', 'P'),
    ('SI', 'ʃ', 'S', 'C', 'F', 'P'),
    ('LA', 'l', 'l', 'C', 'S', 'P'),
    ('MI', 'm', 'm', 'C', 'S', 'P'),
    ('NA', 'n', 'n', 'C', 'S', 'P'),
    ('RE', 'r', 'r', 'C', 'S', 'P'),
    ('ET', 'ħ', 'X', 'C', 'F', 'P'),
    ('HE', 'x', 'x', 'C', 'F', 'P'),
    ('AI', 'ʕ', 'H', 'C', 'F', 'P'),
    ('AL', 'ʔ', '?', 'C', 'C', 'P'),
    ('WA', 'w', 'w', 'C', 'S', 'P'),
    ('YI', 'j', 'j', 'C', 'S', 'P'),
    ('TA', 't', 't', 'C', 'C', 'P'),
    ('AA', 'a', 'a', 'V', 'L', 'P'),
    ('EE', 'e', 'e', 'V', 'M', 'P'),
    ('II', 'i', 'i', 'V', 'H', 'P'),
    ('UU', 'u', 'u', 'V', 'H', 'P'),
    ('AO', 'ɑ', 'a.', 'V', 'L', 'P'),
    ('EO', 'ɛ', 'e.', 'V', 'M', 'P'),
    ('IO', 'ɨ', 'i.', 'V', 'H', 'P'),
    ('UO', 'ʊ', 'u.', 'V', 'H', 'P'),
    (RESYNC_PAUSE_REALIZATION, '.', '_', 'S', 'S', 'P'),
    ('SP', '|', '_', 'S', 'S', 'P'),
    ('ZP', '‖', '_', 'S', 'S', 'P'),
)

REALIZATION_CODE_METADATA = {
    code: {
        'ipa': ipa,
        'mbrola_xsampa': mbrola_xsampa,
        'category': category,
        'type': type_code,
        'emphaticity': emphaticity,
    }
    for code, ipa, mbrola_xsampa, category, type_code, emphaticity in REALIZATION_CODE_ROWS
}

INPUT_TO_REALIZATION_ROWS = (
    ('BET', 'BE'),
    ('DAL', 'DA'),
    ('GIM', 'GI'),
    ('KAP', 'KA'),
    ('PAY', 'PA'),
    ('TUT', 'TU'),
    ('QUP', 'QU'),
    ('SUD', 'SU'),
    ('SAM', 'SA'),
    ('ZIN', 'ZI'),
    ('SIN', 'SI'),
    ('LAM', 'LA'),
    ('MIM', 'MI'),
    ('NAN', 'NA'),
    ('RES', 'RE'),
    ('ETE', 'ET'),
    ('HET', 'HE'),
    ('AIN', 'AI'),
    ('ALE', 'AL'),
    ('WAW', 'WA'),
    ('YID', 'YI'),
    ('TAW', 'TA'),
    ('ARU', 'AL'),
    ('ENA', 'WA'),
    ('ENA', 'YI'),
    ('AYA', 'AA'),
    ('EYA', 'EE'),
    ('IYA', 'II'),
    ('UYA', 'UU'),
    ('AWA', 'AA'),
    ('EWA', 'EE'),
    ('IWA', 'II'),
    ('UWA', 'UU'),
    ('AWI', 'AA'),
    ('EWI', 'EE'),
    ('IWI', 'II'),
    ('UWI', 'UU'),
    ('AYA', 'AO'),
    ('EYA', 'EO'),
    ('IYA', 'IO'),
    ('UYA', 'UO'),
    ('AWA', 'AO'),
    ('EWA', 'EO'),
    ('IWA', 'IO'),
    ('UWA', 'UO'),
    ('AWI', 'AO'),
    ('EWI', 'EO'),
    ('IWI', 'IO'),
    ('UWI', 'UO'),
    (RESYNC_PAUSE_LABEL, RESYNC_PAUSE_REALIZATION),
    ('SES', 'SP'),
    ('ZEN', 'ZP'),
)

INPUT_TO_REALIZATION_CODES: dict[str, tuple[str, ...]] = {}
for label, code in INPUT_TO_REALIZATION_ROWS:
    INPUT_TO_REALIZATION_CODES.setdefault(label, ())
    INPUT_TO_REALIZATION_CODES[label] = INPUT_TO_REALIZATION_CODES[label] + (code,)

PLAIN_VOWEL_REALIZATIONS = {
    'AYA': 'AA',
    'EYA': 'EE',
    'IYA': 'II',
    'UYA': 'UU',
    'AWA': 'AA',
    'EWA': 'EE',
    'IWA': 'II',
    'UWA': 'UU',
    'AWI': 'AA',
    'EWI': 'EE',
    'IWI': 'II',
    'UWI': 'UU',
}

EMPHATIC_VOWEL_REALIZATIONS = {
    'AYA': 'AO',
    'EYA': 'EO',
    'IYA': 'IO',
    'UYA': 'UO',
    'AWA': 'AO',
    'EWA': 'EO',
    'IWA': 'IO',
    'UWA': 'UO',
    'AWI': 'AO',
    'EWI': 'EO',
    'IWI': 'IO',
    'UWI': 'UO',
}




def _is_vowel(symbol: str) -> bool:
    return symbol in SHORT_VOWELS or symbol in LONG_VOWELS


def _classify_symbol(symbol: str) -> tuple[str, str, str]:
    if symbol in CONSONANT_HIATUS:
        return 'C', 'H', 'S'
    if symbol in CONSONANT_VOWEL_TRANSITION:
        return 'C', 'T', 'S'
    if symbol in CONSONANT_CLOSURE:
        return 'C', 'C', 'S'
    if symbol in CONSONANT_FRICATIVE:
        return 'C', 'F', 'S'
    if symbol in CONSONANT_SONORANT:
        return 'C', 'S', 'S'
    if symbol in LOW_VOWELS:
        return 'V', 'L', INPUT_CHARACTER_LENGTHS[symbol]
    if symbol in MID_VOWELS:
        return 'V', 'M', INPUT_CHARACTER_LENGTHS[symbol]
    if symbol in HIGH_VOWELS:
        return 'V', 'H', INPUT_CHARACTER_LENGTHS[symbol]
    raise ValueError(f'Unsupported phonetizer symbol: {symbol!r}')


def _base_realization_for_label(label: str) -> str:
    codes = INPUT_TO_REALIZATION_CODES[label]
    return codes[0]


def _choose_vowel_realization(label: str, emphatic_onset: bool) -> str:
    if emphatic_onset:
        return EMPHATIC_VOWEL_REALIZATIONS[label]
    return PLAIN_VOWEL_REALIZATIONS[label]


def _syllable_ranges(rows: list[dict[str, str]]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start_index: int | None = None
    for index, row in enumerate(rows):
        if row['category'] == 'S':
            start_index = None
            continue
        if start_index is None:
            start_index = index
        if row['boundary'] in {'I', 'E', 'L', 'X', 'F'}:
            ranges.append((start_index, index + 1))
            start_index = None
    if start_index is not None:
        ranges.append((start_index, len(rows)))
    return ranges


def _syllable_has_emphatic_onset(rows: list[dict[str, str]], start_index: int, end_index: int) -> bool:
    return any(
        row['position'] == 'O' and row['text'] in EMPHATIC_CONSONANTS
        for row in rows[start_index:end_index]
    )


def _syllable_has_emphatic_coda(rows: list[dict[str, str]], start_index: int, end_index: int) -> bool:
    return any(
        row['position'] == 'C' and row['text'] in EMPHATIC_CONSONANTS
        for row in rows[start_index:end_index]
    )


def _syllable_has_coloring_blocker(rows: list[dict[str, str]], start_index: int, end_index: int) -> bool:
    return any(
        row['position'] == 'O' and row['text'] in EMPHATIC_COLORING_BLOCKERS
        for row in rows[start_index:end_index]
    )


def _color_syllable_vowels(rows: list[dict[str, str]], start_index: int, end_index: int, *, emphatic: bool) -> None:
    for row in rows[start_index:end_index]:
        if row['category'] == 'V':
            row['realization'] = _choose_vowel_realization(row['label'], emphatic)


def _apply_emphatic_vowel_coloring(
    rows: list[dict[str, str]],
    phonetize_config: dict[str, Any] | None,
) -> None:
    config = _merge_phonetize_config(phonetize_config)
    extended = not bool(config['process']['realization']['limit_emphatic_coloring'])
    ranges = _syllable_ranges(rows)
    carry_targets: set[int] = set()

    for syllable_index, (start_index, end_index) in enumerate(ranges):
        emphatic = (
            syllable_index in carry_targets
            or _syllable_has_emphatic_onset(rows, start_index, end_index)
        )
        carries_forward = False

        if extended and _syllable_has_emphatic_coda(rows, start_index, end_index):
            blocker_present = _syllable_has_coloring_blocker(rows, start_index, end_index)
            if not blocker_present:
                emphatic = True
            carries_forward = True

        _color_syllable_vowels(rows, start_index, end_index, emphatic=emphatic)

        if not extended or not carries_forward or syllable_index + 1 >= len(ranges):
            continue

        next_start, next_end = ranges[syllable_index + 1]
        if any(row['category'] == 'S' and not _is_resync_pause_row(row) for row in rows[end_index:next_start]):
            continue
        if _syllable_has_coloring_blocker(rows, next_start, next_end):
            continue
        carry_targets.add(syllable_index + 1)
        _color_syllable_vowels(rows, next_start, next_end, emphatic=True)


def _choose_vowel_transition_realization(previous_code: str, next_code: str) -> str:
    if next_code in {'UU', 'UO'}:
        return 'WA' if previous_code in {'AA', 'AO', 'EE', 'EO', 'UU', 'UO'} else 'YI'
    if previous_code in {'UU', 'UO'}:
        return 'WA'
    return 'YI'


def _new_segment_seed(symbol: str) -> dict[str, str]:
    label = INPUT_CHARACTER_LABELS[symbol]
    category, type_code, length_code = _classify_symbol(symbol)
    return {
        'label': label,
        'category': category,
        'type': type_code,
        'length': length_code,
        'position': 'N' if category == 'V' else 'O',
        'boundary': 'N',
        'accent': 'F',
        'realization': _base_realization_for_label(label),
        'duration': PHONE_ROW_DURATION_PLACEHOLDER,
        'drift': PHONE_ROW_DRIFT_NEUTRAL,
        'intonation': PHONE_ROW_INTONATION_NEUTRAL,
        'text': symbol,
    }


def _new_pause_row(text: str, *, pause_type: str, length_code: str) -> dict[str, str]:
    is_long = length_code == 'L'
    label = 'ZEN' if is_long else 'SES'
    return {
        'label': label,
        'category': 'S',
        'type': pause_type,
        'length': length_code,
        'position': 'S',
        'boundary': 'N',
        'accent': 'P',
        'realization': 'ZP' if is_long else 'SP',
        'duration': PHONE_ROW_DURATION_PLACEHOLDER,
        'drift': PHONE_ROW_DRIFT_NEUTRAL,
        'intonation': PHONE_ROW_INTONATION_NEUTRAL,
        'text': text,
    }


def _new_resync_pause_row() -> dict[str, str]:
    return {
        'label': RESYNC_PAUSE_LABEL,
        'category': 'S',
        'type': RESYNC_PAUSE_TYPE,
        'length': 'S',
        'position': 'S',
        'boundary': 'N',
        'accent': 'P',
        'realization': RESYNC_PAUSE_REALIZATION,
        'duration': PHONE_ROW_DURATION_PLACEHOLDER,
        'drift': PHONE_ROW_DRIFT_NEUTRAL,
        'intonation': PHONE_ROW_INTONATION_NEUTRAL,
        'text': RESYNC_PAUSE_TEXT,
    }




def _intonation_targets(token: str, base_f0: int) -> tuple[int, ...]:
    canonical = _normalize_intonation_token(token)
    family = canonical[0]
    semitones = int(canonical[1])
    if family == 'H':
        return (_semitone_to_hz(base_f0, semitones),)
    if family == 'L':
        return (_semitone_to_hz(base_f0, -semitones),)
    if family == 'M':
        return (base_f0,)
    if family == 'R':
        return (base_f0, _semitone_to_hz(base_f0, semitones))
    if family == 'F':
        return (base_f0, _semitone_to_hz(base_f0, -semitones))
    if family == 'P':
        peak = _semitone_to_hz(base_f0, semitones)
        return (base_f0, peak, peak, base_f0)
    valley = _semitone_to_hz(base_f0, -semitones)
    return (base_f0, valley, valley, base_f0)


def _suite_has_unknown_alnum(text: str, short_chars: set[str], long_chars: set[str]) -> bool:
    for symbol in text:
        if symbol.isspace():
            continue
        if symbol.isalnum() and symbol not in short_chars and symbol not in long_chars:
            return True
    return False


def _classify_pause_suite(
    suite_text: str,
    *,
    short_pause_chars: set[str],
    long_pause_chars: set[str],
    short_pause_regex: tuple[re.Pattern[str], ...],
    long_pause_regex: tuple[re.Pattern[str], ...],
) -> tuple[str, bool]:
    normalized = suite_text.strip()
    if not normalized:
        raise ValueError('Cannot classify an empty pause suite.')

    has_question = any(symbol in QUESTION_PUNCTUATION_CHARS for symbol in normalized)
    has_exclamation = any(symbol in EXCLAMATION_PUNCTUATION_CHARS for symbol in normalized)
    has_ellipsis = '...' in normalized or '…' in normalized
    statement_candidate = normalized.replace('...', '').replace('…', '')
    has_statement = '\n' in normalized or any(symbol in STATEMENT_PUNCTUATION_CHARS for symbol in statement_candidate)
    has_continuation = has_ellipsis or any(symbol in PRIMARY_CONTINUATION_PUNCTUATION_CHARS for symbol in normalized)

    short_internal_chars = {
        symbol
        for symbol in normalized
        if not symbol.isspace() and symbol in short_pause_chars and symbol not in PRIMARY_CONTINUATION_PUNCTUATION_CHARS
    }
    long_internal_chars = {
        symbol
        for symbol in normalized
        if not symbol.isspace() and symbol in long_pause_chars and symbol not in QUESTION_PUNCTUATION_CHARS | EXCLAMATION_PUNCTUATION_CHARS | STATEMENT_PUNCTUATION_CHARS
    }
    matches_short_internal = any(regex.search(normalized) for regex in short_pause_regex)
    matches_long_internal = any(regex.search(normalized) for regex in long_pause_regex)

    if has_question:
        return 'Q', True
    if has_exclamation:
        return 'E', True
    if has_statement:
        return 'S', True
    if has_continuation:
        return 'C', False
    if short_internal_chars or long_internal_chars or matches_short_internal or matches_long_internal:
        return 'I', bool(long_internal_chars or matches_long_internal)
    if _suite_has_unknown_alnum(normalized, short_pause_chars, long_pause_chars):
        raise ValueError(f'Unsupported armored phonetizer content: {OPEN_ESCAPE}{suite_text}{CLOSE_ESCAPE}')
    return 'I', False


def _consume_pause_suite(
    tilde_text: str,
    start_index: int,
    *,
    short_pause_chars: set[str],
    long_pause_chars: set[str],
) -> tuple[str, int]:
    index = start_index
    while index < len(tilde_text):
        symbol = tilde_text[index]
        if symbol == '\n' or symbol.isspace():
            break
        if symbol in INPUT_CHARACTER_LABELS or symbol in {SYL_SEPARATOR, '.', '-', WORD_LINKER} or symbol in INTERNAL_MERGE_CHARS:
            break
        if symbol in short_pause_chars or symbol in long_pause_chars or symbol == '…':
            index += 1
            continue
        break
    return tilde_text[start_index:index], index


def _finalize_syllable(rows: list[dict[str, str]], syllable: list[dict[str, str]], boundary_code: str) -> None:
    if not syllable:
        return
    nucleus_index = next((index for index, row in enumerate(syllable) if row['category'] == 'V'), None)
    if nucleus_index is None:
        raise ValueError('Invalid _tilde input for phonetizer: syllable without vowel nucleus')
    for index, row in enumerate(syllable):
        if row['category'] == 'V':
            row['position'] = 'N'
        else:
            row['position'] = 'O' if index < nucleus_index else 'C'
    for row in syllable:
        if row['category'] == 'V':
            row['realization'] = _choose_vowel_realization(row['label'], False)
        elif row['label'] == 'ENA':
            row['realization'] = 'YI'
        else:
            row['realization'] = _base_realization_for_label(row['label'])
    syllable[-1]['boundary'] = boundary_code
    rows.extend(syllable)


def _resolve_transition_rows(rows: list[dict[str, str]]) -> None:
    for index, row in enumerate(rows):
        if row['label'] != 'ENA':
            continue
        previous_vowel = next((candidate for candidate in reversed(rows[:index]) if candidate['category'] == 'V'), None)
        next_vowel = next((candidate for candidate in rows[index + 1 :] if candidate['category'] == 'V'), None)
        if previous_vowel is None or next_vowel is None:
            row['realization'] = 'YI'
            continue
        row['realization'] = _choose_vowel_transition_realization(previous_vowel['realization'], next_vowel['realization'])


def _append_armored_pause_rows(
    armored_text: str,
    rows: list[dict[str, str]],
    finish_syllable,
    *,
    short_pause_chars: set[str],
    long_pause_chars: set[str],
    short_pause_regex: tuple[re.Pattern[str], ...],
    long_pause_regex: tuple[re.Pattern[str], ...],
) -> None:
    normalized = armored_text.strip()
    if normalized:
        pause_type, is_long = _classify_pause_suite(
            normalized,
            short_pause_chars=short_pause_chars,
            long_pause_chars=long_pause_chars,
            short_pause_regex=short_pause_regex,
            long_pause_regex=long_pause_regex,
        )
        finish_syllable('F')
        rows.append(_new_pause_row(normalized, pause_type=pause_type, length_code='L' if is_long else 'S'))


def _resolve_pause_punctuation_rules(
    input_frontmatter: dict[str, Any] | None,
) -> tuple[set[str], set[str], tuple[re.Pattern[str], ...], tuple[re.Pattern[str], ...]]:
    inherited = resolve_inherited_punctuation_options(input_frontmatter)
    short_chars = set(SHORT_PAUSE_PUNCTUATION_CHARS) | set(inherited['extra_short_punct_chars'])
    long_chars = set(LONG_PAUSE_PUNCTUATION_CHARS) | set(inherited['extra_long_punct_chars'])
    short_patterns = list(DEFAULT_SHORT_PAUSE_PUNCTUATION_PATTERNS)
    short_patterns.extend(inherited['extra_short_punct_pattern'])
    long_patterns = list(DEFAULT_LONG_PAUSE_PUNCTUATION_PATTERNS)
    long_patterns.extend(inherited['extra_long_punct_pattern'])
    short_regex = tuple(
        compile_contextual_regex(pattern, '--extra-short-punct-pattern', index)
        for index, pattern in enumerate(short_patterns, start=1)
    )
    long_regex = tuple(
        compile_contextual_regex(pattern, '--extra-long-punct-pattern', index)
        for index, pattern in enumerate(long_patterns, start=1)
    )
    return short_chars, long_chars, short_regex, long_regex


def derive_original_tilde_text(tilde_text: str) -> str:
    pieces: list[str] = []
    index = 0
    while index < len(tilde_text):
        symbol = tilde_text[index]
        if symbol == OPEN_ESCAPE:
            close_index = tilde_text.find(CLOSE_ESCAPE, index + 1)
            if close_index < 0:
                raise ValueError('Invalid _tilde input for phonetizer: unterminated armored span')
            pieces.append(tilde_text[index : close_index + 1])
            index = close_index + 1
            continue
        if symbol == '~':
            index += 1
            continue
        if symbol == '&':
            pieces.append(' ')
            index += 1
            continue
        pieces.append(symbol)
        index += 1
    return ''.join(pieces)


def _normalize_terminal_line_break(tilde_text: str) -> str:
    if tilde_text.endswith('\n'):
        return tilde_text
    return tilde_text + '\n'


def build_phone_streams(
    tilde_text: str,
    phonetize_config: dict[str, Any] | None = None,
    input_frontmatter: dict[str, Any] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    original_text = derive_original_tilde_text(tilde_text)
    original_rows = build_phone_rows(original_text, phonetize_config, input_frontmatter)
    accentuated_rows = build_phone_rows(tilde_text, phonetize_config, input_frontmatter)
    return original_rows, accentuated_rows


def realize_phone_streams(
    tilde_text: str,
    phonetize_config: dict[str, Any] | None = None,
    input_frontmatter: dict[str, Any] | None = None,
) -> tuple[tuple[list[dict[str, str]], dict[str, Any]], tuple[list[dict[str, str]], dict[str, Any]]]:
    original_rows, accentuated_rows = build_phone_streams(tilde_text, phonetize_config, input_frontmatter)
    original_report = realize_phone_rows(
        original_rows,
        phonetize_config,
        allow_accentuation=False,
        input_frontmatter=input_frontmatter,
    )
    accentuated_report = realize_phone_rows(
        accentuated_rows,
        phonetize_config,
        allow_accentuation=True,
        input_frontmatter=input_frontmatter,
    )
    realize_row_intonation(original_rows, phonetize_config, accentuated=False)
    realize_row_intonation(accentuated_rows, phonetize_config, accentuated=True)
    return (original_rows, original_report), (accentuated_rows, accentuated_report)


def _semitone_to_hz(base_f0: int, semitones: int) -> int:
    return max(1, int(round(base_f0 * (2 ** (semitones / 12.0)))))


def _rounded_duration_value(value: float) -> int:
    return max(0, int(round(value)))


def _format_duration(value: float) -> str:
    bounded = _rounded_duration_value(value)
    return f'{bounded:04d}'


def _consonant_timing_key(row: dict[str, str]) -> str:
    if row['type'] in {'C', 'H'}:
        return 'closure'
    if row['type'] == 'F':
        return 'fricative'
    if row['type'] in {'S', 'T'}:
        return 'sonorant'
    raise ValueError(f"Unsupported consonant timing type: {row['type']!r}")


def _consonant_anchor(
    row: dict[str, str],
    config: dict[str, Any],
    position: str,
    *,
    pre_pausal_final: bool = False,
) -> float:
    durations = config['timing_model']['durations']
    timing_key = _consonant_timing_key(row)
    consonant_cfg = durations['consonants'][timing_key]
    if row['type'] == 'H':
        return float(durations['consonants']['closure']['special_realization']['hiatus'])
    if row['type'] == 'T':
        return float(durations['consonants']['sonorant']['special_realization']['vowel_transition'])
    if position == 'C':
        if pre_pausal_final:
            return float(consonant_cfg['coda_final'])
        return float(consonant_cfg['coda'])
    return float(consonant_cfg['onset'])


def _consonant_geminate_target(row: dict[str, str], config: dict[str, Any]) -> float:
    durations = config['timing_model']['durations']
    timing_key = _consonant_timing_key(row)
    return float(durations['consonants'][timing_key]['geminate'])


def _consonant_maximum(row: dict[str, str], config: dict[str, Any]) -> float:
    durations = config['timing_model']['durations']
    timing_key = _consonant_timing_key(row)
    return float(durations['consonants'][timing_key]['perception_limits']['gemination_max'])


def _vowel_anchor(
    row: dict[str, str],
    config: dict[str, Any],
    *,
    pre_pausal_final: bool = False,
) -> float:
    vowels_cfg = config['timing_model']['durations']['vowels']
    if row['length'] == 'S':
        key = 'short_final' if pre_pausal_final else 'short'
        return float(vowels_cfg[key])
    key = 'long_final' if pre_pausal_final else 'long'
    return float(vowels_cfg[key])


def _vowel_bounds(
    row: dict[str, str],
    config: dict[str, Any],
    *,
    ordinary_recovery: bool = False,
    pre_pausal_final: bool = False,
) -> tuple[float, float]:
    vowels_cfg = config['timing_model']['durations']['vowels']
    limits = vowels_cfg['perception_limits']
    if row['length'] == 'S':
        key = 'short_final' if pre_pausal_final else 'short'
        anchor = float(vowels_cfg[key])
        return anchor, anchor
    if ordinary_recovery:
        minimum = float(vowels_cfg['long_final']) if pre_pausal_final else float(limits['long_min'])
        ordinary_maximum = min(float(limits['elongation_max']), float(limits['very_long_min']) - 1.0)
        ordinary_maximum = max(minimum, ordinary_maximum)
        return minimum, ordinary_maximum
    return float(limits['long_min']), float(limits['elongation_max'])


def _accent_adjacent_vowel_limit(row: dict[str, str], config: dict[str, Any]) -> float:
    vowels_cfg = config['timing_model']['durations']['vowels']
    limits = vowels_cfg['perception_limits']
    if row['length'] == 'S':
        return float(limits['long_min']) - 1.0
    return float(limits['elongation_max'])


def _timing_refs(config: dict[str, Any]) -> tuple[float, float, float]:
    cvc_reference = float(config['timing_model']['durations']['cvc_reference'])
    return cvc_reference / 2.0, cvc_reference, cvc_reference * 1.5


def _round_half_up(value: float) -> int:
    if value >= 0:
        return int(math.floor(value + 0.5))
    return -int(math.floor(abs(value) + 0.5))


def _normalize_drift_to_nearest_branch(
    drift_value: float,
    synchronization_basis: float,
) -> float:
    threshold = 0.5 * synchronization_basis
    while drift_value > threshold:
        drift_value -= synchronization_basis
    while drift_value < -threshold:
        drift_value += synchronization_basis
    return drift_value


def _partition_phone_units(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    syllable: list[int] = []
    for index, row in enumerate(rows):
        if row['category'] == 'S':
            if syllable:
                units.append({'kind': 'syllable', 'indices': syllable})
                syllable = []
            units.append({'kind': 'pause', 'index': index})
            continue
        syllable.append(index)
        if row['boundary'] != 'N':
            units.append({'kind': 'syllable', 'indices': syllable})
            syllable = []
    if syllable:
        units.append({'kind': 'syllable', 'indices': syllable})
    return units


def realize_row_intonation(
    rows: list[dict[str, str]],
    phonetize_config: dict[str, Any] | None = None,
    *,
    accentuated: bool,
) -> None:
    config = _merge_phonetize_config(phonetize_config)
    runtime_intonation = _runtime_intonation_config(config['process']['intonation'])
    units = _partition_phone_units(rows)

    for row in rows:
        row['intonation'] = PHONE_ROW_INTONATION_NEUTRAL

    syllable_tokens: dict[int, str] = {}
    for unit_index, unit in enumerate(units):
        if unit['kind'] != 'syllable':
            continue
        token = PHONE_ROW_INTONATION_NEUTRAL
        if accentuated and any(rows[index]['accent'] == 'A' for index in unit['indices']):
            token = runtime_intonation['stress']
        syllable_tokens[unit_index] = token

    for unit_index, unit in enumerate(units):
        if unit['kind'] != 'pause':
            continue
        pause_row = rows[unit['index']]
        pause_type = pause_row['type']
        pause_token = PHONE_ROW_INTONATION_NEUTRAL
        if pause_type in PAUSE_TYPE_TO_INTONATION_KEY:
            pause_token = runtime_intonation[PAUSE_TYPE_TO_INTONATION_KEY[pause_type]]
            previous_index = unit_index - 1
            if previous_index >= 0 and units[previous_index]['kind'] == 'syllable':
                syllable_tokens[previous_index] = pause_token
        pause_row['intonation'] = pause_token

    for unit_index, unit in enumerate(units):
        if unit['kind'] != 'syllable':
            continue
        token = syllable_tokens[unit_index]
        for row_index in unit['indices']:
            rows[row_index]['intonation'] = token


def _mbrola_rows(rows: list[dict[str, str]], phonetize_config: dict[str, Any] | None, *, accentuated: bool) -> list[tuple[str, int, tuple[int, ...]]]:
    _ = accentuated
    config = _merge_phonetize_config(phonetize_config)
    baseline_f0 = int(config['process']['intonation']['f0'])
    emitted: list[tuple[str, int, tuple[int, ...]]] = []

    for row in rows:
        emitted.append(
            (
                REALIZATION_CODE_METADATA[row['realization']]['mbrola_xsampa'],
                int(row['duration']),
                _intonation_targets(row['intonation'], baseline_f0),
            )
        )

    merged: list[tuple[str, int, tuple[int, ...]]] = []
    for symbol, duration, targets in emitted:
        if merged and merged[-1][0] == symbol and merged[-1][2] == targets:
            prev_symbol, prev_duration, prev_targets = merged[-1]
            merged[-1] = (prev_symbol, prev_duration + duration, prev_targets)
        else:
            merged.append((symbol, duration, targets))
    return merged


def _analyze_syllable(rows: list[dict[str, str]], indices: list[int]) -> dict[str, Any]:
    vowel_indices = [index for index in indices if rows[index]['category'] == 'V']
    if not vowel_indices:
        raise ValueError('Phase 2 cannot realize a syllable without a vowel nucleus')
    nucleus_index = vowel_indices[0]
    onset_indices = [index for index in indices if index < nucleus_index and rows[index]['category'] == 'C']
    coda_indices = [index for index in indices if index > nucleus_index and rows[index]['category'] == 'C']
    vowel_row = rows[nucleus_index]
    has_coda = bool(coda_indices)
    if vowel_row['length'] == 'S':
        base_shape = 'CVC' if has_coda else 'CV'
    else:
        base_shape = 'CVVC' if has_coda else 'CVV'
    accent_index = next((index for index in indices if rows[index]['accent'] == 'A'), None)
    accent_shape = None
    if accent_index is not None:
        if accent_index in onset_indices:
            accent_shape = 'C:V'
        elif accent_index == nucleus_index:
            accent_shape = 'CVV:'
        elif accent_index in coda_indices:
            accent_shape = 'CVV:C' if vowel_row['length'] == 'L' else 'CVC:'
    return {
        'rows': rows,
        'indices': indices,
        'onset_indices': onset_indices,
        'nucleus_index': nucleus_index,
        'coda_indices': coda_indices,
        'base_shape': base_shape,
        'accent_index': accent_index,
        'accent_shape': accent_shape,
    }


def _shape_reference(analysis: dict[str, Any], config: dict[str, Any], *, accentuated: bool, mora_mode: str = 'bi', mono_lengthening: float = 0.0) -> float:
    one_mora_ref, two_mora_ref, three_mora_ref = _timing_refs(config)
    base_map = {
        'CV': one_mora_ref,
        'CVV': two_mora_ref,
        'CVC': two_mora_ref,
        'CVVC': three_mora_ref,
    }
    target = base_map[analysis['base_shape']]
    if accentuated and analysis['accent_shape'] is not None:
        if mora_mode == 'mono':
            target += mono_lengthening
        else:
            target += one_mora_ref
    return target


def _adjacent_accent_index(analysis: dict[str, Any]) -> int | None:
    accent_shape = analysis['accent_shape']
    if accent_shape == 'C:V':
        return analysis['nucleus_index']
    if accent_shape == 'CVV:':
        return analysis['onset_indices'][0] if analysis['onset_indices'] else None
    if accent_shape == 'CVC:':
        return analysis['nucleus_index']
    if accent_shape == 'CVV:C':
        return analysis['coda_indices'][0] if analysis['coda_indices'] else None
    return None


def _primary_accent_index(analysis: dict[str, Any]) -> int | None:
    accent_shape = analysis['accent_shape']
    if accent_shape == 'C:V':
        return analysis['onset_indices'][0] if analysis['onset_indices'] else analysis['accent_index']
    if accent_shape == 'CVV:':
        return analysis['nucleus_index']
    if accent_shape == 'CVC:':
        return analysis['coda_indices'][0] if analysis['coda_indices'] else analysis['accent_index']
    if accent_shape == 'CVV:C':
        return analysis['nucleus_index']
    return analysis['accent_index']


def _pause_multiple_candidates(minimum: float, maximum: float, synchronization_basis: float) -> list[float]:
    upper = max(1, int(math.ceil(maximum / synchronization_basis)) + 2)
    candidates: list[float] = []
    for n in range(1, upper):
        candidate = _round_sync_precision(n * synchronization_basis)
        if minimum <= candidate <= maximum:
            candidates.append(candidate)
    return candidates


def _preferred_pause_target(row: dict[str, str], config: dict[str, Any], *, synchronization_basis: float) -> float:
    pauses_cfg = config['timing_model']['durations']['pauses']
    band = pauses_cfg['long'] if row['length'] == 'L' else pauses_cfg['short']
    minimum = float(band['min'])
    maximum = float(band['max'])
    candidates = _pause_multiple_candidates(minimum, maximum, synchronization_basis)
    midpoint = (minimum + maximum) / 2.0
    if candidates:
        return min(candidates, key=lambda value: (abs(value - midpoint), value))
    nearest_multiple = max(
        synchronization_basis,
        _round_sync_precision(round(midpoint / synchronization_basis) * synchronization_basis),
    )
    return min(max(nearest_multiple, minimum), maximum)


def _pause_duration_and_drift(
    row: dict[str, str],
    config: dict[str, Any],
    drift_cursor: float,
    *,
    synchronization_basis: float,
) -> tuple[float, float]:
    pauses_cfg = config['timing_model']['durations']['pauses']
    band = pauses_cfg['resync'] if _is_resync_pause_row(row) else (pauses_cfg['long'] if row['length'] == 'L' else pauses_cfg['short'])
    minimum = float(band['min'])
    maximum = float(band['max'])
    if _is_resync_pause_row(row):
        actual = -drift_cursor if drift_cursor < 0 else (synchronization_basis - drift_cursor)
        emitted = float(_rounded_duration_value(actual))
        return emitted, _normalize_drift_to_nearest_branch(drift_cursor + emitted, synchronization_basis)
    preferred = _preferred_pause_target(row, config, synchronization_basis=synchronization_basis)
    desired = preferred - drift_cursor
    actual = min(max(desired, minimum), maximum)
    emitted = float(_rounded_duration_value(actual))
    new_drift = drift_cursor + (emitted - preferred)
    return emitted, new_drift


def _diagnostic_rate(count: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(count / denominator, 4)


def _supports_post_accent_long_vowel_cleanup(
    rows: list[dict[str, str]],
    analysis: dict[str, Any],
) -> bool:
    return rows[analysis['nucleus_index']]['length'] == 'L' and analysis['accent_shape'] in {'CVV:', 'CVV:C'}


def _apply_vowel_correction(
    rows: list[dict[str, str]],
    analysis: dict[str, Any],
    durations: dict[int, float],
    drift_after_assignment: float,
    minimum: float,
    maximum: float,
) -> tuple[float, str | None]:
    vowel_index = analysis['nucleus_index']
    current = durations[vowel_index]
    if drift_after_assignment > 0:
        reducible = min(current - minimum, drift_after_assignment)
        if reducible > 0:
            durations[vowel_index] = current - reducible
            drift_after_assignment -= reducible
            return drift_after_assignment, 'shorten'
    elif drift_after_assignment < 0:
        extendable = min(maximum - current, abs(drift_after_assignment))
        if extendable > 0:
            durations[vowel_index] = current + extendable
            drift_after_assignment += extendable
            return drift_after_assignment, 'lengthen'
    return drift_after_assignment, None


def _apply_accent_increment(
    rows: list[dict[str, str]],
    analysis: dict[str, Any],
    durations: dict[int, float],
    config: dict[str, Any],
    drift_portion: float,
    next_same_onset: int | None,
    *,
    total_increment: float | None = None,
) -> float:
    accent_index = analysis['accent_index']
    if accent_index is None:
        return 0.0
    primary_index = _primary_accent_index(analysis)
    if primary_index is None:
        return 0.0
    before_total = sum(durations[index] for index in analysis['indices'])
    adjacent_index = _adjacent_accent_index(analysis)
    one_mora_ref, _two_mora_ref, _three_mora_ref = _timing_refs(config)
    policy = config['process']['accentuation_distribution_policy']
    primary_share, adjacent_share = ACCENTUATION_DISTRIBUTION_SHARES[policy]
    if total_increment is None:
        total_increment = float(_round_half_up(one_mora_ref))

    consonants_cfg = config['timing_model']['durations']['consonants']

    def _adjacent_singleton_limit(index: int) -> float:
        row = rows[index]
        timing_key = _consonant_timing_key(row)
        geminate_min = float(consonants_cfg[timing_key]['perception_limits']['geminate_min'])
        return min(_consonant_maximum(row, config), geminate_min - 1.0)

    def _segment_limit(index: int, *, adjacent: bool) -> float:
        row = rows[index]
        if row['category'] == 'V':
            if adjacent:
                return _accent_adjacent_vowel_limit(row, config)
            return _vowel_bounds(row, config)[1]
        if adjacent:
            return _adjacent_singleton_limit(index)
        if next_same_onset is not None and analysis['accent_shape'] in {'CVC:', 'CVV:C'} and index in analysis['coda_indices']:
            return max(0.0, _consonant_maximum(row, config) - durations.get(next_same_onset, 0.0))
        return _consonant_maximum(row, config)

    primary_slack = max(0.0, _segment_limit(primary_index, adjacent=False) - durations[primary_index])
    adjacent_slack = 0.0
    if adjacent_index is not None:
        adjacent_slack = max(0.0, _segment_limit(adjacent_index, adjacent=True) - durations[adjacent_index])

    if adjacent_share > 0.0:
        if adjacent_index is None:
            realizable_increment = 0.0
        else:
            realizable_increment = min(
                total_increment,
                primary_slack / primary_share,
                adjacent_slack / adjacent_share,
            )
    else:
        realizable_increment = min(total_increment, primary_slack)

    primary_gain = min(primary_slack, realizable_increment * primary_share)
    durations[primary_index] += primary_gain

    if adjacent_index is not None:
        adjacent_gain = min(adjacent_slack, realizable_increment * adjacent_share)
        durations[adjacent_index] += adjacent_gain

    if analysis['accent_shape'] in {'CVC:', 'CVV:C'} and analysis['coda_indices'] and next_same_onset is not None:
        coda_index = analysis['coda_indices'][0]
        ceiling = _consonant_maximum(rows[coda_index], config)
        combined = durations[coda_index] + durations[next_same_onset]
        if combined > ceiling:
            reduce_onset = min(durations[next_same_onset], combined - ceiling)
            durations[next_same_onset] -= reduce_onset
            combined = durations[coda_index] + durations[next_same_onset]
            if combined > ceiling:
                durations[coda_index] = max(0.0, ceiling - durations[next_same_onset])

    after_total = sum(durations[index] for index in analysis['indices'])
    return max(0.0, after_total - before_total)


def _same_consonant_next_onset(
    rows: list[dict[str, str]],
    analysis: dict[str, Any],
    next_analysis: dict[str, Any] | None,
    durations: dict[int, float],
    config: dict[str, Any],
) -> int | None:
    if not analysis['coda_indices'] or not next_analysis or not next_analysis['onset_indices']:
        return None
    coda_index = analysis['coda_indices'][0]
    onset_index = next_analysis['onset_indices'][0]
    if rows[coda_index]['text'] != rows[onset_index]['text']:
        return None
    coda_duration = durations[coda_index]
    onset_anchor = _consonant_anchor(rows[onset_index], config, 'O')
    ceiling = _consonant_maximum(rows[coda_index], config)
    if config['process']['geminate_policy'] == 'corrective':
        pair_total = min(_consonant_geminate_target(rows[coda_index], config), ceiling)
        consonant_class = _consonant_timing_key(rows[coda_index])
        coda_ratio = float(config['timing_model']['durations']['consonants'][consonant_class]['geminate_coda_ratio'])
        coda_duration = pair_total * coda_ratio
        durations[coda_index] = coda_duration
    else:
        pair_total = min(coda_duration + onset_anchor, ceiling)
    durations[onset_index] = max(0.0, pair_total - coda_duration)
    return onset_index


def _drift_label(drift_value: float) -> str:
    if abs(drift_value) < 0.5:
        return 'On the beat'
    if drift_value < 0:
        return 'Ahead (rushing)'
    return 'Behind (dragging)'


def _format_row_drift_token(drift_value: float) -> str:
    magnitude = int(round(abs(drift_value)))
    if magnitude == 0:
        return PHONE_ROW_DRIFT_NEUTRAL
    if magnitude > 999:
        raise ValueError(f'Row-level drift token magnitude exceeds three digits: {drift_value!r}')
    sign = '-' if drift_value < 0 else '+'
    return f'{sign}{magnitude:03d}'


def _is_chrono_checkpoint_row(row: dict[str, str]) -> bool:
    return row['category'] == 'S' or row['boundary'] in {'F', 'I', 'L', 'X', 'E'}


def _should_fold_completed_syllable(rows: list[dict[str, str]], analysis: dict[str, Any]) -> bool:
    return rows[analysis['indices'][-1]]['boundary'] == 'F'


def _validate_chrono_checkpoints(rows: list[dict[str, str]], cvc_reference: int) -> None:
    if not lib_constants.DEBUG_CHRONO:
        return
    if isinstance(cvc_reference, bool) or not isinstance(cvc_reference, int) or cvc_reference <= 0:
        raise ValueError(
            'DEBUG_CHRONO requires phonetize.process.timing_model.durations.cvc_reference '
            'to be a positive integer.'
        )

    cumulative_duration = 0
    for index, row in enumerate(rows, start=1):
        cumulative_duration += int(row['duration'])
        if not _is_chrono_checkpoint_row(row):
            continue

        drift_value = int(row['drift'])
        numerator = 2 * (cumulative_duration - drift_value)
        if numerator % cvc_reference != 0:
            raise ValueError(
                'DEBUG_CHRONO checkpoint mismatch at row '
                f'{index} ({row["label"]}/{row["text"]}): '
                f'2 * (cumulative_duration - drift) = {numerator} is not divisible by '
                f'cvc_reference = {cvc_reference}. '
                f'cumulative_duration={cumulative_duration}, drift={drift_value}, '
                f'duration={row["duration"]}, boundary={row["boundary"]}.'
            )


def _resync_pause_structurally_eligible(
    rows: list[dict[str, str]],
    units: list[dict[str, Any]],
    unit_index: int,
    analysis: dict[str, Any],
) -> bool:
    if unit_index + 1 >= len(units) or units[unit_index + 1]['kind'] != 'syllable':
        return False
    return rows[analysis['indices'][-1]]['boundary'] == 'F'


def _maybe_insert_resync_pause(
    rows: list[dict[str, str]],
    units: list[dict[str, Any]],
    unit_index: int,
    analysis: dict[str, Any],
    config: dict[str, Any],
    drift_cursor: float,
    synchronization_basis: float,
) -> tuple[dict[str, str], float, float] | None:
    if not config['process']['enable_resync_pause']:
        return None
    if not _resync_pause_structurally_eligible(rows, units, unit_index, analysis):
        return None

    resync_cfg = config['timing_model']['durations']['pauses']['resync']
    resync_min = float(resync_cfg['min'])
    resync_max = float(resync_cfg['max'])

    if drift_cursor < 0:
        target_duration = abs(drift_cursor)
    elif drift_cursor > 0:
        target_duration = abs(drift_cursor - synchronization_basis)
    else:
        return None

    if target_duration < resync_min or target_duration > resync_max:
        return None

    resync_row = _new_resync_pause_row()
    pause_duration, new_drift = _pause_duration_and_drift(
        resync_row,
        config,
        drift_cursor,
        synchronization_basis=synchronization_basis,
    )
    if abs(new_drift) >= abs(drift_cursor) and abs(new_drift) >= 0.5:
        return None
    return resync_row, pause_duration, new_drift


def realize_phone_rows(
    rows: list[dict[str, str]],
    phonetize_config: dict[str, Any] | None = None,
    *,
    allow_accentuation: bool,
    input_frontmatter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = _runtime_view_phonetize_config(_merge_phonetize_config(phonetize_config))
    synchronization_basis = _resolve_synchronization_basis(
        config,
        allow_accentuation=allow_accentuation,
        input_frontmatter=input_frontmatter,
    )
    units = _partition_phone_units(rows)
    durations: dict[int, float] = {}
    drift_cursor = 0.0
    drift_history: list[float] = []
    drift_extension_count = 0
    max_drift_extension = 0.0
    adjusted_non_accented_long_vowel_count = 0
    shortened_non_accented_long_vowel_count = 0
    lengthened_non_accented_long_vowel_count = 0
    non_accented_long_vowel_count = 0
    left_as_is_non_accented_long_vowel_count = 0
    resync_pause_insert_count = 0
    resync_pause_eligible_count = 0
    pause_residual_post_unit_drift_count = 0
    tolerance = float(config['timing_model']['durations']['drift_tolerance'])
    inserted_after: dict[int, list[tuple[dict[str, str], float, str]]] = {}
    row_drift_tokens: dict[int, str] = {}
    last_completed_drift_token = PHONE_ROW_DRIFT_NEUTRAL
    syllable_unit_count = sum(1 for unit in units if unit['kind'] == 'syllable')
    pause_unit_count = sum(1 for unit in units if unit['kind'] == 'pause')

    analyses: dict[int, dict[str, Any]] = {}
    for unit_index, unit in enumerate(units):
        if unit['kind'] == 'syllable':
            analyses[unit_index] = _analyze_syllable(rows, unit['indices'])

    for unit_index, unit in enumerate(units):
        if unit['kind'] == 'pause':
            entry_drift = drift_cursor
            pause_duration, drift_cursor = _pause_duration_and_drift(
                rows[unit['index']],
                config,
                drift_cursor,
                synchronization_basis=synchronization_basis,
            )
            durations[unit['index']] = pause_duration
            drift_cursor = entry_drift + (
                float(_rounded_duration_value(pause_duration))
                - (
                    _preferred_pause_target(
                        rows[unit['index']],
                        config,
                        synchronization_basis=synchronization_basis,
                    )
                    if not _is_resync_pause_row(rows[unit['index']])
                    else 0.0
                )
            )
            if not _is_resync_pause_row(rows[unit['index']]) and abs(drift_cursor) >= 0.5:
                pause_residual_post_unit_drift_count += 1
            drift_history.append(drift_cursor)
            last_completed_drift_token = _format_row_drift_token(drift_cursor)
            row_drift_tokens[unit['index']] = last_completed_drift_token
            continue

        entry_drift = drift_cursor
        analysis = analyses[unit_index]
        next_analysis = None
        if unit_index + 1 < len(units) and units[unit_index + 1]['kind'] == 'syllable':
            next_analysis = analyses[unit_index + 1]
        next_pause_row = None
        if unit_index + 1 < len(units) and units[unit_index + 1]['kind'] == 'pause':
            next_pause_row = rows[units[unit_index + 1]['index']]
        pre_pausal_final = _pause_row_triggers_final_anchors(next_pause_row)

        for row_index in analysis['indices']:
            row_drift_tokens[row_index] = last_completed_drift_token

        for onset_index in analysis['onset_indices']:
            durations.setdefault(onset_index, _consonant_anchor(rows[onset_index], config, 'O'))
        for coda_index in analysis['coda_indices']:
            durations[coda_index] = _consonant_anchor(rows[coda_index], config, 'C', pre_pausal_final=pre_pausal_final)
        nucleus_index = analysis['nucleus_index']
        durations[nucleus_index] = _vowel_anchor(rows[nucleus_index], config, pre_pausal_final=pre_pausal_final)

        next_same_onset = _same_consonant_next_onset(rows, analysis, next_analysis, durations, config)

        mora_mode = _resolve_mora_mode(input_frontmatter)
        shape_ref = _shape_reference(analysis, config, accentuated=False, mora_mode=mora_mode)
        realized_total = sum(durations[index] for index in analysis['indices'])
        drift_after_assignment = drift_cursor + (realized_total - shape_ref)
        cvc_reference = float(config['timing_model']['durations']['cvc_reference'])

        accent_target = 0.0
        if allow_accentuation and analysis['accent_shape'] is not None:
            mora_mode = _resolve_mora_mode(input_frontmatter)
            if mora_mode == 'mono':
                mono_lengthening = float(config['timing_model']['durations'].get('mono_mode_accentuation_lengthening', 50))
                _apply_accent_increment(
                    rows,
                    analysis,
                    durations,
                    config,
                    drift_after_assignment,
                    next_same_onset,
                    total_increment=mono_lengthening,
                )
            else:
                mono_lengthening = 0.0
                _apply_accent_increment(
                    rows,
                    analysis,
                    durations,
                    config,
                    drift_after_assignment,
                    next_same_onset,
                )
            emitted_total = sum(float(_rounded_duration_value(durations[index])) for index in analysis['indices'])
            total_target = _shape_reference(
                analysis, config, accentuated=True,
                mora_mode=mora_mode, mono_lengthening=mono_lengthening,
            )
            accent_target = total_target - shape_ref
            drift_after_assignment = entry_drift + (emitted_total - total_target)

        nucleus_row = rows[analysis['nucleus_index']]
        mora_mode = _resolve_mora_mode(input_frontmatter)
        supports_post_accent_cleanup = (
            _supports_post_accent_long_vowel_cleanup(rows, analysis)
            and mora_mode != 'mono'
        )
        counts_as_non_accented_long_vowel = nucleus_row['length'] == 'L' and not supports_post_accent_cleanup
        if counts_as_non_accented_long_vowel:
            non_accented_long_vowel_count += 1

        ordinary_long_vowel_adjusted = False
        if supports_post_accent_cleanup:
            minimum, maximum = _vowel_bounds(nucleus_row, config, ordinary_recovery=False, pre_pausal_final=pre_pausal_final)
            drift_after_assignment, _correction_kind = _apply_vowel_correction(
                rows,
                analysis,
                durations,
                drift_after_assignment,
                minimum,
                maximum,
            )
        elif abs(drift_after_assignment) > tolerance and nucleus_row['length'] == 'L':
            minimum, maximum = _vowel_bounds(nucleus_row, config, ordinary_recovery=True, pre_pausal_final=pre_pausal_final)
            drift_after_assignment, correction_kind = _apply_vowel_correction(
                rows,
                analysis,
                durations,
                drift_after_assignment,
                minimum,
                maximum,
            )
            if correction_kind is not None:
                ordinary_long_vowel_adjusted = True
                adjusted_non_accented_long_vowel_count += 1
                if correction_kind == 'shorten':
                    shortened_non_accented_long_vowel_count += 1
                elif correction_kind == 'lengthen':
                    lengthened_non_accented_long_vowel_count += 1

        if counts_as_non_accented_long_vowel and nucleus_row['length'] == 'L':
            left_as_is_non_accented_long_vowel_count += int(not ordinary_long_vowel_adjusted)

        emitted_total = sum(float(_rounded_duration_value(durations[index])) for index in analysis['indices'])
        drift_after_assignment = entry_drift + (emitted_total - shape_ref - accent_target)
        if _should_fold_completed_syllable(rows, analysis):
            drift_after_assignment = _normalize_drift_to_nearest_branch(
                drift_after_assignment,
                synchronization_basis,
            )

        if abs(drift_after_assignment) > tolerance:
            extension = abs(drift_after_assignment) - tolerance
            if extension > 0:
                drift_extension_count += 1
                max_drift_extension = max(max_drift_extension, extension)
        drift_cursor = drift_after_assignment
        drift_history.append(drift_cursor)
        last_completed_drift_token = _format_row_drift_token(drift_cursor)
        row_drift_tokens[analysis['indices'][-1]] = last_completed_drift_token

        if config['process']['enable_resync_pause'] and _resync_pause_structurally_eligible(rows, units, unit_index, analysis):
            resync_pause_eligible_count += 1
        resync_pause = _maybe_insert_resync_pause(
            rows,
            units,
            unit_index,
            analysis,
            config,
            drift_cursor,
            synchronization_basis,
        )
        if resync_pause is not None:
            resync_row, resync_duration, drift_cursor = resync_pause
            resync_pause_insert_count += 1
            last_completed_drift_token = _format_row_drift_token(drift_cursor)
            inserted_after.setdefault(analysis['indices'][-1], []).append((resync_row, resync_duration, last_completed_drift_token))
            drift_history.append(drift_cursor)

    finalized_rows: list[dict[str, str]] = []
    for index, row in enumerate(rows):
        row['duration'] = _format_duration(durations.get(index, 0.0))
        row['drift'] = row_drift_tokens.get(index, PHONE_ROW_DRIFT_NEUTRAL)
        finalized_rows.append(row)
        for inserted_row, inserted_duration, inserted_drift in inserted_after.get(index, ()):
            inserted_row['duration'] = _format_duration(inserted_duration)
            inserted_row['drift'] = inserted_drift
            finalized_rows.append(inserted_row)
    rows[:] = finalized_rows
    _validate_chrono_checkpoints(
        rows,
        _rounded_duration_value(float(config['timing_model']['durations']['cvc_reference'])),
    )

    if drift_history:
        mean = sum(drift_history) / len(drift_history)
        variance = sum((value - mean) ** 2 for value in drift_history) / len(drift_history)
        stddev = math.sqrt(variance)
        max_abs = max(abs(value) for value in drift_history)
    else:
        mean = 0.0
        stddev = 0.0
        max_abs = 0.0

    one_mora_ref, two_mora_ref, three_mora_ref = _timing_refs(config)
    resync_pause_row_count = resync_pause_insert_count
    completed_unit_count = syllable_unit_count + pause_unit_count + resync_pause_row_count
    return {
        'duration_scale': float(config['timing_model'].get('duration_scale', 1.0)),
        'one_mora_ref': one_mora_ref,
        'two_mora_ref': two_mora_ref,
        'three_mora_ref': three_mora_ref,
        'syllable_count': syllable_unit_count,
        'pause_count': pause_unit_count,
        'resync_pause_count': resync_pause_row_count,
        'total_unit_count': completed_unit_count,
        'unit_drift': {
            'max': round(max_abs, 4),
            'mean': round(mean, 4),
            'stddev': round(stddev, 4),
            'current': round(drift_cursor, 4),
            'label': _drift_label(drift_cursor),
        },
        'unit_drift_extension_count': drift_extension_count,
        'unit_drift_extension_rate': _diagnostic_rate(drift_extension_count, syllable_unit_count),
        'max_unit_drift_extension': round(max_drift_extension, 4),
        'non_accented_long_vowel_count': non_accented_long_vowel_count,
        'left_as_is_non_accented_long_vowel_count': left_as_is_non_accented_long_vowel_count,
        'drift_tolerance_effect': _diagnostic_rate(
            left_as_is_non_accented_long_vowel_count,
            non_accented_long_vowel_count,
        ),
        'adjusted_non_accented_long_vowel_count': adjusted_non_accented_long_vowel_count,
        'shortened_non_accented_long_vowel_count': shortened_non_accented_long_vowel_count,
        'lengthened_non_accented_long_vowel_count': lengthened_non_accented_long_vowel_count,
        'inserted_resync_pause_count': resync_pause_insert_count,
        'eligible_resync_pause_count': resync_pause_eligible_count,
        'resync_pause_insertion_rate': _diagnostic_rate(resync_pause_insert_count, resync_pause_eligible_count),
        'pause_with_residual_drift_count': pause_residual_post_unit_drift_count,
        'pause_with_residual_drift_rate': _diagnostic_rate(
            pause_residual_post_unit_drift_count,
            pause_unit_count,
        ),
    }


def build_phone_rows(
    tilde_text: str,
    phonetize_config: dict[str, Any] | None = None,
    input_frontmatter: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    tilde_text = _normalize_terminal_line_break(tilde_text)
    rows: list[dict[str, str]] = []
    syllable: list[dict[str, str]] = []
    short_pause_chars, long_pause_chars, short_pause_regex, long_pause_regex = _resolve_pause_punctuation_rules(
        input_frontmatter
    )

    def _finish(boundary_code: str) -> None:
        nonlocal syllable
        _finalize_syllable(rows, syllable, boundary_code)
        syllable = []

    def _consume_eol_run(start_index: int) -> tuple[str, int]:
        end_index = start_index
        while end_index < len(tilde_text) and tilde_text[end_index] == '\n':
            end_index += 1
        newline_count = end_index - start_index
        return EOL_TEXT * newline_count, end_index

    index = 0
    while index < len(tilde_text):
        symbol = tilde_text[index]
        if symbol == '~':
            if syllable:
                syllable[-1]['accent'] = 'A'
            elif rows:
                rows[-1]['accent'] = 'A'
            index += 1
            continue
        if symbol in {SYL_SEPARATOR, '.'}:
            _finish('I')
            index += 1
            continue
        if symbol == '-':
            _finish('E')
            index += 1
            continue
        if symbol in INTERNAL_MERGE_CHARS:
            _finish('L')
            index += 1
            continue
        if symbol == WORD_LINKER:
            _finish('X')
            index += 1
            continue
        if symbol == ' ':
            _finish('F')
            index += 1
            continue
        if symbol == '\n':
            _finish('F')
            eol_text, index = _consume_eol_run(index)
            rows.append(_new_pause_row(eol_text, pause_type='S', length_code='L'))
            continue
        if symbol == OPEN_ESCAPE:
            close_index = tilde_text.find(CLOSE_ESCAPE, index + 1)
            if close_index < 0:
                raise ValueError('Invalid _tilde input for phonetizer: unterminated armored span')
            _append_armored_pause_rows(
                tilde_text[index + 1 : close_index],
                rows,
                _finish,
                short_pause_chars=short_pause_chars,
                long_pause_chars=long_pause_chars,
                short_pause_regex=short_pause_regex,
                long_pause_regex=long_pause_regex,
            )
            index = close_index + 1
            continue
        if symbol in short_pause_chars or symbol in long_pause_chars or symbol == '…':
            suite_text, next_index = _consume_pause_suite(
                tilde_text,
                index,
                short_pause_chars=short_pause_chars,
                long_pause_chars=long_pause_chars,
            )
            pause_type, is_long = _classify_pause_suite(
                suite_text,
                short_pause_chars=short_pause_chars,
                long_pause_chars=long_pause_chars,
                short_pause_regex=short_pause_regex,
                long_pause_regex=long_pause_regex,
            )
            _finish('F')
            rows.append(_new_pause_row(suite_text, pause_type=pause_type, length_code='L' if is_long else 'S'))
            index = next_index
            continue
        if symbol in INPUT_CHARACTER_LABELS and symbol not in {INNER_PUNCT_TEXT, PHRASAL_PUNCT_TEXT}:
            syllable.append(_new_segment_seed(symbol))
            index += 1
            continue
        index += 1
    _finish('F')
    _resolve_transition_rows(rows)
    _apply_emphatic_vowel_coloring(rows, phonetize_config)
    return rows


