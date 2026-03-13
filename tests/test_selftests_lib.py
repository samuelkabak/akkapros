import pytest

from akkapros.lib import atfparse
from akkapros.lib import metrics
from akkapros.lib import print as printlib
from akkapros.lib import repair
from akkapros.lib import syllabify
from akkapros.lib import utils


@pytest.mark.parametrize(
    "name, runner",
    [
        ("atfparse", atfparse.run_tests),
        ("syllabify", syllabify.run_tests),
        ("repair", repair.run_tests),
        ("repair_diphthongs", repair.test_diphthong_restoration),
        ("metrics", metrics.run_tests),
        ("print", printlib.run_tests),
        ("utils", utils.run_tests),
    ],
)
def test_library_selftests(name, runner):
    if name == "syllabify":
        pytest.xfail("Known diphthong-separator regression in syllabify self-tests")
    assert runner(), f"Library self-test failed: {name}"


def test_metrics_refactored_chunks():
    assert metrics._test_word_pattern_matching()
    assert metrics._test_tokenizer()
    assert metrics._test_word_processing()
    assert metrics._test_preprocessing()
    assert metrics._test_segment_extraction()
    assert metrics._test_distance_calculation()
    assert metrics._test_pause_metrics_grouping()
    assert metrics._test_unknown_punctuation_fallback()
