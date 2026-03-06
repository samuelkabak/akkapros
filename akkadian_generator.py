#!/usr/bin/env python3
"""Convenience CLI wrapper for the Akkadian diphone script generator."""

import os
import sys


# Ensure src-layout imports work when run from repository root.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from akkarpos.cli.mbrolatortext import main


if __name__ == "__main__":
    main()
