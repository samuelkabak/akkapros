import os
import sys

import pytest


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from akkapros.lib.utils import FormatValidationError, validate_intermediate_format


def test_validate_syl_ok(tmp_path):
    p = tmp_path / "ok_syl.txt"
    p.write_text("gi.mir\nšar¦\n", encoding="utf-8")
    validate_intermediate_format(p, expected_kind="syl")


def test_validate_tilde_ok(tmp_path):
    p = tmp_path / "ok_tilde.txt"
    p.write_text("gi.mir_dad~.me\n", encoding="utf-8")
    validate_intermediate_format(p, expected_kind="tilde")


def test_validate_empty_fails(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="utf-8")
    with pytest.raises(FormatValidationError, match="empty"):
        validate_intermediate_format(p, expected_kind="syl")


def test_validate_syl_missing_markers_fails(tmp_path):
    p = tmp_path / "bad_syl.txt"
    p.write_text("akkadiantext\n", encoding="utf-8")
    with pytest.raises(FormatValidationError, match="SYL_WORD_ENDING"):
        validate_intermediate_format(p, expected_kind="syl")


def test_validate_tilde_plain_text_ok(tmp_path):
    p = tmp_path / "plain_tilde.txt"
    p.write_text("ku man su tal\n", encoding="utf-8")
    validate_intermediate_format(p, expected_kind="tilde")


def test_validate_tilde_rejects_syl_word_endings(tmp_path):
    p = tmp_path / "not_tilde.txt"
    p.write_text("gi.mir¦\n", encoding="utf-8")
    with pytest.raises(FormatValidationError, match=r"syllabified .*_syl\.txt"):
        validate_intermediate_format(p, expected_kind="tilde")


def test_validate_missing_final_newline_is_accepted(tmp_path):
    p = tmp_path / "no_final_newline.atf"
    p.write_text("1. %n ku man su tal", encoding="utf-8")
    validate_intermediate_format(p, expected_kind="atf")


def test_validate_atf_ok(tmp_path):
    p = tmp_path / "ok.atf"
    p.write_text("1. %n šar gi-mir\n#tr.en: king\n", encoding="utf-8")
    validate_intermediate_format(p, expected_kind="atf")


def test_validate_atf_missing_percent_n_fails(tmp_path):
    p = tmp_path / "bad.atf"
    p.write_text("#tr.en: only translation\n", encoding="utf-8")
    with pytest.raises(FormatValidationError, match="missing %n"):
        validate_intermediate_format(p, expected_kind="atf")


def test_validate_proc_rejects_raw_atf_markers(tmp_path):
    p = tmp_path / "bad_proc.txt"
    p.write_text("1. %n šar\n", encoding="utf-8")
    with pytest.raises(FormatValidationError, match=r"expected cleaned \*_proc.txt"):
        validate_intermediate_format(p, expected_kind="proc")
