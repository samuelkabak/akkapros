#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — eBL ATF Parser (CLI)
Version: 1.0.0

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

# Import from library
from akkapros.lib.atfparse import ATFParser, run_tests, EBLError
from akkapros.lib.utils import simple_safe_filename
from akkapros.cli._cli_common import RawDefaultsHelpFormatter, print_startup_banner

__version__ = "1.0.0"
__author__ = "Samuel KABAK"
__license__ = "MIT"
__project__ = "Akkadian Prosody"
__repo__ = "akkapros"
__ebl_url__ = "https://www.ebl.lmu.de/"


def save_output(results: dict, prefix: str, outdir: Path):
    """Save all output files. If append is True, append to files, ensuring a newline before new content if needed."""
    append = results.get('append', False)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    def write_or_append(path, lines):
        mode = 'a' if append else 'w'
        # Always ensure file ends with a newline before appending
        if append and path.exists():
            with open(path, 'rb+') as f:
                f.seek(-1, 2)
                last = f.read(1)
                if last != b'\n':
                    f.write(b'\n')
        with open(path, mode, encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    # Original Akkadian lines (with ATF markup preserved)
    orig_file = outdir / f"{prefix}_orig.txt"
    write_or_append(orig_file, results['original_akkadian_lines'])

    # Cleaned text file
    proc_file = outdir / f"{prefix}_proc.txt"
    write_or_append(proc_file, results['cleaned_lines'])

    # English translation if present
    if results['english_translations']:
        trans_file = outdir / f"{prefix}_trans.txt"
        write_or_append(trans_file, results['english_translations'])

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
  PREFIX_proc.txt    - Cleaned text for syllabification/repair
  PREFIX_trans.txt   - English translation (if present)

For more information, visit:
{__repo__}

Part of Akkadian Prosody Toolkit v{__version__}
MIT License (c) 2026 Samuel KABAK
"""
    )
    parser.add_argument('--version', action='version',
                       version=f'akkapros-parser {__version__}')
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
        print_startup_banner('akkapros-atfparser', __version__, args)
        print("\n" + "="*80)
        print("AKKADIAN PROSODY TOOLKIT — SELF-TEST SUITE")
        print("="*80)
        success = run_tests()
        if success:
            print(f"✅ All 12 tests PASSED")
        else:
            print(f"❌ Some tests FAILED")
        print("="*80)
        sys.exit(0 if success else 1)
    
    # If no input file, show help
    if not args.input:
        parser.print_help()
        sys.exit(0)
    
    # Regular mode with input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\nError: File '{args.input}' not found.")
        sys.exit(1)
    
    # Determine output prefix
    if args.prefix:
        prefix = args.prefix
    else:
        prefix = input_path.stem
    
    outdir = Path(args.outdir)

    print_startup_banner('akkapros-atfparser', __version__, args)
    
    print(f"\nInput: {args.input}")
    print(f"Output directory: {outdir}")
    print(f"Output prefix: {prefix}")
    print(f"Case: {'PRESERVED' if args.preserve_case else 'CONVERTED TO LOWERCASE'}")
    print(f"Letters [h,H]: {'PRESERVED' if args.preserve_h else 'CONVERTED TO [ḫ,Ḫ]'}")
    print(f"Mode: {'STRICT (warnings enabled)' if args.strict else 'NORMAL (silent)'}")
    print("-" * 60)
    
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
        orig_file, proc_file = save_output(results, prefix, outdir)

        print("\n" + "="*60)
        print("PARSING COMPLETE")
        print("="*60)

        if results['title']:
            print(f"Title: {results['title']}")

        print(f"\nEnglish translations: {len(results['english_translations'])}")
        print(f"Original Akkadian lines: {len(results['original_akkadian_lines'])}")
        print(f"Cleaned lines: {len(results['cleaned_lines'])}")

        if args.strict and results['warnings']:
            print(f"\nWARNINGS ({len(results['warnings'])}):")
            for w in results['warnings'][:20]:
                print(f"  * {w}")
            if len(results['warnings']) > 20:
                print(f"  * ... and {len(results['warnings'])-20} more")

        print("\n" + "-"*60)
        print("FIRST 5 ORIGINAL AKKADIAN LINES (with ATF markup):")
        print("-"*60)
        for i, line in enumerate(results['original_akkadian_lines'][:5]):
            print(f"{i+1:2d}. {line}")

        print("\n" + "-"*60)
        print("FIRST 5 CLEANED LINES (ready for repair):")
        print("-"*60)
        for i, line in enumerate(results['cleaned_lines'][:5]):
            print(f"{i+1:2d}. {line}")

        print("\n" + "="*60)
        print("FILES SAVED:")
        display_prefix = simple_safe_filename(prefix)
        print(f"  {outdir / f'{display_prefix}_orig.txt'} (original, with ATF markup)")
        print(f"  {outdir / f'{display_prefix}_proc.txt'} (cleaned, ready for repair)")
        if results['english_translations']:
            trans_file = outdir / f"{display_prefix}_trans.txt"
            print(f"  {trans_file}")
        print("="*60)
        
    except EBLError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
