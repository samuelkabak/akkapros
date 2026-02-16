#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Syllabifier
Version: 1.0.0

Converts Akkadian text to syllabified format with:
- Pipes | at word ENDINGS (no spaces after pipes)
- Dots . between syllables
- Non-Akkadian text in [brackets] with ALL spaces preserved inside brackets
- Spaces between words are automatically filtered out (not bracketed)
- Mixed words like "d[o]ne" handled correctly
- Fault-tolerant: accepts 'h' for ḫ (both are valid)
- Output: {prefix}_syl.txt (like atf_parser)

SPACE PRESERVATION RULE:
  ALL spaces around punctuation are preserved INSIDE the brackets.
  Standalone spaces between words are discarded (they're implicit in pipes).
  This ensures perfect restoration of original text after repair.
"""

import sys
import re
import unicodedata
from pathlib import Path

__version__ = "1.0.0"


# ------------------------------------------------------------
# Phonetic inventory — Akkadian core
# ------------------------------------------------------------
LONG = set('āēīūâêîû')
SHORT = set('aeiu')
V = LONG | SHORT

# Core Akkadian consonants — 'd' is already here!
C = set('bdgkpṭqṣszšlmnrḥḫʿʾwyt')

# Foreign characters that may appear (only 'h' for ḫ alternative)
FOREIGN = set('')

# Complete set for word detection
def get_akloi(extra=''):
    """Return the set of characters considered as Akkadian letters."""
    result = V | C | {'-'} | FOREIGN
    for c in extra:
        result.add(c)
    return result

# Initialize with default
AKLOI = get_akloi()


def is_akkadian(c, extra=''):
    """Return True if character is an Akkadian letter."""
    if extra:
        return c in (V | C | {'-'} | FOREIGN | set(extra))
    return c in AKLOI


def is_vowel(c):
    return c in V


def syllabify_word(word):
    """Syllabify an Akkadian word using the validated algorithm."""
    segs = [c for c in word if c in V or c in C or c in FOREIGN]
    if not segs:
        return word
    
    # If word has no vowels, return as is (for single consonants like 'd')
    if not any(c in V for c in segs):
        return word
    
    syllables = []
    i, n = 0, len(segs)
    first = True
    
    while i < n:
        if first and segs[i] in V:
            first = False
            syl = [segs[i]]
            i += 1
            if i < n and segs[i] in (C | FOREIGN) and (i+1 >= n or segs[i+1] in (C | FOREIGN)):
                syl.append(segs[i])
                i += 1
            syllables.append(''.join(syl))
            continue
        
        first = False
        onset = []
        while i < n and segs[i] in (C | FOREIGN):
            onset.append(segs[i])
            i += 1
        
        if i < n and segs[i] in V:
            syl = onset + [segs[i]]
            i += 1
            if i < n and segs[i] in (C | FOREIGN):
                if i+1 >= n or segs[i+1] in (C | FOREIGN):
                    syl.append(segs[i])
                    i += 1
            syllables.append(''.join(syl))
    
    return '.'.join(syllables)


def tokenize_line(line, extra=''):
    """
    Split line into tokens correctly.
    
    Rules:
    - Multi-character punctuation (||, ...) detected first
    - Akkadian letters → word tokens
    - Non-Akkadian sequences become punctuation tokens
    """
    tokens = []
    i = 0
    n = len(line)
    
    while i < n:
        # Check for double pipe
        if i+1 < n and line[i] == '|' and line[i+1] == '|':
            # Look ahead to see if there's a space after
            if i+2 < n and line[i+2] == ' ':
                tokens.append(('punct', '|| '))
                i += 3
            else:
                tokens.append(('punct', '||'))
                i += 2
            continue
        
        # Check for ellipsis
        if i+2 < n and line[i] == '.' and line[i+1] == '.' and line[i+2] == '.':
            # Look ahead to see if there's a space after
            if i+3 < n and line[i+3] == ' ':
                tokens.append(('punct', '... '))
                i += 4
            else:
                tokens.append(('punct', '...'))
                i += 3
            continue
        
        # Check for double colon
        if i+1 < n and line[i] == ':' and line[i+1] == ':':
            if i+2 < n and line[i+2] == ' ':
                tokens.append(('punct', ':: '))
                i += 3
            else:
                tokens.append(('punct', '::'))
                i += 2
            continue
        
        # Check for Akkadian word
        if is_akkadian(line[i], extra):
            start = i
            while i < n and is_akkadian(line[i], extra):
                i += 1
            tokens.append(('word', line[start:i]))
            continue
        
        # Check for single punctuation with space after
        if line[i] in ',.;:?!' and i+1 < n and line[i+1] == ' ':
            tokens.append(('punct', line[i] + ' '))
            i += 2
            continue
        
        # Any other non-Akkadian character (including spaces)
        # Collect until next Akkadian letter
        start = i
        while i < n and not is_akkadian(line[i], extra):
            i += 1
        tokens.append(('punct', line[start:i]))
    
    return tokens


def syllabify_text(text, extra=''):
    """Process text and return syllabified version."""
    lines = text.split('\n')
    result_lines = []
    
    for line in lines:
        line = line.rstrip('\n')
        if not line.strip():
            result_lines.append('')
            continue
        
        tokens = tokenize_line(line, extra)
        
        parts = []
        for typ, text in tokens:
            if typ == 'word':
                parts.append(syllabify_word(text) + '|')
            else:  # punct
                # Skip standalone spaces between words
                if text == ' ':
                    continue
                parts.append(f"[{text}]")
        
        result_lines.append(''.join(parts))
    
    return '\n'.join(result_lines)


def process_file(input_file, output_file, extra_letters=''):
    """Main processing function."""
    print(f"Reading: {input_file}")
    print(f"Extra letters: '{extra_letters}'" if extra_letters else "Extra letters: none")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Processing...")
    
    result = syllabify_text(content, extra_letters)
    
    print(f"Written: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)


def run_tests():
    """Run comprehensive unit tests with CORRECT expectations."""
    print("\n" + "="*80)
    print("AKKADIAN SYLLABIFIER — COMPREHENSIVE TESTS")
    print("="*80)
    
    tests = [
        # ===== SYLLABLE TYPES =====
        ("CV", "ša", "ša|"),
        ("CVC", "šar", "šar|"),
        ("CVV", "bā", "bā|"),
        ("CVVC", "nāš", "nāš|"),
        ("#VC", "ap", "ap|"),
        ("#V", "a", "a|"),
        ("#VV", "ī", "ī|"),
        ("#VVC", "ān", "ān|"),
        
        # ===== WORD COMBINATIONS =====
        ("CV-CVC", "gimir", "gi.mir|"),
        ("CVC-CVV", "dadmē", "dad.mē|"),
        ("CVV-CVV", "bānû", "bā.nû|"),
        ("CVC-CVV-CV", "kibrāti", "kib.rā.ti|"),
        ("CVC-CVC-CVC-CV", "ḫendursanga", "ḫen.dur.san.ga|"),
        ("V-CVC", "apil", "a.pil|"),
        ("VC-CVC", "ellil", "el.lil|"),
        ("CVVC-CVV", "rēštû", "rēš.tû|"),
        ("CVC-CV-geminate", "ḫaṭṭi", "ḫaṭ.ṭi|"),
        ("CVVC-CV", "ṣīrti", "ṣīr.ti|"),
        ("CVV-CVC", "nāqid", "nā.qid|"),
        ("CVC-CVVC", "ṣalmāt", "ṣal.māt|"),
        ("CVC-CV-CV", "qaqqadi", "qaq.qa.di|"),
        ("CVV-CVV", "rēʾû", "rē.ʾû|"),
        ("CV-CVV-CVV-CV", "tenēšēti", "te.nē.šē.ti|"),
        ("VV-CVC", "īšum", "ī.šum|"),
        ("CVV-CV-CV", "ṭābiḫu", "ṭā.bi.ḫu|"),
        ("CVC-CV", "naʾdu", "naʾ.du|"),
        ("V-CV", "ana", "a.na|"),
        ("CV-CVV", "našê", "na.šê|"),
        ("CVC-CVV-CV", "kakkīšu", "kak.kī.šu|"),
        ("VC-CVV-CV", "ezzūti", "ez.zū.ti|"),
        ("CVV-CVV-CV", "qātāšu", "qā.tā.šu|"),
        ("VC-CVV", "asmā", "as.mā|"),
        
        # ===== NUMBERS =====
        ("Number standalone", "123", "[123]"),
        ("Number between words", "šar 123 gimir", "šar|[ 123 ]gi.mir|"),
        ("Number with spaces", "šar  123  gimir", "šar|[  123  ]gi.mir|"),
        ("Number with commas", "šar 12,345 gimir", "šar|[ 12,345 ]gi.mir|"),
        
        # ===== SINGLE PUNCTUATION =====
        ("Comma space after", "šar, gimir", "šar|[, ]gi.mir|"),
        ("Period space after", "šar. gimir", "šar|[. ]gi.mir|"),
        ("Colon space after", "šar: gimir", "šar|[: ]gi.mir|"),
        ("Semicolon space after", "šar; gimir", "šar|[; ]gi.mir|"),
        ("Question space after", "šar? gimir", "šar|[? ]gi.mir|"),
        ("Exclamation space after", "šar! gimir", "šar|[! ]gi.mir|"),
        
        # ===== PUNCTUATION WITH SPACE BEFORE =====
        ("Space before comma", "šar ,gimir", "šar|[ ,]gi.mir|"),
        ("Space before period", "šar .gimir", "šar|[ .]gi.mir|"),
        ("Space before question", "šar ?gimir", "šar|[ ?]gi.mir|"),
        
        # ===== PUNCTUATION WITH SPACES BOTH SIDES =====
        ("Space both sides comma", "šar , gimir", "šar|[ , ]gi.mir|"),
        ("Space both sides period", "šar . gimir", "šar|[ . ]gi.mir|"),
        ("Space both sides colon", "šar : gimir", "šar|[ : ]gi.mir|"),
        ("Space both sides semicolon", "šar ; gimir", "šar|[ ; ]gi.mir|"),
        ("Space both sides question", "šar ? gimir", "šar|[ ? ]gi.mir|"),
        ("Space both sides exclamation", "šar ! gimir", "šar|[ ! ]gi.mir|"),
        
        # ===== MULTIPLE PUNCTUATION =====
        ("Double pipe space both sides", "šar || gimir", "šar|[ || ]gi.mir|"),
        ("Double pipe space after only", "šar|| gimir", "šar|[|| ]gi.mir|"),
        ("Double pipe space before only", "šar ||gimir", "šar|[ ||]gi.mir|"),
        ("Double pipe no spaces", "šar||gimir", "šar|[||]gi.mir|"),
        
        # ===== ELLIPSIS =====
        ("Ellipsis space both sides", "šar ... gimir", "šar|[ ... ]gi.mir|"),
        ("Ellipsis space after only", "šar... gimir", "šar|[... ]gi.mir|"),
        ("Ellipsis space before only", "šar ...gimir", "šar|[ ...]gi.mir|"),
        ("Ellipsis no spaces", "šar...gimir", "šar|[...]gi.mir|"),
        
        # ===== MIXED PUNCTUATION =====
        ("Ellipsis and double pipe", "šar ... || gimir", "šar|[ ... || ]gi.mir|"),
        ("Comma and ellipsis", "šar, ... gimir", "šar|[, ][... ]gi.mir|"),
        ("Multiple punctuation with spaces", "šar : ... || gimir", "šar|[ : ... || ]gi.mir|"),
        
        # ===== REAL EXAMPLES =====
        ("Complex line with ellipsis and double pipe", 
         "ikkaru ina muhhi ... || ibakki ṣarpiš",
         "ik.ka.ru|i.na|muh.hi|[ ... || ]i.bak.ki|ṣar.piš|"),
        
        ("Line with numbers and punctuation",
         "šar gimir 123, 456 ... done",
         "šar|gi.mir|[ 123, 456 ... ]d|[o]ne|"),
    ]
    
    passed = 0
    total = len(tests)
    
    print(f"\nRunning {total} tests...\n")
    
    for name, inp, expected in tests:
        # Process the input
        result = syllabify_text(inp)
        
        if result == expected:
            passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
            print(f"   Input:    '{inp}'")
            print(f"   Expected: '{expected}'")
            print(f"   Got:      '{result}'")
            # Show tokens for debugging
            tokens = tokenize_line(inp)
            print(f"   Tokens: {[(t[0], repr(t[1])) for t in tokens]}")
    
    print(f"\nPassed: {passed}/{total}")
    return passed == total

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
    if len(sys.argv) == 1:
        print(__doc__)
        print("\nUsage: python syllabify.py <input> [-o <output>] [--outdir <dir>] [--extra-letters <chars>] [--test]")
        sys.exit(0)
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        print("\n" + "="*60)
        print("OPTIONS:")
        print("  -o <prefix>      Output prefix (creates <prefix>_syl.txt)")
        print("  --outdir <dir>   Output directory (default: .)")
        print("  --extra-letters <chars>  Add extra characters to the letter set")
        print("  --test            Run unit tests")
        print("="*60)
        print("\nEXAMPLES:")
        print("  python syllabify.py input.txt")
        print("  python syllabify.py input.txt -o erra --outdir ./output")
        print("  python syllabify.py input.txt --extra-letters \"abc\"")
        print("  python syllabify.py --test")
        print("="*60)
        sys.exit(0)
    
    if '--test' in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    # Parse arguments
    input_file = None
    output_name = None
    outdir = '.'
    extra_letters = ''
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-o' and i+1 < len(sys.argv):
            output_name = sys.argv[i+1]
            i += 2
        elif arg == '--outdir' and i+1 < len(sys.argv):
            outdir = sys.argv[i+1]
            i += 2
        elif arg == '--extra-letters' and i+1 < len(sys.argv):
            extra_letters = sys.argv[i+1]
            i += 2
        elif arg.startswith('-'):
            print(f"Unknown option: {arg}")
            sys.exit(1)
        else:
            if input_file is None:
                input_file = arg
            else:
                print(f"Unexpected argument: {arg}")
                sys.exit(1)
            i += 1
    
    if not input_file:
        print("Error: No input file specified")
        sys.exit(1)
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    # Update foreign character set
    global FOREIGN, AKLOI
    FOREIGN = set('h')  # Default: 'h' for ḫ
    for c in extra_letters:
        FOREIGN.add(c)
    AKLOI = get_akloi(extra_letters)
    
    if output_name:
        output_name = simple_safe_filename(output_name)
        output_file = Path(outdir) / f"{output_name}_syl.txt"
    else:
        output_file = Path(outdir) / (input_path.stem + '_syl.txt')
    
    process_file(input_file, str(output_file), extra_letters)


if __name__ == "__main__":
    main()