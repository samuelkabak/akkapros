#!/usr/bin/env python3
"""Create or update package-wide YAML config files for akkapros."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__
from akkapros.lib.config import (
    COMMON_SECTION,
    CONFIG_SCHEMA,
    ConfigError,
    add_config_argument,
    apply_overrides,
    build_default_config,
    config_field_cli_flag,
    load_config_file,
    write_config_file,
)
from akkapros.lib.helpmsg import help_for
from akkapros.lib.utils import (
    RawDefaultsHelpFormatter,
    add_standard_logging_arguments,
    add_standard_version_argument,
    format_path_for_logging,
    log_startup_banner,
    setup_cli_logging,
)


_CONFWRITER_COMMON_FLAG_OVERRIDES = {
    'quiet': '--config-quiet',
    'no_console': '--config-no-console',
    'log': '--config-log',
    'log_append': '--config-log-append',
}


def _confwriter_flag(section: str, key: str) -> str:
    if section == COMMON_SECTION and key in _CONFWRITER_COMMON_FLAG_OVERRIDES:
        return _CONFWRITER_COMMON_FLAG_OVERRIDES[key]
    return config_field_cli_flag(section, key)


def _add_override_arguments(parser: argparse.ArgumentParser) -> dict[str, tuple[str, str]]:
    dest_map: dict[str, tuple[str, str]] = {}
    for section, fields in CONFIG_SCHEMA.items():
        for key, field in fields.items():
            flag = _confwriter_flag(section, key)
            if section == COMMON_SECTION:
                dest = key
            else:
                dest = f"{section}__{key}"
            dest_map[dest] = (section, key)
            if field.kind == "bool":
                parser.add_argument(flag, action='store_true', dest=dest, default=None, help=f"Set {section}.{key} to true")
                parser.add_argument(f"--no-{flag[2:]}", action='store_false', dest=dest, default=None, help=f"Set {section}.{key} to false")
            elif field.kind == "float":
                parser.add_argument(flag, type=float, dest=dest, default=None, help=field.description)
            elif field.kind == "string_list":
                parser.add_argument(flag, action='append', dest=dest, default=None, help=field.description)
            else:
                kwargs: dict[str, object] = {"dest": dest, "default": None, "help": field.description}
                if field.choices is not None:
                    kwargs["choices"] = field.choices
                parser.add_argument(flag, **kwargs)
    return dest_map


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Create or incrementally update package-wide akkapros YAML config files',
        formatter_class=RawDefaultsHelpFormatter,
    )
    add_standard_version_argument(parser, 'akkapros-confwriter')
    add_standard_logging_arguments(parser)
    add_config_argument(parser)
    parser.add_argument('--stdout', action='store_true', help=help_for('confwriter.stdout'))
    parser.add_argument('--test', action='store_true', help=help_for('confwriter.test'))
    dest_map = _add_override_arguments(parser)

    args = parser.parse_args()

    if args.test:
        parser.error('--test is not implemented for confwriter yet')

    if not args.conf:
        parser.error('--conf FILE is required')

    overrides = {
        dest_map[dest]: value
        for dest, value in vars(args).items()
        if dest in dest_map and value is not None
    }
    if not overrides:
        parser.error('at least one override option is required in wave one')

    logger = setup_cli_logging(args, 'akkapros.cli.confwriter')
    log_startup_banner(logger, 'akkapros-confwriter', __version__, args)

    try:
        config_path = Path(args.conf)
        if config_path.exists():
            config = load_config_file(config_path)
        else:
            config = build_default_config()
        updated = apply_overrides(config, overrides)
        write_config_file(config_path, updated)
    except ConfigError as exc:
        logger.error('Invalid config update: %s', exc)
        sys.exit(2)

    logger.info('Written file: %s', format_path_for_logging(config_path))
    if args.stdout:
        sys.stdout.write(config_path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    main()
