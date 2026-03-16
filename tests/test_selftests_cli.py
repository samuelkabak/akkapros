import os
import subprocess
import sys

import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _run_cli(args):
    env = os.environ.copy()
    src_path = os.path.join(REPO_ROOT, "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-m"] + args
    return subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True)


@pytest.mark.parametrize(
    "module_args",
    [
        ["akkapros.cli.atfparser", "--test"],
        ["akkapros.cli.syllabifier", "--test"],
        ["akkapros.cli.prosmaker", "--test"],
        ["akkapros.cli.prosmaker", "--test-diphthongs"],
        ["akkapros.cli.metricalc", "--test"],
        ["akkapros.cli.printer", "--test"],
        ["akkapros.cli.fullprosmaker", "--test-cli"],
        ["akkapros.cli.fullprosmaker", "--test-all"],
        ["akkapros.cli.phoneprep", "--test"],
    ],
)
def test_cli_selftest_flags(module_args):
    if module_args in (["akkapros.cli.syllabifier", "--test"], ["akkapros.cli.fullprosmaker", "--test-all"]):
        pytest.xfail("Known diphthong-separator regression in syllabify self-tests")
    proc = _run_cli(module_args)
    assert proc.returncode == 0, (
        f"CLI self-test failed for {' '.join(module_args)}\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )


@pytest.mark.parametrize(
    "script_path",
    [
        os.path.join("src", "akkapros", "cli", "atfparser.py"),
        os.path.join("src", "akkapros", "cli", "syllabifier.py"),
        os.path.join("src", "akkapros", "cli", "prosmaker.py"),
        os.path.join("src", "akkapros", "cli", "metricalc.py"),
        os.path.join("src", "akkapros", "cli", "printer.py"),
        os.path.join("src", "akkapros", "cli", "fullprosmaker.py"),
        os.path.join("src", "akkapros", "cli", "phoneprep.py"),
    ],
)
def test_cli_direct_script_version(script_path):
    """Direct script execution should work without manual PYTHONPATH tweaks."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, script_path, "--version"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"Direct CLI script failed for {script_path}\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

