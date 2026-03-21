import pytest

from akkapros.lib import atfparse
from akkapros.lib import metrics
from akkapros.lib import print as printlib
from akkapros.lib import prosody
from akkapros.lib import syllabify
from akkapros.lib import utils


@pytest.mark.parametrize(
    "name, runner",
    [
        ("atfparse", atfparse.run_tests),
        ("syllabify", syllabify.run_tests),
        ("prosody", prosody.run_tests),
        ("prosody_diphthongs", prosody.test_diphthong_restoration),
        ("metrics", metrics.run_tests),
        ("print", printlib.run_tests),
        ("utils", utils.run_tests),
    ],
)
def test_library_selftests(name, runner):
    assert runner(), f"Library self-test failed: {name}"


def test_metrics_refactored_chunks():
    assert metrics._test_word_pattern_matching()
    assert metrics._test_tokenizer()
    assert metrics._test_word_processing()
    assert metrics._test_preprocessing()
    assert metrics._test_segment_extraction()
    assert metrics._test_distance_calculation()
    assert metrics._test_consonant_distance_definitions()
    assert metrics._test_punctuation_marks_segment_boundaries()
    assert metrics._test_pause_metrics_grouping()
    assert metrics._test_unknown_punctuation_raises()
    assert metrics._test_mora_totals_and_original_speech()
    assert metrics._test_table_and_csv_new_fields()

