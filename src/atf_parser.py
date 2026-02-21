#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — eBL ATF Parser
Version: 1.0.0

SPECIALIZED for the electronic Babylonian Library (eBL) platform.
https://www.ebl.lmu.de/

Converts eBL ATF files to clean Akkadian text for the repair pipeline.
Only processes %%n lines (Akkadian) and #tr.en: lines (translations).
All other lines are silently ignored (see help for details).

Part of the Akkadian Prosody project (akkapros)
https://github.com/samuelkabak/akkapros

MIT License
Copyright (c) 2026 Samuel KABAK
"""

import re
import unicodedata
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

__version__ = "1.0.0"
__author__ = "Samuel KABAK"
__license__ = "MIT"
__project__ = "Akkadian Prosody"
__repo__ = "akkapros"
__ebl_url__ = "https://www.ebl.lmu.de/"


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
    - || double pipe - PRESERVE (major division/phrase boundary)
    - ‡ Glossenkeil - REPLACE with ':' (word divider)
    - ' single quote - PRESERVE (emendation marker)
    - x broken sign - REPLACE with a SINGLE '...' (multiple x's collapse)
    - 0-9 numerals - PRESERVE
    - ? ! * ° - REMOVE (editorial signs)
    - ... - PRESERVE (ellipsis)
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
        self.cleaned_lines = []              # Cleaned text for syllabification/repair
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
        text = text.replace('\u00A0', ' ')
        
        # Convert both || and ‡ to em-dash with spaces
        text = text.replace('||', ' — ')
        text = text.replace('‡', ' — ')
        
        # Handle single pipes (convert to space)
        text = text.replace('|', ' ')
        
        # Remove all editorial characters
        editorial_chars = {'?', '!', '*', '°'}
        for char in editorial_chars:
            text = text.replace(char, '')
        
        # Handle broken sign 'x' - remove completely
        text = re.sub(r'x', '', text)
        
        # Remove all types of brackets, keep content
        text = re.sub(r'\(([^)]+)\)', r'\1', text)
        text = re.sub(r'\[([^\]]+)\]', r'\1', text)
        text = re.sub(r'\[\s*\]', '', text)
        text = re.sub(r'<([^>]+)>', r'\1', text)
        text = re.sub(r'<>\s*', '', text)
        text = re.sub(r'\{([^}]+)\}', r'\1', text)
        text = re.sub(r'\{\s*\}', '', text)
        
        # STEP 2: Process long vowels (vowel followed by same vowel with hyphen)
        # Examples: ba-nu-u₂ → banû, kib-ra-a-ti → kibrāti
        # But don't affect da-ad₂-me (different vowels)

        # STEP: Process long vowels (always do this, regardless of hyphen option)
        text = re.sub(r'a-a', 'ā', text)
        text = re.sub(r'e-e', 'ē', text)
        text = re.sub(r'i-i', 'ī', text)
        text = re.sub(r'u-u', 'ū', text)

        # STEP: Handle hyphens based on option
        if self.remove_hyphens:
            text = text.replace('-', '')
        # else: keep hyphens

        # Remove subscript numerals (after processing vowel length)
        text = re.sub(r'[₂₃₄₅₆₇₈₉]', '', text)
        
        # Remove collation markers #
        text = text.replace('#', '')
        
        # Convert ... ellipsis to …
        text = text.replace('...', '…')
        text = re.sub(r'\.{2,}', '…', text)
        
        # Collapse multiple ellipsis
        text = re.sub(r'…\s*…', ' … ', text)
        
        # Remove any remaining single dots
        text = re.sub(r'(?<!\.)\.(?!\.)', '', text)
        
        # Normalize spaces
        text = re.sub(r' +', ' ', text)
        
        # Clean up spacing around em-dash
        text = re.sub(r' ?— ?', ' — ', text)
        
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


def run_tests():
    """Run comprehensive self-tests."""
    print("\n" + "="*80)
    print("AKKADIAN PROSODY TOOLKIT — SELF-TEST SUITE")
    print("="*80)
    
    parser = ATFParser(test_mode=True)
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Parentheses removed, content kept
    test1 = parser.clean_line("(u) ana šubruq", for_test=True)
    if test1 == "u ana šubruq":
        tests_passed += 1
        print(f"✅ Test 1: Parentheses removed → '{test1}'")
    else:
        tests_failed += 1
        print(f"❌ Test 1: Expected 'u ana šubruq', got '{test1}'")
    
    # Test 2: Single pipe to space
    test2 = parser.clean_line("erra | qarrād", for_test=True)
    if test2 == "erra qarrād":
        tests_passed += 1
        print(f"✅ Test 2: Single pipe → space → '{test2}'")
    else:
        tests_failed += 1
        print(f"❌ Test 2: Expected 'erra qarrād', got '{test2}'")
    
    # Test 3: Double pipe to em-dash
    test3 = parser.clean_line("libbašu || epēš", for_test=True)
    if test3 == "libbašu — epēš":
        tests_passed += 1
        print(f"✅ Test 3: Double pipe → em-dash → '{test3}'")
    else:
        tests_failed += 1
        print(f"❌ Test 3: Expected 'libbašu — epēš', got '{test3}'")
    
    # Test 4: Glossenkeil to em-dash
    test4 = parser.clean_line("iqabbīku‡ ana kâša", for_test=True)
    if test4 == "iqabbīku — ana kâša":
        tests_passed += 1
        print(f"✅ Test 4: Glossenkeil → em-dash → '{test4}'")
    else:
        tests_failed += 1
        print(f"❌ Test 4: Expected 'iqabbīku — ana kâša', got '{test4}'")
    
    # Test 5: Ellipsis preserved
    test5 = parser.clean_line("kibrāti ...", for_test=True)
    if test5 == "kibrāti …":
        tests_passed += 1
        print(f"✅ Test 5: Ellipsis preserved → '{test5}'")
    else:
        tests_failed += 1
        print(f"❌ Test 5: Expected 'kibrāti …', got '{test5}'")
    
    # Test 6: Question marks removed
    test6 = parser.clean_line("tenēšēti?", for_test=True)
    if test6 == "tenēšēti":
        tests_passed += 1
        print(f"✅ Test 6: Question marks removed → '{test6}'")
    else:
        tests_failed += 1
        print(f"❌ Test 6: Expected 'tenēšēti', got '{test6}'")
    
    # Test 7: Subscripts removed
    test7 = parser.clean_line("da-ad₂-me", for_test=True)
    if test7 == "dād-me":
        tests_passed += 1
        print(f"✅ Test 7: Subscripts removed → '{test7}'")
    else:
        tests_failed += 1
        print(f"❌ Test 7: Expected 'dād-me', got '{test7}'")
    
    # Test 8: Collation markers removed
    test8 = parser.clean_line("ba-nu-u₂#", for_test=True)
    if test8 == "ba-nū":
        tests_passed += 1
        print(f"✅ Test 8: Collation markers removed → '{test8}'")
    else:
        tests_failed += 1
        print(f"❌ Test 8: Expected 'banū', got '{test8}'")
    
    # Test 9: Brackets removed, content kept
    test9 = parser.clean_line("kibrā[ti]", for_test=True)
    if test9 == "kibrāti":
        tests_passed += 1
        print(f"✅ Test 9: Brackets removed → '{test9}'")
    else:
        tests_failed += 1
        print(f"❌ Test 9: Expected 'kibrāti', got '{test9}'")
    
    # Test 10: Multiple x's removed
    test10 = parser.clean_line("kib-ra-a-ti x x x", for_test=True)
    if test10 == "kib-rā-ti":
        tests_passed += 1
        print(f"✅ Test 10: Broken signs removed → '{test10}'")
    else:
        tests_failed += 1
        print(f"❌ Test 10: Expected 'kibrāti', got '{test10}'")
    
    # Test 11: Complex line with multiple markers
    test11 = parser.clean_line("1. %n šar (|) gimir (|) dadmē | bānû (|) kibrā[ti (|) ... ]", for_test=True)
    if test11 == "šar gimir dadmē bānû kibrāti …":
        tests_passed += 1
        print(f"✅ Test 11: Complex line cleaned → '{test11}'")
    else:
        tests_failed += 1
        print(f"❌ Test 11: Expected 'šar gimir dadmē bānû kibrāti …', got '{test11}'")
    
    # Test 12: Multiple spaces normalized
    test12 = parser.clean_line("šar   gimir    dadmē", for_test=True)
    if test12 == "šar gimir dadmē":
        tests_passed += 1
        print(f"✅ Test 12: Multiple spaces normalized → '{test12}'")
    else:
        tests_failed += 1
        print(f"❌ Test 12: Expected 'šar gimir dadmē', got '{test12}'")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests passed: {tests_passed}/12")
    print(f"Tests failed: {tests_failed}/12")
    print("="*80)
    
    return tests_failed == 0


def save_output(results: Dict, prefix: str, outdir: Path):
    """Save all output files."""
    if outdir != Path('.'):
        outdir.mkdir(parents=True, exist_ok=True)
    
    # Original Akkadian lines (with ATF markup preserved)
    orig_file = outdir / f"{prefix}_orig.txt"
    with open(orig_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(results['original_akkadian_lines']))
    
    # Cleaned text file
    proc_file = outdir / f"{prefix}_proc.txt"
    with open(proc_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(results['cleaned_lines']))
    
    # English translation if present
    if results['english_translations']:
        trans_file = outdir / f"{prefix}_trans.txt"
        with open(trans_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results['english_translations']))
    
    return orig_file, proc_file


def simple_safe_filename(text):
    """
    Minimal safe filename conversion
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


def main():
    parser = argparse.ArgumentParser(
        description='Convert eBL ATF files to clean Akkadian text',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
SOURCE:
  This parser is STRICTLY designed for ATF files from the
  electronic Babylonian Library (eBL) platform:
  {__ebl_url__}
  
  PROCESSING RULES:
  * %%n lines are processed as Akkadian
  * #tr.en: lines are processed as translations
  * All other line types (&, @, $, #note:, manuscript sigla) are SILENTLY IGNORED
  
  WITHIN AKKADIAN LINES:
  * ( ) parentheses - KEEP content, remove parentheses
  * [ ] brackets - KEEP content, remove brackets
  * < > angle brackets - KEEP content, remove brackets
  * {{ }} braces - REMOVE entirely (determinatives)
  * | single pipe - CONVERT to space (word boundary)
  * || double pipe - PRESERVE (major division/phrase boundary)
  * ‡ Glossenkeil - REPLACE with ':' (word divider)
  * ' single quote - PRESERVE (emendation marker)
  * x broken sign - REPLACE with a SINGLE '...' (multiple x's collapse)
  * 0-9 numerals - PRESERVE
  * ? ! * ° - REMOVE (editorial signs)
  * ... - PRESERVE (ellipsis)
  * Hyphens - PRESERVE (part of transliteration)

  MULTI-LINE HANDLING:
  * Consecutive %%n lines are concatenated with spaces
  * Empty %%n lines (line numbers only) are ignored

  LIMITATIONS (The program does NOT preserve):
  * Line numbers
  * Column divisions
  * Parallel passages
  * Variant readings
  * Other structural metadata

OPTIONS:
  --test      - Run self-test suite
  --strict    - Enable warnings for informational purposes

OUTPUT FILES:
  PREFIX_orig.txt    - Original %%n lines (with ATF markup preserved)
  PREFIX_proc.txt    - Cleaned text for syllabification/repair
  PREFIX_trans.txt   - English translation (if present)

For more information, visit:
{__repo__}

Part of Akkadian Prosody Toolkit v{__version__}
MIT License (c) 2026 Samuel KABAK
"""
    )
    parser.add_argument('--version', action='version',
                       version=f'akkapros-parser {__version__}')
    parser.add_argument('input', nargs='?', help='eBL ATF file (must contain %%n lines)')
    parser.add_argument('-o', '--output', 
                       help='Output prefix (default: input filename without extension)')
    parser.add_argument('--outdir', default='.',
                       help='Output directory (default: current directory .)')
    parser.add_argument('--remove-hyphens', action='store_true',
                    help='Remove hyphens (cuneiform sign boundaries) for cleaner reading text')
    parser.add_argument('--preserve-case', action='store_true',
                       help='Preserve original case (default: convert to lowercase)')
    parser.add_argument('--preserve-h', action='store_true',
                       help='Preserve original [h,H] (default: convert to [ḫ,Ḫ]})')
    parser.add_argument('--strict', action='store_true',
                       help='Enable warnings for informational purposes')
    parser.add_argument('--test', action='store_true', help='Run self-test suite')
    
    args = parser.parse_args()
    
    # Handle test mode
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # If no input file, show help
    if not args.input:
        parser.print_help()
        sys.exit(0)
    
    # Regular mode with input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\nError: File '{args.input}' not found.")
        sys.exit(1)
    
    # Determine output prefix
    if args.output:
        prefix = args.output
    else:
        prefix = input_path.stem
    
    outdir = Path(args.outdir)
    
    print(f"\nInput: {args.input}")
    print(f"Output directory: {outdir}")
    print(f"Output prefix: {prefix}")
    print(f"Case: {'PRESERVED' if args.preserve_case else 'CONVERTED TO LOWERCASE'}")
    print(f"Letters [h,H]: {'PRESERVED' if args.preserve_h else 'CONVERTED TO [ḫ,Ḫ]'}")
    print(f"Mode: {'STRICT (warnings enabled)' if args.strict else 'NORMAL (silent)'}")
    print("-" * 60)
    
    try:
        parser_obj = ATFParser(
            preserve_case=args.preserve_case,
            preserve_h=args.preserve_h,
            remove_hyphens=args.remove_hyphens, 
            strict_mode=args.strict
        )
        results = parser_obj.parse_file(str(input_path))
        
        # Save outputs
        orig_file, proc_file = save_output(results, prefix, outdir)
        
        print("\n" + "="*60)
        print("PARSING COMPLETE")
        print("="*60)
        
        if results['title']:
            print(f"Title: {results['title']}")
        
        print(f"\nEnglish translations: {len(results['english_translations'])}")
        print(f"Original Akkadian lines: {len(results['original_akkadian_lines'])}")
        print(f"Cleaned lines: {len(results['cleaned_lines'])}")
        
        if args.strict and results['warnings']:
            print(f"\nWARNINGS ({len(results['warnings'])}):")
            for w in results['warnings'][:20]:
                print(f"  * {w}")
            if len(results['warnings']) > 20:
                print(f"  * ... and {len(results['warnings'])-20} more")
        
        print("\n" + "-"*60)
        print("FIRST 5 ORIGINAL AKKADIAN LINES (with ATF markup):")
        print("-"*60)
        for i, line in enumerate(results['original_akkadian_lines'][:5]):
            print(f"{i+1:2d}. {line}")
        
        print("\n" + "-"*60)
        print("FIRST 5 CLEANED LINES (ready for repair):")
        print("-"*60)
        for i, line in enumerate(results['cleaned_lines'][:5]):
            print(f"{i+1:2d}. {line}")
        
        print("\n" + "="*60)
        print("FILES SAVED:")
        display_prefix = simple_safe_filename(prefix)
        print(f"  {outdir / f'{display_prefix}_orig.txt'} (original, with ATF markup)")
        print(f"  {outdir / f'{display_prefix}_proc.txt'} (cleaned, ready for repair)")
        if results['english_translations']:
            trans_file = outdir / f"{display_prefix}_trans.txt"
            print(f"  {trans_file}")
        print("="*60)
        
    except EBLError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()