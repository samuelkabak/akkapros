#!/usr/bin/env python3
"""Packaging wrapper: sync docs then run isolated build.

Usage:
  python scripts/build_package.py [--outdir DIR] [--sdist] [--wheel]

This script ensures `docs/` is synced into `src/akkapros/docs/` before
building sdist/wheel. It invokes the existing `scripts/sync_docs.py` and
then runs `python -m build` with the provided arguments.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import os


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync docs and build distribution")
    parser.add_argument("--outdir", default="dist", help="Output directory for distributions")
    parser.add_argument("--sdist", action="store_true", help="Build sdist")
    parser.add_argument("--wheel", action="store_true", help="Build wheel")
    parser.add_argument("--no-isolation", action="store_true", help="Pass --no-isolation to build (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Run sync in dry-run mode and skip build")
    args, extra = parser.parse_known_args(argv)

    here = os.path.dirname(__file__) or os.getcwd()
    sync_script = os.path.join(here, "sync_docs.py")

    if not os.path.exists(sync_script):
        print(f"Sync script not found: {sync_script}")
        return 2

    sync_cmd = [sys.executable, sync_script]
    if args.dry_run:
        sync_cmd.append("--dry-run")

    print("Running doc sync:", " ".join(sync_cmd))
    subprocess.check_call(sync_cmd)

    if args.dry_run:
        print("Dry run: skipping build.")
        return 0

    build_cmd = [sys.executable, "-m", "build", "--outdir", args.outdir]
    if args.sdist and not args.wheel:
        build_cmd.append("--sdist")
    elif args.wheel and not args.sdist:
        build_cmd.append("--wheel")
    # if neither specified, build both (default)
    if args.no_isolation:
        build_cmd.append("--no-isolation")
    if extra:
        build_cmd.extend(extra)

    print("Running build:", " ".join(build_cmd))
    subprocess.check_call(build_cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
