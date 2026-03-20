#!/usr/bin/env python3
"""Akkadian Prosody Toolkit — Metrics Calculator (CLI wrapper)

This module provides the command-line interface and delegates all
metrics computation to ``akkapros.lib.metrics``.
"""

import sys
import json
from copy import deepcopy
import argparse
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros import __version__
from akkapros.lib.metrics import (
    update_character_sets,
    process_file,
    format_table,
    format_csv,
    run_tests,
)
from akkapros.lib.utils import (
    RawDefaultsHelpFormatter,
    add_standard_version_argument,
    print_startup_banner,
    simple_safe_filename,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Compute metrics for Akkadian text',
        formatter_class=RawDefaultsHelpFormatter,
        epilog=f"""
EXAMPLES:
    python metricalc.py erra_tilde.txt --table
    python metricalc.py --test
    python metricalc.py erra_tilde.txt --extra-consonants "xyz" --extra-vowels "ø"
    python metricalc.py erra_tilde.txt --long-punct-weight 2.5

Version {__version__}
"""
    )
    add_standard_version_argument(parser, 'akkapros-metricalc')
    parser.add_argument('input', nargs='?', help='Input *_tilde.txt file')
    parser.add_argument('--input-list', help='File containing list of input files (one per line)')
    parser.add_argument('-p', '--prefix', help='Output prefix')
    parser.add_argument('--outdir', default='.', help='Output directory')
    parser.add_argument('--csv', action='store_true', help='Output CSV format')
    parser.add_argument('--table', action='store_true', help='Output human-readable table')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--wpm', type=float, default=165, help='Words per minute [words/min]')
    parser.add_argument('--pause-ratio', type=float, default=35,
                        help='Pause ratio [percent of total time]')
    parser.add_argument('--long-punct-weight', type=float, default=2.0,
                        help='Long pause punctuation weight relative to short pause punctuation [unitless]')
    parser.add_argument('--extra-consonants', default='',
                        help='Extra characters to treat as consonants')
    parser.add_argument('--extra-vowels', default='',
                        help='Extra characters to treat as vowels')
    parser.add_argument('--test', action='store_true', help='Run unit tests')

    args = parser.parse_args()

    print_startup_banner('akkapros-metrics', __version__, args)

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not (args.csv or args.table or args.json):
        args.table = True

    input_files = []
    if args.input_list:
        with open(args.input_list, 'r', encoding='utf-8') as f:
            input_files = [line.strip() for line in f if line.strip()]
    elif args.input:
        input_files = [args.input]
    else:
        parser.print_help()
        sys.exit(1)

    for input_file in input_files:
        if not Path(input_file).exists():
            print(f"Error: File not found: {input_file}")
            sys.exit(1)

    update_character_sets(args.extra_consonants, args.extra_vowels)

    results = []
    for input_file in input_files:
        print(f"Processing: {input_file}")
        result = process_file(
            input_file,
            args.wpm,
            args.pause_ratio,
            args.long_punct_weight,
        )
        results.append(result)

    if args.outdir != '.':
        Path(args.outdir).mkdir(parents=True, exist_ok=True)

    if args.prefix:
        safe_output = simple_safe_filename(args.prefix)
        base = Path(args.outdir) / safe_output
    else:
        if len(input_files) == 1:
            base = Path(args.outdir) / Path(input_files[0]).stem
        else:
            base = Path(args.outdir) / 'metrics'

    if args.json:
        json_file = base.with_name(base.name + '_metrics.json')
        pruned = deepcopy(results[0] if len(results) == 1 else results)
        def _prune_res(obj):
            try:
                if isinstance(obj, dict):
                    orig = obj.get('original')
                    rep = obj.get('accentuated')
                    if isinstance(orig, dict):
                        orig.get('acoustic', {}).pop('distances', None)
                    if isinstance(rep, dict):
                        rep.get('acoustic', {}).pop('distances', None)
            except Exception:
                pass

        if isinstance(pruned, list):
            for r in pruned:
                _prune_res(r)
        else:
            _prune_res(pruned)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(pruned, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print(f"JSON saved to: {json_file}")

    if args.csv:
        csv_file = base.with_name(base.name + '_metrics.csv')
        format_csv(results, csv_file)
        print(f"CSV saved to: {csv_file}")

    if args.table:
        if len(results) == 1:
            table_context = {
                'cli': 'metricalc.py',
                'wpm_words_per_min': args.wpm,
                'pause_ratio_percent': args.pause_ratio,
                'short_pause_punct_weight_unitless': 1.0,
                'long_pause_punct_weight_unitless': args.long_punct_weight,
                'extra_consonants': args.extra_consonants,
                'extra_vowels': args.extra_vowels,
                'input': input_files[0],
            }
            table = format_table(results[0], run_context=table_context)
            if args.prefix:
                table_file = base.with_name(base.name + '_metrics.txt')
            else:
                table_file = base.with_name(base.stem + '_metrics.txt')

            with open(table_file, 'w', encoding='utf-8') as f:
                f.write(table)
            print(f"Table saved to: {table_file}")
        else:
            for result in results:
                table_context = {
                    'cli': 'metricalc.py',
                    'wpm_words_per_min': args.wpm,
                    'pause_ratio_percent': args.pause_ratio,
                    'short_pause_punct_weight_unitless': 1.0,
                    'long_pause_punct_weight_unitless': args.long_punct_weight,
                    'extra_consonants': args.extra_consonants,
                    'extra_vowels': args.extra_vowels,
                    'input': result['file'],
                }
                table = format_table(result, run_context=table_context)
                safe_stem = simple_safe_filename(Path(result['file']).stem)
                table_file = Path(args.outdir) / f"{safe_stem}_metrics.txt"
                with open(table_file, 'w', encoding='utf-8') as f:
                    f.write(table)
                print(f"Table saved to: {table_file}")


if __name__ == "__main__":
    main()

