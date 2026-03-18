#!/usr/bin/env python3
"""Simple Markdown link checker for the repository.

Checks relative links to files and optional heading anchors. Skips http(s) links.
Exits with non-zero code if any broken links are found.
"""
import re
import sys
from pathlib import Path
from urllib.parse import urldefrag


MD_GLOB = "**/*.md"


def slugify_anchor(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"[^a-z0-9\-\_]+", "", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-_")


link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def check_file(md_path: Path, repo_root: Path):
    text = md_path.read_text(encoding="utf-8")
    errors = []
    for m in link_re.finditer(text):
        target = m.group(2).strip()
        if target.startswith("http://") or target.startswith("https://"):
            continue
        if target.startswith("mailto:"):
            continue
        # allow pure anchors
        if target.startswith("#"):
            frag = target[1:]
            # check anchor in same file
            anchors = [slugify_anchor(h) for h in re.findall(r"^#+\s*(.*)$", text, flags=re.M)]
            if slugify_anchor(frag) not in anchors:
                errors.append(f"Missing anchor #{frag} in {md_path}")
            continue

        # resolve relative path against md_path
        target_path_str, frag = urldefrag(target)
        target_path = (md_path.parent / target_path_str).resolve()
        try:
            # ensure it's inside repo
            target_path.relative_to(repo_root.resolve())
        except Exception:
            # external file path — just skip existence check
            continue

        if not target_path.exists():
            errors.append(f"Missing target file: {target_path} (linked from {md_path})")
            continue

        if frag:
            tgt_text = target_path.read_text(encoding="utf-8")
            anchors = [slugify_anchor(h) for h in re.findall(r"^#+\s*(.*)$", tgt_text, flags=re.M)]
            if slugify_anchor(frag) not in anchors:
                errors.append(f"Missing anchor #{frag} in {target_path} (linked from {md_path})")

    return errors


def main():
    repo_root = Path(__file__).resolve().parent.parent
    md_files = list(repo_root.glob(MD_GLOB))
    total_errors = []
    for md in md_files:
        errs = check_file(md, repo_root)
        total_errors.extend(errs)

    if total_errors:
        print("Broken links / anchors found:")
        for e in total_errors:
            print("- ", e)
        sys.exit(2)

    print("No broken relative Markdown links or anchors detected.")


if __name__ == "__main__":
    main()
