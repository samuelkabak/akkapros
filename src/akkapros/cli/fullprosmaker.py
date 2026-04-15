#!/usr/bin/env python3
"""Akkadian Prosody Toolkit - Full Prosody Pipeline (CLI wrapper)

Runs the complete processing pipeline in one command:
1) syllabify (from *_proc.txt to *_syl.txt)
2) prosody realization (from *_syl.txt to *_tilde.txt)
3) metrics   (from *_ophone.txt + *_phone.txt to selected metrics outputs)
4) print     (from *_ophone.txt + *_phone.txt to selected accent outputs)

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
from akkapros.lib.config import (
    ConfigError,
    add_config_argument,
    add_runtime_interface_arguments,
    log_deprecated_config_flag_warnings,
    normalize_runtime_config_path,
    parse_args_with_config,
    require_effective_prefix,
    render_runtime_help,
)
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
    resolve_inherited_syllabify_options,
    resolve_file_title,
    with_inherited_syllabify_options,
)
from akkapros.lib.helpmsg import help_for
from akkapros.lib.phonetize import (
    PHONETIZE_SECTION,
    PROCESS_KEYS,
    build_default_phonetize_config,
    realize_phone_streams,
    serialize_mbrola_rows,
    serialize_phone_rows,
)
from akkapros.lib.prosody import (
    AccentStyle,
    MoraMode,
    ProsodyEngine,
    run_tests as run_prosody_tests,
    test_diphthong_restoration,
)
from akkapros.lib.metrics import (
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



PHONETIZE_DEFAULT_WPM = 193
PHONETIZE_DEFAULT_PAUSE_RATIO = 35


def _resolve_ipa_options(args: argparse.Namespace) -> tuple[bool, str, bool]:
    """Resolve IPA output flags: enabled, mode, and circumflex hiatus splitting."""
    output_ipa = args.print_ipa
    ipa_mode = 'ipa-strict' if getattr(args, 'print_ipa_proto_semitic', None) == 'preserve' else 'ipa-ob'
    circ_hiatus = args.print_circ_hiatus

    return output_ipa, ipa_mode, circ_hiatus


def _apply_phonetize_process_overrides(args: argparse.Namespace) -> dict[str, object]:
    config = build_default_phonetize_config()
    for key in PROCESS_KEYS:
        value = getattr(args, f'phonetize_{key}')
        if value is not None:
            config['process']['timing_model'][key] = value
    for raw in args.option_values or []:
        path, sep, value = raw.partition('=')
        if not sep or not path.strip():
            raise ConfigError(
                f"Invalid phonetize override {raw!r}; expected KEY=VALUE"
            )
        from akkapros.lib.config import parse_config_cli_value, set_config_value, get_section_config
        updated = set_config_value({PHONETIZE_SECTION: config}, normalize_runtime_config_path(path), parse_config_cli_value(value))
        config = get_section_config(updated, PHONETIZE_SECTION)
    return config


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
    extra_short_punct_chars: str,
    extra_long_punct_chars: str,
    extra_short_punct_patterns: list[str] | None,
    extra_long_punct_patterns: list[str] | None,
    number_format: str,
    style: str,
    mora_mode: str,
    only_last: bool,
    phonetize_config: dict[str, object],
    output_table: bool,
    output_json: bool,
    output_acute: bool,
    output_bold: bool,
    output_ipa: bool,
    output_xar: bool,
    print_merger: bool,
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
    ophone_file = outdir / f"{safe_prefix}_ophone.txt"
    phone_file = outdir / f"{safe_prefix}_phone.txt"
    ombrola_file = outdir / f"{safe_prefix}_ombrola.pho"
    mbrola_file = outdir / f"{safe_prefix}_mbrola.pho"
    metrics_base = outdir / safe_prefix
    acute_file = outdir / f"{safe_prefix}_accent_acute.txt"
    bold_file = outdir / f"{safe_prefix}_accent_bold.md"
    ipa_file = outdir / f"{safe_prefix}_accent_ipa.txt"
    xar_file = outdir / f"{safe_prefix}_accent_xar.txt"
    xar_plain_file = outdir / f"{safe_prefix}_xar.txt"

    # 1) Syllabify using library call
    input_frontmatter, source_text = read_text_file(input_file)

    syllabify.configure_punctuation_rules(
        short_punct_chars=extra_short_punct_chars,
        long_punct_chars=extra_long_punct_chars,
        short_punct_patterns=extra_short_punct_patterns,
        long_punct_patterns=extra_long_punct_patterns,
    )

    syl_text = syllabify.syllabify_text(
        source_text,
        extra_vowels=extra_vowels,
        extra_consonants=extra_consonants,
        merge_hyphen=merge_hyphen,
        preserve_lines=preserve_lines,
        short_punct_chars=extra_short_punct_chars,
        long_punct_chars=extra_long_punct_chars,
        short_punct_patterns=extra_short_punct_patterns,
        long_punct_patterns=extra_long_punct_patterns,
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
    mora_mode_map = {'bi': MoraMode.BI, 'mono': MoraMode.MONO}
    engine = ProsodyEngine(style=style_map[style], only_last=only_last, mora_mode=mora_mode_map[mora_mode])
    engine.process_file(str(syl_file), str(tilde_file), options=options)
    logger.info('Written file: %s', format_path_for_logging(tilde_file))

    # 3) Phonetize transitional artifact
    tilde_frontmatter, tilde_body = read_text_file(tilde_file)
    (ophone_rows, ophone_report), (phone_rows, phone_report) = realize_phone_streams(
        tilde_body,
        phonetize_config,
        tilde_frontmatter,
    )
    ophone_body = serialize_phone_rows(ophone_rows)
    phone_body = serialize_phone_rows(phone_rows)
    ombrola_body = serialize_mbrola_rows(ophone_rows, phonetize_config, accentuated=False)
    mbrola_body = serialize_mbrola_rows(phone_rows, phonetize_config, accentuated=True)
    ophone_frontmatter = build_output_frontmatter(
        output_path=ophone_file,
        step='phonetize',
        title=resolve_file_title(tilde_frontmatter),
        body=ophone_body,
        options=options,
        input_frontmatter=tilde_frontmatter,
        stage_data={
            'source_variant': 'original',
            'phone_row_count': len(ophone_rows),
            'silence_row_count': sum(1 for row in ophone_rows if row['category'] == 'S'),
            'phoneme_row_count': sum(1 for row in ophone_rows if row['category'] != 'S'),
            'drift': ophone_report['drift'],
            'drift_extension_count': ophone_report['drift_extension_count'],
            'max_drift_extension': ophone_report['max_drift_extension'],
        },
        file_format='phone',
    )
    phone_frontmatter = build_output_frontmatter(
        output_path=phone_file,
        step='phonetize',
        title=resolve_file_title(tilde_frontmatter),
        body=phone_body,
        options=options,
        input_frontmatter=tilde_frontmatter,
        stage_data={
            'source_variant': 'accentuated',
            'phone_row_count': len(phone_rows),
            'silence_row_count': sum(1 for row in phone_rows if row['category'] == 'S'),
            'phoneme_row_count': sum(1 for row in phone_rows if row['category'] != 'S'),
            'drift': phone_report['drift'],
            'drift_extension_count': phone_report['drift_extension_count'],
            'max_drift_extension': phone_report['max_drift_extension'],
        },
        file_format='phone',
    )
    with open(ophone_file, 'w', encoding='utf-8') as f:
        f.write(compose_text_document(ophone_frontmatter, ophone_body))
    logger.info('Written file: %s', format_path_for_logging(ophone_file))
    with open(phone_file, 'w', encoding='utf-8') as f:
        f.write(compose_text_document(phone_frontmatter, phone_body))
    logger.info('Written file: %s', format_path_for_logging(phone_file))
    with open(ombrola_file, 'w', encoding='utf-8') as f:
        f.write(ombrola_body)
    logger.info('Written file: %s', format_path_for_logging(ombrola_file))
    with open(mbrola_file, 'w', encoding='utf-8') as f:
        f.write(mbrola_body)
    logger.info('Written file: %s', format_path_for_logging(mbrola_file))

    # 4) Metrics
    inherited_syllabify = resolve_inherited_syllabify_options(tilde_frontmatter)
    configure_pause_punctuation_rules(
        short_punct_chars=inherited_syllabify['extra_short_punct_chars'],
        long_punct_chars=inherited_syllabify['extra_long_punct_chars'],
        short_punct_patterns=inherited_syllabify['extra_short_punct_pattern'],
        long_punct_patterns=inherited_syllabify['extra_long_punct_pattern'],
    )
    update_character_sets(
        inherited_syllabify['extra_consonants'],
        inherited_syllabify['extra_vowels'],
    )
    try:
        metrics_result = process_metrics_file(
            str(phone_file),
            ophone_filename=str(ophone_file),
        )
    except ValueError as exc:
        logger.error('%s', exc)
        return 2
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

    if output_table:
        table_context = {
            'cli': 'fullprosmaker.py',
            'extra_consonants': inherited_syllabify['extra_consonants'],
            'extra_vowels': inherited_syllabify['extra_vowels'],
            'prosody_style': style,
            'prosody_relax_last': not only_last,
            'prosody_restore_diphthongs': True,
            'input': format_path_for_logging(phone_file),
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

    # 5) Printer outputs
    accent_print.process_file(
        input_file=str(phone_file),
        output_acute_file=str(acute_file),
        output_bold_file=str(bold_file),
        ophone_file=str(ophone_file),
        output_ipa_file=str(ipa_file),
        output_xar_file=str(xar_file),
        output_xar_plain_file=str(xar_plain_file),
        write_acute=output_acute,
        write_bold=output_bold,
        write_ipa=output_ipa,
        write_xar=output_xar,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
        print_merger=print_merger,
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
        add_help=False,
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
    add_config_argument(parser)
    add_runtime_interface_arguments(parser, 'fullprosmaker')

    # Input/output (shared)
    parser.add_argument('input', nargs='?', help=help_for('fullprosmaker.input'))
    parser.add_argument('-p', '--prefix', help=help_for('fullprosmaker.prefix'))
    parser.add_argument('--outdir', default='.', help=help_for('fullprosmaker.outdir'))

    # Syllabifier options
    parser.add_argument('--extra-vowels', default='', help=help_for('fullprosmaker.extra_vowels'))
    parser.add_argument('--extra-consonants', default='', help=help_for('fullprosmaker.extra_consonants'))
    parser.add_argument('--extra-short-punct-chars', default='', help=help_for('fullprosmaker.extra_short_punct_chars'))
    parser.add_argument('--extra-long-punct-chars', default='', help=help_for('fullprosmaker.extra_long_punct_chars'))
    parser.add_argument('--extra-short-punct-pattern', action='append', default=[],
                        help=help_for('fullprosmaker.extra_short_punct_pattern'))
    parser.add_argument('--extra-long-punct-pattern', action='append', default=[],
                        help=help_for('fullprosmaker.extra_long_punct_pattern'))
    parser.add_argument('--number-format', default='',
                        help=help_for('fullprosmaker.number_format'))
    parser.add_argument('--syl-merge-hyphens', action='store_true', help=help_for('fullprosmaker.syl_merge_hyphens'))
    parser.add_argument('--syl-merge-lines', action='store_true',
                        help=help_for('fullprosmaker.syl_merge_lines'))
    parser.add_argument('--title', help=help_for('fullprosmaker.title'))

    # Prosmaker options
    parser.add_argument('--prosody-style', dest='prosody_style', choices=['lob', 'sob'], default='lob',
                        help=help_for('fullprosmaker.prosody_style'))
    parser.add_argument('--mora-mode', choices=['bi', 'mono'], default='bi',
                        help=help_for('fullprosmaker.mora_mode'))
    parser.add_argument('--prosody-relax-last', dest='prosody_relax_last', action='store_true',
                        help=help_for('fullprosmaker.prosody_relax_last'))

    # Phonetizer options
    parser.add_argument('--phonetize-geminate-policy', dest='phonetize_geminate_policy', choices=['corrective', 'cumulative'], default=None,
                        help=help_for('fullprosmaker.phonetize_geminate_policy'))
    parser.add_argument('--phonetize-accentuation-distribution-policy', dest='phonetize_accentuation_distribution_policy', choices=['100_0', '85_15', '70_30'], default=None,
                        help=help_for('fullprosmaker.phonetize_accentuation_distribution_policy'))
    parser.add_argument('--phonetize-drift-tolerance', dest='phonetize_drift_tolerance', type=int, default=None,
                        help=help_for('fullprosmaker.phonetize_drift_tolerance'))

    # Metricalc options
    parser.add_argument('--metrics-table', action='store_true', help=help_for('fullprosmaker.metrics_table'))
    parser.add_argument('--metrics-json', action='store_true', help=help_for('fullprosmaker.metrics_json'))

    # Printer options
    parser.add_argument('--print-acute', action='store_true',
                        help=help_for('fullprosmaker.print_acute'))
    parser.add_argument('--print-bold', action='store_true',
                        help=help_for('fullprosmaker.print_bold'))
    parser.add_argument('--print-ipa', action='store_true',
                        help=help_for('fullprosmaker.print_ipa'))
    parser.add_argument('--print-ipa-proto-semitic', choices=['preserve', 'replace'], default='preserve',
                        help=help_for('fullprosmaker.print_ipa_proto_semitic'))
    parser.add_argument('--print-circ-hiatus', action='store_true',
                        help=help_for('fullprosmaker.print_circ_hiatus'))
    parser.add_argument('--print-xar', action='store_true',
                        help=help_for('fullprosmaker.print_xar'))
    parser.add_argument('--print-merger', action='store_true',
                        help=help_for('fullprosmaker.print_merger'))

    # Test controls (covering all grouped sub-components)
    parser.add_argument('--test-syllabify', action='store_true', help=help_for('fullprosmaker.test_syllabify'))
    parser.add_argument('--test-prosody', dest='test_prosody', action='store_true',
                        help=help_for('fullprosmaker.test_prosody'))
    parser.add_argument('--test-diphthongs', action='store_true', help=help_for('fullprosmaker.test_diphthongs'))
    parser.add_argument('--test-metrics', action='store_true', help=help_for('fullprosmaker.test_metrics'))
    parser.add_argument('--test-print', action='store_true', help=help_for('fullprosmaker.test_print'))
    parser.add_argument('--test-cli', action='store_true', help=help_for('fullprosmaker.test_cli'))
    parser.add_argument('--test-all', action='store_true', help=help_for('fullprosmaker.test_all'))

    try:
        args = parse_args_with_config(parser, 'fullprosmaker')
    except ConfigError as exc:
        sys.stderr.write(f"Invalid config: {exc}\n")
        sys.exit(2)

    if args.test_all:
        logger = setup_cli_logging(args, 'akkapros.cli.fullprosmaker')
        log_deprecated_config_flag_warnings(logger, args)
        ok = _run_all_selftests_with_summary(logger)
        sys.exit(0 if ok else 1)

    if args.test_syllabify or args.test_prosody or args.test_diphthongs or args.test_metrics or args.test_print or args.test_cli:
        logger = setup_cli_logging(args, 'akkapros.cli.fullprosmaker')
        log_deprecated_config_flag_warnings(logger, args)
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
        sys.stdout.write(render_runtime_help(parser, 'fullprosmaker'))
        sys.exit(1)

    logger = setup_cli_logging(args, 'akkapros.cli.fullprosmaker')
    log_startup_banner(logger, 'akkapros-fullprosmaker', __version__, args)
    log_deprecated_config_flag_warnings(logger, args)

    try:
        syllabify.configure_punctuation_rules(
            short_punct_chars=args.extra_short_punct_chars,
            long_punct_chars=args.extra_long_punct_chars,
            short_punct_patterns=args.extra_short_punct_pattern,
            long_punct_patterns=args.extra_long_punct_pattern,
        )
    except syllabify.PunctuationConfigError as exc:
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
    try:
        prefix = require_effective_prefix(args.prefix, 'fullprosmaker')
    except ConfigError as exc:
        logger.error('%s', exc)
        sys.exit(2)

    output_table = args.metrics_table
    output_json = args.metrics_json
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

    try:
        phonetize_config = _apply_phonetize_process_overrides(args)
    except ConfigError as exc:
        logger.error('%s', exc)
        sys.exit(2)

    option_values = with_inherited_syllabify_options(
        {
            **effective_options_from_namespace(
                args,
                exclude={'input', 'outdir', 'prefix', 'test_syllabify', 'test_prosody', 'test_diphthongs', 'test_metrics', 'test_print', 'test_cli', 'test_all', 'version', 'conf'},
            ),
            'print_merger': args.print_merger,
        },
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        extra_short_punct_chars=args.extra_short_punct_chars,
        extra_long_punct_chars=args.extra_long_punct_chars,
        extra_short_punct_pattern=args.extra_short_punct_pattern,
        extra_long_punct_pattern=args.extra_long_punct_pattern,
    )

    code = run_pipeline(
        logger=logger,
        input_file=input_path,
        outdir=outdir,
        prefix=prefix,
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        merge_hyphen=args.syl_merge_hyphens,
        preserve_lines=not args.syl_merge_lines,
        extra_short_punct_chars=args.extra_short_punct_chars,
        extra_long_punct_chars=args.extra_long_punct_chars,
        extra_short_punct_patterns=args.extra_short_punct_pattern,
        extra_long_punct_patterns=args.extra_long_punct_pattern,
        number_format=args.number_format,
        style=args.prosody_style,
        mora_mode=args.mora_mode,
        only_last=only_last,
        phonetize_config=phonetize_config,
        output_table=output_table,
        output_json=output_json,
        output_acute=output_acute,
        output_bold=output_bold,
        output_ipa=output_ipa,
        output_xar=output_xar,
        print_merger=args.print_merger,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
        title=args.title,
        options=option_values,
    )
    sys.exit(code)


if __name__ == '__main__':
    main()


