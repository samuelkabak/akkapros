import os
import argparse
import subprocess
import sys
from pathlib import Path

import pytest

from akkapros.lib.config import (
    ConfigError,
    add_config_argument,
    apply_overrides,
    build_default_config,
    dump_config_text,
    load_config_file,
    parse_args_with_config,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_default_yaml_matches_schema_defaults() -> None:
    default_yaml = REPO_ROOT / "src" / "akkapros" / "config" / "default.yaml"
    text = default_yaml.read_text(encoding="utf-8")
    loaded = load_config_file(default_yaml)
    assert loaded == build_default_config()
    assert "metrics_prefix" not in loaded["common"]
    assert "print_prefix" not in loaded["common"]
    assert "fullprosmaker:" not in text
    assert "fullprosmaker reads common plus the syllabify, prosody, metrics, and" in text
    assert text.count('extra_vowels: ""') == 1
    assert text.count('extra_consonants: ""') == 1
    assert "long_punct_weight" not in text
    assert "long_punct_weight" not in loaded["metrics"]


def test_parse_args_with_config_applies_config_and_cli_override(tmp_path: Path) -> None:
    config = apply_overrides(
        build_default_config(),
        {
            ("common", "prefix"): "from-config",
            ("common", "outdir"): str(tmp_path / "configured"),
            ("metrics", "json"): True,
            ("prosody", "style"): "sob",
        },
    )
    config_path = tmp_path / "run.yaml"
    config_path.write_text(dump_config_text(config), encoding="utf-8")

    parser = argparse.ArgumentParser()
    add_config_argument(parser)
    parser.add_argument("input", nargs="?")
    parser.add_argument("-p", "--prefix")
    parser.add_argument("--outdir", default=".")
    parser.add_argument("--metrics-json", action="store_true")
    parser.add_argument("--prosody-style", dest="prosody_style", choices=["lob", "sob"], default="lob")

    args = parse_args_with_config(
        parser,
        "fullprosmaker",
        ["--conf", str(config_path), "--prefix", "from-cli", "input_proc.txt"],
    )

    assert args.prefix == "from-cli"
    assert args.outdir == str(tmp_path / "configured")
    assert args.metrics_json is True
    assert args.prosody_style == "sob"


def test_confwriter_incrementally_updates_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    cmd_prefix = [sys.executable, "-m", "akkapros.cli.confwriter", "--conf", str(config_path)]

    first = subprocess.run(
        cmd_prefix + ["--prefix", "one"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert first.returncode == 0, first.stderr

    second = subprocess.run(
        cmd_prefix + ["--outdir", str(tmp_path / "out"), "--atfparse-preserve-case"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert second.returncode == 0, second.stderr

    loaded = load_config_file(config_path)
    text = config_path.read_text(encoding="utf-8")
    assert loaded["common"]["prefix"] == "one"
    assert loaded["common"]["outdir"] == str(tmp_path / "out")
    assert loaded["atfparse"]["preserve_case"] is True
    assert "# Shared output prefix used by file-producing CLIs." in text
    assert "fullprosmaker:" not in text


def test_confwriter_rejects_null_effective_prefix(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    config_path.write_text("common:\n  prefix: null\n", encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.confwriter", "--conf", str(config_path), "--outdir", str(tmp_path / "out")],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 2
    assert "null common.prefix" in (proc.stderr + proc.stdout)


def test_removed_metrics_long_punct_weight_key_is_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    config_path.write_text(
        "metrics:\n  long_punct_weight: 2.0\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        load_config_file(config_path)

    assert "Unknown keys in section 'metrics': long_punct_weight" in str(excinfo.value)


def test_removed_long_punct_weight_cli_flags_absent() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    metricalc_help = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.metricalc", "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert metricalc_help.returncode == 0, metricalc_help.stderr
    assert "--long-punct-weight" not in (metricalc_help.stdout + metricalc_help.stderr)

    fullprosmaker_help = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.fullprosmaker", "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert fullprosmaker_help.returncode == 0, fullprosmaker_help.stderr
    assert "--metrics-long-punct-weight" not in (fullprosmaker_help.stdout + fullprosmaker_help.stderr)
