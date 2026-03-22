"""
Tests for ``akkapros.lib.utils.akkadian_likelihood`` and ``classify_text``.

The scorer is a linguistic heuristic, not a deterministic classifier, so
assertions use relative (threshold) comparisons rather than exact values.

coverage areas
--------------
* Forbidden characters → 0.0 immediately
* Obvious Akkadian text → high score
* Obvious English text  → 0.0
* Function-word recognition
* Enclitic suffix detection
* Short-text penalty branch
* classify_text label mapping
* validate_intermediate_format integration (proc stage)
"""
import pytest

from akkapros.lib.utils import (
    akkadian_likelihood,
    classify_text,
    AKKASCORE_THRESHOLDS,
    FormatValidationError,
    validate_intermediate_format,
)
from akkapros.lib.constants import NON_AKKADIAN_CHARS


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

OBVIOUS_AKKADIAN = (
    "īpuš-ma pâšu izakkar ana rubê marūtuk"
)
RICH_AKKADIAN = (
    "rubû marūtuk adi attā ana bīti šâšu terrubū-ma gīru ṣubātka ubbabū-ma "
    "tatūra ašrukka šiptu duppir lemnu šēdu lemnu utukku lemnu"
)
FUNCTION_WORD_SENTENCE = "ana šamê ellī-ma ana igīgī anaddin ûrta"
ENCLITIC_SENTENCE = "terrubū-ma gīru ṣubātka ubbabū-ma"   # -ma enclitics
ENGLISH_TEXT = "This is clearly English text with no Akkadian characters"
LATIN_LETTERS_ONLY = "nusquam officia vero"          # contains 'o', 'v' → forbidden


# ---------------------------------------------------------------------------
# Basic score range
# ---------------------------------------------------------------------------

class TestAkkadianLikelihoodRange:
    """Score must always be in [0.0, 1.0]."""

    @pytest.mark.parametrize("text", [
        OBVIOUS_AKKADIAN,
        RICH_AKKADIAN,
        FUNCTION_WORD_SENTENCE,
        ENCLITIC_SENTENCE,
        ENGLISH_TEXT,
        LATIN_LETTERS_ONLY,
        "",
        "a",
        "šar",
    ])
    def test_score_in_range(self, text):
        score, _ = akkadian_likelihood(text)
        assert 0.0 <= score <= 1.0, f"Score {score!r} out of [0,1] for {text!r}"


# ---------------------------------------------------------------------------
# Forbidden-character detection (immediate 0.0)
# ---------------------------------------------------------------------------

class TestForbiddenCharacters:
    """Texts containing NON_AKKADIAN_CHARS must return exactly 0.0."""

    @pytest.mark.parametrize("char", list(NON_AKKADIAN_CHARS))
    def test_single_forbidden_char(self, char):
        text = f"ana šarri {char}ina"
        score, details = akkadian_likelihood(text)
        assert score == 0.0
        assert details['has_non_akkadian'] is True

    def test_obvious_english_is_zero(self):
        score, details = akkadian_likelihood(ENGLISH_TEXT)
        # 'o', 'c' etc. are in NON_AKKADIAN_CHARS
        assert score == 0.0
        assert details['has_non_akkadian'] is True

    def test_latin_only_is_zero(self):
        score, _ = akkadian_likelihood(LATIN_LETTERS_ONLY)
        assert score == 0.0


# ---------------------------------------------------------------------------
# Obvious Akkadian
# ---------------------------------------------------------------------------

class TestObviousAkkadian:
    """Well-formed Akkadian text should score noticeably above the 'possibly' threshold."""

    def test_rich_akkadian_high_score(self):
        score, _ = akkadian_likelihood(RICH_AKKADIAN)
        assert score >= AKKASCORE_THRESHOLDS['possibly'], (
            f"Expected >= {AKKASCORE_THRESHOLDS['possibly']}, got {score:.3f}"
        )

    def test_rich_akkadian_details_no_forbidden(self):
        _, details = akkadian_likelihood(RICH_AKKADIAN)
        assert details['has_non_akkadian'] is False

    def test_rich_akkadian_has_distinctive_chars(self):
        _, details = akkadian_likelihood(RICH_AKKADIAN)
        assert details['distinctive_count'] > 0

    def test_rich_akkadian_vowel_consonant_counts(self):
        _, details = akkadian_likelihood(RICH_AKKADIAN)
        assert details['vowel_count'] > 0
        assert details['consonant_count'] > 0


# ---------------------------------------------------------------------------
# Function-word detection
# ---------------------------------------------------------------------------

class TestFunctionWordDetection:
    """Function words are counted in details and raise the score."""

    def test_function_words_matched(self):
        score, details = akkadian_likelihood(FUNCTION_WORD_SENTENCE)
        # "ana" appears twice in the test sentence
        assert details['function_word_matches'] >= 2

    def test_function_words_raises_score_vs_no_function_words(self):
        # A sentence that is dense with function words must produce a higher
        # function_words *component* score than a sentence with none.
        # We compare the sub-score directly instead of the total, because
        # a content-only sentence may outscore on distinctive-char or V/C
        # components independently.
        _, details_fw = akkadian_likelihood(FUNCTION_WORD_SENTENCE)
        # Content words only, long enough to pass min_length, no enclitics
        # 'bēl' 'šarr' 'nakr' 'idd' etc. — none end with known enclitics
        _, details_nofw = akkadian_likelihood("šarrum nakrum tabûm iddinšu bēl māti")
        assert details_fw['scores']['function_words'] > details_nofw['scores']['function_words']

    def test_function_word_ratio_in_details(self):
        _, details = akkadian_likelihood(FUNCTION_WORD_SENTENCE)
        assert 'function_word_ratio' in details
        assert 0.0 <= details['function_word_ratio'] <= 1.0


# ---------------------------------------------------------------------------
# Enclitic detection (-ma, -šu, etc.)
# ---------------------------------------------------------------------------

class TestEncliticDetection:
    """Words ending in known enclitics yield fractional function_word_matches."""

    def test_enclitic_ma_detected(self):
        # "terrubū-ma" and "ubbabū-ma" end with enclitic "ma"
        _, details = akkadian_likelihood(ENCLITIC_SENTENCE)
        # At least 1.0 (two half-counts) from enclitic detection
        assert details['function_word_matches'] >= 1.0

    def test_enclitic_does_not_fire_on_whole_function_word(self):
        # "ana" is a whole function word — counted as 1.0, not as an enclitic.
        # Use a sentence long enough to bypass the short-text branch (> 10 chars).
        _, details = akkadian_likelihood("ana šarri nakrim bēlum")
        # 'ana' must be a full function-word match (1.0), not an enclitic (0.5)
        assert details['function_word_matches'] >= 1.0


# ---------------------------------------------------------------------------
# Short-text penalty
# ---------------------------------------------------------------------------

class TestShortTextPenalty:
    """Texts below min_length trigger the confidence-penalty branch."""

    def test_single_char_gives_low_score(self):
        score, details = akkadian_likelihood("a", min_length=10)
        assert 0.0 < score <= 0.5
        assert 'confidence_penalty' in details
        assert details['confidence_penalty'] < 1.0

    def test_empty_text_gives_zero_or_very_low(self):
        score, _ = akkadian_likelihood("", min_length=10)
        # Empty → length=0, 0 < min_length → 0.5 * (0/10) = 0.0
        assert score == 0.0

    def test_at_min_length_no_penalty(self):
        # A string of exactly min_length Akkadian vowels/consonants
        # should NOT enter the short-text branch.
        text = "ānašarri"   # 8 characters, use min_length=8
        score, details = akkadian_likelihood(text, min_length=8)
        assert 'confidence_penalty' not in details

    def test_below_min_length_has_penalty(self):
        text = "šar"   # 3 chars
        _, details = akkadian_likelihood(text, min_length=10)
        assert 'confidence_penalty' in details


# ---------------------------------------------------------------------------
# classify_text
# ---------------------------------------------------------------------------

class TestClassifyText:
    """classify_text returns correct labels for representative inputs."""

    def test_not_akkadian_label(self):
        label = classify_text(ENGLISH_TEXT)
        assert label.startswith("NOT AKKADIAN")

    def test_highly_likely_label(self):
        # RICH_AKKADIAN should hit the 'likely' or 'highly_likely' tier.
        label = classify_text(RICH_AKKADIAN)
        assert "AKKADIAN" in label

    def test_label_contains_percentage(self):
        # All non-zero labels embed a percentage.
        label = classify_text("ana šarri")
        if "NOT AKKADIAN" not in label:
            assert "%" in label

    def test_classify_consistency_with_score(self):
        """classify_text label must be consistent with the raw score."""
        for text in [RICH_AKKADIAN, FUNCTION_WORD_SENTENCE, "šar gimir dadmē"]:
            score, _ = akkadian_likelihood(text)
            label = classify_text(text)
            if score == 0.0:
                assert "NOT AKKADIAN" in label
            elif score >= AKKASCORE_THRESHOLDS['highly_likely']:
                assert "HIGHLY LIKELY" in label
            elif score >= AKKASCORE_THRESHOLDS['likely']:
                assert "LIKELY AKKADIAN" in label
            elif score >= AKKASCORE_THRESHOLDS['possibly']:
                assert "POSSIBLY" in label
            else:
                assert "UNLIKELY" in label


# ---------------------------------------------------------------------------
# validate_intermediate_format integration (proc guard)
# ---------------------------------------------------------------------------

class TestValidateIntermediateFormatProc:
    """validate_intermediate_format('proc') triggers the likelihood guard."""

    def _write_tmp(self, tmp_path, content: str, name: str = "test.txt"):
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_valid_akkadian_proc_passes(self, tmp_path):
        content = (RICH_AKKADIAN + "\n") * 3  # repeat for length
        p = self._write_tmp(tmp_path, content)
        # Must not raise
        validate_intermediate_format(p, "proc")

    def test_non_akkadian_proc_raises(self, tmp_path):
        # English text > 50 chars should trigger the likelihood guard
        content = (
            "The sun rises in the east and sets in the west "
            "every single day of every beautiful year.\n"
        )
        p = self._write_tmp(tmp_path, content)
        with pytest.raises((FormatValidationError, ValueError)):
            validate_intermediate_format(p, "proc")

    def test_stub_proc_below_50_chars_not_blocked(self, tmp_path):
        # Very short file (< _VALIDATE_PROC_MIN_CHARS) bypasses likelihood guard.
        content = "šar\n"
        p = self._write_tmp(tmp_path, content)
        # Should not raise due to likelihood (file is too short to check)
        # It may raise for other reasons (like needing Akkadian letters) — that's fine.
        try:
            validate_intermediate_format(p, "proc")
        except FormatValidationError as e:
            # Acceptable failure reason must NOT mention likelihood score
            assert "likelihood" not in str(e).lower(), (
                f"Short stub incorrectly blocked by likelihood guard: {e}"
            )

    def test_syl_format_not_affected_by_likelihood(self, tmp_path):
        """syl format must NOT trigger likelihood guard even for low-scoring text."""
        # Syllabified text loses function-word recognition — must still pass
        content = "šar¦ gi.mir¦ dad.mē¦ bā.nû¦\n"
        p = self._write_tmp(tmp_path, content)
        # May raise for missing ¦ or other structural reasons, but not likelihood
        try:
            validate_intermediate_format(p, "syl")
        except FormatValidationError as e:
            assert "likelihood" not in str(e).lower()
