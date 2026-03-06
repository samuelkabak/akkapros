from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from akkarpos.cli import mbrolatortext as gen  # noqa: E402


@pytest.fixture(autouse=True)
def restore_inventory() -> None:
    """Keep module-level mutable inventory isolated between tests."""
    snapshot = {
        "plain_consonants": list(gen.PLAIN_CONSONANTS),
        "emphatic_consonants": list(gen.EMPHATIC_CONSONANTS),
        "plain_vowels_short": list(gen.PLAIN_VOWELS_SHORT),
        "plain_vowels_long": list(gen.PLAIN_VOWELS_LONG),
        "colored_vowels_short": list(gen.COLORED_VOWELS_SHORT),
        "colored_vowels_long": list(gen.COLORED_VOWELS_LONG),
    }
    yield
    gen.set_active_inventory(
        plain_consonants=snapshot["plain_consonants"],
        emphatic_consonants=snapshot["emphatic_consonants"],
        plain_vowels_short=snapshot["plain_vowels_short"],
        plain_vowels_long=snapshot["plain_vowels_long"],
        colored_vowels_short=snapshot["colored_vowels_short"],
        colored_vowels_long=snapshot["colored_vowels_long"],
    )


def activate_small_set() -> None:
    """Use the historical reduced inventory used in earlier debugging runs."""
    gen.set_active_inventory(
        plain_consonants=["m"],
        emphatic_consonants=["q"],
        plain_vowels_short=["a"],
        plain_vowels_long=["ā"],
        colored_vowels_short=["ɑ"],
        colored_vowels_long=["ɑ̄"],
    )


def test_small_set_inventory_normalization() -> None:
    activate_small_set()

    assert gen.PLAIN_CONSONANTS == ["m"]
    assert gen.EMPHATIC_CONSONANTS == ["q"]
    assert gen.ALL_CONSONANTS == ["m", "q"]

    # Long vowels are folded into short inventory in this generator.
    assert gen.PLAIN_VOWELS_SHORT == ["a"]
    assert gen.PLAIN_VOWELS_LONG == []
    assert gen.COLORED_VOWELS_SHORT == ["ɑ"]
    assert gen.COLORED_VOWELS_LONG == []


def test_format_word_adds_dotted_syllable_boundaries() -> None:
    activate_small_set()

    p1 = ["a", "m", "q", "ɑ", "m", "q", "ɑ"]
    p2 = ["m", "a", "q", "ɑ", "m", "q", "ɑ", "q"]
    p3 = ["m", "a", "a", "q", "ɑ", "ɑ", "q"]

    assert gen.format_word(p1, 1) == "_am.qɑm.qɑ_"
    assert gen.format_word(p2, 2) == "_ma.qɑm.qɑq_"
    assert gen.format_word(p3, 3) == "_maa.qɑɑq_"


def test_small_set_ipa_to_mbrola_mapping_contains_expected_pairs() -> None:
    activate_small_set()
    pairs = gen.ipa_to_mbrola_mapping_list()

    assert ("m", "m") in pairs
    assert ("q", "q") in pairs
    assert ("a", "a") in pairs
    assert ("ɑ", "a.") in pairs


def test_generate_script_completes_on_small_set() -> None:
    activate_small_set()
    random.seed(42)

    words, stats = gen.generate_script(
        target_coverage=1,
        max_iterations=5000,
        candidate_pool_size=16,
    )

    assert words
    assert stats["total"] > 0
    assert stats["ratio"] == pytest.approx(1.0)
    # Small inventory should stay compact.
    assert len(words) <= 40
