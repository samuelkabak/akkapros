import os
import subprocess
import sys
from pathlib import Path

from akkapros.lib.frontmatter import split_frontmatter
from akkapros.lib.prosody import AccentStyle, MoraMode, ProsodyEngine, parse_syl_line


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*module_and_args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, "-m", *module_and_args],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, (
        f"CLI failed: {' '.join(module_and_args)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    return proc


def _read_frontmatter(path: Path):
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter is not None
    return frontmatter, body


def test_bi_mode_preserves_even_word_without_accentuation() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.BI)
    result = engine.accentuation_line(parse_syl_line("ip-pa-lis-ma¦"))
    assert result == "ip-pa-lis-ma"


def test_mono_mode_accentuates_even_word_with_legal_candidate() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.MONO)
    result = engine.accentuation_line(parse_syl_line("ip-pa-lis-ma¦"))
    assert result == "ip-pa-lis~-ma"


def test_mono_mode_skips_forward_merge_and_uses_last_resort() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.MONO)
    result = engine.accentuation_line(parse_syl_line("ba·na¦šar·ri¦"))
    assert result == "ba·n~a šar~·ri"


def test_mono_mode_keeps_explicit_pre_tail_word_locked_before_last_resort() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.MONO)
    result = engine.accentuation_line(parse_syl_line("bā·nû+˙a·na·ku¦šar·ri¦"))
    assert result == "bā·nû+˙~a·na·ku šar~·ri"


def test_mono_mode_explicit_group_uses_internal_accentuation_before_last_resort() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.MONO)
    result = engine.accentuation_line(parse_syl_line("e·li+ap·sî¦"))
    assert result == "e·li+ap·sî~"


def test_mono_mode_function_word_group_accentuates_content_host() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.MONO)
    result = engine.accentuation_line(parse_syl_line("e·li¦ap·sî¦"))
    assert result == "e·li+ap·sî~"


def test_mono_mode_function_word_group_falls_to_last_resort_on_content_host() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.MONO)
    result = engine.accentuation_line(parse_syl_line("˙a·na¦˙e·¨a¦"))
    assert result == "˙a·na+˙~e·¨a"


def test_bi_mode_function_word_group_accentuates_odd_unit_content_host() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.BI)
    result = engine.accentuation_line(parse_syl_line("˙a·na¦˙i·lī¦"))
    assert result == "˙a·na+˙i·lī~"


def test_bi_mode_function_word_group_preserves_even_unit_without_accentuation() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.BI)
    result = engine.accentuation_line(parse_syl_line("e·li¦ap·sî¦"))
    assert result == "e·li+ap·sî"


def test_function_words_before_punctuation_attach_backward_to_previous_host() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.BI)
    result = engine.accentuation_line(
        parse_syl_line("tab·nâ¦ša¦at·tu·nu¦⟦ ,⟧i·dā·ša¦al·kū¦")
    )
    assert result == "tab·nâ+ša+at·tu·nu⟦ ,⟧i·dā·ša al·kū"


def test_punctuation_armor_is_preserved_in_tilde_output() -> None:
    engine = ProsodyEngine(style=AccentStyle.LOB, mora_mode=MoraMode.BI)
    result = engine.accentuation_line(parse_syl_line("šar¦⟦ : ⟧ti·¨ām·tu¦"))

    assert result == "šar⟦ : ⟧ti·¨ā~m·tu"


def test_prosmaker_frontmatter_records_mora_mode(tmp_path: Path) -> None:
    syl_file = tmp_path / "sample_syl.txt"
    syl_file.write_text("ip-pa-lis-ma¦\n", encoding="utf-8")

    _run_cli(
        "akkapros.cli.prosmaker",
        str(syl_file),
        "-p",
        "sample",
        "--outdir",
        str(tmp_path),
        "--mora-mode",
        "mono",
    )

    tilde_frontmatter, _ = _read_frontmatter(tmp_path / "sample_tilde.txt")
    assert tilde_frontmatter["metadata"]["options"]["mora_mode"] == "mono"


def test_fullprosmaker_propagates_mora_mode_to_downstream_frontmatter(tmp_path: Path) -> None:
    proc_file = tmp_path / "sample_proc.txt"
    proc_file.write_text("ip palis ma\n", encoding="utf-8")

    _run_cli(
        "akkapros.cli.fullprosmaker",
        str(proc_file),
        "-p",
        "sample",
        "--outdir",
        str(tmp_path),
        "--mora-mode",
        "mono",
        "--metrics-table",
    )

    tilde_frontmatter, _ = _read_frontmatter(tmp_path / "sample_tilde.txt")
    metrics_frontmatter, _ = _read_frontmatter(tmp_path / "sample_metrics.txt")

    assert tilde_frontmatter["metadata"]["options"]["mora_mode"] == "mono"
    assert metrics_frontmatter["metadata"]["options"]["mora_mode"] == "mono"