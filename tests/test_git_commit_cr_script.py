from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "git-commit-cr.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("git_commit_cr_script", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_extract_cr_title_reads_change_request_heading(tmp_path: Path) -> None:
    module = _load_module()
    cr_file = tmp_path / "024-sample.md"
    cr_file.write_text(
        "---\nstatus: Done\n---\n\n# Change Request: Sample Title\n",
        encoding="utf-8",
    )

    assert module.extract_cr_title(cr_file) == "Sample Title"


def test_find_cr_file_requires_exactly_one_match(tmp_path: Path) -> None:
    module = _load_module()
    (tmp_path / "024-one.md").write_text("# Change Request: One\n", encoding="utf-8")
    (tmp_path / "024-two.md").write_text("# Change Request: Two\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="Expected exactly one CR file"):
        module.find_cr_file("024", cr_dir=tmp_path)


def test_main_builds_commit_message_and_runs_git(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_module()
    cr_dir = tmp_path / "docs" / "internal" / "cr"
    cr_dir.mkdir(parents=True)
    (cr_dir / "024-minimize-frontmatter.md").write_text(
        "# Change Request: Minimize Frontmatter and Enable Source-Flexible Stage Inputs\n",
        encoding="utf-8",
    )

    calls: list[tuple[list[str], str]] = []

    class Completed:
        returncode = 0

    def fake_run(cmd: list[str], cwd: str):
        calls.append((cmd, cwd))
        return Completed()

    monkeypatch.setattr(module, "CR_DIR", cr_dir)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda prompt: "Y")

    result = module.main(["024"])

    captured = capsys.readouterr()
    assert result == 0
    assert "---- CR SUBMITTER ---" in captured.out
    assert "Ensure all and only files related to CR-024 are staged" in captured.out
    assert 'git commit -m "Implement CR-024: Minimize Frontmatter and Enable Source-Flexible Stage Inputs"' in captured.out
    assert calls == [
        (
            [
                "git",
                "commit",
                "-m",
                "Implement CR-024: Minimize Frontmatter and Enable Source-Flexible Stage Inputs",
            ],
            str(module.ROOT),
        )
    ]


@pytest.mark.parametrize("response", ["", "n", "N", "abc"])
def test_main_exits_without_commit_on_default_or_no(
    response: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_module()
    cr_dir = tmp_path / "docs" / "internal" / "cr"
    cr_dir.mkdir(parents=True)
    (cr_dir / "024-minimize-frontmatter.md").write_text(
        "# Change Request: Minimize Frontmatter and Enable Source-Flexible Stage Inputs\n",
        encoding="utf-8",
    )

    calls: list[tuple[list[str], str]] = []

    def fake_run(cmd: list[str], cwd: str):
        calls.append((cmd, cwd))
        raise AssertionError("git commit should not run when the user declines")

    monkeypatch.setattr(module, "CR_DIR", cr_dir)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", lambda prompt: response)

    result = module.main(["024"])

    captured = capsys.readouterr()
    assert result == 0
    assert "exit witout commit" in captured.out
    assert calls == []


def test_main_rejects_non_three_digit_number(capsys: pytest.CaptureFixture[str]) -> None:
    module = _load_module()

    result = module.main(["24"])

    captured = capsys.readouterr()
    assert result == 2
    assert "CR number must be exactly three digits" in captured.err