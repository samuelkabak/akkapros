from __future__ import annotations

import re
from typing import List, Union

from akkapros.lib.constants import (
    CLOSE_ESCAPE,
    FUNCTION_WORDS,
    HIATUS_MARKER,
    MERGE_LINKERS,
    OPEN_ESCAPE,
    SYL_SEPARATOR,
    SYL_WORD_ENDING,
    WORD_LINKER,
)
from akkapros.lib.diphthongs import ALL_REPLACEMENTS


HYPHEN = '-'


def is_function_word(word_text: str) -> bool:
    """Return True if word is a function word (ignoring dots and hyphens)."""
    return (
        word_text.replace(SYL_SEPARATOR, '')
        .replace(HYPHEN, '')
        .replace(HIATUS_MARKER, '') in FUNCTION_WORDS
    )


def parse_syl_line(line: str) -> List[Union[object, str]]:
    from akkapros.lib.prosody_model import Word

    if not line.strip():
        return []

    tokens = []
    i = 0
    n = len(line)
    word_count = 0

    while i < n:
        if line[i] == OPEN_ESCAPE:
            j = line.find(CLOSE_ESCAPE, i)
            if j == -1:
                j = n
            tokens.append(line[i:j+1])
            i = j + 1
        elif line[i].isspace():
            i += 1
        elif line[i] == WORD_LINKER:
            tokens.append(WORD_LINKER)
            i += 1
        elif line[i] == SYL_WORD_ENDING:
            i += 1
        else:
            start = i
            while i < n and line[i] != SYL_WORD_ENDING and line[i] != OPEN_ESCAPE and line[i] != WORD_LINKER:
                i += 1
            if start < i:
                word_text = line[start:i]
                if word_text:
                    tokens.append(Word(word_text, word_count))
                    word_count += 1

    return tokens


def assemble_line(parts: List[str], tokens: List[Union[object, str]]) -> str:
    """
    Assemble the final line with proper underscore attachment.
    Underscores attach to the preceding word only.
    """
    from akkapros.lib.prosody_model import Word

    if not parts:
        return ""

    combined = []
    i = 0
    while i < len(parts):
        if parts[i] in MERGE_LINKERS:
            if combined:
                combined[-1] = combined[-1] + parts[i]
            i += 1
        else:
            if combined and combined[-1].endswith(tuple(MERGE_LINKERS)):
                combined[-1] = combined[-1] + parts[i]
            else:
                combined.append(parts[i])
            i += 1

    akkadian_chars = set()
    for token in tokens:
        if isinstance(token, Word):
            for syllable in token.syllables:
                for c in syllable.text:
                    if c not in (SYL_SEPARATOR, HYPHEN):
                        akkadian_chars.add(c)
    akkadian_chars.add('~')

    def is_word(text: str) -> bool:
        """Return True if text contains Akkadian letters."""
        return any(c in akkadian_chars for c in text)

    result = []
    i = 0
    while i < len(combined):
        result.append(combined[i])
        if i < len(combined) - 1 and is_word(combined[i]) and is_word(combined[i + 1]):
            result.append(' ')
        i += 1

    assembled = ''.join(result)
    assembled = re.sub(r' {2,}', ' ', assembled)
    return assembled.strip()


def _pivot_diphthong_replacement(replacement: str) -> str:
    """Generated replacements already encode the exact pivot form to emit."""
    return replacement


def postprocess_restore_diphthongs(output_lines: List[str]) -> List[str]:
    """
    Restore diphthongs using generated regex patterns.

    The *_tilde pivot format keeps DIPH_SEPARATOR so downstream metrics and
    print rendering can still see restored diphthong-internal syllable breaks.
    """

    new_lines = []
    for line in output_lines:
        for pattern, repl in ALL_REPLACEMENTS:
            line = re.sub(pattern, _pivot_diphthong_replacement(repl), line)
        new_lines.append(line)

    return new_lines