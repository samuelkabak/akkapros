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
        ("metrics", metrics._run_tests()),
        ("phonetize", phonetize.run_tests),
        ("print", printlib.run_tests),
        ("utils", utils.run_tests),
    ],
)
def test_library_selftests(name, runner):
    assert runner(), f"Library self-test failed: {name}"


def test_metrics_refactored_chunks():
    from akkapros.lib.tests.metrics_tests import (
        _test_word_pattern_matching,
        _test_tokenizer,
        _test_word_processing,
        _test_preprocessing,
        _test_segment_extraction,
        _test_distance_calculation,
        _test_consonant_distance_definitions,
        _test_punctuation_marks_segment_boundaries,
        _test_pause_metrics_grouping,
        _test_unknown_punctuation_raises,
        _test_armored_pause_token_classification,
        _test_mora_totals_and_original_speech,
        _test_table_new_fields_and_no_csv,
        _test_small_corpus_metrics_consistency,
        _test_small_corpus_exact_surface_values,
        _test_interval_metrics_zero_case,
        _test_percent_v_fallback_safe,
    )
    assert _test_word_pattern_matching()
    assert _test_tokenizer()
    assert _test_word_processing()
    assert _test_preprocessing()
    assert _test_segment_extraction()
    assert _test_distance_calculation()
    assert _test_consonant_distance_definitions()
    assert _test_punctuation_marks_segment_boundaries()
    assert _test_pause_metrics_grouping()
    assert _test_unknown_punctuation_raises()
    assert _test_armored_pause_token_classification()
    assert _test_mora_totals_and_original_speech()
    assert _test_table_new_fields_and_no_csv()
    assert _test_small_corpus_metrics_consistency()
    assert _test_small_corpus_exact_surface_values()
    assert _test_interval_metrics_zero_case()
    assert _test_percent_v_fallback_safe()


def test_source_tree_has_no_print_calls():
    for path in (REPO_ROOT / 'src').rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'print':
                pytest.fail(f"print() call found in source tree: {path}:{node.lineno}")

