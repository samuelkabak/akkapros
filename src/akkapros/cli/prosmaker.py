#!/usr/bin/env python3
"""Akkadian Prosody Toolkit - Prosmaker (CLI wrapper).

This module provides a command-line interface that delegates moraic prosody
realization logic to ``akkapros.lib.prosody``. CLI concerns (arguments,
output prefix, output directory and safe filename handling) stay here.
"""

import sys
import argparse
from pathlib import Path

# If the script is executed directly, the package root may not be on sys.path.
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib.prosody import (
    AccentStyle,
    MoraMode,
    ProsodyEngine,
    run_tests,
    test_diphthong_restoration,
)
from akkapros import __version__
from akkapros.lib.config import ConfigError, add_config_argument, parse_args_with_config, require_effective_prefix
from akkapros.lib.frontmatter import effective_options_from_namespace
from akkapros.lib.helpmsg import help_for
from akkapros.lib.utils import (
    FormatValidationError,
    RawDefaultsHelpFormatter,
    add_standard_logging_arguments,
    add_standard_version_argument,
    log_startup_banner,
    setup_cli_logging,
    simple_safe_filename,
    validate_intermediate_format,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Apply moraic prosody realization to syllabified Akkadian text',
        formatter_class=RawDefaultsHelpFormatter,
    )
    add_standard_version_argument(parser, 'akkapros-prosmaker')
    add_standard_logging_arguments(parser)
    add_config_argument(parser)
    parser.add_argument('input', nargs='?', help=help_for('prosmaker.input'))
    parser.add_argument('-p', '--prefix', help=help_for('prosmaker.prefix'))
    parser.add_argument('--outdir', default='.', help=help_for('prosmaker.outdir'))
    parser.add_argument('--style', choices=['lob', 'sob'], default='lob', help=help_for('prosmaker.style'))
    parser.add_argument('--mora-mode', choices=['bi', 'mono'], default='bi', help=help_for('prosmaker.mora_mode'))
    parser.add_argument('-r', '--relax-last', action='store_true',
                        help=help_for('prosmaker.relax_last'))
    parser.add_argument('--test', action='store_true', help=help_for('prosmaker.test'))
    parser.add_argument('--test-diphthongs', action='store_true', help=help_for('prosmaker.test_diphthongs'))

    try:
        args = parse_args_with_config(parser, 'prosmaker')
    except ConfigError as exc:
        sys.stderr.write(f"Invalid config: {exc}\n")
        sys.exit(2)

    if args.test:
        logger = setup_cli_logging(args, 'akkapros.cli.prosmaker')
        log_startup_banner(logger, 'akkapros-prosmaker', __version__, args)
        success = run_tests()
        sys.exit(0 if success else 1)

    if args.test_diphthongs:
        logger = setup_cli_logging(args, 'akkapros.cli.prosmaker')
        log_startup_banner(logger, 'akkapros-prosmaker', __version__, args)
        success = test_diphthong_restoration()
        sys.exit(0 if success else 1)

    if not args.input:
        parser.print_help()
        sys.exit(0)

    logger = setup_cli_logging(args, 'akkapros.cli.prosmaker')
    log_startup_banner(logger, 'akkapros-prosmaker', __version__, args)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error('File not found: %s', args.input)
        sys.exit(1)

    try:
        validate_intermediate_format(input_path, expected_kind='syl')
    except FormatValidationError as exc:
        logger.error('Invalid input format: %s', exc)
        logger.error('Hint: upstream stage output may be partial/corrupted; re-run syllabifier.')
        sys.exit(2)

    outdir = Path(args.outdir)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        safe_output = simple_safe_filename(require_effective_prefix(args.prefix, 'prosmaker'))
    except ConfigError as exc:
        logger.error('%s', exc)
        sys.exit(2)
    output_file = outdir / f"{safe_output}_tilde.txt"

    style_map = {'lob': AccentStyle.LOB, 'sob': AccentStyle.SOB}
    mora_mode_map = {'bi': MoraMode.BI, 'mono': MoraMode.MONO}
    style = style_map[args.style]

    engine = ProsodyEngine(style=style, only_last=not args.relax_last, mora_mode=mora_mode_map[args.mora_mode])
    engine.process_file(
        str(input_path),
        str(output_file),
        options=effective_options_from_namespace(
            args,
            exclude={'input', 'outdir', 'prefix', 'test', 'test_diphthongs', 'version', 'conf'},
        ),
    )


if __name__ == "__main__":
    main()

