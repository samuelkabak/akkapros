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

CONFIG_SECTION_ORDER = (
    COMMON_SECTION,
    ATFPARSE_SECTION,
    SYLLABIFY_SECTION,
    PROSODY_SECTION,
    METRICS_SECTION,
    PRINT_SECTION,
)

PREFIX_REQUIRED_TOOLS = frozenset(
    {
        "atfparser",
        "syllabifier",
        "prosmaker",
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
        "wpm": ConfigField(165.0, "float", config_help(METRICS_SECTION, "wpm")),
        "pause_ratio": ConfigField(35.0, "float", config_help(METRICS_SECTION, "pause_ratio")),
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
            METRICS_SECTION,
            {
                "csv": "metrics_csv",
                "table": "metrics_table",
                "json": "metrics_json",
                "wpm": "metrics_wpm",
                "pause_ratio": "metrics_pause_ratio",
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


def build_default_config() -> dict[str, dict[str, Any]]:
    return {
        section: {key: deepcopy(field.default) for key, field in fields.items()}
        for section, fields in CONFIG_SCHEMA.items()
    }


def resolve_config_path(path: str) -> tuple[str, str, ConfigField]:
    parts = [part for part in path.split(".") if part]
    if len(parts) != 2:
        raise ConfigError(f"Unknown config key: {path}")
    section, key = parts
    fields = CONFIG_SCHEMA.get(section)
    if fields is None or key not in fields:
        raise ConfigError(f"Unknown config key: {path}")
    return section, key, fields[key]


def iter_config_paths() -> list[tuple[str, ConfigField]]:
    entries: list[tuple[str, ConfigField]] = []
    for section in CONFIG_SECTION_ORDER:
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

    unknown_sections = sorted(set(config) - set(CONFIG_SCHEMA))
    if unknown_sections:
        raise ConfigError(f"Unknown config sections: {', '.join(unknown_sections)}")

    validated: dict[str, dict[str, Any]] = {}
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
            merged[dest] = deepcopy(section_values[key])
    return merged


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
        for key, value in values.items():
            materialized[section][key] = deepcopy(value)
    return materialized


def get_config_value(config: dict[str, Any], path: str) -> Any:
    section, key, _field = resolve_config_path(path)
    normalized = normalize_config(config)
    return deepcopy(normalized[section][key])


def set_config_value(config: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    section, key, field = resolve_config_path(path)
    updated = validate_config_source(config)
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
    section_values = deepcopy(updated.get(section, {}))
    section_values[key] = None
    updated[section] = section_values
    return updated


def set_default_config_value(config: dict[str, Any], path: str) -> dict[str, Any]:
    section, key, field = resolve_config_path(path)
    updated = validate_config_source(config)
    section_values = deepcopy(updated.get(section, {}))
    section_values[key] = deepcopy(field.default)
    updated[section] = section_values
    return updated


def add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--conf', help=help_for("config.conf"))


def _explicit_option_dests(parser: argparse.ArgumentParser, argv: list[str]) -> set[str]:
    explicit: set[str] = set()
    option_map = parser._option_string_actions  # type: ignore[attr-defined]
    for token in argv:
        if not token.startswith('-') or token == '-':
            continue
        option = token.split('=', 1)[0]
        action = option_map.get(option)
        if action is None:
            continue
        explicit.add(action.dest)
    return explicit


def parse_args_with_config(
    parser: argparse.ArgumentParser,
    tool_name: str,
    argv: list[str] | None = None,
) -> argparse.Namespace:
    argv = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(argv)
    conf_path = getattr(args, 'conf', None)
    if not conf_path:
        return args

    config = load_config_file(conf_path)
    values = tool_config_values(config, tool_name)
    explicit = _explicit_option_dests(parser, argv)
    for dest, value in values.items():
        if dest in explicit:
            continue
        setattr(args, dest, deepcopy(value))
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
    for chunk in textwrap.wrap(text, width=width):
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
        _render_documented_section(lines, section, config[section])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_documented_default_config() -> str:
    return _render_documented_config(build_default_config())
