#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Full Repair Pipeline (CLI wrapper)

Runs the complete processing pipeline in one command:
1) syllabify (from *_proc.txt to *_syl.txt)
2) repair    (from *_syl.txt to *_tilde.txt)
3) metrics   (from *_tilde.txt to selected metrics outputs)

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
from akkapros.lib.repair import (
    __version__ as repair_version,
    AccentStyle,
    RepairEngine,
    run_tests as run_repair_tests,
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


__version__ = f"syllabify-{syllabify.__version__}|repair-{repair_version}|metrics-{metrics_version}"


def run_pipeline(
    input_file: Path,
    outdir: Path,
    prefix: str,
    extra_vowels: str,
    extra_consonants: str,
    merge_hyphen: bool,
    style: str,
    only_last: bool,
    restore_diphthongs: bool,
    only_restore_diphthongs: bool,
    wpm: float,
    pause_ratio: float,
    punct_weight: float,
    output_table: bool,
    output_json: bool,
    output_csv: bool,
) -> int:
    """Execute syllabify -> repair -> metrics and write all outputs."""
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)

    safe_prefix = simple_safe_filename(prefix)
    syl_file = outdir / f"{safe_prefix}_syl.txt"
    tilde_file = outdir / f"{safe_prefix}_tilde.txt"
    metrics_base = outdir / safe_prefix

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
    )
    with open(syl_file, 'w', encoding='utf-8') as f:
        f.write(syl_text)
    print(f"Written: {syl_file}")

    # 2) Repair using library engine
    print("\n[2/3] Repairing...")
    style_map = {'lob': AccentStyle.LOB, 'sob': AccentStyle.SOB}
    engine = RepairEngine(style=style_map[style], only_last=only_last)
    engine.process_file(
        str(syl_file),
        str(tilde_file),
        restore_diphthongs=restore_diphthongs,
        only_restore_diphthongs=only_restore_diphthongs,
    )
    print(f"Written: {tilde_file}")

    # 3) Metrics
    print("\n[3/3] Computing metrics...")
    update_character_sets(extra_consonants, extra_vowels)
    metrics_result = process_metrics_file(str(tilde_file), wpm, pause_ratio, punct_weight)

    if output_json:
        json_file = metrics_base.with_suffix('.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_result, f, indent=2, ensure_ascii=False)
        print(f"JSON saved to: {json_file}")

    if output_csv:
        csv_file = metrics_base.with_suffix('.csv')
        format_csv([metrics_result], csv_file)
        print(f"CSV saved to: {csv_file}")

    if output_table:
        table = format_table(metrics_result)
        table_file = metrics_base.with_name(metrics_base.name + '_metrics.txt')
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(table)
        print(f"Table saved to: {table_file}")

    print("\nPipeline completed successfully.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Run full Akkadian pipeline: syllabify -> repair -> metrics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
EXAMPLES:
  python fullreparer.py outputs/erra_proc.txt -p erra --outdir outputs --style lob --table
  python fullreparer.py outputs/erra_proc.txt -p erra --restore-diphthongs --json --csv
    python fullreparer.py --test-all

Versions: {__version__}
"""
    )
    parser.add_argument('--version', action='version', version=f'akkapros-fullreparer {__version__}')

    # Input/output (shared)
    parser.add_argument('input', nargs='?', help='Input Akkadian file (typically *_proc.txt)')
    parser.add_argument('-p', '--prefix', help='Shared output prefix for all generated files')
    parser.add_argument('--outdir', default='.', help='Shared output directory (default: .)')

    # Syllabifier options
    parser.add_argument('--extra-vowels', default='', help='Extra characters to treat as vowels')
    parser.add_argument('--extra-consonants', default='', help='Extra characters to treat as consonants')
    parser.add_argument('--merge-hyphen', action='store_true', help='Merge hyphens into syllable separators in syllabification')

    # Repairer options
    parser.add_argument('--style', choices=['lob', 'sob'], default='lob', help='Repair accent style')
    parser.add_argument('-r', '--relax-last', action='store_true',
                        help='For explicit + links, allow repair propagation before the last linked word')
    parser.add_argument('--restore-diphthongs', action='store_true',
                        help='Restore diphthongs after repair (or restoration-only mode)')
    parser.add_argument('--only-restore-diphthongs', action='store_true',
                        help='Skip repair and only restore diphthongs on syllabified text')

    # Metricser options
    parser.add_argument('--csv', action='store_true', help='Write CSV metrics output')
    parser.add_argument('--table', action='store_true', help='Write human-readable metrics table output')
    parser.add_argument('--json', action='store_true', help='Write JSON metrics output')
    parser.add_argument('--wpm', type=float, default=165, help='Words per minute for speech-rate estimation')
    parser.add_argument('--pause-ratio', type=float, default=35, help='Pause ratio percentage')
    parser.add_argument('--punct-weight', type=float, default=2.0,
                        help='Punctuation pause multiplier relative to space pauses')

    # Test controls (covering all grouped sub-components)
    parser.add_argument('--test-syllabify', action='store_true', help='Run syllabify library tests')
    parser.add_argument('--test-repair', action='store_true', help='Run repair library tests')
    parser.add_argument('--test-diphthongs', action='store_true', help='Run diphthong restoration tests')
    parser.add_argument('--test-metrics', action='store_true', help='Run metrics library tests')
    parser.add_argument('--test-print', action='store_true', help='Run print library tests')
    parser.add_argument('--test-all', action='store_true', help='Run tests for syllabify, repair, diphthongs, metrics and print')

    args = parser.parse_args()

    if args.test_all:
        ok = True
        ok = syllabify.run_tests() and ok
        ok = run_repair_tests() and ok
        ok = test_diphthong_restoration() and ok
        ok = run_metrics_tests() and ok
        ok = accent_print.run_tests() and ok
        sys.exit(0 if ok else 1)

    if args.test_syllabify or args.test_repair or args.test_diphthongs or args.test_metrics or args.test_print:
        ok = True
        if args.test_syllabify:
            ok = syllabify.run_tests() and ok
        if args.test_repair:
            ok = run_repair_tests() and ok
        if args.test_diphthongs:
            ok = test_diphthong_restoration() and ok
        if args.test_metrics:
            ok = run_metrics_tests() and ok
        if args.test_print:
            ok = accent_print.run_tests() and ok
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

    output_table = args.table
    output_json = args.json
    output_csv = args.csv

    # Match metricser behavior: default to table if no explicit format selected.
    if not (output_table or output_json or output_csv):
        output_table = True

    only_last = not args.relax_last

    code = run_pipeline(
        input_file=input_path,
        outdir=outdir,
        prefix=prefix,
        extra_vowels=args.extra_vowels,
        extra_consonants=args.extra_consonants,
        merge_hyphen=args.merge_hyphen,
        style=args.style,
        only_last=only_last,
        restore_diphthongs=args.restore_diphthongs,
        only_restore_diphthongs=args.only_restore_diphthongs,
        wpm=args.wpm,
        pause_ratio=args.pause_ratio,
        punct_weight=args.punct_weight,
        output_table=output_table,
        output_json=output_json,
        output_csv=output_csv,
    )
    sys.exit(code)


if __name__ == '__main__':
    main()
