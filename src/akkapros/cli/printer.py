#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Printer (CLI wrapper)

Converts *_tilde text into:
- <prefix>_accent_accute.txt
- <prefix>_accent_bold.md
- <prefix>_accent_ipa.txt
"""

import sys
import argparse
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib import print as accent_print
from akkapros.lib.utils import simple_safe_filename


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Convert *_tilde text into accent-accute, accent-bold and accent-ipa reading outputs'
    )
    parser.add_argument('--version', action='version', version=f'akkapros-printer {accent_print.__version__}')
    parser.add_argument('input', nargs='?', help='Input *_tilde.txt file')
    parser.add_argument('-p', '--prefix', help='Output prefix (shared for all selected outputs)')
    parser.add_argument('--outdir', default='.', help='Output directory (default: .)')

    parser.add_argument('--accute', '--acute', dest='accute', action='store_true',
                        help='Write <prefix>_accent_accute.txt')
    parser.add_argument('--bold', action='store_true',
                        help='Write <prefix>_accent_bold.md')
    parser.add_argument('--ipa', action='store_true',
                        help='Write <prefix>_accent_ipa.txt')
    parser.add_argument('--test', action='store_true', help='Run internal tests')

    args = parser.parse_args()

    if args.test:
        ok = accent_print.run_tests()
        sys.exit(0 if ok else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    outdir = Path(args.outdir)
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    default_prefix = input_path.stem.replace('_tilde', '')
    prefix = simple_safe_filename(args.prefix if args.prefix else default_prefix)

    write_accute = args.accute
    write_bold = args.bold
    write_ipa = args.ipa
    if not (write_accute or write_bold or write_ipa):
        write_accute = True
        write_bold = True

    accute_out = outdir / f"{prefix}_accent_accute.txt"
    bold_out = outdir / f"{prefix}_accent_bold.md"
    ipa_out = outdir / f"{prefix}_accent_ipa.txt"

    accent_print.process_file(
        input_file=str(input_path),
        output_accute_file=str(accute_out),
        output_bold_file=str(bold_out),
        output_ipa_file=str(ipa_out),
        write_accute=write_accute,
        write_bold=write_bold,
        write_ipa=write_ipa,
    )

    print(f"Input: {input_path}")
    if write_accute:
        print(f"Written: {accute_out}")
    if write_bold:
        print(f"Written: {bold_out}")
    if write_ipa:
        print(f"Written: {ipa_out}")


if __name__ == '__main__':
    main()
