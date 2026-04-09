import os
import subprocess
import sys
from shutil import copyfile
from pathlib import Path

from akkapros.lib.utils import format_path_for_logging


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PROC = REPO_ROOT / "tests" / "integration_refs" / "stage_pipeline" / "expected_e2e_proc.txt"


def _run_cli(*module_and_args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", *module_and_args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _build_tilde(tmp_path: Path) -> Path:
    outdir = tmp_path / "logging_case"
    outdir.mkdir(parents=True, exist_ok=True)

    syllabifier = _run_cli(
        "akkapros.cli.syllabifier",
        str(INPUT_PROC),
        "-p",
        "logging",
        "--outdir",
        str(outdir),
    )
    assert syllabifier.returncode == 0, syllabifier.stderr or syllabifier.stdout

    prosmaker = _run_cli(
        "akkapros.cli.prosmaker",
        str(outdir / "logging_syl.txt"),
        "-p",
        "logging",
        "--outdir",
        str(outdir),
        "--style",
        "lob",
    )
    assert prosmaker.returncode == 0, prosmaker.stderr or prosmaker.stdout
    return outdir / "logging_tilde.txt"


def test_cli_help_lists_shared_logging_options() -> None:
    modules = [
        "akkapros.cli.atfparser",
        "akkapros.cli.syllabifier",
        "akkapros.cli.prosmaker",
        "akkapros.cli.phonetizer",
        "akkapros.cli.metricalc",
        "akkapros.cli.printer",
        "akkapros.cli.fullprosmaker",
        "akkapros.cli.phoneprep",
    ]

    for module in modules:
        proc = _run_cli(module, "--help")
        assert proc.returncode == 0, f"help failed for {module}: {proc.stderr or proc.stdout}"
        help_text = proc.stdout + proc.stderr
        assert "--quiet" in help_text
        assert "--no-console" in help_text
        assert "--log" in help_text
        assert "--log-append" in help_text


def test_cli_log_append_requires_log() -> None:
    proc = _run_cli("akkapros.cli.phoneprep", "--log-append")
    assert proc.returncode == 2
    assert "--log-append requires --log" in proc.stderr


def test_metricalc_no_console_logs_to_file(tmp_path: Path) -> None:
    tilde_file = _build_tilde(tmp_path)
    outdir = tilde_file.parent
    log_file = outdir / "metricalc.log"

    proc = _run_cli(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        "logging",
        "--outdir",
        str(outdir),
        "--no-console",
        "--log",
        str(log_file),
        "--table",
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert proc.stdout == ""
    assert proc.stderr == ""
    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "akkapros.cli.metricalc" in log_text
    assert "Written file:" in log_text


def test_metricalc_console_and_logfile_are_coherent(tmp_path: Path) -> None:
    tilde_file = _build_tilde(tmp_path)
    outdir = tilde_file.parent
    log_file = outdir / "metricalc.log"

    proc = _run_cli(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        "logging",
        "--outdir",
        str(outdir),
        "--log",
        str(log_file),
        "--table",
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert proc.stderr == ""
    assert log_file.exists()
    assert log_file.read_text(encoding="utf-8") == proc.stdout
    assert "INFO:akkapros.cli.metricalc:" in proc.stdout


def test_metricalc_quiet_keeps_warning_channel(tmp_path: Path) -> None:
    tilde_file = _build_tilde(tmp_path)
    outdir = tilde_file.parent

    proc = _run_cli(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        "logging",
        "--outdir",
        str(outdir),
        "--quiet",
        "--csv",
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Processing:" not in proc.stdout
    assert "WARNING:" in proc.stderr
    assert "--csv option is not anymore supported" in proc.stderr


def test_format_path_for_logging_redacts_to_one_parent() -> None:
    assert format_path_for_logging(r"C:\Users\samue\folder\corpus_syl.txt") == r"...\folder\corpus_syl.txt"
    assert format_path_for_logging(r"C:\corpus_syl.txt") == r"C:\corpus_syl.txt"
    assert format_path_for_logging(r"relative\results\corpus_syl.txt") == r"...\results\corpus_syl.txt"


def test_syllabifier_logs_redacted_paths(tmp_path: Path) -> None:
    src_dir = tmp_path / "secret" / "results"
    out_dir = tmp_path / "private" / "outputs"
    src_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    input_file = src_dir / "corpus_proc.txt"
    copyfile(INPUT_PROC, input_file)

    proc = _run_cli(
        "akkapros.cli.syllabifier",
        str(input_file),
        "-p",
        "corpus",
        "--outdir",
        str(out_dir),
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert str(input_file) not in proc.stdout
    assert str(out_dir / "corpus_syl.txt") not in proc.stdout
    assert r"...\results\corpus_proc.txt" in proc.stdout
    assert r"...\outputs\corpus_syl.txt" in proc.stdout


def test_prosmaker_does_not_emit_line_count_progress(tmp_path: Path) -> None:
    outdir = tmp_path / "progress_case"
    outdir.mkdir(parents=True, exist_ok=True)

    syllabifier = _run_cli(
        "akkapros.cli.syllabifier",
        str(INPUT_PROC),
        "-p",
        "progress",
        "--outdir",
        str(outdir),
    )
    assert syllabifier.returncode == 0, syllabifier.stderr or syllabifier.stdout

    proc = _run_cli(
        "akkapros.cli.prosmaker",
        str(outdir / "progress_syl.txt"),
        "-p",
        "progress",
        "--outdir",
        str(outdir),
        "--style",
        "lob",
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "Processing 1108 lines" not in proc.stdout
    assert "Processed 10/" not in proc.stdout


def test_fullprosmaker_omits_stage_narration(tmp_path: Path) -> None:
    outdir = tmp_path / "full_pipeline"
    outdir.mkdir(parents=True, exist_ok=True)

    proc = _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p",
        "logging",
        "--outdir",
        str(outdir),
        "--prosody-style",
        "lob",
        "--metrics-table",
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "[1/4]" not in proc.stdout
    assert "Pipeline completed successfully" not in proc.stdout
    assert "Output directory:" not in proc.stdout


def test_phonetizer_no_console_logs_to_file(tmp_path: Path) -> None:
    tilde_file = _build_tilde(tmp_path)
    outdir = tilde_file.parent
    log_file = outdir / "phonetizer.log"

    proc = _run_cli(
        "akkapros.cli.phonetizer",
        str(tilde_file),
        "-p",
        "logging",
        "--outdir",
        str(outdir),
        "--no-console",
        "--log",
        str(log_file),
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert proc.stdout == ""
    assert proc.stderr == ""
    assert log_file.exists()
    assert (outdir / "logging_ophone.txt").exists()
    assert (outdir / "logging_phone.txt").exists()