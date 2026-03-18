#!/usr/bin/env python3
"""Ensure POSIX script files end with a newline (LF) without altering encodings.

Behavior:
- Scans the repo for files that are UTF-8 text and either have a shebang line
  (starting with #!) that mentions 'sh' or have a '.sh' extension.
- If the file does not end with LF (0x0A), appends a single LF byte.
- Verifies that the post-edit content equals original + LF (no other changes).

This script works in binary mode to avoid re-encoding and preserves bytes.
"""
from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIRS = {'.git', 'venv', '__pycache__'}


def is_text_utf8(b: bytes) -> bool:
    try:
        b.decode('utf-8')
        return True
    except Exception:
        return False


def has_shebang_sh(b: bytes) -> bool:
    if not b.startswith(b'#!'):
        return False
    firstline = b.splitlines()[0].lower()
    return b'sh' in firstline or b'bash' in firstline


def should_fix(path: Path, data: bytes) -> bool:
    if path.suffix.lower() == '.sh':
        return True
    return has_shebang_sh(data)


def main():
    modified = []
    problems = []
    for p in ROOT.rglob('*'):
        if p.is_dir():
            if p.name in EXCLUDE_DIRS:
                # don't descend into excluded dirs
                try:
                    for _ in p.iterdir():
                        pass
                except Exception:
                    pass
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        # skip binary-ish files by size/extension heuristics
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if not data:
            continue
        if not is_text_utf8(data):
            continue
        if not should_fix(p, data):
            continue
        if data.endswith(b'\n'):
            continue
        # append single LF byte
        try:
            with open(p, 'ab') as f:
                f.write(b'\n')
        except Exception as e:
            problems.append((p, str(e)))
            continue
        new_data = p.read_bytes()
        if new_data != data + b'\n':
            problems.append((p, 'content changed beyond appended LF'))
            # attempt to restore original
            try:
                p.write_bytes(data)
            except Exception:
                pass
        else:
            modified.append(p.relative_to(ROOT))

    print('\nPOSIX newline enforcement summary:')
    if modified:
        print(f'  Modified {len(modified)} file(s):')
        for m in modified:
            print(f'   - {m}')
    else:
        print('  No files needed modification.')

    if problems:
        print('\nProblems encountered:')
        for p, msg in problems:
            print(f'   - {p}: {msg}')
        sys.exit(2)

    print('\nVerification: all changes are single trailing LF bytes.')


if __name__ == '__main__':
    main()
