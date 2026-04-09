import os
import subprocess
import sys
from pathlib import Path

from akkapros.lib.frontmatter import split_frontmatter
from akkapros.lib import print as printlib


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PROC = REPO_ROOT / "tests" / "integration_refs" / "stage_pipeline" / "expected_e2e_proc.txt"


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


def _read_frontmatter(path: Path) -> tuple[dict, str]:
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    return frontmatter, body


def test_printer_default_renders_spaces_and_records_false(tmp_path: Path) -> None:
    tilde_file = tmp_path / "sample_tilde.txt"
    tilde_file.write_text("gi·mir+dad~·mē\n", encoding="utf-8")

    _run_cli(
        "akkapros.cli.printer",
        str(tilde_file),
        "-p",
        "sample",
        "--outdir",
        str(tmp_path),
        "--acute",
        "--bold",
        "--xar",
    )

    acute_frontmatter, acute_body = _read_frontmatter(tmp_path / "sample_accent_acute.txt")
    bold_frontmatter, bold_body = _read_frontmatter(tmp_path / "sample_accent_bold.md")
    xar_frontmatter, xar_body = _read_frontmatter(tmp_path / "sample_accent_xar.txt")
    plain_xar_frontmatter, plain_xar_body = _read_frontmatter(tmp_path / "sample_xar.txt")

    assert acute_frontmatter["metadata"]["options"]["print_merger"] is False
    assert bold_frontmatter["metadata"]["options"]["print_merger"] is False
    assert xar_frontmatter["metadata"]["options"]["print_merger"] is False
    assert plain_xar_frontmatter["metadata"]["options"]["print_merger"] is False
    assert acute_body == "gimir dad´mē\n"
    assert bold_body == "gimir **dad**mē\n"
    assert xar_body == "gimir dad´mee\n"
    assert plain_xar_body == "gimir dadmee\n"


def test_printer_print_merger_preserves_visible_connector(tmp_path: Path) -> None:
    tilde_file = tmp_path / "sample_tilde.txt"
    tilde_file.write_text("gi·mir+dad~·mē\n", encoding="utf-8")

    _run_cli(
        "akkapros.cli.printer",
        str(tilde_file),
        "-p",
        "sample",
        "--outdir",
        str(tmp_path),
        "--acute",
        "--bold",
        "--xar",
        "--print-merger",
    )

    acute_frontmatter, acute_body = _read_frontmatter(tmp_path / "sample_accent_acute.txt")
    bold_frontmatter, bold_body = _read_frontmatter(tmp_path / "sample_accent_bold.md")
    xar_frontmatter, xar_body = _read_frontmatter(tmp_path / "sample_accent_xar.txt")
    plain_xar_frontmatter, plain_xar_body = _read_frontmatter(tmp_path / "sample_xar.txt")

    assert acute_frontmatter["metadata"]["options"]["print_merger"] is True
    assert bold_frontmatter["metadata"]["options"]["print_merger"] is True
    assert xar_frontmatter["metadata"]["options"]["print_merger"] is True
    assert plain_xar_frontmatter["metadata"]["options"]["print_merger"] is True
    assert acute_body == "gimir‿dad´mē\n"
    assert bold_body == "gimir‿**dad**mē\n"
    assert xar_body == "gimir‿dad´mee\n"
    assert plain_xar_body == "gimir dadmee\n"


def test_convert_line_dearmors_pivot_punctuation_only_at_render_time() -> None:
    tilde = "gi·mir+dad~·mē⟦ : ⟧šar"

    assert printlib.convert_line(tilde, "acute") == "gimir dad´mē : šar"
    assert printlib.convert_line(tilde, "bold") == "gimir **dad**mē : šar"


def test_convert_line_accepts_internal_merge_connector() -> None:
    tilde = "gi·mir&dad~·mē"

    assert printlib.convert_line(tilde, "acute") == "gimir dad´mē"
    assert printlib.convert_line(tilde, "ipa") == "gi.mir.ˈdadː.meː"


def test_fullprosmaker_default_print_merger_false(tmp_path: Path) -> None:
    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p",
        "sample",
        "--outdir",
        str(tmp_path),
        "--print-acute",
        "--print-bold",
        "--print-xar",
        "--metrics-table",
    )

    acute_frontmatter, acute_body = _read_frontmatter(tmp_path / "sample_accent_acute.txt")
    bold_frontmatter, bold_body = _read_frontmatter(tmp_path / "sample_accent_bold.md")
    xar_frontmatter, xar_body = _read_frontmatter(tmp_path / "sample_accent_xar.txt")

    assert acute_frontmatter["metadata"]["options"]["print_merger"] is False
    assert bold_frontmatter["metadata"]["options"]["print_merger"] is False
    assert xar_frontmatter["metadata"]["options"]["print_merger"] is False
    assert "‿" not in acute_body
    assert "‿" not in bold_body
    assert "‿" not in xar_body
    assert "ana ilī" in acute_body


def test_fullprosmaker_print_merger_true(tmp_path: Path) -> None:
    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p",
        "sample",
        "--outdir",
        str(tmp_path),
        "--print-acute",
        "--print-bold",
        "--print-xar",
        "--metrics-table",
        "--print-merger",
    )

    acute_frontmatter, acute_body = _read_frontmatter(tmp_path / "sample_accent_acute.txt")
    bold_frontmatter, bold_body = _read_frontmatter(tmp_path / "sample_accent_bold.md")
    xar_frontmatter, xar_body = _read_frontmatter(tmp_path / "sample_accent_xar.txt")

    assert acute_frontmatter["metadata"]["options"]["print_merger"] is True
    assert bold_frontmatter["metadata"]["options"]["print_merger"] is True
    assert xar_frontmatter["metadata"]["options"]["print_merger"] is True
    assert "‿" in acute_body
    assert "‿" in bold_body
    assert "‿" in xar_body
