#!/usr/bin/env python3
"""Update release-notes/unreleased.md with commits since a base ref.

Usage:
  python scripts/update_unreleased.py [--base TAG_OR_REF]

Defaults to base tag `v1.0.1`. The script replaces the "Commits since release"
section in `release-notes/unreleased.md` with a bullet list of commits
(`- `hash` (YYYY-MM-DD) — message`).

This is intended as a convenience for maintainers preparing release notes.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from typing import List


ROOT = os.path.dirname(os.path.dirname(__file__))
RELEASE_FILE = os.path.join(ROOT, "release-notes", "unreleased.md")


def git_commits(base: str) -> List[str]:
    cmd = [
        "git",
        "log",
        f"--pretty=format:%h %ad %s",
        "--date=short",
        f"{base}..HEAD",
    ]
    try:
        out = subprocess.check_output(cmd, cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("git command failed:", e.output, file=sys.stderr)
        raise
    lines = [ln.rstrip() for ln in out.splitlines() if ln.strip()]
    return lines


def format_commits(base: str, commits: List[str]) -> str:
    header = f"Commits since release `{base}`:\n\n"
    if not commits:
        return header + "- (no commits)\n\n"
    bullets = []
    for ln in commits:
        # ln: "hash YYYY-MM-DD message"
        m = re.match(r"^(?P<h>[0-9a-f]+) (?P<d>\d{4}-\d{2}-\d{2}) (?P<s>.*)$", ln)
        if m:
            bullets.append(f"- `{m.group('h')}` ({m.group('d')}) — {m.group('s')}")
        else:
            bullets.append(f"- `{ln}`")
    return header + "\n".join(bullets) + "\n\n"


def replace_section(mdtext: str, new_section: str) -> str:
    # Find the line that begins with "Commits since release"
    pattern = re.compile(r"^Commits since release .*:$", re.MULTILINE)
    m = pattern.search(mdtext)
    if not m:
        # If not found, append the section after the first header
        return mdtext.strip() + "\n\n" + new_section
    start = m.start()
    # Find next top-level header '## ' after the match
    next_header = re.search(r"^##\s", mdtext[m.end():], re.MULTILINE)
    if next_header:
        end = m.end() + next_header.start()
    else:
        end = len(mdtext)
    before = mdtext[:start]
    after = mdtext[end:]
    # Ensure spacing
    return before.rstrip() + "\n\n" + new_section + after.lstrip()


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="v1.0.1", help="Base ref/tag to list commits since (default: v1.0.1)")
    args = p.parse_args(argv)

    if not os.path.isfile(RELEASE_FILE):
        print(f"Release notes file not found: {RELEASE_FILE}", file=sys.stderr)
        return 2

    commits = git_commits(args.base)
    new_section = format_commits(args.base, commits)

    with open(RELEASE_FILE, "r", encoding="utf-8") as fh:
        md = fh.read()

    updated = replace_section(md, new_section)

    with open(RELEASE_FILE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(updated)

    print(f"Updated {RELEASE_FILE} with {len(commits)} commits since {args.base}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
