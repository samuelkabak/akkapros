#!/usr/bin/env python3
"""Akkadian phoneprep CLI wrapper.

This module is intentionally thin and delegates implementation to
``akkapros.lib.phoneprep``.
"""

import sys
from pathlib import Path

# If the script is executed directly, the package root may not be on sys.path.
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from akkapros.lib.phoneprep import main


if __name__ == "__main__":
    main()
