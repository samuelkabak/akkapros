#!/usr/bin/env python3
"""Akkadian Prosody Toolkit - Full Prosody Pipeline (CLI wrapper)

Runs the complete processing pipeline in one command:
1) syllabify (from *_proc.txt to *_syl.txt)
2) prosody realization (from *_syl.txt to *_tilde.txt)
3) metrics   (from *_tilde.txt to selected metrics outputs)
4) print     (from *_tilde.txt to selected accent outputs)

The CLI deduplicates shared options across stages (for example, --prefix,
--outdir, --extra-vowels, --extra-consonants).
"""

import sys
import json
import argparse
import logging
from copy import deepcopy
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib import syllabify
from akkapros import __version__
from akkapros.lib.frontmatter import (
    build_output_frontmatter,
    build_syllabify_stage_data,
    count_function_words,
    count_lines,
    count_prosodic_units,
    count_syllables_from_marked_text,
    compose_text_document,
    effective_options_from_namespace,
    extract_lexical_words,
    read_text_file,
    resolve_file_title,
)
from akkapros.lib.prosody import (
    AccentStyle,
    ProsodyEngine,
    run_tests as run_prosody_tests,
    test_diphthong_restoration,
)
from akkapros.lib.metrics import (
    METRICS_CSV_DEPRECATION_MESSAGE,
    PunctuationConfigError as MetricsPunctuationConfigError,
    configure_pause_punctuation_rules,
    update_character_sets,
    process_file as process_metrics_file,
    format_table,
    run_tests as run_metrics_tests,
)
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
    """Resolve IPA output flags: enabled, mode, and circumflex hiatus splitting."""
    output_ipa = args.print_ipa
    ipa_mode = 'ipa-strict' if getattr(args, 'print_ipa_proto_semitic', None) == 'preserve' else 'ipa-ob'
    circ_hiatus = args.print_circ_hiatus

    return output_ipa, ipa_mode, circ_hiatus


class _AggregateSelftestCounter(logging.Handler):
    """Count structured self-test records so --test-all can emit one final summary."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.passed = 0
        self.total = 0

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if not message.startswith('Test: '):
            return
        if '] Summary ' in message:
            return
        if 'Test: PASS [' in message:
            self.passed += 1
            self.total += 1
            return
        if 'Test: FAIL [' in message:
            self.total += 1


def _run_all_selftests_with_summary(logger: logging.Logger) -> bool:
    counter = _AggregateSelftestCounter()
    aggregate_logger = logging.getLogger('akkapros')
    aggregate_logger.addHandler(counter)
    try:
        ok = True
        ok = syllabify.run_tests() and ok
        ok = run_prosody_tests() and ok
        ok = test_diphthong_restoration() and ok
        ok = run_metrics_tests() and ok
        ok = accent_print.run_tests() and ok
        ok = run_tests() and ok
    finally:
        aggregate_logger.removeHandler(counter)

    log_selftest_summary(logger, 'All', counter.passed, counter.total)
    return ok and counter.passed == counter.total


def run_tests() -> bool:
    """Run fullprosmaker CLI resolution tests only (no pipeline execution)."""
    logger = get_logger_with_fallback('akkapros.cli.fullprosmaker')
    class _Args:
        def __init__(self, print_ipa: bool, print_ipa_proto_semitic: str, print_circ_hiatus: bool) -> None:
            self.print_ipa = print_ipa
            self.print_ipa_proto_semitic = print_ipa_proto_semitic
            self.print_circ_hiatus = print_circ_hiatus

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
                'Full pipeline',
                format_selftest_label(index, total, 'Cli ipa mode'),
            )
        else:
            log_selftest_result(
                logger,
                False,
                'Full pipeline',
                format_selftest_label(index, total, 'Cli ipa mode'),
                details=[
                    f'print_ipa={args.print_ipa}',
                    f'print_ipa_proto_semitic={args.print_ipa_proto_semitic!r}',
                    f'print_circ_hiatus={args.print_circ_hiatus}',
                    f'expected_output_ipa={exp_write}',
                    f'expected_ipa_mode={exp_mode!r}',
                    f'expected_print_circ_hiatus={exp_circ_hiatus}',
                    f'got_output_ipa={got_write}',
                    f'got_ipa_mode={got_mode!r}',
                    f'got_print_circ_hiatus={got_circ_hiatus}',
                ],
            )

    log_selftest_summary(logger, 'Full pipeline', passed, total)
    return passed == total


def run_pipeline(
    logger,
    input_file: Path,
    outdir: Path,
    prefix: str,
    extra_vowels: str,
    extra_consonants: str,
    merge_hyphen: bool,
    preserve_lines: bool,
    short_punct_chars: str,
    long_punct_chars: str,
    short_punct_patterns: list[str] | None,
    long_punct_patterns: list[str] | None,
    number_format: str,
    style: str,
    only_last: bool,
    wpm: float,
    pause_ratio: float,
    long_punct_weight: float,
    explicit_link_count: str | None,
    output_table: bool,
    output_json: bool,
    output_csv: bool,
    output_acute: bool,
    output_bold: bool,
    output_ipa: bool,
    output_xar: bool,
    ipa_mode: str = 'ipa-ob',
    circ_hiatus: bool = False,
    title: str | None = None,
    options: dict[str, object] | None = None,
) -> int:
    """Execute syllabify -> prosody realization -> metrics -> print and write all outputs."""
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    safe_prefix = simple_safe_filename(prefix)
    syl_file = outdir / f"{safe_prefix}_syl.txt"
    tilde_file = outdir / f"{safe_prefix}_tilde.txt"
    metrics_base = outdir / safe_prefix
    acute_file = outdir / f"{safe_prefix}_accent_acute.txt"
    bold_file = outdir / f"{safe_prefix}_accent_bold.md"
    ipa_file = outdir / f"{safe_prefix}_accent_ipa.txt"
    xar_file = outdir / f"{safe_prefix}_accent_xar.txt"
    xar_plain_file = outdir / f"{safe_prefix}_xar.txt"

    # 1) Syllabify using library call
    input_frontmatter, source_text = read_text_file(input_file)

    syllabify.configure_punctuation_rules(
        short_punct_chars=short_punct_chars,
        long_punct_chars=long_punct_chars,
        short_punct_patterns=short_punct_patterns,
        long_punct_patterns=long_punct_patterns,
    )

    syl_text = syllabify.syllabify_text(
        source_text,
        extra_vowels=extra_vowels,
        extra_consonants=extra_consonants,
        merge_hyphen=merge_hyphen,
        preserve_lines=preserve_lines,
        short_punct_chars=short_punct_chars,
        long_punct_chars=long_punct_chars,
        short_punct_patterns=short_punct_patterns,
        long_punct_patterns=long_punct_patterns,
    )
    syl_body = syl_text if syl_text.endswith('\n') else syl_text + '\n'
    logger.info('Computed line_count: %d', count_lines(syl_body))
    logger.info('Computed word_count: %d', len(extract_lexical_words(syl_body)))
    logger.info('Computed syllable_count: %d', count_syllables_from_marked_text(syl_body))
    syl_frontmatter = build_output_frontmatter(
        output_path=syl_file,
        step='syllabify',
        title=resolve_file_title(input_frontmatter, override_title=title),
        body=syl_body,
        options=options,
        stage_data=build_syllabify_stage_data(source_text, syl_body, input_frontmatter=input_frontmatter),
        input_frontmatter=input_frontmatter,
        file_format='syl',
    )
    with open(syl_file, 'w', encoding='utf-8') as f:
        f.write(compose_text_document(syl_frontmatter, syl_body))
    logger.info('Written file: %s', format_path_for_logging(syl_file))

    # 2) Prosody realization using library engine
    style_map = {'lob': AccentStyle.LOB, 'sob': AccentStyle.SOB}
    engine = ProsodyEngine(style=style_map[style], only_last=only_last)
    engine.process_file(str(syl_file), str(tilde_file), options=options)
    logger.info('Written file: %s', format_path_for_logging(tilde_file))

    # 3) Metrics
    configure_pause_punctuation_rules(
        short_punct_chars=short_punct_chars,
        long_punct_chars=long_punct_chars,
        short_punct_patterns=short_punct_patterns,
        long_punct_patterns=long_punct_patterns,
    )
    update_character_sets(extra_consonants, extra_vowels)
    try:
        metrics_result = process_metrics_file(
            str(tilde_file),
            wpm,
            pause_ratio,
            long_punct_weight,
            explicit_link_count_override=explicit_link_count,
        )
    except ValueError as exc:
        logger.error('%s', exc)
        return 2
    tilde_frontmatter, tilde_body = read_text_file(tilde_file)
    logger.info('Computed line_count: %d', count_lines(tilde_body))
    logger.info('Computed word_count: %d', len(extract_lexical_words(tilde_body)))
    logger.info('Computed syllable_count: %d', count_syllables_from_marked_text(tilde_body))
    logger.info('Computed function_word_count: %d', count_function_words(tilde_body))
    logger.info('Computed prosodic_unit_count: %d', count_prosodic_units(tilde_body))
    logger.info('Computed accentuated_syllable_count: %d', int(metrics_result['accentuation_stats']['accentuated_syllables']))

    if output_json:
        json_file = metrics_base.with_suffix('.json')
        pruned = deepcopy(metrics_result)
        try:
            pruned.get('original', {}).get('acoustic', {}).pop('distances', None)
        except Exception:
            pass
        try:
            pruned.get('accentuated', {}).get('acoustic', {}).pop('distances', None)
        except Exception:
            pass
        pruned['frontmatter'] = build_output_frontmatter(
            output_path=json_file,
            step='metrics',
            title=resolve_file_title(tilde_frontmatter),
            body=json.dumps(pruned, ensure_ascii=False, sort_keys=True),
            options=options,
            input_frontmatter=tilde_frontmatter,
            file_format='metrics',
            include_metadata_data=False,
        )
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(pruned, f, indent=2, ensure_ascii=False)
            f.write('\n')
        logger.info('Written file: %s', format_path_for_logging(json_file))

    if output_csv:
        logger.warning('%s', METRICS_CSV_DEPRECATION_MESSAGE)

    if output_table:
        table_context = {
            'cli': 'fullprosmaker.py',
            'wpm_words_per_min': wpm,
            'pause_ratio_percent': pause_ratio,
            'short_pause_punct_weight_unitless': 1.0,
            'long_pause_punct_weight_unitless': long_punct_weight,
            'extra_consonants': extra_consonants,
            'extra_vowels': extra_vowels,
            'prosody_style': style,
            'prosody_relax_last': not only_last,
            'prosody_restore_diphthongs': True,
            'input': format_path_for_logging(tilde_file),
        }
        table = format_table(metrics_result, run_context=table_context)
        table_file = metrics_base.with_name(metrics_base.name + '_metrics.txt')
        table_frontmatter = build_output_frontmatter(
            output_path=table_file,
            step='metrics',
            title=resolve_file_title(tilde_frontmatter),
            body=table,
            options=options,
            input_frontmatter=tilde_frontmatter,
            file_format='metrics',
            include_metadata_data=False,
        )
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(compose_text_document(table_frontmatter, table))
        logger.info('Written file: %s', format_path_for_logging(table_file))

    # 4) Printer outputs
    accent_print.process_file(
        input_file=str(tilde_file),
        output_acute_file=str(acute_file),
        output_bold_file=str(bold_file),
        output_ipa_file=str(ipa_file),
        output_xar_file=str(xar_file),
        output_xar_plain_file=str(xar_plain_file),
        write_acute=output_acute,
        write_bold=output_bold,
        write_ipa=output_ipa,
        write_xar=output_xar,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
        options=options,
    )

    if output_acute:
        logger.info('Written file: %s', format_path_for_logging(acute_file))
    if output_bold:
        logger.info('Written file: %s', format_path_for_logging(bold_file))
    if output_ipa:
        logger.info('Written file: %s', format_path_for_logging(ipa_file))
    if output_xar:
        logger.info('Written file: %s', format_path_for_logging(xar_file))
        logger.info('Written file: %s', format_path_for_logging(xar_plain_file))

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run full Akkadian pipeline: syllabify -> prosody realization -> metrics',
        formatter_class=RawDefaultsHelpFormatter,
        epilog=f"""
EXAMPLES:
    python fullprosmaker.py outputs/erra_proc.txt -p erra --outdir outputs --prosody-style lob --metrics-table
    python fullprosmaker.py outputs/erra_proc.txt -p erra --metrics-json
    python fullprosmaker.py outputs/erra_proc.txt -p erra --print-acute --print-bold --print-ipa --print-xar
    python fullprosmaker.py --test-all

Version: {__version__}
"""
    )
    add_standard_version_argument(parser, 'akkapros-fullprosmaker')
    add_standard_logging_arguments(parser)

    # Input/output (shared)
    parser.add_argument('input', nargs='?', help='Input Akkadian file (typically *_proc.txt)')
    parser.add_argument('-p', '--prefix', help='Shared output prefix for all generated files')
    parser.add_argument('--outdir', default='.', help='Shared output directory')

    # Syllabifier options
    parser.add_argument('--extra-vowels', default='', help='Extra characters to treat as vowels')
    parser.add_argument('--extra-consonants', default='', help='Extra characters to treat as consonants')
    parser.add_argument('--short-punct-chars', default='', help='Additional short-pause punctuation characters')
    parser.add_argument('--long-punct-chars', default='', help='Additional long-pause punctuation characters')
    parser.add_argument('--short-punct-pattern', action='append', default=[],
                        help='Repeatable regex for short-pause punctuation segments')
    parser.add_argument('--long-punct-pattern', action='append', default=[],
                        help='Repeatable regex for long-pause punctuation segments')
    parser.add_argument('--number-format', default='',
                        help='Number regex for syllabifier stage; empty uses built-in English-grouping-compatible pattern')
    parser.add_argument('--syl-merge-hyphens', action='store_true', help='Merge hyphens into syllable separators in syllabification')
    parser.add_argument('--syl-merge-lines', action='store_true',
                        help='Merge lines (1 newline=space, 2+ to paragraph break). Default preserves original lines')
    parser.add_argument('--title', help='Override inherited or missing file.title for syllabifier output front matter')

    # Prosmaker options
    parser.add_argument('--prosody-style', dest='prosody_style', choices=['lob', 'sob'], default='lob',
                        help='Prosody realization accent style')
    parser.add_argument('--prosody-relax-last', dest='prosody_relax_last', action='store_true',
                        help='For explicit + links, allow prosody realization propagation before the last linked word')

    # Metricalc options
    parser.add_argument('--metrics-csv', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--metrics-table', action='store_true', help='Write human-readable metrics table output')
    parser.add_argument('--metrics-json', action='store_true', help='Write JSON metrics output')
    parser.add_argument('--metrics-wpm', type=float, default=165, help='Words per minute [words/min] for speech-rate estimation')
    parser.add_argument('--metrics-pause-ratio', type=float, default=35, help='Pause ratio [percent of total time]')
    parser.add_argument('--metrics-long-punct-weight', type=float, default=2.0,
                        help='Long pause punctuation weight relative to short pause punctuation [unitless]')
    parser.add_argument('--explicit-link-count',
                        help='Override inherited metadata.data.prosody.explicit_word_link_count for metrics')

    # Printer options
    parser.add_argument('--print-acute', action='store_true',
                        help='Write <prefix>_accent_acute.txt')
    parser.add_argument('--print-bold', action='store_true',
                        help='Write <prefix>_accent_bold.md')
    parser.add_argument('--print-ipa', action='store_true',
                        help='Write <prefix>_accent_ipa.txt')
    parser.add_argument('--print-ipa-proto-semitic', choices=['preserve', 'replace'], default='preserve',
                        help='IPA proto-Semitic policy: preserve=Old Akkadian, replace=Old Babylonian merger')
    parser.add_argument('--print-circ-hiatus', action='store_true',
                        help='Speculative IPA mode: split circumflex vowels into hiatus (e.g., qu -> qu.u)')
    parser.add_argument('--print-xar', action='store_true',
                        help='Write both <prefix>_accent_xar.txt and <prefix>_xar.txt')

    # Test controls (covering all grouped sub-components)
    parser.add_argument('--test-syllabify', action='store_true', help='Run syllabify library tests')
    parser.add_argument('--test-prosody', dest='test_prosody', action='store_true',
                        help='Run prosody realization library tests')
    parser.add_argument('--test-diphthongs', action='store_true', help='Run diphthong restoration tests')
    parser.add_argument('--test-metrics', action='store_true', help='Run metrics library tests')
    parser.add_argument('--test-print', action='store_true', help='Run print library tests')
    parser.add_argument('--test-cli', action='store_true', help='Run fullprosmaker CLI option-resolution tests')
    parser.add_argument('--test-all', action='store_true', help='Run tests for syllabify, prosody realization, diphthongs, metrics and print')

    args = parser.parse_args()

    if args.test_all:
        logger = setup_cli_logging(args, 'akkapros.cli.fullprosmaker')
        log_startup_banner(logger, 'akkapros-fullprosmaker', __version__, args)
        ok = _run_all_selftests_with_summary(logger)
        sys.exit(0 if ok else 1)

    if args.test_syllabify or args.test_prosody or args.test_diphthongs or args.test_metrics or args.test_print or args.test_cli:
        logger = setup_cli_logging(args, 'akkapros.cli.fullprosmaker')
        log_startup_banner(logger, 'akkapros-fullprosmaker', __version__, args)
        ok = True
        if args.test_syllabify:
            ok = syllabify.run_tests() and ok
        if args.test_prosody:
            ok = run_prosody_tests() and ok
        if args.test_diphthongs:
            ok = test_diphthong_restoration() and ok
        if args.test_metrics:
            ok = run_metrics_tests() and ok
        if args.test_print:
            ok = accent_print.run_tests() and ok
        if args.test_cli:
            ok = run_tests() and ok
        sys.exit(0 if ok else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    logger = setup_cli_logging(args, 'akkapros.cli.fullprosmaker')
    log_startup_banner(logger, 'akkapros-fullprosmaker', __version__, args)

    try:
        syllabify.configure_punctuation_rules(
            short_punct_chars=args.short_punct_chars,
            long_punct_chars=args.long_punct_chars,
            short_punct_patterns=args.short_punct_pattern,
            long_punct_patterns=args.long_punct_pattern,
        )
        configure_pause_punctuation_rules(
            short_punct_chars=args.short_punct_chars,
            long_punct_chars=args.long_punct_chars,
            short_punct_patterns=args.short_punct_pattern,
            long_punct_patterns=args.long_punct_pattern,
        )
    except (syllabify.PunctuationConfigError, MetricsPunctuationConfigError) as exc:
        logger.error('Invalid punctuation regex/options: %s', exc)
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error('File not found: %s', args.input)
        sys.exit(1)

    try:
        validate_intermediate_format(input_path, expected_kind='proc')
    except FormatValidationError as exc:
        logger.error('Invalid input format: %s', exc)
        logger.error('Hint: expected cleaned *_proc.txt input from atfparser; fullprosmaker does not accept raw .atf.')
        sys.exit(2)

    outdir = Path(args.outdir)
    prefix = args.prefix if args.prefix else input_path.stem.replace('_proc', '')

    output_table = args.metrics_table
    output_json = args.metrics_json
    output_csv = args.metrics_csv
    output_acute = args.print_acute
    output_bold = args.print_bold
    output_ipa, ipa_mode, circ_hiatus = _resolve_ipa_options(args)
    output_xar = args.print_xar

    # Match metricalc behavior: default to table if no explicit format selected.
    if not (output_table or output_json):
        output_table = True

    # Match printer behavior: default to acute + bold if no explicit format selected.
    if not (output_acute or output_bold or output_ipa or output_xar):
        output_acute = True
        output_bold = True

    only_last = not args.prosody_relax_last

    code = run_pipeline(
        logger=logger,
        input_file=input_path,
        outdir=outdir,
        prefix=prefix,
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        merge_hyphen=args.syl_merge_hyphens,
        preserve_lines=not args.syl_merge_lines,
        short_punct_chars=args.short_punct_chars,
        long_punct_chars=args.long_punct_chars,
        short_punct_patterns=args.short_punct_pattern,
        long_punct_patterns=args.long_punct_pattern,
        number_format=args.number_format,
        style=args.prosody_style,
        only_last=only_last,
        wpm=args.metrics_wpm,
        pause_ratio=args.metrics_pause_ratio,
        long_punct_weight=args.metrics_long_punct_weight,
        explicit_link_count=args.explicit_link_count,
        output_table=output_table,
        output_json=output_json,
        output_csv=output_csv,
        output_acute=output_acute,
        output_bold=output_bold,
        output_ipa=output_ipa,
        output_xar=output_xar,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
        title=args.title,
        options=effective_options_from_namespace(
            args,
            exclude={'input', 'outdir', 'prefix', 'test_syllabify', 'test_prosody', 'test_diphthongs', 'test_metrics', 'test_print', 'test_cli', 'test_all', 'version', 'metrics_csv'},
        ),
    )
    sys.exit(code)


if __name__ == '__main__':
    main()


