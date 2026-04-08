#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Metrics Calculator (CLI wrapper)

This module provides the command-line interface and delegates all
metrics computation to ``akkapros.lib.metrics``.
"""

import sys
import json
from copy import deepcopy
import argparse
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__
from akkapros.lib.config import ConfigError, add_config_argument, parse_args_with_config, require_effective_prefix
from akkapros.lib.frontmatter import (
    build_output_frontmatter,
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
)
from akkapros.lib.helpmsg import help_for
from akkapros.lib.metrics import (
    METRICS_CSV_DEPRECATION_MESSAGE,
    PunctuationConfigError,
    configure_pause_punctuation_rules,
    update_character_sets,
    process_file,
    format_table,
    run_tests,
)
from akkapros.lib.utils import (
    FormatValidationError,
    RawDefaultsHelpFormatter,
    add_standard_logging_arguments,
    add_standard_version_argument,
    format_path_for_logging,
    log_startup_banner,
    setup_cli_logging,
    simple_safe_filename,
    validate_intermediate_format,
)


PHONETIZE_DEFAULT_WPM = 193
PHONETIZE_DEFAULT_PAUSE_RATIO = 35


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Compute metrics for Akkadian text',
        formatter_class=RawDefaultsHelpFormatter,
        epilog=f"""
EXAMPLES:
    python metricalc.py erra_tilde.txt --table
    python metricalc.py --test

Version {__version__}
"""
    )
    add_standard_version_argument(parser, 'akkapros-metricalc')
    add_standard_logging_arguments(parser)
    add_config_argument(parser)
    parser.add_argument('input', nargs='?', help=help_for('metricalc.input'))
    parser.add_argument('--input-list', help=help_for('metricalc.input_list'))
    parser.add_argument('-p', '--prefix', help=help_for('metricalc.prefix'))
    parser.add_argument('--outdir', default='.', help=help_for('metricalc.outdir'))
    parser.add_argument('--csv', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--table', action='store_true', help=help_for('metricalc.table'))
    parser.add_argument('--json', action='store_true', help=help_for('metricalc.json'))
    parser.add_argument('--explicit-link-count',
                        help=help_for('metricalc.explicit_link_count'))
    parser.add_argument('--test', action='store_true', help=help_for('metricalc.test'))

    try:
        args = parse_args_with_config(parser, 'metricalc')
    except ConfigError as exc:
        sys.stderr.write(f"Invalid config: {exc}\n")
        sys.exit(2)

    if args.test:
        logger = setup_cli_logging(args, 'akkapros.cli.metricalc')
        log_startup_banner(logger, 'akkapros-metrics', __version__, args)
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.input and not args.input_list:
        parser.print_help()
        sys.exit(1)

    logger = setup_cli_logging(args, 'akkapros.cli.metricalc')
    log_startup_banner(logger, 'akkapros-metrics', __version__, args)

    if not (args.table or args.json):
        args.table = True

    input_files = []
    if args.input_list:
        with open(args.input_list, 'r', encoding='utf-8') as f:
            input_files = [line.strip() for line in f if line.strip()]
    elif args.input:
        input_files = [args.input]

    for input_file in input_files:
        if not Path(input_file).exists():
            logger.error('File not found: %s', input_file)
            sys.exit(1)

    for input_file in input_files:
        try:
            validate_intermediate_format(input_file, expected_kind='tilde')
        except FormatValidationError as exc:
            logger.error('Invalid input format: %s', exc)
            logger.error('Hint: upstream stage output may be partial/corrupted; re-run prosmaker.')
            sys.exit(2)

    option_values = effective_options_from_namespace(
        args,
        exclude={'input', 'input_list', 'outdir', 'prefix', 'test', 'version', 'csv', 'conf'},
    )

    results = []
    inherited_syllabify_options = []
    for input_file in input_files:
        input_frontmatter, tilde_body = read_text_file(input_file)
        inherited_syllabify = resolve_inherited_syllabify_options(input_frontmatter)
        try:
            configure_pause_punctuation_rules(
                short_punct_chars=inherited_syllabify['extra_short_punct_chars'],
                long_punct_chars=inherited_syllabify['extra_long_punct_chars'],
                short_punct_patterns=inherited_syllabify['extra_short_punct_pattern'],
                long_punct_patterns=inherited_syllabify['extra_long_punct_pattern'],
            )
        except PunctuationConfigError as exc:
            logger.error('Invalid inherited punctuation regex/options: %s', exc)
            sys.exit(2)
        update_character_sets(
            inherited_syllabify['extra_consonants'],
            inherited_syllabify['extra_vowels'],
        )
        try:
            result = process_file(
                input_file,
                PHONETIZE_DEFAULT_WPM,
                PHONETIZE_DEFAULT_PAUSE_RATIO,
                explicit_link_count_override=args.explicit_link_count,
            )
        except ValueError as exc:
            logger.error('%s', exc)
            sys.exit(2)
        logger.info('Computed line_count: %d', count_lines(tilde_body))
        logger.info('Computed word_count: %d', len(extract_lexical_words(tilde_body)))
        logger.info('Computed syllable_count: %d', count_syllables_from_marked_text(tilde_body))
        logger.info('Computed function_word_count: %d', count_function_words(tilde_body))
        logger.info('Computed prosodic_unit_count: %d', count_prosodic_units(tilde_body))
        logger.info('Computed accentuated_syllable_count: %d', int(result['accentuation_stats']['accentuated_syllables']))
        results.append(result)
        inherited_syllabify_options.append(inherited_syllabify)

    if args.outdir != '.':
        Path(args.outdir).mkdir(parents=True, exist_ok=True)

    try:
        safe_output = simple_safe_filename(require_effective_prefix(args.prefix, 'metricalc'))
    except ConfigError as exc:
        logger.error('%s', exc)
        sys.exit(2)
    base = Path(args.outdir) / safe_output

    if args.json:
        json_file = base.with_name(base.name + '_metrics.json')
        pruned = deepcopy(results[0] if len(results) == 1 else results)
        def _prune_res(obj):
            try:
                if isinstance(obj, dict):
                    orig = obj.get('original')
                    rep = obj.get('accentuated')
                    if isinstance(orig, dict):
                        orig.get('acoustic', {}).pop('distances', None)
                    if isinstance(rep, dict):
                        rep.get('acoustic', {}).pop('distances', None)
            except Exception:
                pass

        if isinstance(pruned, list):
            for r in pruned:
                _prune_res(r)
        else:
            _prune_res(pruned)

        if len(input_files) == 1 and isinstance(pruned, dict):
            input_frontmatter, tilde_body = read_text_file(input_files[0])
            pruned['frontmatter'] = build_output_frontmatter(
                output_path=json_file,
                step='metrics',
                title=resolve_file_title(input_frontmatter),
                body=json.dumps(pruned, ensure_ascii=False, sort_keys=True),
                options=option_values,
                input_frontmatter=input_frontmatter,
                file_format='metrics',
                include_metadata_data=False,
            )

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(pruned, f, indent=2, ensure_ascii=False)
            f.write('\n')
        logger.info('JSON saved to: %s', format_path_for_logging(json_file))

    if args.csv:
        logger.warning('%s', METRICS_CSV_DEPRECATION_MESSAGE)

    if args.table:
        if len(results) == 1:
            inherited_syllabify = inherited_syllabify_options[0]
            table_context = {
                'cli': 'metricalc.py',
                'wpm_words_per_min': PHONETIZE_DEFAULT_WPM,
                'pause_ratio_percent': PHONETIZE_DEFAULT_PAUSE_RATIO,
                'short_pause_punct_weight_unitless': 1.0,
                'fixed_long_pause_punct_weight_unitless': 2.0,
                'extra_consonants': inherited_syllabify['extra_consonants'],
                'extra_vowels': inherited_syllabify['extra_vowels'],
                'input': format_path_for_logging(input_files[0]),
            }
            table = format_table(results[0], run_context=table_context)
            input_frontmatter, tilde_body = read_text_file(input_files[0])
            table_file = base.with_name(base.name + '_metrics.txt')

            frontmatter = build_output_frontmatter(
                output_path=table_file,
                step='metrics',
                title=resolve_file_title(input_frontmatter),
                body=table,
                options=option_values,
                input_frontmatter=input_frontmatter,
                file_format='metrics',
                include_metadata_data=False,
            )

            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(compose_text_document(frontmatter, table))
            logger.info('Written file: %s', format_path_for_logging(table_file))
        else:
            for input_file, result, inherited_syllabify in zip(input_files, results, inherited_syllabify_options):
                table_context = {
                    'cli': 'metricalc.py',
                    'wpm_words_per_min': PHONETIZE_DEFAULT_WPM,
                    'pause_ratio_percent': PHONETIZE_DEFAULT_PAUSE_RATIO,
                    'short_pause_punct_weight_unitless': 1.0,
                    'fixed_long_pause_punct_weight_unitless': 2.0,
                    'extra_consonants': inherited_syllabify['extra_consonants'],
                    'extra_vowels': inherited_syllabify['extra_vowels'],
                    'input': format_path_for_logging(input_file),
                }
                table = format_table(result, run_context=table_context)
                safe_stem = simple_safe_filename(Path(input_file).stem)
                table_file = Path(args.outdir) / f"{safe_stem}_metrics.txt"
                input_frontmatter, tilde_body = read_text_file(input_file)
                frontmatter = build_output_frontmatter(
                    output_path=table_file,
                    step='metrics',
                    title=resolve_file_title(input_frontmatter),
                    body=table,
                    options=option_values,
                    input_frontmatter=input_frontmatter,
                    file_format='metrics',
                    include_metadata_data=False,
                )
                with open(table_file, 'w', encoding='utf-8') as f:
                    f.write(compose_text_document(frontmatter, table))
                logger.info('Written file: %s', format_path_for_logging(table_file))


if __name__ == "__main__":
    main()

