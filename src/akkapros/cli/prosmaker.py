#!/usr/bin/env python3
"""Akkadian Prosody Toolkit - Prosmaker (CLI wrapper).

This module provides a command-line interface that delegates moraic prosody
realization logic to ``akkapros.lib.prosody``. CLI concerns (arguments,
output prefix, output directory and safe filename handling) stay here.
"""

import sys
import argparse
from pathlib import Path

# If the script is executed directly, the package root may not be on sys.path.
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib.prosody import (
    AccentStyle,
    ProsodyEngine,
    run_tests,
    test_diphthong_restoration,
)
from akkapros import __version__
from akkapros.lib.utils import (
    RawDefaultsHelpFormatter,
    add_standard_version_argument,
    print_startup_banner,
    simple_safe_filename,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Apply moraic prosody realization to syllabified Akkadian text',
        formatter_class=RawDefaultsHelpFormatter,
    )
    add_standard_version_argument(parser, 'akkapros-prosmaker')
    parser.add_argument('input', nargs='?', help='Input *_syl.txt file')
    parser.add_argument('-p', '--prefix', help='Output prefix (creates <prefix>_tilde.txt)')
    parser.add_argument('--outdir', default='.', help='Output directory')
    parser.add_argument('--style', choices=['lob', 'sob'], default='lob', help='Accent style')
    parser.add_argument('-r', '--relax-last', action='store_true',
                        help='For explicit + links, allow prosody realization propagation before the last linked word')
    parser.add_argument('--test', action='store_true', help='Run standard tests')
    parser.add_argument('--test-diphthongs', action='store_true', help='Run diphthong restoration tests')

    args = parser.parse_args()

    if args.test:
        print_startup_banner('akkapros-prosmaker', __version__, args)
        success = run_tests()
        sys.exit(0 if success else 1)

    if args.test_diphthongs:
        print_startup_banner('akkapros-prosmaker', __version__, args)
        success = test_diphthong_restoration()
        sys.exit(0 if success else 1)

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    outdir = Path(args.outdir)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    if args.prefix:
        safe_output = simple_safe_filename(args.prefix)
        output_file = outdir / f"{safe_output}_tilde.txt"
    else:
        output_file = outdir / (input_path.stem.replace('_syl', '') + '_tilde.txt')

    style_map = {'lob': AccentStyle.LOB, 'sob': AccentStyle.SOB}
    style = style_map[args.style]

    print_startup_banner('akkapros-prosmaker', __version__, args)

    engine = ProsodyEngine(style=style, only_last=not args.relax_last)
    engine.process_file(str(input_path), str(output_file))


if __name__ == "__main__":
    main()

