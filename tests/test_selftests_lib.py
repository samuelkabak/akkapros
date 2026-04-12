import ast
from pathlib import Path

import pytest

from akkapros.lib import atfparse
from akkapros.lib import metrics
from akkapros.lib import phonetize
from akkapros.lib import print as printlib
from akkapros.lib import prosody
from akkapros.lib import syllabify
from akkapros.lib import utils


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name, runner",
    [
        ("atfparse", atfparse.run_tests),
        ("syllabify", syllabify.run_tests),
        ("prosody", prosody.run_tests),
        ("prosody_diphthongs", prosody.test_diphthong_restoration),
        ("metrics", metrics.run_tests),
        ("phonetize", phonetize.run_tests),
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
    assert metrics._test_armored_pause_token_classification()
    assert metrics._test_mora_totals_and_original_speech()
    assert metrics._test_table_new_fields_and_no_csv()
    assert metrics._test_small_corpus_metrics_consistency()
    assert metrics._test_small_corpus_exact_surface_values()
    assert metrics._test_interval_metrics_zero_case()
    assert metrics._test_percent_v_fallback_safe()


def test_source_tree_has_no_print_calls():
    for path in (REPO_ROOT / 'src').rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                pytest.fail(f"print() call found in source tree: {path}:{node.lineno}")

