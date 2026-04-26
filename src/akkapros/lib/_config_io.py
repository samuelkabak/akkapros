"""
CLI argument parsing, help text rendering, and documented config output for the
Akkadian Prosody Toolkit configuration system.

Extracted from config.py during CR-092 split. All functions here handle
I/O concerns: argument parsing, help rendering, config file loading/writing.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import sys
import textwrap
from typing import Any

from akkapros.lib.config import (
    COMMON_SECTION,
    CONFIG_SCHEMA,
    CONFIG_SECTION_ORDER,
    PHONETIZE_SECTION,
    RUNTIME_HELP_DEST,
    RUNTIME_HELP_SENTINEL,
    RUNTIME_OPTION_DEST,
    ConfigError,
    _coerce_scalar,
    _dump_scalar,
    _is_config_field,
    _iter_section_fields,
    _merge_defined_values,
    _merge_explicit_values,
    _parse_scalar,
    _set_nested_value,
    build_default_config,
    build_runtime_default_config,
    build_runtime_effective_config,
    get_program_config_roots,
    get_section_config,
    normalize_config,
    normalize_runtime_config_path,
    overlay_config_source,
    parse_config_cli_value,
    parse_config_text,
    resolve_config_path,
    runtime_display_path,
    set_config_value,
    tool_config_values,
    tool_dest_to_config_path,
    validate_config_source,
    validate_config_write,
)
from akkapros.lib.helpmsg import (
    CONFIG_FILE_COMMENTS,
)
from akkapros.lib.helpmsg import config_help, help_for, section_help
from akkapros.lib.phonetize import (
    iter_phonetize_fields,
    render_documented_phonetize_section,
    validate_phonetize_source,
)


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
        for relative_path, field in _iter_section_fields(section):
            entries.append((f'{section}.{".".join(relative_path)}', field))
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

    def _render(node: dict[str, Any], schema: dict[str, Any], indent: int) -> None:
        prefix = ' ' * indent
        for key, spec in schema.items():
            value = node[key]
            if _is_config_field(spec):
                _append_wrapped_comment(lines, spec.description, indent=indent)
                lines.append(f'{prefix}{key}: {_dump_scalar(value)}')
                continue
            lines.append(f'{prefix}{key}:')
            _render(value, spec, indent + 2)

    _render(values, CONFIG_SCHEMA[section], 2)


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
