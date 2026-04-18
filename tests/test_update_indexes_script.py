from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "update-indexes.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("update_indexes_script", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_cr(path: Path, status: str, title: str) -> None:
    path.write_text(
        f"---\nstatus: {status}\n---\n\n# Change Request: {title}\n",
        encoding="utf-8",
    )


def _write_req(path: Path, status: str, title: str) -> None:
    path.write_text(
        f"---\nstatus: {status}\n---\n\n# Requirement: {title}\n",
        encoding="utf-8",
    )


def _write_adr(path: Path, status: str, title: str) -> None:
    path.write_text(
        f"---\nstatus: {status}\n---\n\n# {title}\n",
        encoding="utf-8",
    )


def _write_review(path: Path, title: str) -> None:
    path.write_text(f"# {title}\n", encoding="utf-8")


def test_governance_id_sort_value_supports_post_999_identifiers() -> None:
    module = _load_module()

    assert module.governance_id_sort_value("071") == 71
    assert module.governance_id_sort_value("999") == 999
    assert module.governance_id_sort_value("A00") == 1000
    assert module.governance_id_sort_value("A01") == 1001
    assert module.governance_id_sort_value("B00") == 1100


def test_build_cr_index_orders_mixed_identifier_families(tmp_path: Path) -> None:
    module = _load_module()
    cr_dir = tmp_path / "cr"
    cr_dir.mkdir()
    (cr_dir / "index.md").write_text("# CR Index\n\n", encoding="utf-8")

    _write_cr(cr_dir / "071-earlier.md", "Approved", "Earlier Numeric")
    _write_cr(cr_dir / "999-last-numeric.md", "Done", "Last Numeric")
    _write_cr(cr_dir / "A00-first-postnumeric.md", "Draft", "First Post Numeric")

    warnings = module.build_cr_index(cr_dir=cr_dir)

    assert warnings == []
    lines = [line for line in (cr_dir / "index.md").read_text(encoding="utf-8").splitlines() if line.startswith("[")]
    assert lines == [
        "[A00. First Post Numeric](A00-first-postnumeric.md) - Draft",
        "[999. Last Numeric](999-last-numeric.md) - Done",
        "[071. Earlier Numeric](071-earlier.md) - Approved",
    ]


def test_build_review_index_supports_post_999_identifiers(tmp_path: Path) -> None:
    module = _load_module()
    review_dir = tmp_path / "review"
    review_dir.mkdir()
    (review_dir / "index.md").write_text("# Review Index\n\n", encoding="utf-8")

    _write_review(review_dir / "011-review.md", "Numeric Review")
    _write_review(review_dir / "review-A00.md", "Post Numeric Review")

    warnings = module.build_review_index(review_dir=review_dir)

    assert warnings == []
    lines = [line for line in (review_dir / "index.md").read_text(encoding="utf-8").splitlines() if line.startswith("-")]
    assert lines == [
        "- [review-A00. Post Numeric Review](review-A00.md)",
        "- [review-011. Numeric Review](011-review.md)",
    ]


def test_build_review_index_supports_slugged_suffix_review_filenames(tmp_path: Path) -> None:
    module = _load_module()
    review_dir = tmp_path / "review"
    review_dir.mkdir()
    (review_dir / "index.md").write_text("# Review Index\n\n", encoding="utf-8")

    _write_review(review_dir / "002-frontmatter-data-review.md", "Frontmatter Data Review")
    _write_review(review_dir / "001-review.md", "Simple Review")

    warnings = module.build_review_index(review_dir=review_dir)

    assert warnings == []
    lines = [line for line in (review_dir / "index.md").read_text(encoding="utf-8").splitlines() if line.startswith("-")]
    assert lines == [
        "- [review-002. Frontmatter Data Review](002-frontmatter-data-review.md)",
        "- [review-001. Simple Review](001-review.md)",
    ]


def test_main_surfaces_malformed_governance_files(tmp_path: Path, capsys) -> None:
    module = _load_module()
    docs_internal = tmp_path / "docs" / "internal"
    adr_dir = docs_internal / "adr"
    cr_dir = docs_internal / "cr"
    req_dir = docs_internal / "req"
    review_dir = docs_internal / "review"
    for directory in (adr_dir, cr_dir, req_dir, review_dir):
        directory.mkdir(parents=True)

    (adr_dir / "index.md").write_text("# ADR Index\n\n", encoding="utf-8")
    (cr_dir / "index.md").write_text("# CR Index\n\n", encoding="utf-8")
    (req_dir / "index.md").write_text("# Req Index\n\n", encoding="utf-8")
    (review_dir / "index.md").write_text("# Review Index\n\n", encoding="utf-8")

    _write_adr(adr_dir / "048-governance.md", "Accepted", "48. Governance Alignment")
    _write_cr(cr_dir / "071-governance-housekeeping.md", "Draft", "Governance Housekeeping")
    _write_req(req_dir / "037-governance-alignment.md", "Draft", "Governance Alignment")
    _write_review(review_dir / "011-review.md", "Existing Review")
    (cr_dir / "bad-name.md").write_text("# Change Request: Bad Name\n", encoding="utf-8")

    module.ADR_DIR = adr_dir
    module.CR_DIR = cr_dir
    module.REQ_DIR = req_dir
    module.REVIEW_DIR = review_dir

    result = module.main()

    captured = capsys.readouterr()
    assert result == 1
    assert "WARNING: Unsupported CR governance file name: bad-name.md" in captured.err
