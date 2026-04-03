import pytest

from akkapros.lib.frontmatter import (
    build_output_frontmatter,
    merge_frontmatter_documents,
    read_text_file,
    resolve_inherited_syllabify_options,
    validate_stage_data_consistency,
    with_inherited_syllabify_options,
)


def test_merge_frontmatter_documents_joins_titles_and_sums_stage_data(tmp_path):
    corpus_file = tmp_path / "corpus_proc.txt"
    corpus_file.write_text(
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"atfparse\"\n"
        "file:\n"
        "  id: \"doc-1\"\n"
        "  title: \"Title One\"\n"
        "  format: \"proc\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-27\"\n"
        "metadata:\n"
        "  input_file_id: null\n"
        "  options:\n"
        "    append: true\n"
        "  data:\n"
        "---\n\n"
        "šar gi-mir\n"
        "ana šarri\n"
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"atfparse\"\n"
        "file:\n"
        "  id: \"doc-2\"\n"
        "  title: \"Title Two\"\n"
        "  format: \"proc\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-27\"\n"
        "metadata:\n"
        "  input_file_id: null\n"
        "  options:\n"
        "    append: true\n"
        "  data:\n"
        "---\n\n"
        "bānu rabû\n",
        encoding="utf-8",
    )

    frontmatter, body = read_text_file(corpus_file)

    assert frontmatter is not None
    assert frontmatter["file"]["title"] == "Title One | Title Two"
    assert frontmatter["metadata"]["input_file_id"] is None
    assert frontmatter["metadata"]["data"] == {}
    assert body == "šar gi-mir\nana šarri\nbānu rabû\n"


def test_validate_stage_data_consistency_rejects_mismatch():
    input_frontmatter = {
        "metadata": {
            "data": {
                "atfparse": {
                    "line_count": 2,
                }
            }
        }
    }

    with pytest.raises(ValueError, match="line_count"):
        validate_stage_data_consistency(
            "syllabify",
            {"line_count": 3},
            input_frontmatter=input_frontmatter,
        )


def test_build_output_frontmatter_preserves_inherited_data_when_new_stage_data_is_empty():
    input_frontmatter = {
        "file": {
            "id": "proc-id",
        },
        "metadata": {
            "data": {
                "atfparse": {
                    "line_count": 2,
                }
            }
        },
    }

    frontmatter = build_output_frontmatter(
        output_path="corpus_syl.txt",
        step="syllabify",
        title="Corpus",
        body="šar¦ gi.mir¦\n",
        stage_data={},
        input_frontmatter=input_frontmatter,
        file_format="syl",
    )

    assert frontmatter["metadata"]["data"]["atfparse"] == {"line_count": 2}
    assert "syllabify" not in frontmatter["metadata"]["data"]


def test_build_output_frontmatter_can_omit_metadata_data_section():
    input_frontmatter = {
        "file": {
            "id": "tilde-id",
        },
        "metadata": {
            "data": {
                "prosody": {
                    "explicit_word_link_count": 2,
                }
            }
        },
    }

    frontmatter = build_output_frontmatter(
        output_path="corpus_metrics.txt",
        step="metrics",
        title="Corpus",
        body="metrics body\n",
        input_frontmatter=input_frontmatter,
        file_format="metrics",
        include_metadata_data=False,
    )

    assert "data" not in frontmatter["metadata"]


def test_merge_frontmatter_documents_rejects_conflicting_options():
    with pytest.raises(ValueError, match="option"):
        merge_frontmatter_documents(
            [
                {
                    "package": {"name": "akkapros", "version": "2.0.0"},
                    "pipeline": "pipeline",
                    "step": "atfparse",
                    "file": {"id": "a", "title": "One", "format": "proc", "version": "1.0.0", "date": "2026-03-27"},
                    "metadata": {"input_file_id": None, "options": {"append": True}, "data": {}},
                },
                {
                    "package": {"name": "akkapros", "version": "2.0.0"},
                    "pipeline": "pipeline",
                    "step": "atfparse",
                    "file": {"id": "b", "title": "Two", "format": "proc", "version": "1.0.0", "date": "2026-03-27"},
                    "metadata": {"input_file_id": None, "options": {"append": False}, "data": {}},
                },
            ],
            body="x\ny\n",
        )


def test_inherited_syllabify_options_round_trip_lists_and_inventory_settings():
    options = with_inherited_syllabify_options(
        {},
        extra_vowels="ø",
        extra_consonants="ɣ",
        extra_short_punct_chars="o",
        extra_long_punct_chars="!",
        extra_short_punct_pattern=["foo"],
        extra_long_punct_pattern=["bar"],
    )

    resolved = resolve_inherited_syllabify_options(
        {
            "metadata": {
                "options": {
                    **options,
                    "extra_short_punct_pattern": "['foo']",
                    "extra_long_punct_pattern": "['bar']",
                }
            }
        }
    )

    assert resolved == {
        "extra_vowels": "ø",
        "extra_consonants": "ɣ",
        "extra_short_punct_chars": "o",
        "extra_long_punct_chars": "!",
        "extra_short_punct_pattern": ["foo"],
        "extra_long_punct_pattern": ["bar"],
    }