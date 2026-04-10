import os
import subprocess
import sys
from pathlib import Path

from akkapros.lib.frontmatter import split_frontmatter


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*module_and_args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "-m", *module_and_args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, (
        f"CLI failed: {' '.join(module_and_args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    return proc


def _write_atf(path: Path, tablet_id: str, title: str, lines: list[str]) -> None:
    content = [f"&{tablet_id} = {title}"]
    for idx, line in enumerate(lines, start=1):
        content.append(f"{idx}. %n {line}")
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def _read_frontmatter(path: Path):
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    return frontmatter, body


def test_append_pipeline_frontmatter_contract(tmp_path: Path) -> None:
    atf_one = tmp_path / "one.atf"
    atf_two = tmp_path / "two.atf"
    outdir = tmp_path / "out"
    prefix = "corpus"

    _write_atf(atf_one, "X000001", "Title One", ["šar gi-mir", "ana šarri"])
    _write_atf(atf_two, "X000002", "Title Two", ["bānu rabû"])

    _run_cli("akkapros.cli.atfparser", str(atf_one), "-p", prefix, "--outdir", str(outdir))
    _run_cli("akkapros.cli.atfparser", str(atf_two), "-p", prefix, "--outdir", str(outdir), "--append")

    proc_file = outdir / f"{prefix}_proc.txt"
    proc_frontmatter, proc_body = _read_frontmatter(proc_file)
    assert proc_frontmatter["file"]["title"] == "Title One | Title Two"
    assert proc_frontmatter["metadata"]["input_file_id"] is None
    assert proc_frontmatter["metadata"]["data"] == {}
    assert proc_body.count("\n") == 3

    _run_cli("akkapros.cli.syllabifier", str(proc_file), "-p", prefix, "--outdir", str(outdir))
    syl_file = outdir / f"{prefix}_syl.txt"
    syl_frontmatter, _ = _read_frontmatter(syl_file)
    assert syl_frontmatter["file"]["title"] == "Title One | Title Two"
    assert syl_frontmatter["metadata"]["data"] == {}

    _run_cli("akkapros.cli.prosmaker", str(syl_file), "-p", prefix, "--outdir", str(outdir), "--style", "sob")
    tilde_file = outdir / f"{prefix}_tilde.txt"
    tilde_frontmatter, _ = _read_frontmatter(tilde_file)
    assert tilde_frontmatter["metadata"]["data"] == {}

    _run_cli("akkapros.cli.phonetizer", str(tilde_file), "-p", prefix, "--outdir", str(outdir))
    phone_file = outdir / f"{prefix}_phone.txt"

    _run_cli(
        "akkapros.cli.metricalc",
        str(phone_file),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--table",
        "--json",
    )
    metrics_file = outdir / f"{prefix}_metrics.txt"
    metrics_frontmatter, _ = _read_frontmatter(metrics_file)
    assert "data" not in metrics_frontmatter["metadata"]

    _run_cli("akkapros.cli.printer", str(tilde_file), "-p", prefix, "--outdir", str(outdir), "--acute")
    acute_file = outdir / f"{prefix}_accent_acute.txt"
    acute_frontmatter, _ = _read_frontmatter(acute_file)
    assert acute_frontmatter["file"]["title"] == "Title One | Title Two"
    assert "data" not in acute_frontmatter["metadata"]