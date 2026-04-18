import os
import json
import re
import subprocess
import sys
from pathlib import Path

from akkapros.lib.config import apply_overrides, build_default_config, dump_config_text, load_config_file
from akkapros.lib.frontmatter import split_frontmatter
from akkapros.lib.phonetize import (
    MINI_PAUSE_LABEL,
    MINI_PAUSE_REALIZATION,
    MINI_PAUSE_TEXT,
    MINI_PAUSE_TYPE,
    parse_phone_row,
    reconstruct_tilde_from_phone_rows,
)
from akkapros.lib.utils import format_path_for_logging


REPO_ROOT = Path(__file__).resolve().parents[1]
INTREF_DIR = REPO_ROOT / "tests" / "integration_refs"
STAGE_REF_DIR = INTREF_DIR / "stage_pipeline"
FULL_REF_DIR = INTREF_DIR / "fullprosmaker"
PHONEPREP_REF_DIR = INTREF_DIR / "phoneprep"
REGRESSION_CONFIG = INTREF_DIR / "regression_defaults.yaml"
INPUT_ATF = INTREF_DIR / "L_I.2_Poem_of_Creation_SB_II.atf"
INPUT_PROC = STAGE_REF_DIR / "expected_e2e_proc.txt"

# Gold-standard values for the current phone-interval metrics model.
# Metrics are intentionally verified from parsed current outputs and manual
# formulas, not by pinning old snapshot files from the superseded _tilde model.
GOLD_TILDE_SAMPLE_LINE = "u·kap·pit-ma⟦ : ⟧ti·¨ā~m·tu pi·tiq·ša"
GOLD_MONO_TILDE_SAMPLE_LINE = "tā·ḫā~·za ˙ik~·ta·ṣar⟦ : ⟧˙a·na&˙i·lī~ nip·rī~·ša"
GOLD_REGULAR_METRICS = {
    "original": {
        "stats": {
            "total_syllables": 23,
            "syllable_counts": {
                "CV": 9,
                "CVC": 5,
                "CVV": 4,
                "V": 3,
                "VC": 1,
                "VVC": 1,
            },
            "word_stats": {
                "total_words": 8,
                "syllables_per_word": {
                    "mean": 2.875,
                    "std": 0.6408699444616558,
                },
                "morae_per_word": {
                    "mean": 4.375,
                    "std": 1.3024701806293193,
                },
            },
            "mora_stats": {
                "mean": 1.5217391304347827,
                "std": 0.5931093121225481,
                "total": 35,
            },
        },
        "acoustic": {
            "percent_c": 27.629629629629633,
            "percent_v": 31.11111111111111,
            "mean_c_ms": 108.79166666666667,
            "mean_v_ms": 127.82608695652173,
            "delta_c_ms": 53.581697097879314,
            "delta_v_ms": 36.12255970263873,
            "varco_c": 49.251655700846555,
            "varco_v": 28.259145345601734,
            "rpvi_c": 68.52173913043478,
            "npvi_v": 19.56809762705244,
        },
        "drift": {
            "max": 115.0,
            "mean": 23.3333,
            "stddev": 37.6278,
        },
        "prominence_statistics": {
            "function_word_count": 1,
            "explicit_word_link_count": 0,
            "prominence_candidate_word_count": 7,
        },
    },
    "accentuated": {
        "stats": {
            "total_syllables": 23,
            "syllable_counts": {
                "CV": 9,
                "CVC": 5,
                "CVV": 1,
                "CVV:": 3,
                "V": 3,
                "VC:": 1,
                "VV:C": 1,
            },
            "word_stats": {
                "total_words": 7,
                "syllables_per_word": {
                    "mean": 3.2857142857142856,
                    "std": 0.4879500364742666,
                },
                "morae_per_word": {
                    "mean": 5.714285714285714,
                    "std": 0.7559289460184545,
                },
            },
            "mora_stats": {
                "mean": 1.7391304347826086,
                "std": 0.91539317456032,
                "total": 40,
            },
        },
        "acoustic": {
            "percent_c": 27.666666666666668,
            "percent_v": 32.68627450980392,
            "mean_c_ms": 117.58333333333333,
            "mean_v_ms": 144.95652173913044,
            "delta_c_ms": 65.20603031076872,
            "delta_v_ms": 64.69492168825562,
            "varco_c": 55.45516397797482,
            "varco_v": 44.630569850926186,
            "rpvi_c": 84.78260869565217,
            "npvi_v": 33.87121263935948,
        },
        "drift": {
            "max": 134.0,
            "mean": -1.1481,
            "stddev": 43.5624,
        },
    },
    "accentuation_stats": {
        "accentuated_syllables": 5,
        "accentuation_rate": 21.73913043478261,
        "accentuation_types": {
            "CVV:": 3,
            "VC:": 1,
            "VV:C": 1,
        },
        "merged_words": 2,
        "merged_units": 1,
        "avg_unit_size": 2.0,
    },
}
GOLD_MONO_METRICS = {
    "original": {
        "stats": {
            "total_syllables": 23,
            "syllable_counts": {
                "CV": 9,
                "CVC": 5,
                "CVV": 4,
                "V": 3,
                "VC": 1,
                "VVC": 1,
            },
            "word_stats": {
                "total_words": 8,
                "syllables_per_word": {
                    "mean": 2.875,
                    "std": 0.6408699444616558,
                },
                "morae_per_word": {
                    "mean": 4.375,
                    "std": 1.3024701806293193,
                },
            },
            "mora_stats": {
                "mean": 1.5217391304347827,
                "std": 0.5931093121225481,
                "total": 35,
            },
        },
        "acoustic": {
            "percent_c": 27.629629629629633,
            "percent_v": 31.11111111111111,
            "mean_c_ms": 108.79166666666667,
            "mean_v_ms": 127.82608695652173,
            "delta_c_ms": 53.581697097879314,
            "delta_v_ms": 36.12255970263873,
            "varco_c": 49.251655700846555,
            "varco_v": 28.259145345601734,
            "rpvi_c": 68.52173913043478,
            "npvi_v": 19.56809762705244,
        },
        "prominence_statistics": {
            "function_word_count": 1,
            "explicit_word_link_count": 0,
            "prominence_candidate_word_count": 7,
        },
    },
    "accentuated": {
        "stats": {
            "total_syllables": 23,
            "syllable_counts": {
                "CV": 9,
                "CVC": 3,
                "CVC:": 2,
                "CVV": 1,
                "CVV:": 3,
                "V": 3,
                "VC:": 1,
                "VV:C": 1,
            },
            "word_stats": {
                "total_words": 7,
                "syllables_per_word": {
                    "mean": 3.2857142857142856,
                    "std": 0.4879500364742666,
                },
                "morae_per_word": {
                    "mean": 6.0,
                    "std": 0.5773502691896257,
                },
            },
            "mora_stats": {
                "mean": 1.826086956521739,
                "std": 0.9840627249521833,
                "total": 42,
            },
        },
        "acoustic": {
            "percent_c": 29.16190476190476,
            "percent_v": 32.32380952380952,
            "mean_c_ms": 127.58333333333333,
            "mean_v_ms": 147.56521739130434,
            "delta_c_ms": 83.30762103326575,
            "delta_v_ms": 63.831862077312834,
            "varco_c": 65.29663307636767,
            "varco_v": 43.25671266288141,
            "rpvi_c": 105.65217391304348,
            "npvi_v": 38.234849002995844,
        },
        "drift": {
            "max": 134.0,
            "mean": -1.1481,
            "stddev": 43.5624,
        },
    },
    "accentuation_stats": {
        "accentuated_syllables": 7,
        "accentuation_rate": 30.434782608695656,
        "accentuation_types": {
            "CVC:": 2,
            "CVV:": 3,
            "VC:": 1,
            "VV:C": 1,
        },
        "merged_words": 2,
        "merged_units": 1,
        "avg_unit_size": 2.0,
    },
}


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


def _load_regression_config() -> dict:
    return load_config_file(REGRESSION_CONFIG)


def _write_regression_config(config_path: Path, overrides: dict[tuple[str, str], object]) -> Path:
    config = apply_overrides(_load_regression_config(), overrides)
    config_path.write_text(dump_config_text(config), encoding="utf-8")
    return config_path


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


def _assert_nested_expected(actual: dict, expected: dict) -> None:
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if isinstance(expected_value, dict):
            assert isinstance(actual_value, dict), key
            _assert_nested_expected(actual_value, expected_value)
        elif isinstance(expected_value, float):
            assert abs(actual_value - expected_value) < 1e-12, key
        else:
            assert actual_value == expected_value, key


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


def _assert_phone_artifact(path: Path) -> None:
    _assert_non_empty_text_file(path)
    _assert_has_yaml_frontmatter(path, require_title=False)
    frontmatter, body = split_frontmatter(_read_text(path))
    first_line = body.strip().splitlines()[0]
    first_row = parse_phone_row(first_line)
    assert list(first_row) == ['label', 'category', 'type', 'length', 'position', 'boundary', 'accent', 'realization', 'duration', 'drift', 'intonation', 'text']
    assert first_row['category'] in {'C', 'V', 'S'}
    assert len(first_row['duration']) == 4
    assert len(first_row['drift']) == 4
    assert len(first_row['intonation']) == 3
    all_rows = [parse_phone_row(line) for line in body.strip().splitlines()]
    assert any(row['duration'] != '0000' for row in all_rows)
    assert all(re.fullmatch(r'[+-]\d{3}', row['drift']) for row in all_rows)
    assert all(len(row['intonation']) == 3 for row in all_rows)
    assert frontmatter['metadata']['data']['phonetize']['drift']['max'] >= 0
    assert 'mean' in frontmatter['metadata']['data']['phonetize']['drift']
    assert 'stddev' in frontmatter['metadata']['data']['phonetize']['drift']


def _assert_pho_artifact(path: Path) -> None:
    _assert_non_empty_text_file(path)
    lines = _read_text(path).strip().splitlines()
    assert lines
    for line in lines:
        parts = line.split()
        assert len(parts) >= 3
        symbol, duration, *pitch_targets = parts
        assert symbol
        assert int(duration) > 0
        assert pitch_targets
        assert all(int(target) > 0 for target in pitch_targets)


def _parse_pho_artifact(path: Path) -> list[tuple[str, int, int]]:
    rows: list[tuple[str, int, tuple[int, ...]]] = []
    for line in _read_text(path).strip().splitlines():
        symbol, duration, *pitch_targets = line.split()
        rows.append((symbol, int(duration), tuple(int(target) for target in pitch_targets)))
    return rows


def _build_tilde_file(tmp_path: Path, prefix: str) -> tuple[Path, Path]:
    outdir = tmp_path / prefix
    outdir.mkdir(parents=True, exist_ok=True)
    _run_cli("akkapros.cli.syllabifier", str(INPUT_PROC), "-p", prefix, "--outdir", str(outdir))
    _run_cli("akkapros.cli.prosmaker", str(outdir / f"{prefix}_syl.txt"), "-p", prefix, "--outdir", str(outdir), "--style", "lob")
    return outdir / f"{prefix}_tilde.txt", outdir


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
    config_path = _write_regression_config(
        outdir / "regression.yaml",
        {
            ("common", "run.prefix"): prefix,
            ("common", "run.outdir"): str(outdir),
            ("prosody", "process.style"): "lob",
        },
    )

    _run_cli("akkapros.cli.atfparser", str(INPUT_ATF), "--conf", str(config_path))
    proc_file = outdir / f"{prefix}_proc.txt"
    orig_file = outdir / f"{prefix}_orig.txt"
    trans_file = outdir / f"{prefix}_trans.txt"
    _assert_non_empty_text_file(proc_file)
    _assert_non_empty_text_file(orig_file)
    _assert_non_empty_text_file(trans_file)
    _assert_has_yaml_frontmatter(proc_file)
    _assert_has_yaml_frontmatter(orig_file)
    _assert_has_yaml_frontmatter(trans_file)

    _run_cli("akkapros.cli.syllabifier", str(proc_file), "--conf", str(config_path))
    syl_file = outdir / f"{prefix}_syl.txt"
    _assert_non_empty_text_file(syl_file)
    _assert_has_yaml_frontmatter(syl_file)

    _run_cli("akkapros.cli.prosmaker", str(syl_file), "--conf", str(config_path))
    tilde_file = outdir / f"{prefix}_tilde.txt"
    _assert_non_empty_text_file(tilde_file)
    _assert_has_yaml_frontmatter(tilde_file)

    _run_cli("akkapros.cli.phonetizer", str(tilde_file), "--conf", str(config_path))
    ophone_file = outdir / f"{prefix}_ophone.txt"
    phone_file = outdir / f"{prefix}_phone.txt"
    ombrola_file = outdir / f"{prefix}_ombrola.pho"
    mbrola_file = outdir / f"{prefix}_mbrola.pho"
    _assert_phone_artifact(ophone_file)
    _assert_phone_artifact(phone_file)
    _assert_pho_artifact(ombrola_file)
    _assert_pho_artifact(mbrola_file)

    _run_cli(
        "akkapros.cli.metricalc",
        str(phone_file),
        "--conf",
        str(config_path),
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
    _assert_metrics_artifact_paths_are_safe(metrics_txt, metrics_json, phone_file)

    _run_cli(
        "akkapros.cli.printer",
        str(phone_file),
        "--conf",
        str(config_path),
        "--acute",
        "--bold",
        "--ipa",
        "--xar",
    )
    printer_outputs = [
        outdir / f"{prefix}_accent_acute.txt",
        outdir / f"{prefix}_accent_bold.md",
        outdir / f"{prefix}_accent_ipa.txt",
        outdir / f"{prefix}_accent_xar.txt",
        outdir / f"{prefix}_xar.txt",
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
        printer_outputs[0]: STAGE_REF_DIR / "expected_e2e_accent_acute.txt",
        printer_outputs[1]: STAGE_REF_DIR / "expected_e2e_accent_bold.md",
        printer_outputs[2]: STAGE_REF_DIR / "expected_e2e_accent_ipa.txt",
        printer_outputs[3]: STAGE_REF_DIR / "expected_e2e_accent_xar.txt",
        printer_outputs[4]: STAGE_REF_DIR / "expected_e2e_xar.txt",
    }
    for generated, reference in reference_map.items():
        _assert_matches_reference(generated, reference)


def test_phonetizer_preflight_fails_before_phase2_on_blocking_config(tmp_path: Path) -> None:
    tilde_file, outdir = _build_tilde_file(tmp_path, 'verify_blocking')
    prefix = 'verify_blocking'
    config = apply_overrides(
        build_default_config(),
        {('phonetize', 'process.timing_model.speech.pause_ratio'): 100},
    )
    config_path = outdir / 'verify.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    proc = _run_cli_expect_failure(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '-p',
        prefix,
        '--outdir',
        str(outdir),
        '--conf',
        str(config_path),
    )

    assert proc.returncode == 2
    assert 'FAIL phonetize.process.timing_model.speech.pause_ratio' in proc.stderr
    assert 'Phonetizer preflight failed before Phase 2 processing continued.' in proc.stderr
    assert not (outdir / f'{prefix}_ophone.txt').exists()
    assert not (outdir / f'{prefix}_phone.txt').exists()
    assert not (outdir / f'{prefix}_ombrola.pho').exists()
    assert not (outdir / f'{prefix}_mbrola.pho').exists()


def test_phonetizer_preflight_reports_warnings_without_blocking(tmp_path: Path) -> None:
    tilde_file, outdir = _build_tilde_file(tmp_path, 'verify_warning')
    prefix = 'verify_warning'
    config = apply_overrides(
        build_default_config(),
        {('phonetize', 'process.timing_model.speech.pause_ratio'): 71},
    )
    config_path = outdir / 'verify.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    proc = _run_cli(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '-p',
        prefix,
        '--outdir',
        str(outdir),
        '--conf',
        str(config_path),
    )

    assert 'WARN phonetize.process.timing_model.speech.pause_ratio' in proc.stderr
    assert (outdir / f'{prefix}_ophone.txt').exists()
    assert (outdir / f'{prefix}_phone.txt').exists()
    assert (outdir / f'{prefix}_ombrola.pho').exists()
    assert (outdir / f'{prefix}_mbrola.pho').exists()


def test_printer_accepts_defaults_only_runtime_config_plus_path_override(tmp_path: Path) -> None:
    tilde_file, outdir = _build_tilde_file(tmp_path, 'printer_runtime_defaults')
    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '-p', 'printer_runtime_defaults', '--outdir', str(outdir))
    phone_file = outdir / 'printer_runtime_defaults_phone.txt'

    _run_cli(
        'akkapros.cli.printer',
        str(phone_file),
        '--outdir',
        str(outdir),
        '--option',
        'print.run.ipa=true',
    )

    assert (outdir / 'akkapros_accent_ipa.txt').exists()


def test_phonetizer_pho_outputs_xsampa_while_phone_rows_keep_realization_codes(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_xsampa'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'sample_tilde.txt'
    tilde_file.write_text('ḥa ḫa ʿa ʾa qa\n', encoding='utf-8')

    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '-p', 'sample', '--outdir', str(outdir))

    phone_body = _strip_yaml_frontmatter(_read_text(outdir / 'sample_phone.txt'))
    ophone_body = _strip_yaml_frontmatter(_read_text(outdir / 'sample_ophone.txt'))
    mbrola_rows = _parse_pho_artifact(outdir / 'sample_mbrola.pho')
    ombrola_rows = _parse_pho_artifact(outdir / 'sample_ombrola.pho')

    assert '|ET|' in phone_body
    assert '|HE|' in phone_body
    assert '|AI|' in phone_body
    assert '|AL|' in phone_body
    assert '|QU|' in phone_body
    assert '|AO|' in phone_body

    assert '|ET|' in ophone_body
    assert '|HE|' in ophone_body

    emitted_symbols = {symbol for symbol, _duration, _frequency in mbrola_rows}
    assert {'X', 'x', 'H', '?', 'q', 'a.', '_'}.issubset(emitted_symbols)
    assert not emitted_symbols.intersection({'ET', 'HE', 'AI', 'AL', 'QU', 'AO', 'SP', 'ZP'})

    original_symbols = {symbol for symbol, _duration, _frequency in ombrola_rows}
    assert '_' in original_symbols
    assert 'a.' in original_symbols


def test_phonetizer_cli_keeps_short_vowel_anchor_under_higher_cvc_reference(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_short_vowel_anchor'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'anchor_tilde.txt'
    tilde_file.write_text('qat\n', encoding='utf-8')

    config = apply_overrides(
        _load_regression_config(),
        {('phonetize', 'process.timing_model.durations.cvc_reference'): 350},
    )
    config_path = outdir / 'anchor.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    _run_cli(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '-p',
        'anchor',
        '--outdir',
        str(outdir),
        '--conf',
        str(config_path),
    )

    phone_body = _strip_yaml_frontmatter(_read_text(outdir / 'anchor_phone.txt'))
    phone_rows = [parse_phone_row(line) for line in phone_body.strip().splitlines()]

    vowel_row = next(row for row in phone_rows if row['category'] == 'V')
    assert vowel_row['text'] == 'a'
    assert vowel_row['duration'] == '0110'


def test_phonetizer_cli_inserts_mini_pause_without_changing_reconstructed_tilde(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_mini_pause'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'mini_tilde.txt'
    tilde_file.write_text('qat pa\n', encoding='utf-8')

    config = apply_overrides(
        _load_regression_config(),
        {
            ('phonetize', 'process.timing_model.durations.cvc_reference'): 350,
            ('phonetize', 'process.timing_model.durations.pauses.mini.min'): 50,
            ('phonetize', 'process.timing_model.durations.pauses.mini.max'): 80,
        },
    )
    config_path = outdir / 'mini.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    _run_cli(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '-p',
        'mini',
        '--outdir',
        str(outdir),
        '--conf',
        str(config_path),
    )

    phone_text = _read_text(outdir / 'mini_phone.txt')
    frontmatter, phone_body = split_frontmatter(phone_text)
    assert frontmatter is not None
    phone_rows = [parse_phone_row(line) for line in phone_body.strip().splitlines()]

    mini_rows = [row for row in phone_rows if row['category'] == 'S' and row['text'] == MINI_PAUSE_TEXT]
    assert len(mini_rows) == 1
    assert mini_rows[0]['label'] == MINI_PAUSE_LABEL
    assert mini_rows[0]['type'] == MINI_PAUSE_TYPE
    assert mini_rows[0]['realization'] == MINI_PAUSE_REALIZATION
    assert mini_rows[0]['duration'] == '0064'
    assert reconstruct_tilde_from_phone_rows(phone_rows) == 'qat pa\n'
    assert frontmatter['metadata']['data']['phonetize']['phone_row_count'] == len(phone_rows)


def test_phonetizer_cli_coalesces_consecutive_newlines_but_preserves_eol_text(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_eol_coalesce'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'eol_tilde.txt'
    tilde_file.write_text('ba\n\n\nma', encoding='utf-8')

    _run_cli(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '-p',
        'eol',
        '--outdir',
        str(outdir),
    )

    phone_text = _read_text(outdir / 'eol_phone.txt')
    frontmatter, phone_body = split_frontmatter(phone_text)
    assert frontmatter is not None

    phone_rows = [parse_phone_row(line) for line in phone_body.strip().splitlines()]
    newline_rows = [row for row in phone_rows if row['category'] == 'S' and '<EOL>' in row['text']]

    assert len(newline_rows) == 2
    assert [row['text'] for row in newline_rows] == ['<EOL><EOL><EOL>', '<EOL>']
    assert reconstruct_tilde_from_phone_rows(phone_rows) == 'ba\n\n\nma\n'
    assert frontmatter['metadata']['data']['phonetize']['phone_row_count'] == len(phone_rows)


def test_printer_corrects_het_mapping_across_xar_and_ipa_modes(tmp_path: Path) -> None:
    outdir = tmp_path / 'printer_het_mapping'
    outdir.mkdir(parents=True, exist_ok=True)

    proc_file = outdir / 'het_proc.txt'
    proc_file.write_text('ḥa ḫa ʿa ʾa\n', encoding='utf-8')

    _run_cli('akkapros.cli.syllabifier', str(proc_file), '-p', 'het', '--outdir', str(outdir))
    _run_cli('akkapros.cli.prosmaker', str(outdir / 'het_syl.txt'), '-p', 'het', '--outdir', str(outdir), '--style', 'lob')
    _run_cli('akkapros.cli.phonetizer', str(outdir / 'het_tilde.txt'), '-p', 'het', '--outdir', str(outdir))

    phone_file = outdir / 'het_phone.txt'

    _run_cli('akkapros.cli.printer', str(phone_file), '-p', 'het_preserve', '--outdir', str(outdir), '--ipa')
    _run_cli(
        'akkapros.cli.printer',
        str(phone_file),
        '-p',
        'het_replace',
        '--outdir',
        str(outdir),
        '--ipa',
        '--ipa-proto-semitic',
        'replace',
        '--xar',
    )

    preserve_body = _strip_yaml_frontmatter(_read_text(outdir / 'het_preserve_accent_ipa.txt'))
    replace_ipa_body = _strip_yaml_frontmatter(_read_text(outdir / 'het_replace_accent_ipa.txt'))
    replace_xar_body = _strip_yaml_frontmatter(_read_text(outdir / 'het_replace_xar.txt'))

    assert 'ħa' in preserve_body
    assert 'χa' in preserve_body
    assert 'ʕa' in preserve_body
    assert 'ʔa' in preserve_body

    assert replace_ipa_body.count('ʔa') >= 3
    assert 'χa' in replace_ipa_body
    assert 'ħa' not in replace_ipa_body

    assert replace_xar_body.count("'a") >= 3
    assert 'ḫa' in replace_xar_body


def test_prosmaker_path_override_wins_over_dedicated_flag(tmp_path: Path) -> None:
    outdir = tmp_path / 'prosmaker_override'
    outdir.mkdir(parents=True, exist_ok=True)

    _run_cli('akkapros.cli.syllabifier', str(INPUT_PROC), '--outdir', str(outdir))
    syl_file = outdir / 'akkapros_syl.txt'

    _run_cli(
        'akkapros.cli.prosmaker',
        str(syl_file),
        '--outdir',
        str(outdir),
        '--style',
        'sob',
        '--option',
        'prosody.process.style=lob',
    )

    tilde_file = outdir / 'akkapros_tilde.txt'
    frontmatter, _body = split_frontmatter(_read_text(tilde_file))
    assert frontmatter is not None
    assert frontmatter['metadata']['options']['style'] == 'lob'


def test_cli_stage_pipeline_outputs_all_files_in_mono_mode(tmp_path: Path) -> None:
    """Run each stage CLI in sequence with prosody mono mode and pin outputs."""
    outdir = tmp_path / "stage_pipeline_mono"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = "e2e_mono"
    config_path = _write_regression_config(
        outdir / "regression_mono.yaml",
        {
            ("common", "run.prefix"): prefix,
            ("common", "run.outdir"): str(outdir),
            ("prosody", "process.style"): "lob",
            ("prosody", "process.mora_mode"): "mono",
        },
    )

    _run_cli("akkapros.cli.atfparser", str(INPUT_ATF), "--conf", str(config_path))
    proc_file = outdir / f"{prefix}_proc.txt"
    orig_file = outdir / f"{prefix}_orig.txt"
    trans_file = outdir / f"{prefix}_trans.txt"
    _assert_non_empty_text_file(proc_file)
    _assert_non_empty_text_file(orig_file)
    _assert_non_empty_text_file(trans_file)
    _assert_has_yaml_frontmatter(proc_file)
    _assert_has_yaml_frontmatter(orig_file)
    _assert_has_yaml_frontmatter(trans_file)

    _run_cli("akkapros.cli.syllabifier", str(proc_file), "--conf", str(config_path))
    syl_file = outdir / f"{prefix}_syl.txt"
    _assert_non_empty_text_file(syl_file)
    _assert_has_yaml_frontmatter(syl_file)

    _run_cli("akkapros.cli.prosmaker", str(syl_file), "--conf", str(config_path))
    tilde_file = outdir / f"{prefix}_tilde.txt"
    _assert_non_empty_text_file(tilde_file)
    _assert_has_yaml_frontmatter(tilde_file)
    tilde_frontmatter, tilde_body = split_frontmatter(_read_text(tilde_file))
    assert tilde_frontmatter is not None
    assert tilde_frontmatter["metadata"]["options"]["mora_mode"] == "mono"
    assert GOLD_MONO_TILDE_SAMPLE_LINE in tilde_body

    _run_cli("akkapros.cli.phonetizer", str(tilde_file), "--conf", str(config_path))
    ophone_file = outdir / f"{prefix}_ophone.txt"
    phone_file = outdir / f"{prefix}_phone.txt"
    ombrola_file = outdir / f"{prefix}_ombrola.pho"
    mbrola_file = outdir / f"{prefix}_mbrola.pho"
    _assert_phone_artifact(ophone_file)
    _assert_phone_artifact(phone_file)
    _assert_pho_artifact(ombrola_file)
    _assert_pho_artifact(mbrola_file)

    _run_cli(
        "akkapros.cli.metricalc",
        str(phone_file),
        "--conf",
        str(config_path),
        "--ophone",
        str(ophone_file),
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
    _assert_metrics_artifact_paths_are_safe(metrics_txt, metrics_json, phone_file)

    _run_cli(
        "akkapros.cli.printer",
        str(phone_file),
        "--conf",
        str(config_path),
        "--acute",
        "--bold",
        "--ipa",
        "--xar",
    )
    printer_outputs = [
        outdir / f"{prefix}_accent_acute.txt",
        outdir / f"{prefix}_accent_bold.md",
        outdir / f"{prefix}_accent_ipa.txt",
        outdir / f"{prefix}_accent_xar.txt",
        outdir / f"{prefix}_xar.txt",
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
        printer_outputs[0]: STAGE_REF_DIR / "expected_e2e_mono_accent_acute.txt",
        printer_outputs[1]: STAGE_REF_DIR / "expected_e2e_mono_accent_bold.md",
        printer_outputs[2]: STAGE_REF_DIR / "expected_e2e_mono_accent_ipa.txt",
        printer_outputs[3]: STAGE_REF_DIR / "expected_e2e_mono_accent_xar.txt",
        printer_outputs[4]: STAGE_REF_DIR / "expected_e2e_mono_xar.txt",
    }
    for generated, reference in reference_map.items():
        _assert_matches_reference(generated, reference)


def test_cli_fullprosmaker_gold_standard_reference(tmp_path: Path) -> None:
    """Run fullprosmaker and assert pinned metrics + reference outputs."""
    outdir = tmp_path / "full_pipeline"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = "test"
    config_path = _write_regression_config(
        outdir / "fullprosmaker_regression.yaml",
        {
            ("common", "run.prefix"): prefix,
            ("common", "run.outdir"): str(outdir),
            ("prosody", "process.style"): "lob",
        },
    )

    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "--conf",
        str(config_path),
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
        outdir / "test_ophone.txt",
        outdir / "test_phone.txt",
        outdir / "test_ombrola.pho",
        outdir / "test_mbrola.pho",
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
    metrics_json = json.loads(_read_text(outdir / "test.json"))
    _assert_nested_expected(metrics_json["original"], GOLD_REGULAR_METRICS["original"])
    _assert_nested_expected(metrics_json["accentuated"], GOLD_REGULAR_METRICS["accentuated"])
    _assert_nested_expected(metrics_json["accentuation_stats"], GOLD_REGULAR_METRICS["accentuation_stats"])

    for expected_line in [
        "Total syllables: 23 syllables",
        "Total words: 8 words",
        "Total words: 7 words",
        "Function words: 1 words",
        "Prominence candidates: 7 words",
        "%C: 27.63%",
        "%V: 31.11%",
            "%C: 27.67%",
            "%V: 32.69%",
        "VarcoC: 49.25",
            "VarcoC: 55.46",
        "Accentuation rate: 21.74%",
        "Accentuated syllables: 5 syllables",
        "Drift max: 115.00 ms",
            "Drift max: 134.00 ms",
    ]:
        assert expected_line in metrics_text
    assert metrics_text.count("Speech metrics:") == 2
    assert "Speech rate (original):" not in metrics_text
    assert "Speech rate (accentuated):" not in metrics_text
    assert "Pause metrics:" not in metrics_text
    assert "Pause duration allocation" not in metrics_text

    tilde_text = _read_text(outdir / "test_tilde.txt")
    assert GOLD_TILDE_SAMPLE_LINE in tilde_text, "Pinned sample line not found in _tilde output"

    full_reference_map = {
        outdir / "test_syl.txt": FULL_REF_DIR / "expected_test_syl.txt",
        outdir / "test_tilde.txt": FULL_REF_DIR / "expected_test_tilde.txt",
        outdir / "test_accent_acute.txt": FULL_REF_DIR / "expected_test_accent_acute.txt",
        outdir / "test_accent_bold.md": FULL_REF_DIR / "expected_test_accent_bold.md",
        outdir / "test_accent_ipa.txt": FULL_REF_DIR / "expected_test_accent_ipa.txt",
        outdir / "test_accent_xar.txt": FULL_REF_DIR / "expected_test_accent_xar.txt",
        outdir / "test_xar.txt": FULL_REF_DIR / "expected_test_xar.txt",
    }
    for generated, reference in full_reference_map.items():
        _assert_matches_reference(generated, reference)

    _assert_metrics_artifact_paths_are_safe(outdir / "test_metrics.txt", outdir / "test.json", outdir / "test_phone.txt")


def test_cli_fullprosmaker_mono_reference(tmp_path: Path) -> None:
    """Run fullprosmaker in mono mode and assert pinned reference outputs."""
    outdir = tmp_path / "full_pipeline_mono"
    outdir.mkdir(parents=True, exist_ok=True)
    prefix = "test_mono"
    config_path = _write_regression_config(
        outdir / "fullprosmaker_regression_mono.yaml",
        {
            ("common", "run.prefix"): prefix,
            ("common", "run.outdir"): str(outdir),
            ("prosody", "process.style"): "lob",
            ("prosody", "process.mora_mode"): "mono",
        },
    )

    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "--conf",
        str(config_path),
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
        outdir / "test_mono_ophone.txt",
        outdir / "test_mono_phone.txt",
        outdir / "test_mono_ombrola.pho",
        outdir / "test_mono_mbrola.pho",
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
    _assert_nested_expected(metrics_json["original"], GOLD_MONO_METRICS["original"])
    _assert_nested_expected(metrics_json["accentuated"], GOLD_MONO_METRICS["accentuated"])
    _assert_nested_expected(metrics_json["accentuation_stats"], GOLD_MONO_METRICS["accentuation_stats"])

    tilde_frontmatter, tilde_body = split_frontmatter(_read_text(outdir / "test_mono_tilde.txt"))
    assert tilde_frontmatter is not None
    assert tilde_frontmatter["metadata"]["options"]["mora_mode"] == "mono"
    assert GOLD_MONO_TILDE_SAMPLE_LINE in tilde_body

    metrics_text = _read_text(outdir / "test_mono_metrics.txt")
    for expected_line in [
        "Total syllables: 23 syllables",
        "Total words: 8 words",
        "Total words: 7 words",
        "%C: 27.63%",
        "%V: 31.11%",
            "%C: 29.16%",
            "%V: 32.32%",
        "VarcoC: 49.25",
            "VarcoC: 65.30",
        "Accentuated syllables: 7 syllables",
        "Accentuation rate: 30.43%",
    ]:
        assert expected_line in metrics_text
    assert metrics_text.count("Speech metrics:") == 2
    assert "Pause metrics:" not in metrics_text
    assert "Pause duration allocation" not in metrics_text

    full_reference_map = {
        outdir / "test_mono_syl.txt": FULL_REF_DIR / "expected_test_syl.txt",
        outdir / "test_mono_tilde.txt": FULL_REF_DIR / "expected_test_mono_tilde.txt",
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
        outdir / "test_mono_phone.txt",
    )


def test_metricalc_removed_csv_flag_is_rejected(tmp_path: Path) -> None:
    outdir = tmp_path / "removed_metricalc_csv"
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
    _run_cli(
        "akkapros.cli.phonetizer",
        str(outdir / "legacy_tilde.txt"),
        "-p",
        "legacy",
        "--outdir",
        str(outdir),
    )

    proc = _run_cli_expect_failure(
        "akkapros.cli.metricalc",
        str(outdir / "legacy_phone.txt"),
        "-p",
        "legacy",
        "--outdir",
        str(outdir),
        "--csv",
    )

    assert proc.returncode == 2
    assert "unrecognized arguments: --csv" in proc.stderr
    assert not (outdir / "legacy_metrics.txt").exists()
    assert not (outdir / "legacy_metrics.csv").exists()


def test_fullprosmaker_removed_metrics_csv_flag_is_rejected(tmp_path: Path) -> None:
    outdir = tmp_path / "removed_fullprosmaker_csv"
    outdir.mkdir(parents=True, exist_ok=True)

    proc = _run_cli_expect_failure(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p",
        "legacy",
        "--outdir",
        str(outdir),
        "--metrics-csv",
    )

    assert proc.returncode == 2
    assert "unrecognized arguments: --metrics-csv" in proc.stderr
    assert not (outdir / "legacy_metrics.txt").exists()
    assert not (outdir / "legacy.csv").exists()


def test_metricalc_fails_clearly_when_derived_ophone_is_missing(tmp_path: Path) -> None:
    outdir = tmp_path / "missing_ophone"
    outdir.mkdir(parents=True, exist_ok=True)
    phone_file = outdir / "broken_phone.txt"
    phone_file.write_text("AA-V-V-S-N-N-A-AA-0100:a\n", encoding="utf-8")

    proc = _run_cli_expect_failure(
        "akkapros.cli.metricalc",
        str(phone_file),
        "-p",
        "broken",
        "--outdir",
        str(outdir),
        "--table",
    )

    assert proc.returncode != 0
    assert "Derived original phone file does not exist" in (proc.stderr + proc.stdout)


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


def test_metricalc_rejects_removed_explicit_link_count_flag(tmp_path: Path) -> None:
    outdir = tmp_path / "explicit_override"
    outdir.mkdir(parents=True, exist_ok=True)
    _run_cli("akkapros.cli.syllabifier", str(INPUT_PROC), "-p", "override", "--outdir", str(outdir))
    _run_cli(
        "akkapros.cli.prosmaker",
        str(outdir / "override_syl.txt"),
        "-p",
        "override",
        "--outdir",
        str(outdir),
        "--style",
        "lob",
    )
    _run_cli(
        "akkapros.cli.phonetizer",
        str(outdir / "override_tilde.txt"),
        "-p",
        "override",
        "--outdir",
        str(outdir),
    )

    bad_flag = _run_cli_expect_failure(
        "akkapros.cli.metricalc",
        str(outdir / "override_phone.txt"),
        "-p",
        "override_bad_flag",
        "--outdir",
        str(outdir),
        "--table",
        "--explicit-link-count",
        "1",
    )
    assert bad_flag.returncode != 0
    assert "unrecognized arguments: --explicit-link-count 1" in (bad_flag.stderr + bad_flag.stdout)


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


def test_fullprosmaker_runs_from_config_file(tmp_path: Path) -> None:
    outdir = tmp_path / "config_fullprosmaker"
    config = apply_overrides(
        build_default_config(),
        {
            ("common", "run.prefix"): "cfgdemo",
            ("common", "run.outdir"): str(outdir),
            ("metrics", "run.json"): True,
            ("print", "run.ipa"): True,
            ("prosody", "process.style"): "sob",
        },
    )
    config_path = tmp_path / "fullprosmaker.yaml"
    config_path.write_text(dump_config_text(config), encoding="utf-8")

    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "--conf",
        str(config_path),
    )

    syl_file = outdir / "cfgdemo_syl.txt"
    tilde_file = outdir / "cfgdemo_tilde.txt"
    ophone_file = outdir / "cfgdemo_ophone.txt"
    phone_file = outdir / "cfgdemo_phone.txt"
    metrics_json = outdir / "cfgdemo.json"
    ipa_file = outdir / "cfgdemo_accent_ipa.txt"
    for path in [syl_file, tilde_file, ophone_file, phone_file, metrics_json, ipa_file]:
        _assert_non_empty_text_file(path)

    tilde_frontmatter, _ = split_frontmatter(_read_text(tilde_file))
    assert tilde_frontmatter is not None
    assert tilde_frontmatter["metadata"]["options"]["prosody_style"] == "sob"


def test_atfparser_cli_flag_overrides_config_file(tmp_path: Path) -> None:
    outdir = tmp_path / "config_override"
    config = apply_overrides(
        build_default_config(),
        {
            ("common", "run.prefix"): "from_config",
            ("common", "run.outdir"): str(outdir),
            ("atfparse", "process.preserve_case"): True,
        },
    )
    config_path = tmp_path / "atfparser.yaml"
    config_path.write_text(dump_config_text(config), encoding="utf-8")

    _run_cli(
        "akkapros.cli.atfparser",
        str(INPUT_ATF),
        "--conf",
        str(config_path),
        "--prefix",
        "from_cli",
    )

    proc_file = outdir / "from_cli_proc.txt"
    _assert_non_empty_text_file(proc_file)
    frontmatter, _ = split_frontmatter(_read_text(proc_file))
    assert frontmatter is not None
    assert frontmatter["metadata"]["options"]["preserve_case"] is True
    assert not (outdir / "from_config_proc.txt").exists()


def test_confwriter_generated_config_is_reused_by_cli(tmp_path: Path) -> None:
    outdir = tmp_path / "confwriter_reuse"
    config_path = tmp_path / "generated.yaml"

    _run_cli(
        "akkapros.cli.confwriter",
        "--conf",
        str(config_path),
        "--set",
        "common.run.prefix=writerdemo",
    )
    _run_cli(
        "akkapros.cli.confwriter",
        "--conf",
        str(config_path),
        "--set",
        f"common.run.outdir={outdir}",
        "--set",
        "atfparse.process.preserve_case=true",
    )

    _run_cli(
        "akkapros.cli.atfparser",
        str(INPUT_ATF),
        "--conf",
        str(config_path),
    )

    proc_file = outdir / "writerdemo_proc.txt"
    _assert_non_empty_text_file(proc_file)
    frontmatter, _ = split_frontmatter(_read_text(proc_file))
    assert frontmatter is not None
    assert frontmatter["metadata"]["options"]["preserve_case"] is True
