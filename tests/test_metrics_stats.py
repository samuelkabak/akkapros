import json
import math
from pathlib import Path

from akkapros.lib.frontmatter import compose_text_document, split_frontmatter
from akkapros.lib import metrics
from akkapros.lib import print as printlib
from akkapros.lib.constants import DIPH_SEPARATOR, SYL_SEPARATOR
from akkapros.lib.phonetize import build_default_phonetize_config, build_phone_rows, parse_phone_row, realize_phone_streams, serialize_phone_rows
from akkapros.lib.prosody import AccentStyle, ProsodyEngine, parse_syl_line, postprocess_restore_diphthongs
from akkapros.lib.syllabify import syllabify_text
from akkapros.lib.utils import format_path_for_logging


SAMPLE_PROC_TEXT = """appūnā-ma ištēn-ešret : kīma šuāti uštabši
ina ilī bukrīša : šūt iškunūši puḫra
ušašqi qingu : ina birīšunu šâšu ušrabbīš
ālikūt maḫri pān ummāni muʾerrūt puḫri
"""

VARCO_VERIFICATION_SAMPLE = "šazu šuḫgurim ina rebî : šākin tašmê ana ilī abbīšu\n"
VARCO_VERIFICATION_ORIGINAL = {
    "percent_c": 31.944444444444443,
    "percent_v": 35.52777777777778,
    "mean_c_ms": 109.52380952380952,
    "mean_v_ms": 127.9,
    "delta_c_ms": 50.67320043800653,
    "delta_v_ms": 34.222653316188094,
    "varco_c": 46.26683518252771,
    "varco_v": 26.75735208458803,
    "rpvi_c": 59.0,
    "npvi_v": 21.698221153635842,
}
VARCO_VERIFICATION_ACCENTUATED = {
    "percent_c": 33.013333333333335,
    "percent_v": 36.733333333333334,
    "mean_c_ms": 123.8,
    "mean_v_ms": 137.75,
    "delta_c_ms": 64.1237865382262,
    "delta_v_ms": 51.86508941474988,
    "varco_c": 51.796273455756214,
    "varco_v": 37.651607560616974,
    "rpvi_c": 75.78947368421052,
    "npvi_v": 30.249305872660635,
}
VARCO_VERIFICATION_ORIGINAL_DRIFT = {
    "max": 150.0,
    "mean": 32.4167,
    "stddev": 49.3203,
}
VARCO_VERIFICATION_ACCENTUATED_DRIFT = {
    "max": 189.0,
    "mean": 28.1739,
    "stddev": 63.0787,
}
LEXLINKS_CONSTRUCT_OPHONE = Path("demo/akkapros/lexlinks/results/erra_construct_ophone.txt")
LEXLINKS_CONSTRUCT_PHONE = Path("demo/akkapros/lexlinks/results/erra_construct_phone.txt")
LEXLINKS_REFERENCE_WORD_COUNTS = {
    "original": 1169,
    "accentuated": 963,
}
LEXLINKS_REFERENCE_PROMINENCE = {
    "function_word_count": 189,
    "explicit_word_link_count": 63,
    "prominence_candidate_word_count": 917,
}
SMALL_SAMPLE_REFERENCE = {
    "original": {
        "stats": {
            "total_syllables": 60,
            "syllable_counts": {
                "CV": 22,
                "CVC": 10,
                "CVV": 9,
                "CVVC": 6,
                "V": 4,
                "VC": 7,
                "VV": 2,
            },
            "word_stats": {
                "total_words": 22,
                "syllables_per_word": {
                    "mean": 2.727272727272727,
                    "std": 1.1204513623586057,
                },
                "morae_per_word": {
                    "mean": 4.545454545454546,
                    "std": 1.4712247158412493,
                },
            },
            "mora_stats": {
                "mean": 1.6666666666666667,
                "std": 0.6552698154756148,
                "total": 100,
            },
        },
        "prominence_statistics": {
            "function_word_count": 2,
            "explicit_word_link_count": 1,
            "prominence_candidate_word_count": 19,
        },
    },
    "accentuated": {
        "stats": {
            "total_syllables": 60,
            "syllable_counts": {
                "CV": 22,
                "CVC": 5,
                "CVC:": 5,
                "CVV": 2,
                "CVV:": 7,
                "CVV:C": 3,
                "CVVC": 3,
                "V": 4,
                "VC": 6,
                "VC:": 1,
                "VV": 2,
            },
            "word_stats": {
                "total_words": 22,
                "syllables_per_word": {
                    "mean": 2.727272727272727,
                    "std": 1.1204513623586057,
                },
                "morae_per_word": {
                    "mean": 5.2727272727272725,
                    "std": 1.4203225046854737,
                },
            },
            "mora_stats": {
                "mean": 1.9333333333333333,
                "std": 0.954324087130172,
                "total": 116,
            },
        },
    },
    "accentuation_stats": {
        "accentuated_syllables": 16,
        "accentuation_rate": 26.666666666666668,
        "accentuation_types": {
            "CVC:": 5,
            "CVV:": 7,
            "CVV:C": 3,
            "VC:": 1,
        },
        "merged_words": 4,
        "merged_units": 2,
        "avg_unit_size": 2.0,
    },
}
LEXLINKS_REFERENCE_METRICS = {
    "original": {
        "stats": {
            "total_syllables": 2989,
            "word_stats": {
                "total_words": 1169,
                "morae_per_word": {
                    "mean": 3.97519247219846,
                    "std": 1.6783983573546182,
                },
            },
            "mora_stats": {
                "mean": 1.554700568752091,
                "std": 0.5531661505946163,
                "total": 4647,
            },
            "merge_stats": {
                "total_merged_words": 124,
                "merged_units": 61,
                "avg_unit_size": 2.0327868852459017,
            },
        },
        "acoustic": {
            "percent_c": 31.793444599516068,
            "percent_v": 30.34329553806641,
            "mean_c_ms": 112.60675983100423,
            "mean_v_ms": 110.63466042154566,
            "delta_c_ms": 59.83111911232471,
            "delta_v_ms": 43.67900892958426,
            "varco_c": 53.13279522660708,
            "varco_v": 39.480402220385855,
            "rpvi_c": 72.50585175552666,
            "npvi_v": 32.238025778638516,
        },
        "drift": {
            "max": 315.0,
            "mean": -32.0933,
            "stddev": 65.2012,
        },
        "prominence_statistics": {
            "function_word_count": 189,
            "explicit_word_link_count": 63,
            "prominence_candidate_word_count": 917,
        },
    },
    "accentuated": {
        "stats": {
            "total_syllables": 2989,
            "word_stats": {
                "total_words": 963,
                "morae_per_word": {
                    "mean": 5.393561786085151,
                    "std": 1.6433068693377408,
                },
            },
            "mora_stats": {
                "mean": 1.7377049180327868,
                "std": 0.7941302095614974,
                "total": 5194,
            },
            "merge_stats": {
                "total_merged_words": 522,
                "merged_units": 253,
                "avg_unit_size": 2.0632411067193677,
            },
        },
        "acoustic": {
            "percent_c": 33.14144039904045,
            "percent_v": 31.13352600456254,
            "mean_c_ms": 124.91492829204694,
            "mean_v_ms": 120.44831047172967,
            "delta_c_ms": 74.31371974760972,
            "delta_v_ms": 56.822572145599395,
            "varco_c": 59.49146412177952,
            "varco_v": 47.175898045440974,
            "rpvi_c": 90.61102054124552,
            "npvi_v": 41.781706015357734,
        },
        "drift": {
            "max": 412.0,
            "mean": -36.9931,
            "stddev": 74.6999,
        },
    },
    "accentuation_stats": {
        "accentuated_syllables": 547,
        "accentuation_rate": 18.30043492806959,
        "accentuation_types": {
            "CVV:C": 18,
            "CVC:": 174,
            "VV:": 13,
            "VC:": 60,
            "CVV:": 282,
        },
        "merged_words": 522,
        "merged_units": 253,
        "avg_unit_size": 2.0632411067193677,
    },
}


def _assert_nested_expected(actual: dict, expected: dict) -> None:
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if isinstance(expected_value, dict):
            assert isinstance(actual_value, dict), key
            _assert_nested_expected(actual_value, expected_value)
        elif isinstance(expected_value, float):
            assert math.isclose(actual_value, expected_value, rel_tol=0.0, abs_tol=1e-12), key
        else:
            assert actual_value == expected_value, key


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


def _write_phone_pair(tmp_path: Path, prefix: str, tilde_text: str) -> tuple[Path, Path]:
    (ophone_rows, _ophone_report), (phone_rows, _phone_report) = realize_phone_streams(
        tilde_text,
        build_default_phonetize_config(),
        None,
    )
    ophone_file = tmp_path / f"{prefix}_ophone.txt"
    phone_file = tmp_path / f"{prefix}_phone.txt"
    ophone_file.write_text(serialize_phone_rows(ophone_rows), encoding="utf-8")
    phone_file.write_text(serialize_phone_rows(phone_rows), encoding="utf-8")
    return ophone_file, phone_file


def _build_varco_verification_tilde() -> str:
    syllabified = syllabify_text(VARCO_VERIFICATION_SAMPLE, preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    accentuated = [engine.accentuation_line(parse_syl_line(line)) for line in syllabified.splitlines() if line.strip()]
    return "\n".join(postprocess_restore_diphthongs(accentuated)) + "\n"


def _write_phone_pair_with_drift_frontmatter(tmp_path: Path, prefix: str, tilde_text: str) -> tuple[Path, Path]:
    (ophone_rows, ophone_report), (phone_rows, phone_report) = realize_phone_streams(
        tilde_text,
        build_default_phonetize_config(),
        None,
    )
    ophone_frontmatter = {
        "metadata": {
            "data": {
                "phonetize": {
                    "drift": {
                        "max": ophone_report["drift"]["max"],
                        "mean": ophone_report["drift"]["mean"],
                        "stddev": ophone_report["drift"]["stddev"],
                    },
                }
            }
        }
    }
    phone_frontmatter = {
        "metadata": {
            "data": {
                "phonetize": {
                    "drift": {
                        "max": phone_report["drift"]["max"],
                        "mean": phone_report["drift"]["mean"],
                        "stddev": phone_report["drift"]["stddev"],
                    },
                }
            }
        }
    }
    ophone_file = tmp_path / f"{prefix}_ophone.txt"
    phone_file = tmp_path / f"{prefix}_phone.txt"
    ophone_file.write_text(compose_text_document(ophone_frontmatter, serialize_phone_rows(ophone_rows)), encoding="utf-8")
    phone_file.write_text(compose_text_document(phone_frontmatter, serialize_phone_rows(phone_rows)), encoding="utf-8")
    return ophone_file, phone_file


def _count_reference_words_from_phone_file(path: Path) -> int:
    _frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    count = 0
    after_separator = True
    previous_boundary = None

    for raw_line in body.splitlines():
        if not raw_line.strip():
            continue
        row = parse_phone_row(raw_line)
        if row["category"] == "S":
            after_separator = True
            previous_boundary = None
            continue
        if after_separator or previous_boundary == "F":
            count += 1
        after_separator = False
        previous_boundary = row["boundary"]

    return count


def test_small_corpus_metrics_formula_consistency() -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
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
        assert speech["articulation_duration_ms"] == speech["total_duration_ms"] - speech["pause_duration_ms"]
        expected_wpm = total_words / (speech["total_duration_ms"] / 60000.0) if speech["total_duration_ms"] else 0.0
        expected_pause_ratio = (speech["pause_duration_ms"] / speech["total_duration_ms"] * 100.0) if speech["total_duration_ms"] else 0.0
        assert speech["wpm"] == expected_wpm
        assert speech["pause_ratio"] == expected_pause_ratio

    pause_metrics = metrics.compute_pause_metrics(
        build_phone_rows(_build_sample_tilde()),
        result["accentuated"]["stats"],
    )
    accentuated_total_syllables = result["accentuated"]["stats"]["total_syllables"]
    assert pause_metrics["punctuation_per_syllable"] == pause_metrics["raw_counts"]["punctuation"] / accentuated_total_syllables
    assert pause_metrics["short_punctuation_per_syllable"] == pause_metrics["raw_counts"]["short_punctuation"] / accentuated_total_syllables
    assert pause_metrics["long_punctuation_per_syllable"] == pause_metrics["raw_counts"]["long_punctuation"] / accentuated_total_syllables

    accentuation_stats = result["accentuation_stats"]
    original_total_syllables = result["original"]["stats"]["total_syllables"]
    assert accentuation_stats["accentuation_rate"] == accentuation_stats["accentuated_syllables"] / original_total_syllables * 100.0


def test_small_corpus_metrics_match_fixed_reference_values() -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
        prominence_statistics=_sample_prominence_counts(),
    )

    _assert_nested_expected(result["original"], SMALL_SAMPLE_REFERENCE["original"])
    _assert_nested_expected(result["accentuated"], SMALL_SAMPLE_REFERENCE["accentuated"])
    _assert_nested_expected(result["accentuation_stats"], SMALL_SAMPLE_REFERENCE["accentuation_stats"])


def test_compute_speech_metrics_from_rows_matches_manual_formula() -> None:
    (_ophone_rows, _ophone_report), (rows, _phone_report) = realize_phone_streams(
        _build_sample_tilde(),
        build_default_phonetize_config(),
        None,
    )
    stats = metrics.analyze_text(_build_sample_tilde(), is_accentuated=True)

    speech = metrics.compute_speech_metrics_from_rows(rows, stats)

    total_duration_ms = sum(int(row["duration"]) for row in rows)
    pause_duration_ms = sum(int(row["duration"]) for row in rows if row["category"] == "S")
    expected_wpm = stats["word_stats"]["total_words"] / (total_duration_ms / 60000.0) if total_duration_ms else 0.0

    assert speech == {
        "total_duration_ms": total_duration_ms,
        "pause_duration_ms": pause_duration_ms,
        "articulation_duration_ms": total_duration_ms - pause_duration_ms,
        "wpm": expected_wpm,
        "pause_ratio": pause_duration_ms / total_duration_ms * 100.0,
        "pause_row_count": sum(1 for row in rows if row["category"] == "S"),
    }


def test_small_corpus_metrics_outputs_surface_totals(tmp_path: Path) -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
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
    assert (
        f"Prominence candidates: {result['original']['prominence_statistics']['prominence_candidate_word_count']} words"
        in table
    )
    assert f"%C: {result['original']['acoustic']['percent_c']:.2f}%" in table
    assert f"%V: {result['original']['acoustic']['percent_v']:.2f}%" in table
    assert f"ΔC: {result['original']['acoustic']['delta_c_ms']:.2f} ms" in table
    assert f"ΔV: {result['original']['acoustic']['delta_v_ms']:.2f} ms" in table
    assert f"meanC: {result['original']['acoustic']['mean_c_ms']:.2f} ms" in table
    assert f"meanV: {result['original']['acoustic']['mean_v_ms']:.2f} ms" in table
    assert f"VarcoC: {result['original']['acoustic']['varco_c']:.2f}" in table
    assert f"VarcoV: {result['original']['acoustic']['varco_v']:.2f}" in table
    assert f"rPVI-C: {result['original']['acoustic']['rpvi_c']:.2f}" in table
    assert f"nPVI-V: {result['original']['acoustic']['npvi_v']:.2f}" in table
    assert f"VarcoC: {result['original']['acoustic']['varco_c']:.2f} %" not in table
    assert f"Total syllables: {result['original']['stats']['total_syllables']} syllables" in table
    assert f"Total syllables: {result['accentuated']['stats']['total_syllables']} syllables" in table
    assert table.count("Speech metrics:") == 2
    assert "Speech rate (original):" not in table
    assert "Speech rate (accentuated):" not in table
    assert "Pause metrics:" not in table
    assert "Pause duration allocation" not in table
    assert "SPS (speech):" not in table
    assert "Average syllable duration:" not in table
    assert "Total duration:" in table
    assert "Total pause duration:" in table
    assert "Total articulate duration:" in table

    json_text = json.dumps(result, ensure_ascii=False)
    assert '"syllable_statistics"' in json_text
    assert '"word_statistics"' in json_text
    assert '"mora_statistics"' in json_text
    assert '"percent_c"' in json_text
    assert '"delta_c_ms"' in json_text
    assert '"delta_v_ms"' in json_text
    assert '"mean_c_ms"' in json_text
    assert '"mean_v_ms"' in json_text
    assert '"prominence_statistics"' in json_text
    assert (
        f'"prominence_candidate_word_count": {result["original"]["prominence_statistics"]["prominence_candidate_word_count"]}'
        in json_text
    )

    original_stats = result["original"]["stats"]
    assert original_stats["word_statistics"]["total_words"] == original_stats["word_stats"]["total_words"]
    assert original_stats["mora_statistics"]["total_morae"] == original_stats["mora_stats"]["total"]
    assert original_stats["mora_statistics"]["mean_morae_per_word"]["mean"] == original_stats["word_stats"]["morae_per_word"]["mean"]
    expected_candidate_count = original_stats["word_stats"]["total_words"] - 2 - 1
    assert result["original"]["prominence_statistics"] == {
        "function_word_count": 2,
        "explicit_word_link_count": 1,
        "prominence_candidate_word_count": expected_candidate_count,
    }
    assert set(result["original"]["speech"]) == {
        "total_duration_ms",
        "pause_duration_ms",
        "articulation_duration_ms",
        "wpm",
        "pause_ratio",
        "pause_row_count",
    }
    assert set(result["accentuated"]["speech"]) == {
        "total_duration_ms",
        "pause_duration_ms",
        "articulation_duration_ms",
        "wpm",
        "pause_ratio",
        "pause_row_count",
    }
    assert "pause_metrics" not in result["accentuated"]
    assert "pause_durations" not in result["accentuated"]

    original_other = result["original"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0)
    accentuated_other = result["accentuated"]["stats"]["syllable_counts"].get(metrics.UNCLASSIFIED_SYLLABLE_TYPE, 0)
    assert original_other == 0
    assert accentuated_other == 0
    assert metrics.UNCLASSIFIED_SYLLABLE_TYPE not in table
    assert not hasattr(metrics, "format_csv")


def test_process_filetext_shortens_artifact_file_path() -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
        filesrc=r"C:\Users\samue\private\results\sample_tilde.txt",
        prominence_statistics=_sample_prominence_counts(),
    )

    assert result["file"] == r"...\results\sample_tilde.txt"


def test_process_file_uses_safe_path_display(tmp_path: Path) -> None:
    base = tmp_path / "alpha" / "beta"
    base.mkdir(parents=True)
    ophone_file, phone_file = _write_phone_pair(base, "sample", "er~·ra\n")

    result = metrics.process_file(str(phone_file), ophone_filename=str(ophone_file))

    assert result["file"] == format_path_for_logging(phone_file)


def test_format_table_shortens_run_context_input_path() -> None:
    result = metrics.process_filetext(
        _build_sample_tilde(),
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
        prominence_statistics={
            "function_word_count": 0,
            "explicit_word_link_count": 0,
        },
    )

    raw_counts = metrics.compute_pause_metrics(
        build_phone_rows(tilde),
        result["accentuated"]["stats"],
    )["raw_counts"]
    assert raw_counts["long_punctuation"] == 1
    assert raw_counts["short_punctuation"] == 1


def test_metrics_accepts_unknown_armored_punctuation_as_internal_pause() -> None:
    stats = metrics.analyze_text("at·tā⟦ @ ⟧ā·lik", is_accentuated=True)
    rows = build_phone_rows("at·tā⟦ @ ⟧ā·lik")
    pause_rows = [row for row in rows if row["category"] == "S"]
    pause_metrics = metrics.compute_pause_metrics(rows, stats)

    assert len(pause_rows) == 2
    assert pause_rows[0]["type"] == "I"
    assert pause_rows[0]["length"] == "S"
    assert pause_metrics["raw_counts"]["short_punctuation"] == 1
    assert pause_metrics["raw_counts"]["long_punctuation"] == 1


def test_diphthong_separator_propagates_to_tilde_metrics_and_print() -> None:
    tilde = postprocess_restore_diphthongs([
        f"ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu"
    ])[0]

    assert tilde == f"ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu"

    result = metrics.process_filetext(
        tilde + "\n",
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


def test_process_file_derives_prominence_statistics_from_phone_rows(tmp_path: Path) -> None:
    ophone_file, phone_file = _write_phone_pair(
        tmp_path,
        "sample",
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n",
    )

    result = metrics.process_file(str(phone_file), ophone_filename=str(ophone_file))

    assert result["original"]["prominence_statistics"] == {
        "function_word_count": 0,
        "explicit_word_link_count": 1,
        "prominence_candidate_word_count": 3,
    }


def test_process_file_missing_derived_ophone_fails_clearly(tmp_path: Path) -> None:
    phone_file = tmp_path / "sample_phone.txt"
    phone_file.write_text("AA-V-V-S-N-N-A-AA-0100:a\n", encoding="utf-8")

    try:
        metrics.process_file(str(phone_file))
        raise AssertionError("Expected missing sibling _ophone.txt to fail")
    except ValueError as exc:
        assert "Derived original phone file does not exist" in str(exc)


def test_compute_interval_metrics_uses_manual_phone_intervals() -> None:
    rows = [
        {"category": "V", "duration": "0100"},
        {"category": "C", "duration": "0080"},
        {"category": "C", "duration": "0040"},
        {"category": "S", "duration": "0100"},
        {"category": "C", "duration": "0045"},
        {"category": "V", "duration": "0245"},
    ]

    acoustic = metrics.compute_interval_metrics(rows)

    assert acoustic["intervals"] == [("V", 100), ("C", 120), ("P", 100), ("C", 45), ("V", 245)]
    assert math.isclose(acoustic["percent_v"], 345 / 610 * 100)
    assert math.isclose(acoustic["percent_c"], 165 / 610 * 100)
    assert math.isclose(acoustic["mean_v_ms"], 172.5)
    assert math.isclose(acoustic["mean_c_ms"], 82.5)
    assert math.isclose(acoustic["delta_v_ms"], 72.5)
    assert math.isclose(acoustic["delta_c_ms"], 37.5)
    assert math.isclose(acoustic["varco_v"], 42.028985507246375)
    assert math.isclose(acoustic["varco_c"], 45.45454545454545)
    assert math.isclose(acoustic["rpvi_c"], 75.0)
    assert math.isclose(acoustic["npvi_v"], 84.05797101449275)


def test_compute_interval_metrics_zero_case_returns_zero_public_metrics() -> None:
    acoustic = metrics.compute_interval_metrics([])

    assert acoustic["intervals"] == []
    assert acoustic["v_intervals_ms"] == []
    assert acoustic["c_intervals_ms"] == []
    assert acoustic["p_intervals_ms"] == []
    assert acoustic["total_duration_ms"] == 0
    assert acoustic["percent_v"] == 0.0
    assert acoustic["percent_c"] == 0.0
    assert acoustic["mean_v_ms"] == 0.0
    assert acoustic["mean_c_ms"] == 0.0
    assert acoustic["delta_v_ms"] == 0.0
    assert acoustic["delta_c_ms"] == 0.0
    assert acoustic["varco_v"] == 0.0
    assert acoustic["varco_c"] == 0.0
    assert acoustic["rpvi_c"] == 0.0
    assert acoustic["npvi_v"] == 0.0


def test_metrics_loader_accepts_phone_rows_with_drift_column(tmp_path: Path) -> None:
    phone_file = tmp_path / "sample_phone.txt"
    phone_file.write_text(
        "---\n"
        "file:\n"
        "  format: \"phone\"\n"
        "---\n\n"
        "KAP|C|C|S|O|N|F|KA|0108|+003|M0C|k\n",
        encoding="utf-8",
    )

    _frontmatter, rows, _body = metrics._load_phone_rows(str(phone_file))

    assert rows[0]["duration"] == "0108"
    assert rows[0]["drift"] == "+003"
    assert rows[0]["intonation"] == "M0C"
    assert rows[0]["text"] == "k"


def test_single_line_metrics_match_manual_varco_verification_reference(tmp_path: Path) -> None:
    ophone_file, phone_file = _write_phone_pair_with_drift_frontmatter(
        tmp_path,
        "varco-verification",
        _build_varco_verification_tilde(),
    )

    result = metrics.process_file(
        str(phone_file),
        ophone_filename=str(ophone_file),
    )

    for key, expected in VARCO_VERIFICATION_ORIGINAL.items():
        assert math.isclose(result["original"]["acoustic"][key], expected, rel_tol=0.0, abs_tol=1e-9), key

    for key, expected in VARCO_VERIFICATION_ACCENTUATED.items():
        assert math.isclose(result["accentuated"]["acoustic"][key], expected, rel_tol=0.0, abs_tol=1e-9), key

    assert result["original"]["drift"] == VARCO_VERIFICATION_ORIGINAL_DRIFT
    assert result["accentuated"]["drift"] == VARCO_VERIFICATION_ACCENTUATED_DRIFT


def test_lexlinks_construct_word_counts_match_independent_reference() -> None:
    assert LEXLINKS_CONSTRUCT_OPHONE.exists()
    assert LEXLINKS_CONSTRUCT_PHONE.exists()

    assert _count_reference_words_from_phone_file(LEXLINKS_CONSTRUCT_OPHONE) == LEXLINKS_REFERENCE_WORD_COUNTS["original"]
    assert _count_reference_words_from_phone_file(LEXLINKS_CONSTRUCT_PHONE) == LEXLINKS_REFERENCE_WORD_COUNTS["accentuated"]

    result = metrics.process_file(
        str(LEXLINKS_CONSTRUCT_PHONE),
        ophone_filename=str(LEXLINKS_CONSTRUCT_OPHONE),
    )

    assert result["original"]["stats"]["word_stats"]["total_words"] == LEXLINKS_REFERENCE_WORD_COUNTS["original"]
    assert result["original"]["stats"]["word_statistics"]["total_words"] == LEXLINKS_REFERENCE_WORD_COUNTS["original"]
    assert result["accentuated"]["stats"]["word_stats"]["total_words"] == LEXLINKS_REFERENCE_WORD_COUNTS["accentuated"]
    assert result["accentuated"]["stats"]["word_statistics"]["total_words"] == LEXLINKS_REFERENCE_WORD_COUNTS["accentuated"]
    assert result["original"]["prominence_statistics"] == LEXLINKS_REFERENCE_PROMINENCE

    _assert_nested_expected(result["original"], LEXLINKS_REFERENCE_METRICS["original"])
    _assert_nested_expected(result["accentuated"], LEXLINKS_REFERENCE_METRICS["accentuated"])
    _assert_nested_expected(result["accentuation_stats"], LEXLINKS_REFERENCE_METRICS["accentuation_stats"])

    table = metrics.format_table(result)
    assert "Total syllables: 2989 syllables" in table
    assert "Total words: 1169 words" in table
    assert "Total words: 963 words" in table
    assert "Mean morae per syllable: 1.555" in table
    assert "Mean morae per word: 3.975" in table
    assert "Total morae: 4647 mora" in table
    assert "Function words: 189 words" in table
    assert "Explicitly linked words: 63 words" in table
    assert "Prominence candidates: 917 words" in table
    assert table.count("Speech metrics:") == 2
    assert "Speech rate (original):" not in table
    assert "Pause metrics:" not in table
    assert "Pause duration allocation" not in table
    assert "%C: 31.79%" in table
    assert "%V: 30.34%" in table
    assert "meanC: 112.61 ms" in table
    assert "meanV: 110.63 ms" in table
    assert "ΔC: 59.83 ms" in table
    assert "ΔV: 43.68 ms" in table
    assert "VarcoC: 53.13" in table
    assert "VarcoV: 39.48" in table
    assert "rPVI-C: 72.51" in table
    assert "nPVI-V: 32.24" in table
    assert "Drift max: 315.00 ms" in table
    assert "Drift mean: -32.09 ms" in table
    assert "Drift stddev: 65.20 ms" in table
    assert "Accentuated syllables: 547" in table
    assert "Accentuation rate: 18.30%" in table