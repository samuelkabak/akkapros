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
from akkapros.lib.utils import simple_safe_filename
from akkapros.cli._cli_common import RawDefaultsHelpFormatter, print_startup_banner, add_standard_version_argument


def process_file(
    input_file: str,
    output_file: str,
    extra_vowels: str = '',
    extra_consonants: str = '',
    merge_hyphen: bool = False,
    preserve_lines: bool = True,
):
    """Read input, syllabify and write output."""
    print(f"Reading: {input_file}")
    if extra_vowels:
        print(f"Extra vowels: '{extra_vowels}'")
    if extra_consonants:
        print(f"Extra consonants: '{extra_consonants}'")
    print(f"Hyphen mode: {'MERGE TO DOTS' if merge_hyphen else 'PRESERVE'}")
    print(f"Line mode: {'PRESERVE ORIGINAL LINES' if preserve_lines else 'NORMALIZE (1 newline=space, 2+=paragraph break)'}")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Processing...")
    result = syllabify.syllabify_text(
        content,
        extra_vowels=extra_vowels,
        extra_consonants=extra_consonants,
        merge_hyphen=merge_hyphen,
        preserve_lines=preserve_lines,
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"Written: {output_file}")


def run_tests() -> bool:
    """Run the module's self-tests."""
    return syllabify.run_tests()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Syllabify Akkadian text",
        formatter_class=RawDefaultsHelpFormatter,
    )
    add_standard_version_argument(parser, 'akkapros-syllabifier')
    parser.add_argument('input', nargs='?', help='Input file')
    parser.add_argument('-p', '--prefix', help='Output file prefix')
    parser.add_argument('--outdir', default='.',
                        help='Output directory')
    parser.add_argument('--extra-vowels', default='', help='Extra vowels')
    parser.add_argument('--extra-consonants', default='', help='Extra consonants')
    parser.add_argument('--merge-hyphen', action='store_true', help='Merge hyphen to dots')
    parser.add_argument('--merge-lines', action='store_true',
                        help='Merge lines (1 newline=space, 2+ to paragraph break). Default preserves original lines')
    parser.add_argument('--test', action='store_true', help='Run internal tests')

    args = parser.parse_args()
    if args.test:
        print_startup_banner('akkapros-syllabifier', __version__, args)
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File '{args.input}' not found.")
        sys.exit(1)

    # choose prefix and output directory
    if args.prefix:
        prefix = args.prefix
    else:
        prefix = input_path.stem
    outdir = Path(args.outdir)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)
    output_path = outdir / f"{prefix}_syl.txt"

    # display configuration
    print_startup_banner('akkapros-syllabifier', __version__, args)
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Output directory: {outdir}")
    print(f"Output prefix: {prefix}")

    process_file(
        str(input_path),
        str(output_path),
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        merge_hyphen=args.merge_hyphen,
        preserve_lines=not args.merge_lines,
    )


if __name__ == '__main__':
    main()
