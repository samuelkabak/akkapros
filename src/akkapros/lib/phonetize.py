from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any

from akkapros.lib.constants import (
    CLOSE_ESCAPE,
    HIATUS_MARKER,
    OPEN_ESCAPE,
    SYL_SEPARATOR,
    WORD_LINKER,
)
from akkapros.lib.frontmatter import resolve_inherited_punctuation_options
from akkapros.lib.utils import compile_contextual_regex


PHONETIZE_SECTION = 'phonetize'
PHONETIZE_SECTION_HELP = 'Options used by the phonetizer CLI and by fullprosmaker during the phonetize stage.'


@dataclass(frozen=True)
class PhonetizeField:
    default: Any
    kind: str
    description: str
    choices: tuple[str, ...] | None = None


def _field(default: Any, kind: str, description: str, choices: tuple[str, ...] | None = None) -> PhonetizeField:
    return PhonetizeField(default=default, kind=kind, description=description, choices=choices)


PHONETIZE_SCHEMA: dict[str, Any] = {
    'process': {
        '__comment__': None,
        'geminate_policy': _field(
            'corrective',
            'string',
            'geminate realization policy\n- cumulative: keep coda duration + onset duration instead of correcting to the configured geminate target\n- corrective: correct the sequence to the configured geminate target',
            choices=('cumulative', 'corrective'),
        ),
        'accentuation_distribution_policy': _field(
            '85_15',
            'string',
            'this policy indicates how the accentuation mora (0.5 * cvc_reference) is distributed, format N_M\nN = percentage on the accentuated segment; M = percentage on the adjacent segment\nDistribution stops when legality ranges would be challenged; if full assignment is impossible, Phase 2 must fail fatally.\nAllowed values: 100_0, 85_15, 70_30',
            choices=('100_0', '85_15', '70_30'),
        ),
        'short_pause_policy': _field(
            'strict',
            'string',
            'short pause discharge policy\n- strict: the pause must realize a preferred legal short-band target derived from the nearest integer multiple of cvc_reference, and it must discharge drift reserve through that target as far as the band allows; config validation should warn if no integer multiple N * cvc_reference remains inside the empirically grounded short-pause band, and should fail only if the nearest-multiple gap exceeds the vowel perception-gap threshold used by shared semantic verification\n- best_effort: the pause may choose any legal short-band realization that maximizes drift discharge, and any remainder carries into the following phrase',
            choices=('strict', 'best_effort'),
        ),
        'drift_policy': _field(
            'strict',
            'string',
            'drift recovery policy\n- strict: use running drift first, then legal vowel adjustment, and fail if the mismatch still cannot be resolved\n- extensible: use running drift first, then legal vowel adjustment, then extend drift beyond drift_tolerance if needed',
            choices=('strict', 'extensible'),
        ),
        'drift_tolerance': _field(
            12,
            'int',
            'maximum local timing mismatch tolerated before the algorithm must fail',
        ),
    },
    'timing_model': {
        '__comment__': None,
        'speech': {
            '__comment__': None,
            'wpm': _field(193, 'int', 'Speech-rate estimate used by timing and pause logic.'),
            'pause_ratio': _field(35, 'int', 'Share of total time reserved for pauses.'),
        },
        'durations': {
            '__comment__': None,
            'segmental_ceiling': _field(
                310,
                'int',
                'Upper ordinary duration for one vowel or consonant. Model-facing ceiling from comparative duration limits; does not apply to pauses or CVC totals.',
            ),
            'cvc_reference': _field(
                305,
                'int',
                'Central heavy-syllable timing reference used by accentuation and pause alignment. Set inside the empirically grounded CVC interval 286-306 ms. This keeps the control value conservative and compatible with pause-band alignment whenever at least one integer multiple N * cvc_reference falls inside a configured pause band.',
            ),
            'consonants': {
                '__comment__': None,
                'closure': {
                    '__comment__': 'Stop-like closure class. Includes lexical ʾ.',
                    'onset': _field(108, 'int', 'Default onset closure duration. Direct comparative stop-closure anchor.'),
                    'coda': _field(103, 'int', 'Default post-vocalic closure duration. Direct comparative coda/post-vocalic stop anchor.'),
                    'geminate': _field(195, 'int', 'Default geminate closure target. Summary point for the attested stop-geminate band.'),
                    'special_realization': {
                        '__comment__': None,
                        'hiatus': _field(18, 'int', 'Hiatus or zero-onset marker between adjacent vowels. Unstressed light glottal-stop realization; stressed cases defer to full geminated closure timing.'),
                    },
                    'perception_limits': {
                        '__comment__': None,
                        'geminate_min': _field(180, 'int', 'Earliest closure duration treated as geminate-like. Perceptual threshold from the stop singleton/geminate contrast, not the lowest measured token.'),
                    },
                },
                'fricative': {
                    '__comment__': 'Fricative class. Heavier than closures by manner, but less directly grounded than the stop row.',
                    'onset': _field(137, 'int', 'Default onset fricative duration. Derived from closure onset plus fricative manner delta.'),
                    'coda': _field(142, 'int', 'Default post-vocalic fricative duration. Current heavy post-vocalic anchor used by the simplified row.'),
                    'geminate': _field(279, 'int', 'Default geminate fricative target. Exploratory value based on the current onset + post-vocalic row.'),
                    'perception_limits': {
                        '__comment__': None,
                        'geminate_min': _field(152, 'int', 'Earliest fricative duration treated as held or geminate-like. Class-specific perceptual floor from weak fricative gemination evidence.'),
                    },
                },
                'sonorant': {
                    '__comment__': 'Sonorant, nasal, and glide class.',
                    'onset': _field(89, 'int', 'Default onset sonorant duration. Set from the clearer singleton liquid onset anchor.'),
                    'coda': _field(70, 'int', 'Default post-vocalic sonorant duration. Structural minimum retained on the coda side of the row.'),
                    'geminate': _field(163, 'int', 'Default geminate sonorant target. Set from the direct glide geminate region.'),
                    'special_realization': {
                        '__comment__': None,
                        'vowel_transition': _field(11, 'int', 'Diphthong-internal or glide-like VV transition marker. Unstressed light glide realization; stressed cases defer to full geminated glide timing.'),
                    },
                    'perception_limits': {
                        '__comment__': None,
                        'geminate_min': _field(152, 'int', 'Earliest sonorant duration treated as geminate-like. Lower perceptual boundary from moraic nasal/liquid comparison.'),
                    },
                },
            },
            'vowels': {
                '__comment__': None,
                'short': _field(85, 'int', 'Default short-vowel duration. Production anchor from the retained short-vowel baseline.'),
                'long': _field(160, 'int', 'Default long-vowel duration. Production anchor from the retained long-vowel baseline.'),
                'very_long': _field(220, 'int', 'Default very-long vowel duration. Contextual extension anchor, not ordinary lexical default.'),
                'perception_limits': {
                    '__comment__': None,
                    'short_min': _field(40, 'int', 'Minimum duration still treated as a realized short-vowel nucleus.'),
                    'long_min': _field(123, 'int', 'Earliest duration treated as long. Midpoint-style boundary derived from short and long anchors.'),
                    'very_long_min': _field(190, 'int', 'Earliest duration treated as very long. Midpoint-style boundary derived from long and very-long anchors.'),
                    'max': _field(240, 'int', 'Upper ordinary bound for contextual vowel extension.'),
                },
            },
            'pauses': {
                '__comment__': None,
                'short': {
                    '__comment__': 'Default short-pause band. Empirically grounded short-pause region from comparative studies. Rhythmic alignment remains possible when at least one integer multiple N * cvc_reference falls inside this band without redefining the empirical range.',
                    'min': _field(600, 'int', 'Minimum short-pause duration.'),
                    'max': _field(680, 'int', 'Maximum short-pause duration.'),
                },
                'long': {
                    '__comment__': 'Default long-pause band. Clause-boundary range from comparative pause data. If rhythmic alignment is used, enumerate all integer multiples N * cvc_reference inside this band. Choose the candidate nearest the band center; if two are equally near, choose the smaller one.',
                    'min': _field(1200, 'int', 'Minimum long-pause duration.'),
                    'max': _field(1780, 'int', 'Maximum long-pause duration.'),
                },
            },
        },
    },
}


PROCESS_KEYS = (
    'geminate_policy',
    'accentuation_distribution_policy',
    'short_pause_policy',
    'drift_policy',
    'drift_tolerance',
)

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
    'text',
)
PHONE_ROW_DURATION_PLACEHOLDER = '0000'
INNER_PUNCT_TEXT = ':inner-punct:'
PHRASAL_PUNCT_TEXT = ':phrasal-punct:'
EOL_TEXT = '<EOL>'

CONSONANT_HIATUS = set('˙')
CONSONANT_VOWEL_TRANSITION = set('¨')
CONSONANT_CLOSURE = set('bdgkptṭqʾ')
CONSONANT_FRICATIVE = set('szšṣḥḫʿ')
CONSONANT_SONORANT = set('lrmnwy')
EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}

SHORT_VOWELS = set('aeiu')
LONG_VOWELS = set('āēīūâêîû')
LOW_VOWELS = set('aāâ')
MID_VOWELS = set('eēê')
HIGH_VOWELS = set('iuīūîû')

SHORT_PAUSE_PUNCTUATION_CHARS = {',', ';', ':', '—', '–', '(', ')', '«', '»', '“', '”', '‘', '’', '"', "'", '/', '\\', '|', '†', '‡'}
LONG_PAUSE_PUNCTUATION_CHARS = {'.', '?', '!', '[', ']', '{', '}', '<', '>', '*', '#'}
INTERNAL_MERGE_CHARS = {'&', '_'}
DEFAULT_SHORT_PAUSE_PUNCTUATION_PATTERNS: tuple[str, ...] = ()
DEFAULT_LONG_PAUSE_PUNCTUATION_PATTERNS: tuple[str, ...] = ()

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
    ('BE', 'b', 'C', 'C', 'P'),
    ('DA', 'd', 'C', 'C', 'P'),
    ('GI', 'ɡ', 'C', 'C', 'P'),
    ('KA', 'k', 'C', 'C', 'P'),
    ('PA', 'p', 'C', 'C', 'P'),
    ('TU', 'tˤ', 'C', 'C', 'E'),
    ('QU', 'q', 'C', 'C', 'E'),
    ('SU', 'sˤ', 'C', 'F', 'E'),
    ('SA', 's', 'C', 'F', 'P'),
    ('ZI', 'z', 'C', 'F', 'P'),
    ('SI', 'ʃ', 'C', 'F', 'P'),
    ('LA', 'l', 'C', 'S', 'P'),
    ('MI', 'm', 'C', 'S', 'P'),
    ('NA', 'n', 'C', 'S', 'P'),
    ('RE', 'r', 'C', 'S', 'P'),
    ('ET', 'ħ', 'C', 'F', 'P'),
    ('HE', 'x', 'C', 'F', 'P'),
    ('AI', 'ʕ', 'C', 'F', 'P'),
    ('AL', 'ʔ', 'C', 'C', 'P'),
    ('WA', 'w', 'C', 'S', 'P'),
    ('YI', 'j', 'C', 'S', 'P'),
    ('TA', 't', 'C', 'C', 'P'),
    ('AA', 'a', 'V', 'L', 'P'),
    ('EE', 'e', 'V', 'M', 'P'),
    ('II', 'i', 'V', 'H', 'P'),
    ('UU', 'u', 'V', 'H', 'P'),
    ('AO', 'ɑ', 'V', 'L', 'P'),
    ('EO', 'ɛ', 'V', 'M', 'P'),
    ('IO', 'ɨ', 'V', 'H', 'P'),
    ('UO', 'ʊ', 'V', 'H', 'P'),
    ('SP', '|', 'S', 'S', 'P'),
    ('ZP', '‖', 'S', 'S', 'P'),
)

REALIZATION_CODE_METADATA = {
    code: {
        'ipa': ipa,
        'category': category,
        'type': type_code,
        'emphaticity': emphaticity,
    }
    for code, ipa, category, type_code, emphaticity in REALIZATION_CODE_ROWS
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


def _is_field(node: Any) -> bool:
    return isinstance(node, PhonetizeField)


def build_default_phonetize_config() -> dict[str, Any]:
    def _build(node: dict[str, Any]) -> dict[str, Any]:
        built: dict[str, Any] = {}
        for key, value in node.items():
            if key == '__comment__':
                continue
            if _is_field(value):
                built[key] = deepcopy(value.default)
            else:
                built[key] = _build(value)
        return built

    return _build(PHONETIZE_SCHEMA)


def iter_phonetize_fields() -> list[tuple[tuple[str, ...], PhonetizeField]]:
    items: list[tuple[tuple[str, ...], PhonetizeField]] = []

    def _walk(prefix: tuple[str, ...], node: dict[str, Any]) -> None:
        for key, value in node.items():
            if key == '__comment__':
                continue
            path = prefix + (key,)
            if _is_field(value):
                items.append((path, value))
            else:
                _walk(path, value)

    _walk((PHONETIZE_SECTION,), PHONETIZE_SCHEMA)
    return items


def get_phonetize_field(relative_path: tuple[str, ...]) -> PhonetizeField:
    node: Any = PHONETIZE_SCHEMA
    for part in relative_path:
        if not isinstance(node, dict) or part not in node:
            raise KeyError(relative_path)
        node = node[part]
    if not _is_field(node):
        raise KeyError(relative_path)
    return node


def validate_phonetize_source(section: Any, coerce_scalar) -> dict[str, Any]:
    if section is None:
        return {}
    if not isinstance(section, dict):
        raise ValueError('Config section \'phonetize\' must be a mapping')

    def _validate(raw: dict[str, Any], schema: dict[str, Any], prefix: tuple[str, ...]) -> dict[str, Any]:
        allowed = {key for key in schema if key != '__comment__'}
        unknown_keys = sorted(set(raw) - allowed)
        if unknown_keys:
            joined = ', '.join('.'.join(prefix + (key,)) for key in unknown_keys)
            raise ValueError(f'Unknown config keys: {joined}')

        validated: dict[str, Any] = {}
        for key, raw_value in raw.items():
            spec = schema[key]
            path = '.'.join(prefix + (key,))
            if _is_field(spec):
                if raw_value is None:
                    validated[key] = None
                    continue
                value = coerce_scalar(raw_value, spec.kind)
                if spec.choices is not None and value not in spec.choices:
                    raise ValueError(f'Invalid value for {path}: {value!r}; expected one of {spec.choices!r}')
                validated[key] = value
            else:
                if raw_value is None:
                    validated[key] = None
                    continue
                if not isinstance(raw_value, dict):
                    raise ValueError(f'Config path {path!r} must be a mapping')
                validated[key] = _validate(raw_value, spec, prefix + (key,))
        return validated

    return _validate(section, PHONETIZE_SCHEMA, (PHONETIZE_SECTION,))


def normalize_phonetize_config(section: Any, coerce_scalar) -> dict[str, Any]:
    defaults = build_default_phonetize_config()
    validated = validate_phonetize_source(section, coerce_scalar) if section not in ({}, None) else {}

    def _merge(target: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
        for key, value in source.items():
            if value is None:
                continue
            if isinstance(value, dict):
                _merge(target[key], value)
            else:
                target[key] = deepcopy(value)
        return target

    return _merge(defaults, validated)


def render_documented_phonetize_section(
    lines: list[str],
    values: dict[str, Any],
    *,
    append_comment,
    dump_scalar,
) -> None:
    append_comment(lines, PHONETIZE_SECTION_HELP)
    lines.append(f'{PHONETIZE_SECTION}:')

    def _render(node: dict[str, Any], schema: dict[str, Any], indent: int) -> None:
        prefix = ' ' * indent
        for key, spec in schema.items():
            if key == '__comment__':
                continue
            value = node[key]
            if _is_field(spec):
                append_comment(lines, spec.description, indent=indent)
                lines.append(f'{prefix}{key}: {dump_scalar(value)}')
            else:
                comment = spec.get('__comment__')
                if comment:
                    append_comment(lines, comment, indent=indent)
                lines.append(f'{prefix}{key}:')
                _render(value, spec, indent + 2)

    _render(values, PHONETIZE_SCHEMA, 2)


def get_relative_value(config: dict[str, Any], relative_path: tuple[str, ...]) -> Any:
    current: Any = config
    for part in relative_path:
        current = current[part]
    return deepcopy(current)


def set_relative_value(config: dict[str, Any], relative_path: tuple[str, ...], value: Any) -> dict[str, Any]:
    updated = deepcopy(config)
    current = updated
    for part in relative_path[:-1]:
        current = current.setdefault(part, {})
    current[relative_path[-1]] = value
    return updated


def apply_timing_override(config: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    parts = tuple(part for part in path.split('.') if part)
    if len(parts) < 4 or parts[0] != PHONETIZE_SECTION or parts[1] != 'timing_model':
        raise ValueError(f'Invalid phonetize timing-model override path: {path}')
    get_phonetize_field(parts[1:])
    return set_relative_value(config, parts[1:], value)


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
        'text': symbol,
    }


def _new_pause_row(text: str, *, is_long: bool) -> dict[str, str]:
    label = 'ZEN' if is_long else 'SES'
    return {
        'label': label,
        'category': 'S',
        'type': 'S',
        'length': 'L' if is_long else 'S',
        'position': 'S',
        'boundary': 'N',
        'accent': 'P',
        'realization': 'ZP' if is_long else 'SP',
        'duration': PHONE_ROW_DURATION_PLACEHOLDER,
        'text': text,
    }


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
    emphatic_onset = any(
        row['position'] == 'O' and row['text'] in EMPHATIC_CONSONANTS
        for row in syllable
    )
    for row in syllable:
        if row['category'] == 'V':
            row['realization'] = _choose_vowel_realization(row['label'], emphatic_onset)
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
        if any(regex.search(normalized) for regex in long_pause_regex) or any(
            symbol in long_pause_chars for symbol in normalized if not symbol.isspace()
        ):
            finish_syllable('F')
            rows.append(_new_pause_row(normalized, is_long=True))
            return
        if any(regex.search(normalized) for regex in short_pause_regex) or any(
            symbol in short_pause_chars for symbol in normalized if not symbol.isspace()
        ):
            finish_syllable('F')
            rows.append(_new_pause_row(normalized, is_long=False))
            return
    for symbol in armored_text:
        if symbol == '\n':
            finish_syllable('F')
            rows.append(_new_pause_row(EOL_TEXT, is_long=True))
            continue
        if symbol.isspace():
            continue
        if symbol in short_pause_chars:
            finish_syllable('F')
            rows.append(_new_pause_row(symbol, is_long=False))
            continue
        if symbol in long_pause_chars:
            finish_syllable('F')
            rows.append(_new_pause_row(symbol, is_long=True))
            continue
        raise ValueError(f'Unsupported armored phonetizer content: {OPEN_ESCAPE}{armored_text}{CLOSE_ESCAPE}')


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


def build_phone_rows(
    tilde_text: str,
    phonetize_config: dict[str, Any] | None = None,
    input_frontmatter: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    _ = phonetize_config
    rows: list[dict[str, str]] = []
    syllable: list[dict[str, str]] = []
    short_pause_chars, long_pause_chars, short_pause_regex, long_pause_regex = _resolve_pause_punctuation_rules(
        input_frontmatter
    )

    def _finish(boundary_code: str) -> None:
        nonlocal syllable
        _finalize_syllable(rows, syllable, boundary_code)
        syllable = []

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
            rows.append(_new_pause_row(EOL_TEXT, is_long=True))
            index += 1
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
        if symbol in short_pause_chars:
            _finish('F')
            rows.append(_new_pause_row(symbol, is_long=False))
            index += 1
            continue
        if symbol in long_pause_chars:
            _finish('F')
            rows.append(_new_pause_row(symbol, is_long=True))
            index += 1
            continue
        if symbol in INPUT_CHARACTER_LABELS and symbol not in {INNER_PUNCT_TEXT, PHRASAL_PUNCT_TEXT}:
            syllable.append(_new_segment_seed(symbol))
            index += 1
            continue
        index += 1
    _finish('F')
    _resolve_transition_rows(rows)
    return rows


def serialize_phone_row(row: dict[str, str]) -> str:
    head = '-'.join(row[field] for field in PHONE_ROW_FIELDS[:-1])
    return f'{head}:{row[PHONE_ROW_FIELDS[-1]]}'


def serialize_phone_rows(rows: list[dict[str, str]]) -> str:
    return '\n'.join(serialize_phone_row(row) for row in rows) + '\n'


def parse_phone_row(line: str) -> dict[str, str]:
    stripped = line.strip()
    if not stripped:
        raise ValueError('Phone row is empty')
    head, sep, text = stripped.partition(':')
    if not sep:
        raise ValueError(f'Invalid phone row: {line!r}')
    parts = head.split('-')
    if len(parts) != len(PHONE_ROW_FIELDS) - 1:
        raise ValueError(f'Invalid phone row field count: {line!r}')
    return dict(zip(PHONE_ROW_FIELDS, parts + [text]))


def reconstruct_tilde_from_phone_rows(rows: list[dict[str, str]]) -> str:
    pieces: list[str] = []
    previous_boundary = ''
    for row in rows:
        if row['category'] != 'S' and previous_boundary == 'F':
            pieces.append(' ')
        if row['category'] == 'S':
            pieces.append('\n' if row['text'] == EOL_TEXT else row['text'])
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


def run_tests() -> bool:
    cases = [
        lambda: CONSONANT_HIATUS == set('˙') and CONSONANT_VOWEL_TRANSITION == set('¨'),
        lambda: INPUT_CHARACTER_LABELS['ṣ'] == 'SUD' and INPUT_CHARACTER_LENGTHS['û'] == 'L',
        lambda: REALIZATION_CODE_METADATA['SP']['category'] == 'S' and INPUT_TO_REALIZATION_CODES['ENA'] == ('WA', 'YI'),
        lambda: _test_emphatic_vowel_and_row_format(),
        lambda: _test_boundary_reconstruction(),
        lambda: _test_transition_resolution(),
    ]
    return all(case() for case in cases)


def _test_emphatic_vowel_and_row_format() -> bool:
    rows = build_phone_rows('qā')
    if rows[0]['realization'] != 'QU' or rows[1]['realization'] != 'AO':
        return False
    line = serialize_phone_row(rows[0])
    return parse_phone_row(line) == rows[0] and rows[0]['duration'] == PHONE_ROW_DURATION_PLACEHOLDER


def _test_boundary_reconstruction() -> bool:
    sample = 'šit·ku·nat-ma'
    rows = build_phone_rows(sample)
    return reconstruct_tilde_from_phone_rows(rows) == sample


def _test_transition_resolution() -> bool:
    rows = build_phone_rows('a¨u')
    transition = next(row for row in rows if row['label'] == 'ENA')
    return transition['realization'] == 'WA'