import json
import math
from pathlib import Path

from akkapros.lib import metrics
from akkapros.lib import print as printlib
from akkapros.lib.constants import DIPH_SEPARATOR, SYL_SEPARATOR
from akkapros.lib.prosody import AccentStyle, ProsodyEngine, parse_syl_line, postprocess_restore_diphthongs
from akkapros.lib.syllabify import syllabify_text


SAMPLE_PROC_TEXT = """appūnā-ma ištēn-ešret : kīma šuāti uštabši
ina ilī bukrīša : šūt iškunūši puḫra
ušašqi qingu : ina birīšunu šâšu ušrabbīš
ālikūt maḫri pān ummāni muʾerrūt puḫri
"""


def _build_sample_tilde() -> str:
    syllabified = syllabify_text(SAMPLE_PROC_TEXT, preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    accentuated_lines = []
    for line in syllabified.splitlines():
        if not line.strip():
            accentuated_lines.append("")
            continue
        accentuated_lines.append(engine.accentuation_line(parse_syl_line(line)))
    return "\n".join(postprocess_restore_diphthongs(accentuated_lines)) + "\n"


def test_small_corpus_metrics_formula_consistency() -> None:
    result = metrics.process_filetext(_build_sample_tilde(), wpm=165, pause_ratio=35.0)

    for section_name in ("original", "accentuated"):
        stats = result[section_name]["stats"]
        speech = result[section_name]["speech"]
        total_syllables = stats["total_syllables"]
        total_words = stats["word_stats"]["total_words"]
        total_morae = stats["mora_stats"]["total"]

        assert sum(stats["syllable_counts"].values()) == total_syllables
        assert stats["word_stats"]["syllables_per_word"]["mean"] == total_syllables / total_words
        assert stats["word_stats"]["morae_per_word"]["mean"] == total_morae / total_words
        assert speech["sps_speech"] == (speech["wpm"] / 60.0) * stats["word_stats"]["syllables_per_word"]["mean"]

    pause_metrics = result["accentuated"]["pause_metrics"]
    accentuated_total_syllables = result["accentuated"]["stats"]["total_syllables"]
    assert pause_metrics["punctuation_per_syllable"] == pause_metrics["raw_counts"]["punctuation"] / accentuated_total_syllables
    assert pause_metrics["short_punctuation_per_syllable"] == pause_metrics["raw_counts"]["short_punctuation"] / accentuated_total_syllables
    assert pause_metrics["long_punctuation_per_syllable"] == pause_metrics["raw_counts"]["long_punctuation"] / accentuated_total_syllables

    accentuation_stats = result["accentuation_stats"]
    original_total_syllables = result["original"]["stats"]["total_syllables"]
    assert accentuation_stats["accentuation_rate"] == accentuation_stats["accentuated_syllables"] / original_total_syllables * 100.0


def test_small_corpus_metrics_outputs_surface_totals(tmp_path: Path) -> None:
    result = metrics.process_filetext(_build_sample_tilde(), wpm=165, pause_ratio=35.0)

    table = metrics.format_table(result)
    assert table.count("Syllable statistics:") == 2
    assert f"Total syllables: {result['original']['stats']['total_syllables']} syllables" in table
    assert f"Total syllables: {result['accentuated']['stats']['total_syllables']} syllables" in table

    csv_path = tmp_path / "sample_metrics.csv"
    metrics.format_csv([result], csv_path)
    csv_text = csv_path.read_text(encoding="utf-8")
    assert "original_syllable_statistics_count," in csv_text
    assert "accentuated_syllable_statistics_count," in csv_text

    json_text = json.dumps(result, ensure_ascii=False)
    assert '"syllable_statistics"' in json_text
    assert '"total_syllables"' in json_text

    original_other = result["original"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0)
    accentuated_other = result["accentuated"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0)
    assert original_other == 0
    assert accentuated_other == 0
    assert f"count_{metrics.UNCLASSIFIED_SYLLABLE_TYPE},0" in csv_text
    assert metrics.UNCLASSIFIED_SYLLABLE_TYPE not in table


def test_function_words_remain_syllabified_in_tilde_output() -> None:
    syllabified = syllabify_text("u ana ina šarri\n", preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    tilde = postprocess_restore_diphthongs([
        engine.accentuation_line(parse_syl_line(syllabified.strip()))
    ])[0]

    assert tilde == "u+a·na+i·na+šar·ri"


def test_diphthong_separator_propagates_to_tilde_metrics_and_print() -> None:
    tilde = postprocess_restore_diphthongs([
        f"ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu"
    ])[0]

    assert tilde == f"ti{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu"

    result = metrics.process_filetext(tilde + "\n", wpm=165, pause_ratio=35.0)
    assert result["original"]["stats"]["total_syllables"] == 3
    assert result["accentuated"]["stats"]["total_syllables"] == 3
    assert result["original"]["stats"]["syllable_counts"].get("VVC", 0) == 1
    assert result["accentuated"]["stats"]["syllable_counts"].get("VV:C", 0) == 1
    assert result["original"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0) == 0
    assert result["accentuated"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0) == 0
    assert printlib.convert_line(tilde, "acute") == "tiā´mtu"
    assert printlib.convert_line(tilde, "ipa") == "ti.ˈaːːm.tu"
    assert printlib.convert_line(tilde, "xar") == "tiaa´mtu"
    assert printlib.convert_line(tilde, "bold") == "ti**ām**tu"


def test_compute_percent_v_from_stats_fallback_is_safe() -> None:
    stats = {
        "syllable_counts": {
            "CV": 2,
            "VC:": 1,
            "VV:C": 1,
            metrics.UNCLASSIFIED_SYLLABLE_TYPE: 5,
        },
        "mora_stats": {},
    }

    expected_vowel_morae = 2 * 1 + 1 * 1 + 1 * 3
    expected_total_morae = 2 * 1 + 1 * 3 + 1 * 4
    expected = expected_vowel_morae / expected_total_morae * 100

    assert math.isclose(metrics.compute_percent_v_from_stats(stats), expected)