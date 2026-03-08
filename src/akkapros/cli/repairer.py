#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Repairer (CLI wrapper)

This module provides a command-line interface that delegates moraic repair
logic to ``akkapros.lib.repair``. CLI concerns (arguments, output prefix,
output directory and safe filename handling) stay here.
"""

import sys
import re
import argparse
import unicodedata
from pathlib import Path

# if the script is executed directly (e.g. `python cli/repairer.py`),
# the package root may not be on sys.path. Prepend the "src" directory.
_repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib.repair import (
    __version__,
    AccentStyle,
    RepairEngine,
    run_tests,
    test_diphthong_restoration,
)
from akkapros.cli._cli_common import RawDefaultsHelpFormatter, print_startup_banner


def simple_safe_filename(text: str) -> str:
    """Minimal safe filename conversion."""
    if not text:
        return "unnamed"

    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    text = re.sub(r'[<>:"/\\|?*\s]', '_', text)
    text = re.sub(r'[^\w\-.]', '_', text)
    text = re.sub(r'_+', '_', text)
    text = text.strip('._-')

    return text or "unnamed"


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Apply moraic repair to syllabified Akkadian text',
        formatter_class=RawDefaultsHelpFormatter,
    )
    parser.add_argument('--version', action='version', version=f'akkapros-repairer {__version__}')
    parser.add_argument('input', nargs='?', help='Input *_syl.txt file')
    parser.add_argument('-p', '--prefix', help='Output prefix (creates <prefix>_tilde.txt)')
    parser.add_argument('--outdir', default='.', help='Output directory')
    parser.add_argument('--style', choices=['lob', 'sob'], default='lob', help='Accent style')
    parser.add_argument('-r', '--relax-last', action='store_true',
                        help='For explicit + links, allow repair propagation before the last linked word')
    parser.add_argument('--restore-diphthongs', action='store_true',
                        help='Restore original diphthongs by removing inserted glottal stops')
    parser.add_argument('--only-restore-diphthongs', action='store_true',
                        help='ONLY restore diphthongs without running repair algorithm')
    parser.add_argument('--test', action='store_true', help='Run standard tests')
    parser.add_argument('--test-diphthongs', action='store_true', help='Run diphthong restoration tests')

    args = parser.parse_args()

    if args.test:
        print_startup_banner('akkapros-repairer', __version__, args)
        success = run_tests()
        sys.exit(0 if success else 1)

    if args.test_diphthongs:
        print_startup_banner('akkapros-repairer', __version__, args)
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

    print_startup_banner('akkapros-repairer', __version__, args)

    engine = RepairEngine(style=style, only_last=not args.relax_last)
    engine.process_file(
        str(input_path),
        str(output_file),
        args.restore_diphthongs,
        args.only_restore_diphthongs,
    )


if __name__ == "__main__":
    main()
