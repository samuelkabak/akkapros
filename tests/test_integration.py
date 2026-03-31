import os
import json
import re
import subprocess
import sys
from pathlib import Path

from akkapros.lib.frontmatter import split_frontmatter
from akkapros.lib import metrics
from akkapros.lib.utils import format_path_for_logging


REPO_ROOT = Path(__file__).resolve().parents[1]
INTREF_DIR = REPO_ROOT / "tests" / "integration_refs"
STAGE_REF_DIR = INTREF_DIR / "stage_pipeline"
FULL_REF_DIR = INTREF_DIR / "fullprosmaker"
PHONEPREP_REF_DIR = INTREF_DIR / "phoneprep"
INPUT_ATF = INTREF_DIR / "L_I.2_Poem_of_Creation_SB_II.atf"
INPUT_PROC = STAGE_REF_DIR / "expected_e2e_proc.txt"

# Gold-standard values from known-good output for this reference sample.
GOLD_VARCOC_ACCENTUATED = 86.57
GOLD_ACCENTUATION_RATE = 21.74
GOLD_TILDE_SAMPLE_LINE = "u·kap·pit-ma : ti·¨ā~m·tu pi·tiq·ša"
GOLD_MONO_TILDE_SAMPLE_LINE = "tā·ḫā~·za ik~·ta·ṣar : a·na+i·lī~ nip·rī~·ša"


def _run_cli(*module_and_args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-m", *module_and_args]
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, (
        f"CLI failed: {' '.join(module_and_args)}\n"
        f"STDOUT:\n{proc.stdout}\n"
        f"STDERR:\n{proc.stderr}"
    )
    return proc


def _run_cli_expect_failure(*module_and_args: str) -> subprocess.CompletedProcess:
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


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_yaml_frontmatter(text: str) -> str:
    _, body = split_frontmatter(text)
    return body


def _assert_has_yaml_frontmatter(path: Path, *, require_title: bool = True) -> None:
    frontmatter, body = split_frontmatter(_read_text(path))
    assert frontmatter is not None, f"Expected YAML front matter in: {path}"
    assert body.strip(), f"Expected non-empty body in: {path}"
    assert frontmatter["pipeline"] == "pipeline"
    assert frontmatter["file"]["id"]
    if require_title:
        assert frontmatter["file"]["title"]


def _assert_non_empty_text_file(path: Path) -> None:
    assert path.exists(), f"Expected output file missing: {path}"
    content = _read_text(path)
    assert content.strip(), f"Expected non-empty content in: {path}"
    assert content.endswith("\n"), f"Expected trailing newline in: {path}"


def _parse_metrics_table(metrics_text: str) -> tuple[float, float]:
    accent_section = None
    m_section = re.search(r"--- ACCENTUATED TEXT ---.*?Acoustic metrics \(accentuated\):", metrics_text, re.S)
    if m_section:
        accent_section = metrics_text[m_section.end():m_section.end() + 400]

    var_matches = re.findall(r"VarcoC:\s*([0-9]+\.[0-9]+)", metrics_text)
    assert var_matches, "VarcoC not found in metrics table"

    if accent_section:
        m_var = re.search(r"VarcoC:\s*([0-9]+\.[0-9]+)", accent_section)
        varcoc = float(m_var.group(1)) if m_var else float(var_matches[-1])
    else:
        varcoc = float(var_matches[-1])

    m_rate = re.search(r"Accentuation rate:\s*([0-9]+\.[0-9]+)%", metrics_text)
    assert m_rate, "Accentuation rate not found in metrics table"
    acc_rate = float(m_rate.group(1))
    return varcoc, acc_rate


def _norm_lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.replace("\r\n", "\n").splitlines()]


def _sanitize_metrics_table_lines(lines: list[str]) -> list[str]:
    """Drop path-dependent lines so golden comparison is stable across temp dirs."""
    out: list[str] = []
    for ln in lines:
        if ln.startswith("METRICS SUMMARY:"):
            continue
        if ln.startswith("  input:"):
            continue
        out.append(ln)
    return out


def _sanitize_metrics_json_text(text: str) -> str:
    data = json.loads(text)
    if isinstance(data, dict):
        data.pop("frontmatter", None)

    def _walk(obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k in {"file", "input"} and isinstance(v, str):
                    out[k] = "<PATH>"
                else:
                    out[k] = _walk(v)
            return out
        if isinstance(obj, list):
            return [_walk(v) for v in obj]
        return obj

    return json.dumps(_walk(data), ensure_ascii=False, sort_keys=True, indent=2)


def _assert_matches_reference(generated: Path, reference: Path) -> None:
    assert reference.exists(), f"Reference file missing: {reference}"
    gen = _read_text(generated)
    ref = _read_text(reference)

    if generated.name.endswith("_metrics.txt"):
        assert _sanitize_metrics_table_lines(_norm_lines(_strip_yaml_frontmatter(gen))) == _sanitize_metrics_table_lines(_norm_lines(ref)), (
            f"Mismatch vs reference for: {generated.name}"
        )
        return

    if generated.suffix == ".json":
        assert _sanitize_metrics_json_text(gen) == _sanitize_metrics_json_text(ref), (
            f"Mismatch vs reference for: {generated.name}"
        )
        return

    assert _norm_lines(_strip_yaml_frontmatter(gen)) == _norm_lines(ref), f"Mismatch vs reference for: {generated.name}"


def _assert_metrics_artifact_paths_are_safe(metrics_txt: Path, metrics_json: Path, source_path: Path) -> None:
    safe_path = format_path_for_logging(source_path)
    metrics_table = _strip_yaml_frontmatter(_read_text(metrics_txt))
    assert f"METRICS SUMMARY: {safe_path}" in metrics_table
    assert f"  input: {safe_path}" in metrics_table
    assert str(source_path) not in metrics_table

    metrics_obj = json.loads(_read_text(metrics_json))
    assert metrics_obj["file"] == safe_path
    assert str(source_path) != metrics_obj["file"]


def test_cli_stage_pipeline_outputs_all_files(tmp_path: Path) -> None:
    """Run each stage CLI in sequence and verify all stage outputs are produced."""
    outdir = tmp_path / "stage_pipeline"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = "e2e"

    _run_cli("akkapros.cli.atfparser", str(INPUT_ATF), "-p", prefix, "--outdir", str(outdir))
    proc_file = outdir / f"{prefix}_proc.txt"
    orig_file = outdir / f"{prefix}_orig.txt"
    trans_file = outdir / f"{prefix}_trans.txt"
    _assert_non_empty_text_file(proc_file)
    _assert_non_empty_text_file(orig_file)
    _assert_non_empty_text_file(trans_file)
    _assert_has_yaml_frontmatter(proc_file)
    _assert_has_yaml_frontmatter(orig_file)
    _assert_has_yaml_frontmatter(trans_file)

    _run_cli("akkapros.cli.syllabifier", str(proc_file), "-p", prefix, "--outdir", str(outdir))
    syl_file = outdir / f"{prefix}_syl.txt"
    _assert_non_empty_text_file(syl_file)
    _assert_has_yaml_frontmatter(syl_file)

    _run_cli("akkapros.cli.prosmaker", str(syl_file), "-p", prefix, "--outdir", str(outdir), "--style", "lob")
    tilde_file = outdir / f"{prefix}_tilde.txt"
    _assert_non_empty_text_file(tilde_file)
    _assert_has_yaml_frontmatter(tilde_file)

    _run_cli(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--table",
        "--json",
    )
    metrics_txt = outdir / f"{prefix}_metrics.txt"
    metrics_json = outdir / f"{prefix}_metrics.json"
    _assert_non_empty_text_file(metrics_txt)
    _assert_non_empty_text_file(metrics_json)
    assert not (outdir / f"{prefix}_metrics.csv").exists()
    _assert_has_yaml_frontmatter(metrics_txt)
    metrics_json_obj = json.loads(_read_text(metrics_json))
    assert "frontmatter" in metrics_json_obj
    assert "data" not in metrics_json_obj["frontmatter"]["metadata"]
    _assert_metrics_artifact_paths_are_safe(metrics_txt, metrics_json, tilde_file)

    _run_cli(
        "akkapros.cli.printer",
        str(tilde_file),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--acute",
        "--bold",
        "--ipa",
        "--xar",
        "--mbrola",
    )
    printer_outputs = [
        outdir / f"{prefix}_accent_acute.txt",
        outdir / f"{prefix}_accent_bold.md",
        outdir / f"{prefix}_accent_ipa.txt",
        outdir / f"{prefix}_accent_xar.txt",
        outdir / f"{prefix}_xar.txt",
        outdir / f"{prefix}_accent_mbrola.txt",
    ]
    for path in printer_outputs:
        _assert_non_empty_text_file(path)
        _assert_has_yaml_frontmatter(path)

    reference_map = {
        proc_file: STAGE_REF_DIR / "expected_e2e_proc.txt",
        orig_file: STAGE_REF_DIR / "expected_e2e_orig.txt",
        trans_file: STAGE_REF_DIR / "expected_e2e_trans.txt",
        syl_file: STAGE_REF_DIR / "expected_e2e_syl.txt",
        tilde_file: STAGE_REF_DIR / "expected_e2e_tilde.txt",
        metrics_txt: STAGE_REF_DIR / "expected_e2e_metrics.txt",
        metrics_json: STAGE_REF_DIR / "expected_e2e_metrics.json",
        printer_outputs[0]: STAGE_REF_DIR / "expected_e2e_accent_acute.txt",
        printer_outputs[1]: STAGE_REF_DIR / "expected_e2e_accent_bold.md",
        printer_outputs[2]: STAGE_REF_DIR / "expected_e2e_accent_ipa.txt",
        printer_outputs[3]: STAGE_REF_DIR / "expected_e2e_accent_xar.txt",
        printer_outputs[4]: STAGE_REF_DIR / "expected_e2e_xar.txt",
        printer_outputs[5]: STAGE_REF_DIR / "expected_e2e_accent_mbrola.txt",
    }
    for generated, reference in reference_map.items():
        _assert_matches_reference(generated, reference)


def test_cli_stage_pipeline_outputs_all_files_in_mono_mode(tmp_path: Path) -> None:
    """Run each stage CLI in sequence with prosody mono mode and pin outputs."""
    outdir = tmp_path / "stage_pipeline_mono"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = "e2e_mono"

    _run_cli("akkapros.cli.atfparser", str(INPUT_ATF), "-p", prefix, "--outdir", str(outdir))
    proc_file = outdir / f"{prefix}_proc.txt"
    orig_file = outdir / f"{prefix}_orig.txt"
    trans_file = outdir / f"{prefix}_trans.txt"
    _assert_non_empty_text_file(proc_file)
    _assert_non_empty_text_file(orig_file)
    _assert_non_empty_text_file(trans_file)
    _assert_has_yaml_frontmatter(proc_file)
    _assert_has_yaml_frontmatter(orig_file)
    _assert_has_yaml_frontmatter(trans_file)

    _run_cli("akkapros.cli.syllabifier", str(proc_file), "-p", prefix, "--outdir", str(outdir))
    syl_file = outdir / f"{prefix}_syl.txt"
    _assert_non_empty_text_file(syl_file)
    _assert_has_yaml_frontmatter(syl_file)

    _run_cli(
        "akkapros.cli.prosmaker",
        str(syl_file),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--style",
        "lob",
        "--mora-mode",
        "mono",
    )
    tilde_file = outdir / f"{prefix}_tilde.txt"
    _assert_non_empty_text_file(tilde_file)
    _assert_has_yaml_frontmatter(tilde_file)
    tilde_frontmatter, tilde_body = split_frontmatter(_read_text(tilde_file))
    assert tilde_frontmatter is not None
    assert tilde_frontmatter["metadata"]["options"]["mora_mode"] == "mono"
    assert GOLD_MONO_TILDE_SAMPLE_LINE in tilde_body

    _run_cli(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--table",
        "--json",
    )
    metrics_txt = outdir / f"{prefix}_metrics.txt"
    metrics_json = outdir / f"{prefix}_metrics.json"
    _assert_non_empty_text_file(metrics_txt)
    _assert_non_empty_text_file(metrics_json)
    _assert_has_yaml_frontmatter(metrics_txt)
    metrics_json_obj = json.loads(_read_text(metrics_json))
    assert "frontmatter" in metrics_json_obj
    assert metrics_json_obj["frontmatter"]["metadata"]["options"]["mora_mode"] == "mono"
    _assert_metrics_artifact_paths_are_safe(metrics_txt, metrics_json, tilde_file)

    _run_cli(
        "akkapros.cli.printer",
        str(tilde_file),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--acute",
        "--bold",
        "--ipa",
        "--xar",
        "--mbrola",
    )
    printer_outputs = [
        outdir / f"{prefix}_accent_acute.txt",
        outdir / f"{prefix}_accent_bold.md",
        outdir / f"{prefix}_accent_ipa.txt",
        outdir / f"{prefix}_accent_xar.txt",
        outdir / f"{prefix}_xar.txt",
        outdir / f"{prefix}_accent_mbrola.txt",
    ]
    for path in printer_outputs:
        _assert_non_empty_text_file(path)
        _assert_has_yaml_frontmatter(path)

    reference_map = {
        proc_file: STAGE_REF_DIR / "expected_e2e_proc.txt",
        orig_file: STAGE_REF_DIR / "expected_e2e_orig.txt",
        trans_file: STAGE_REF_DIR / "expected_e2e_trans.txt",
        syl_file: STAGE_REF_DIR / "expected_e2e_syl.txt",
        tilde_file: STAGE_REF_DIR / "expected_e2e_mono_tilde.txt",
        metrics_txt: STAGE_REF_DIR / "expected_e2e_mono_metrics.txt",
        metrics_json: STAGE_REF_DIR / "expected_e2e_mono_metrics.json",
        printer_outputs[0]: STAGE_REF_DIR / "expected_e2e_mono_accent_acute.txt",
        printer_outputs[1]: STAGE_REF_DIR / "expected_e2e_mono_accent_bold.md",
        printer_outputs[2]: STAGE_REF_DIR / "expected_e2e_mono_accent_ipa.txt",
        printer_outputs[3]: STAGE_REF_DIR / "expected_e2e_mono_accent_xar.txt",
        printer_outputs[4]: STAGE_REF_DIR / "expected_e2e_mono_xar.txt",
        printer_outputs[5]: STAGE_REF_DIR / "expected_e2e_mono_accent_mbrola.txt",
    }
    for generated, reference in reference_map.items():
        _assert_matches_reference(generated, reference)


def test_cli_fullprosmaker_gold_standard_reference(tmp_path: Path) -> None:
    """Run fullprosmaker and assert pinned metrics + reference outputs."""
    outdir = tmp_path / "full_pipeline"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = "test"

    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--metrics-table",
        "--metrics-json",
        "--print-acute",
        "--print-bold",
        "--print-ipa",
        "--print-xar",
    )

    expected_outputs = [
        outdir / "test_syl.txt",
        outdir / "test_tilde.txt",
        outdir / "test_metrics.txt",
        outdir / "test.json",
        outdir / "test_accent_acute.txt",
        outdir / "test_accent_bold.md",
        outdir / "test_accent_ipa.txt",
        outdir / "test_accent_xar.txt",
        outdir / "test_xar.txt",
    ]
    for path in expected_outputs:
        _assert_non_empty_text_file(path)
    for path in expected_outputs:
        if path.suffix in {".txt", ".md"}:
            _assert_has_yaml_frontmatter(path, require_title=False)
    assert "frontmatter" in json.loads(_read_text(outdir / "test.json"))

    metrics_text = _read_text(outdir / "test_metrics.txt")
    varcoc, acc_rate = _parse_metrics_table(metrics_text)
    assert abs(varcoc - GOLD_VARCOC_ACCENTUATED) < 0.5, (
        f"VarcoC differs: {varcoc} != {GOLD_VARCOC_ACCENTUATED}"
    )
    assert abs(acc_rate - GOLD_ACCENTUATION_RATE) < 0.5, (
        f"Accentuation rate differs: {acc_rate} != {GOLD_ACCENTUATION_RATE}"
    )

    tilde_text = _read_text(outdir / "test_tilde.txt")
    assert GOLD_TILDE_SAMPLE_LINE in tilde_text, "Pinned sample line not found in _tilde output"

    full_reference_map = {
        outdir / "test_syl.txt": FULL_REF_DIR / "expected_test_syl.txt",
        outdir / "test_tilde.txt": FULL_REF_DIR / "expected_test_tilde.txt",
        outdir / "test_metrics.txt": FULL_REF_DIR / "expected_test_metrics.txt",
        outdir / "test.json": FULL_REF_DIR / "expected_test.json",
        outdir / "test_accent_acute.txt": FULL_REF_DIR / "expected_test_accent_acute.txt",
        outdir / "test_accent_bold.md": FULL_REF_DIR / "expected_test_accent_bold.md",
        outdir / "test_accent_ipa.txt": FULL_REF_DIR / "expected_test_accent_ipa.txt",
        outdir / "test_accent_xar.txt": FULL_REF_DIR / "expected_test_accent_xar.txt",
        outdir / "test_xar.txt": FULL_REF_DIR / "expected_test_xar.txt",
    }
    for generated, reference in full_reference_map.items():
        _assert_matches_reference(generated, reference)

    _assert_metrics_artifact_paths_are_safe(outdir / "test_metrics.txt", outdir / "test.json", outdir / "test_tilde.txt")


def test_cli_fullprosmaker_mono_reference(tmp_path: Path) -> None:
    """Run fullprosmaker in mono mode and assert pinned reference outputs."""
    outdir = tmp_path / "full_pipeline_mono"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = "test_mono"

    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--mora-mode",
        "mono",
        "--metrics-table",
        "--metrics-json",
        "--print-acute",
        "--print-bold",
        "--print-ipa",
        "--print-xar",
    )

    expected_outputs = [
        outdir / "test_mono_syl.txt",
        outdir / "test_mono_tilde.txt",
        outdir / "test_mono_metrics.txt",
        outdir / "test_mono.json",
        outdir / "test_mono_accent_acute.txt",
        outdir / "test_mono_accent_bold.md",
        outdir / "test_mono_accent_ipa.txt",
        outdir / "test_mono_accent_xar.txt",
        outdir / "test_mono_xar.txt",
    ]
    for path in expected_outputs:
        _assert_non_empty_text_file(path)
    for path in expected_outputs:
        if path.suffix in {".txt", ".md"}:
            _assert_has_yaml_frontmatter(path, require_title=False)

    metrics_json = json.loads(_read_text(outdir / "test_mono.json"))
    assert "frontmatter" in metrics_json
    assert metrics_json["frontmatter"]["metadata"]["options"]["mora_mode"] == "mono"

    tilde_frontmatter, tilde_body = split_frontmatter(_read_text(outdir / "test_mono_tilde.txt"))
    assert tilde_frontmatter is not None
    assert tilde_frontmatter["metadata"]["options"]["mora_mode"] == "mono"
    assert GOLD_MONO_TILDE_SAMPLE_LINE in tilde_body

    full_reference_map = {
        outdir / "test_mono_syl.txt": FULL_REF_DIR / "expected_test_syl.txt",
        outdir / "test_mono_tilde.txt": FULL_REF_DIR / "expected_test_mono_tilde.txt",
        outdir / "test_mono_metrics.txt": FULL_REF_DIR / "expected_test_mono_metrics.txt",
        outdir / "test_mono.json": FULL_REF_DIR / "expected_test_mono.json",
        outdir / "test_mono_accent_acute.txt": FULL_REF_DIR / "expected_test_mono_accent_acute.txt",
        outdir / "test_mono_accent_bold.md": FULL_REF_DIR / "expected_test_mono_accent_bold.md",
        outdir / "test_mono_accent_ipa.txt": FULL_REF_DIR / "expected_test_mono_accent_ipa.txt",
        outdir / "test_mono_accent_xar.txt": FULL_REF_DIR / "expected_test_mono_accent_xar.txt",
        outdir / "test_mono_xar.txt": FULL_REF_DIR / "expected_test_mono_xar.txt",
    }
    for generated, reference in full_reference_map.items():
        _assert_matches_reference(generated, reference)

    _assert_metrics_artifact_paths_are_safe(
        outdir / "test_mono_metrics.txt",
        outdir / "test_mono.json",
        outdir / "test_mono_tilde.txt",
    )


def test_metricalc_legacy_csv_flag_logs_warning_notice(tmp_path: Path) -> None:
    outdir = tmp_path / "legacy_metricalc_csv"
    outdir.mkdir(parents=True, exist_ok=True)

    _run_cli("akkapros.cli.syllabifier", str(INPUT_PROC), "-p", "legacy", "--outdir", str(outdir))
    _run_cli(
        "akkapros.cli.prosmaker",
        str(outdir / "legacy_syl.txt"),
        "-p",
        "legacy",
        "--outdir",
        str(outdir),
        "--style",
        "lob",
    )

    proc = _run_cli(
        "akkapros.cli.metricalc",
        str(outdir / "legacy_tilde.txt"),
        "-p",
        "legacy",
        "--outdir",
        str(outdir),
        "--csv",
    )

    assert metrics.METRICS_CSV_DEPRECATION_MESSAGE not in proc.stdout
    assert metrics.METRICS_CSV_DEPRECATION_MESSAGE in proc.stderr
    _assert_non_empty_text_file(outdir / "legacy_metrics.txt")
    assert not (outdir / "legacy_metrics.csv").exists()


def test_fullprosmaker_legacy_metrics_csv_flag_logs_warning_notice(tmp_path: Path) -> None:
    outdir = tmp_path / "legacy_fullprosmaker_csv"
    outdir.mkdir(parents=True, exist_ok=True)

    proc = _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p",
        "legacy",
        "--outdir",
        str(outdir),
        "--metrics-csv",
    )

    assert metrics.METRICS_CSV_DEPRECATION_MESSAGE not in proc.stdout
    assert metrics.METRICS_CSV_DEPRECATION_MESSAGE in proc.stderr
    _assert_non_empty_text_file(outdir / "legacy_metrics.txt")
    assert not (outdir / "legacy.csv").exists()


def test_metricalc_requires_frontmatter_prominence_counts(tmp_path: Path) -> None:
    outdir = tmp_path / "missing_prominence"
    outdir.mkdir(parents=True, exist_ok=True)
    tilde_file = tmp_path / "missing_prominence_tilde.txt"
    tilde_file.write_text(
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Missing prominence\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-28\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "---\n\n"
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n",
        encoding="utf-8",
    )

    proc = _run_cli_expect_failure(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        "broken",
        "--outdir",
        str(outdir),
        "--table",
    )

    assert proc.returncode != 0
    assert "missing required field" in proc.stderr or "missing required field" in proc.stdout


def test_syllabifier_accepts_content_only_input_and_title_override(tmp_path: Path) -> None:
    outdir = tmp_path / "content_only"
    outdir.mkdir(parents=True, exist_ok=True)
    proc_file = tmp_path / "content_only_proc.txt"
    proc_file.write_text("šar gi-mir\nana šarri\n", encoding="utf-8")

    _run_cli(
        "akkapros.cli.syllabifier",
        str(proc_file),
        "-p",
        "content_only",
        "--outdir",
        str(outdir),
        "--title",
        "Manual Title",
    )

    syl_file = outdir / "content_only_syl.txt"
    frontmatter, body = split_frontmatter(_read_text(syl_file))
    assert frontmatter is not None
    assert frontmatter["file"]["title"] == "Manual Title"
    assert frontmatter["metadata"]["data"] == {}
    assert body.strip()


def test_metricalc_explicit_link_count_override_and_validation(tmp_path: Path) -> None:
    outdir = tmp_path / "explicit_override"
    outdir.mkdir(parents=True, exist_ok=True)
    tilde_file = tmp_path / "override_tilde.txt"
    tilde_file.write_text(
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Override\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-29\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "---\n\n"
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n",
        encoding="utf-8",
    )

    _run_cli(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        "override",
        "--outdir",
        str(outdir),
        "--table",
        "--explicit-link-count",
        "1",
    )
    assert (outdir / "override_metrics.txt").exists()

    bad_type = _run_cli_expect_failure(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        "override_bad_type",
        "--outdir",
        str(outdir),
        "--table",
        "--explicit-link-count",
        "abc",
    )
    assert bad_type.returncode != 0
    assert "--explicit-link-count must be a positive integer" in (bad_type.stderr + bad_type.stdout)

    bad_range = _run_cli_expect_failure(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        "override_bad_range",
        "--outdir",
        str(outdir),
        "--table",
        "--explicit-link-count",
        "5",
    )
    assert bad_range.returncode != 0
    assert "--explicit-link-count must be an integer between 0 and 4, where 4 = word_count - function_word_count" in (bad_range.stderr + bad_range.stdout)
    assert not (outdir / "override_bad_range_metrics.txt").exists()


def test_cli_phoneprep_outputs(tmp_path: Path) -> None:
    """Run phoneprep in reduced mode and verify script + sidecars are produced."""
    outdir = tmp_path / "phoneprep"
    outdir.mkdir(parents=True, exist_ok=True)
    script_path = outdir / "phoneprep_script.txt"

    _run_cli(
        "akkapros.cli.phoneprep",
        "--debug-reduced-set",
        "--coverage",
        "1",
        "--max-iterations",
        "2000",
        "--candidate-pool-size",
        "8",
        "--output",
        str(script_path),
        "--with-html-recording-helper",
    )

    sidecar_manifest = outdir / "phoneprep_script_manifest.tsv"
    sidecar_diphones = outdir / "phoneprep_script_diphones.tsv"
    sidecar_words = outdir / "phoneprep_script_words.txt"
    helper_html = outdir / "phoneprep_script_recording_helper.html"

    _assert_non_empty_text_file(script_path)
    _assert_non_empty_text_file(sidecar_manifest)
    _assert_non_empty_text_file(sidecar_diphones)
    _assert_non_empty_text_file(sidecar_words)
    _assert_non_empty_text_file(helper_html)

    phoneprep_reference_map = {
        script_path: PHONEPREP_REF_DIR / "expected_phoneprep_script.txt",
        sidecar_manifest: PHONEPREP_REF_DIR / "expected_phoneprep_script_manifest.tsv",
        sidecar_diphones: PHONEPREP_REF_DIR / "expected_phoneprep_script_diphones.tsv",
        sidecar_words: PHONEPREP_REF_DIR / "expected_phoneprep_script_words.txt",
        helper_html: PHONEPREP_REF_DIR / "expected_phoneprep_script_recording_helper.html",
    }
    for generated, reference in phoneprep_reference_map.items():
        _assert_matches_reference(generated, reference)
