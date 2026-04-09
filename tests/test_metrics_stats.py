import json
import math
from pathlib import Path

from akkapros.lib import metrics
from akkapros.lib import print as printlib
from akkapros.lib.constants import DIPH_SEPARATOR, SYL_SEPARATOR
from akkapros.lib.prosody import AccentStyle, ProsodyEngine, parse_syl_line, postprocess_restore_diphthongs
from akkapros.lib.syllabify import syllabify_text
from akkapros.lib.utils import format_path_for_logging


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


def _sample_prominence_counts(function_word_count: int = 2, explicit_word_link_count: int = 1) -> dict[str, int]:
    return {
        "function_word_count": function_word_count,
        "explicit_word_link_count": explicit_word_link_count,
    }


def test_small_corpus_metrics_formula_consistency() -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
        wpm=165,
        pause_ratio=35.0,
        prominence_statistics=_sample_prominence_counts(),
    )

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
    result = metrics.process_filetext(
        _build_sample_tilde(),
        wpm=165,
        pause_ratio=35.0,
        prominence_statistics=_sample_prominence_counts(),
    )

    table = metrics.format_table(result)
    assert table.count("Syllable statistics:") == 2
    assert table.count("Word statistics:") == 2
    assert table.count("Prominence statistics:") == 1
    assert table.count("Mora statistics:") == 2
    assert table.find("Word statistics:") < table.find("Prominence statistics:") < table.find("Mora statistics:")
    assert "Std dev morae per syllable:" not in table
    assert "Total morae number:" not in table
    assert "Mean morae per word:" in table
    assert "Function words: 2 words" in table
    assert "Explicitly linked words: 1 words" in table
    assert "Prominence candidates: 19 words" in table
    assert f"ΔC: {result['original']['acoustic']['delta_c_seconds']:.4f} s" in table
    assert f"ΔC_mora: {result['original']['acoustic']['delta_c_mora']:.4f} mora" in table
    assert f"MeanC: {result['original']['acoustic']['mean_c_seconds']:.4f} s" in table
    assert f"MeanC_mora: {result['original']['acoustic']['mean_c_mora']:.4f} mora" in table
    assert f"VarcoC: {result['original']['acoustic']['varco_c']:.2f}" in table
    assert f"VarcoC: {result['original']['acoustic']['varco_c']:.2f} %" not in table
    assert f"Total syllables: {result['original']['stats']['total_syllables']} syllables" in table
    assert f"Total syllables: {result['accentuated']['stats']['total_syllables']} syllables" in table

    json_text = json.dumps(result, ensure_ascii=False)
    assert '"syllable_statistics"' in json_text
    assert '"word_statistics"' in json_text
    assert '"mora_statistics"' in json_text
    assert '"delta_c_seconds"' in json_text
    assert '"delta_c_mora"' in json_text
    assert '"mean_c_seconds"' in json_text
    assert '"mean_c_mora"' in json_text
    assert '"prominence_statistics"' in json_text
    assert '"prominence_candidate_word_count": 19' in json_text

    original_stats = result["original"]["stats"]
    assert original_stats["word_statistics"]["total_words"] == original_stats["word_stats"]["total_words"]
    assert original_stats["mora_statistics"]["total_morae"] == original_stats["mora_stats"]["total"]
    assert original_stats["mora_statistics"]["mean_morae_per_word"]["mean"] == original_stats["word_stats"]["morae_per_word"]["mean"]
    assert result["original"]["prominence_statistics"] == {
        "function_word_count": 2,
        "explicit_word_link_count": 1,
        "prominence_candidate_word_count": 19,
    }

    original_other = result["original"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0)
    accentuated_other = result["accentuated"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0)
    assert original_other == 0
    assert accentuated_other == 0
    assert metrics.UNCLASSIFIED_SYLLABLE_TYPE not in table
    assert not hasattr(metrics, "format_csv")


def test_process_filetext_shortens_artifact_file_path() -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
        wpm=165,
        pause_ratio=35.0,
        filesrc=r"C:\Users\samue\private\results\sample_tilde.txt",
        prominence_statistics=_sample_prominence_counts(),
    )

    assert result["file"] == r"...\results\sample_tilde.txt"


def test_process_file_uses_safe_path_display(tmp_path: Path) -> None:
    tilde_file = tmp_path / "alpha" / "beta" / "sample_tilde.txt"
    tilde_file.parent.mkdir(parents=True)
    tilde_file.write_text(
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Sample\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-29\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "    prosody:\n"
        "      explicit_word_link_count: 0\n"
        "---\n\n"
        "er~·ra\n",
        encoding="utf-8",
    )

    result = metrics.process_file(str(tilde_file), wpm=165, pause_ratio=35.0)

    assert result["file"] == format_path_for_logging(tilde_file)


def test_format_table_shortens_run_context_input_path() -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
        wpm=165,
        pause_ratio=35.0,
        filesrc=r"...\results\sample_tilde.txt",
        prominence_statistics=_sample_prominence_counts(),
    )

    table = metrics.format_table(
        result,
        run_context={
            "cli": "metricalc.py",
            "input": r"C:\Users\samue\private\results\sample_tilde.txt",
        },
    )

    assert "METRICS SUMMARY: ...\\results\\sample_tilde.txt" in table
    assert "  input: ...\\results\\sample_tilde.txt" in table
    assert r"C:\Users\samue\private\results\sample_tilde.txt" not in table


def test_function_words_remain_syllabified_in_tilde_output() -> None:
    syllabified = syllabify_text("u ana ina šarri\n", preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    tilde = postprocess_restore_diphthongs([
        engine.accentuation_line(parse_syl_line(syllabified.strip()))
    ])[0]

    assert tilde == "˙u&˙a·na&˙i·na&šar·ri"


def test_metrics_accepts_armored_punctuation_in_tilde_contract() -> None:
    tilde = "˙u·kap·pit-ma⟦ : ⟧ti·¨ā~m·tu pi·tiq·ša\n"

    result = metrics.process_filetext(
        tilde,
        wpm=165,
        pause_ratio=35.0,
        prominence_statistics={
            "function_word_count": 0,
            "explicit_word_link_count": 0,
        },
    )

    raw_counts = result["accentuated"]["pause_metrics"]["raw_counts"]
    assert raw_counts["long_punctuation"] == 1
    assert raw_counts["short_punctuation"] == 1


def test_metrics_rejects_unknown_armored_punctuation() -> None:
    stats = metrics.analyze_text("at·tā⟦ @ ⟧ā·lik", is_accentuated=True)

    try:
        metrics.compute_pause_metrics("at·tā⟦ @ ⟧ā·lik", stats)
        raise AssertionError("Expected armored unknown punctuation to fail")
    except metrics.PunctuationConfigError as exc:
        assert "⟦ @ ⟧" in str(exc)


def test_diphthong_separator_propagates_to_tilde_metrics_and_print() -> None:
    tilde = postprocess_restore_diphthongs([
        f"ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu"
    ])[0]

    assert tilde == f"ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu"

    result = metrics.process_filetext(
        tilde + "\n",
        wpm=165,
        pause_ratio=35.0,
        prominence_statistics={
            "function_word_count": 0,
            "explicit_word_link_count": 0,
        },
    )
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


def test_bold_markdown_preserves_adjacent_line_breaks() -> None:
    bold = printlib.convert_text("er~·ra\n~a·pil\n")[1]
    assert bold == "**er**ra\\\n**a**pil\n"


def test_bold_markdown_preserves_blank_lines_without_escape_markers() -> None:
    bold = printlib.convert_text("er~·ra\n\n~a·pil\n")[1]
    assert bold == "**er**ra\n\n**a**pil\n"


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


def test_enrich_acoustic_metrics_adds_seconds_and_mora_views() -> None:
    acoustic = {
        "delta_c": 0.75,
        "mean_interval": 1.25,
        "varco_c": 60.0,
    }
    speech = {
        "mora_duration": 0.05,
    }

    enriched = metrics.enrich_acoustic_metrics(acoustic, speech)

    assert math.isclose(enriched["delta_c_seconds"], 0.0375)
    assert math.isclose(enriched["delta_c_mora"], 0.75)
    assert math.isclose(enriched["mean_c_seconds"], 0.0625)
    assert math.isclose(enriched["mean_c_mora"], 1.25)


def test_process_file_reads_prominence_statistics_from_frontmatter(tmp_path: Path) -> None:
    tilde_file = tmp_path / "sample_tilde.txt"
    tilde_file.write_text(
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Sample\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-28\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "    prosody:\n"
        "      explicit_word_link_count: 1\n"
        "---\n\n"
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n",
        encoding="utf-8",
    )

    result = metrics.process_file(str(tilde_file), wpm=165, pause_ratio=35.0)

    assert result["original"]["prominence_statistics"] == {
        "function_word_count": 0,
        "explicit_word_link_count": 1,
        "prominence_candidate_word_count": 3,
    }


def test_process_file_missing_prominence_statistics_fails_clearly(tmp_path: Path) -> None:
    tilde_file = tmp_path / "sample_tilde.txt"
    tilde_file.write_text(
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Sample\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-28\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "---\n\n"
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n",
        encoding="utf-8",
    )

    try:
        metrics.process_file(str(tilde_file), wpm=165, pause_ratio=35.0)
        raise AssertionError("Expected missing prominence front matter to fail")
    except ValueError as exc:
        assert "missing required field" in str(exc)


def test_process_file_accepts_explicit_link_override_without_frontmatter(tmp_path: Path) -> None:
    tilde_file = tmp_path / "sample_tilde.txt"
    tilde_file.write_text(
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Sample\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-28\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "---\n\n"
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n",
        encoding="utf-8",
    )

    result = metrics.process_file(
        str(tilde_file),
        wpm=165,
        pause_ratio=35.0,
        explicit_link_count_override="1",
    )

    assert result["original"]["prominence_statistics"]["explicit_word_link_count"] == 1