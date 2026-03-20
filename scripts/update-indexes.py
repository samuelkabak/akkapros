#!/usr/bin/env python3
"""Update docs/internal/adr/index.md and docs/internal/cr/index.md from source files.

Behavior:
- ADR index: list markdown ADR files in `docs/internal/adr/*.md` (excluding `index.md` and templates),
  extract title and Status header, sort by number descending and write lines like:
  - [015. Title](015-slug.md) - Accepted

- CR index: list subdirectories in `docs/internal/cr/` that contain `CR.md`, extract CR number,
  title and Status, sort by number ascending and write lines like:
  [001. Title](001-slug/CR.md) - Draft

The script preserves the header portion of existing index files.
"""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ADR_DIR = DOCS / "internal" / "adr"
CR_DIR = DOCS / "internal" / "cr"
SPEC_DIR = DOCS / "internal" / "specs"
REVIEWS_DIR = DOCS / "internal" / "reviews"


def read_header(index_path, entry_starts):
    """Return the header text (lines before the first entry) from an index file.

    entry_starts: iterable of prefixes to detect the start of entries (e.g. ('- ', '[')).
    """
    if not index_path.exists():
        return ""
    text = index_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header_lines = []
    for ln in lines:
        if any(ln.lstrip().startswith(p) for p in entry_starts):
            break
        header_lines.append(ln)
    # preserve trailing blank line
    header = "\n".join(header_lines).rstrip() + "\n\n"
    return header


def extract_status_and_title(md_path):
    text = md_path.read_text(encoding="utf-8")
    status = None
    title = None
    for line in text.splitlines()[:40]:
        m = re.match(r"\s*Status:\s*(.+)", line)
        if m:
            status = m.group(1).strip()
            break
    for line in text.splitlines():
        m = re.match(r"\s*#\s*(.+)", line)
        if m:
            candidate = m.group(1).strip()
            # skip front-matter separator lines like '---'
            if re.fullmatch(r"-+", candidate):
                continue
            # require some letter content in the heading
            if not re.search(r"[A-Za-z]", candidate):
                continue
            title = candidate
            break
    return status, title


def build_adr_index():
    index_path = ADR_DIR / "index.md"
    header = read_header(index_path, entry_starts=("- ",))
    if not header.strip():
        header = "# ADR Index\n\nThis index lists architectural decision records (ADRs). It is maintained by `scripts/update-indexes.py`.\n\n| ID | Title | Status |\n|----|-------|--------|\n\n"

    entries = []
    for p in ADR_DIR.glob("*.md"):
        if p.name in ("index.md", "000-adr-template.md"):
            continue
        m = re.match(r"^(\d{3})-(.+)\.md$", p.name)
        if not m:
            continue
        num = int(m.group(1))
        status, title = extract_status_and_title(p)
        if title:
            # remove leading numeric prefix in title if present
            title = re.sub(r"^\d+\.\s*", "", title)
        else:
            title = m.group(2).replace("-", " ")
        display = f"{num:03d}. {title}"
        entry = f"- [{display}]({p.name}) - {status or 'Unknown'}"
        entries.append((num, entry))

    # Latest ADRs first (descending number)
    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n"
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")


def build_cr_index():
    index_path = CR_DIR / "index.md"
    header = read_header(index_path, entry_starts=("[", "- "))
    if not header.strip():
        header = "# CR Index\n\nThis index lists Change Requests. It is maintained by `scripts/update-indexes.py`.\n\n"

    entries = []
    for d in sorted(CR_DIR.iterdir()):
        if not d.is_dir():
            continue
        # skip template or example directories
        if d.name.startswith("000-"):
            continue
        cr_md = d / "CR.md"
        if not cr_md.exists():
            continue
        # try to infer numeric id from directory name or CR-ID metadata
        mdir = re.match(r"^(\d{3})-", d.name)
        num = int(mdir.group(1)) if mdir else None
        status = None
        title = None
        text = cr_md.read_text(encoding="utf-8")
        for line in text.splitlines()[:40]:
            m = re.match(r"\s*CR-ID:\s*CR-(\d{3})", line)
            if m and num is None:
                num = int(m.group(1))
            m2 = re.match(r"\s*Status:\s*(.+)", line)
            if m2:
                status = m2.group(1).strip()
            m3 = re.match(r"\s*#\s*Change Request:\s*(.+)", line)
            if m3:
                title = m3.group(1).strip()
        if title is None:
            # fallback: use directory label
            title = re.sub(r"^\d+-", "", d.name).replace("-", " ")
        if num is None:
            # fallback numeric sort key: attempt to parse leading digits from dir
            mo = re.match(r"^(\d{1,3})", d.name)
            num = int(mo.group(1)) if mo else 0
        display = f"{num:03d}. {title}"
        entry = f"[{display}]({d.name}/CR.md) - {status or 'Unknown'}"
        entries.append((num, entry))

    # CRs: list latest first (descending numeric order)
    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n"
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")


def main():
    missing = [p for p in (ADR_DIR, CR_DIR, SPEC_DIR, REVIEWS_DIR) if not p.exists()]
    if missing:
        print("Error: expected docs/internal/adr, docs/internal/cr and docs/internal/specs directories.")
        for m in missing:
            print("  Missing:", m)
        sys.exit(1)
    build_adr_index()
    build_cr_index()
    build_reviews_index()
    build_spec_index()


def build_reviews_index():
    index_path = REVIEWS_DIR / "index.md"
    header = read_header(index_path, entry_starts=("- ",))
    if not header.strip():
        header = "# Review Index\n\nThis index lists review documents. It is maintained by `scripts/update-indexes.py`.\n\n"

    entries = []
    for p in REVIEWS_DIR.glob("*.md"):
        if p.name == "index.md":
            continue
        # skip template or example review files (000-...)
        if p.name.startswith("000-"):
            continue
        # Accept either 'review-001.md' or '001-review.md' naming conventions
        m = re.match(r"^review-(\d{1,3})(?:-(.+))?\.md$", p.name)
        if not m:
            m2 = re.match(r"^(\d{1,3})-review(?:-(.+))?\.md$", p.name)
            if not m2:
                continue
            num = int(m2.group(1))
            remainder = m2.group(2)
        else:
            num = int(m.group(1))
            remainder = m.group(2)
        status, title = extract_status_and_title(p)
        if title:
            title = re.sub(r"^\d+\.\s*", "", title)
        else:
            title = (remainder or p.stem).replace("-", " ")
        display = f"review-{num:03d}. {title}"
        entry = f"- [{display}]({p.name}) - {status or 'Unknown'}"
        entries.append((num, entry))

    # Reviews: list latest first (descending numeric order)
    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n" if entries else ""
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")


def build_spec_index():
    index_path = SPEC_DIR / "index.md"
    header = read_header(index_path, entry_starts=("- ",))
    if not header.strip():
        header = "# Spec Index\n\nThis index lists requirement/specification documents. It is maintained by `scripts/update-indexes.py`.\n\n| ID | Title | Status | Priority |\n|----|-------|--------|----------|\n\n"

    entries = []
    for p in SPEC_DIR.glob("*.md"):
        if p.name in ("index.md", "000-req-template.md"):
            continue
        m = re.match(r"^(\d{3})-(.+)\.md$", p.name)
        if not m:
            continue
        num = int(m.group(1))
        status = None
        title = None
        # extract Status and title
        status, title = extract_status_and_title(p)
        if title:
            title = re.sub(r"^\d+\.\s*", "", title)
        else:
            title = m.group(2).replace("-", " ")
        display = f"{num:03d}. {title}"
        entry = f"- [{display}]({p.name}) - {status or 'Unknown'}"
        entries.append((num, entry))

    # Specs: list latest first (descending numeric order)
    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n"
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")


if __name__ == '__main__':
    main()

