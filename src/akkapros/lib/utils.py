#!/usr/bin/env python3
"""
Utility helpers shared across akkapros modules.

This file contains small, generic functions that are used in multiple
command‑line tools.  The goal is to avoid duplication and provide a
single place for commonly useful routines.  By default there are no
external dependencies beyond the Python standard library.

Currently defined:

* ``simple_safe_filename`` – convert arbitrary text into a filesystem-
  safe filename fragment.

The module also provides a small test harness for its routines; running
``utils.run_tests()`` should return ``True`` when everything is working.
"""

import argparse
import re
import unicodedata
from typing import Any

from akkapros import get_version_display

__version__ = "1.0.1"
__author__ = "Samuel KABAK"
__license__ = "MIT"


class RawDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Help formatter that keeps epilog formatting and always shows defaults."""


def print_startup_banner(program_title: str, version: str, args: argparse.Namespace) -> None:
    """Print a stable startup banner with effective runtime parameters."""
    print("=" * 78)
    print(program_title)
    print(f"Version: {version}")
    print("Running with:")

    for key in sorted(vars(args)):
        value: Any = getattr(args, key)
        print(f"  {key} = {value!r}")

    print("=" * 78)


def add_standard_version_argument(parser: argparse.ArgumentParser, tool_name: str) -> None:
    """Add a standardized multi-line --version/-v option to a CLI parser."""
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=get_version_display(tool_name),
    )


def simple_safe_filename(text: str) -> str:
    """Return a minimal filename-safe version of ``text``.

    The function performs the same sequence of operations that were
    previously duplicated across several CLI modules:

    1. Normalize to ``NFKD`` and strip accent marks.
    2. Replace characters that are illegal in filenames (``<>:"/\\|?*``)
       or whitespace with underscores.
    3. Remove any other non-word characters, keeping ``-`` and ``.``.
    4. Collapse consecutive underscores, then strip leading or trailing
       ``._-`` characters.
    5. Guarantee a non-empty result by returning ``"unnamed"`` if the
       cleaned string is empty.

    >>> simple_safe_filename('foo/bar baz?')
    'foo_bar_baz'
    >>> simple_safe_filename('')
    'unnamed'
    """
    if not text:
        return "unnamed"

    # Remove accents
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')

    # Replace invalid chars and spaces with underscores
    text = re.sub(r'[<>:"/\\|?*\s]', '_', text)

    # Keep only safe characters
    text = re.sub(r'[^\w\-\.]', '_', text)

    # Clean up
    text = re.sub(r'_+', '_', text)
    text = text.strip('._-')

    return text or "unnamed"


def run_tests() -> bool:
    """Simple self-test suite.

    The tests here are deliberately minimal; they exist primarily to
    ensure that the behaviour of ``simple_safe_filename`` is stable.
    Calling ``run_tests`` from a higher‑level test harness (for example,
    ``parse.run_tests``) is sufficient for our purposes.
    """
    passed = 0
    failed = 0

    # basic conversion
    if simple_safe_filename('foo/bar baz?') == 'foo_bar_baz':
        passed += 1
    else:
        failed += 1

    # empty string returns placeholder
    if simple_safe_filename('') == 'unnamed':
        passed += 1
    else:
        failed += 1

    print(f"utils tests: {passed} passed, {failed} failed")
    return failed == 0
