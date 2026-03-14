"""
Akkadian Prosody Toolkit — Library API

This package exposes the core functionality as importable modules.
"""

from .atfparse import ATFParser, run_tests, EBLError, TestResult, TestCase

__version__ = "1.0.1"
__all__ = [
    "ATFParser",
    "run_tests",
    "EBLError",
    "TestResult",
    "TestCase",
]
