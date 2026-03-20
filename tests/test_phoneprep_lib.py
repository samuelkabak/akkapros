import os
import sys


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from akkapros.lib import phoneprep


def test_parse_symbol_list():
    assert phoneprep.parse_symbol_list("a, b c") == ["a", "b", "c"]


def test_vv_class_legality():
    assert phoneprep.is_vv_class_legal("a", "ē")
    assert not phoneprep.is_vv_class_legal("a", "ɑ")


def test_validate_pattern1_sample():
    sample = ["a", "m", "n", "a", "m", "n", "a"]
    assert phoneprep.validate_pattern1(sample)


def test_phoneprep_lib_selftest():
    assert phoneprep.run_tests()
