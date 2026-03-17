#!/usr/bin/env python3
"""Update docs/adr/index.md and docs/cr/index.md from source files.

Behavior:
- ADR index: list markdown ADR files in `docs/adr/*.md` (excluding `index.md` and templates),
  extract title and Status header, sort by number descending and write lines like:
  - [015. Title](015-slug.md) - Accepted

- CR index: list subdirectories in `docs/cr/` that contain `CR.md`, extract CR number,
  title and Status, sort by number ascending and write lines like:
  [001. Title](001-slug/CR.md) - Draft

The script preserves the header portion of existing index files.
"""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ADR_DIR = DOCS / "adr"
CR_DIR = DOCS / "cr"


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

    # CRs: keep ascending numeric order (older first)
    entries.sort(key=lambda x: x[0])
    body = "\n".join(e for _, e in entries) + "\n"
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")


def main():
    if not ADR_DIR.exists() or not CR_DIR.exists():
        print("Error: expected docs/adr and docs/cr directories under repo root.")
        sys.exit(1)
    build_adr_index()
    build_cr_index()


if __name__ == '__main__':
    main()
