#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Syllabifier (CLI wrapper)

This module provides a simple command-line interface that delegates the
syllabification work to ``akkapros.lib.syllabify``.  It replaces the old
``syllabify.py`` script and follows the naming convention: CLI modules are
"actors" (``-ifier``) while library modules are "verbs" (``-ify``).
"""

import sys
from pathlib import Path

# if the script is executed directly (e.g. `python cli/syllabifier.py`),
# the package root may not be on sys.path.  Prepend the "src" directory
# relative to the repo root so that `akkapros.lib` can be imported.
_repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib import syllabify
from akkapros.lib.utils import simple_safe_filename

__version__ = syllabify.__version__


def process_file(input_file: str, output_file: str, extra_vowels: str = '', extra_consonants: str = '', merge_hyphen: bool = False):
    """Read input, syllabify and write output."""
    print(f"Reading: {input_file}")
    if extra_vowels:
        print(f"Extra vowels: '{extra_vowels}'")
    if extra_consonants:
        print(f"Extra consonants: '{extra_consonants}'")
    print(f"Hyphen mode: {'MERGE TO DOTS' if merge_hyphen else 'PRESERVE'}")

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Processing...")
    result = syllabify.syllabify_text(content, extra_vowels=extra_vowels, extra_consonants=extra_consonants, merge_hyphen=merge_hyphen)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"Written: {output_file}")


def run_tests() -> bool:
    """Run the module's self-tests."""
    return syllabify.run_tests()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Syllabify Akkadian text")
    parser.add_argument('--version', action='version', version=f'akkapros-syllabifier {__version__}')
    parser.add_argument('input', nargs='?', help='Input file')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--extra-vowels', default='', help='Extra vowels')
    parser.add_argument('--extra-consonants', default='', help='Extra consonants')
    parser.add_argument('--merge-hyphen', action='store_true', help='Merge hyphen to dots')
    parser.add_argument('--test', action='store_true', help='Run internal tests')

    args = parser.parse_args()
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File '{args.input}' not found.")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix('_syl.txt')
    process_file(str(input_path), str(output_path), extra_vowels=args.extra_vowels, extra_consonants=args.extra_consonants, merge_hyphen=args.merge_hyphen)


if __name__ == '__main__':
    main()
