from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from typing import Any

from akkapros.lib.constants import (
    AKKADIAN_CONSONANTS,
    AKKADIAN_VOWELS,
    HIATUS_MARKER,
    LONG_PAUSE_PUNCTUATION_CHARS,
    SHORT_PAUSE_PUNCTUATION_CHARS,
    SYL_SEPARATOR,
    WORD_LINKER,
)


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
            'short pause discharge policy\n- strict: the pause must realize a preferred legal short-band target derived from the nearest integer multiple of cvc_reference, and it must discharge drift reserve through that target as far as the band allows\n- best_effort: the pause may choose any legal short-band realization that maximizes drift discharge, and any remainder carries into the following phrase',
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
                'Central heavy-syllable timing reference used by accentuation and pause alignment. Set inside the empirically grounded CVC interval 286-306 ms.',
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
                    '__comment__': 'Default short-pause band. Empirically grounded short-pause region from comparative studies.',
                    'min': _field(600, 'int', 'Minimum short-pause duration.'),
                    'max': _field(680, 'int', 'Maximum short-pause duration.'),
                },
                'long': {
                    '__comment__': 'Default long-pause band. Clause-boundary range from comparative pause data.',
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

SHORT_VOWELS = set('aeiu')
LONG_VOWELS = set('āēīūâêîû')
VERY_LONG_VOWELS = set('àèìù')
CLOSURE_CONSONANTS = set('bdgkptṭqʾ')
FRICATIVE_CONSONANTS = set('szšṣḥḫʿ')
SONORANT_CONSONANTS = set('lrmnwy')
SPECIAL_CLOSURE = {HIATUS_MARKER}
SPECIAL_SONORANT = {'¨'}


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


def _next_symbol_type(text: str, index: int) -> str | None:
    stop_chars = {' ', '\t', '\r', '\n', SYL_SEPARATOR, '.', '-', '_', '&', WORD_LINKER}
    for cursor in range(index + 1, len(text)):
        char = text[cursor]
        if char == '~':
            continue
        if char in stop_chars:
            return None
        if char in AKKADIAN_VOWELS or char in VERY_LONG_VOWELS:
            return 'vowel'
        if char in AKKADIAN_CONSONANTS or char in SPECIAL_CLOSURE or char in SPECIAL_SONORANT:
            return 'consonant'
        if char in SHORT_PAUSE_PUNCTUATION_CHARS or char in LONG_PAUSE_PUNCTUATION_CHARS:
            return None
    return None


def _classify_consonant(symbol: str) -> tuple[str, int]:
    if symbol in SPECIAL_CLOSURE:
        return 'closure', 18
    if symbol in SPECIAL_SONORANT:
        return 'sonorant', 11
    if symbol in CLOSURE_CONSONANTS:
        return 'closure', 0
    if symbol in FRICATIVE_CONSONANTS:
        return 'fricative', 0
    return 'sonorant', 0


def build_phone_rows(tilde_text: str, phonetize_config: dict[str, Any]) -> list[dict[str, Any]]:
    timing = phonetize_config['timing_model']['durations']
    rows: list[dict[str, Any]] = []
    line_index = 1
    word_index = 1
    syllable_index = 1

    def _mark_boundary(code: str) -> None:
        if rows and rows[-1]['kind'] == 'phoneme':
            rows[-1]['boundary_after'] = code

    for index, symbol in enumerate(tilde_text):
        if symbol == '~':
            if rows and rows[-1]['kind'] == 'phoneme':
                rows[-1]['accentuated'] = True
            continue

        if symbol == '\n':
            rows.append(
                {
                    'kind': 'silence',
                    'symbol': 'LONG_PAUSE',
                    'duration_ms': timing['pauses']['long']['min'],
                    'line_index': line_index,
                    'word_index': word_index,
                    'syllable_index': syllable_index,
                    'accentuated': False,
                    'boundary_after': 'pause',
                    'segment_class': 'pause',
                    'source_marker': '\\n',
                }
            )
            line_index += 1
            word_index = 1
            syllable_index = 1
            continue

        if symbol in SHORT_PAUSE_PUNCTUATION_CHARS:
            rows.append(
                {
                    'kind': 'silence',
                    'symbol': 'SHORT_PAUSE',
                    'duration_ms': timing['pauses']['short']['min'],
                    'line_index': line_index,
                    'word_index': word_index,
                    'syllable_index': syllable_index,
                    'accentuated': False,
                    'boundary_after': 'pause',
                    'segment_class': 'pause',
                    'source_marker': symbol,
                }
            )
            continue

        if symbol in LONG_PAUSE_PUNCTUATION_CHARS:
            rows.append(
                {
                    'kind': 'silence',
                    'symbol': 'LONG_PAUSE',
                    'duration_ms': timing['pauses']['long']['min'],
                    'line_index': line_index,
                    'word_index': word_index,
                    'syllable_index': syllable_index,
                    'accentuated': False,
                    'boundary_after': 'pause',
                    'segment_class': 'pause',
                    'source_marker': symbol,
                }
            )
            continue

        if symbol == ' ':
            _mark_boundary('word')
            word_index += 1
            syllable_index = 1
            continue

        if symbol in {'_', '&'}:
            _mark_boundary('merge-internal')
            continue

        if symbol == WORD_LINKER:
            _mark_boundary('merge-explicit')
            continue

        if symbol in {SYL_SEPARATOR, '.'}:
            _mark_boundary('syllable')
            syllable_index += 1
            continue

        if symbol == '-':
            _mark_boundary('enclitic')
            syllable_index += 1
            continue

        if symbol in SHORT_VOWELS:
            duration_ms = timing['vowels']['short']
            segment_class = 'vowel'
        elif symbol in LONG_VOWELS:
            duration_ms = timing['vowels']['long']
            segment_class = 'vowel'
        elif symbol in VERY_LONG_VOWELS:
            duration_ms = timing['vowels']['very_long']
            segment_class = 'vowel'
        elif symbol in AKKADIAN_CONSONANTS or symbol in SPECIAL_CLOSURE or symbol in SPECIAL_SONORANT:
            consonant_class, special_duration = _classify_consonant(symbol)
            segment_class = consonant_class
            if special_duration:
                duration_ms = special_duration
            else:
                duration_kind = 'onset' if _next_symbol_type(tilde_text, index) == 'vowel' else 'coda'
                duration_ms = timing['consonants'][consonant_class][duration_kind]
        else:
            continue

        rows.append(
            {
                'kind': 'phoneme',
                'symbol': symbol,
                'duration_ms': duration_ms,
                'line_index': line_index,
                'word_index': word_index,
                'syllable_index': syllable_index,
                'accentuated': False,
                'boundary_after': '',
                'segment_class': segment_class,
                'source_marker': symbol,
            }
        )

    return rows


def serialize_phone_rows(rows: list[dict[str, Any]]) -> str:
    return '\n'.join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + '\n'