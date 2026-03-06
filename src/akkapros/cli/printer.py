#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Printer (CLI wrapper)

Converts *_tilde text into:
- <prefix>_accent_acute.txt
- <prefix>_accent_bold.md
- <prefix>_accent_ipa.txt
- <prefix>_accent_xar.txt
"""

import sys
import argparse
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib import print as accent_print
from akkapros.lib.utils import simple_safe_filename


def _resolve_ipa_options(args: argparse.Namespace) -> tuple[bool, str]:
    """Resolve whether IPA output is requested and which IPA mode to use."""
    write_ipa = args.ipa
    ipa_mode = 'ipa-strict' if args.ipa_pharyngeal == 'preserve' else 'ipa-ob'

    return write_ipa, ipa_mode


def run_tests() -> bool:
    """Run printer CLI resolution tests and delegated library tests."""
    ok = True

    class _Args:
        def __init__(self, ipa: bool, ipa_pharyngeal: str) -> None:
            self.ipa = ipa
            self.ipa_pharyngeal = ipa_pharyngeal

    cases = [
        (_Args(False, 'preserve'), False, 'ipa-strict'),
        (_Args(False, 'remove'), False, 'ipa-ob'),
        (_Args(True, 'preserve'), True, 'ipa-strict'),
        (_Args(True, 'remove'), True, 'ipa-ob'),
    ]

    passed = 0
    for args, exp_write, exp_mode in cases:
        got_write, got_mode = _resolve_ipa_options(args)
        if got_write == exp_write and got_mode == exp_mode:
            passed += 1
        else:
            ok = False
            print(
                "FAILED [printer cli ipa mode]"
                f"\n  in : ipa={args.ipa}, ipa_pharyngeal={args.ipa_pharyngeal}"
                f"\n  got: write_ipa={got_write}, ipa_mode={got_mode}"
                f"\n  exp: write_ipa={exp_write}, ipa_mode={exp_mode}"
            )

    print(f"printer.py cli tests: {passed}/{len(cases)} passed")
    ok = accent_print.run_tests() and ok
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Convert *_tilde text into accent-acute, accent-bold, accent-ipa and accent-xar reading outputs'
    )
    parser.add_argument('--version', action='version', version=f'akkapros-printer {accent_print.__version__}')
    parser.add_argument('input', nargs='?', help='Input *_tilde.txt file')
    parser.add_argument('-p', '--prefix', help='Output prefix (shared for all selected outputs)')
    parser.add_argument('--outdir', default='.', help='Output directory (default: .)')

    parser.add_argument('--acute', action='store_true',
                        help='Write <prefix>_accent_acute.txt')
    parser.add_argument('--bold', action='store_true',
                        help='Write <prefix>_accent_bold.md')
    parser.add_argument('--ipa', action='store_true',
                        help='Write <prefix>_accent_ipa.txt')
    parser.add_argument('--ipa-pharyngeal', choices=['preserve', 'remove'], default='preserve',
                        help='IPA pharyngeal policy: preserve=Old Akkadian, remove=Old Babylonian merger (default: preserve)')
    parser.add_argument('--xar', action='store_true',
                        help='Write <prefix>_accent_xar.txt')
    parser.add_argument('--test', action='store_true', help='Run internal tests')

    args = parser.parse_args()

    if args.test:
        ok = run_tests()
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

    write_acute = args.acute
    write_bold = args.bold
    write_ipa, ipa_mode = _resolve_ipa_options(args)
    write_xar = args.xar

    if not (write_acute or write_bold or write_ipa or write_xar):
        write_acute = True
        write_bold = True

    acute_out = outdir / f"{prefix}_accent_acute.txt"
    bold_out = outdir / f"{prefix}_accent_bold.md"
    ipa_out = outdir / f"{prefix}_accent_ipa.txt"
    xar_out = outdir / f"{prefix}_accent_xar.txt"

    accent_print.process_file(
        input_file=str(input_path),
        output_acute_file=str(acute_out),
        output_bold_file=str(bold_out),
        output_ipa_file=str(ipa_out),
        output_xar_file=str(xar_out),
        write_acute=write_acute,
        write_bold=write_bold,
        write_ipa=write_ipa,
        write_xar=write_xar,
        ipa_mode=ipa_mode,
    )

    print(f"Input: {input_path}")
    if write_acute:
        print(f"Written: {acute_out}")
    if write_bold:
        print(f"Written: {bold_out}")
    if write_ipa:
        print(f"Written: {ipa_out}")
    if write_xar:
        print(f"Written: {xar_out}")


if __name__ == '__main__':
    main()
