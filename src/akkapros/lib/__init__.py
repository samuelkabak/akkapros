"""
Akkadian Prosody Toolkit — Library API

This package exposes the core functionality as importable modules.
"""

from akkapros import __version__

from .atfparse import ATFParser, run_tests, EBLError, TestResult, TestCase

__all__ = [
    "ATFParser",
    "run_tests",
    "EBLError",
    "TestResult",
    "TestCase",
]
