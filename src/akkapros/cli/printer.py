#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Printer (CLI wrapper)

Converts *_tilde text into:
- <prefix>_accent_acute.txt
- <prefix>_accent_bold.md
- <prefix>_accent_ipa.txt
- <prefix>_accent_xar.txt
- <prefix>_xar.txt
- <prefix>_accent_mbrola.txt
"""

import sys
import argparse
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__
from akkapros.lib import print as accent_print
from akkapros.lib.utils import simple_safe_filename
from akkapros.lib.utils import RawDefaultsHelpFormatter, print_startup_banner, add_standard_version_argument


def _resolve_ipa_options(args: argparse.Namespace) -> tuple[bool, str, bool]:
    """Resolve IPA output flags: enabled, mode, and circumflex hiatus splitting.

    CLI option renamed: `--ipa-proto-semitic` (values: 'preserve', 'replace').
    Internally this maps to existing IPA modes used by `print.py`.
    """
    write_ipa = args.ipa
    # map new CLI values to existing internal ipa modes
    ipa_mode = 'ipa-strict' if getattr(args, 'ipa_proto_semitic', None) == 'preserve' else 'ipa-ob'
    circ_hiatus = args.circ_hiatus

    return write_ipa, ipa_mode, circ_hiatus


def run_tests() -> bool:
    """Run printer CLI resolution tests and delegated library tests."""
    ok = True

    class _Args:
        def __init__(self, ipa: bool, ipa_proto_semitic: str, circ_hiatus: bool) -> None:
            self.ipa = ipa
            self.ipa_proto_semitic = ipa_proto_semitic
            self.circ_hiatus = circ_hiatus

    cases = [
        (_Args(False, 'preserve', False), False, 'ipa-strict', False),
        (_Args(False, 'replace', False), False, 'ipa-ob', False),
        (_Args(True, 'preserve', False), True, 'ipa-strict', False),
        (_Args(True, 'replace', False), True, 'ipa-ob', False),
        (_Args(True, 'replace', True), True, 'ipa-ob', True),
    ]

    passed = 0
    for args, exp_write, exp_mode, exp_circ_hiatus in cases:
        got_write, got_mode, got_circ_hiatus = _resolve_ipa_options(args)
        if (
            got_write == exp_write
            and got_mode == exp_mode
            and got_circ_hiatus == exp_circ_hiatus
        ):
            passed += 1
        else:
            ok = False
            print(
                "FAILED [printer cli ipa mode]"
                f"\n  in : ipa={args.ipa}, ipa_proto_semitic={args.ipa_proto_semitic}, circ_hiatus={args.circ_hiatus}"
                f"\n  got: write_ipa={got_write}, ipa_mode={got_mode}, circ_hiatus={got_circ_hiatus}"
                f"\n  exp: write_ipa={exp_write}, ipa_mode={exp_mode}, circ_hiatus={exp_circ_hiatus}"
            )

    print(f"printer.py cli tests: {passed}/{len(cases)} passed")
    ok = accent_print.run_tests() and ok
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Convert *_tilde text into accent-acute, accent-bold, accent-ipa and accent-xar reading outputs',
        formatter_class=RawDefaultsHelpFormatter,
    )
    add_standard_version_argument(parser, 'akkapros-printer')
    parser.add_argument('input', nargs='?', help='Input *_tilde.txt file')
    parser.add_argument('-p', '--prefix', help='Output prefix (shared for all selected outputs)')
    parser.add_argument('--outdir', default='.', help='Output directory')

    parser.add_argument('--acute', action='store_true',
                        help='Write <prefix>_accent_acute.txt')
    parser.add_argument('--bold', action='store_true',
                        help='Write <prefix>_accent_bold.md')
    parser.add_argument('--ipa', action='store_true',
                        help='Write <prefix>_accent_ipa.txt (vowel coloring applies post-emphatic only)')
    parser.add_argument('--ipa-proto-semitic', choices=['preserve', 'replace'], default='preserve',
                        help='IPA proto-Semitic policy: preserve=Old Akkadian, replace=Old Babylonian merger')
    parser.add_argument('--circ-hiatus', action='store_true',
                        help='Speculative IPA mode: split circumflex vowels into hiatus (e.g., qû -> qʊ.ʊ)')
    parser.add_argument('--xar', action='store_true',
                        help='Write both <prefix>_accent_xar.txt and <prefix>_xar.txt')
    parser.add_argument('--mbrola', action='store_true',
                        help='Write <prefix>_accent_mbrola.txt (MBROLA/X-SAMPA-like symbols)')
    parser.add_argument('--test', action='store_true', help='Run internal tests')

    args = parser.parse_args()

    if args.test:
        print_startup_banner('akkapros-printer', __version__, args)
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

    print_startup_banner('akkapros-printer', __version__, args)

    write_acute = args.acute
    write_bold = args.bold
    write_ipa, ipa_mode, circ_hiatus = _resolve_ipa_options(args)
    write_xar = args.xar
    write_mbrola = args.mbrola

    if not (write_acute or write_bold or write_ipa or write_xar or write_mbrola):
        write_acute = True
        write_bold = True

    acute_out = outdir / f"{prefix}_accent_acute.txt"
    bold_out = outdir / f"{prefix}_accent_bold.md"
    ipa_out = outdir / f"{prefix}_accent_ipa.txt"
    xar_out = outdir / f"{prefix}_accent_xar.txt"
    xar_plain_out = outdir / f"{prefix}_xar.txt"
    mbrola_out = outdir / f"{prefix}_accent_mbrola.txt"

    accent_print.process_file(
        input_file=str(input_path),
        output_acute_file=str(acute_out),
        output_bold_file=str(bold_out),
        output_ipa_file=str(ipa_out),
        output_xar_file=str(xar_out),
        output_xar_plain_file=str(xar_plain_out),
        output_mbrola_file=str(mbrola_out),
        write_acute=write_acute,
        write_bold=write_bold,
        write_ipa=write_ipa,
        write_xar=write_xar,
        write_mbrola=write_mbrola,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
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
        print(f"Written: {xar_plain_out}")
    if write_mbrola:
        print(f"Written: {mbrola_out}")


if __name__ == '__main__':
    main()
