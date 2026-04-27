#!/usr/bin/env python3
"""Generate call-graph diagrams for akkapros modules via CLI entry points.

Discovers CLI programs in src/akkapros/cli/ dynamically, then traces each
by calling its main() function with minimal arguments. The trace captures
all library modules called downstream — no hardcoded module lists needed.

Output: Mermaid (.mmd) files in docs/internal/code-index/
Usage:  python scripts/gen_code_graph.py [--graph] [--cli CLI_NAME]

Without --cli, generates graphs for all discovered CLI programs.
With --graph, also generates PNG via mmdc (Mermaid CLI) if available.
"""

import argparse, importlib, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import explr

OUT_DIR = 'docs/internal/code-index'
CLI_DIR = 'src/akkapros/cli'

EXCLUDE_MODULES = (
    'explr', 'builtins', 'functools', 'itertools', 'collections',
    're', 'json', 'csv', 'pathlib', 'logging', 'argparse',
)


def discover_clis():
    """Dynamically list CLI modules from src/akkapros/cli/ (excluding __init__)."""
    cli_path = os.path.join(os.path.dirname(__file__), '..', CLI_DIR)
    clis = []
    for f in sorted(os.listdir(cli_path)):
        if f.startswith('_') or f.startswith('__'):
            continue
        if f.endswith('.py'):
            clis.append(f[:-3])  # strip .py
    return clis


def build_harness(cli_name):
    """Build a zero-arg harness that imports and runs the CLI's main()."""
    import_path = f'src.akkapros.cli.{cli_name}'

    def harness():
        mod = importlib.import_module(import_path)
        # Save and override sys.argv for the CLI
        old_argv = sys.argv
        sys.argv = [f'akkapros-{cli_name}']
        try:
            if hasattr(mod, 'main'):
                mod.main()
        except (SystemExit, Exception):
            # CLI may exit on missing args or fail — that's fine, we captured the trace
            pass
        finally:
            sys.argv = old_argv

    return harness


def gen_cli_graph(cli_name, make_png=False):
    """Generate a call graph for one CLI by tracing its main()."""
    harness = build_harness(cli_name)
    stem = f'{cli_name}_callgraph'
    out_path = os.path.join(OUT_DIR, f'{stem}.mmd')

    print(f'  Tracing {cli_name}...')

    try:
        call_graph = explr.trace_func(
            harness,
            max_depth=None,
            no_stdlib=True,
        )
    except Exception as e:
        print(f'    ERROR: {e}')
        return

    if not call_graph.nodes:
        print(f'    (no calls captured)')
        return

    print(f'    captured {len(call_graph.nodes)} nodes, {len(call_graph.edges)} edges')

    explr.render_mermaid(
        call_graph,
        output_path=out_path,
        target_name=cli_name,
        exclude_modules=EXCLUDE_MODULES,
    )
    print(f'    -> {out_path}')

    if make_png:
        _render_png(out_path, stem)


def _render_png(mmd_path, stem):
    """Convert Mermaid to PNG using mmdc (Mermaid CLI) if available."""
    import shutil, subprocess
    mmdc = shutil.which('mmdc')
    if mmdc:
        png_path = os.path.join(OUT_DIR, f'{stem}.png')
        subprocess.run([
            mmdc, '-i', mmd_path, '-o', png_path,
            '-b', 'white', '-w', '1200',
        ], capture_output=True)
        print(f'    -> {png_path}')
    else:
        print(f'    (mmdc not found, skipping PNG)')


def main():
    ap = argparse.ArgumentParser(description='Generate call graphs for akkapros CLI programs')
    ap.add_argument('--graph', action='store_true', help='Also generate PNG via mmdc')
    ap.add_argument('--cli', help='Single CLI name (e.g. fullprosmaker)')
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    clis = discover_clis()
    if args.cli:
        if args.cli not in clis:
            print(f'Unknown CLI: {args.cli}')
            print(f'Discovered: {", ".join(clis)}')
            sys.exit(1)
        clis = [args.cli]

    for name in clis:
        gen_cli_graph(name, make_png=args.graph)

    print(f'\nDone. Output in {OUT_DIR}/')


if __name__ == '__main__':
    main()
