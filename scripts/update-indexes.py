#!/usr/bin/env python3
"""Update docs/internal indexes from source files.

The script preserves the header portion of existing index files and supports
the canonical governance identifier family documented in docs/internal/README.md:
000-999, then A00-A99, B00-B99, and so on.
"""

from dataclasses import dataclass
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ADR_DIR = DOCS / "internal" / "adr"
CR_DIR = DOCS / "internal" / "cr"
REQ_DIR = DOCS / "internal" / "req"
REVIEW_DIR = DOCS / "internal" / "review"

GOVERNANCE_ID_RE = re.compile(r"^(?:\d{3}|[A-Z]\d{2})$")
STANDARD_RECORD_RE = re.compile(r"^(?P<identifier>(?:\d{3}|[A-Z]\d{2}))-(?P<slug>.+)\.md$")
TITLE_PREFIX_RE = re.compile(r"^(?:\d{1,3}|[A-Z]\d{2})\.\s*")
ALLOWED_SUPPORT_FILES = {
    "adr": {"index.md", "README.md", "000-adr-template.md"},
    "cr": {"index.md", "README.md", "000-cr-template.md"},
    "req": {"index.md", "README.md", "000-req-template.md"},
    "review": {"index.md", "README.md", "000-review-template.md"},
}


@dataclass(frozen=True)
class GovernanceRecord:
    identifier: str
    path: Path
    slug: str | None
    sort_value: int


def normalize_governance_id(identifier: str) -> str:
    normalized = identifier.strip().upper()
    if not GOVERNANCE_ID_RE.fullmatch(normalized):
        raise ValueError(f"Invalid governance identifier: {identifier!r}")
    return normalized


def governance_id_sort_value(identifier: str) -> int:
    normalized = normalize_governance_id(identifier)
    if normalized.isdigit():
        return int(normalized)
    return 1000 + (ord(normalized[0]) - ord("A")) * 100 + int(normalized[1:])


def strip_title_prefix(title: str) -> str:
    return TITLE_PREFIX_RE.sub("", title).strip()


def discover_standard_records(directory: Path, kind: str) -> tuple[list[GovernanceRecord], list[str]]:
    records: list[GovernanceRecord] = []
    warnings: list[str] = []
    allowed_names = ALLOWED_SUPPORT_FILES[kind]

    for path in sorted(directory.glob("*.md")):
        if path.name in allowed_names:
            continue
        match = STANDARD_RECORD_RE.fullmatch(path.name)
        if not match:
            warnings.append(f"Unsupported {kind.upper()} governance file name: {path.name}")
            continue
        identifier = match.group("identifier")
        records.append(
            GovernanceRecord(
                identifier=identifier,
                path=path,
                slug=match.group("slug"),
                sort_value=governance_id_sort_value(identifier),
            )
        )

    return records, warnings


def discover_review_records(directory: Path) -> tuple[list[GovernanceRecord], list[str]]:
    records: list[GovernanceRecord] = []
    warnings: list[str] = []
    allowed_names = ALLOWED_SUPPORT_FILES["review"]

    for path in sorted(directory.glob("*.md")):
        if path.name in allowed_names:
            continue
        parsed = parse_review_record_name(path.name)
        if parsed is None:
            warnings.append(f"Unsupported REVIEW governance file name: {path.name}")
            continue
        identifier, slug = parsed
        records.append(
            GovernanceRecord(
                identifier=identifier,
                path=path,
                slug=slug,
                sort_value=governance_id_sort_value(identifier),
            )
        )

    return records, warnings


def parse_review_record_name(filename: str) -> tuple[str, str | None] | None:
    stem = filename[:-3] if filename.endswith(".md") else filename
    prefix_match = re.fullmatch(r"review-(?P<identifier>(?:\d{3}|[A-Z]\d{2}))(?:-(?P<slug>.+))?", stem)
    if prefix_match:
        return prefix_match.group("identifier"), prefix_match.group("slug")

    suffix_match = re.fullmatch(r"(?P<identifier>(?:\d{3}|[A-Z]\d{2}))-review(?:-(?P<slug>.+))?", stem)
    if suffix_match:
        return suffix_match.group("identifier"), suffix_match.group("slug")

    titled_suffix_match = re.fullmatch(r"(?P<identifier>(?:\d{3}|[A-Z]\d{2}))-(?P<slug>.+)-review", stem)
    if titled_suffix_match:
        return titled_suffix_match.group("identifier"), titled_suffix_match.group("slug")

    return None


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
        m = re.match(r"\s*status:\s*(.+)", line, re.IGNORECASE)
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


def build_adr_index(adr_dir: Path | None = None, index_path: Path | None = None) -> list[str]:
    adr_dir = ADR_DIR if adr_dir is None else adr_dir
    index_path = adr_dir / "index.md" if index_path is None else index_path
    header = read_header(index_path, entry_starts=("- ",))
    if not header.strip():
        header = "# ADR Index\n\nThis index lists architectural decision records (ADRs). It is maintained by `scripts/update-indexes.py`.\n\n| ID | Title | Status |\n|----|-------|--------|\n\n"

    entries = []
    records, warnings = discover_standard_records(adr_dir, "adr")
    for record in records:
        p = record.path
        status, title = extract_status_and_title(p)
        if title:
            title = strip_title_prefix(title)
        else:
            title = (record.slug or p.stem).replace("-", " ")
        display = f"{record.identifier}. {title}"
        entry = f"- [{display}]({p.name}) - {status or 'Unknown'}"
        entries.append((record.sort_value, entry))

    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n"
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")
    return warnings


def build_cr_index(cr_dir: Path | None = None, index_path: Path | None = None) -> list[str]:
    cr_dir = CR_DIR if cr_dir is None else cr_dir
    index_path = cr_dir / "index.md" if index_path is None else index_path
    header = read_header(index_path, entry_starts=("[", "- "))
    if not header.strip():
        header = "# CR Index\n\nThis index lists Change Requests. It is maintained by `scripts/update-indexes.py`.\n\n"

    entries = []
    records, warnings = discover_standard_records(cr_dir, "cr")
    for record in records:
        p = record.path
        slug_title = (record.slug or p.stem).replace("-", " ")
        status = None
        title = None
        text = p.read_text(encoding="utf-8")
        for line in text.splitlines()[:40]:
            m2 = re.match(r"\s*status:\s*(.+)", line, re.IGNORECASE)
            if m2:
                status = m2.group(1).strip()
            m3 = re.match(r"\s*#\s*Change Request:\s*(.+)", line)
            if m3:
                title = m3.group(1).strip()
        if title is None:
            title = slug_title
        display = f"{record.identifier}. {title}"
        entry = f"[{display}]({p.name}) - {status or 'Unknown'}"
        entries.append((record.sort_value, entry))

    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n"
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")
    return warnings


def build_review_index(review_dir: Path | None = None, index_path: Path | None = None) -> list[str]:
    review_dir = REVIEW_DIR if review_dir is None else review_dir
    index_path = review_dir / "index.md" if index_path is None else index_path
    header = read_header(index_path, entry_starts=("- ",))
    if not header.strip():
        header = "# Review Index\n\nThis index lists review documents. It is maintained by `scripts/update-indexes.py`.\n\n"

    entries = []
    records, warnings = discover_review_records(review_dir)
    for record in records:
        status, title = extract_status_and_title(record.path)
        if title:
            title = strip_title_prefix(title)
        else:
            title = (record.slug or record.path.stem).replace("-", " ")
        display = f"review-{record.identifier}. {title}"
        entry = f"- [{display}]({record.path.name})"
        entries.append((record.sort_value, entry))

    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n" if entries else ""
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")
    return warnings


def build_req_index(req_dir: Path | None = None, index_path: Path | None = None) -> list[str]:
    req_dir = REQ_DIR if req_dir is None else req_dir
    index_path = req_dir / "index.md" if index_path is None else index_path
    header = read_header(index_path, entry_starts=("- ",))
    if not header.strip():
        header = "# Req Index\n\nThis index lists requirement documents. It is maintained by `scripts/update-indexes.py`.\n\n"

    entries = []
    records, warnings = discover_standard_records(req_dir, "req")
    for record in records:
        status, title = extract_status_and_title(record.path)
        if title:
            title = strip_title_prefix(title)
        else:
            title = (record.slug or record.path.stem).replace("-", " ")
        display = f"{record.identifier}. {title}"
        entry = f"- [{display}]({record.path.name}) - {status or 'Unknown'}"
        entries.append((record.sort_value, entry))

    entries.sort(key=lambda x: x[0], reverse=True)
    body = "\n".join(e for _, e in entries) + "\n"
    index_path.write_text(header + body, encoding="utf-8")
    print(f"Updated {index_path}")
    return warnings


def emit_warnings(warnings: list[str]) -> None:
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)


def main():
    missing = [p for p in (ADR_DIR, CR_DIR, REQ_DIR, REVIEW_DIR) if not p.exists()]
    if missing:
        print("Error: expected docs/internal/adr, docs/internal/cr, docs/internal/req, and docs/internal/review directories.")
        for m in missing:
            print("  Missing:", m)
        sys.exit(1)
    warnings = []
    warnings.extend(build_adr_index())
    warnings.extend(build_cr_index())
    warnings.extend(build_review_index())
    warnings.extend(build_req_index())
    if warnings:
        emit_warnings(warnings)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

