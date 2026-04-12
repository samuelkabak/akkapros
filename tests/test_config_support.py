import os
import argparse
import subprocess
import sys
from pathlib import Path

import pytest

from akkapros.lib.config import (
    ConfigError,
    CONFIG_SCHEMA,
    METRICS_SECTION,
    add_config_argument,
    add_runtime_interface_arguments,
    apply_overrides,
    build_default_config,
    dump_config_text,
    get_config_value,
    load_config_file,
    parse_args_with_config,
)
from akkapros.lib.helpmsg import OPTION_HELP


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_default_yaml_matches_schema_defaults() -> None:
    default_yaml = REPO_ROOT / "src" / "akkapros" / "config" / "default.yaml"
    text = default_yaml.read_text(encoding="utf-8")
    loaded = load_config_file(default_yaml)
    assert loaded == build_default_config()
    assert "metrics_prefix" not in loaded["common"]["run"]
    assert "print_prefix" not in loaded["common"]["run"]
    assert "fullprosmaker:" not in text
    assert "fullprosmaker reads common plus the syllabify, prosody, phonetize," in text
    assert "common:\n  run:" in text
    assert text.count('extra_vowels: ""') == 1
    assert text.count('extra_consonants: ""') == 1
    assert "long_punct_weight" not in text
    assert "long_punct_weight" not in loaded["metrics"]["run"]
    assert "explicit_link_count" not in loaded["metrics"]["run"]
    assert "csv" not in loaded["metrics"]["run"]
    assert "csv:" not in text
    assert loaded["phonetize"]["process"]["timing_model"]["speech"]["wpm"] == 193
    assert loaded["phonetize"]["process"]["timing_model"]["drift_policy"] == "extensible"


def test_metrics_schema_and_help_no_longer_expose_csv() -> None:
    metrics_run_keys = CONFIG_SCHEMA[METRICS_SECTION]["run"].keys()

    assert set(metrics_run_keys) == {"table", "json"}
    assert "metrics.run.csv" not in OPTION_HELP
    assert "metricalc.csv" not in OPTION_HELP
    assert "fullprosmaker.metrics_csv" not in OPTION_HELP
    assert "metrics.csv" not in OPTION_HELP


def test_removed_metrics_csv_config_key_is_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    config_path.write_text(
        "metrics:\n  run:\n    csv: false\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError) as excinfo:
        load_config_file(config_path)

    assert "Unknown config keys: metrics.run.csv" in str(excinfo.value)


def test_parse_args_with_config_applies_config_and_cli_override(tmp_path: Path) -> None:
    config = apply_overrides(
        build_default_config(),
        {
            ("common", "run.prefix"): "from-config",
            ("common", "run.outdir"): str(tmp_path / "configured"),
            ("metrics", "run.json"): True,
            ("prosody", "process.style"): "sob",
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
        cmd_prefix + ["--set", "common.run.prefix=one"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert first.returncode == 0, first.stderr

    second = subprocess.run(
        cmd_prefix + [
            "--set",
            f"common.run.outdir={tmp_path / 'out'}",
            "--set",
            "atfparse.process.preserve_case=true",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert second.returncode == 0, second.stderr

    loaded = load_config_file(config_path)
    text = config_path.read_text(encoding="utf-8")
    assert loaded["common"]["run"]["prefix"] == "one"
    assert loaded["common"]["run"]["outdir"] == str(tmp_path / "out")
    assert loaded["atfparse"]["process"]["preserve_case"] is True
    assert "# Shared output prefix used by file-producing CLIs." in text
    assert "fullprosmaker:" not in text


def test_confwriter_get_list_unset_and_set_default(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    cmd_prefix = [sys.executable, "-m", "akkapros.cli.confwriter", "--conf", str(config_path)]

    seed = subprocess.run(
        cmd_prefix + ["--set", "common.run.prefix=demo", "--set", "prosody.process.style=sob"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert seed.returncode == 0, seed.stderr

    listed = subprocess.run(
        cmd_prefix + ["--list", "prosody"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert listed.returncode == 0, listed.stderr
    assert "prosody.process.style { TEXT }" in listed.stdout
    assert "Accent style for prosody realization." in listed.stdout

    got = subprocess.run(
        cmd_prefix + ["--get", "prosody.process.style"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip() == '"sob"'

    unset = subprocess.run(
        cmd_prefix + ["--unset", "prosody.process.style"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert unset.returncode == 0, unset.stderr
    text = config_path.read_text(encoding="utf-8")
    assert "style: null" in text
    assert get_config_value(load_config_file(config_path), "prosody.process.style") == "lob"

    unset_log = subprocess.run(
        cmd_prefix + ["--unset", "common.run.log"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert unset_log.returncode == 0, unset_log.stderr
    assert "log: null" in config_path.read_text(encoding="utf-8")

    reset = subprocess.run(
        cmd_prefix + ["--set-default", "prosody.process.style"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert reset.returncode == 0, reset.stderr
    reloaded = load_config_file(config_path)
    assert reloaded["prosody"]["process"]["style"] == "lob"
    assert "style: \"lob\"" in config_path.read_text(encoding="utf-8")


def test_confwriter_rejects_invalid_key_without_modifying_file(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    config_path.write_text(dump_config_text(build_default_config()), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    before = config_path.read_text(encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.confwriter", "--conf", str(config_path), "--set", "common.strict=true"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 2
    assert "Unknown config key: common.strict" in (proc.stderr + proc.stdout)
    assert config_path.read_text(encoding="utf-8") == before


def test_confwriter_help_uses_operation_surface() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    help_result = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.confwriter", "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert help_result.returncode == 0, help_result.stderr
    help_text = help_result.stdout + help_result.stderr
    assert "--set KEY=VALUE" in help_text
    assert "--get KEY" in help_text
    assert "--list [SUBSTRING]" in help_text or "--list [SUBSTRING]".replace("[", "").replace("]", "") in help_text
    assert "--unset KEY" in help_text
    assert "--set-default KEY" in help_text
    assert "--verify" in help_text
    assert "--prefix" not in help_text
    assert "--prosody-style" not in help_text


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
    assert "--metrics-wpm" not in (fullprosmaker_help.stdout + fullprosmaker_help.stderr)
    assert "--metrics-pause-ratio" not in (fullprosmaker_help.stdout + fullprosmaker_help.stderr)
    assert "--phonetize-geminate-policy" in (fullprosmaker_help.stdout + fullprosmaker_help.stderr)


def test_confwriter_supports_nested_phonetize_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "akkapros.cli.confwriter",
            "--conf",
            str(config_path),
            "--set",
            "common.run.prefix=demo",
            "--set",
            "phonetize.process.timing_model.geminate_policy=cumulative",
            "--set",
            "phonetize.process.timing_model.speech.wpm=201",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr

    loaded = load_config_file(config_path)
    assert loaded["phonetize"]["process"]["timing_model"]["geminate_policy"] == "cumulative"
    assert loaded["phonetize"]["process"]["timing_model"]["speech"]["wpm"] == 201


def test_confwriter_verify_reports_pass_without_mutating_file(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    config_path.write_text(dump_config_text(build_default_config()), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    before = config_path.read_text(encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.confwriter", "--conf", str(config_path), "--verify"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0, proc.stderr
    assert "VERIFY STATUS: pass" in proc.stdout
    assert config_path.read_text(encoding="utf-8") == before


def test_confwriter_verify_reports_warnings_without_mutating_file(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    config = apply_overrides(
        build_default_config(),
        {("phonetize", "process.timing_model.speech.pause_ratio"): 71},
    )
    config_path.write_text(dump_config_text(config), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    before = config_path.read_text(encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.confwriter", "--conf", str(config_path), "--verify"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0, proc.stderr
    assert "VERIFY STATUS: pass-with-warnings" in proc.stdout
    assert "WARN phonetize.process.timing_model.speech.pause_ratio" in proc.stdout
    assert config_path.read_text(encoding="utf-8") == before


def test_confwriter_verify_reports_failures_without_mutating_file(tmp_path: Path) -> None:
    config_path = tmp_path / "conf.yaml"
    config = apply_overrides(
        build_default_config(),
        {("phonetize", "process.timing_model.speech.pause_ratio"): 100},
    )
    config_path.write_text(dump_config_text(config), encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    before = config_path.read_text(encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.confwriter", "--conf", str(config_path), "--verify"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 1
    assert "VERIFY STATUS: failure" in proc.stdout
    assert "FAIL phonetize.process.timing_model.speech.pause_ratio" in proc.stdout
    assert config_path.read_text(encoding="utf-8") == before


def test_parse_args_with_config_materializes_defaults_without_conf_and_path_override_wins() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    add_config_argument(parser)
    add_runtime_interface_arguments(parser, "phonetizer")
    parser.add_argument("input", nargs="?")
    parser.add_argument("-p", "--prefix")
    parser.add_argument("--outdir", default=".")
    parser.add_argument("--drift-policy", dest="drift_policy", choices=["strict", "extensible"], default=None)
    parser.add_argument("--drift-tolerance", dest="drift_tolerance", type=int, default=None)

    args = parse_args_with_config(
        parser,
        "phonetizer",
        [
            "sample_tilde.txt",
            "--drift-policy",
            "strict",
            "--option",
            "phonetize.process.timing_model.drift_policy=extensible",
        ],
    )

    assert args.prefix == "akkapros"
    assert args.outdir == "."
    assert args.drift_policy == "extensible"
    assert args._effective_config["phonetize"]["process"]["timing_model"]["drift_policy"] == "extensible"
    assert args._effective_grouped_config["phonetize"]["process"]["timing_model"]["drift_policy"] == "extensible"


def test_phonetizer_help_is_program_scoped_and_subtree_scoped() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    default_help = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.phonetizer", "--help"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert default_help.returncode == 0, default_help.stderr
    default_text = default_help.stdout
    assert "Active Config Paths:" in default_text
    assert "common.run.prefix" in default_text
    assert "phonetize.process.timing_model.durations.cvc_reference" in default_text
    assert default_text.index("Active Config Paths:") < default_text.index("Deprecated Dedicated Flags:")

    subtree_help = subprocess.run(
        [sys.executable, "-m", "akkapros.cli.phonetizer", "--help", "phonetize.process.timing_model.durations"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert subtree_help.returncode == 0, subtree_help.stderr
    subtree_text = subtree_help.stdout
    assert "Config Help: phonetize.process.timing_model.durations" in subtree_text
    assert "phonetize.process.timing_model.durations.cvc_reference" in subtree_text
    assert "common.run.prefix" not in subtree_text
    assert "Deprecated Dedicated Flags:" not in subtree_text
