#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — eBL ATF Parser (CLI)

COMMAND-LINE INTERFACE: Wraps library for CLI usage

This module provides the command-line interface.
Core parsing logic is in akkapros.lib.parse (library).

For programmatic use, import from akkapros.lib.parse directly.

Part of the Akkadian Prosody project (akkapros)
https://github.com/samuelkabak/akkapros

MIT License
Copyright (c) 2026 Samuel KABAK
"""

import sys
import argparse
import unicodedata
from pathlib import Path

# If executed directly as a script, ensure package imports resolve from repo src/.
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__, __repo_url__
# Import from library
from akkapros.lib.atfparse import ATFParser, run_tests, EBLError
from akkapros.lib.frontmatter import (
    build_atfparse_stage_data,
    build_output_frontmatter,
    compose_text_document,
    effective_options_from_namespace,
    merge_frontmatter_documents,
    read_text_file,
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

__ebl_url__ = "https://www.ebl.lmu.de/"


def save_output(results: dict, prefix: str, outdir: Path, *, options: dict[str, object]):
    """Save all output files, merging front matter when append mode targets an existing file."""
    append = results.get('append', False)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    proc_body = '\n'.join(results['cleaned_lines']) + '\n'
    stage_data = build_atfparse_stage_data(proc_body)
    title = results.get('title') or prefix
    input_file_id = None

    def write_or_append(path, lines, file_format):
        body = '\n'.join(lines) + '\n'
        new_frontmatter = build_output_frontmatter(
            output_path=path,
            step='atfparse',
            title=title,
            body=body,
            options=options,
            stage_data=stage_data,
            input_file_id=input_file_id,
            file_format=file_format,
        )

        merged_frontmatter = new_frontmatter
        merged_body = body
        if append and path.exists():
            existing_frontmatter, existing_body = read_text_file(path)
            merged_body = existing_body
            if merged_body and not merged_body.endswith('\n'):
                merged_body += '\n'
            merged_body += body
            if existing_frontmatter is not None:
                merged_frontmatter = merge_frontmatter_documents(
                    [existing_frontmatter, new_frontmatter],
                    body=merged_body,
                ) or new_frontmatter

        document = compose_text_document(merged_frontmatter, merged_body)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(document)

    # Original Akkadian lines (with ATF markup preserved)
    orig_file = outdir / f"{prefix}_orig.txt"
    write_or_append(orig_file, results['original_akkadian_lines'], 'orig')

    # Cleaned text file
    proc_file = outdir / f"{prefix}_proc.txt"
    write_or_append(proc_file, results['cleaned_lines'], 'proc')

    # English translation if present
    if results['english_translations']:
        trans_file = outdir / f"{prefix}_trans.txt"
        write_or_append(trans_file, results['english_translations'], 'trans')

    return orig_file, proc_file


# simple_safe_filename is provided by akkapros.lib.utils


def main():
    parser = argparse.ArgumentParser(
        description='Convert eBL ATF files to clean Akkadian text',
        formatter_class=RawDefaultsHelpFormatter,
        epilog=f"""
SOURCE:
  This parser is STRICTLY designed for ATF files from the
  electronic Babylonian Library (eBL) platform:
  {__ebl_url__}
  
  PROCESSING RULES:
  * %%n lines are processed as Akkadian
  * #tr.en: lines are processed as translations
  * All other line types (&, @, $, #note:, manuscript sigla) are SILENTLY IGNORED
  
  WITHIN AKKADIAN LINES:
  * ( ) parentheses - KEEP content, remove parentheses
  * [ ] brackets - KEEP content, remove brackets
  * < > angle brackets - KEEP content, remove brackets
  * {{ }} braces - REMOVE entirely (determinatives)
  * | single pipe - CONVERT to space (word boundary)
    * || double pipe - REPLACE with ':' (major division/phrase boundary)
    * ‡ Glossenkeil - REPLACE with ':' (phrase divider)
  * ' single quote - PRESERVE (emendation marker)
    * x broken sign - REPLACE with a SINGLE '…' (multiple x's collapse)
  * 0-9 numerals - PRESERVE
  * ? ! * ° - REMOVE (editorial signs)
    * … - PRESERVE (ellipsis)
  * Hyphens - PRESERVE (part of transliteration)

  MULTI-LINE HANDLING:
  * Consecutive %%n lines are concatenated with spaces
  * Empty %%n lines (line numbers only) are ignored

  LIMITATIONS (The program does NOT preserve):
  * Line numbers
  * Column divisions
  * Parallel passages
  * Variant readings
  * Other structural metadata

OPTIONS:
  --test      - Run self-test suite
  --strict    - Enable warnings for informational purposes
  -p, --prefix PREFIX  - Specify output file prefix (default is input filename stem)

OUTPUT FILES (created in --outdir):
  PREFIX_orig.txt    - Original %%n lines (with ATF markup preserved)
    PREFIX_proc.txt    - Cleaned text for syllabification/prosody realization
  PREFIX_trans.txt   - English translation (if present)

For more information, visit:
{__repo_url__}

Part of Akkadian Prosody Toolkit v{__version__}
MIT License (c) 2026 Samuel KABAK
"""
    )
    add_standard_version_argument(parser, 'akkapros-atfparser')
    add_standard_logging_arguments(parser)
    parser.add_argument('input', nargs='?', help='eBL ATF file (must contain %%n lines)')
    parser.add_argument('-p', '--prefix', 
                       help='Output prefix')
    parser.add_argument('--outdir', default='.',
                       help='Output directory')
    parser.add_argument('--remove-hyphens', action='store_true',
                    help='Remove hyphens (cuneiform sign boundaries) for cleaner reading text')
    parser.add_argument('--preserve-case', action='store_true',
                       help='Preserve original case')
    parser.add_argument('--preserve-h', action='store_true',
                       help='Preserve original [h,H]')
    parser.add_argument('--strict', action='store_true',
                       help='Enable warnings for informational purposes')
    parser.add_argument('--test', action='store_true', help='Run self-test suite')
    parser.add_argument('--append', action='store_true', help='Append to output files instead of overwriting (each appended block starts on a new line)')
    
    args = parser.parse_args()
    
    # Handle test mode
    if args.test:
        logger = setup_cli_logging(args, 'akkapros.cli.atfparser')
        log_startup_banner(logger, 'akkapros-atfparser', __version__, args)
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # If no input file, show help
    if not args.input:
        parser.print_help()
        sys.exit(0)

    logger = setup_cli_logging(args, 'akkapros.cli.atfparser')
    log_startup_banner(logger, 'akkapros-atfparser', __version__, args)
    
    # Regular mode with input file
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("File '%s' not found.", args.input)
        sys.exit(1)

    try:
        validate_intermediate_format(input_path, expected_kind='atf')
    except FormatValidationError as exc:
        logger.error('Invalid input format: %s', exc)
        logger.error('Hint: expected ATF input with %%n lines; verify line markup and rerun.')
        sys.exit(2)
    
    # Determine output prefix
    if args.prefix:
        prefix = args.prefix
    else:
        prefix = input_path.stem
    
    outdir = Path(args.outdir)

    try:
        parser_obj = ATFParser(
            preserve_case=args.preserve_case,
            preserve_h=args.preserve_h,
            remove_hyphens=args.remove_hyphens, 
            strict_mode=args.strict
        )
        results = parser_obj.parse_file(str(input_path))
        # Pass append flag to save_output via results dict
        results['append'] = args.append
        # Save outputs
        orig_file, proc_file = save_output(
            results,
            prefix,
            outdir,
            options=effective_options_from_namespace(
                args,
                exclude={'input', 'outdir', 'prefix', 'test', 'version'},
            ),
        )

        logger.info('')
        logger.info('%s', '=' * 60)
        logger.info('PARSING COMPLETE')
        logger.info('%s', '=' * 60)

        if results['title']:
            logger.info('Title: %s', results['title'])

        logger.info('English translations: %d', len(results['english_translations']))
        logger.info('Original Akkadian lines: %d', len(results['original_akkadian_lines']))
        logger.info('Cleaned lines: %d', len(results['cleaned_lines']))

        if args.strict and results['warnings']:
            logger.warning('WARNINGS (%d):', len(results['warnings']))
            for w in results['warnings'][:20]:
                logger.warning('  * %s', w)
            if len(results['warnings']) > 20:
                logger.warning('  * ... and %d more', len(results['warnings']) - 20)

        logger.info('')
        logger.info('%s', '-' * 60)
        logger.info('FIRST 5 ORIGINAL AKKADIAN LINES (with ATF markup):')
        logger.info('%s', '-' * 60)
        for i, line in enumerate(results['original_akkadian_lines'][:5]):
            logger.info('%2d. %s', i + 1, line)

        logger.info('')
        logger.info('%s', '-' * 60)
        logger.info('FIRST 5 CLEANED LINES (ready for prosody realization):')
        logger.info('%s', '-' * 60)
        for i, line in enumerate(results['cleaned_lines'][:5]):
            logger.info('%2d. %s', i + 1, line)

        logger.info('')
        logger.info('%s', '=' * 60)
        logger.info('FILES SAVED:')
        display_prefix = simple_safe_filename(prefix)
        logger.info(
            '  %s (original, with ATF markup)',
            format_path_for_logging(outdir / f'{display_prefix}_orig.txt'),
        )
        logger.info(
            '  %s (cleaned, ready for prosody realization)',
            format_path_for_logging(outdir / f'{display_prefix}_proc.txt'),
        )
        if results['english_translations']:
            trans_file = outdir / f"{display_prefix}_trans.txt"
            logger.info('  %s', format_path_for_logging(trans_file))
        logger.info('%s', '=' * 60)
        
    except EBLError as e:
        logger.error('%s', e)
        sys.exit(1)
    except Exception as e:
        logger.exception('UNEXPECTED ERROR: %s', e)
        sys.exit(1)


if __name__ == "__main__":
    main()
