#!/usr/bin/env python3
"""Create or update package-wide YAML config files for akkapros."""

from __future__ import annotations

import argparse
from copy import deepcopy
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__
from akkapros.lib.config import (
    ConfigError,
    add_config_argument,
    build_default_config,
    get_config_value,
    iter_config_paths,
    load_raw_config_file,
    parse_config_cli_value,
    resolve_config_path,
    set_config_value,
    set_default_config_value,
    unset_config_value,
    write_config_file,
)
from akkapros.lib.helpmsg import help_for
from akkapros.lib.phonetize import (
    PHONETIZE_SECTION,
    render_phonetize_verification_lines,
    verify_phonetize_config,
)
from akkapros.lib.utils import (
    RawDefaultsHelpFormatter,
    add_standard_logging_arguments,
    add_standard_version_argument,
    format_path_for_logging,
    log_startup_banner,
    log_selftest_result,
    log_selftest_summary,
    setup_cli_logging,
)


def _format_scalar(value: object) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return 'null'
    if isinstance(value, float):
        if value.is_integer():
            return f'{value:.1f}'
        return str(value)
    if isinstance(value, list):
        inner = ', '.join(_format_scalar(item) for item in value)
        return f'[{inner}]'
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def _type_display(kind: str) -> str:
    displays = {
        'bool': 'true | false',
        'float': 'NUMBER',
        'string': 'TEXT',
        'nullable_string': 'TEXT | null',
        'nullable_scalar': 'SCALAR | null',
        'string_list': 'LIST[TEXT]',
    }
    return displays.get(kind, kind)


def _parse_assignment(raw: str) -> tuple[str, object]:
    key, sep, value = raw.partition('=')
    if not sep or not key.strip():
        raise ConfigError(f'Invalid --set argument: {raw!r}; expected KEY=VALUE')
    section, schema_key, _field = resolve_config_path(key.strip())
    return f'{section}.{schema_key}', parse_config_cli_value(value)


def _list_lines(filter_text: str | None) -> list[str]:
    filtered = (filter_text or '').lower()
    lines: list[str] = []
    for path, field in iter_config_paths():
        if filtered and filtered not in path.lower():
            continue
        default_text = f'(default: {_format_scalar(deepcopy(field.default))})'
        lines.append(
            f'{path} {{ {_type_display(field.kind)} }} {default_text} : {field.description}'
        )
    return lines


def _run_selftests() -> bool:
    logger = setup_cli_logging(argparse.Namespace(quiet=False, no_console=False, log=None, log_append=False), 'akkapros.cli.confwriter')
    cases = [
        ('set assignment', lambda: _parse_assignment('common.run.prefix=demo')[0] == 'common.run.prefix'),
        ('set assignment rejects bad key', _selftest_invalid_key),
        ('list filter works', lambda: all('atfparse' in line for line in _list_lines('atfparse'))),
        ('list inventory non-empty', lambda: len(_list_lines(None)) > 0),
        ('shared verify warns on high pause ratio', lambda: verify_phonetize_config({'process': {'timing_model': {'speech': {'pause_ratio': 71}}}}).status == 'pass-with-warnings'),
    ]
    passed = 0
    total = len(cases)
    for index, (label, checker) in enumerate(cases, start=1):
        ok = checker()
        if ok:
            passed += 1
        log_selftest_result(logger, ok, 'Confwriter', f'[{index}/{total}] {label}')
    log_selftest_summary(logger, 'Confwriter', passed, total)
    return passed == total


def _selftest_invalid_key() -> bool:
    try:
        _parse_assignment('common.strict=true')
    except ConfigError:
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Create, inspect, and update package-wide akkapros YAML config files',
        formatter_class=RawDefaultsHelpFormatter,
    )
    add_standard_version_argument(parser, 'akkapros-confwriter')
    add_standard_logging_arguments(parser)
    add_config_argument(parser)
    parser.add_argument('--set', action='append', dest='set_values', default=None, metavar='KEY=VALUE', help=help_for('confwriter.set'))
    parser.add_argument('--get', metavar='KEY', help=help_for('confwriter.get'))
    parser.add_argument('--list', nargs='?', const='', metavar='SUBSTRING', help=help_for('confwriter.list'))
    parser.add_argument('--unset', action='append', dest='unset_keys', default=None, metavar='KEY', help=help_for('confwriter.unset'))
    parser.add_argument('--set-default', action='append', dest='set_default_keys', default=None, metavar='KEY', help=help_for('confwriter.set_default'))
    parser.add_argument('--verify', action='store_true', help=help_for('confwriter.verify'))
    parser.add_argument('--stdout', action='store_true', help=help_for('confwriter.stdout'))
    parser.add_argument('--test', action='store_true', help=help_for('confwriter.test'))

    args = parser.parse_args()

    if args.test:
        if _run_selftests():
            return
        sys.exit(1)

    if not args.conf:
        parser.error('--conf FILE is required')

    has_operation = any(
        value
        for value in (args.set_values, args.get, args.unset_keys, args.set_default_keys, args.verify)
    ) or args.list is not None
    if not has_operation:
        parser.error('at least one operation is required: --set, --get, --list, --unset, or --set-default')

    if args.verify and any((args.set_values, args.unset_keys, args.set_default_keys, args.get, args.list is not None, args.stdout)):
        parser.error('--verify is a standalone read-only operation')

    logger = setup_cli_logging(args, 'akkapros.cli.confwriter')
    is_read_only = not any((args.set_values, args.unset_keys, args.set_default_keys))
    if not is_read_only:
        log_startup_banner(logger, 'akkapros-confwriter', __version__, args)

    try:
        config_path = Path(args.conf)
        if config_path.exists():
            config = load_raw_config_file(config_path)
        else:
            config = build_default_config()
        updated = deepcopy(config)

        if args.set_values:
            for raw in args.set_values:
                path, value = _parse_assignment(raw)
                updated = set_config_value(updated, path, value)
        if args.unset_keys:
            for path in args.unset_keys:
                resolve_config_path(path)
                updated = unset_config_value(updated, path)
        if args.set_default_keys:
            for path in args.set_default_keys:
                resolve_config_path(path)
                updated = set_default_config_value(updated, path)

        mutated = updated != config
        if mutated:
            write_config_file(config_path, updated)

        if args.verify:
            phonetize_config = updated.get(PHONETIZE_SECTION, {})
            result = verify_phonetize_config(phonetize_config)
            sys.stdout.write('\n'.join(render_phonetize_verification_lines(result)) + '\n')
            if result.failures:
                sys.exit(1)
            return

        output_lines: list[str] = []
        if args.list is not None:
            output_lines.extend(_list_lines(args.list))
        if args.get:
            output_lines.append(_format_scalar(get_config_value(updated, args.get)))

        if output_lines:
            sys.stdout.write('\n'.join(output_lines) + '\n')
        if args.stdout and mutated:
            sys.stdout.write(config_path.read_text(encoding='utf-8'))
    except ConfigError as exc:
        logger.error('Invalid config update: %s', exc)
        sys.exit(2)

    if mutated:
        logger.info('Written file: %s', format_path_for_logging(config_path))


if __name__ == '__main__':
    main()
