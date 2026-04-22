from __future__ import annotations

import re
from typing import List, Optional, Tuple

from akkapros.lib.constants import (
    CLOSE_PRESERVE,
    CLOSE_PRESERVE_CHAR,
    OPEN_PRESERVE,
    OPEN_PRESERVE_CHAR,
    TAG_PRESERVE_RE,
)


ESCAPE_TAG_RE = re.compile(rf'^{TAG_PRESERVE_RE}$')


def parse_escape_at(text: str, start: int) -> Optional[Tuple[str, int]]:
    """Parse one escape token at ``start`` and return ``(token, next_index)``.

    Supported forms:
    - ``{{text}}``
    - ``{tag{text}}`` where ``tag`` matches ``[0-9a-z_]{1,16}``

    Nested escapes are intentionally unsupported.
    """
    n = len(text)
    if start >= n:
        return None

    if text.startswith(OPEN_PRESERVE, start):
        close_idx = text.find(CLOSE_PRESERVE, start + len(OPEN_PRESERVE))
        if close_idx == -1:
            return None
        payload = text[start + len(OPEN_PRESERVE):close_idx]
        if OPEN_PRESERVE_CHAR in payload or CLOSE_PRESERVE_CHAR in payload:
            return None
        return f"{OPEN_PRESERVE}{payload}{CLOSE_PRESERVE}", close_idx + len(CLOSE_PRESERVE)

    if text[start] != OPEN_PRESERVE_CHAR:
        return None

    tag_end = text.find(OPEN_PRESERVE_CHAR, start + 1)
    if tag_end == -1:
        return None

    tag = text[start + 1:tag_end]
    if not ESCAPE_TAG_RE.fullmatch(tag):
        return None

    close_idx = text.find(CLOSE_PRESERVE, tag_end + 1)
    if close_idx == -1:
        return None

    payload = text[tag_end + 1:close_idx]
    if OPEN_PRESERVE_CHAR in payload or CLOSE_PRESERVE_CHAR in payload:
        return None
    return (
        f"{OPEN_PRESERVE_CHAR}{tag}{OPEN_PRESERVE_CHAR}{payload}{CLOSE_PRESERVE}",
        close_idx + len(CLOSE_PRESERVE),
    )


def split_by_escape_segments(text: str) -> List[Tuple[bool, str]]:
    """Split text into ``(is_escape, segment)`` tuples.

    This intentionally supports only ``{{...}}`` and ``{tag{...}}`` forms.
    """
    segments: List[Tuple[bool, str]] = []
    i = 0
    last = 0
    n = len(text)

    while i < n:
        parsed = parse_escape_at(text, i)
        if parsed is None:
            i += 1
            continue

        token, next_i = parsed
        if last < i:
            segments.append((False, text[last:i]))
        segments.append((True, token))
        i = next_i
        last = i

    if last < n:
        segments.append((False, text[last:]))

    if not segments:
        return [(False, text)]
    return segments


def split_by_brackets_level3(text):
    """Deprecated compatibility alias.

    CR-005 removes nested square-bracket parsing; this helper now delegates
    to the simple escape splitter and returns only segment text.
    """
    return [seg for _, seg in split_by_escape_segments(text)]