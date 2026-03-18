#!/usr/bin/env python3
"""Migrate legacy bracket escapes to CR-005 double-brace escapes.

Default behavior converts only wrapped legacy escapes in syllabifier output:
    ⟦ [text] ⟧  ->  ⟦{{text}}⟧

Optional --convert-bare also converts plain bracket chunks:
    [text] -> {{text}}
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

OPEN_ESCAPE = "⟦"
CLOSE_ESCAPE = "⟧"

WRAPPED_RE = re.compile(r"⟦\s*\[(.*?)\]\s*⟧", re.DOTALL)
BARE_RE = re.compile(r"\[(.*?)\]", re.DOTALL)


def _wrapped_repl(match: re.Match[str]) -> str:
    payload = match.group(1).strip()
    return f"{OPEN_ESCAPE}{{{{{payload}}}}}{CLOSE_ESCAPE}"


def _bare_repl(match: re.Match[str]) -> str:
    payload = match.group(1).strip()
    return f"{{{{{payload}}}}}"


def migrate_text(text: str, convert_bare: bool) -> str:
    migrated = WRAPPED_RE.sub(_wrapped_repl, text)
    if convert_bare:
        migrated = BARE_RE.sub(_bare_repl, migrated)
    return migrated


def migrate_file(path: Path, in_place: bool, output: Path | None, convert_bare: bool) -> Path:
    original = path.read_text(encoding="utf-8")
    migrated = migrate_text(original, convert_bare)

    if in_place:
        target = path
    else:
        target = output if output is not None else path.with_name(f"{path.stem}_cr005{path.suffix}")

    target.write_text(migrated, encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate legacy [ ] escapes to CR-005 {{ }} syntax")
    parser.add_argument("input", help="Input text file")
    parser.add_argument("-o", "--output", help="Output file (default: <input>_cr005<suffix>)")
    parser.add_argument("--in-place", action="store_true", help="Rewrite input file in place")
    parser.add_argument(
        "--convert-bare",
        action="store_true",
        help="Also convert bare [text] chunks (off by default for safety)",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"Input file not found: {in_path}")

    out_path = Path(args.output) if args.output else None
    written = migrate_file(in_path, args.in_place, out_path, args.convert_bare)
    print(f"Migrated: {in_path}")
    print(f"Written : {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
