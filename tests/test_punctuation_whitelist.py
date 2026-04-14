import os
import subprocess
import sys

import pytest

from akkapros.lib import metrics, syllabify
from akkapros.lib.frontmatter import split_frontmatter


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


def test_syllabify_accepts_repeated_ellipsis_chunk():
    out = syllabify.syllabify_text("sar … … gimir")
    assert "⟦ … … ⟧" in out


def test_syllabify_merges_only_immediate_cross_line_hyphenation():
    merged = syllabify.text_preprocess_boundaries("ukappit-\nma", [], preserve_lines=False)
    not_merged = syllabify.text_preprocess_boundaries("ukappit-\n ma", [], preserve_lines=False)
    assert merged == "ukappit-ma"
    assert not_merged == "ukappit- ma"


def test_syllabify_merges_only_immediate_cross_line_linker():
    merged = syllabify.text_preprocess_boundaries("apil+\nellil", [], preserve_lines=False)
    not_merged = syllabify.text_preprocess_boundaries("apil+\n ellil", [], preserve_lines=False)
    assert merged == "apil+ellil"
    assert not_merged == "apil+ ellil"


def test_metrics_rejects_unknown_punctuation_gap():
    with pytest.raises(metrics.PunctuationConfigError):
        metrics.process_filetext("at·ta @ a·lik")


def test_metrics_accepts_extension_char():
    metrics.configure_pause_punctuation_rules(short_punct_chars='@')
    result = metrics.process_filetext("at·ta @ a·lik")
    assert result["accentuated"]["speech"]["pause_row_count"] >= 1


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
        "--extra-short-punct-chars",
        "o",
        "--metrics-table",
    ]
    proc = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"


def test_metricalc_help_omits_inherited_punctuation_flags(tmp_path):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    src_path = os.path.join(repo_root, "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.metricalc", "--help"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0
    assert "--short-punct-chars" not in proc.stdout
    assert "--long-punct-chars" not in proc.stdout
    assert "--short-punct-pattern" not in proc.stdout
    assert "--long-punct-pattern" not in proc.stdout
    assert "--extra-consonants" not in proc.stdout
    assert "--extra-vowels" not in proc.stdout


def test_metricalc_consumes_inherited_punctuation_options_from_input(tmp_path):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    src_path = os.path.join(repo_root, "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    proc_file = tmp_path / "sample_proc.txt"
    proc_file.write_text("sar o gimir\n", encoding="utf-8")
    outdir = tmp_path / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    syl = subprocess.run(
        [
            sys.executable,
            "-m",
            "akkapros.cli.syllabifier",
            str(proc_file),
            "-p",
            "sample",
            "--outdir",
            str(outdir),
            "--extra-short-punct-chars",
            "o",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert syl.returncode == 0, f"STDOUT:\n{syl.stdout}\nSTDERR:\n{syl.stderr}"

    tilde = subprocess.run(
        [
            sys.executable,
            "-m",
            "akkapros.cli.prosmaker",
            str(outdir / "sample_syl.txt"),
            "-p",
            "sample",
            "--outdir",
            str(outdir),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert tilde.returncode == 0, f"STDOUT:\n{tilde.stdout}\nSTDERR:\n{tilde.stderr}"

    metrics_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "akkapros.cli.phonetizer",
            str(outdir / "sample_tilde.txt"),
            "-p",
            "sample",
            "--outdir",
            str(outdir),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert metrics_proc.returncode == 0, f"STDOUT:\n{metrics_proc.stdout}\nSTDERR:\n{metrics_proc.stderr}"

    metrics_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "akkapros.cli.metricalc",
            str(outdir / "sample_phone.txt"),
            "-p",
            "sample",
            "--outdir",
            str(outdir),
            "--table",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert metrics_proc.returncode == 0, f"STDOUT:\n{metrics_proc.stdout}\nSTDERR:\n{metrics_proc.stderr}"


def test_fullprosmaker_propagates_extra_inventory_settings_to_metrics_outputs(tmp_path):
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = os.environ.copy()
    src_path = os.path.join(repo_root, "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    proc_file = tmp_path / "sample_proc.txt"
    proc_file.write_text("sar gimir\n", encoding="utf-8")
    outdir = tmp_path / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "akkapros.cli.fullprosmaker",
            str(proc_file),
            "-p",
            "sample",
            "--outdir",
            str(outdir),
            "--extra-vowels",
            "ø",
            "--extra-consonants",
            "ɣ",
            "--metrics-table",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    tilde_frontmatter, _ = split_frontmatter((outdir / "sample_tilde.txt").read_text(encoding="utf-8"))
    metrics_frontmatter, _ = split_frontmatter((outdir / "sample_metrics.txt").read_text(encoding="utf-8"))

    assert tilde_frontmatter is not None
    assert metrics_frontmatter is not None
    assert tilde_frontmatter["metadata"]["options"]["extra_vowels"] == "ø"
    assert tilde_frontmatter["metadata"]["options"]["extra_consonants"] == "ɣ"
    assert metrics_frontmatter["metadata"]["options"]["extra_vowels"] == "ø"
    assert metrics_frontmatter["metadata"]["options"]["extra_consonants"] == "ɣ"
