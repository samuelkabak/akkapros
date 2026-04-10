from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import sys
import textwrap
from typing import Any

from akkapros.lib.helpmsg import CONFIG_FILE_COMMENTS, config_help, help_for, section_help
from akkapros.lib.phonetize import (
    PHONETIZE_SECTION,
    PHONETIZE_SECTION_HELP,
    build_default_phonetize_config,
    get_phonetize_field,
    get_relative_value as get_phonetize_relative_value,
    iter_phonetize_fields,
    normalize_phonetize_config,
    render_documented_phonetize_section,
    set_relative_value as set_phonetize_relative_value,
    validate_phonetize_source,
)


class ConfigError(ValueError):
    """Raised when a config file or config option is invalid."""


@dataclass(frozen=True)
class ConfigField:
    default: Any
    kind: str
    description: str
    choices: tuple[str, ...] | None = None


COMMON_SECTION = "common"
ATFPARSE_SECTION = "atfparse"
SYLLABIFY_SECTION = "syllabify"
PROSODY_SECTION = "prosody"
METRICS_SECTION = "metrics"
PRINT_SECTION = "print"
RUNTIME_HELP_DEST = 'help_path'
RUNTIME_HELP_SENTINEL = '__PROGRAM__'
RUNTIME_OPTION_DEST = 'option_values'
RUNTIME_PHONETIZE_ROOT = f'{PHONETIZE_SECTION}.process.timing_model'

CONFIG_SECTION_ORDER = (
    COMMON_SECTION,
    ATFPARSE_SECTION,
    SYLLABIFY_SECTION,
    PROSODY_SECTION,
    PHONETIZE_SECTION,
    METRICS_SECTION,
    PRINT_SECTION,
)

PREFIX_REQUIRED_TOOLS = frozenset(
    {
        "atfparser",
        "syllabifier",
        "prosmaker",
        "phonetizer",
        "metricalc",
        "printer",
        "fullprosmaker",
    }
)

CONFIG_SCHEMA: dict[str, dict[str, ConfigField]] = {
    COMMON_SECTION: {
        "prefix": ConfigField("akkapros", "nullable_string", config_help(COMMON_SECTION, "prefix")),
        "outdir": ConfigField(".", "string", config_help(COMMON_SECTION, "outdir")),
        "quiet": ConfigField(False, "bool", config_help(COMMON_SECTION, "quiet")),
        "no_console": ConfigField(False, "bool", config_help(COMMON_SECTION, "no_console")),
        "log": ConfigField(None, "nullable_string", config_help(COMMON_SECTION, "log")),
        "log_append": ConfigField(False, "bool", config_help(COMMON_SECTION, "log_append")),
    },
    ATFPARSE_SECTION: {
        "remove_hyphens": ConfigField(False, "bool", config_help(ATFPARSE_SECTION, "remove_hyphens")),
        "preserve_case": ConfigField(False, "bool", config_help(ATFPARSE_SECTION, "preserve_case")),
        "preserve_h": ConfigField(False, "bool", config_help(ATFPARSE_SECTION, "preserve_h")),
        "strict": ConfigField(False, "bool", config_help(ATFPARSE_SECTION, "strict")),
        "append": ConfigField(False, "bool", config_help(ATFPARSE_SECTION, "append")),
    },
    SYLLABIFY_SECTION: {
        "extra_vowels": ConfigField("", "string", config_help(SYLLABIFY_SECTION, "extra_vowels")),
        "extra_consonants": ConfigField("", "string", config_help(SYLLABIFY_SECTION, "extra_consonants")),
        "extra_short_punct_chars": ConfigField("", "string", config_help(SYLLABIFY_SECTION, "extra_short_punct_chars")),
        "extra_long_punct_chars": ConfigField("", "string", config_help(SYLLABIFY_SECTION, "extra_long_punct_chars")),
        "extra_short_punct_pattern": ConfigField([], "string_list", config_help(SYLLABIFY_SECTION, "extra_short_punct_pattern")),
        "extra_long_punct_pattern": ConfigField([], "string_list", config_help(SYLLABIFY_SECTION, "extra_long_punct_pattern")),
        "number_format": ConfigField("", "string", config_help(SYLLABIFY_SECTION, "number_format")),
        "merge_hyphen": ConfigField(False, "bool", config_help(SYLLABIFY_SECTION, "merge_hyphen")),
        "merge_lines": ConfigField(False, "bool", config_help(SYLLABIFY_SECTION, "merge_lines")),
        "title": ConfigField(None, "nullable_string", config_help(SYLLABIFY_SECTION, "title")),
    },
    PROSODY_SECTION: {
        "style": ConfigField("lob", "string", config_help(PROSODY_SECTION, "style"), choices=("lob", "sob")),
        "mora_mode": ConfigField("bi", "string", config_help(PROSODY_SECTION, "mora_mode"), choices=("bi", "mono")),
        "relax_last": ConfigField(False, "bool", config_help(PROSODY_SECTION, "relax_last")),
    },
    METRICS_SECTION: {
        "csv": ConfigField(False, "bool", config_help(METRICS_SECTION, "csv")),
        "table": ConfigField(False, "bool", config_help(METRICS_SECTION, "table")),
        "json": ConfigField(False, "bool", config_help(METRICS_SECTION, "json")),
        "explicit_link_count": ConfigField(None, "nullable_scalar", config_help(METRICS_SECTION, "explicit_link_count")),
    },
    PRINT_SECTION: {
        "acute": ConfigField(False, "bool", config_help(PRINT_SECTION, "acute")),
        "bold": ConfigField(False, "bool", config_help(PRINT_SECTION, "bold")),
        "ipa": ConfigField(False, "bool", config_help(PRINT_SECTION, "ipa")),
        "ipa_proto_semitic": ConfigField("preserve", "string", config_help(PRINT_SECTION, "ipa_proto_semitic"), choices=("preserve", "replace")),
        "circ_hiatus": ConfigField(False, "bool", config_help(PRINT_SECTION, "circ_hiatus")),
        "xar": ConfigField(False, "bool", config_help(PRINT_SECTION, "xar")),
        "mbrola": ConfigField(False, "bool", config_help(PRINT_SECTION, "mbrola")),
        "print_merger": ConfigField(False, "bool", config_help(PRINT_SECTION, "print_merger")),
    },
}

TOOL_CONFIG_SECTIONS: dict[str, tuple[tuple[str, dict[str, str] | None], ...]] = {
    "atfparser": ((COMMON_SECTION, None), (ATFPARSE_SECTION, None)),
    "syllabifier": ((COMMON_SECTION, None), (SYLLABIFY_SECTION, None)),
    "prosmaker": ((COMMON_SECTION, None), (PROSODY_SECTION, None)),
    "phonetizer": (
        (COMMON_SECTION, None),
        (
            PHONETIZE_SECTION,
            {
                "process.geminate_policy": "geminate_policy",
                "process.accentuation_distribution_policy": "accentuation_distribution_policy",
                "process.short_pause_policy": "short_pause_policy",
                "process.drift_policy": "drift_policy",
                "process.drift_tolerance": "drift_tolerance",
            },
        ),
    ),
    "metricalc": ((COMMON_SECTION, None), (METRICS_SECTION, None)),
    "printer": ((COMMON_SECTION, None), (PRINT_SECTION, None)),
    "fullprosmaker": (
        (COMMON_SECTION, None),
        (
            SYLLABIFY_SECTION,
            {
                "extra_vowels": "extra_vowels",
                "extra_consonants": "extra_consonants",
                "extra_short_punct_chars": "extra_short_punct_chars",
                "extra_long_punct_chars": "extra_long_punct_chars",
                "extra_short_punct_pattern": "extra_short_punct_pattern",
                "extra_long_punct_pattern": "extra_long_punct_pattern",
                "number_format": "number_format",
                "merge_hyphen": "syl_merge_hyphens",
                "merge_lines": "syl_merge_lines",
                "title": "title",
            },
        ),
        (
            PROSODY_SECTION,
            {
                "style": "prosody_style",
                "mora_mode": "mora_mode",
                "relax_last": "prosody_relax_last",
            },
        ),
        (
            PHONETIZE_SECTION,
            {
                "process.geminate_policy": "phonetize_geminate_policy",
                "process.accentuation_distribution_policy": "phonetize_accentuation_distribution_policy",
                "process.short_pause_policy": "phonetize_short_pause_policy",
                "process.drift_policy": "phonetize_drift_policy",
                "process.drift_tolerance": "phonetize_drift_tolerance",
            },
        ),
        (
            METRICS_SECTION,
            {
                "csv": "metrics_csv",
                "table": "metrics_table",
                "json": "metrics_json",
                "explicit_link_count": "explicit_link_count",
            },
        ),
        (
            PRINT_SECTION,
            {
                "acute": "print_acute",
                "bold": "print_bold",
                "ipa": "print_ipa",
                "ipa_proto_semitic": "print_ipa_proto_semitic",
                "circ_hiatus": "print_circ_hiatus",
                "xar": "print_xar",
                "print_merger": "print_merger",
            },
        ),
    ),
}

PROGRAM_CONFIG_ROOTS: dict[str, tuple[str, ...]] = {
    tool_name: tuple(section for section, _field_map in sections)
    for tool_name, sections in TOOL_CONFIG_SECTIONS.items()
}


def build_default_config() -> dict[str, dict[str, Any]]:
    defaults = {
        section: {key: deepcopy(field.default) for key, field in fields.items()}
        for section, fields in CONFIG_SCHEMA.items()
    }
    defaults[PHONETIZE_SECTION] = build_default_phonetize_config()
    return defaults


def build_runtime_default_config() -> dict[str, dict[str, Any]]:
    defaults = build_default_config()
    defaults[PHONETIZE_SECTION]['process']['drift_policy'] = 'extensible'
    return defaults


def resolve_config_path(path: str) -> tuple[str, str, ConfigField]:
    parts = [part for part in path.split(".") if part]
    if not parts:
        raise ConfigError(f"Unknown config key: {path}")
    section = parts[0]
    if section == PHONETIZE_SECTION:
        try:
            return PHONETIZE_SECTION, ".".join(parts[1:]), get_phonetize_field(tuple(parts[1:]))  # type: ignore[return-value]
        except KeyError as exc:
            raise ConfigError(f"Unknown config key: {path}") from exc
    if len(parts) != 2:
        raise ConfigError(f"Unknown config key: {path}")
    key = parts[1]
    fields = CONFIG_SCHEMA.get(section)
    if fields is None or key not in fields:
        raise ConfigError(f"Unknown config key: {path}")
    return section, key, fields[key]


def iter_config_paths() -> list[tuple[str, ConfigField]]:
    entries: list[tuple[str, ConfigField]] = []
    for section in CONFIG_SECTION_ORDER:
        if section == PHONETIZE_SECTION:
            for path, field in iter_phonetize_fields():
                entries.append((".".join(path), field))
            continue
        for key, field in CONFIG_SCHEMA[section].items():
            entries.append((f"{section}.{key}", field))
    return entries


def _parse_scalar(raw: str) -> Any:
    if raw.startswith('"') or raw.startswith('[') or raw.startswith('{'):
        return json.loads(raw)
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "null":
        return None
    if raw and raw[0] == "'" and raw[-1] == "'":
        return raw[1:-1]
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def parse_config_cli_value(raw: str) -> Any:
    return _parse_scalar(raw)


def parse_config_text(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ConfigError(f"Invalid config indentation: {line!r}")
        stripped = line.strip()
        key, sep, value = stripped.partition(":")
        if not sep:
            raise ConfigError(f"Invalid config line: {line!r}")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ConfigError("Invalid config structure")
        parent = stack[-1][1]
        value = value.lstrip()
        if value == "":
            node: dict[str, Any] = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = _parse_scalar(value)
    return root


def _dump_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return f"{value:.1f}"
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def _dump_mapping(lines: list[str], mapping: dict[str, Any], indent: int) -> None:
    prefix = " " * indent
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            _dump_mapping(lines, value, indent + 2)
        else:
            lines.append(f"{prefix}{key}: {_dump_scalar(value)}")


def dump_config_text(config: dict[str, Any]) -> str:
    lines: list[str] = []
    _dump_mapping(lines, config, 0)
    return "\n".join(lines) + "\n"


def _coerce_scalar(value: Any, kind: str) -> Any:
    if kind == "bool":
        if not isinstance(value, bool):
            raise ConfigError(f"Expected boolean value, got {type(value).__name__}")
        return value
    if kind == "string":
        if not isinstance(value, str):
            raise ConfigError(f"Expected string value, got {type(value).__name__}")
        return value
    if kind == "nullable_string":
        if value is not None and not isinstance(value, str):
            raise ConfigError(f"Expected string or null value, got {type(value).__name__}")
        return value
    if kind == "nullable_scalar":
        if value is not None and isinstance(value, (dict, list)):
            raise ConfigError(f"Expected scalar or null value, got {type(value).__name__}")
        return value
    if kind == "float":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConfigError(f"Expected numeric value, got {type(value).__name__}")
        return float(value)
    if kind == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ConfigError(f"Expected integer value, got {type(value).__name__}")
        return int(value)
    if kind == "string_list":
        if not isinstance(value, list):
            raise ConfigError(f"Expected list value, got {type(value).__name__}")
        if not all(isinstance(item, str) for item in value):
            raise ConfigError("Expected a list of strings")
        return list(value)
    raise ConfigError(f"Unknown config field kind: {kind}")


def validate_config_source(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(config, dict):
        raise ConfigError("Config root must be a mapping")

    valid_sections = set(CONFIG_SCHEMA) | {PHONETIZE_SECTION}
    unknown_sections = sorted(set(config) - valid_sections)
    if unknown_sections:
        raise ConfigError(f"Unknown config sections: {', '.join(unknown_sections)}")

    validated: dict[str, Any] = {}
    for section, fields in CONFIG_SCHEMA.items():
        if section not in config:
            continue
        raw_section = config[section]
        if raw_section is None:
            raw_section = {}
        if not isinstance(raw_section, dict):
            raise ConfigError(f"Config section {section!r} must be a mapping")
        unknown_keys = sorted(set(raw_section) - set(fields))
        if unknown_keys:
            raise ConfigError(f"Unknown keys in section {section!r}: {', '.join(unknown_keys)}")
        validated_section: dict[str, Any] = {}
        for key, raw_value in raw_section.items():
            field = fields[key]
            if raw_value is None:
                validated_section[key] = None
                continue
            value = _coerce_scalar(raw_value, field.kind)
            if field.choices is not None and value not in field.choices:
                raise ConfigError(
                    f"Invalid value for {section}.{key}: {value!r}; expected one of {field.choices!r}"
                )
            validated_section[key] = value
        validated[section] = validated_section
    if PHONETIZE_SECTION in config:
        try:
            validated[PHONETIZE_SECTION] = validate_phonetize_source(config[PHONETIZE_SECTION], _coerce_scalar)
        except ValueError as exc:
            raise ConfigError(str(exc)) from exc
    return validated


def normalize_config(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validated = validate_config_source(config)
    normalized = build_default_config()
    for section, fields in CONFIG_SCHEMA.items():
        raw_section = validated.get(section, {})
        for key in fields:
            if key not in raw_section:
                continue
            value = raw_section[key]
            if value is None:
                continue
            normalized[section][key] = value
    if PHONETIZE_SECTION in validated:
        normalized[PHONETIZE_SECTION] = normalize_phonetize_config(validated[PHONETIZE_SECTION], _coerce_scalar)
    return normalized


def load_config_file(path: str | Path) -> dict[str, dict[str, Any]]:
    config_path = Path(path)
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Unable to read config file {config_path}: {exc}") from exc
    return normalize_config(parse_config_text(text))


def load_raw_config_file(path: str | Path) -> dict[str, dict[str, Any]]:
    config_path = Path(path)
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Unable to read config file {config_path}: {exc}") from exc
    return validate_config_source(parse_config_text(text))


def write_config_file(path: str | Path, config: dict[str, Any]) -> None:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    materialized = validate_config_write(config)
    config_path.write_text(_render_documented_config(materialized), encoding="utf-8")


def apply_overrides(
    config: dict[str, dict[str, Any]],
    overrides: dict[tuple[str, str], Any],
) -> dict[str, dict[str, Any]]:
    updated = normalize_config(config)
    for (section, key), value in overrides.items():
        if section == PHONETIZE_SECTION:
            path = key.split('.') if key else []
            field = get_phonetize_field(tuple(path))
            coerced = _coerce_scalar(value, field.kind)
            if field.choices is not None and coerced not in field.choices:
                raise ConfigError(
                    f"Invalid value for {section}.{key}: {coerced!r}; expected one of {field.choices!r}"
                )
            updated[PHONETIZE_SECTION] = set_phonetize_relative_value(updated[PHONETIZE_SECTION], tuple(path), coerced)
            continue
        if section not in CONFIG_SCHEMA or key not in CONFIG_SCHEMA[section]:
            raise ConfigError(f"Unknown override target: {section}.{key}")
        field = CONFIG_SCHEMA[section][key]
        coerced = _coerce_scalar(value, field.kind)
        if field.choices is not None and coerced not in field.choices:
            raise ConfigError(
                f"Invalid value for {section}.{key}: {coerced!r}; expected one of {field.choices!r}"
            )
        updated[section][key] = coerced
    return updated


def overlay_config_source(
    base_config: dict[str, dict[str, Any]],
    source: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    updated = deepcopy(base_config)
    for section, values in source.items():
        if section == PHONETIZE_SECTION:
            updated_section = deepcopy(updated[PHONETIZE_SECTION])

            def _merge(target: dict[str, Any], incoming: dict[str, Any]) -> None:
                for key, value in incoming.items():
                    if value is None:
                        continue
                    if isinstance(value, dict):
                        _merge(target[key], value)
                    else:
                        target[key] = deepcopy(value)

            _merge(updated_section, values)
            updated[PHONETIZE_SECTION] = updated_section
            continue
        section_values = deepcopy(updated[section])
        for key, value in values.items():
            if value is None:
                continue
            section_values[key] = deepcopy(value)
        updated[section] = section_values
    return normalize_config(updated)


def tool_config_values(config: dict[str, dict[str, Any]], tool_name: str) -> dict[str, Any]:
    normalized = normalize_config(config)
    if tool_name not in TOOL_CONFIG_SECTIONS:
        raise ConfigError(f"Unsupported tool config section: {tool_name}")
    merged: dict[str, Any] = {}
    for section, field_map in TOOL_CONFIG_SECTIONS[tool_name]:
        section_values = normalized[section]
        if field_map is None:
            merged.update(deepcopy(section_values))
            continue
        for key, dest in field_map.items():
            if section == PHONETIZE_SECTION:
                merged[dest] = deepcopy(get_phonetize_relative_value(section_values, tuple(key.split('.'))))
                continue
            merged[dest] = deepcopy(section_values[key])
    return merged


def tool_dest_to_config_path(tool_name: str) -> dict[str, str]:
    if tool_name not in TOOL_CONFIG_SECTIONS:
        raise ConfigError(f"Unsupported tool config section: {tool_name}")
    mapping: dict[str, str] = {}
    for section, field_map in TOOL_CONFIG_SECTIONS[tool_name]:
        if field_map is None:
            if section == PHONETIZE_SECTION:
                continue
            for key in CONFIG_SCHEMA[section]:
                mapping[key] = f'{section}.{key}'
            continue
        for key, dest in field_map.items():
            mapping[dest] = f'{section}.{key}'
    return mapping


def runtime_display_path(path: str) -> str:
    if path.startswith(f'{PHONETIZE_SECTION}.process.'):
        key = path[len(f'{PHONETIZE_SECTION}.process.'):]
        head = key.split('.', 1)[0]
        if head in {'geminate_policy', 'accentuation_distribution_policy', 'short_pause_policy', 'drift_policy', 'drift_tolerance'}:
            return f'{RUNTIME_PHONETIZE_ROOT}.{key}'
    if path.startswith(f'{PHONETIZE_SECTION}.timing_model.'):
        key = path[len(f'{PHONETIZE_SECTION}.timing_model.'):]
        return f'{RUNTIME_PHONETIZE_ROOT}.{key}'
    return path


def normalize_runtime_config_path(path: str) -> str:
    normalized = path.strip()
    if normalized.startswith(f'{RUNTIME_PHONETIZE_ROOT}.'):
        key = normalized[len(f'{RUNTIME_PHONETIZE_ROOT}.'):]
        head = key.split('.', 1)[0]
        if head in {'geminate_policy', 'accentuation_distribution_policy', 'short_pause_policy', 'drift_policy', 'drift_tolerance'}:
            return f'{PHONETIZE_SECTION}.process.{key}'
        return f'{PHONETIZE_SECTION}.timing_model.{key}'
    return normalized


def build_runtime_effective_config(config: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    normalized = normalize_config(config)
    runtime = deepcopy(normalized)
    phonetize_section = runtime[PHONETIZE_SECTION]
    runtime_timing_model = deepcopy(phonetize_section['timing_model'])
    for key, value in phonetize_section['process'].items():
        runtime_timing_model[key] = deepcopy(value)
    runtime[PHONETIZE_SECTION] = {
        'process': {
            'timing_model': runtime_timing_model,
        }
    }
    return runtime


def get_section_config(config: dict[str, dict[str, Any]], section: str) -> Any:
    normalized = normalize_config(config)
    if section not in normalized:
        raise ConfigError(f"Unsupported config section: {section}")
    return deepcopy(normalized[section])


def get_program_config_roots(tool_name: str) -> tuple[str, ...]:
    try:
        return PROGRAM_CONFIG_ROOTS[tool_name]
    except KeyError as exc:
        raise ConfigError(f'Unsupported tool config section: {tool_name}') from exc


def require_effective_prefix(prefix: Any, tool_name: str) -> str:
    if tool_name not in PREFIX_REQUIRED_TOOLS:
        return "" if prefix is None else str(prefix)
    if not isinstance(prefix, str) or not prefix.strip():
        raise ConfigError(
            f"{tool_name} requires a non-null effective prefix; set common.prefix in --conf or pass --prefix"
        )
    return prefix


def validate_config_write(config: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    source = validate_config_source(config)
    normalized = normalize_config(source)
    prefix = normalized[COMMON_SECTION].get("prefix")
    if not isinstance(prefix, str) or not prefix.strip():
        raise ConfigError(
            "confwriter cannot write a config with a null common.prefix; set --prefix or update the config first"
        )
    materialized = build_default_config()
    for section, values in source.items():
        if section == PHONETIZE_SECTION:
            materialized[PHONETIZE_SECTION] = deepcopy(values)
            continue
        for key, value in values.items():
            materialized[section][key] = deepcopy(value)
    return materialized


def get_config_value(config: dict[str, Any], path: str) -> Any:
    section, key, _field = resolve_config_path(path)
    normalized = normalize_config(config)
    if section == PHONETIZE_SECTION:
        return get_phonetize_relative_value(normalized[PHONETIZE_SECTION], tuple(key.split('.')))
    return deepcopy(normalized[section][key])


def set_config_value(config: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    section, key, field = resolve_config_path(path)
    updated = validate_config_source(config)
    if section == PHONETIZE_SECTION:
        coerced = _coerce_scalar(value, field.kind)
        if field.choices is not None and coerced not in field.choices:
            raise ConfigError(
                f"Invalid value for {path}: {coerced!r}; expected one of {field.choices!r}"
            )
        section_values = deepcopy(updated.get(PHONETIZE_SECTION, {}))
        updated[PHONETIZE_SECTION] = set_phonetize_relative_value(section_values, tuple(key.split('.')), coerced)
        return updated
    section_values = deepcopy(updated.get(section, {}))
    coerced = _coerce_scalar(value, field.kind)
    if field.choices is not None and coerced not in field.choices:
        raise ConfigError(
            f"Invalid value for {path}: {coerced!r}; expected one of {field.choices!r}"
        )
    section_values[key] = coerced
    updated[section] = section_values
    return updated


def unset_config_value(config: dict[str, Any], path: str) -> dict[str, Any]:
    section, key, _field = resolve_config_path(path)
    updated = validate_config_source(config)
    if section == PHONETIZE_SECTION:
        section_values = deepcopy(updated.get(PHONETIZE_SECTION, {}))
        updated[PHONETIZE_SECTION] = set_phonetize_relative_value(section_values, tuple(key.split('.')), None)
        return updated
    section_values = deepcopy(updated.get(section, {}))
    section_values[key] = None
    updated[section] = section_values
    return updated


def set_default_config_value(config: dict[str, Any], path: str) -> dict[str, Any]:
    section, key, field = resolve_config_path(path)
    updated = validate_config_source(config)
    if section == PHONETIZE_SECTION:
        section_values = deepcopy(updated.get(PHONETIZE_SECTION, {}))
        updated[PHONETIZE_SECTION] = set_phonetize_relative_value(section_values, tuple(key.split('.')), deepcopy(field.default))
        return updated
    section_values = deepcopy(updated.get(section, {}))
    section_values[key] = deepcopy(field.default)
    updated[section] = section_values
    return updated


def add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--conf', help=help_for("config.conf"))


def add_runtime_interface_arguments(parser: argparse.ArgumentParser, tool_name: str) -> None:
    parser.add_argument(
        '-h',
        '--help',
        nargs='?',
        const=RUNTIME_HELP_SENTINEL,
        default=None,
        dest=RUNTIME_HELP_DEST,
        metavar='PATH',
        help='Show program-scoped help, or help for one config subtree.',
    )
    option_help_key = f'{tool_name}.option'
    try:
        option_help = help_for(option_help_key)
    except KeyError:
        option_help = 'Override one config path with KEY=VALUE syntax; repeatable.'
    parser.add_argument(
        '-t',
        '--option',
        dest=RUNTIME_OPTION_DEST,
        action='append',
        default=[],
        metavar='KEY=VALUE',
        help=option_help,
    )


def _explicit_option_map(parser: argparse.ArgumentParser, argv: list[str]) -> dict[str, str]:
    explicit: dict[str, str] = {}
    option_map = parser._option_string_actions  # type: ignore[attr-defined]
    for token in argv:
        if not token.startswith('-') or token == '-':
            continue
        option = token.split('=', 1)[0]
        action = option_map.get(option)
        if action is None:
            continue
        explicit[action.dest] = option
    return explicit


def _runtime_paths_for_tool(tool_name: str) -> list[tuple[str, Any]]:
    entries: list[tuple[str, Any]] = []
    for section in CONFIG_SECTION_ORDER:
        if section == PHONETIZE_SECTION:
            for path, field in iter_phonetize_fields():
                dotted = '.'.join(path)
                entries.append((runtime_display_path(dotted), field))
            continue
        for key, field in CONFIG_SCHEMA[section].items():
            entries.append((f'{section}.{key}', field))
    roots = get_program_config_roots(tool_name)
    allowed_prefixes = tuple(f'{root}.' for root in roots)
    return [
        (path, field)
        for path, field in entries
        if path in roots or path.startswith(allowed_prefixes)
    ]


def _format_field_kind(kind: str) -> str:
    labels = {
        'bool': 'BOOL',
        'string': 'TEXT',
        'nullable_string': 'TEXT|null',
        'nullable_scalar': 'SCALAR|null',
        'float': 'NUMBER',
        'int': 'INTEGER',
        'string_list': 'TEXT[]',
    }
    return labels.get(kind, kind.upper())


def _render_runtime_config_entries(entries: list[tuple[str, Any]]) -> list[str]:
    lines: list[str] = []
    for path, field in entries:
        choice_suffix = ''
        if field.choices is not None:
            choice_suffix = f' choices={", ".join(str(choice) for choice in field.choices)}'
        lines.append(f'  {path} [{_format_field_kind(field.kind)}] default={_dump_scalar(field.default)}{choice_suffix}')
        for raw_line in field.description.splitlines():
            lines.append(f'    {raw_line}')
    return lines


def _classify_parser_actions(
    parser: argparse.ArgumentParser,
    tool_name: str,
) -> tuple[list[tuple[argparse.Action, str]], list[argparse.Action], list[argparse.Action]]:
    config_backed = tool_dest_to_config_path(tool_name)
    deprecated_actions: list[tuple[argparse.Action, str]] = []
    interface_actions: list[argparse.Action] = []
    cli_only_actions: list[argparse.Action] = []
    for action in parser._actions:
        if action.dest == 'help':
            continue
        if action.dest == RUNTIME_HELP_DEST or action.dest == RUNTIME_OPTION_DEST or action.dest == 'conf':
            interface_actions.append(action)
            continue
        if action.dest in config_backed:
            deprecated_actions.append((action, runtime_display_path(config_backed[action.dest])))
            continue
        cli_only_actions.append(action)
    return deprecated_actions, interface_actions, cli_only_actions


def _render_action_lines(actions: list[argparse.Action]) -> list[str]:
    lines: list[str] = []
    for action in actions:
        if action.help == argparse.SUPPRESS:
            continue
        if action.option_strings:
            label = ', '.join(action.option_strings)
            if action.metavar:
                label = f'{label} {action.metavar}'
            elif action.nargs not in (0, None) and action.dest:
                label = f'{label} {action.dest.upper()}'
        else:
            label = action.dest
        lines.append(f'  {label}')
        if action.help:
            lines.append(f'    {action.help}')
    return lines


def render_runtime_help(
    parser: argparse.ArgumentParser,
    tool_name: str,
    help_path: str | None = None,
) -> str:
    normalized_path = None if help_path in (None, RUNTIME_HELP_SENTINEL) else help_path.strip()
    lines = [parser.format_usage().rstrip(), '']
    if parser.description:
        lines.append(parser.description)
        lines.append('')

    deprecated_actions, interface_actions, cli_only_actions = _classify_parser_actions(parser, tool_name)

    if interface_actions:
        lines.append('Runtime Config Interface:')
        lines.extend(_render_action_lines(interface_actions))
        lines.append('')

    all_entries = _runtime_paths_for_tool(tool_name)
    if normalized_path is None:
        lines.append('Active Config Paths:')
        lines.extend(_render_runtime_config_entries(all_entries))
        lines.append('')
    else:
        entries = [
            (path, field)
            for path, field in all_entries
            if path == normalized_path or path.startswith(f'{normalized_path}.')
        ]
        if not entries and normalized_path not in get_program_config_roots(tool_name):
            raise ConfigError(f'Unknown help path for {tool_name}: {normalized_path}')
        lines.append(f'Config Help: {normalized_path}')
        lines.extend(_render_runtime_config_entries(entries))
        lines.append('')

    if deprecated_actions and normalized_path is None:
        lines.append('Deprecated Dedicated Flags:')
        for action, path in deprecated_actions:
            label = ', '.join(action.option_strings)
            lines.append(f'  {label} -> {path}')
            if action.help:
                lines.append(f'    {action.help}')
        lines.append('')

    if cli_only_actions and normalized_path is None:
        lines.append('CLI-only Arguments:')
        lines.extend(_render_action_lines(cli_only_actions))
        lines.append('')

    return '\n'.join(line for line in lines).rstrip() + '\n'


def log_deprecated_config_flag_warnings(logger, args: argparse.Namespace) -> None:
    for option_string, runtime_path in getattr(args, '_deprecated_config_flags', ()):  # pragma: no branch - simple loop
        logger.info(
            'Deprecated config-backed flag %s is still supported for compatibility; prefer --option %s=VALUE or --conf FILE.',
            option_string,
            runtime_path,
        )


def parse_args_with_config(
    parser: argparse.ArgumentParser,
    tool_name: str,
    argv: list[str] | None = None,
) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(argv)
    help_path = getattr(args, RUNTIME_HELP_DEST, None)
    if help_path is not None:
        sys.stdout.write(render_runtime_help(parser, tool_name, help_path))
        raise SystemExit(0)

    explicit = _explicit_option_map(parser, argv)
    config = build_runtime_default_config()
    conf_path = getattr(args, 'conf', None)
    if conf_path:
        config = overlay_config_source(config, load_raw_config_file(conf_path))

    dest_to_path = tool_dest_to_config_path(tool_name)
    for dest, path in dest_to_path.items():
        if dest not in explicit:
            continue
        config = set_config_value(config, path, deepcopy(getattr(args, dest)))

    for raw in getattr(args, RUNTIME_OPTION_DEST, []) or []:
        path, sep, value = raw.partition('=')
        if not sep or not path.strip():
            raise ConfigError(f"Invalid --option argument: {raw!r}; expected KEY=VALUE")
        config = set_config_value(config, normalize_runtime_config_path(path), parse_config_cli_value(value))

    values = tool_config_values(config, tool_name)
    for dest, value in values.items():
        setattr(args, dest, deepcopy(value))
    args._effective_grouped_config = deepcopy(config)
    args._effective_config = build_runtime_effective_config(config)
    args._config_roots = get_program_config_roots(tool_name)
    args._deprecated_config_flags = tuple(
        (explicit[dest], runtime_display_path(path))
        for dest, path in dest_to_path.items()
        if dest in explicit
    )
    return args


def config_field_cli_flag(section: str, key: str) -> str:
    if section == COMMON_SECTION:
        return f"--{key.replace('_', '-')}"
    return f"--{section.replace('_', '-')}-{key.replace('_', '-')}"


def config_comment_lines() -> list[str]:
    return [f"# {line}" for line in CONFIG_FILE_COMMENTS]


def _append_wrapped_comment(lines: list[str], text: str, indent: int = 0) -> None:
    prefix = " " * indent + "# "
    width = max(40, 88 - len(prefix))
    for raw_line in text.splitlines():
        if not raw_line.strip():
            lines.append(prefix.rstrip())
            continue
        for chunk in textwrap.wrap(raw_line, width=width):
            lines.append(f"{prefix}{chunk}")


def _render_documented_section(lines: list[str], section: str, values: dict[str, Any]) -> None:
    _append_wrapped_comment(lines, section_help(section))
    lines.append(f"{section}:")
    for key, value in values.items():
        _append_wrapped_comment(lines, config_help(section, key), indent=2)
        lines.append(f"  {key}: {_dump_scalar(value)}")


def _render_documented_config(config: dict[str, dict[str, Any]]) -> str:
    lines = config_comment_lines() + [""]
    for section in CONFIG_SECTION_ORDER:
        if section == PHONETIZE_SECTION:
            render_documented_phonetize_section(
                lines,
                config[PHONETIZE_SECTION],
                append_comment=_append_wrapped_comment,
                dump_scalar=_dump_scalar,
            )
            lines.append("")
            continue
        _render_documented_section(lines, section, config[section])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_documented_default_config() -> str:
    return _render_documented_config(build_default_config())
