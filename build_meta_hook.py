"""PEP 517 build-backend wrapper that syncs docs before delegating to setuptools.build_meta.

Place this module in the project root and set `build-backend = "build_meta_hook"`
in `pyproject.toml`. It will run `scripts/sync_docs.py` prior to building sdist/wheel
so the packaged wheel includes `src/akkapros/docs/` copied from the repository `docs/`.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
import os
from typing import Any

_delegate = importlib.import_module("setuptools.build_meta")


def _run_sync() -> None:
    # Run the Python sync script if present; ignore errors but surface failures.
    here = os.path.dirname(__file__)
    script = os.path.join(here, "scripts", "sync_docs.py")
    if os.path.exists(script):
        try:
            subprocess.check_call([sys.executable, script])
        except subprocess.CalledProcessError as e:
            raise


def _wrap(fn_name: str):
    def _wrapped(*args: Any, **kwargs: Any):
        _run_sync()
        fn = getattr(_delegate, fn_name)
        return fn(*args, **kwargs)

    return _wrapped


# Wrap common PEP 517 functions by delegating after running sync.
build_wheel = _wrap("build_wheel")
build_sdist = _wrap("build_sdist")
prepare_metadata_for_build_wheel = _wrap("prepare_metadata_for_build_wheel")
get_requires_for_build_wheel = _wrap("get_requires_for_build_wheel")
get_requires_for_build_sdist = _wrap("get_requires_for_build_sdist")
