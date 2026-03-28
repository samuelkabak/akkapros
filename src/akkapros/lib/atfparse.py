#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — eBL ATF Parser (Library)

LIBRARY MODULE: Core ATF parsing functionality

This module contains the core ATF parsing logic, independent of CLI.
Use this module when you need to process ATF files programmatically.

For CLI usage, see atfparser.py in the cli package.

Part of the Akkadian Prosody project (akkapros)
https://github.com/samuelkabak/akkapros

MIT License
Copyright (c) 2026 Samuel KABAK
"""

import logging
import re
import unicodedata
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from akkapros.lib.utils import get_logger_with_fallback, run_simple_selftest_suite

__author__ = "Samuel KABAK"
__license__ = "MIT"
__project__ = "Akkadian Prosody"
__repo__ = "akkapros"

HYPHEN = '-'

class EBLError(Exception):
    """Exception raised for eBL-specific parsing errors."""
    pass


class TestResult(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️ WARN"


@dataclass
class TestCase:
    name: str
    input_line: str
    expected_output: str
    expected_warnings: List[str]
    result: TestResult = TestResult.PASS
    actual_output: str = ""
    actual_warnings: List[str] = None


class ATFParser:
    """
    Parser for eBL ATF files following our established spec.
    
    Only processes:
    - %%n lines (Akkadian text)
    - #tr.en: lines (English translations)
    
    All other lines (&, @, $, #note:, manuscript sigla) are silently ignored.
    
    Within Akkadian lines:
    - ( ) parentheses - KEEP content, remove parentheses
    - [ ] brackets - KEEP content, remove brackets
    - < > angle brackets - KEEP content, remove brackets
    - { } braces - REMOVE entirely (determinatives)
    - | single pipe - CONVERT to space (word boundary)
    - || double pipe - REPLACE with ':' (major division/phrase boundary)
    - ‡ Glossenkeil - REPLACE with ':' (phrase divider)
    - ' single quote - PRESERVE (emendation marker)
    - x broken sign - REPLACE with a SINGLE '…' (multiple x's collapse)
    - 0-9 numerals - PRESERVE
    - ? ! * ° - REMOVE (editorial signs)
    - … - PRESERVE (ellipsis)
    - Hyphens - PRESERVE (part of transliteration)
    """
    
    # Complete set of editorial characters to remove
    EDITORIAL_CHARS = {
        '?',  # question mark - uncertain reading
        '!',  # exclamation - emendation
        '*',  # asterisk - reconstructed form
        '°',  # degree sign - sign value uncertain
    }
    
    def __init__(self, preserve_case: bool = False, preserve_h: bool = False, 
             remove_hyphens: bool = False, strict_mode: bool = False, test_mode: bool = False):
        self.preserve_case = preserve_case
        self.preserve_h = preserve_h
        self.remove_hyphens = remove_hyphens  
        self.strict_mode = strict_mode
        self.test_mode = test_mode
        self.metadata = {}
        self.title = None
        self.english_translations = []
        self.original_akkadian_lines = []   # Raw %n lines (with %n removed)
        self.cleaned_lines = []              # Cleaned text for syllabification/accentuation
        self.warnings = []
        self.warning_counts = {
            'determinative': False,
            'numeral': False,
            'broken_sign': False,
            'multiline': False
        }
        self.test_cases = []

    def _warn(self, message: str, category: str = None):
        """Add a warning message (only used in strict mode or test mode)."""
        self.warnings.append(message)
        if self.strict_mode and not self.test_mode:
            raise EBLError(f"STRICT MODE: {message}")

    def _warn_once(self, message: str, category: str):
        """Add a warning only once per category (only used in strict mode)."""
        if self.strict_mode and not self.warning_counts.get(category, False):
            self.warning_counts[category] = True
            self._warn(message)

    def clean_line(self, line: str, for_test: bool = False) -> str:
        """
        Clean a line of Akkadian text for reading aloud.
        Output guarantees proper spacing around … and :.
        """
        original = line
        text = line
        
        # STEP 1: Remove line numbers and %n markers
        text = re.sub(r'^\d+\.\s*%n\s*', '', text)
        text = re.sub(r'^\d+\.\s*', '', text)
        
        # Convert to lowercase unless case preservation is requested
        if not self.preserve_case:
            text = text.lower()
        
        # Convert h unless h preservation is requested
        if not self.preserve_h:
            text = text.replace('h', 'ḫ').replace('H', 'Ḫ')
        
        # Replace NBSP with normal space
        text = text.replace(' ', ' ')
        
        # Replace tabs with spaces
        text = text.replace('\t', '  ')
        
        # Convert both || and ‡ to colon phrase separator (no spaces yet)
        text = text.replace('||', ':')
        text = text.replace('‡', ':')

        # Normalize editorial dash separators to colon phrase separator.
        text = text.replace('—', ':')
        text = text.replace('–', ':')
        
        # Handle single pipes (convert to space)
        text = text.replace('|', ' ')
        
        # Remove all editorial characters
        editorial_chars = {'?', '!', '*', '°'}
        for char in editorial_chars:
            text = text.replace(char, '')
        
        # Handle broken sign x/xx/... -> one ellipsis marker.
        # Collapse repeated broken-sign tokens (e.g., x x x) to a single ellipsis.
        text = re.sub(r'\bx+\b(?:\s+\bx+\b)+', '…', text)
        text = re.sub(r'\bx+\b', '…', text)
        
        # Remove all types of brackets, keep content
        text = re.sub(r'\(([^)]+)\)', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]', r'\1', text)
        text = re.sub(r'\[\s*\]', '', text)
        text = re.sub(r'<([^>]+)>', r'\1', text)
        text = re.sub(r'<>\s*', '', text)
        text = re.sub(r'\{([^}]+)\}', r'\1', text)
        text = re.sub(r'\{\s*\}', '', text)
        
        # Process long vowels
        text = re.sub(r'a-a', 'ā', text)
        text = re.sub(r'e-e', 'ē', text)
        text = re.sub(r'i-i', 'ī', text)
        text = re.sub(r'u-u', 'ū', text)
        
        # Handle hyphens based on option
        if self.remove_hyphens:
            text = text.replace(HYPHEN, '')
        
        # Remove subscript numerals
        text = re.sub(r'[₂₃₄₅₆₇₈₉]', '', text)
        
        # Remove collation markers
        text = text.replace('#', '')
        
        # ===== PUNCTUATION SPACING GUARANTEES =====
        
        # Convert ... ellipsis to …
        text = text.replace('...', '…')
        text = re.sub(r'\.{2,}', '…', text)
        
        # ALWAYS add spaces around … and :
        text = re.sub(r'…', ' … ', text)
        text = re.sub(r':', ' : ', text)
        
        # Normalize spaces (collapse multiple spaces)
        text = re.sub(r' +', ' ', text)
        
        # Trim trailing spaces only (preserve leading)
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)
        
        result = text.strip()
        
        # Store test case if in test mode
        if for_test:
            warnings_snapshot = self.warnings.copy()
            self.test_cases.append(TestCase(
                name=f"Test {len(self.test_cases)+1}",
                input_line=original,
                expected_output=result,
                expected_warnings=[],
                actual_output=result,
                actual_warnings=warnings_snapshot
            ))
        
        return result


    def parse_file(self, filename: str) -> Dict:
        """
        Parse an eBL ATF file - only processes %n lines and #tr.en: lines.
        All other lines are silently ignored.
        """
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.metadata = {}
        self.title = None
        self.english_translations = []
        self.original_akkadian_lines = []
        self.cleaned_lines = []
        self.warnings = []
        self.warning_counts = {
            'determinative': False,
            'numeral': False,
            'broken_sign': False,
            'multiline': False
        }
        
        line_number = 0
        found_akkadian = False
        
        for line in lines:
            line = line.rstrip()
            line_number += 1
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # &-lines: Extract title (silently)
            if line.startswith('&'):
                self._parse_header(line)
                continue
            
            # #tr.en: lines - extract translations
            if line.startswith('#tr.en:'):
                trans = line.replace('#tr.en:', '').strip()
                if trans:
                    self.english_translations.append(trans)
                continue
            
            # %n lines - Akkadian text
            if '%n' in line:
                found_akkadian = True
                # Extract content after %n
                match = re.search(r'%n\s+(.*?)(?:\s*#|$)', line)
                if match:
                    akkadian_line = match.group(1).strip()
                    
                    # Store original (with ATF markup preserved)
                    self.original_akkadian_lines.append(akkadian_line)
                    
                    # Clean for processing according to spec
                    cleaned = self.clean_line(akkadian_line)

                    if cleaned:
                        self.cleaned_lines.append(cleaned)
                continue
            
            # All other lines are silently ignored
        
        if not found_akkadian:
            raise EBLError("No %n lines found in file")
        return {
            'metadata': self.metadata,
            'title': self.title,
            'english_translations': self.english_translations,
            'original_akkadian_lines': self.original_akkadian_lines,
            'cleaned_lines': self.cleaned_lines,
            'warnings': self.warnings,
        }

    def _parse_header(self, line: str):
        """Parse &X000001 = title format."""
        match = re.match(r'&([^\s=]+)\s*=\s*(.+)', line)
        if match:
            self.metadata['id'] = match.group(1).strip()
            self.title = match.group(2).strip()


def run_tests() -> bool:
    """Run comprehensive self-tests. Returns True if all pass, False otherwise."""
    parser = ATFParser(test_mode=True)
    logger = get_logger_with_fallback(__name__)
    suites = [
        ('Parentheses content kept', lambda: parser.clean_line('(u) ana šubruq', for_test=True) == 'u ana šubruq'),
        ('Single pipe to space', lambda: parser.clean_line('erra | qarrād', for_test=True) == 'erra qarrād'),
        ('Double pipe to colon', lambda: parser.clean_line('libbašu || epēš', for_test=True) == 'libbašu : epēš'),
        ('Glossenkeil to colon', lambda: parser.clean_line('iqabbīku‡ ana kâša', for_test=True) == 'iqabbīku : ana kâša'),
        ('Ellipsis preserved', lambda: parser.clean_line('kibrāti ...', for_test=True) == 'kibrāti …'),
        ('Question marks removed', lambda: parser.clean_line('tenēšēti?', for_test=True) == 'tenēšēti'),
        ('Subscripts removed', lambda: parser.clean_line('da-ad₂-me', for_test=True) == 'dād-me'),
        ('Collation markers removed', lambda: parser.clean_line('ba-nu-u₂#', for_test=True) == 'ba-nū'),
        ('Brackets content kept', lambda: parser.clean_line('kibrā[ti]', for_test=True) == 'kibrāti'),
        ('Broken signs collapse', lambda: parser.clean_line('kib-ra-a-ti x x x', for_test=True) == 'kib-rā-ti …'),
        (
            'Complex line cleanup',
            lambda: parser.clean_line(
                '1. %n šar (|) gimir (|) dadmē | bānû (|) kibrā[ti (|) ... ]',
                for_test=True,
            ) == 'šar gimir dadmē bānû kibrāti …',
        ),
        ('Multiple spaces normalized', lambda: parser.clean_line('šar   gimir    dadmē', for_test=True) == 'šar gimir dadmē'),
    ]
    return run_simple_selftest_suite(logger, 'Atfparse', suites)

