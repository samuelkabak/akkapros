#!/usr/bin/env python3
"""Sync top-level docs/ into src/akkapros/docs/ for packaging.

Usage:
  python scripts/sync_docs.py [--dry-run]

This script is intended to be run before building a distribution so the
package includes the markdown docs under `src/akkapros/docs/` while keeping
the canonical source at the repository root `docs/`.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys


def sync_docs(src: Path, dst: Path, dry_run: bool = False) -> int:
    if not src.exists():
        print(f"Source docs directory not found: {src}")
        return 2

    # If repository stores docs under docs/akkapros, prefer that subdir
    candidate = src / "akkapros"
    if candidate.exists() and candidate.is_dir():
        source_dir = candidate
    else:
        source_dir = src

    if dry_run:
        print(f"DRY RUN: would remove and copy {source_dir} -> {dst}")
        return 0

    if dst.exists():
        print(f"Removing existing target: {dst}")
        shutil.rmtree(dst)

    print(f"Copying {source_dir} -> {dst}")
    # copytree requires dst not to exist and copies the full tree
    shutil.copytree(source_dir, dst)
    print("Sync complete.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync docs into package before build")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without modifying files")
    parser.add_argument("--src", default="docs", help="Source docs directory (default: docs)")
    parser.add_argument("--dst", default="src/akkapros/docs", help="Destination inside package")
    args = parser.parse_args(argv)

    src = Path(args.src)
    dst = Path(args.dst)

    try:
        return sync_docs(src, dst, args.dry_run)
    except Exception as e:
        print("Error while syncing docs:", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
