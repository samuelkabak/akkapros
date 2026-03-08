#!/usr/bin/env python3
"""Shared CLI utilities for akkapros command-line entrypoints."""

from __future__ import annotations

import argparse
from typing import Any


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
