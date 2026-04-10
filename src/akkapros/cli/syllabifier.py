#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Syllabifier (CLI wrapper)

This module provides a simple command-line interface that delegates the
syllabification work to ``akkapros.lib.syllabify``.  It replaces the old
``syllabify.py`` script and follows the naming convention: CLI modules are
"actors" (``-ifier``) while library modules are "verbs" (``-ify``).

The interface mirrors other CLIs (e.g. ``atfparser.py``) by allowing the
user to specify an output directory plus a prefix; the final file will be
``<prefix>_syl.txt``.  Use ``-p/--prefix`` and ``--outdir`` rather than
providing a complete file path.
"""

import sys
from pathlib import Path

# If the script is executed directly, the package root may not be on
# sys.path. Prepend repo/src so that `akkapros.*` imports resolve.
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib import syllabify
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
from akkapros.lib.helpmsg import help_for
from akkapros.lib.frontmatter import (
    build_output_frontmatter,
    build_syllabify_stage_data,
    count_lines,
    count_syllables_from_marked_text,
    compose_text_document,
    effective_options_from_namespace,
    extract_lexical_words,
    read_text_file,
    resolve_file_title,
    with_inherited_syllabify_options,
)
from akkapros.lib.utils import simple_safe_filename
from akkapros.lib.utils import (
    FormatValidationError,
    RawDefaultsHelpFormatter,
    add_standard_logging_arguments,
    add_standard_version_argument,
    format_path_for_logging,
    log_startup_banner,
    setup_cli_logging,
    validate_intermediate_format,
)


def process_file(
    input_file: str,
    output_file: str,
    extra_vowels: str = '',
    extra_consonants: str = '',
    merge_hyphen: bool = False,
    preserve_lines: bool = True,
    extra_short_punct_chars: str = '',
    extra_long_punct_chars: str = '',
    extra_short_punct_patterns: list[str] | None = None,
    extra_long_punct_patterns: list[str] | None = None,
    number_format: str = '',
    title: str | None = None,
    options: dict[str, object] | None = None,
    logger=None,
):
    """Read input, syllabify and write output."""
    logger.info('Reading: %s', format_path_for_logging(input_file))
    if extra_vowels:
        logger.info("Extra vowels: '%s'", extra_vowels)
    if extra_consonants:
        logger.info("Extra consonants: '%s'", extra_consonants)
    logger.info('Hyphen mode: %s', 'MERGE TO DOTS' if merge_hyphen else 'PRESERVE')
    logger.info(
        'Line mode: %s',
        'PRESERVE ORIGINAL LINES' if preserve_lines else 'NORMALIZE (1 newline=space, 2+=paragraph break)',
    )

    input_frontmatter, content = read_text_file(input_file)

    logger.info('Processing...')
    result = syllabify.syllabify_text(
        content,
        extra_vowels=extra_vowels,
        extra_consonants=extra_consonants,
        merge_hyphen=merge_hyphen,
        preserve_lines=preserve_lines,
        short_punct_chars=extra_short_punct_chars,
        long_punct_chars=extra_long_punct_chars,
        short_punct_patterns=extra_short_punct_patterns,
        long_punct_patterns=extra_long_punct_patterns,
        number_format=number_format,
    )

    output_body = result if result.endswith('\n') else result + '\n'
    logger.info('Computed line_count: %d', count_lines(output_body))
    logger.info('Computed word_count: %d', len(extract_lexical_words(output_body)))
    logger.info('Computed syllable_count: %d', count_syllables_from_marked_text(output_body))
    frontmatter = build_output_frontmatter(
        output_path=output_file,
        step='syllabify',
        title=resolve_file_title(input_frontmatter, override_title=title),
        body=output_body,
        options=options,
        stage_data=build_syllabify_stage_data(content, output_body, input_frontmatter=input_frontmatter),
        input_frontmatter=input_frontmatter,
        file_format='syl',
    )
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(compose_text_document(frontmatter, output_body))
    logger.info('Written file: %s', format_path_for_logging(output_file))


def run_tests() -> bool:
    """Run the module's self-tests."""
    return syllabify.run_tests()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Syllabify Akkadian text",
        formatter_class=RawDefaultsHelpFormatter,
        add_help=False,
    )
    add_standard_version_argument(parser, 'akkapros-syllabifier')
    add_standard_logging_arguments(parser)
    add_config_argument(parser)
    add_runtime_interface_arguments(parser, 'syllabifier')
    parser.add_argument('input', nargs='?', help=help_for('syllabifier.input'))
    parser.add_argument('-p', '--prefix', help=help_for('syllabifier.prefix'))
    parser.add_argument('--outdir', default='.',
                        help=help_for('syllabifier.outdir'))
    parser.add_argument('--extra-vowels', default='', help=help_for('syllabifier.extra_vowels'))
    parser.add_argument('--extra-consonants', default='', help=help_for('syllabifier.extra_consonants'))
    parser.add_argument('--extra-short-punct-chars', default='', help=help_for('syllabifier.extra_short_punct_chars'))
    parser.add_argument('--extra-long-punct-chars', default='', help=help_for('syllabifier.extra_long_punct_chars'))
    parser.add_argument('--extra-short-punct-pattern', action='append', default=[],
                        help=help_for('syllabifier.extra_short_punct_pattern'))
    parser.add_argument('--extra-long-punct-pattern', action='append', default=[],
                        help=help_for('syllabifier.extra_long_punct_pattern'))
    parser.add_argument('--number-format', default='',
                        help=help_for('syllabifier.number_format'))
    parser.add_argument('--merge-hyphen', action='store_true', help=help_for('syllabifier.merge_hyphen'))
    parser.add_argument('--merge-lines', action='store_true',
                        help=help_for('syllabifier.merge_lines'))
    parser.add_argument('--title', help=help_for('syllabifier.title'))
    parser.add_argument('--test', action='store_true', help=help_for('syllabifier.test'))

    try:
        args = parse_args_with_config(parser, 'syllabifier')
    except ConfigError as exc:
        sys.stderr.write(f"Invalid config: {exc}\n")
        sys.exit(2)
    if args.test:
        logger = setup_cli_logging(args, 'akkapros.cli.syllabifier')
        log_startup_banner(logger, 'akkapros-syllabifier', __version__, args)
        log_deprecated_config_flag_warnings(logger, args)
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.input:
        sys.stdout.write(render_runtime_help(parser, 'syllabifier'))
        sys.exit(0)

    logger = setup_cli_logging(args, 'akkapros.cli.syllabifier')
    log_startup_banner(logger, 'akkapros-syllabifier', __version__, args)
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
        sys.exit(2)

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("File '%s' not found.", args.input)
        sys.exit(1)

    try:
        validate_intermediate_format(input_path, expected_kind='proc')
    except FormatValidationError as exc:
        logger.error('Invalid input format: %s', exc)
        logger.error('Hint: expected cleaned *_proc.txt content; re-run atfparser if needed.')
        sys.exit(2)

    # choose prefix and output directory
    try:
        prefix = require_effective_prefix(args.prefix, 'syllabifier')
    except ConfigError as exc:
        logger.error('%s', exc)
        sys.exit(2)
    outdir = Path(args.outdir)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)
    output_path = outdir / f"{prefix}_syl.txt"

    option_values = with_inherited_syllabify_options(
        effective_options_from_namespace(
            args,
            exclude={'input', 'outdir', 'prefix', 'test', 'version', 'conf'},
        ),
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        extra_short_punct_chars=args.extra_short_punct_chars,
        extra_long_punct_chars=args.extra_long_punct_chars,
        extra_short_punct_pattern=args.extra_short_punct_pattern,
        extra_long_punct_pattern=args.extra_long_punct_pattern,
    )

    process_file(
        str(input_path),
        str(output_path),
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        merge_hyphen=args.merge_hyphen,
        preserve_lines=not args.merge_lines,
        extra_short_punct_chars=args.extra_short_punct_chars,
        extra_long_punct_chars=args.extra_long_punct_chars,
        extra_short_punct_patterns=args.extra_short_punct_pattern,
        extra_long_punct_patterns=args.extra_long_punct_pattern,
        number_format=args.number_format,
        title=args.title,
        options=option_values,
        logger=logger,
    )


if __name__ == '__main__':
    main()
