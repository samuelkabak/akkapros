#!/usr/bin/env python3
"""Akkadian Prosody Toolkit - Full Prosody Pipeline (CLI wrapper)

Runs the complete processing pipeline in one command:
1) syllabify (from *_proc.txt to *_syl.txt)
2) prosody realization (from *_syl.txt to *_tilde.txt)
3) metrics   (from *_tilde.txt to selected metrics outputs)
4) print     (from *_tilde.txt to selected accent outputs)

The CLI deduplicates shared options across stages (for example, --prefix,
--outdir, --extra-vowels, --extra-consonants).
"""

import sys
import json
import argparse
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib import syllabify
from akkapros.lib.prosody import (
    __version__ as prosody_version,
    AccentStyle,
    ProsodyEngine,
    run_tests as run_prosody_tests,
    test_diphthong_restoration,
)
from akkapros.lib.metrics import (
    __version__ as metrics_version,
    update_character_sets,
    process_file as process_metrics_file,
    format_table,
    format_csv,
    run_tests as run_metrics_tests,
)
from akkapros.lib import print as accent_print
from akkapros.lib.utils import simple_safe_filename
from akkapros.cli._cli_common import RawDefaultsHelpFormatter, print_startup_banner


__version__ = f"syllabify-{syllabify.__version__}|prosody-{prosody_version}|metrics-{metrics_version}"


def _resolve_ipa_options(args: argparse.Namespace) -> tuple[bool, str, bool]:
    """Resolve IPA output flags: enabled, mode, and circumflex hiatus splitting."""
    output_ipa = args.print_ipa
    ipa_mode = 'ipa-strict' if getattr(args, 'print_ipa_proto_semitic', None) == 'preserve' else 'ipa-ob'
    circ_hiatus = args.print_circ_hiatus

    return output_ipa, ipa_mode, circ_hiatus


def run_tests() -> bool:
    """Run fullprosmaker CLI resolution tests only (no pipeline execution)."""
    class _Args:
        def __init__(self, print_ipa: bool, print_ipa_proto_semitic: str, print_circ_hiatus: bool) -> None:
            self.print_ipa = print_ipa
            self.print_ipa_proto_semitic = print_ipa_proto_semitic
            self.print_circ_hiatus = print_circ_hiatus

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
            print(
                "FAILED [fullprosmaker cli ipa mode]"
                f"\n  in : print_ipa={args.print_ipa}, print_ipa_proto_semitic={args.print_ipa_proto_semitic}, print_circ_hiatus={args.print_circ_hiatus}"
                f"\n  got: output_ipa={got_write}, ipa_mode={got_mode}, print_circ_hiatus={got_circ_hiatus}"
                f"\n  exp: output_ipa={exp_write}, ipa_mode={exp_mode}, print_circ_hiatus={exp_circ_hiatus}"
            )

    print(f"fullprosmaker.py cli tests: {passed}/{len(cases)} passed")
    return passed == len(cases)


def run_pipeline(
    input_file: Path,
    outdir: Path,
    prefix: str,
    extra_vowels: str,
    extra_consonants: str,
    merge_hyphen: bool,
    preserve_lines: bool,
    style: str,
    only_last: bool,
    wpm: float,
    pause_ratio: float,
    long_punct_weight: float,
    output_table: bool,
    output_json: bool,
    output_csv: bool,
    output_acute: bool,
    output_bold: bool,
    output_ipa: bool,
    output_xar: bool,
    ipa_mode: str = 'ipa-ob',
    circ_hiatus: bool = False,
) -> int:
    """Execute syllabify -> prosody realization -> metrics -> print and write all outputs."""
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    safe_prefix = simple_safe_filename(prefix)
    syl_file = outdir / f"{safe_prefix}_syl.txt"
    tilde_file = outdir / f"{safe_prefix}_tilde.txt"
    metrics_base = outdir / safe_prefix
    acute_file = outdir / f"{safe_prefix}_accent_acute.txt"
    bold_file = outdir / f"{safe_prefix}_accent_bold.md"
    ipa_file = outdir / f"{safe_prefix}_accent_ipa.txt"
    xar_file = outdir / f"{safe_prefix}_accent_xar.txt"
    xar_plain_file = outdir / f"{safe_prefix}_xar.txt"

    print(f"Input: {input_file}")
    print(f"Output directory: {outdir}")
    print(f"Output prefix: {safe_prefix}")

    # 1) Syllabify using library call
    print("\n[1/3] Syllabifying...")
    with open(input_file, 'r', encoding='utf-8') as f:
        source_text = f.read()

    syl_text = syllabify.syllabify_text(
        source_text,
        extra_vowels=extra_vowels,
        extra_consonants=extra_consonants,
        merge_hyphen=merge_hyphen,
        preserve_lines=preserve_lines,
    )
    with open(syl_file, 'w', encoding='utf-8') as f:
        f.write(syl_text)
    print(f"Written: {syl_file}")

    # 2) Prosody realization using library engine
    print("\n[2/3] Applying prosody realization...")
    style_map = {'lob': AccentStyle.LOB, 'sob': AccentStyle.SOB}
    engine = ProsodyEngine(style=style_map[style], only_last=only_last)
    engine.process_file(str(syl_file), str(tilde_file))
    print(f"Written: {tilde_file}")

    # 3) Metrics
    print("\n[3/4] Computing metrics...")
    update_character_sets(extra_consonants, extra_vowels)
    metrics_result = process_metrics_file(
        str(tilde_file),
        wpm,
        pause_ratio,
        long_punct_weight,
    )

    if output_json:
        json_file = metrics_base.with_suffix('.json')
        # Deep-copy and prune 'distances' before writing JSON to avoid large lists in output
        from copy import deepcopy
        pruned = deepcopy(metrics_result)
        try:
            pruned.get('original', {}).get('acoustic', {}).pop('distances', None)
        except Exception:
            pass
        try:
            pruned.get('repaired', {}).get('acoustic', {}).pop('distances', None)
        except Exception:
            pass
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(pruned, f, indent=2, ensure_ascii=False)
        print(f"JSON saved to: {json_file}")

    if output_csv:
        csv_file = metrics_base.with_suffix('.csv')
        format_csv([metrics_result], csv_file)
        print(f"CSV saved to: {csv_file}")

    if output_table:
        table_context = {
            'cli': 'fullprosmaker.py',
            'wpm_words_per_min': wpm,
            'pause_ratio_percent': pause_ratio,
            'short_pause_punct_weight_unitless': 1.0,
            'long_pause_punct_weight_unitless': long_punct_weight,
            'extra_consonants': extra_consonants,
            'extra_vowels': extra_vowels,
            'prosody_style': style,
            'prosody_relax_last': not only_last,
            'prosody_restore_diphthongs': True,
            'input': str(tilde_file),
        }
        table = format_table(metrics_result, run_context=table_context)
        table_file = metrics_base.with_name(metrics_base.name + '_metrics.txt')
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"Table saved to: {table_file}")

    # 4) Printer outputs
    print("\n[4/4] Generating accent outputs...")
    accent_print.process_file(
        input_file=str(tilde_file),
        output_acute_file=str(acute_file),
        output_bold_file=str(bold_file),
        output_ipa_file=str(ipa_file),
        output_xar_file=str(xar_file),
        output_xar_plain_file=str(xar_plain_file),
        write_acute=output_acute,
        write_bold=output_bold,
        write_ipa=output_ipa,
        write_xar=output_xar,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
    )

    if output_acute:
        print(f"Accent acute saved to: {acute_file}")
    if output_bold:
        print(f"Accent bold saved to: {bold_file}")
    if output_ipa:
        print(f"Accent IPA saved to: {ipa_file}")
    if output_xar:
        print(f"Accent XAR saved to: {xar_file}")
        print(f"XAR saved to: {xar_plain_file}")

    print("\nPipeline completed successfully.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run full Akkadian pipeline: syllabify -> prosody realization -> metrics',
        formatter_class=RawDefaultsHelpFormatter,
        epilog=f"""
EXAMPLES:
    python fullprosmaker.py outputs/erra_proc.txt -p erra --outdir outputs --prosody-style lob --metrics-table
    python fullprosmaker.py outputs/erra_proc.txt -p erra --metrics-json --metrics-csv
    python fullprosmaker.py outputs/erra_proc.txt -p erra --print-acute --print-bold --print-ipa --print-xar
    python fullprosmaker.py --test-all

Versions: {__version__}
"""
    )
    parser.add_argument('--version', action='version', version=f'akkapros-fullprosmaker {__version__}')

    # Input/output (shared)
    parser.add_argument('input', nargs='?', help='Input Akkadian file (typically *_proc.txt)')
    parser.add_argument('-p', '--prefix', help='Shared output prefix for all generated files')
    parser.add_argument('--outdir', default='.', help='Shared output directory')

    # Syllabifier options
    parser.add_argument('--extra-vowels', default='', help='Extra characters to treat as vowels')
    parser.add_argument('--extra-consonants', default='', help='Extra characters to treat as consonants')
    parser.add_argument('--syl-merge-hyphens', action='store_true', help='Merge hyphens into syllable separators in syllabification')
    parser.add_argument('--syl-merge-lines', action='store_true',
                        help='Merge lines (1 newline=space, 2+ to paragraph break). Default preserves original lines')

    # Prosmaker options
    parser.add_argument('--prosody-style', dest='prosody_style', choices=['lob', 'sob'], default='lob',
                        help='Prosody realization accent style')
    parser.add_argument('--prosody-relax-last', dest='prosody_relax_last', action='store_true',
                        help='For explicit + links, allow prosody realization propagation before the last linked word')

    # Metricalc options
    parser.add_argument('--metrics-csv', action='store_true', help='Write CSV metrics output')
    parser.add_argument('--metrics-table', action='store_true', help='Write human-readable metrics table output')
    parser.add_argument('--metrics-json', action='store_true', help='Write JSON metrics output')
    parser.add_argument('--metrics-wpm', type=float, default=165, help='Words per minute [words/min] for speech-rate estimation')
    parser.add_argument('--metrics-pause-ratio', type=float, default=35, help='Pause ratio [percent of total time]')
    parser.add_argument('--metrics-long-punct-weight', type=float, default=2.0,
                        help='Long pause punctuation weight relative to short pause punctuation [unitless]')

    # Printer options
    parser.add_argument('--print-acute', action='store_true',
                        help='Write <prefix>_accent_acute.txt')
    parser.add_argument('--print-bold', action='store_true',
                        help='Write <prefix>_accent_bold.md')
    parser.add_argument('--print-ipa', action='store_true',
                        help='Write <prefix>_accent_ipa.txt')
    parser.add_argument('--print-ipa-proto-semitic', choices=['preserve', 'replace'], default='preserve',
                        help='IPA proto-Semitic policy: preserve=Old Akkadian, replace=Old Babylonian merger')
    parser.add_argument('--print-circ-hiatus', action='store_true',
                        help='Speculative IPA mode: split circumflex vowels into hiatus (e.g., qu -> qu.u)')
    parser.add_argument('--print-xar', action='store_true',
                        help='Write both <prefix>_accent_xar.txt and <prefix>_xar.txt')

    # Test controls (covering all grouped sub-components)
    parser.add_argument('--test-syllabify', action='store_true', help='Run syllabify library tests')
    parser.add_argument('--test-prosody', dest='test_prosody', action='store_true',
                        help='Run prosody realization library tests')
    parser.add_argument('--test-diphthongs', action='store_true', help='Run diphthong restoration tests')
    parser.add_argument('--test-metrics', action='store_true', help='Run metrics library tests')
    parser.add_argument('--test-print', action='store_true', help='Run print library tests')
    parser.add_argument('--test-cli', action='store_true', help='Run fullprosmaker CLI option-resolution tests')
    parser.add_argument('--test-all', action='store_true', help='Run tests for syllabify, prosody realization, diphthongs, metrics and print')

    args = parser.parse_args()

    print_startup_banner('akkapros-fullprosmaker', __version__, args)

    if args.test_all:
        ok = True
        ok = syllabify.run_tests() and ok
        ok = run_prosody_tests() and ok
        ok = test_diphthong_restoration() and ok
        ok = run_metrics_tests() and ok
        ok = accent_print.run_tests() and ok
        ok = run_tests() and ok
        sys.exit(0 if ok else 1)

    if args.test_syllabify or args.test_prosody or args.test_diphthongs or args.test_metrics or args.test_print or args.test_cli:
        ok = True
        if args.test_syllabify:
            ok = syllabify.run_tests() and ok
        if args.test_prosody:
            ok = run_prosody_tests() and ok
        if args.test_diphthongs:
            ok = test_diphthong_restoration() and ok
        if args.test_metrics:
            ok = run_metrics_tests() and ok
        if args.test_print:
            ok = accent_print.run_tests() and ok
        if args.test_cli:
            ok = run_tests() and ok
        sys.exit(0 if ok else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    outdir = Path(args.outdir)
    prefix = args.prefix if args.prefix else input_path.stem.replace('_proc', '')

    output_table = args.metrics_table
    output_json = args.metrics_json
    output_csv = args.metrics_csv
    output_acute = args.print_acute
    output_bold = args.print_bold
    output_ipa, ipa_mode, circ_hiatus = _resolve_ipa_options(args)
    output_xar = args.print_xar

    # Match metricalc behavior: default to table if no explicit format selected.
    if not (output_table or output_json or output_csv):
        output_table = True

    # Match printer behavior: default to acute + bold if no explicit format selected.
    if not (output_acute or output_bold or output_ipa or output_xar):
        output_acute = True
        output_bold = True

    only_last = not args.prosody_relax_last

    code = run_pipeline(
        input_file=input_path,
        outdir=outdir,
        prefix=prefix,
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        merge_hyphen=args.syl_merge_hyphens,
        preserve_lines=not args.syl_merge_lines,
        style=args.prosody_style,
        only_last=only_last,
        wpm=args.metrics_wpm,
        pause_ratio=args.metrics_pause_ratio,
        long_punct_weight=args.metrics_long_punct_weight,
        output_table=output_table,
        output_json=output_json,
        output_csv=output_csv,
        output_acute=output_acute,
        output_bold=output_bold,
        output_ipa=output_ipa,
        output_xar=output_xar,
        ipa_mode=ipa_mode,
        circ_hiatus=circ_hiatus,
    )
    sys.exit(code)


if __name__ == '__main__':
    main()

