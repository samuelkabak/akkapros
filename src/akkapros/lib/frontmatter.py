#!/usr/bin/env python3
"""Front matter helpers for CLI pipeline files.

This module centralizes the YAML front matter contract introduced for the
pipeline file formats. It intentionally supports only the small YAML subset the
project emits: nested mappings with scalar values.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
import uuid
from typing import Any

from akkapros import __version__
from akkapros.lib.constants import (
    AKKADIAN_CONSONANTS,
    AKKADIAN_VOWELS,
    CLOSE_ESCAPE,
    DIPH_SEPARATOR,
    HIATUS_MARKER,
    FUNCTION_WORDS,
    OPEN_ESCAPE,
    SYL_SEPARATOR,
    SYL_WORD_ENDING,
    WORD_LINKER,
        INTERNAL_WORD_LINKER,
        MERGE_LINKERS,
)


PACKAGE_NAME = "akkapros"
PIPELINE_ID = "pipeline"
FORMAT_VERSIONS = {
    "orig": "1.0.0",
    "proc": "1.0.0",
    "trans": "1.0.0",
    "syl": "1.0.0",
    "tilde": "1.0.0",
    "phone": "1.0.0",
    "metrics": "1.0.0",
    "acute": "1.0.0",
    "bold": "1.0.0",
    "ipa": "1.0.0",
    "xar": "1.0.0",
    "mbrola": "1.0.0",
}
SUPPORTED_TEXT_FORMATS = {"orig", "proc", "trans", "syl", "tilde", "phone", "metrics", "acute", "bold", "ipa", "xar", "mbrola"}
ESCAPE_RE = re.compile(rf"{re.escape(OPEN_ESCAPE)}.*?{re.escape(CLOSE_ESCAPE)}")
MERGE_LINKER_RE = re.compile(rf"[{re.escape(WORD_LINKER)}{re.escape(INTERNAL_WORD_LINKER)}]")
AKKADIAN_LETTERS = set(AKKADIAN_VOWELS) | set(AKKADIAN_CONSONANTS)
APPEND_TITLE_SEPARATOR = " | "


def derive_format_from_path(path: str | Path) -> str:
    stem = Path(path).stem
    if stem.endswith("_accent_acute"):
        return "acute"
    if stem.endswith("_accent_bold"):
        return "bold"
    if stem.endswith("_accent_ipa"):
        return "ipa"
    if stem.endswith("_accent_xar"):
        return "xar"
    if stem.endswith("_accent_mbrola"):
        return "mbrola"
    return stem.split("_")[-1]


def _parse_scalar(raw: str) -> Any:
    if raw.startswith('"'):
        return json.loads(raw)
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "null":
        return None
    if re.fullmatch(r"-?[0-9]+", raw):
        return int(raw)
    if re.fullmatch(r"-?[0-9]+\.[0-9]+", raw):
        return float(raw)
    return raw


def parse_yaml_frontmatter(block: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for line in block.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError(f"Invalid front matter indentation: {line!r}")
        stripped = line.strip()
        key, sep, value = stripped.partition(":")
        if not sep:
            raise ValueError(f"Invalid front matter line: {line!r}")

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError("Invalid front matter structure")
        parent = stack[-1][1]

        value = value.lstrip()
        if value == "":
            node: dict[str, Any] = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = _parse_scalar(value)

    return root


def split_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text

    end_index: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        raise ValueError("Unterminated YAML front matter")

    block = "".join(lines[1:end_index])
    body = "".join(lines[end_index + 1 :])
    if body.startswith("\n"):
        body = body[1:]
    return parse_yaml_frontmatter(block), body


def _try_parse_frontmatter_at(lines: list[str], start_index: int) -> tuple[dict[str, Any], int] | None:
    if start_index >= len(lines) or lines[start_index].strip() != "---":
        return None

    end_index: int | None = None
    for idx in range(start_index + 1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        raise ValueError("Unterminated YAML front matter")

    block = "".join(lines[start_index + 1 : end_index])
    parsed = parse_yaml_frontmatter(block)
    return parsed, end_index + 1


def split_frontmatter_documents(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split one or more concatenated front-matter documents.

    Append-mode corpus files may contain several complete YAML-front-matter
    documents concatenated in one text file. This helper returns the first
    document's front matter and a body formed by concatenating the content body
    of every embedded document, stripping each front matter block before the
    content validator or downstream stages inspect the text.
    """
    lines = text.splitlines(keepends=True)
    if not lines:
        return None, text

    frontmatters: list[dict[str, Any]] = []
    body_chunks: list[str] = []
    index = 0

    while index < len(lines):
        parsed = _try_parse_frontmatter_at(lines, index)
        if parsed is None:
            if not frontmatters:
                return None, text
            body_chunks.append("".join(lines[index:]))
            break

        frontmatter, body_start = parsed
        frontmatters.append(frontmatter)

        index = body_start
        body_lines: list[str] = []
        while index < len(lines):
            maybe_next = _try_parse_frontmatter_at(lines, index)
            if maybe_next is not None:
                break
            body_lines.append(lines[index])
            index += 1

        body = "".join(body_lines)
        if body.startswith("\n"):
            body = body[1:]
        body_chunks.append(body)

    merged_body = "".join(body_chunks)
    return merge_frontmatter_documents(frontmatters, body=merged_body), merged_body


def read_text_file(path: str | Path) -> tuple[dict[str, Any] | None, str]:
    text = Path(path).read_text(encoding="utf-8")
    return split_frontmatter_documents(text)


def _dump_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _dump_mapping(lines: list[str], mapping: dict[str, Any], indent: int) -> None:
    prefix = " " * indent
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            _dump_mapping(lines, value, indent + 2)
        else:
            lines.append(f"{prefix}{key}: {_dump_scalar(value)}")


def dump_yaml_frontmatter(frontmatter: dict[str, Any]) -> str:
    lines = ["---"]
    _dump_mapping(lines, frontmatter, 0)
    lines.append("---")
    return "\n".join(lines)


def compose_text_document(frontmatter: dict[str, Any], body: str) -> str:
    normalized_body = body if body.endswith("\n") else body + "\n"
    return dump_yaml_frontmatter(frontmatter) + "\n\n" + normalized_body


def effective_options_from_namespace(namespace: Any, *, exclude: set[str] | None = None) -> dict[str, Any]:
    exclude = exclude or set()
    options: dict[str, Any] = {}
    for key, value in vars(namespace).items():
        if key.startswith("_"):
            continue
        if key in exclude:
            continue
        if value in (None, False, ""):
            continue
        if isinstance(value, (list, tuple, set)) and len(value) == 0:
            continue
        options[key] = value
    return options


INHERITED_SYLLABIFY_OPTION_DEFAULTS = {
    "extra_vowels": "",
    "extra_consonants": "",
    "extra_short_punct_chars": "",
    "extra_long_punct_chars": "",
    "extra_short_punct_pattern": [],
    "extra_long_punct_pattern": [],
}


def with_inherited_syllabify_options(
    options: dict[str, Any] | None,
    *,
    extra_vowels: str,
    extra_consonants: str,
    extra_short_punct_chars: str,
    extra_long_punct_chars: str,
    extra_short_punct_pattern: list[str] | tuple[str, ...],
    extra_long_punct_pattern: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    updated = deepcopy(options) if options else {}
    updated["extra_vowels"] = extra_vowels
    updated["extra_consonants"] = extra_consonants
    updated["extra_short_punct_chars"] = extra_short_punct_chars
    updated["extra_long_punct_chars"] = extra_long_punct_chars
    updated["extra_short_punct_pattern"] = list(extra_short_punct_pattern)
    updated["extra_long_punct_pattern"] = list(extra_long_punct_pattern)
    return updated


def resolve_inherited_syllabify_options(input_frontmatter: dict[str, Any] | None) -> dict[str, Any]:
    if not input_frontmatter:
        return deepcopy(INHERITED_SYLLABIFY_OPTION_DEFAULTS)

    options = input_frontmatter.get("metadata", {}).get("options", {})
    if not isinstance(options, dict):
        raise ValueError("invalid front matter: metadata.options must be a mapping")

    resolved = deepcopy(INHERITED_SYLLABIFY_OPTION_DEFAULTS)
    for key, default in INHERITED_SYLLABIFY_OPTION_DEFAULTS.items():
        value = deepcopy(options.get(key, default))
        if isinstance(default, list):
            if isinstance(value, str):
                try:
                    value = ast.literal_eval(value)
                except (SyntaxError, ValueError) as exc:
                    raise ValueError(
                        f"invalid front matter: metadata.options.{key} must be a list of strings"
                    ) from exc
            if isinstance(value, tuple):
                value = list(value)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError(f"invalid front matter: metadata.options.{key} must be a list of strings")
        else:
            if not isinstance(value, str):
                raise ValueError(f"invalid front matter: metadata.options.{key} must be a string")
        resolved[key] = value
    return resolved


def with_inherited_punctuation_options(
    options: dict[str, Any] | None,
    *,
    extra_short_punct_chars: str,
    extra_long_punct_chars: str,
    extra_short_punct_pattern: list[str] | tuple[str, ...],
    extra_long_punct_pattern: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    return with_inherited_syllabify_options(
        options,
        extra_vowels="",
        extra_consonants="",
        extra_short_punct_chars=extra_short_punct_chars,
        extra_long_punct_chars=extra_long_punct_chars,
        extra_short_punct_pattern=extra_short_punct_pattern,
        extra_long_punct_pattern=extra_long_punct_pattern,
    )


def resolve_inherited_punctuation_options(input_frontmatter: dict[str, Any] | None) -> dict[str, Any]:
    resolved = resolve_inherited_syllabify_options(input_frontmatter)
    return {
        "extra_short_punct_chars": resolved["extra_short_punct_chars"],
        "extra_long_punct_chars": resolved["extra_long_punct_chars"],
        "extra_short_punct_pattern": resolved["extra_short_punct_pattern"],
        "extra_long_punct_pattern": resolved["extra_long_punct_pattern"],
    }


def _stable_uuid_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _ordered_unique_non_empty(values: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    ordered: list[Any] = []
    for value in values:
        if value in (None, ""):
            continue
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _merge_titles(frontmatters: list[dict[str, Any]]) -> str | None:
    titles = _ordered_unique_non_empty([
        frontmatter.get("file", {}).get("title")
        for frontmatter in frontmatters
    ])
    if not titles:
        return None
    return APPEND_TITLE_SEPARATOR.join(str(title) for title in titles)


def _merge_scalar_identity(frontmatters: list[dict[str, Any]], path: tuple[str, ...]) -> Any:
    values: list[Any] = []
    for frontmatter in frontmatters:
        current: Any = frontmatter
        for key in path:
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(key)
        if current is not None:
            values.append(current)

    unique_values = _ordered_unique_non_empty(values)
    if len(unique_values) > 1:
        dotted = ".".join(path)
        raise ValueError(f"incompatible appended front matter field {dotted!r}: {unique_values!r}")
    return unique_values[0] if unique_values else None


def _merge_options(frontmatters: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for frontmatter in frontmatters:
        options = frontmatter.get("metadata", {}).get("options", {})
        if not isinstance(options, dict):
            raise ValueError("invalid front matter: metadata.options must be a mapping")
        for key, value in options.items():
            if key in merged and merged[key] != value:
                raise ValueError(
                    f"incompatible appended front matter option {key!r}: {merged[key]!r} != {value!r}"
                )
            merged[key] = deepcopy(value)
    return merged


def _merge_stage_data_blocks(frontmatters: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, dict[str, Any]] = {}
    for frontmatter in frontmatters:
        data = frontmatter.get("metadata", {}).get("data", {})
        if not isinstance(data, dict):
            raise ValueError("invalid front matter: metadata.data must be a mapping")
        for stage, block in data.items():
            if not isinstance(block, dict):
                raise ValueError(f"invalid front matter: metadata.data.{stage} must be a mapping")
            target = merged.setdefault(stage, {})
            for key, value in block.items():
                if key not in target:
                    target[key] = deepcopy(value)
                    continue
                existing = target[key]
                if isinstance(existing, (int, float)) and isinstance(value, (int, float)):
                    target[key] = existing + value
                elif existing != value:
                    raise ValueError(
                        f"incompatible appended front matter stage data {stage}.{key}: {existing!r} != {value!r}"
                    )
    return {stage: block for stage, block in merged.items() if block}


def _build_aggregate_file_id(
    frontmatters: list[dict[str, Any]],
    *,
    step: str,
    file_format: str,
    title: str,
    input_file_id: str | None,
    body: str,
) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            _stable_uuid_payload(
                {
                    "aggregate": True,
                    "step": step,
                    "format": file_format,
                    "title": title,
                    "input_file_id": input_file_id,
                    "document_ids": [
                        frontmatter.get("file", {}).get("id")
                        for frontmatter in frontmatters
                    ],
                    "body": body,
                }
            ),
        )
    )


def merge_frontmatter_documents(
    frontmatters: list[dict[str, Any]],
    *,
    body: str,
) -> dict[str, Any] | None:
    if not frontmatters:
        return None
    if len(frontmatters) == 1:
        return deepcopy(frontmatters[0])

    package_name = _merge_scalar_identity(frontmatters, ("package", "name"))
    package_version = _merge_scalar_identity(frontmatters, ("package", "version"))
    pipeline = _merge_scalar_identity(frontmatters, ("pipeline",))
    step = _merge_scalar_identity(frontmatters, ("step",))
    file_format = _merge_scalar_identity(frontmatters, ("file", "format"))
    format_version = _merge_scalar_identity(frontmatters, ("file", "version"))
    title = _merge_titles(frontmatters)
    options = _merge_options(frontmatters)
    stage_data = _merge_stage_data_blocks(frontmatters)

    input_ids = _ordered_unique_non_empty([
        frontmatter.get("metadata", {}).get("input_file_id")
        for frontmatter in frontmatters
    ])
    input_file_id = input_ids[0] if len(input_ids) == 1 else None

    dates = _ordered_unique_non_empty([
        frontmatter.get("file", {}).get("date")
        for frontmatter in frontmatters
    ])
    merged_date = max(dates) if dates else date.today().isoformat()

    return {
        "package": {
            "name": package_name or PACKAGE_NAME,
            "version": package_version or __version__,
        },
        "pipeline": pipeline or PIPELINE_ID,
        "step": step,
        "file": {
            "id": _build_aggregate_file_id(
                frontmatters,
                step=step,
                file_format=file_format,
                title=title,
                input_file_id=input_file_id,
                body=body,
            ),
            "title": title,
            "format": file_format,
            "version": format_version,
            "date": merged_date,
        },
        "metadata": {
            "input_file_id": input_file_id,
            "options": options,
            "data": stage_data,
        },
    }


def _flatten_stage_data(stage_data: dict[str, Any]) -> dict[str, tuple[str, Any]]:
    flattened: dict[str, tuple[str, Any]] = {}
    for stage, block in stage_data.items():
        if not isinstance(block, dict):
            continue
        for key, value in block.items():
            flattened[key] = (stage, value)
    return flattened


def validate_stage_data_consistency(
    step: str,
    stage_data: dict[str, Any] | None,
    *,
    input_frontmatter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not stage_data:
        return {}

    inherited_data = deepcopy(input_frontmatter.get("metadata", {}).get("data", {})) if input_frontmatter else {}
    prior_fields = _flatten_stage_data(inherited_data)
    cleaned: dict[str, Any] = {}

    for key, value in stage_data.items():
        previous = prior_fields.get(key)
        if previous is None:
            cleaned[key] = value
            continue
        previous_stage, previous_value = previous
        if previous_value != value:
            raise ValueError(
                f"stage data mismatch for {key!r}: inherited {previous_stage}.{key}={previous_value!r}, new {step}.{key}={value!r}"
            )

    return cleaned


def resolve_file_title(
    input_frontmatter: dict[str, Any] | None,
    *,
    override_title: str | None = None,
    fallback_title: str | None = None,
) -> str | None:
    if override_title is not None:
        return override_title
    inherited_title = (input_frontmatter or {}).get("file", {}).get("title")
    if inherited_title is not None:
        return inherited_title
    return fallback_title


def build_output_frontmatter(
    *,
    output_path: str | Path,
    step: str,
    title: str | None,
    body: str,
    options: dict[str, Any] | None = None,
    stage_data: dict[str, Any] | None = None,
    input_frontmatter: dict[str, Any] | None = None,
    input_file_id: str | None = None,
    file_format: str | None = None,
    include_metadata_data: bool = True,
) -> dict[str, Any]:
    file_format = file_format or derive_format_from_path(output_path)
    format_version = FORMAT_VERSIONS.get(file_format, "1.0.0")
    inherited_options = deepcopy(input_frontmatter.get("metadata", {}).get("options", {})) if input_frontmatter else {}
    if options:
        inherited_options.update(options)
    inherited_data: dict[str, Any] = {}
    if include_metadata_data:
        inherited_data = deepcopy(input_frontmatter.get("metadata", {}).get("data", {})) if input_frontmatter else {}
        cleaned_stage_data = validate_stage_data_consistency(
            step,
            stage_data,
            input_frontmatter=input_frontmatter,
        )
        if cleaned_stage_data:
            inherited_data[step] = cleaned_stage_data

    resolved_input_file_id = input_file_id
    if resolved_input_file_id is None and input_frontmatter:
        resolved_input_file_id = input_frontmatter.get("file", {}).get("id")

    file_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            _stable_uuid_payload(
                {
                    "step": step,
                    "format": file_format,
                    "title": title,
                    "input_file_id": resolved_input_file_id,
                    "body": body,
                }
            ),
        )
    )

    metadata = {
        "input_file_id": resolved_input_file_id,
        "options": inherited_options,
    }
    if include_metadata_data:
        metadata["data"] = inherited_data

    return {
        "package": {
            "name": PACKAGE_NAME,
            "version": __version__,
        },
        "pipeline": PIPELINE_ID,
        "step": step,
        "file": {
            "id": file_id,
            "title": title,
            "format": file_format,
            "version": format_version,
            "date": date.today().isoformat(),
        },
        "metadata": metadata,
    }


def _remove_escape_segments(text: str) -> str:
    return ESCAPE_RE.sub(" ", text)


def _normalize_word_piece(piece: str) -> str:
    normalized = piece.replace(SYL_WORD_ENDING, "")
    normalized = normalized.replace(SYL_SEPARATOR, "")
    normalized = normalized.replace(DIPH_SEPARATOR, "")
    normalized = normalized.replace(HIATUS_MARKER, "")
    normalized = normalized.replace("~", "")
    return normalized.strip()


def extract_lexical_words(text: str) -> list[str]:
    cleaned = _remove_escape_segments(text)
    words: list[str] = []

    if SYL_WORD_ENDING in cleaned:
        for segment in re.findall(rf"[^{re.escape(SYL_WORD_ENDING)}]+{re.escape(SYL_WORD_ENDING)}", cleaned):
            core = segment[:-1]
            for piece in MERGE_LINKER_RE.split(core):
                normalized = _normalize_word_piece(piece)
                if normalized and any(ch in AKKADIAN_LETTERS for ch in normalized):
                    words.append(normalized)
        return words

    normalized_text = cleaned.replace(":", " ")
    for token in normalized_text.split():
        for piece in MERGE_LINKER_RE.split(token):
            normalized = _normalize_word_piece(piece)
            if normalized and any(ch in AKKADIAN_LETTERS for ch in normalized):
                words.append(normalized)
    return words


def count_syllables_in_text(text: str) -> int:
    total = 0
    for word in extract_lexical_words(text):
        separators = sum(1 for ch in word if ch in {SYL_SEPARATOR, "-", DIPH_SEPARATOR})
        total += 1 + separators
    return total


def count_syllables_from_marked_text(text: str) -> int:
    total = 0
    for raw_word in extract_raw_lexical_words(text):
        # Hiatus is represented as either `·¨` in *_syl.txt or bare `¨` in
        # *_tilde.txt after diphthong restoration. Both encodings mark a
        # single syllable boundary and must therefore count once.
        separators = len(re.findall(rf"(?:{re.escape(SYL_SEPARATOR)}{re.escape(DIPH_SEPARATOR)}|[{re.escape(SYL_SEPARATOR)}{re.escape(DIPH_SEPARATOR)}-])", raw_word))
        total += 1 + separators
    return total


def extract_raw_lexical_words(text: str) -> list[str]:
    cleaned = _remove_escape_segments(text)
    words: list[str] = []
    if SYL_WORD_ENDING in cleaned:
        for segment in re.findall(rf"[^{re.escape(SYL_WORD_ENDING)}]+{re.escape(SYL_WORD_ENDING)}", cleaned):
            core = segment[:-1]
            for piece in MERGE_LINKER_RE.split(core):
                if any(ch in AKKADIAN_LETTERS for ch in piece):
                    words.append(piece)
        return words
    normalized_text = cleaned.replace(":", " ")
    for token in normalized_text.split():
        for piece in MERGE_LINKER_RE.split(token):
            if any(ch in AKKADIAN_LETTERS for ch in piece):
                words.append(piece)
    return words


def count_function_words(text: str) -> int:
    total = 0
    for word in extract_lexical_words(text):
        if word.replace("-", "") in FUNCTION_WORDS:
            total += 1
    return total


def count_explicit_word_links(text: str) -> int:
    return _remove_escape_segments(text).count(WORD_LINKER)


def count_prosodic_units(text: str) -> int:
    cleaned = _remove_escape_segments(text)
    return sum(1 for token in cleaned.replace(":", " ").split() if any(ch in AKKADIAN_LETTERS for ch in token))


def count_lines(text: str) -> int:
    return len(text.splitlines())


def count_non_empty_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def extract_metrics_prominence_counts(
    input_frontmatter: dict[str, Any] | None,
) -> dict[str, int]:
    stage_data = (input_frontmatter or {}).get("metadata", {}).get("data", {})
    flattened = _flatten_stage_data(stage_data)

    entry = flattened.get("explicit_word_link_count")
    if entry is None:
        raise ValueError(
            "metrics requires front matter with propagated explicit word link count; "
            "missing required field: metadata.data.prosody.explicit_word_link_count"
        )

    _, value = entry
    return {
        "explicit_word_link_count": int(value),
    }


def resolve_metrics_prominence_counts(
    text: str,
    *,
    input_frontmatter: dict[str, Any] | None = None,
    explicit_link_count_override: str | int | None = None,
) -> dict[str, int]:
    word_count = count_prosodic_units(text)
    function_word_count = count_function_words(text)
    max_explicit_links = word_count - function_word_count

    if explicit_link_count_override is None:
        resolved = extract_metrics_prominence_counts(input_frontmatter)["explicit_word_link_count"]
    else:
        try:
            resolved = int(explicit_link_count_override)
        except (TypeError, ValueError) as exc:
            raise ValueError("--explicit-link-count must be a positive integer") from exc
        if resolved < 0:
            raise ValueError("--explicit-link-count must be a positive integer")
        if resolved > max_explicit_links:
            raise ValueError(
                "--explicit-link-count must be an integer between 0 and "
                f"{max_explicit_links}, where {max_explicit_links} = word_count - function_word_count"
            )

    return {
        "function_word_count": function_word_count,
        "explicit_word_link_count": resolved,
    }


def build_atfparse_stage_data(proc_body: str) -> dict[str, int]:
    return {}


def build_syllabify_stage_data(
    proc_body: str,
    syl_body: str,
    *,
    input_frontmatter: dict[str, Any] | None = None,
) -> dict[str, int]:
    return {}


def build_prosody_stage_data(
    syl_body: str,
    tilde_body: str,
    *,
    input_frontmatter: dict[str, Any] | None = None,
    accentuated_syllable_count: int | None = None,
) -> dict[str, int]:
    return {}


def build_metrics_stage_data(
    tilde_body: str,
    result: dict[str, Any],
    *,
    input_frontmatter: dict[str, Any] | None = None,
) -> dict[str, int]:
    return {}