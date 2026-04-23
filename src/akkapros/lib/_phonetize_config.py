from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
import re
from typing import Any


PHONETIZE_SECTION = 'phonetize'
PHONETIZE_SECTION_HELP = 'Options used by the phonetizer CLI and by fullprosmaker during the phonetize stage.'
REMOVED_TIMING_MODEL_KEYS = {
    'short_pause_policy': 'CR-061',
    'drift_policy': 'CR-061',
    'speech': 'CR-081',
}
ACCENTUATION_DISTRIBUTION_SHARES = {
    '100_0': (1.0, 0.0),
    '95_05': (0.95, 0.05),
    '90_10': (0.90, 0.10),
    '85_15': (0.85, 0.15),
    '80_20': (0.80, 0.20),
    '75_25': (0.75, 0.25),
    '70_30': (0.70, 0.30),
}
ACCENTUATION_DISTRIBUTION_CHOICES = tuple(ACCENTUATION_DISTRIBUTION_SHARES)
SYNC_PRECISION_DIGITS = 1


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
        'realization': {
            '__comment__': None,
            'limit_emphatic_coloring': _field(
                False,
                'bool',
                'When true, limit emphatic vowel coloring to the legacy onset‑only rule (non‑experimental). When false, enable same‑syllable emphatic‑coda coloring and immediate next‑syllable carry (experimental).',
            ),
        },
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
                '80_20',
                'string',
                'this policy indicates how the accentuation mora (0.5 * cvc_reference) is distributed, format N_M\nN = percentage on the accentuated segment; M = percentage on the adjacent segment\nWhen legality caps block the full target, the solver preserves the configured ratio, realizes the largest legal proportional increment, and carries the remaining shortfall into drift.\nAllowed values: 100_0, 95_05, 90_10, 85_15, 80_20, 75_25, 70_30',
                choices=ACCENTUATION_DISTRIBUTION_CHOICES,
            ),
            'drift_tolerance': _field(
                19,
                'int',
                'maximum local timing mismatch tolerated before the algorithm must fail',
            ),
            'enable_resync_pause': _field(
                False,
                'bool',
                'Enable algorithmic resynchronization-pause insertion at eligible non-punctuation boundaries.',
            ),
            'durations': {
                '__comment__': None,
                'scale': _field(
                    1.0,
                    'float',
                    'Global multiplier applied to all other numeric duration leaves when different from 1.0. Runtime treats 1.0 as a true no-op path and uses configured values directly.',
                ),
                'segmental_ceiling': _field(
                    310,
                    'int',
                    'Global validation ceiling for class-local consonant gemination maxima and the vowel elongation max. This key remains part of the config and verification surface, but runtime consonant saturation uses class-local gemination_max values instead.',
                ),
                'segmental_floor': _field(
                    20,
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
                        'coda_final': _field(87, 'int', 'Default pre-pausal final closure duration. Used only when the next realized unit is a punctuation-owned short or long pause.'),
                        'geminate': _field(175, 'int', 'Default geminate closure target. Summary point for the attested stop-geminate band.'),
                        'geminate_coda_ratio': _field(0.60, 'float', 'Corrective same-consonant coda share used when geminate_policy is corrective. The onset side receives the exact remainder of the selected pair total.'),
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
                        'coda_final': _field(112, 'int', 'Default pre-pausal final fricative duration. Used only when the next realized unit is a punctuation-owned short or long pause.'),
                        'geminate': _field(210, 'int', 'Default geminate fricative target. Retuned summary point for the live fricative geminate-like row.'),
                        'geminate_coda_ratio': _field(0.60, 'float', 'Corrective same-consonant coda share used when geminate_policy is corrective. The onset side receives the exact remainder of the selected pair total.'),
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
                        'coda_final': _field(100, 'int', 'Default pre-pausal final sonorant duration. Used only when the next realized unit is a punctuation-owned short or long pause.'),
                        'geminate': _field(190, 'int', 'Default geminate sonorant target. Set from the direct glide geminate region.'),
                        'geminate_coda_ratio': _field(0.60, 'float', 'Corrective same-consonant coda share used when geminate_policy is corrective. The onset side receives the exact remainder of the selected pair total.'),
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
                    'short_final': _field(110, 'int', 'Default pre-pausal final short-vowel duration. Used only when the next realized unit is a punctuation-owned short or long pause.'),
                    'long': _field(160, 'int', 'Default long-vowel duration. Production anchor from the retained long-vowel baseline.'),
                    'long_final': _field(160, 'int', 'Default pre-pausal final long-vowel duration. Used only when the next realized unit is a punctuation-owned short or long pause. Ordinary downward recovery in that context must not go below this anchor.'),
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
                    'resync': {
                        '__comment__': 'Default resync-pause band. Non-punctuation recovery gap used only when the stream is ahead of the beat and no punctuation-owned pause already follows the current merged unit boundary.',
                        'min': _field(100, 'int', 'Minimum resync-pause duration.'),
                        'max': _field(200, 'int', 'Maximum resync-pause duration.'),
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
    'enable_resync_pause',
)

INTONATION_FAMILY_SHAPES = {
    'H': 'C',
    'L': 'C',
    'M': 'C',
    'R': 'L',
    'F': 'L',
    'P': 'E',
    'V': 'E',
}
INTONATION_PRESET_RE = re.compile(r'^[HLMRFPV][0-9](?:[CLE])?$')


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
                    cr_ids = {REMOVED_TIMING_MODEL_KEYS[key] for key in removed}
                    joined = ', '.join('.'.join(prefix + (key,)) for key in removed)
                    if len(cr_ids) == 1:
                        cr_id = next(iter(cr_ids))
                        raise ValueError(
                            f'Removed config keys ({cr_id}): {joined}. '
                            'These options were removed and are no longer part of the active config contract.'
                        )
                    grouped = '; '.join(
                        f"{cr_id}: {', '.join('.'.join(prefix + (key,)) for key in removed if REMOVED_TIMING_MODEL_KEYS[key] == cr_id)}"
                        for cr_id in sorted(cr_ids)
                    )
                    raise ValueError(
                        'Removed config keys: '
                        f'{grouped}. These options were removed and are no longer part of the active config contract.'
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


def _runtime_intonation_config(intonation_config: dict[str, Any]) -> dict[str, Any]:
    normalized = {'f0': intonation_config['f0']}
    for key in ('stress', 'question', 'statement', 'exclamation', 'continuation'):
        normalized[key] = _normalize_intonation_token(str(intonation_config[key]))
    return normalized


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
    effective_durations, duration_scale = _derive_effective_durations(timing_model['durations'])
    timing_model['durations'] = effective_durations
    process = {key: deepcopy(timing_model[key]) for key in PROCESS_KEYS}
    process['realization'] = deepcopy(phonetize_config['process'].get('realization', {}))
    model_only = {key: deepcopy(value) for key, value in timing_model.items() if key not in PROCESS_KEYS}
    model_only['duration_scale'] = duration_scale
    return {
        'process': process,
        'intonation': _runtime_intonation_config(deepcopy(phonetize_config['process'].get('intonation', {}))),
        'timing_model': model_only,
    }


def _scale_duration_values(node: Any, scale: float, *, path: tuple[str, ...] = ()) -> Any:
    if isinstance(node, dict):
        scaled: dict[str, Any] = {}
        for key, value in node.items():
            if path == () and key == 'scale':
                scaled[key] = value
            else:
                scaled[key] = _scale_duration_values(value, scale, path=path + (key,))
        return scaled
    if isinstance(node, (int, float)) and not isinstance(node, bool):
        return float(node) * scale
    return deepcopy(node)


def _derive_effective_durations(durations: dict[str, Any]) -> tuple[dict[str, Any], float]:
    raw_scale = durations.get('scale', 1.0)
    if not isinstance(raw_scale, (int, float)) or isinstance(raw_scale, bool):
        raise ValueError('phonetize.process.timing_model.durations.scale must be a positive number.')
    scale = float(raw_scale)
    if scale <= 0:
        raise ValueError('phonetize.process.timing_model.durations.scale must be > 0.')
    if scale == 1.0:
        return deepcopy(durations), scale
    return _scale_duration_values(deepcopy(durations), scale), scale


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


def _round_sync_precision(value: float) -> float:
    return round(float(value), SYNC_PRECISION_DIGITS)


def _resolve_mora_mode(input_frontmatter: dict[str, Any] | None) -> str:
    if not isinstance(input_frontmatter, dict):
        return 'bi'
    metadata = input_frontmatter.get('metadata')
    if not isinstance(metadata, dict):
        return 'bi'
    options = metadata.get('options')
    if not isinstance(options, dict):
        return 'bi'
    return 'mono' if options.get('mora_mode') == 'mono' else 'bi'


def _resolve_synchronization_basis(
    config: dict[str, Any],
    *,
    allow_accentuation: bool,
    input_frontmatter: dict[str, Any] | None = None,
) -> float:
    cvc_reference = float(config['timing_model']['durations']['cvc_reference'])
    if not allow_accentuation:
        return _round_sync_precision(cvc_reference / 2.0)
    if _resolve_mora_mode(input_frontmatter) == 'mono':
        return _round_sync_precision(cvc_reference / 2.0)
    return _round_sync_precision(cvc_reference)


def _supported_synchronization_bases(cvc_reference: float) -> tuple[float, ...]:
    half = _round_sync_precision(cvc_reference / 2.0)
    full = _round_sync_precision(cvc_reference)
    if half == full:
        return (full,)
    return (half, full)


def _iter_numeric_leaves(prefix: tuple[str, ...], node: Any) -> list[tuple[str, float]]:
    leaves: list[tuple[str, float]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            leaves.extend(_iter_numeric_leaves(prefix + (key,), value))
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        leaves.append(('.'.join(prefix), float(node)))
    return leaves


def verify_phonetize_config(phonetize_config: dict[str, Any] | None = None) -> PhonetizeVerificationResult:
    from akkapros.lib.phonetize import _pause_multiple_candidates

    raw_config = _merge_phonetize_config(phonetize_config)
    try:
        config = _runtime_view_phonetize_config(raw_config)
    except ValueError as exc:
        return PhonetizeVerificationResult(
            (
                _make_issue(
                    'failure',
                    'phonetize.process.timing_model.durations.scale',
                    'scale is a positive numeric value',
                    str(exc),
                ),
            ),
            (),
        )
    verification_defaults = build_default_phonetize_verification_config()
    failures: list[VerificationIssue] = []
    warnings: list[VerificationIssue] = []

    def add_failure(path: str, relation: str, reason: str, *, summary_hint: str | None = None) -> None:
        failures.append(_make_issue('failure', path, relation, reason, summary_hint=summary_hint))

    def add_warning(path: str, relation: str, reason: str, *, summary_hint: str | None = None) -> None:
        warnings.append(_make_issue('warning', path, relation, reason, summary_hint=summary_hint))

    process = config['process']
    timing_model = config['timing_model']
    durations = timing_model['durations']
    duration_scale = float(timing_model.get('duration_scale', 1.0))
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
        'phonetize.process.timing_model.accentuation_distribution_policy': ACCENTUATION_DISTRIBUTION_CHOICES,
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

    if not isinstance(raw_config['process']['timing_model']['durations'].get('scale', 1.0), (int, float)) or isinstance(raw_config['process']['timing_model']['durations'].get('scale', 1.0), bool) or float(raw_config['process']['timing_model']['durations'].get('scale', 1.0)) <= 0:
        add_failure(
            'phonetize.process.timing_model.durations.scale',
            'scale is a positive numeric value',
            'Timing-model duration scale must be a positive number.',
        )

    for path, value in _iter_numeric_leaves(('phonetize', 'process', 'timing_model', 'durations'), durations):
        if value <= 0:
            add_failure(
                path,
                'value is a positive numeric duration',
                'Timing-model durations must be positive numeric values.',
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
        geminate_coda_ratio = row['geminate_coda_ratio']
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
        if not (row['coda'] <= row['coda_final'] < geminate_min):
            add_failure(
                f'{base_path}.coda, {base_path}.coda_final, {base_path}.perception_limits.geminate_min',
                f'{base_path}.coda <= {base_path}.coda_final < {base_path}.perception_limits.geminate_min',
                'Final-position coda timing must stay category-preserving and below the geminate threshold.',
            )
        for min_path, min_value in (
            (f'{base_path}.onset', row['onset']),
            (f'{base_path}.coda', row['coda']),
            (f'{base_path}.coda_final', row['coda_final']),
            (f'{base_path}.perception_limits.geminate_min', geminate_min),
        ):
            if min_value < segmental_floor:
                add_failure(
                    f'{min_path}, phonetize.process.timing_model.durations.segmental_floor',
                    f'phonetize.process.timing_model.durations.segmental_floor <= {min_path}',
                    'The configured segmental floor is above a required consonant anchor or minimum.',
                )
        if not isinstance(geminate_coda_ratio, (int, float)) or isinstance(geminate_coda_ratio, bool) or not (0 < geminate_coda_ratio < 1):
            add_failure(
                f'{base_path}.geminate_coda_ratio',
                f'0 < {base_path}.geminate_coda_ratio < 1',
                'Corrective geminate coda share must be numeric and strictly between 0 and 1.',
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
        vowel_limits['short_min'] < vowels['short'] <= vowels['short_final'] < vowel_limits['long_min']
        <= vowels['long'] <= vowels['long_final'] < vowel_limits['very_long_min']
        < vowels['very_long'] < vowel_limits['elongation_max']
    ):
        add_failure(
            'phonetize.process.timing_model.durations.vowels.perception_limits.short_min, phonetize.process.timing_model.durations.vowels.short, phonetize.process.timing_model.durations.vowels.short_final, phonetize.process.timing_model.durations.vowels.perception_limits.long_min, phonetize.process.timing_model.durations.vowels.long, phonetize.process.timing_model.durations.vowels.long_final, phonetize.process.timing_model.durations.vowels.perception_limits.very_long_min, phonetize.process.timing_model.durations.vowels.very_long, phonetize.process.timing_model.durations.vowels.perception_limits.elongation_max',
            'short_min < short <= short_final < long_min <= long <= long_final < very_long_min < very_long < elongation_max',
            'Vowel category ordering is invalid.',
        )

    if not (
        pauses['resync']['min'] < pauses['resync']['max']
        and pauses['resync']['max'] < pauses['short']['min']
        and pauses['short']['min'] < pauses['short']['max']
        and pauses['short']['max'] < pauses['long']['min']
        and pauses['long']['min'] < pauses['long']['max']
    ):
        add_failure(
            'phonetize.process.timing_model.durations.pauses.resync.min, phonetize.process.timing_model.durations.pauses.resync.max, phonetize.process.timing_model.durations.pauses.short.min, phonetize.process.timing_model.durations.pauses.short.max, phonetize.process.timing_model.durations.pauses.long.min, phonetize.process.timing_model.durations.pauses.long.max',
            'resync.min < resync.max < short.min < short.max < long.min < long.max',
            'Pause-band ordering is invalid.',
        )

    cvc_reference = float(durations['cvc_reference'])
    short_min = float(pauses['short']['min'])
    short_max = float(pauses['short']['max'])
    long_min = float(pauses['long']['min'])
    long_max = float(pauses['long']['max'])

    supported_sync_bases = _supported_synchronization_bases(cvc_reference)

    if not any(_pause_multiple_candidates(short_min, short_max, basis) for basis in supported_sync_bases):
        add_warning(
            'phonetize.process.timing_model.durations.pauses.short.min, phonetize.process.timing_model.durations.pauses.short.max, phonetize.process.timing_model.durations.cvc_reference',
            'exists N >= 1 with short.min <= N * synchronization_basis <= short.max',
            'No integer multiple of the active synchronization bases (0.5 * cvc_reference or cvc_reference) falls inside the configured short-pause band.',
            summary_hint=short_pause_hint,
        )

    short_gap = min(_nearest_multiple_gap(short_min, short_max, basis) for basis in supported_sync_bases)
    short_gap_limit = float(vowel_limits['long_min'] - vowel_limits['short_min'])
    if short_gap > short_gap_limit:
        add_failure(
            'phonetize.process.timing_model.durations.pauses.short.min, phonetize.process.timing_model.durations.pauses.short.max, phonetize.process.timing_model.durations.cvc_reference, phonetize.process.timing_model.durations.vowels.perception_limits.long_min, phonetize.process.timing_model.durations.vowels.perception_limits.short_min',
            'short_pause_gap <= long_min - short_min',
            'The nearest-multiple gap for the short-pause band exceeds the allowed vowel perception-gap threshold.',
            summary_hint=verification_hint,
        )

    if not any(_pause_multiple_candidates(long_min, long_max, basis) for basis in supported_sync_bases):
        add_failure(
            'phonetize.process.timing_model.durations.pauses.long.min, phonetize.process.timing_model.durations.pauses.long.max, phonetize.process.timing_model.durations.cvc_reference',
            'exists N >= 1 with long.min <= N * synchronization_basis <= long.max',
            'No integer multiple of the active synchronization bases (0.5 * cvc_reference or cvc_reference) falls inside the configured long-pause band.',
            summary_hint=verification_hint,
        )

    selected_default_paths = (
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
        ('process', 'timing_model', 'durations', 'pauses', 'resync', 'min'),
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

    _ = duration_scale
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