#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Phonetizer (CLI wrapper)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__
from akkapros.lib.config import (
    ConfigError,
    add_config_argument,
    add_runtime_interface_arguments,
    build_runtime_default_config,
    get_section_config,
    log_deprecated_config_flag_warnings,
    normalize_runtime_config_path,
    parse_args_with_config,
    parse_config_cli_value,
    render_runtime_help,
    require_effective_prefix,
    set_config_value,
)
from akkapros.lib.frontmatter import (
    build_output_frontmatter,
    compose_text_document,
    effective_options_from_namespace,
    read_text_file,
    resolve_file_title,
)
from akkapros.lib.helpmsg import help_for
from akkapros.lib.phonetize import (
    PHONETIZE_SECTION,
    PROCESS_KEYS,
    render_phonetize_verification_lines,
    realize_phone_streams,
    run_tests as run_phonetize_tests,
    serialize_mbrola_rows,
    serialize_phone_rows,
    verify_phonetize_config,
)
from akkapros.lib.utils import (
    FormatValidationError,
    RawDefaultsHelpFormatter,
    add_standard_logging_arguments,
    add_standard_version_argument,
    format_path_for_logging,
    format_selftest_label,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
    log_startup_banner,
    setup_cli_logging,
    simple_safe_filename,
    validate_intermediate_format,
)


def _apply_path_overrides(phonetize_config: dict[str, object], option_values: list[str] | None) -> dict[str, object]:
    updated = {PHONETIZE_SECTION: phonetize_config}
    for raw in option_values or []:
        path, sep, value = raw.partition('=')
        if not sep or not path.strip():
            raise ConfigError(f"Invalid --option argument: {raw!r}; expected KEY=VALUE")
        updated = set_config_value(updated, normalize_runtime_config_path(path), parse_config_cli_value(value))
    return get_section_config(updated, PHONETIZE_SECTION)


def _apply_process_flag_overrides(args: argparse.Namespace, phonetize_config: dict[str, object]) -> dict[str, object]:
    updated = {PHONETIZE_SECTION: phonetize_config}
    for key in PROCESS_KEYS:
        value = getattr(args, key)
        if value is None:
            continue
        updated = set_config_value(updated, f'phonetize.process.timing_model.{key}', value)
    return get_section_config(updated, PHONETIZE_SECTION)


def run_tests() -> bool:
    logger = get_logger_with_fallback('akkapros.cli.phonetizer')

    class _Args:
        def __init__(self, **kwargs) -> None:
            self.__dict__.update(kwargs)

    defaults = _Args(
        geminate_policy='corrective',
        accentuation_distribution_policy='80_20',
        drift_tolerance=0,
    )
    config = build_runtime_default_config()[PHONETIZE_SECTION]
    updated = _apply_process_flag_overrides(defaults, config)
    cases = [
        ('default process overrides', lambda: updated['process']['timing_model']['geminate_policy'] == 'corrective' and updated['process']['timing_model']['drift_tolerance'] == 0),
        ('timing override path', lambda: _apply_path_overrides(config, ['phonetize.process.timing_model.drift_tolerance=3'])['process']['timing_model']['drift_tolerance'] == 3),
        ('reject bad option path', _selftest_invalid_option_path),
        ('reject removed speech option path', _selftest_removed_speech_option_path),
        ('canonical phone rows', run_phonetize_tests),
    ]
    passed = 0
    total = len(cases)
    for index, (label, callback) in enumerate(cases, start=1):
        ok = bool(callback())
        if ok:
            passed += 1
        log_selftest_result(logger, ok, 'Phonetizer', format_selftest_label(index, total, label))
    log_selftest_summary(logger, 'Phonetizer', passed, total)
    return passed == total


def _selftest_invalid_option_path() -> bool:
    try:
        _apply_path_overrides(build_runtime_default_config()[PHONETIZE_SECTION], ['metrics.wpm=193'])
    except ConfigError:
        return True
    return False


def _selftest_removed_speech_option_path() -> bool:
    try:
        _apply_path_overrides(
            build_runtime_default_config()[PHONETIZE_SECTION],
            ['phonetize.process.timing_model.speech.wpm=193'],
        )
    except ConfigError:
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Build the transitional phonetize-stage _phone artifact from *_tilde.txt',
        formatter_class=RawDefaultsHelpFormatter,
        add_help=False,
    )
    add_standard_version_argument(parser, 'akkapros-phonetizer')
    add_standard_logging_arguments(parser)
    add_config_argument(parser)
    add_runtime_interface_arguments(parser, 'phonetizer')
    parser.add_argument('input', nargs='?', help=help_for('phonetizer.input'))
    parser.add_argument('-p', '--prefix', help=help_for('phonetizer.prefix'))
    parser.add_argument('--outdir', default='.', help=help_for('phonetizer.outdir'))
    parser.add_argument('--geminate-policy', dest='geminate_policy', choices=['corrective', 'cumulative'], default=None, help=help_for('phonetizer.geminate_policy'))
    parser.add_argument('--accentuation-distribution-policy', dest='accentuation_distribution_policy', choices=['100_0', '95_05', '90_10', '85_15', '80_20', '75_25', '70_30'], default=None, help=help_for('phonetizer.accentuation_distribution_policy'))
    parser.add_argument('--drift-tolerance', dest='drift_tolerance', type=int, default=None, help=help_for('phonetizer.drift_tolerance'))
    parser.add_argument('--test', action='store_true', help=help_for('phonetizer.test'))

    try:
        args = parse_args_with_config(parser, 'phonetizer')
    except ConfigError as exc:
        sys.stderr.write(f'Invalid config: {exc}\n')
        sys.exit(2)

    if args.test:
        logger = setup_cli_logging(args, 'akkapros.cli.phonetizer')
        log_startup_banner(logger, 'akkapros-phonetizer', __version__, args)
        log_deprecated_config_flag_warnings(logger, args)
        sys.exit(0 if run_tests() else 1)

    if not args.input:
        sys.stdout.write(render_runtime_help(parser, 'phonetizer'))
        sys.exit(1)

    logger = setup_cli_logging(args, 'akkapros.cli.phonetizer')
    log_startup_banner(logger, 'akkapros-phonetizer', __version__, args)
    log_deprecated_config_flag_warnings(logger, args)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error('File not found: %s', args.input)
        sys.exit(1)

    try:
        validate_intermediate_format(input_path, expected_kind='tilde')
    except FormatValidationError as exc:
        logger.error('Invalid input format: %s', exc)
        sys.exit(2)

    try:
        prefix = require_effective_prefix(args.prefix, 'phonetizer')
    except ConfigError as exc:
        logger.error('%s', exc)
        sys.exit(2)

    phonetize_config = get_section_config(args._effective_grouped_config, PHONETIZE_SECTION)

    verification = verify_phonetize_config(phonetize_config)
    for line in render_phonetize_verification_lines(verification)[1:]:
        if line.startswith('FAIL '):
            logger.error('%s', line)
        else:
            logger.warning('%s', line)
    if verification.failures:
        logger.error('Phonetizer preflight failed before Phase 2 processing continued.')
        sys.exit(2)

    input_frontmatter, tilde_body = read_text_file(input_path)
    (original_rows, original_report), (accentuated_rows, accentuated_report) = realize_phone_streams(
        tilde_body,
        phonetize_config,
        input_frontmatter,
    )
    original_body = serialize_phone_rows(original_rows)
    accentuated_body = serialize_phone_rows(accentuated_rows)
    original_mbrola_body = serialize_mbrola_rows(original_rows, phonetize_config, accentuated=False)
    accentuated_mbrola_body = serialize_mbrola_rows(accentuated_rows, phonetize_config, accentuated=True)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    safe_prefix = simple_safe_filename(prefix)
    original_output_path = outdir / f'{safe_prefix}_ophone.txt'
    accentuated_output_path = outdir / f'{safe_prefix}_phone.txt'
    original_mbrola_output_path = outdir / f'{safe_prefix}_ombrola.pho'
    accentuated_mbrola_output_path = outdir / f'{safe_prefix}_mbrola.pho'
    option_values = effective_options_from_namespace(
        args,
        exclude={'input', 'outdir', 'prefix', 'version', 'test', 'conf'},
    )
    original_frontmatter = build_output_frontmatter(
        output_path=original_output_path,
        step='phonetize',
        title=resolve_file_title(input_frontmatter),
        body=original_body,
        options=option_values,
        input_frontmatter=input_frontmatter,
        stage_data={
            'source_variant': 'original',
            'phone_row_count': len(original_rows),
            'silence_row_count': sum(1 for row in original_rows if row['category'] == 'S'),
            'phoneme_row_count': sum(1 for row in original_rows if row['category'] != 'S'),
            'unit_drift': original_report['unit_drift'],
            'unit_drift_extension_count': original_report['unit_drift_extension_count'],
            'unit_drift_extension_rate': original_report['unit_drift_extension_rate'],
            'max_unit_drift_extension': original_report['max_unit_drift_extension'],
            'syllable_count': original_report['syllable_count'],
            'pause_count': original_report['pause_count'],
            'mini_pause_count': original_report['mini_pause_count'],
            'total_unit_count': original_report['total_unit_count'],
            'non_accented_long_vowel_count': original_report['non_accented_long_vowel_count'],
            'left_as_is_non_accented_long_vowel_count': original_report['left_as_is_non_accented_long_vowel_count'],
            'drift_tolerance_effect': original_report['drift_tolerance_effect'],
            'adjusted_non_accented_long_vowel_count': original_report['adjusted_non_accented_long_vowel_count'],
            'shortened_non_accented_long_vowel_count': original_report['shortened_non_accented_long_vowel_count'],
            'lengthened_non_accented_long_vowel_count': original_report['lengthened_non_accented_long_vowel_count'],
            'inserted_mini_pause_count': original_report['inserted_mini_pause_count'],
            'eligible_mini_pause_count': original_report['eligible_mini_pause_count'],
            'mini_pause_insertion_rate': original_report['mini_pause_insertion_rate'],
            'pause_with_residual_drift_count': original_report['pause_with_residual_drift_count'],
            'pause_with_residual_drift_rate': original_report['pause_with_residual_drift_rate'],
        },
        file_format='phone',
    )
    accentuated_frontmatter = build_output_frontmatter(
        output_path=accentuated_output_path,
        step='phonetize',
        title=resolve_file_title(input_frontmatter),
        body=accentuated_body,
        options=option_values,
        input_frontmatter=input_frontmatter,
        stage_data={
            'source_variant': 'accentuated',
            'phone_row_count': len(accentuated_rows),
            'silence_row_count': sum(1 for row in accentuated_rows if row['category'] == 'S'),
            'phoneme_row_count': sum(1 for row in accentuated_rows if row['category'] != 'S'),
            'unit_drift': accentuated_report['unit_drift'],
            'unit_drift_extension_count': accentuated_report['unit_drift_extension_count'],
            'unit_drift_extension_rate': accentuated_report['unit_drift_extension_rate'],
            'max_unit_drift_extension': accentuated_report['max_unit_drift_extension'],
            'syllable_count': accentuated_report['syllable_count'],
            'pause_count': accentuated_report['pause_count'],
            'mini_pause_count': accentuated_report['mini_pause_count'],
            'total_unit_count': accentuated_report['total_unit_count'],
            'non_accented_long_vowel_count': accentuated_report['non_accented_long_vowel_count'],
            'left_as_is_non_accented_long_vowel_count': accentuated_report['left_as_is_non_accented_long_vowel_count'],
            'drift_tolerance_effect': accentuated_report['drift_tolerance_effect'],
            'adjusted_non_accented_long_vowel_count': accentuated_report['adjusted_non_accented_long_vowel_count'],
            'shortened_non_accented_long_vowel_count': accentuated_report['shortened_non_accented_long_vowel_count'],
            'lengthened_non_accented_long_vowel_count': accentuated_report['lengthened_non_accented_long_vowel_count'],
            'inserted_mini_pause_count': accentuated_report['inserted_mini_pause_count'],
            'eligible_mini_pause_count': accentuated_report['eligible_mini_pause_count'],
            'mini_pause_insertion_rate': accentuated_report['mini_pause_insertion_rate'],
            'pause_with_residual_drift_count': accentuated_report['pause_with_residual_drift_count'],
            'pause_with_residual_drift_rate': accentuated_report['pause_with_residual_drift_rate'],
        },
        file_format='phone',
    )
    original_output_path.write_text(compose_text_document(original_frontmatter, original_body), encoding='utf-8')
    accentuated_output_path.write_text(compose_text_document(accentuated_frontmatter, accentuated_body), encoding='utf-8')
    original_mbrola_output_path.write_text(original_mbrola_body, encoding='utf-8')
    accentuated_mbrola_output_path.write_text(accentuated_mbrola_body, encoding='utf-8')
    logger.info('Written file: %s', format_path_for_logging(original_output_path))
    logger.info('Written file: %s', format_path_for_logging(accentuated_output_path))
    logger.info('Written file: %s', format_path_for_logging(original_mbrola_output_path))
    logger.info('Written file: %s', format_path_for_logging(accentuated_mbrola_output_path))


if __name__ == '__main__':
    main()