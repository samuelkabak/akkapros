import os
import subprocess
import sys

import pytest

from akkapros.lib import metrics, syllabify


@pytest.fixture(autouse=True)
def _reset_punctuation_rules():
    syllabify.configure_punctuation_rules()
    metrics.configure_pause_punctuation_rules()
    yield
    syllabify.configure_punctuation_rules()
    metrics.configure_pause_punctuation_rules()


def test_syllabify_rejects_undeclared_punctuation_char():
    with pytest.raises(syllabify.PunctuationConfigError):
        syllabify.syllabify_text("sar o gimir")


def test_syllabify_accepts_extension_char():
    out = syllabify.syllabify_text("sar o gimir", short_punct_chars="o")
    assert "⟦" in out


def test_syllabify_invalid_regex_fails_fast():
    with pytest.raises(syllabify.PunctuationConfigError):
        syllabify.syllabify_text("sar gimir", short_punct_patterns=["["])


def test_bol_token_pattern_accepts_line_start_hyphen():
    out = syllabify.syllabify_text(
        "sar\n- 123\ngimir",
        preserve_lines=True,
        short_punct_patterns=[r"^[:bol:]\s*-\s+\d+[:eol:]$"],
    )
    assert "⟦- 123⟧" in out


def test_custom_long_pattern_two_dashes_space_or_eol():
    pattern = r"^[ \t]+--([ \t]+|[:eol:])$"
    out_inline = syllabify.syllabify_text(
        "aba -- ana",
        short_punct_patterns=[pattern],
        long_punct_patterns=[pattern],
    )
    assert "⟦ -- ⟧" in out_inline

    out_newline = syllabify.syllabify_text(
        "aba --\nana",
        preserve_lines=True,
        short_punct_patterns=[pattern],
        long_punct_patterns=[pattern],
    )
    assert "⟦ --⟧\n" in out_newline


def test_metrics_rejects_unknown_punctuation_gap():
    with pytest.raises(metrics.PunctuationConfigError):
        metrics.process_filetext("at·ta @ a·lik", wpm=165, pause_ratio=35.0)


def test_metrics_accepts_extension_char():
    metrics.configure_pause_punctuation_rules(short_punct_chars='@')
    result = metrics.process_filetext("at·ta @ a·lik", wpm=165, pause_ratio=35.0)
    assert result["accentuated"]["pause_metrics"]["raw_counts"]["short_punctuation"] >= 1


def test_fullprosmaker_passes_punctuation_options(tmp_path):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    src_path = os.path.join(repo_root, "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    input_file = tmp_path / "sample_proc.txt"
    input_file.write_text("sar o gimir\n", encoding="utf-8")

    outdir = tmp_path / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "akkapros.cli.fullprosmaker",
        str(input_file),
        "-p",
        "sample",
        "--outdir",
        str(outdir),
        "--short-punct-chars",
        "o",
        "--metrics-table",
    ]
    proc = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
