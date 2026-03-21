import os
import json
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INTREF_DIR = REPO_ROOT / "tests" / "integration_refs"
STAGE_REF_DIR = INTREF_DIR / "stage_pipeline"
FULL_REF_DIR = INTREF_DIR / "fullprosmaker"
PHONEPREP_REF_DIR = INTREF_DIR / "phoneprep"
INPUT_ATF = INTREF_DIR / "L_I.2_Poem_of_Creation_SB_II.atf"
INPUT_PROC = STAGE_REF_DIR / "expected_e2e_proc.txt"

# Gold-standard values from known-good output for this reference sample.
GOLD_VARCOC_ACCENTUATED = 84.92
GOLD_ACCENTUATION_RATE = 14.29
GOLD_TILDE_SAMPLE_LINE = "u·kap·pit-ma : tiā~m·tu pi·tiq·ša"


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


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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

    var_matches = re.findall(r"VarcoC:\s*([0-9]+\.[0-9]+) %", metrics_text)
    assert var_matches, "VarcoC not found in metrics table"

    if accent_section:
        m_var = re.search(r"VarcoC:\s*([0-9]+\.[0-9]+) %", accent_section)
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


def _sanitize_metrics_csv_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    for ln in lines:
        if ln.startswith("Metric,"):
            out.append("Metric,<PATH>")
            continue
        out.append(ln)
    return out


def _assert_matches_reference(generated: Path, reference: Path) -> None:
    assert reference.exists(), f"Reference file missing: {reference}"
    gen = _read_text(generated)
    ref = _read_text(reference)

    if generated.name.endswith("_metrics.txt"):
        assert _sanitize_metrics_table_lines(_norm_lines(gen)) == _sanitize_metrics_table_lines(_norm_lines(ref)), (
            f"Mismatch vs reference for: {generated.name}"
        )
        return

    if generated.suffix == ".json":
        assert _sanitize_metrics_json_text(gen) == _sanitize_metrics_json_text(ref), (
            f"Mismatch vs reference for: {generated.name}"
        )
        return

    if generated.suffix == ".csv":
        assert _sanitize_metrics_csv_lines(_norm_lines(gen)) == _sanitize_metrics_csv_lines(_norm_lines(ref)), (
            f"Mismatch vs reference for: {generated.name}"
        )
        return

    assert _norm_lines(gen) == _norm_lines(ref), f"Mismatch vs reference for: {generated.name}"


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

    _run_cli("akkapros.cli.syllabifier", str(proc_file), "-p", prefix, "--outdir", str(outdir))
    syl_file = outdir / f"{prefix}_syl.txt"
    _assert_non_empty_text_file(syl_file)

    _run_cli("akkapros.cli.prosmaker", str(syl_file), "-p", prefix, "--outdir", str(outdir), "--style", "lob")
    tilde_file = outdir / f"{prefix}_tilde.txt"
    _assert_non_empty_text_file(tilde_file)

    _run_cli(
        "akkapros.cli.metricalc",
        str(tilde_file),
        "-p",
        prefix,
        "--outdir",
        str(outdir),
        "--table",
        "--json",
        "--csv",
    )
    metrics_txt = outdir / f"{prefix}_metrics.txt"
    metrics_json = outdir / f"{prefix}_metrics.json"
    metrics_csv = outdir / f"{prefix}_metrics.csv"
    _assert_non_empty_text_file(metrics_txt)
    _assert_non_empty_text_file(metrics_json)
    _assert_non_empty_text_file(metrics_csv)

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

    reference_map = {
        proc_file: STAGE_REF_DIR / "expected_e2e_proc.txt",
        orig_file: STAGE_REF_DIR / "expected_e2e_orig.txt",
        trans_file: STAGE_REF_DIR / "expected_e2e_trans.txt",
        syl_file: STAGE_REF_DIR / "expected_e2e_syl.txt",
        tilde_file: STAGE_REF_DIR / "expected_e2e_tilde.txt",
        metrics_txt: STAGE_REF_DIR / "expected_e2e_metrics.txt",
        metrics_json: STAGE_REF_DIR / "expected_e2e_metrics.json",
        metrics_csv: STAGE_REF_DIR / "expected_e2e_metrics.csv",
        printer_outputs[0]: STAGE_REF_DIR / "expected_e2e_accent_acute.txt",
        printer_outputs[1]: STAGE_REF_DIR / "expected_e2e_accent_bold.md",
        printer_outputs[2]: STAGE_REF_DIR / "expected_e2e_accent_ipa.txt",
        printer_outputs[3]: STAGE_REF_DIR / "expected_e2e_accent_xar.txt",
        printer_outputs[4]: STAGE_REF_DIR / "expected_e2e_xar.txt",
        printer_outputs[5]: STAGE_REF_DIR / "expected_e2e_accent_mbrola.txt",
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
        "--metrics-csv",
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
        outdir / "test.csv",
        outdir / "test_accent_acute.txt",
        outdir / "test_accent_bold.md",
        outdir / "test_accent_ipa.txt",
        outdir / "test_accent_xar.txt",
        outdir / "test_xar.txt",
    ]
    for path in expected_outputs:
        _assert_non_empty_text_file(path)

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
        outdir / "test.csv": FULL_REF_DIR / "expected_test.csv",
        outdir / "test_accent_acute.txt": FULL_REF_DIR / "expected_test_accent_acute.txt",
        outdir / "test_accent_bold.md": FULL_REF_DIR / "expected_test_accent_bold.md",
        outdir / "test_accent_ipa.txt": FULL_REF_DIR / "expected_test_accent_ipa.txt",
        outdir / "test_accent_xar.txt": FULL_REF_DIR / "expected_test_accent_xar.txt",
        outdir / "test_xar.txt": FULL_REF_DIR / "expected_test_xar.txt",
    }
    for generated, reference in full_reference_map.items():
        _assert_matches_reference(generated, reference)


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
