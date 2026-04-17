from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from akkapros.lib.docflow import sync_registered_flowcharts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or verify code-derived Mermaid flowcharts in user-facing docs.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when generated flowcharts do not match the current docs.",
    )
    args = parser.parse_args(argv)

    problems = sync_registered_flowcharts(check=args.check, repo_root=ROOT)
    if problems:
        stream = sys.stderr if args.check else sys.stdout
        for problem in problems:
            stream.write(problem + "\n")
        return 1

    if args.check:
        sys.stdout.write("Flowcharts are in sync.\n")
    else:
        sys.stdout.write("Flowcharts synchronized.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())