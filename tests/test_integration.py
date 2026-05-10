import os
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from akkapros.lib.config import apply_overrides, build_default_config, dump_config_text, load_config_file
from akkapros.lib.frontmatter import compose_text_document, split_frontmatter
from akkapros.lib.phonetize import (
    RESYNC_PAUSE_LABEL,
    RESYNC_PAUSE_REALIZATION,
    RESYNC_PAUSE_TEXT,
    RESYNC_PAUSE_TYPE,
    parse_phone_row,
    reconstruct_tilde_from_phone_rows,
)
from akkapros.lib.utils import format_path_for_logging

pytestmark = pytest.mark.integration


REPO_ROOT = Path(__file__).resolve().parents[1]
INTREF_DIR = REPO_ROOT / "tests" / "integration_refs"
STAGE_REF_DIR = INTREF_DIR / "stage_pipeline"
FULL_REF_DIR = INTREF_DIR / "fullprosmaker"
PHONEPREP_REF_DIR = INTREF_DIR / "phoneprep"
CR088_REF_DIR = INTREF_DIR / "cr088"
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
            "percent_c": 26.779487179487177,
            "percent_v": 30.164102564102564,
            "mean_c_ms": 108.79166666666667,
            "mean_v_ms": 127.8695652173913,
            "delta_c_ms": 53.581697097879314,
            "delta_v_ms": 36.18467649232811,
            "varco_c": 49.251655700846555,
            "varco_v": 28.298114903894817,
            "rpvi_c": 68.52173913043478,
            "npvi_v": 19.61582462860357,
        },
        "unit_drift": {
            "max": 75.0,
            "mean": 12.6667,
            "stddev": 35.5663,
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
                "total_words": 8,
                "syllables_per_word": {
                    "mean": 2.875,
                    "std": 0.6408699444616558,
                },
                "morae_per_word": {
                    "mean": 5.0,
                    "std": 1.511857892036909,
                },
            },
            "mora_stats": {
                "mean": 1.7391304347826086,
                "std": 0.91539317456032,
                "total": 40,
            },
        },
        "acoustic": {
            "percent_c": 27.95098039215686,
            "percent_v": 32.55882352941176,
            "mean_c_ms": 118.79166666666667,
            "mean_v_ms": 144.3913043478261,
            "delta_c_ms": 64.78938902749088,
            "delta_v_ms": 63.62166648339828,
            "varco_c": 54.54034853243708,
            "varco_v": 44.061979196572125,
            "rpvi_c": 84.17391304347827,
            "npvi_v": 33.50426605831368,
        },
        "unit_drift": {
            "max": 116.0,
            "mean": 2.4074,
            "stddev": 39.7131,
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
            "percent_c": 26.779487179487177,
            "percent_v": 30.164102564102564,
            "mean_c_ms": 108.79166666666667,
            "mean_v_ms": 127.8695652173913,
            "delta_c_ms": 53.581697097879314,
            "delta_v_ms": 36.18467649232811,
            "varco_c": 49.251655700846555,
            "varco_v": 28.298114903894817,
            "rpvi_c": 68.52173913043478,
            "npvi_v": 19.61582462860357,
        },
        "unit_drift": {
            "max": 75.0,
            "mean": 12.6667,
            "stddev": 35.5663,
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
                "V": 3,
                "CVC": 3,
                "CVC:": 2,
                "CV": 9,
                "VV:C": 1,
                "CVV": 1,
                "CVV:": 3,
                "VC:": 1,
            },
            "word_stats": {
                "total_words": 8,
                "syllables_per_word": {
                    "mean": 2.875,
                    "std": 0.6408699444616558,
                },
                "morae_per_word": {
                    "mean": 5.25,
                    "std": 1.5811388300841898,
                },
            },
            "mora_stats": {
                "mean": 1.826086956521739,
                "std": 0.9840627249521833,
                "total": 42,
            },
        },
        "acoustic": {
            "percent_c": 27.849246231155778,
            "percent_v": 31.055276381909547,
            "mean_c_ms": 115.45833333333333,
            "mean_v_ms": 134.34782608695653,
            "delta_c_ms": 62.10339440982451,
            "delta_v_ms": 44.11408992665168,
            "varco_c": 53.78857689771881,
            "varco_v": 32.83573036611613,
            "rpvi_c": 80.69565217391305,
            "npvi_v": 26.0051289916666,
        },
        "unit_drift": {
            "max": 84.0,
            "mean": 9.7778,
            "stddev": 39.3308,
        },
    },
    "accentuation_stats": {
        "accentuated_syllables": 7,
        "accentuation_rate": 30.434782608695656,
        "accentuation_types": {
            "CVC:": 2,
            "VC:": 1,
            "CVV:": 3,
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
    assert frontmatter['metadata']['data']['phonetize']['duration_scale'] > 0
    assert frontmatter['metadata']['data']['phonetize']['unit_drift']['max'] >= 0
    assert 'mean' in frontmatter['metadata']['data']['phonetize']['unit_drift']
    assert 'stddev' in frontmatter['metadata']['data']['phonetize']['unit_drift']
    assert 'syllable_count' in frontmatter['metadata']['data']['phonetize']
    assert 'pause_count' in frontmatter['metadata']['data']['phonetize']
    assert 'resync_pause_count' in frontmatter['metadata']['data']['phonetize']
    assert 'total_unit_count' in frontmatter['metadata']['data']['phonetize']
    assert 'unit_drift_extension_rate' in frontmatter['metadata']['data']['phonetize']
    assert 'non_accented_long_vowel_count' in frontmatter['metadata']['data']['phonetize']
    assert 'left_as_is_non_accented_long_vowel_count' in frontmatter['metadata']['data']['phonetize']
    assert 'drift_tolerance_effect' in frontmatter['metadata']['data']['phonetize']
    assert 'eligible_resync_pause_count' in frontmatter['metadata']['data']['phonetize']
    assert 'resync_pause_insertion_rate' in frontmatter['metadata']['data']['phonetize']
    assert 'pause_with_residual_drift_count' in frontmatter['metadata']['data']['phonetize']
    assert 'pause_with_residual_drift_rate' in frontmatter['metadata']['data']['phonetize']


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


@pytest.mark.slow
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


def test_phonetizer_rejects_removed_speech_config_before_processing(tmp_path: Path) -> None:
    tilde_file, outdir = _build_tilde_file(tmp_path, 'verify_removed_speech')
    prefix = 'verify_removed_speech'
    config_path = outdir / 'verify.yaml'
    config_path.write_text(
        'phonetize:\n'
        '  process:\n'
        '    timing_model:\n'
        '      speech:\n'
        '        wpm: 201\n',
        encoding='utf-8',
    )

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
    assert 'Removed config keys (CR-081): phonetize.process.timing_model.speech' in proc.stderr
    assert not (outdir / f'{prefix}_ophone.txt').exists()
    assert not (outdir / f'{prefix}_phone.txt').exists()
    assert not (outdir / f'{prefix}_ombrola.pho').exists()
    assert not (outdir / f'{prefix}_mbrola.pho').exists()


def test_phonetizer_rejects_removed_speech_option_path(tmp_path: Path) -> None:
    tilde_file, outdir = _build_tilde_file(tmp_path, 'verify_removed_option')
    prefix = 'verify_removed_option'

    proc = _run_cli_expect_failure(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '-p',
        prefix,
        '--outdir',
        str(outdir),
        '--option',
        'phonetize.process.timing_model.speech.pause_ratio=35',
    )

    assert proc.returncode == 2
    assert 'Removed config key (CR-081): phonetize.process.timing_model.speech.pause_ratio' in proc.stderr
    assert not (outdir / f'{prefix}_ophone.txt').exists()
    assert not (outdir / f'{prefix}_phone.txt').exists()
    assert not (outdir / f'{prefix}_ombrola.pho').exists()
    assert not (outdir / f'{prefix}_mbrola.pho').exists()


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


def test_phonetizer_cli_applies_pause_intonation_to_ophone_and_ombrola(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_original_pause_intonation'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'pause_tilde.txt'
    tilde_file.write_text('at·ta~?\n', encoding='utf-8')

    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '-p', 'pause', '--outdir', str(outdir))

    ophone_body = _strip_yaml_frontmatter(_read_text(outdir / 'pause_ophone.txt'))
    phone_body = _strip_yaml_frontmatter(_read_text(outdir / 'pause_phone.txt'))
    ophone_rows = [parse_phone_row(line) for line in ophone_body.strip().splitlines()]
    phone_rows = [parse_phone_row(line) for line in phone_body.strip().splitlines()]
    ombrola_rows = _parse_pho_artifact(outdir / 'pause_ombrola.pho')

    assert [row['intonation'] for row in ophone_rows[:2]] == ['M0C', 'M0C']
    assert [row['intonation'] for row in ophone_rows[2:4]] == ['H3C', 'H3C']
    assert ophone_rows[-2]['type'] == 'Q'
    assert ophone_rows[-2]['intonation'] == 'H3C'

    assert phone_rows[-2]['type'] == 'Q'
    assert phone_rows[-2]['intonation'] == 'H3C'
    assert any(any(target != 120 for target in targets) for _symbol, _duration, targets in ombrola_rows)


def test_printer_outputs_follow_limit_emphatic_coloring_configs(tmp_path: Path) -> None:
    outdir = tmp_path / 'cr088_printer_outputs'
    outdir.mkdir(parents=True, exist_ok=True)
    tilde_file = outdir / 'cr088_tilde.txt'
    tilde_file.write_text(_read_text(CR088_REF_DIR / 'extended_emphatic_coloring_sample_tilde.txt'), encoding='utf-8')

    cases = [
        (
            False,  # limit_emphatic_coloring: false = extended coloring enabled
            'limit_off',
            'expected_extended_emphatic_coloring_ipa.txt',
            'expected_extended_emphatic_coloring_xar.txt',
        ),
        (
            True,   # limit_emphatic_coloring: true = extended coloring disabled (legacy)
            'limit_on',
            'expected_legacy_emphatic_coloring_ipa.txt',
            'expected_legacy_emphatic_coloring_xar.txt',
        ),
    ]

    for limit_enabled, prefix, ipa_name, xar_name in cases:
        overrides = {('phonetize', 'process.realization.limit_emphatic_coloring'): limit_enabled}
        if limit_enabled:
            overrides[('phonetize', 'process.allow_experimental')] = True
        config_path = _write_regression_config(
            outdir / f'{prefix}.yaml',
            overrides,
        )
        _run_cli(
            'akkapros.cli.phonetizer',
            str(tilde_file),
            '--conf',
            str(config_path),
            '-p',
            prefix,
            '--outdir',
            str(outdir),
        )
        _run_cli(
            'akkapros.cli.printer',
            str(outdir / f'{prefix}_phone.txt'),
            '-p',
            prefix,
            '--outdir',
            str(outdir),
            '--ophone',
            str(outdir / f'{prefix}_ophone.txt'),
            '--ipa',
            '--xar',
        )

        ipa_body = _strip_yaml_frontmatter(_read_text(outdir / f'{prefix}_accent_ipa.txt'))
        xar_body = _strip_yaml_frontmatter(_read_text(outdir / f'{prefix}_accent_xar.txt'))
        expected_ipa = _read_text(CR088_REF_DIR / ipa_name)
        expected_xar = _read_text(CR088_REF_DIR / xar_name)
        if not expected_ipa.endswith('\n'):
            expected_ipa += '\n'
        if not expected_xar.endswith('\n'):
            expected_xar += '\n'

        assert ipa_body == expected_ipa
        assert xar_body == expected_xar


def test_phonetizer_cli_ratio_override_changes_corrective_same_consonant_split(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_corrective_ratio'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'ratio_tilde.txt'
    tilde_file.write_text('at·ta\n', encoding='utf-8')

    config = apply_overrides(
        build_default_config(),
        {
            ('common', 'run.prefix'): 'ratio',
            ('common', 'run.outdir'): str(outdir),
            ('phonetize', 'process.timing_model.durations.consonants.closure.geminate_coda_ratio'): 0.4,
        },
    )
    config_path = outdir / 'ratio.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '--conf', str(config_path))

    phone_rows = [
        parse_phone_row(line)
        for line in _strip_yaml_frontmatter(_read_text(outdir / 'ratio_phone.txt')).strip().splitlines()
    ]

    assert phone_rows[1]['text'] == 't'
    assert phone_rows[1]['duration'] == '0070'
    assert phone_rows[2]['text'] == 't'
    assert phone_rows[2]['duration'] == '0105'


def test_phonetizer_cli_uses_frontmatter_mora_mode_for_half_beat_alignment(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_half_beat_alignment'
    outdir.mkdir(parents=True, exist_ok=True)

    config = apply_overrides(
        _load_regression_config(),
        {
            ('phonetize', 'process.timing_model.durations.cvc_reference'): 305,
            ('phonetize', 'process.timing_model.durations.pauses.short.min'): 600,
            ('phonetize', 'process.timing_model.durations.pauses.short.max'): 850,
        },
    )
    config_path = outdir / 'half_beat.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    bi_tilde = outdir / 'bi_tilde.txt'
    bi_tilde.write_text(
        compose_text_document(
            {
                'pipeline': 'pipeline',
                'file': {'id': 'bi-tilde', 'title': 'bi tilde', 'format': 'tilde', 'version': '1.0.0'},
                'metadata': {'options': {'mora_mode': 'bi'}},
            },
            'qat,\n',
        ),
        encoding='utf-8',
    )
    mono_tilde = outdir / 'mono_tilde.txt'
    mono_tilde.write_text(
        compose_text_document(
            {
                'pipeline': 'pipeline',
                'file': {'id': 'mono-tilde', 'title': 'mono tilde', 'format': 'tilde', 'version': '1.0.0'},
                'metadata': {'options': {'mora_mode': 'mono'}},
            },
            'qat,\n',
        ),
        encoding='utf-8',
    )

    _run_cli('akkapros.cli.phonetizer', str(bi_tilde), '-p', 'bi', '--outdir', str(outdir), '--conf', str(config_path))
    _run_cli('akkapros.cli.phonetizer', str(mono_tilde), '-p', 'mono', '--outdir', str(outdir), '--conf', str(config_path))

    bi_phone_rows = [parse_phone_row(line) for line in _strip_yaml_frontmatter(_read_text(outdir / 'bi_phone.txt')).strip().splitlines()]
    bi_ophone_rows = [parse_phone_row(line) for line in _strip_yaml_frontmatter(_read_text(outdir / 'bi_ophone.txt')).strip().splitlines()]
    mono_phone_rows = [parse_phone_row(line) for line in _strip_yaml_frontmatter(_read_text(outdir / 'mono_phone.txt')).strip().splitlines()]
    mono_ophone_rows = [parse_phone_row(line) for line in _strip_yaml_frontmatter(_read_text(outdir / 'mono_ophone.txt')).strip().splitlines()]

    bi_phone_short_pause = next(row for row in bi_phone_rows if row['category'] == 'S' and row['text'] == ',')
    bi_ophone_short_pause = next(row for row in bi_ophone_rows if row['category'] == 'S' and row['text'] == ',')
    mono_phone_short_pause = next(row for row in mono_phone_rows if row['category'] == 'S' and row['text'] == ',')
    mono_ophone_short_pause = next(row for row in mono_ophone_rows if row['category'] == 'S' and row['text'] == ',')

    assert bi_phone_short_pause['duration'] == '0629'
    assert bi_ophone_short_pause['duration'] == '0782'
    assert mono_phone_short_pause['duration'] == '0782'
    assert mono_ophone_short_pause['duration'] == '0782'


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


def test_phonetizer_cli_applies_pre_pausal_final_anchor_overrides_before_punctuation_owned_pause(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_final_anchor_override'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'final_anchor_tilde.txt'
    tilde_file.write_text('qat,\n', encoding='utf-8')

    config = apply_overrides(
        _load_regression_config(),
        {
            ('common', 'run.prefix'): 'final_anchor',
            ('common', 'run.outdir'): str(outdir),
            ('phonetize', 'process.timing_model.durations.consonants.closure.coda_final'): 120,
        },
    )
    config_path = outdir / 'final_anchor.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '--conf', str(config_path))

    phone_rows = [
        parse_phone_row(line)
        for line in _strip_yaml_frontmatter(_read_text(outdir / 'final_anchor_phone.txt')).strip().splitlines()
    ]

    coda_row = next(row for row in phone_rows if row['position'] == 'C' and row['text'] == 't')
    assert coda_row['duration'] == '0120'


def test_phonetizer_cli_inserts_resync_pause_without_changing_reconstructed_tilde(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_resync_pause'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'resync_tilde.txt'
    tilde_file.write_text('qat pa\n', encoding='utf-8')

    config = apply_overrides(
        _load_regression_config(),
        {
            ('phonetize', 'process.allow_experimental'): True,
            ('phonetize', 'process.timing_model.enable_resync_pause'): True,
            ('phonetize', 'process.timing_model.durations.cvc_reference'): 350,
            ('phonetize', 'process.timing_model.durations.pauses.resync.min'): 50,
            ('phonetize', 'process.timing_model.durations.pauses.resync.max'): 80,
        },
    )
    config_path = outdir / 'resync.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    _run_cli(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '-p',
        'resync',
        '--outdir',
        str(outdir),
        '--conf',
        str(config_path),
    )

    phone_text = _read_text(outdir / 'resync_phone.txt')
    frontmatter, phone_body = split_frontmatter(phone_text)
    assert frontmatter is not None
    phone_rows = [parse_phone_row(line) for line in phone_body.strip().splitlines()]

    resync_rows = [row for row in phone_rows if row['category'] == 'S' and row['text'] == RESYNC_PAUSE_TEXT]
    assert len(resync_rows) == 1
    assert resync_rows[0]['label'] == RESYNC_PAUSE_LABEL
    assert resync_rows[0]['type'] == RESYNC_PAUSE_TYPE
    assert resync_rows[0]['realization'] == RESYNC_PAUSE_REALIZATION
    assert resync_rows[0]['duration'] == '0064'
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


def test_phonetizer_cli_drift_tolerance_changes_rates_without_changing_population_denominators(tmp_path: Path) -> None:
    outdir = tmp_path / 'phonetizer_probability_diagnostics'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'diag_tilde.txt'
    tilde_file.write_text('qā\n', encoding='utf-8')

    low_config = apply_overrides(
        _load_regression_config(),
        {
            ('common', 'run.prefix'): 'low',
            ('common', 'run.outdir'): str(outdir),
            ('phonetize', 'process.timing_model.durations.drift_tolerance'): 1,
            ('phonetize', 'process.timing_model.durations.cvc_reference'): 340,
        },
    )
    high_config = apply_overrides(
        _load_regression_config(),
        {
            ('common', 'run.prefix'): 'high',
            ('common', 'run.outdir'): str(outdir),
            ('phonetize', 'process.timing_model.durations.drift_tolerance'): 500,
            ('phonetize', 'process.timing_model.durations.cvc_reference'): 340,
        },
    )
    low_config_path = outdir / 'low.yaml'
    high_config_path = outdir / 'high.yaml'
    low_config_path.write_text(dump_config_text(low_config), encoding='utf-8')
    high_config_path.write_text(dump_config_text(high_config), encoding='utf-8')

    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '--conf', str(low_config_path))
    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '--conf', str(high_config_path))

    low_frontmatter, _ = split_frontmatter(_read_text(outdir / 'low_phone.txt'))
    high_frontmatter, _ = split_frontmatter(_read_text(outdir / 'high_phone.txt'))
    assert low_frontmatter is not None
    assert high_frontmatter is not None

    low_data = low_frontmatter['metadata']['data']['phonetize']
    high_data = high_frontmatter['metadata']['data']['phonetize']

    assert low_data['syllable_count'] == high_data['syllable_count'] == 1
    assert low_data['non_accented_long_vowel_count'] == high_data['non_accented_long_vowel_count'] == 1
    assert low_data['drift_tolerance_effect'] < high_data['drift_tolerance_effect']


def test_printer_corrects_het_mapping_across_xar_and_ipa_modes(tmp_path: Path) -> None:
    """Verify printer IPA and XAR mappings for proto-Semitic consonants.

    The proto-Semitic replacement now happens in the phonetizer stage
    (via replace_proto_semitic), not in the printer. The printer uses a
    single IPA_MAP: ḥ→ʔ, ḫ→χ, ʿ→ʔ, ʾ→ʔ.
    """
    outdir = tmp_path / 'printer_het_mapping'
    outdir.mkdir(parents=True, exist_ok=True)

    proc_file = outdir / 'het_proc.txt'
    proc_file.write_text('ḥa ḫa ʿa ʾa\n', encoding='utf-8')

    _run_cli('akkapros.cli.syllabifier', str(proc_file), '-p', 'het', '--outdir', str(outdir))
    _run_cli('akkapros.cli.prosmaker', str(outdir / 'het_syl.txt'), '-p', 'het', '--outdir', str(outdir), '--style', 'lob')
    _run_cli('akkapros.cli.phonetizer', str(outdir / 'het_tilde.txt'), '-p', 'het', '--outdir', str(outdir))

    phone_file = outdir / 'het_phone.txt'
    _run_cli(
        'akkapros.cli.printer',
        str(phone_file),
        '-p',
        'het',
        '--outdir',
        str(outdir),
        '--ipa',
        '--xar',
    )

    ipa_body = _strip_yaml_frontmatter(_read_text(outdir / 'het_accent_ipa.txt'))
    xar_body = _strip_yaml_frontmatter(_read_text(outdir / 'het_accent_xar.txt'))
    xar_plain_body = _strip_yaml_frontmatter(_read_text(outdir / 'het_xar.txt'))

    # IPA: ḥ→ʔ, ḫ→χ, ʿ→ʔ, ʾ→ʔ
    assert ipa_body.count('ʔa') >= 3
    assert 'χa' in ipa_body

    # XAR: ḥ→', ḫ→ḫ, ʿ→', ʾ→'
    assert xar_body.count("'a") >= 3
    assert 'ḫa' in xar_body

    # Plain XAR (no accent marks): same consonant mapping
    assert xar_plain_body.count("'a") >= 3
    assert 'ḫa' in xar_plain_body


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


@pytest.mark.slow
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


@pytest.mark.slow
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
        "Total words: 8 words",
        "Function words: 1 words",
        "Prominence candidates: 7 words",
        "%C: 26.78%",
        "%V: 30.16%",
            "%C: 27.95%",
            "%V: 32.56%",
        "VarcoC: 49.25",
            "VarcoC: 54.54",
        "Accentuation rate: 21.74%",
        "Accentuated syllables: 5 syllables",
        "Unit drift max: 75.00 ms",
            "Unit drift max: 116.00 ms",
        "Phonetizer diagnostics:",
        "Unit drift extension:",
        "Drift tolerance effect:",
        "Inserted resync pauses:",
        "Pauses with residual drift:",
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


@pytest.mark.slow
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
        "Total words: 8 words",
        "%C: 26.78%",
        "%V: 30.16%",
        "VarcoC: 49.25",
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







def test_phonetizer_cli_ultraheavy_hiatus_produces_y_files(tmp_path: Path) -> None:
    """Run phonetizer with ultraheavy_hiatus_enable=true and verify yphone/ymbrola output."""
    outdir = tmp_path / 'ultraheavy_yfiles'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'uh_tilde.txt'
    tilde_file.write_text('qû ba\n', encoding='utf-8')

    config = apply_overrides(
        _load_regression_config(),
        {
            ('common', 'run.prefix'): 'uh',
            ('common', 'run.outdir'): str(outdir),
            ('phonetize', 'process.allow_experimental'): True,
            ('phonetize', 'process.realization.ultraheavy_hiatus_enable'): True,
        },
    )
    config_path = outdir / 'uh.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    _run_cli('akkapros.cli.phonetizer', str(tilde_file), '--conf', str(config_path))

    # Standard files still produced
    phone_file = outdir / 'uh_phone.txt'
    ophone_file = outdir / 'uh_ophone.txt'
    mbrola_file = outdir / 'uh_mbrola.pho'
    ombrola_file = outdir / 'uh_ombrola.pho'
    _assert_phone_artifact(phone_file)
    _assert_phone_artifact(ophone_file)
    _assert_pho_artifact(mbrola_file)
    _assert_pho_artifact(ombrola_file)

    # Y-files produced
    yphone_file = outdir / 'uh_yphone.txt'
    yophone_file = outdir / 'uh_yophone.txt'
    ymbrola_file = outdir / 'uh_ymbrola.pho'
    yombrola_file = outdir / 'uh_yombrola.pho'
    _assert_non_empty_text_file(yphone_file)
    _assert_non_empty_text_file(yophone_file)
    _assert_non_empty_text_file(ymbrola_file)
    _assert_non_empty_text_file(yombrola_file)

    # Verify yphone has more rows than phone (circumflex expanded)
    phone_rows = [parse_phone_row(line) for line in _strip_yaml_frontmatter(_read_text(phone_file)).strip().splitlines()]
    yphone_rows = [parse_phone_row(line) for line in _strip_yaml_frontmatter(_read_text(yphone_file)).strip().splitlines()]
    assert len(yphone_rows) > len(phone_rows), 'yphone should have more rows due to circumflex expansion'

    # Verify the circumflex vowel (û) is expanded into 3 rows in yphone
    # Find the UWI rows in phone (1 row) vs yphone (3 rows)
    phone_uwi = [row for row in phone_rows if row['label'] == 'UWI']
    yphone_uwi = [row for row in yphone_rows if row['label'] == 'UWI']
    assert len(phone_uwi) == 1, 'phone should have 1 UWI row'
    assert len(yphone_uwi) == 2, 'yphone should have 2 UWI rows (vowel1 + vowel2)'

    # Verify transition row exists
    yphone_ena = [row for row in yphone_rows if row['label'] == 'ENA']
    assert len(yphone_ena) == 1, 'yphone should have 1 ENA transition row'

    # Verify timing: U1 + T + U2 = Z
    original_duration = int(phone_uwi[0]['duration'])
    u1_duration = int(yphone_uwi[0]['duration'])
    t_duration = int(yphone_ena[0]['duration'])
    u2_duration = int(yphone_uwi[1]['duration'])
    assert u1_duration + t_duration + u2_duration == original_duration, (
        f'Timing mismatch: {u1_duration} + {t_duration} + {u2_duration} != {original_duration}'
    )

    # Verify frontmatter has ultraheavy_hiatus_enable
    yphone_frontmatter, _ = split_frontmatter(_read_text(yphone_file))
    assert yphone_frontmatter is not None
    assert yphone_frontmatter['metadata']['options'].get('ultraheavy_hiatus_enable') is True

    # Verify ymbrola has more rows than mbrola
    mbrola_lines = _read_text(mbrola_file).strip().splitlines()
    ymbrola_lines = _read_text(ymbrola_file).strip().splitlines()
    assert len(ymbrola_lines) > len(mbrola_lines), 'ymbrola should have more rows due to circumflex expansion'

    # Verify standard phone/mbrola are unchanged (no y-files when disabled)
    outdir2 = tmp_path / 'ultraheavy_disabled'
    outdir2.mkdir(parents=True, exist_ok=True)
    tilde_file2 = outdir2 / 'uh_disabled_tilde.txt'
    tilde_file2.write_text('qû ba\n', encoding='utf-8')
    config2 = apply_overrides(
        _load_regression_config(),
        {
            ('common', 'run.prefix'): 'uh_disabled',
            ('common', 'run.outdir'): str(outdir2),
            ('phonetize', 'process.allow_experimental'): True,
        },
    )
    config_path2 = outdir2 / 'uh_disabled.yaml'
    config_path2.write_text(dump_config_text(config2), encoding='utf-8')
    _run_cli('akkapros.cli.phonetizer', str(tilde_file2), '--conf', str(config_path2))
    assert not (outdir2 / 'uh_disabled_yphone.txt').exists()
    assert not (outdir2 / 'uh_disabled_ymbrola.pho').exists()


def test_phonetizer_cli_ultraheavy_hiatus_rejects_without_experimental(tmp_path: Path) -> None:
    """Verify ultraheavy_hiatus_enable=true without allow_experimental=true raises error."""
    outdir = tmp_path / 'ultraheavy_reject'
    outdir.mkdir(parents=True, exist_ok=True)

    tilde_file = outdir / 'uh_reject_tilde.txt'
    tilde_file.write_text('qû\n', encoding='utf-8')

    config = apply_overrides(
        _load_regression_config(),
        {
            ('common', 'run.prefix'): 'uh_reject',
            ('common', 'run.outdir'): str(outdir),
            ('phonetize', 'process.realization.ultraheavy_hiatus_enable'): True,
        },
    )
    config_path = outdir / 'uh_reject.yaml'
    config_path.write_text(dump_config_text(config), encoding='utf-8')

    proc = _run_cli_expect_failure(
        'akkapros.cli.phonetizer',
        str(tilde_file),
        '--conf',
        str(config_path),
    )

    assert proc.returncode == 2
    assert 'allow_experimental' in proc.stderr
    assert 'ultraheavy_hiatus_enable' in proc.stderr
    assert not (outdir / 'uh_reject_yphone.txt').exists()
    assert not (outdir / 'uh_reject_ymbrola.pho').exists()


def test_fullprosmaker_max_lines_caps_input_and_records_in_frontmatter(tmp_path: Path) -> None:

    """--max-lines N caps the number of proc body lines and records input_max_lines in frontmatter."""
    outdir = tmp_path / "max_lines"
    outdir.mkdir(parents=True, exist_ok=True)
    # INPUT_PROC has 2 body lines; cap at 1 to exercise slicing
    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p", "maxlines",
        "--outdir", str(outdir),
        "--max-lines", "1",
    )
    syl_file = outdir / "maxlines_syl.txt"
    _assert_non_empty_text_file(syl_file)
    frontmatter, body = split_frontmatter(_read_text(syl_file))
    assert frontmatter is not None
    assert frontmatter["metadata"]["options"]["input_max_lines"] == 1
    non_empty_lines = [ln for ln in body.strip().splitlines() if ln.strip()]
    assert len(non_empty_lines) == 1


def test_fullprosmaker_fast_mode_applies_line_cap_and_records_fast_flag(tmp_path: Path) -> None:
    """--fast records fast_mode and input_max_lines in output frontmatter."""
    outdir = tmp_path / "fast_mode"
    outdir.mkdir(parents=True, exist_ok=True)
    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(INPUT_PROC),
        "-p", "fastmode",
        "--outdir", str(outdir),
        "--fast",
    )
    syl_file = outdir / "fastmode_syl.txt"
    _assert_non_empty_text_file(syl_file)
    frontmatter, body = split_frontmatter(_read_text(syl_file))
    assert frontmatter is not None
    assert frontmatter["metadata"]["options"]["fast_mode"] is True
    assert frontmatter["metadata"]["options"]["input_max_lines"] == 10
    # Pipeline still produces valid output
    _assert_non_empty_text_file(outdir / "fastmode_tilde.txt")
    _assert_non_empty_text_file(outdir / "fastmode_phone.txt")







