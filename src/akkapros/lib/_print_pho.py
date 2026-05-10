"""
Akkadian Prosody Toolkit — Accent Printer Phone-Row Rendering

Internal submodule for .pho export, MBROLA format, and phone row rendering.
Imported by print.py (facade).
"""

import logging
from pathlib import Path
from typing import Tuple

from akkapros.lib.frontmatter import (
    build_output_frontmatter,
    compose_text_document,
    count_lines,
    count_syllables_from_marked_text,
    extract_lexical_words,
    read_text_file,
    resolve_file_title,
)
from akkapros.lib.phonetize import (
    EOL_TEXT,
    RESYNC_PAUSE_LABEL,
    RESYNC_PAUSE_TEXT,
    RESYNC_PAUSE_REALIZATION,
    RESYNC_PAUSE_TYPE,
    parse_phone_row,
    realize_phone_streams,
    reconstruct_tilde_from_phone_rows,
    serialize_phone_rows,
)
from akkapros.lib._print_ipa import (
    ACUTE_MARK,
    ALL_VOWELS,
    IPA_PROSODY_STRONG,
    IPA_PROSODY_WEAK,
    _detect_ipa_tag,
    _append_ipa_tag,
    _normalize_ipa_spacing,
    _preserve_markdown_lineation,
    _row_vowel_is_emphatic,
    convert_line,
)
from akkapros.lib.utils import get_logger_with_fallback


def _load_phone_rows(filename: str) -> tuple[dict | None, list[dict[str, str]]]:
    input_frontmatter, body = read_text_file(filename)
    rows: list[dict[str, str]] = []
    for line in body.splitlines():
        if not line.strip():
            continue
        rows.append(parse_phone_row(line))
    if not rows:
        raise ValueError(f'Printer input file is empty or has no phone rows: {filename}')
    return input_frontmatter, rows


def _resolve_original_phone_path(phone_filename: str, ophone_filename: str | None = None) -> str:
    if ophone_filename:
        return ophone_filename
    if not phone_filename.endswith('_phone.txt'):
        raise ValueError(
            'printer requires positional <prefix>_phone.txt input when --ophone is omitted'
        )
    derived = phone_filename[:-10] + '_ophone.txt'
    if not Path(derived).exists():
        raise ValueError(f'Derived original phone file does not exist: {derived}')
    return derived


def _render_ipa_pause_row(row: dict[str, str]) -> str:
    if row['text'] == EOL_TEXT:
        return ' ⟨linebreak⟩ ‖\n'

    out: list[str] = []
    text = row['text']
    index = 0
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue
        tag, next_index = _detect_ipa_tag(text, index)
        _append_ipa_tag(out, tag or 'punct')
        index = next_index
    if out:
        out.append(f" {IPA_PROSODY_STRONG if row['length'] == 'L' else IPA_PROSODY_WEAK} ")
    return ''.join(out)


def _render_pause_row(row: dict[str, str], mode: str) -> str:
    if (
        row['label'] == RESYNC_PAUSE_LABEL
        and row['type'] == RESYNC_PAUSE_TYPE
        and row['realization'] == RESYNC_PAUSE_REALIZATION
        and row['text'] == RESYNC_PAUSE_TEXT
    ):
        if mode == 'ipa':
            return '.'
        return ' '
    if mode == 'ipa':
        return _render_ipa_pause_row(row)
    if row['text'] == EOL_TEXT:
        return '\n'
    return f' {row["text"]} '


def _normalize_ipa_text(text: str) -> str:
    normalized_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if line.endswith('\n'):
            normalized_lines.append(_normalize_ipa_spacing(line[:-1]) + '\n')
        else:
            normalized_lines.append(_normalize_ipa_spacing(line))
    return ''.join(normalized_lines)


def _render_phone_rows(
    rows: list[dict[str, str]],
    *,
    mode: str,
    ipa_ultraheavy_hiatus: bool = False,
    print_merger: bool = False,
) -> str:
    pieces: list[str] = []
    chunk: list[dict[str, str]] = []

    def _chunk_emphatic_map(chunk_text: str) -> dict[int, bool]:
        vowel_positions = [index for index, char in enumerate(chunk_text) if char in ALL_VOWELS]
        vowel_rows = [row for row in chunk if row['category'] == 'V']
        return {
            position: _row_vowel_is_emphatic(row)
            for position, row in zip(vowel_positions, vowel_rows)
        }

    def flush_chunk() -> None:
        nonlocal chunk
        if not chunk:
            return
        chunk_text = reconstruct_tilde_from_phone_rows(chunk)
        emphatic_map = _chunk_emphatic_map(chunk_text) if mode in {'ipa', 'xar'} else None
        pieces.append(
            convert_line(
                chunk_text,
                mode=mode,
                ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus,
                print_merger=print_merger,
                emphatic_by_source_index=emphatic_map,
            )
        )
        chunk = []

    for row in rows:
        if row['category'] == 'S':
            flush_chunk()
            pieces.append(_render_pause_row(row, mode))
            continue
        chunk.append(row)

    flush_chunk()
    rendered = ''.join(pieces)
    if mode == 'ipa':
        return _normalize_ipa_text(rendered)
    if mode == 'bold':
        return ''.join(_preserve_markdown_lineation(rendered.splitlines(keepends=True)))
    return rendered


def process_file(
    input_file: str,
    output_acute_file: str,
    output_bold_file: str,
    ophone_file: str = '',
    output_ipa_file: str = '',
    output_xar_file: str = '',
    output_xar_plain_file: str = '',
    write_acute: bool = True,
    write_bold: bool = True,
    write_ipa: bool = False,
    write_xar: bool = False,
    ipa_ultraheavy_hiatus: bool = False,
    print_merger: bool = False,
    options: dict | None = None,
) -> None:
    """Read paired phone-row input and write selected output files."""
    phone_frontmatter, phone_rows = _load_phone_rows(input_file)
    resolved_ophone = _resolve_original_phone_path(input_file, ophone_file or None)
    ophone_frontmatter, ophone_rows = _load_phone_rows(resolved_ophone)
    text = reconstruct_tilde_from_phone_rows(phone_rows)
    logger = get_logger_with_fallback(__name__)
    logger.info('Computed line_count: %d', count_lines(text))
    logger.info('Computed word_count: %d', len(extract_lexical_words(text)))
    logger.info('Computed syllable_count: %d', count_syllables_from_marked_text(text))

    title_frontmatter = phone_frontmatter or ophone_frontmatter
    acute_text = _render_phone_rows(phone_rows, mode='acute', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=print_merger)
    bold_text = _render_phone_rows(phone_rows, mode='bold', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=print_merger)
    ipa_text = _render_phone_rows(phone_rows, mode='ipa', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=print_merger)
    xar_text = _render_phone_rows(phone_rows, mode='xar', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=print_merger)
    plain_xar_text = _render_phone_rows(ophone_rows, mode='xar', ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus, print_merger=False).replace(ACUTE_MARK, '')

    def _write(text: str, path: str) -> None:
        """Write text to path, ensuring a POSIX-compliant trailing newline."""
        normalized = text if text.endswith('\n') else text + '\n'
        frontmatter = build_output_frontmatter(
            output_path=path,
            step='print',
            title=resolve_file_title(title_frontmatter),
            body=normalized,
            options=options,
            input_frontmatter=phone_frontmatter,
            include_metadata_data=False,
        )
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(compose_text_document(frontmatter, normalized))

    if write_acute:
        Path(output_acute_file).parent.mkdir(parents=True, exist_ok=True)
        _write(acute_text, output_acute_file)

    if write_bold:
        Path(output_bold_file).parent.mkdir(parents=True, exist_ok=True)
        _write(bold_text, output_bold_file)

    if write_ipa:
        if not output_ipa_file:
            raise ValueError("output_ipa_file is required when write_ipa is True")
        Path(output_ipa_file).parent.mkdir(parents=True, exist_ok=True)
        _write(ipa_text, output_ipa_file)

    if write_xar:
        if not output_xar_file:
            raise ValueError("output_xar_file is required when write_xar is True")

        plain_xar_file = output_xar_plain_file
        if not plain_xar_file:
            base = Path(output_xar_file)
            plain_name = (
                base.name.replace('_accent_xar.txt', '_xar.txt')
                if base.name.endswith('_accent_xar.txt')
                else f"{base.stem}_xar.txt"
            )
            plain_xar_file = str(base.with_name(plain_name))

        Path(output_xar_file).parent.mkdir(parents=True, exist_ok=True)
        _write(xar_text, output_xar_file)

        Path(plain_xar_file).parent.mkdir(parents=True, exist_ok=True)
        _write(plain_xar_text, plain_xar_file)
