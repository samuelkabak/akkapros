from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
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


PHONETIZE_SECTION = 'phonetize'
PHONETIZE_SECTION_HELP = 'Options used by the phonetizer CLI and by fullprosmaker during the phonetize stage.'
REMOVED_TIMING_MODEL_KEYS = frozenset({'short_pause_policy', 'drift_policy'})


@dataclass(frozen=True)
class PhonetizeField:
    default: Any
    kind: str
    description: str
    choices: tuple[str, ...] | None = None


@dataclass(frozen=True)
class VerificationIssue:
    severity: str
    path: str
    relation: str
    reason: str
    summary_hint: str | None = None


@dataclass(frozen=True)
class PhonetizeVerificationResult:
    failures: tuple[VerificationIssue, ...]
    warnings: tuple[VerificationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def status(self) -> str:
        if self.failures:
            return 'failure'
        if self.warnings:
            return 'pass-with-warnings'
        return 'pass'


def _field(default: Any, kind: str, description: str, choices: tuple[str, ...] | None = None) -> PhonetizeField:
    return PhonetizeField(default=default, kind=kind, description=description, choices=choices)


PHONETIZE_SCHEMA: dict[str, Any] = {
    'process': {
        '__comment__': None,
        'intonation': {
            '__comment__': None,
            'f0': _field(120, 'int', 'Baseline speaker pitch in Hertz used for emitted .pho rows.'),
            'stress': _field('H2', 'string', 'Compact intonation preset for non-pause-governed stressed syllables. Normalized to canonical row token form.'),
            'question': _field('H3', 'string', 'Compact intonation preset for question-final contours. Normalized to canonical row token form.'),
            'statement': _field('L2', 'string', 'Compact intonation preset for statement-final contours. Normalized to canonical row token form.'),
            'exclamation': _field('H4', 'string', 'Compact intonation preset for exclamatory contours. Normalized to canonical row token form.'),
            'continuation': _field('H1', 'string', 'Compact intonation preset for continuation contours. Normalized to canonical row token form.'),
        },
        'timing_model': {
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
            'drift_tolerance': _field(
                0,
                'int',
                'maximum local timing mismatch tolerated before the algorithm must fail',
            ),
            'speech': {
                '__comment__': None,
                'wpm': _field(193, 'int', 'Speech-rate estimate used by timing and pause logic.'),
                'pause_ratio': _field(35, 'int', 'Share of total time reserved for pauses. Shared semantic verification fails outside 0 < pause_ratio < 100 and emits a warning when pause_ratio > 70.'),
            },
            'durations': {
                '__comment__': None,
                'segmental_ceiling': _field(
                    310,
                    'int',
                    'Global validation ceiling for class-local consonant gemination maxima and the vowel elongation max. This key remains part of the config and verification surface, but runtime consonant saturation uses class-local gemination_max values instead.',
                ),
                'segmental_floor': _field(
                    10,
                    'int',
                    'Global validation floor for vowel minima, consonant anchors and minima, and the hiatus and vowel-transition special realizations. Validation-only; not a runtime timing control.',
                ),
                'cvc_reference': _field(
                    300,
                    'int',
                    'Central heavy-syllable timing reference used by accentuation and pause alignment. Set inside the empirically grounded CVC interval 286-306 ms. This keeps the control value conservative and compatible with pause-band alignment whenever at least one integer multiple N * cvc_reference falls inside a configured pause band.',
                ),
                'consonants': {
                    '__comment__': None,
                    'closure': {
                        '__comment__': 'Stop-like closure class. Includes lexical ʾ.',
                        'onset': _field(89, 'int', 'Default onset closure duration. Direct comparative stop-closure anchor.'),
                        'coda': _field(87, 'int', 'Default post-vocalic closure duration. Direct comparative coda/post-vocalic stop anchor.'),
                        'geminate': _field(175, 'int', 'Default geminate closure target. Summary point for the attested stop-geminate band.'),
                        'special_realization': {
                            '__comment__': None,
                            'hiatus': _field(35, 'int', 'Hiatus or zero-onset marker between adjacent vowels. Unstressed light glottal-stop realization; stressed cases defer to full geminated closure timing.'),
                        },
                        'perception_limits': {
                            '__comment__': None,
                            'geminate_min': _field(145, 'int', 'Earliest closure duration treated as geminate-like. Perceptual threshold from the stop singleton/geminate contrast, not the lowest measured token.'),
                            'gemination_max': _field(260, 'int', 'Latest closure duration treated as the legal runtime geminate-like maximum. Runtime same-consonant saturation and accent-extension ceilings use this class-local bound rather than the global segmental ceiling.'),
                        },
                    },
                    'fricative': {
                        '__comment__': 'Fricative class. Heavier than closures by manner, but less directly grounded than the stop row.',
                        'onset': _field(115, 'int', 'Default onset fricative duration. Derived from closure onset plus fricative manner delta.'),
                        'coda': _field(112, 'int', 'Default post-vocalic fricative duration. Current heavy post-vocalic anchor used by the simplified row.'),
                        'geminate': _field(210, 'int', 'Default geminate fricative target. Retuned summary point for the live fricative geminate-like row.'),
                        'perception_limits': {
                            '__comment__': None,
                            'geminate_min': _field(163, 'int', 'Earliest fricative duration treated as held or geminate-like. Retuned class-specific perceptual floor.'),
                            'gemination_max': _field(290, 'int', 'Latest fricative duration treated as the legal runtime geminate-like maximum. Runtime same-consonant saturation and accent-extension ceilings use this class-local bound rather than the global segmental ceiling.'),
                        },
                    },
                    'sonorant': {
                        '__comment__': 'Sonorant, nasal, and glide class.',
                        'onset': _field(105, 'int', 'Default onset sonorant duration. Set from the clearer singleton liquid onset anchor.'),
                        'coda': _field(100, 'int', 'Default post-vocalic sonorant duration. Structural minimum retained on the coda side of the row.'),
                        'geminate': _field(190, 'int', 'Default geminate sonorant target. Set from the direct glide geminate region.'),
                        'special_realization': {
                            '__comment__': None,
                            'vowel_transition': _field(25, 'int', 'Diphthong-internal or glide-like VV transition marker. Unstressed light glide realization; stressed cases defer to full geminated glide timing.'),
                        },
                        'perception_limits': {
                            '__comment__': None,
                            'geminate_min': _field(148, 'int', 'Earliest sonorant duration treated as geminate-like. Lower perceptual boundary from moraic nasal/liquid comparison.'),
                            'gemination_max': _field(275, 'int', 'Latest sonorant duration treated as the legal runtime geminate-like maximum. Runtime same-consonant saturation and accent-extension ceilings use this class-local bound rather than the global segmental ceiling.'),
                        },
                    },
                },
                'vowels': {
                    '__comment__': None,
                    'short': _field(110, 'int', 'Default short-vowel duration. Production anchor from the retained short-vowel baseline.'),
                    'long': _field(160, 'int', 'Default long-vowel duration. Production anchor from the retained long-vowel baseline.'),
                    'very_long': _field(260, 'int', 'Default very-long vowel duration. Contextual extension anchor, not ordinary lexical default.'),
                    'perception_limits': {
                        '__comment__': None,
                        'short_min': _field(60, 'int', 'Minimum duration still treated as a realized short-vowel nucleus.'),
                        'long_min': _field(153, 'int', 'Earliest duration treated as long. Midpoint-style boundary derived from short and long anchors.'),
                        'very_long_min': _field(233, 'int', 'Earliest duration treated as very long. Midpoint-style boundary derived from long and very-long anchors. Ordinary non-accentual long-vowel recovery must stop at very_long_min - 1.'),
                        'elongation_max': _field(280, 'int', 'Upper contextual bound for vowel extension. Ordinary non-accentual long-vowel recovery still stops at very_long_min - 1.'),
                    },
                },
                'pauses': {
                    '__comment__': None,
                    'mini': {
                        '__comment__': 'Default mini-pause band. Non-punctuation recovery gap used only when the stream is ahead of the beat and no punctuation-owned pause already follows the current merged unit boundary.',
                        'min': _field(100, 'int', 'Minimum mini-pause duration.'),
                        'max': _field(200, 'int', 'Maximum mini-pause duration.'),
                    },
                    'short': {
                        '__comment__': 'Default short-pause band. Empirically grounded short-pause region from comparative studies. Rhythmic alignment remains possible when at least one integer multiple N * cvc_reference falls inside this band without redefining the empirical range.',
                        'min': _field(520, 'int', 'Minimum short-pause duration.'),
                        'max': _field(680, 'int', 'Maximum short-pause duration.'),
                    },
                    'long': {
                        '__comment__': 'Default long-pause band. Clause-boundary range from comparative pause data. If rhythmic alignment is used, enumerate all integer multiples N * cvc_reference inside this band. Choose the candidate nearest the band center; if two are equally near, choose the smaller one.',
                        'min': _field(1100, 'int', 'Minimum long-pause duration.'),
                        'max': _field(1780, 'int', 'Maximum long-pause duration.'),
                    },
                },
            },
        },
    },
}


PROCESS_KEYS = (
    'geminate_policy',
    'accentuation_distribution_policy',
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
    'drift',
    'intonation',
    'text',
)
PHONE_ROW_DURATION_PLACEHOLDER = '0000'
PHONE_ROW_DRIFT_NEUTRAL = '+000'
PHONE_ROW_INTONATION_NEUTRAL = 'M0C'
INNER_PUNCT_TEXT = ':inner-punct:'
PHRASAL_PUNCT_TEXT = ':phrasal-punct:'
EOL_TEXT = '<EOL>'
MINI_PAUSE_LABEL = 'MEN'
MINI_PAUSE_TYPE = 'M'
MINI_PAUSE_REALIZATION = 'MP'
MINI_PAUSE_TEXT = ' '

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

SHORT_PAUSE_PUNCTUATION_CHARS = {',', ';', ':', '—', '–', '…', '(', ')', '«', '»', '“', '”', '‘', '’', '"', "'", '/', '\\', '|', '†', '‡'}
LONG_PAUSE_PUNCTUATION_CHARS = {'.', '?', '!', '[', ']', '{', '}', '<', '>', '*', '#'}
INTERNAL_MERGE_CHARS = {'&', '_'}
DEFAULT_SHORT_PAUSE_PUNCTUATION_PATTERNS: tuple[str, ...] = ()
DEFAULT_LONG_PAUSE_PUNCTUATION_PATTERNS: tuple[str, ...] = ()
PRIMARY_CONTINUATION_PUNCTUATION_CHARS = {',', ';', ':', '—', '–', '…'}
QUESTION_PUNCTUATION_CHARS = {'?'}
EXCLAMATION_PUNCTUATION_CHARS = {'!'}
STATEMENT_PUNCTUATION_CHARS = {'.'}
INTONATION_FAMILY_SHAPES = {
    'H': 'C',
    'L': 'C',
    'M': 'C',
    'R': 'L',
    'F': 'L',
    'P': 'E',
    'V': 'E',
}
PAUSE_TYPE_TO_INTONATION_KEY = {
    'Q': 'question',
    'S': 'statement',
    'E': 'exclamation',
    'C': 'continuation',
}
INTONATION_PRESET_RE = re.compile(r'^[HLMRFPV][0-9](?:[CLE])?$')

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
    (MINI_PAUSE_REALIZATION, '.', '_', 'S', 'S', 'P'),
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
    (MINI_PAUSE_LABEL, MINI_PAUSE_REALIZATION),
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


def build_default_phonetize_verification_config() -> dict[str, Any]:
    return build_default_phonetize_config()


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
            if prefix == (PHONETIZE_SECTION, 'process', 'timing_model'):
                removed = [key for key in unknown_keys if key in REMOVED_TIMING_MODEL_KEYS]
                if removed:
                    joined = ', '.join('.'.join(prefix + (key,)) for key in removed)
                    raise ValueError(
                        f'Removed config keys (CR-061): {joined}. '
                        'These options were removed and behavior is now fixed internally.'
                    )
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
    if len(parts) < 5 or parts[0] != PHONETIZE_SECTION or parts[1] != 'process' or parts[2] != 'timing_model':
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


def _new_mini_pause_row() -> dict[str, str]:
    return {
        'label': MINI_PAUSE_LABEL,
        'category': 'S',
        'type': MINI_PAUSE_TYPE,
        'length': 'S',
        'position': 'S',
        'boundary': 'N',
        'accent': 'P',
        'realization': MINI_PAUSE_REALIZATION,
        'duration': PHONE_ROW_DURATION_PLACEHOLDER,
        'drift': PHONE_ROW_DRIFT_NEUTRAL,
        'intonation': PHONE_ROW_INTONATION_NEUTRAL,
        'text': MINI_PAUSE_TEXT,
    }


def _is_mini_pause_row(row: dict[str, str]) -> bool:
    return (
        row['category'] == 'S'
        and row['label'] == MINI_PAUSE_LABEL
        and row['type'] == MINI_PAUSE_TYPE
        and row['realization'] == MINI_PAUSE_REALIZATION
    )


def _normalize_intonation_token(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError('Intonation preset must be a string token.')
    token = value.strip().upper()
    if not INTONATION_PRESET_RE.fullmatch(token):
        raise ValueError(f'Invalid intonation token: {value!r}')
    family = token[0]
    degree = token[1]
    shape = token[2] if len(token) == 3 else INTONATION_FAMILY_SHAPES[family]
    if INTONATION_FAMILY_SHAPES[family] != shape:
        raise ValueError(f'Invalid shape {shape!r} for intonation family {family!r}.')
    if family == 'M' and (degree != '0' or shape != 'C'):
        raise ValueError('Neutral medium intonation is only valid as M0C.')
    return f'{family}{degree}{shape}'


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


def _runtime_intonation_config(intonation_config: dict[str, Any]) -> dict[str, Any]:
    normalized = {'f0': intonation_config['f0']}
    for key in ('stress', 'question', 'statement', 'exclamation', 'continuation'):
        normalized[key] = _normalize_intonation_token(str(intonation_config[key]))
    return normalized


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
    original_report = realize_phone_rows(original_rows, phonetize_config, allow_accentuation=False)
    accentuated_report = realize_phone_rows(accentuated_rows, phonetize_config, allow_accentuation=True)
    realize_row_intonation(original_rows, phonetize_config, accentuated=False)
    realize_row_intonation(accentuated_rows, phonetize_config, accentuated=True)
    return (original_rows, original_report), (accentuated_rows, accentuated_report)


def _merge_phonetize_config(phonetize_config: dict[str, Any] | None) -> dict[str, Any]:
    merged = build_default_phonetize_config()
    if not phonetize_config:
        return merged

    def _merge(target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                _merge(target[key], value)
            else:
                target[key] = deepcopy(value)

    _merge(merged, phonetize_config)
    return merged


def _runtime_view_phonetize_config(phonetize_config: dict[str, Any]) -> dict[str, Any]:
    timing_model = deepcopy(phonetize_config['process']['timing_model'])
    process = {key: deepcopy(timing_model[key]) for key in PROCESS_KEYS}
    model_only = {key: deepcopy(value) for key, value in timing_model.items() if key not in PROCESS_KEYS}
    return {
        'process': process,
        'intonation': _runtime_intonation_config(deepcopy(phonetize_config['process'].get('intonation', {}))),
        'timing_model': model_only,
    }


def _semitone_to_hz(base_f0: int, semitones: int) -> int:
    return max(1, int(round(base_f0 * (2 ** (semitones / 12.0)))))


def _make_issue(
    severity: str,
    path: str,
    relation: str,
    reason: str,
    *,
    summary_hint: str | None = None,
) -> VerificationIssue:
    return VerificationIssue(
        severity=severity,
        path=path,
        relation=relation,
        reason=reason,
        summary_hint=summary_hint,
    )


def _interval_distance(value: float, minimum: float, maximum: float) -> float:
    if minimum <= value <= maximum:
        return 0.0
    return min(abs(value - minimum), abs(value - maximum))


def _nearest_multiple_gap(minimum: float, maximum: float, cvc_reference: float) -> float:
    upper = max(1, int(maximum // cvc_reference) + 2)
    return min(
        _interval_distance(n * cvc_reference, minimum, maximum)
        for n in range(1, upper + 1)
    )


def _iter_numeric_leaves(prefix: tuple[str, ...], node: Any) -> list[tuple[str, int]]:
    leaves: list[tuple[str, int]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            leaves.extend(_iter_numeric_leaves(prefix + (key,), value))
    elif isinstance(node, int) and not isinstance(node, bool):
        leaves.append(('.'.join(prefix), node))
    return leaves


def verify_phonetize_config(phonetize_config: dict[str, Any] | None = None) -> PhonetizeVerificationResult:
    raw_config = _merge_phonetize_config(phonetize_config)
    config = _runtime_view_phonetize_config(raw_config)
    verification_defaults = build_default_phonetize_verification_config()
    failures: list[VerificationIssue] = []
    warnings: list[VerificationIssue] = []

    def add_failure(path: str, relation: str, reason: str, *, summary_hint: str | None = None) -> None:
        failures.append(_make_issue('failure', path, relation, reason, summary_hint=summary_hint))

    def add_warning(path: str, relation: str, reason: str, *, summary_hint: str | None = None) -> None:
        warnings.append(_make_issue('warning', path, relation, reason, summary_hint=summary_hint))

    process = config['process']
    timing_model = config['timing_model']
    speech = timing_model['speech']
    durations = timing_model['durations']
    consonants = durations['consonants']
    vowels = durations['vowels']
    pauses = durations['pauses']
    verification_hint = (
        'Configured pause ranges no longer support coherent isochrony organized '
        'by the phonetize.process.timing_model.durations.cvc_reference foot.'
    )
    short_pause_hint = (
        'Configured short-pause settings no longer support clean equal-duration '
        'setup from the phonetize.process.timing_model.durations.cvc_reference foot.'
    )

    enum_policies = {
        'phonetize.process.timing_model.geminate_policy': ('cumulative', 'corrective'),
        'phonetize.process.timing_model.accentuation_distribution_policy': ('100_0', '85_15', '70_30'),
    }
    for path, choices in enum_policies.items():
        value = get_relative_value(raw_config, tuple(path.split('.')[1:]))
        if value not in choices:
            add_failure(
                path,
                f'value in {{{" | ".join(choices)}}}',
                f'Expected one of {choices!r}, got {value!r}.',
            )

    if not isinstance(process['drift_tolerance'], int) or isinstance(process['drift_tolerance'], bool) or process['drift_tolerance'] < 0:
        add_failure(
            'phonetize.process.timing_model.drift_tolerance',
            'drift_tolerance is an integer >= 0',
            'Drift tolerance must be a non-negative integer number of milliseconds.',
        )

    if not isinstance(speech['wpm'], int) or isinstance(speech['wpm'], bool) or speech['wpm'] <= 0:
        add_failure(
            'phonetize.process.timing_model.speech.wpm',
            'wpm > 0',
            'Speech-rate estimate must be a positive integer.',
        )

    pause_ratio = speech['pause_ratio']
    if not isinstance(pause_ratio, int) or isinstance(pause_ratio, bool) or not (0 < pause_ratio < 100):
        add_failure(
            'phonetize.process.timing_model.speech.pause_ratio',
            '0 < pause_ratio < 100',
            'pause_ratio must be a percentage strictly between 0 and 100.',
        )
    elif pause_ratio > 70:
        add_warning(
            'phonetize.process.timing_model.speech.pause_ratio',
            'pause_ratio > 70',
            'pause_ratio above 70 reserves an unusually large share of time for pauses.',
        )

    for path, value in _iter_numeric_leaves(('phonetize', 'process', 'timing_model', 'durations'), durations):
        if value <= 0:
            add_failure(
                path,
                'value is a positive integer in milliseconds',
                'Timing-model durations must be positive integers measured in milliseconds.',
            )

    intonation = raw_config['process']['intonation']
    if not isinstance(intonation['f0'], int) or isinstance(intonation['f0'], bool) or intonation['f0'] <= 0:
        add_failure(
            'phonetize.process.intonation.f0',
            'f0 > 0',
            'Baseline emitted F0 must be a positive integer Hertz value.',
        )
    for key in ('stress', 'question', 'statement', 'exclamation', 'continuation'):
        value = intonation[key]
        if not isinstance(value, str):
            add_failure(
                f'phonetize.process.intonation.{key}',
                f'{key} is a compact intonation preset token',
                'Intonation presets must be compact token strings such as H2, L2, M0, R1, F1, P2, or V2.',
            )
            continue
        try:
            _normalize_intonation_token(value)
        except ValueError as exc:
            add_failure(
                f'phonetize.process.intonation.{key}',
                f'{key} normalizes to one legal canonical row token',
                str(exc),
            )

    segmental_ceiling = durations['segmental_ceiling']
    segmental_floor = durations['segmental_floor']
    if vowels['perception_limits']['elongation_max'] > segmental_ceiling:
        add_failure(
            'phonetize.process.timing_model.durations.vowels.perception_limits.elongation_max, phonetize.process.timing_model.durations.segmental_ceiling',
            'phonetize.process.timing_model.durations.vowels.perception_limits.elongation_max <= phonetize.process.timing_model.durations.segmental_ceiling',
            'The vowel contextual max exceeds the configured segmental ceiling.',
        )

    for consonant_class in ('closure', 'fricative', 'sonorant'):
        base_path = f'phonetize.process.timing_model.durations.consonants.{consonant_class}'
        row = consonants[consonant_class]
        geminate_min = row['perception_limits']['geminate_min']
        gemination_max = row['perception_limits']['gemination_max']
        if not (row['onset'] < geminate_min <= row['geminate'] <= gemination_max <= segmental_ceiling):
            add_failure(
                f'{base_path}.onset, {base_path}.perception_limits.geminate_min, {base_path}.geminate, {base_path}.perception_limits.gemination_max, phonetize.process.timing_model.durations.segmental_ceiling',
                f'{base_path}.onset < {base_path}.perception_limits.geminate_min <= {base_path}.geminate <= {base_path}.perception_limits.gemination_max <= phonetize.process.timing_model.durations.segmental_ceiling',
                'Consonant timing ordering does not hold on the onset side.',
            )
        if not (row['coda'] < geminate_min <= row['geminate'] <= gemination_max <= segmental_ceiling):
            add_failure(
                f'{base_path}.coda, {base_path}.perception_limits.geminate_min, {base_path}.geminate, {base_path}.perception_limits.gemination_max, phonetize.process.timing_model.durations.segmental_ceiling',
                f'{base_path}.coda < {base_path}.perception_limits.geminate_min <= {base_path}.geminate <= {base_path}.perception_limits.gemination_max <= phonetize.process.timing_model.durations.segmental_ceiling',
                'Consonant timing ordering does not hold on the coda side.',
            )
        for min_path, min_value in (
            (f'{base_path}.onset', row['onset']),
            (f'{base_path}.coda', row['coda']),
            (f'{base_path}.perception_limits.geminate_min', geminate_min),
        ):
            if min_value < segmental_floor:
                add_failure(
                    f'{min_path}, phonetize.process.timing_model.durations.segmental_floor',
                    f'phonetize.process.timing_model.durations.segmental_floor <= {min_path}',
                    'The configured segmental floor is above a required consonant anchor or minimum.',
                )
        if abs(row['onset'] - row['coda']) / row['onset'] >= 0.5:
            add_warning(
                f'{base_path}.onset, {base_path}.coda',
                f'abs({base_path}.onset - {base_path}.coda) / {base_path}.onset >= 0.5',
                'Onset and coda anchors for this consonant class diverge sharply.',
            )

    if consonants['closure']['special_realization']['hiatus'] < segmental_floor:
        add_failure(
            'phonetize.process.timing_model.durations.consonants.closure.special_realization.hiatus, phonetize.process.timing_model.durations.segmental_floor',
            'phonetize.process.timing_model.durations.segmental_floor <= phonetize.process.timing_model.durations.consonants.closure.special_realization.hiatus',
            'Hiatus realization must stay at or above the configured segmental floor.',
        )
    if not (
        consonants['closure']['special_realization']['hiatus'] < consonants['closure']['onset']
        and consonants['closure']['special_realization']['hiatus'] < consonants['closure']['coda']
    ):
        add_failure(
            'phonetize.process.timing_model.durations.consonants.closure.special_realization.hiatus, phonetize.process.timing_model.durations.consonants.closure.onset, phonetize.process.timing_model.durations.consonants.closure.coda',
            'hiatus < onset and hiatus < coda',
            'Hiatus realization must stay below both closure onset and closure coda anchors.',
        )

    if consonants['sonorant']['special_realization']['vowel_transition'] < segmental_floor:
        add_failure(
            'phonetize.process.timing_model.durations.consonants.sonorant.special_realization.vowel_transition, phonetize.process.timing_model.durations.segmental_floor',
            'phonetize.process.timing_model.durations.segmental_floor <= phonetize.process.timing_model.durations.consonants.sonorant.special_realization.vowel_transition',
            'Vowel-transition realization must stay at or above the configured segmental floor.',
        )
    if not (
        consonants['sonorant']['special_realization']['vowel_transition'] < consonants['sonorant']['onset']
        and consonants['sonorant']['special_realization']['vowel_transition'] < consonants['sonorant']['coda']
    ):
        add_failure(
            'phonetize.process.timing_model.durations.consonants.sonorant.special_realization.vowel_transition, phonetize.process.timing_model.durations.consonants.sonorant.onset, phonetize.process.timing_model.durations.consonants.sonorant.coda',
            'vowel_transition < onset and vowel_transition < coda',
            'Vowel-transition realization must stay below both sonorant onset and sonorant coda anchors.',
        )

    vowel_limits = vowels['perception_limits']
    for vowel_min_key in ('short_min', 'long_min', 'very_long_min'):
        if vowel_limits[vowel_min_key] < segmental_floor:
            add_failure(
                f'phonetize.process.timing_model.durations.vowels.perception_limits.{vowel_min_key}, phonetize.process.timing_model.durations.segmental_floor',
                f'phonetize.process.timing_model.durations.segmental_floor <= phonetize.process.timing_model.durations.vowels.perception_limits.{vowel_min_key}',
                'A vowel perception minimum falls below the configured segmental floor.',
            )
    if not (
        vowel_limits['short_min'] < vowels['short'] < vowel_limits['long_min'] < vowels['long']
        < vowel_limits['very_long_min'] < vowels['very_long'] < vowel_limits['elongation_max']
    ):
        add_failure(
            'phonetize.process.timing_model.durations.vowels.perception_limits.short_min, phonetize.process.timing_model.durations.vowels.short, phonetize.process.timing_model.durations.vowels.perception_limits.long_min, phonetize.process.timing_model.durations.vowels.long, phonetize.process.timing_model.durations.vowels.perception_limits.very_long_min, phonetize.process.timing_model.durations.vowels.very_long, phonetize.process.timing_model.durations.vowels.perception_limits.elongation_max',
            'short_min < short < long_min < long < very_long_min < very_long < elongation_max',
            'Vowel category ordering is invalid.',
        )

    if not (
        pauses['mini']['min'] < pauses['mini']['max']
        and pauses['mini']['max'] < pauses['short']['min']
        and pauses['short']['min'] < pauses['short']['max']
        and pauses['short']['max'] < pauses['long']['min']
        and pauses['long']['min'] < pauses['long']['max']
    ):
        add_failure(
            'phonetize.process.timing_model.durations.pauses.mini.min, phonetize.process.timing_model.durations.pauses.mini.max, phonetize.process.timing_model.durations.pauses.short.min, phonetize.process.timing_model.durations.pauses.short.max, phonetize.process.timing_model.durations.pauses.long.min, phonetize.process.timing_model.durations.pauses.long.max',
            'mini.min < mini.max < short.min < short.max < long.min < long.max',
            'Pause-band ordering is invalid.',
        )

    cvc_reference = float(durations['cvc_reference'])
    short_min = float(pauses['short']['min'])
    short_max = float(pauses['short']['max'])
    long_min = float(pauses['long']['min'])
    long_max = float(pauses['long']['max'])

    if not _pause_multiple_candidates(short_min, short_max, cvc_reference):
        add_warning(
            'phonetize.process.timing_model.durations.pauses.short.min, phonetize.process.timing_model.durations.pauses.short.max, phonetize.process.timing_model.durations.cvc_reference',
            'exists N >= 1 with short.min <= N * cvc_reference <= short.max',
            'No integer multiple of cvc_reference falls inside the configured short-pause band.',
            summary_hint=short_pause_hint,
        )

    short_gap = _nearest_multiple_gap(short_min, short_max, cvc_reference)
    short_gap_limit = float(vowel_limits['long_min'] - vowel_limits['short_min'])
    if short_gap > short_gap_limit:
        add_failure(
            'phonetize.process.timing_model.durations.pauses.short.min, phonetize.process.timing_model.durations.pauses.short.max, phonetize.process.timing_model.durations.cvc_reference, phonetize.process.timing_model.durations.vowels.perception_limits.long_min, phonetize.process.timing_model.durations.vowels.perception_limits.short_min',
            'short_pause_gap <= long_min - short_min',
            'The nearest-multiple gap for the short-pause band exceeds the allowed vowel perception-gap threshold.',
            summary_hint=verification_hint,
        )

    if not _pause_multiple_candidates(long_min, long_max, cvc_reference):
        add_failure(
            'phonetize.process.timing_model.durations.pauses.long.min, phonetize.process.timing_model.durations.pauses.long.max, phonetize.process.timing_model.durations.cvc_reference',
            'exists N >= 1 with long.min <= N * cvc_reference <= long.max',
            'No integer multiple of cvc_reference falls inside the configured long-pause band.',
            summary_hint=verification_hint,
        )

    selected_default_paths = (
        ('process', 'timing_model', 'speech', 'wpm'),
        ('process', 'timing_model', 'durations', 'segmental_ceiling'),
        ('process', 'timing_model', 'durations', 'segmental_floor'),
        ('process', 'timing_model', 'durations', 'cvc_reference'),
        ('process', 'timing_model', 'durations', 'consonants', 'closure', 'perception_limits', 'geminate_min'),
        ('process', 'timing_model', 'durations', 'consonants', 'closure', 'perception_limits', 'gemination_max'),
        ('process', 'timing_model', 'durations', 'consonants', 'fricative', 'perception_limits', 'geminate_min'),
        ('process', 'timing_model', 'durations', 'consonants', 'fricative', 'perception_limits', 'gemination_max'),
        ('process', 'timing_model', 'durations', 'consonants', 'sonorant', 'perception_limits', 'geminate_min'),
        ('process', 'timing_model', 'durations', 'consonants', 'sonorant', 'perception_limits', 'gemination_max'),
        ('process', 'timing_model', 'durations', 'vowels', 'perception_limits', 'long_min'),
        ('process', 'timing_model', 'durations', 'vowels', 'perception_limits', 'very_long_min'),
        ('process', 'timing_model', 'durations', 'vowels', 'perception_limits', 'elongation_max'),
        ('process', 'timing_model', 'durations', 'pauses', 'mini', 'min'),
        ('process', 'timing_model', 'durations', 'pauses', 'short', 'min'),
        ('process', 'timing_model', 'durations', 'pauses', 'long', 'min'),
    )
    for relative_path in selected_default_paths:
        actual = get_relative_value(raw_config, relative_path)
        default = get_relative_value(verification_defaults, relative_path)
        if default and abs(actual - default) / default >= 0.5:
            path = 'phonetize.' + '.'.join(relative_path)
            add_warning(
                path,
                'abs(value - default) / default >= 0.5',
                f'Value deviates sharply from the canonical verification default {default}.',
            )

    return PhonetizeVerificationResult(tuple(failures), tuple(warnings))


def render_phonetize_verification_lines(result: PhonetizeVerificationResult) -> list[str]:
    lines = [f'VERIFY STATUS: {result.status}']
    if result.failures:
        lines.append(f'Blocking failures ({len(result.failures)}):')
        for issue in result.failures:
            lines.append(
                f'FAIL {issue.path} | relation: {issue.relation} | reason: {issue.reason}'
            )
    if result.warnings:
        lines.append(f'Warnings ({len(result.warnings)}):')
        for issue in result.warnings:
            lines.append(
                f'WARN {issue.path} | relation: {issue.relation} | reason: {issue.reason}'
            )
        hints = []
        for issue in result.warnings + result.failures:
            if issue.summary_hint and issue.summary_hint not in hints:
                hints.append(issue.summary_hint)
        if hints:
            lines.append('Warning summary hints:')
            for hint in hints:
                lines.append(f'Hint: {hint}')
    return lines


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


def _consonant_anchor(row: dict[str, str], config: dict[str, Any], position: str) -> float:
    durations = config['timing_model']['durations']
    timing_key = _consonant_timing_key(row)
    consonant_cfg = durations['consonants'][timing_key]
    if row['type'] == 'H':
        return float(durations['consonants']['closure']['special_realization']['hiatus'])
    if row['type'] == 'T':
        return float(durations['consonants']['sonorant']['special_realization']['vowel_transition'])
    if position == 'C':
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


def _vowel_anchor(row: dict[str, str], config: dict[str, Any]) -> float:
    vowels_cfg = config['timing_model']['durations']['vowels']
    return float(vowels_cfg['short'] if row['length'] == 'S' else vowels_cfg['long'])


def _vowel_bounds(
    row: dict[str, str],
    config: dict[str, Any],
    *,
    ordinary_recovery: bool = False,
) -> tuple[float, float]:
    vowels_cfg = config['timing_model']['durations']['vowels']
    limits = vowels_cfg['perception_limits']
    if row['length'] == 'S':
        anchor = float(vowels_cfg['short'])
        return anchor, anchor
    if ordinary_recovery:
        ordinary_maximum = min(float(limits['elongation_max']), float(limits['very_long_min']) - 1.0)
        ordinary_maximum = max(float(limits['long_min']), ordinary_maximum)
        return float(limits['long_min']), ordinary_maximum
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
    cvc_reference: float,
) -> float:
    threshold = float(_round_half_up(0.5 * cvc_reference))
    while drift_value > threshold:
        drift_value -= cvc_reference
    while drift_value < -threshold:
        drift_value += cvc_reference
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

    if not accentuated:
        return

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


def serialize_mbrola_rows(rows: list[dict[str, str]], phonetize_config: dict[str, Any] | None = None, *, accentuated: bool) -> str:
    return '\n'.join(
        ' '.join([symbol, str(duration)] + [str(target) for target in targets])
        for symbol, duration, targets in _mbrola_rows(rows, phonetize_config, accentuated=accentuated)
    ) + '\n'


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


def _shape_reference(analysis: dict[str, Any], config: dict[str, Any], *, accentuated: bool) -> float:
    one_mora_ref, two_mora_ref, three_mora_ref = _timing_refs(config)
    base_map = {
        'CV': one_mora_ref,
        'CVV': two_mora_ref,
        'CVC': two_mora_ref,
        'CVVC': three_mora_ref,
    }
    target = base_map[analysis['base_shape']]
    if accentuated and analysis['accent_shape'] is not None:
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


def _pause_multiple_candidates(minimum: float, maximum: float, cvc_reference: float) -> list[float]:
    upper = max(1, int(maximum // cvc_reference) + 2)
    return [n * cvc_reference for n in range(1, upper) if minimum <= n * cvc_reference <= maximum]


def _preferred_pause_target(row: dict[str, str], config: dict[str, Any]) -> float:
    pauses_cfg = config['timing_model']['durations']['pauses']
    cvc_reference = float(config['timing_model']['durations']['cvc_reference'])
    band = pauses_cfg['long'] if row['length'] == 'L' else pauses_cfg['short']
    minimum = float(band['min'])
    maximum = float(band['max'])
    candidates = _pause_multiple_candidates(minimum, maximum, cvc_reference)
    midpoint = (minimum + maximum) / 2.0
    if candidates:
        return min(candidates, key=lambda value: (abs(value - midpoint), value))
    nearest_multiple = max(cvc_reference, round(midpoint / cvc_reference) * cvc_reference)
    return min(max(nearest_multiple, minimum), maximum)


def _pause_duration_and_drift(row: dict[str, str], config: dict[str, Any], drift_cursor: float) -> tuple[float, float]:
    pauses_cfg = config['timing_model']['durations']['pauses']
    band = pauses_cfg['mini'] if _is_mini_pause_row(row) else (pauses_cfg['long'] if row['length'] == 'L' else pauses_cfg['short'])
    minimum = float(band['min'])
    maximum = float(band['max'])
    if _is_mini_pause_row(row):
        cvc_reference = float(config['timing_model']['durations']['cvc_reference'])
        actual = -drift_cursor if drift_cursor < 0 else (cvc_reference - drift_cursor)
        emitted = float(_rounded_duration_value(actual))
        return emitted, _normalize_drift_to_nearest_branch(drift_cursor + emitted, cvc_reference)
    preferred = _preferred_pause_target(row, config)
    desired = preferred - drift_cursor
    actual = min(max(desired, minimum), maximum)
    emitted = float(_rounded_duration_value(actual))
    new_drift = drift_cursor + (emitted - preferred)
    return emitted, new_drift


def _apply_vowel_correction(
    rows: list[dict[str, str]],
    analysis: dict[str, Any],
    durations: dict[int, float],
    drift_after_assignment: float,
    tolerance: float,
    config: dict[str, Any],
) -> float:
    vowel_index = analysis['nucleus_index']
    minimum, maximum = _vowel_bounds(rows[vowel_index], config, ordinary_recovery=True)
    current = durations[vowel_index]
    if drift_after_assignment > tolerance:
        reducible = min(current - minimum, drift_after_assignment - tolerance)
        if reducible > 0:
            durations[vowel_index] = current - reducible
            drift_after_assignment -= reducible
    elif drift_after_assignment < -tolerance:
        extendable = min(maximum - current, abs(drift_after_assignment) - tolerance)
        if extendable > 0:
            durations[vowel_index] = current + extendable
            drift_after_assignment += extendable
    return drift_after_assignment


def _apply_accent_increment(
    rows: list[dict[str, str]],
    analysis: dict[str, Any],
    durations: dict[int, float],
    config: dict[str, Any],
    drift_portion: float,
    next_same_onset: int | None,
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
    share_map = {
        '100_0': (1.0, 0.0),
        '85_15': (0.85, 0.15),
        '70_30': (0.70, 0.30),
    }
    primary_share, adjacent_share = share_map[policy]
    total_increment = max(0.0, float(_round_half_up(one_mora_ref)) - drift_portion)

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
    primary_gain = min(total_increment * primary_share, primary_slack)
    durations[primary_index] += primary_gain
    remaining = total_increment - primary_gain

    if adjacent_index is not None:
        adjacent_slack = max(0.0, _segment_limit(adjacent_index, adjacent=True) - durations[adjacent_index])
        adjacent_gain = min(total_increment * adjacent_share, adjacent_slack, remaining)
        durations[adjacent_index] += adjacent_gain
        remaining -= adjacent_gain
        if remaining > 0 and primary_slack > primary_gain:
            extra_primary = min(remaining, primary_slack - primary_gain)
            durations[primary_index] += extra_primary
            remaining -= extra_primary
        if remaining > 0 and adjacent_slack > adjacent_gain:
            extra_adjacent = min(remaining, adjacent_slack - adjacent_gain)
            durations[adjacent_index] += extra_adjacent
            remaining -= extra_adjacent
    elif remaining > 0 and primary_slack > primary_gain:
        extra_primary = min(remaining, primary_slack - primary_gain)
        durations[primary_index] += extra_primary

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


def _maybe_insert_mini_pause(
    rows: list[dict[str, str]],
    units: list[dict[str, Any]],
    unit_index: int,
    analysis: dict[str, Any],
    config: dict[str, Any],
    drift_cursor: float,
) -> tuple[dict[str, str], float, float] | None:
    if unit_index + 1 >= len(units) or units[unit_index + 1]['kind'] != 'syllable':
        return None
    if rows[analysis['indices'][-1]]['boundary'] != 'F':
        return None

    mini_cfg = config['timing_model']['durations']['pauses']['mini']
    mini_min = float(mini_cfg['min'])
    mini_max = float(mini_cfg['max'])
    cvc_reference = float(config['timing_model']['durations']['cvc_reference'])

    if drift_cursor < 0:
        target_duration = abs(drift_cursor)
    elif drift_cursor > 0:
        target_duration = abs(drift_cursor - cvc_reference)
    else:
        return None

    if target_duration < mini_min or target_duration > mini_max:
        return None

    mini_row = _new_mini_pause_row()
    pause_duration, new_drift = _pause_duration_and_drift(mini_row, config, drift_cursor)
    if abs(new_drift) >= abs(drift_cursor) and abs(new_drift) >= 0.5:
        return None
    return mini_row, pause_duration, new_drift


def realize_phone_rows(
    rows: list[dict[str, str]],
    phonetize_config: dict[str, Any] | None = None,
    *,
    allow_accentuation: bool,
) -> dict[str, Any]:
    config = _runtime_view_phonetize_config(_merge_phonetize_config(phonetize_config))
    units = _partition_phone_units(rows)
    durations: dict[int, float] = {}
    drift_cursor = 0.0
    drift_history: list[float] = []
    drift_extension_count = 0
    max_drift_extension = 0.0
    tolerance = float(config['process']['drift_tolerance'])
    inserted_after: dict[int, list[tuple[dict[str, str], float, str]]] = {}
    row_drift_tokens: dict[int, str] = {}
    last_completed_drift_token = PHONE_ROW_DRIFT_NEUTRAL

    analyses: dict[int, dict[str, Any]] = {}
    for unit_index, unit in enumerate(units):
        if unit['kind'] == 'syllable':
            analyses[unit_index] = _analyze_syllable(rows, unit['indices'])

    for unit_index, unit in enumerate(units):
        if unit['kind'] == 'pause':
            entry_drift = drift_cursor
            pause_duration, drift_cursor = _pause_duration_and_drift(rows[unit['index']], config, drift_cursor)
            durations[unit['index']] = pause_duration
            drift_cursor = entry_drift + (float(_rounded_duration_value(pause_duration)) - (_preferred_pause_target(rows[unit['index']], config) if not _is_mini_pause_row(rows[unit['index']]) else 0.0))
            drift_history.append(drift_cursor)
            last_completed_drift_token = _format_row_drift_token(drift_cursor)
            row_drift_tokens[unit['index']] = last_completed_drift_token
            continue

        entry_drift = drift_cursor
        analysis = analyses[unit_index]
        next_analysis = None
        if unit_index + 1 < len(units) and units[unit_index + 1]['kind'] == 'syllable':
            next_analysis = analyses[unit_index + 1]

        for row_index in analysis['indices']:
            row_drift_tokens[row_index] = last_completed_drift_token

        for onset_index in analysis['onset_indices']:
            durations.setdefault(onset_index, _consonant_anchor(rows[onset_index], config, 'O'))
        for coda_index in analysis['coda_indices']:
            durations[coda_index] = _consonant_anchor(rows[coda_index], config, 'C')
        nucleus_index = analysis['nucleus_index']
        durations[nucleus_index] = _vowel_anchor(rows[nucleus_index], config)

        next_same_onset = _same_consonant_next_onset(rows, analysis, next_analysis, durations, config)

        shape_ref = _shape_reference(analysis, config, accentuated=False)
        realized_total = sum(durations[index] for index in analysis['indices'])
        drift_after_assignment = drift_cursor + (realized_total - shape_ref)
        cvc_reference = float(config['timing_model']['durations']['cvc_reference'])

        nucleus_row = rows[analysis['nucleus_index']]
        if abs(drift_after_assignment) > tolerance and nucleus_row['length'] == 'L':
            drift_after_assignment = _apply_vowel_correction(
                rows,
                analysis,
                durations,
                drift_after_assignment,
                tolerance,
                config,
            )

        drift_portion = drift_after_assignment
        accent_target = 0.0
        if allow_accentuation and analysis['accent_shape'] is not None:
            accent_increment_applied = _apply_accent_increment(
                rows,
                analysis,
                durations,
                config,
                drift_portion,
                next_same_onset,
            )
            accent_target = float(_round_half_up(0.5 * cvc_reference))
            drift_after_assignment = drift_portion + (accent_increment_applied - accent_target)

        emitted_total = sum(float(_rounded_duration_value(durations[index])) for index in analysis['indices'])
        drift_after_assignment = entry_drift + (emitted_total - shape_ref - accent_target)
        if _should_fold_completed_syllable(rows, analysis):
            drift_after_assignment = _normalize_drift_to_nearest_branch(drift_after_assignment, cvc_reference)

        if abs(drift_after_assignment) > tolerance:
            extension = abs(drift_after_assignment) - tolerance
            if extension > 0:
                drift_extension_count += 1
                max_drift_extension = max(max_drift_extension, extension)
        drift_cursor = drift_after_assignment
        drift_history.append(drift_cursor)
        last_completed_drift_token = _format_row_drift_token(drift_cursor)
        row_drift_tokens[analysis['indices'][-1]] = last_completed_drift_token

        mini_pause = _maybe_insert_mini_pause(rows, units, unit_index, analysis, config, drift_cursor)
        if mini_pause is not None:
            mini_row, mini_duration, drift_cursor = mini_pause
            last_completed_drift_token = _format_row_drift_token(drift_cursor)
            inserted_after.setdefault(analysis['indices'][-1], []).append((mini_row, mini_duration, last_completed_drift_token))
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
        int(config['timing_model']['durations']['cvc_reference']),
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
    return {
        'one_mora_ref': one_mora_ref,
        'two_mora_ref': two_mora_ref,
        'three_mora_ref': three_mora_ref,
        'drift': {
            'max': round(max_abs, 4),
            'mean': round(mean, 4),
            'stddev': round(stddev, 4),
            'current': round(drift_cursor, 4),
            'label': _drift_label(drift_cursor),
        },
        'drift_extension_count': drift_extension_count,
        'max_drift_extension': round(max_drift_extension, 4),
    }


def build_phone_rows(
    tilde_text: str,
    phonetize_config: dict[str, Any] | None = None,
    input_frontmatter: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    _ = phonetize_config
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
            rows.append(_new_pause_row(EOL_TEXT, pause_type='S', length_code='L'))
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
    return rows


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
            if row['text'] == EOL_TEXT:
                pieces.append('\n')
                previous_boundary = ''
            elif not _is_mini_pause_row(row):
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


def run_tests() -> bool:
    cases = [
        lambda: CONSONANT_HIATUS == set('˙') and CONSONANT_VOWEL_TRANSITION == set('¨'),
        lambda: INPUT_CHARACTER_LABELS['ṣ'] == 'SUD' and INPUT_CHARACTER_LENGTHS['û'] == 'L',
        lambda: REALIZATION_CODE_METADATA['SP']['category'] == 'S' and INPUT_TO_REALIZATION_CODES['ENA'] == ('WA', 'YI'),
        lambda: REALIZATION_CODE_METADATA[MINI_PAUSE_REALIZATION]['ipa'] == '.' and INPUT_TO_REALIZATION_CODES[MINI_PAUSE_LABEL] == (MINI_PAUSE_REALIZATION,),
        lambda: derive_original_tilde_text('u+ana&šar~.ri') == 'u+ana šar.ri',
        lambda: _test_emphatic_vowel_and_row_format(),
        lambda: _test_mini_pause_row_contract(),
        lambda: _test_boundary_reconstruction(),
        lambda: _test_transition_resolution(),
        lambda: _test_dual_stream_generation(),
        lambda: _test_finalized_stream_generation(),
        lambda: _test_intonation_normalization_and_assignment(),
        lambda: _test_shared_verification(),
        lambda: _test_mbrola_export(),
    ]
    return all(case() for case in cases)


def _test_emphatic_vowel_and_row_format() -> bool:
    rows = build_phone_rows('qā')
    if rows[0]['realization'] != 'QU' or rows[1]['realization'] != 'AO':
        return False
    line = serialize_phone_row(rows[0])
    return parse_phone_row(line) == rows[0] and rows[0]['duration'] == PHONE_ROW_DURATION_PLACEHOLDER


def _test_mini_pause_row_contract() -> bool:
    row = _new_mini_pause_row()
    return (
        row['label'] == MINI_PAUSE_LABEL
        and row['type'] == MINI_PAUSE_TYPE
        and row['realization'] == MINI_PAUSE_REALIZATION
        and parse_phone_row(serialize_phone_row(row))['text'] == MINI_PAUSE_TEXT
    )


def _test_boundary_reconstruction() -> bool:
    sample = 'šit·ku·nat-ma'
    rows = build_phone_rows(sample)
    return reconstruct_tilde_from_phone_rows(rows) == sample + '\n'


def _test_transition_resolution() -> bool:
    rows = build_phone_rows('a¨u')
    transition = next(row for row in rows if row['label'] == 'ENA')
    return transition['realization'] == 'WA'


def _test_dual_stream_generation() -> bool:
    original_rows, accentuated_rows = build_phone_streams('u+ana&šar~·ri')
    return (
        reconstruct_tilde_from_phone_rows(original_rows) == 'u+ana šar·ri\n'
        and reconstruct_tilde_from_phone_rows(accentuated_rows) == 'u+ana&šar~·ri\n'
    )


def _test_finalized_stream_generation() -> bool:
    config = {
        'process': {
            'timing_model': {
                'drift_tolerance': 0,
            },
        }
    }
    (_original_rows, original_report), (_accentuated_rows, accentuated_report) = realize_phone_streams(
        'b~a, bāt~\n',
        config,
    )
    return (
        any(row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in _original_rows)
        and any(row['duration'] != PHONE_ROW_DURATION_PLACEHOLDER for row in _accentuated_rows)
        and all(row['intonation'] for row in _original_rows)
        and all(row['intonation'] for row in _accentuated_rows)
        and 'stddev' in original_report['drift']
        and 'stddev' in accentuated_report['drift']
    )


def _test_intonation_normalization_and_assignment() -> bool:
    rows = build_phone_rows('at·ta~?!')
    realize_phone_rows(rows, allow_accentuation=True)
    realize_row_intonation(rows, accentuated=True)
    return (
        _normalize_intonation_token('H2') == 'H2C'
        and _normalize_intonation_token('R1') == 'R1L'
        and rows[-2]['type'] == 'Q'
        and rows[-2]['intonation'] == 'H3C'
        and rows[-1]['type'] == 'S'
        and all(row['intonation'] == 'M0C' for row in rows[:2])
        and all(row['intonation'] == 'H3C' for row in rows[2:-1])
    )


def _test_shared_verification() -> bool:
    warnings_only = verify_phonetize_config({'process': {'timing_model': {'speech': {'pause_ratio': 71}}}})
    blocking = verify_phonetize_config({'process': {'timing_model': {'speech': {'pause_ratio': 100}}}})
    rendered = render_phonetize_verification_lines(warnings_only)
    return (
        warnings_only.status == 'pass-with-warnings'
        and blocking.status == 'failure'
        and any('pause_ratio > 70' in line for line in rendered)
    )


def _test_mbrola_export() -> bool:
    original_rows, accentuated_rows = build_phone_streams('at~·ta')
    realize_phone_rows(original_rows, allow_accentuation=False)
    realize_phone_rows(accentuated_rows, allow_accentuation=True)
    realize_row_intonation(original_rows, accentuated=False)
    realize_row_intonation(accentuated_rows, accentuated=True)
    original_lines = serialize_mbrola_rows(original_rows, accentuated=False).strip().splitlines()
    accentuated_lines = serialize_mbrola_rows(accentuated_rows, accentuated=True).strip().splitlines()
    return (
        len(original_lines) > 0
        and len(accentuated_lines) > 0
        and all(len(line.split()) >= 3 for line in original_lines + accentuated_lines)
        and any(line.endswith(' 135') for line in accentuated_lines)
    )