#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Printer (CLI wrapper)

Converts *_tilde text into:
- <prefix>_accent_acute.txt
- <prefix>_accent_bold.md
- <prefix>_accent_ipa.txt
- <prefix>_accent_xar.txt
- <prefix>_xar.txt
"""

import sys
import argparse
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__
from akkapros.lib.config import (
    ConfigError,
    add_config_argument,
    add_runtime_interface_arguments,
    log_deprecated_config_flag_warnings,
    parse_args_with_config,
    render_runtime_help,
    require_effective_prefix,
)
from akkapros.lib.frontmatter import effective_options_from_namespace
from akkapros.lib.helpmsg import help_for
from akkapros.lib import print as accent_print
from akkapros.lib.utils import simple_safe_filename
from akkapros.lib.utils import (
    FormatValidationError,
    RawDefaultsHelpFormatter,
    add_standard_logging_arguments,
    add_standard_version_argument,
    format_selftest_label,
    format_path_for_logging,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
    log_startup_banner,
    setup_cli_logging,
    validate_intermediate_format,
)


def _resolve_ipa_options(args: argparse.Namespace) -> tuple[bool, str, bool]:
    """Resolve IPA output flags: enabled, mode, and circumflex hiatus splitting.

    CLI option renamed: `--ipa-proto-semitic` (values: 'preserve', 'replace').
    Internally this maps to existing IPA modes used by `print.py`.
    """
    write_ipa = args.ipa
    # map new CLI values to existing internal ipa modes
    ipa_mode = 'ipa-strict' if getattr(args, 'ipa_proto_semitic', None) == 'preserve' else 'ipa-ob'
    circ_hiatus = args.circ_hiatus

    return write_ipa, ipa_mode, circ_hiatus


def run_tests() -> bool:
    """Run printer CLI resolution tests and delegated library tests."""
    logger = get_logger_with_fallback(__name__)
    ok = True

    class _Args:
        def __init__(self, ipa: bool, ipa_proto_semitic: str, circ_hiatus: bool) -> None:
            self.ipa = ipa
            self.ipa_proto_semitic = ipa_proto_semitic
            self.circ_hiatus = circ_hiatus

    cases = [
        (_Args(False, 'preserve', False), False, 'ipa-strict', False),
        (_Args(False, 'replace', False), False, 'ipa-ob', False),
        (_Args(True, 'preserve', False), True, 'ipa-strict', False),
        (_Args(True, 'replace', False), True, 'ipa-ob', False),
        (_Args(True, 'replace', True), True, 'ipa-ob', True),
    ]

    passed = 0
    total = len(cases)
    for index, (args, exp_write, exp_mode, exp_circ_hiatus) in enumerate(cases, start=1):
        got_write, got_mode, got_circ_hiatus = _resolve_ipa_options(args)
        if (
            got_write == exp_write
            and got_mode == exp_mode
            and got_circ_hiatus == exp_circ_hiatus
        ):
            passed += 1
            log_selftest_result(
                logger,
                True,
                'Printer',
                format_selftest_label(index, total, 'Cli ipa mode'),
            )
        else:
            ok = False
            log_selftest_result(
                logger,
                False,
                'Printer',
                format_selftest_label(index, total, 'Cli ipa mode'),
                details=[
                    f'ipa={args.ipa}',
                    f'ipa_proto_semitic={args.ipa_proto_semitic!r}',
                    f'circ_hiatus={args.circ_hiatus}',
                    f'expected_write_ipa={exp_write}',
                    f'expected_ipa_mode={exp_mode!r}',
                    f'expected_circ_hiatus={exp_circ_hiatus}',
                    f'got_write_ipa={got_write}',
                    f'got_ipa_mode={got_mode!r}',
                    f'got_circ_hiatus={got_circ_hiatus}',
                ],
            )

    log_selftest_summary(logger, 'Printer', passed, total)
    ok = accent_print.run_tests() and ok
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Convert *_tilde text into accent-acute, accent-bold, accent-ipa and accent-xar reading outputs',
        formatter_class=RawDefaultsHelpFormatter,
        add_help=False,
    )
    add_standard_version_argument(parser, 'akkapros-printer')
    add_standard_logging_arguments(parser)
    add_config_argument(parser)
    add_runtime_interface_arguments(parser, 'printer')
    parser.add_argument('input', nargs='?', help=help_for('printer.input'))
    parser.add_argument('-p', '--prefix', help=help_for('printer.prefix'))
    parser.add_argument('--outdir', default='.', help=help_for('printer.outdir'))

    parser.add_argument('--acute', action='store_true',
                        help=help_for('printer.acute'))
    parser.add_argument('--bold', action='store_true',
                        help=help_for('printer.bold'))
    parser.add_argument('--ipa', action='store_true',
                        help=help_for('printer.ipa'))
    parser.add_argument('--ipa-proto-semitic', choices=['preserve', 'replace'], default='preserve',
                        help=help_for('printer.ipa_proto_semitic'))
    parser.add_argument('--circ-hiatus', action='store_true',
                        help=help_for('printer.circ_hiatus'))
    parser.add_argument('--xar', action='store_true',
                        help=help_for('printer.xar'))
    parser.add_argument('--print-merger', action='store_true',
                        help=help_for('printer.print_merger'))
    parser.add_argument('--test', action='store_true', help=help_for('printer.test'))

    try:
        args = parse_args_with_config(parser, 'printer')
    except ConfigError as exc:
        sys.stderr.write(f"Invalid config: {exc}\n")
        sys.exit(2)

    if args.test:
        logger = setup_cli_logging(args, 'akkapros.cli.printer')
        log_startup_banner(logger, 'akkapros-printer', __version__, args)
        log_deprecated_config_flag_warnings(logger, args)
        ok = run_tests()
        sys.exit(0 if ok else 1)

    if not args.input:
        sys.stdout.write(render_runtime_help(parser, 'printer'))
        sys.exit(1)

    logger = setup_cli_logging(args, 'akkapros.cli.printer')
    log_startup_banner(logger, 'akkapros-printer', __version__, args)
    log_deprecated_config_flag_warnings(logger, args)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error('File not found: %s', args.input)
        sys.exit(1)

    try:
        validate_intermediate_format(input_path, expected_kind='tilde')
    except FormatValidationError as exc:
        logger.error('Invalid input format: %s', exc)
        logger.error('Hint: expected prosody-realized *_tilde.txt content; re-run prosmaker if needed.')
        sys.exit(2)

    outdir = Path(args.outdir)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    try:
        prefix = simple_safe_filename(require_effective_prefix(args.prefix, 'printer'))
    except ConfigError as exc:
        logger.error('%s', exc)
        sys.exit(2)

    write_acute = args.acute
    write_bold = args.bold
    write_ipa, ipa_mode, circ_hiatus = _resolve_ipa_options(args)
    write_xar = args.xar

    if not (write_acute or write_bold or write_ipa or write_xar):
        write_acute = True
        write_bold = True

    acute_out = outdir / f"{prefix}_accent_acute.txt"
    bold_out = outdir / f"{prefix}_accent_bold.md"
    ipa_out = outdir / f"{prefix}_accent_ipa.txt"
    xar_out = outdir / f"{prefix}_accent_xar.txt"
    xar_plain_out = outdir / f"{prefix}_xar.txt"

    accent_print.process_file(
        input_file=str(input_path),
        output_acute_file=str(acute_out),
        output_bold_file=str(bold_out),
        output_ipa_file=str(ipa_out),
        output_xar_file=str(xar_out),
        output_xar_plain_file=str(xar_plain_out),
        write_acute=write_acute,
        write_bold=write_bold,
        write_ipa=write_ipa,
        write_xar=write_xar,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
        print_merger=args.print_merger,
        options={
            **effective_options_from_namespace(
                args,
                exclude={'input', 'outdir', 'prefix', 'test', 'version', 'conf'},
            ),
            'print_merger': args.print_merger,
        },
    )

    if write_acute:
        logger.info('Written file: %s', format_path_for_logging(acute_out))
    if write_bold:
        logger.info('Written file: %s', format_path_for_logging(bold_out))
    if write_ipa:
        logger.info('Written file: %s', format_path_for_logging(ipa_out))
    if write_xar:
        logger.info('Written file: %s', format_path_for_logging(xar_out))
        logger.info('Written file: %s', format_path_for_logging(xar_plain_out))


if __name__ == '__main__':
    main()
