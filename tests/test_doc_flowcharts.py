from __future__ import annotations

from pathlib import Path

import pytest

from akkapros.lib.docflow import (
    FLOWCHART_TARGETS,
    FlowchartSyncError,
    FlowchartTarget,
    render_mermaid_block,
    sync_flowchart_block,
    sync_registered_flowcharts,
    validate_flowchart_target,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_all_registered_flowchart_targets_validate_against_live_code() -> None:
    for target in FLOWCHART_TARGETS:
        validate_flowchart_target(target)


def test_render_mermaid_block_uses_mermaid_fence() -> None:
    target = FlowchartTarget(
        key="sample",
        doc_path="docs/sample.md",
        validator=lambda: None,
        mermaid_lines=("flowchart TD", "    A[\"Start\"] --> B[\"Finish\"]"),
    )

    rendered = render_mermaid_block(target)

    assert rendered.startswith("```mermaid\nflowchart TD\n")
    assert rendered.endswith("\n```")


def test_sync_flowchart_block_replaces_content_between_markers() -> None:
    target = FlowchartTarget(
        key="sample",
        doc_path="docs/sample.md",
        validator=lambda: None,
        mermaid_lines=("flowchart TD", "    A[\"Start\"] --> B[\"Finish\"]"),
    )
    original = (
        "# Title\n\n"
        "<!-- GENERATED FLOWCHART: sample -->\n"
        "old content\n"
        "<!-- END GENERATED FLOWCHART: sample -->\n"
    )

    updated = sync_flowchart_block(original, target)

    assert "old content" not in updated
    assert "```mermaid" in updated
    assert "A[\"Start\"] --> B[\"Finish\"]" in updated


def test_sync_flowchart_block_requires_markers() -> None:
    target = FlowchartTarget(
        key="sample",
        doc_path="docs/sample.md",
        validator=lambda: None,
        mermaid_lines=("flowchart TD",),
    )

    with pytest.raises(FlowchartSyncError, match="missing the required flowchart markers"):
        sync_flowchart_block("# Title\n", target)


def test_sync_registered_flowcharts_writes_generated_block(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    doc_file = docs_dir / "sample.md"
    doc_file.write_text(
        "# Title\n\n"
        "<!-- GENERATED FLOWCHART: sample -->\n"
        "<!-- END GENERATED FLOWCHART: sample -->\n",
        encoding="utf-8",
    )
    target = FlowchartTarget(
        key="sample",
        doc_path="docs/sample.md",
        validator=lambda: None,
        mermaid_lines=("flowchart TD", "    A[\"Start\"] --> B[\"Finish\"]"),
    )

    problems = sync_registered_flowcharts(check=False, repo_root=tmp_path, targets=(target,))

    assert problems == []
    synced = doc_file.read_text(encoding="utf-8")
    assert "```mermaid" in synced
    assert "A[\"Start\"] --> B[\"Finish\"]" in synced


def test_sync_registered_flowcharts_check_reports_out_of_sync(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    doc_file = docs_dir / "sample.md"
    doc_file.write_text(
        "# Title\n\n"
        "<!-- GENERATED FLOWCHART: sample -->\n"
        "stale\n"
        "<!-- END GENERATED FLOWCHART: sample -->\n",
        encoding="utf-8",
    )
    target = FlowchartTarget(
        key="sample",
        doc_path="docs/sample.md",
        validator=lambda: None,
        mermaid_lines=("flowchart TD", "    A[\"Start\"] --> B[\"Finish\"]"),
    )

    problems = sync_registered_flowcharts(check=True, repo_root=tmp_path, targets=(target,))

    assert problems == [
        "Generated Mermaid block is out of sync for docs/sample.md; run scripts/sync_doc_flowcharts.py"
    ]


def test_repo_docs_flowcharts_are_in_sync() -> None:
    problems = sync_registered_flowcharts(check=True, repo_root=REPO_ROOT)

    assert problems == []