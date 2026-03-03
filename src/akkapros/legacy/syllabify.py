#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Syllabifier
Version: 1.2.0

Converts Akkadian text to syllabified format with:
- Initially, pipes | at word ENDINGS (no spaces after) - replaced by ¦
- Dots . between syllables (hyphens preserved by default)
- Non-Akkadian text in [brackets] with ALL whitespace preserved inside
- Spaces between Akkadian words are eliminated (replaced by pipe)
- Newlines between words are preserved as line breaks
- Hyphen vs dash distinction: attached hyphen = syllable separator, spaced dash = punctuation
- Hyphen split across lines automatically merged with warning
- Leading/trailing spaces trimmed
- Diphthong detection: inserts glottal stop between adjacent vowels
"""

import sys
import re
import unicodedata
from pathlib import Path

__version__ = "1.2.0"


# ------------------------------------------------------------
# Phonetic inventory — Akkadian core
# ------------------------------------------------------------
AKKADIAN_VOWELS = set('āēīūâêîûaeiu')
AKKADIAN_CONSONANTS = set('bdgkpṭqṣszšlmnrḥḫʿʾwyt')

# Vowel length categories
SHORT = set('aeiu')
LONG = set('āēīūâêîû')

# Foreign characters (from command line)
FOREIGN_VOWELS = set()
FOREIGN_CONSONANTS = set()
EXTRA_VOWELS = set()
EXTRA_CONSONANTS = set()

# All vowels for processing
ALL_VOWELS = AKKADIAN_VOWELS | FOREIGN_VOWELS | EXTRA_VOWELS
ALL_CONSONANTS = AKKADIAN_CONSONANTS | FOREIGN_CONSONANTS | EXTRA_CONSONANTS
ALL_AKKADIAN = ALL_VOWELS | ALL_CONSONANTS

GLOTTAL = 'ʾ'  # Glottal stop symbol (U+02BE)

SYL_WORD_ENDING = '¦'

if GLOTTAL not in ALL_CONSONANTS:
    ALL_CONSONANTS.add(GLOTTAL)

def is_vowel(c):
    """Return True if character is a vowel."""
    return c in ALL_VOWELS


def is_consonant(c):
    """Return True if character is a consonant."""
    return c in ALL_CONSONANTS


def is_akkadian_letter(c):
    """Return True if character is an Akkadian letter."""
    return c in ALL_AKKADIAN


def is_hyphen(c, before='', after=''):
    """Return True if character is a hyphen attached to letters (not a dash)."""
    if c != '-':
        return False
    
    # If no context, just return True for hyphen character
    if before == '' and after == '':
        return True
    
    # Check if this is a dash (surrounded by spaces) or hyphen (attached to letters)
    before_is_letter = before and is_akkadian_letter(before)
    after_is_letter = after and is_akkadian_letter(after)
    
    # If it has a letter on either side, it's a hyphen (part of word)
    return before_is_letter or after_is_letter


def is_word_char(c, extra='', before='', after=''):
    """Return True if character can be part of an Akkadian word."""
    if is_akkadian_letter(c):
        return True
    if c == '-':
        return is_hyphen(c, before, after)
    return False


def preprocess_diphthongs(text):
    """
    Detect and process diphthongs by inserting a glottal stop between adjacent vowels.
    
    A diphthong is defined as two vowels in sequence (VV) within a word.
    For each occurrence, insert a glottal stop between them: V ʾ V
    
    Examples:
        'ua' → 'uʾa'
        'ai' → 'aʾi'
        'āi' → 'āʾi'
    
    Returns:
        Processed text with diphthongs separated by glottal stops
        Also prints warnings for each detected diphthong
    """
    # Build a regex pattern that matches two vowels in sequence
    vowels_pattern = f'([{re.escape("".join(ALL_VOWELS))}])([{re.escape("".join(ALL_VOWELS))}])'
    
    # Find all diphthongs
    matches = list(re.finditer(vowels_pattern, text))
    
    if matches:
        print("\n⚠️  DIPHTHONG WARNINGS:", file=sys.stderr)
        for match in matches:
            diphthong = match.group(0)
            pos = match.start()
            # Show context (10 chars before and after)
            start = max(0, pos - 10)
            end = min(len(text), pos + 10)
            context = text[start:end]
            print(f"   Diphthong '{diphthong}' at position {pos}: ...{context}...", file=sys.stderr)
            print(f"     → Inserting glottal stop: {diphthong[0]}ʾ{diphthong[1]}", file=sys.stderr)
        
        # Replace all diphthongs with vowel + glottal + vowel
        text = re.sub(vowels_pattern, r'\1' + GLOTTAL + r'\2', text)
        print(f"   Total diphthongs processed: {len(matches)}", file=sys.stderr)
        print(file=sys.stderr)
    
    return text


def text_preprocess_boundaries(text, warnings, extra_vowels='', extra_consonants=''):
    """
    Preprocess text before syllabification:
    1. Update character sets with extra vowels/consonants
    2. Process diphthongs (insert glottal stops)
    3. Trim trailing whitespace from each line (preserve leading spaces)
    4. Detect and merge hyphen-split words across lines
    5. Preserve newlines for paragraph structure
    6. Warn about tabs between Akkadian words
    """
    
    if not isinstance(warnings, list):
        raise TypeError("Expected a list in text_preprocess_boundaries")

    # Update global character sets
    global ALL_VOWELS, ALL_CONSONANTS, ALL_AKKADIAN
    ALL_VOWELS = AKKADIAN_VOWELS | set(extra_vowels)
    ALL_CONSONANTS = AKKADIAN_CONSONANTS | set(extra_consonants)
    ALL_AKKADIAN = ALL_VOWELS | ALL_CONSONANTS
    
    # Process diphthongs
    text = preprocess_diphthongs(text)
    
    lines = text.split('\n')
    processed_lines = []
    warnings = []
    tab_warning_issued = False
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')
        original_line = line
        
        # Only trim trailing whitespace, preserve leading spaces
        line = line.rstrip()
        
        # Check for hyphen at end of line
        if original_line.rstrip().endswith('-') and i + 1 < len(lines):
            next_line = lines[i + 1]
            next_line_stripped = next_line.lstrip()
            if next_line_stripped and is_word_char(next_line_stripped[0]):
                base = original_line.rstrip().rstrip('-')
                merged = base + '-' + next_line_stripped
                warnings.append(f"Hyphen split across lines merged: '{original_line.rstrip()}' + '{next_line}' → '{merged}'")
                processed_lines.append(merged)
                
                # Add the rest of the next line after the merged word
                rest = next_line[len(next_line_stripped):]
                if rest:
                    processed_lines.append(rest)
                else:
                    processed_lines.append('')
                
                i += 2
                continue
        
        processed_lines.append(line)
        i += 1
    
    if '\t' in text and not tab_warning_issued:
        warnings.append("Tabs detected: tabs between Akkadian words are treated as spaces and eliminated")
        tab_warning_issued = True
        
    return '\n'.join(processed_lines)


def syllabify_word(word, merge_hyphen=False):
    """Syllabify an Akkadian word."""
    if '-' not in word:
        segs = [c for c in word if is_akkadian_letter(c)]
        if not segs:
            return word
        
        if not any(is_vowel(c) for c in segs):
            return word
        
        syllables = []
        i, n = 0, len(segs)
        first = True
        
        while i < n:
            if first and is_vowel(segs[i]):
                first = False
                syl = [segs[i]]
                i += 1
                if i < n and not is_vowel(segs[i]) and (i+1 >= n or not is_vowel(segs[i+1])):
                    syl.append(segs[i])
                    i += 1
                syllables.append(''.join(syl))
                continue
            
            first = False
            onset = []
            while i < n and not is_vowel(segs[i]):
                onset.append(segs[i])
                i += 1
            
            if i < n and is_vowel(segs[i]):
                syl = onset + [segs[i]]
                i += 1
                if i < n and not is_vowel(segs[i]):
                    if i+1 >= n or not is_vowel(segs[i+1]):
                        syl.append(segs[i])
                        i += 1
                syllables.append(''.join(syl))
        
        return '.'.join(syllables)
    
    parts = word.split('-')
    result_parts = []
    for part in parts:
        result_parts.append(syllabify_word(part, merge_hyphen))
    
    separator = '-' if not merge_hyphen else '.'
    return separator.join(result_parts)


def tokenize_line(line, extra=''):
    """Split line into word and punctuation tokens."""
    tokens = []
    i = 0
    n = len(line)

    while i < n:
        before = line[i-1] if i > 0 else ''
        after = line[i+1] if i+1 < n else ''
        
        if is_word_char(line[i], extra, before, after):
            start = i
            while i < n:
                before_inner = line[i-1] if i > start else ''
                after_inner = line[i+1] if i+1 < n else ''
                if not is_word_char(line[i], extra, before_inner, after_inner):
                    break
                i += 1
            word = line[start:i]
            tokens.append(('word', word))
        else:
            start = i
            while i < n:
                before_inner = line[i-1] if i > start else ''
                after_inner = line[i+1] if i+1 < n else ''
                if is_word_char(line[i], extra, before_inner, after_inner):
                    break
                i += 1
            punct = line[start:i]
            
            if punct.isspace():
                prev_is_word = tokens and tokens[-1][0] == 'word'
                next_is_word = i < n and is_word_char(line[i], extra)
                if prev_is_word and next_is_word:
                    continue
            
            if punct:
                tokens.append(('punct', punct))
    
    return tokens


def syllabify_text(text, extra_vowels='', extra_consonants='', merge_hyphen=False):
    """Process text and return syllabified version."""
    warnings = []  
    text = text_preprocess_boundaries(text, warnings, extra_vowels, extra_consonants)
    lines = text.split('\n')
    result_lines = []
  

    for line in lines:
        line = line.rstrip('\n')
        if not line:
            result_lines.append('')
            continue
        
        tokens = tokenize_line(line, '')  # extra parameter handled via globals
        current_line_parts = []
        in_brackets = False
        
        for typ, token_text in tokens:
            if typ == 'word':
                if in_brackets:
                    current_line_parts.append(token_text + SYL_WORD_ENDING)
                else:
                    syllabified = syllabify_word(token_text, merge_hyphen)
                    current_line_parts.append(syllabified + SYL_WORD_ENDING)
            else:
                # 'punct'
                if '[' in token_text:
                    in_brackets = True
                if ']' in token_text:
                    in_brackets = False
                current_line_parts.append(f"[{token_text}]")
                if not ' ' in token_text and not '\t' in token_text:
                    warnings.append(f"Punctuation part does not contain a space: '{token_text}' line '{line}")
        
        if current_line_parts:
            result_lines.append(''.join(current_line_parts))
    
    if warnings:
        print("\n⚠️  WARNINGS:", file=sys.stderr)
        for w in warnings:
            print(f"   {w}", file=sys.stderr)
        print(file=sys.stderr)


    return '\n'.join(result_lines)


def process_file(input_file, output_file, extra_vowels='', extra_consonants='', merge_hyphen=False):
    """Main processing function."""
    print(f"Reading: {input_file}")
    if extra_vowels:
        print(f"Extra vowels: '{extra_vowels}'")
    if extra_consonants:
        print(f"Extra consonants: '{extra_consonants}'")
    print(f"Hyphen mode: {'MERGE TO DOTS' if merge_hyphen else 'PRESERVE'}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Processing...")
    result = syllabify_text(content, extra_vowels, extra_consonants, merge_hyphen)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"Written: {output_file}")


def run_tests():
    """Run unit tests."""
    print("\n" + "="*80)
    print("AKKADIAN SYLLABIFIER — COMPREHENSIVE TESTS")
    print("="*80)
    
    tests = [
        # ===== SYLLABLE TYPES =====
        ("CV", "ša", "ša¦"),
        ("CVC", "šar", "šar¦"),
        ("CVV", "bā", "bā¦"),
        ("CVVC", "nāš", "nāš¦"),
        ("#VC", "ap", "ap¦"),
        ("#V", "a", "a¦"),
        ("#VV", "ī", "ī¦"),
        ("#VVC", "ān", "ān¦"),
        
        # ===== WORD COMBINATIONS =====
        ("CV-CVC", "gimir", "gi.mir¦"),
        ("CVC-CVV", "dadmē", "dad.mē¦"),
        ("CVV-CVV", "bānû", "bā.nû¦"),
        ("CVC-CVV-CV", "kibrāti", "kib.rā.ti¦"),
        ("CVC-CVC-CVC-CV", "ḫendursanga", "ḫen.dur.san.ga¦"),
        ("V-CVC", "apil", "a.pil¦"),
        ("VC-CVC", "ellil", "el.lil¦"),
        ("CVVC-CVV", "rēštû", "rēš.tû¦"),
        ("CVC-CV-geminate", "ḫaṭṭi", "ḫaṭ.ṭi¦"),
        ("CVVC-CV", "ṣīrti", "ṣīr.ti¦"),
        ("CVV-CVC", "nāqid", "nā.qid¦"),
        ("CVC-CVVC", "ṣalmāt", "ṣal.māt¦"),
        ("CVC-CV-CV", "qaqqadi", "qaq.qa.di¦"),
        ("CVV-CVV", "rēʾû", "rē.ʾû¦"),
        ("CV-CVV-CVV-CV", "tenēšēti", "te.nē.šē.ti¦"),
        ("VV-CVC", "īšum", "ī.šum¦"),
        ("CVV-CV-CV", "ṭābiḫu", "ṭā.bi.ḫu¦"),
        ("CVC-CV", "naʾdu", "naʾ.du¦"),
        ("V-CV", "ana", "a.na¦"),
        ("CV-CVV", "našê", "na.šê¦"),
        ("CVC-CVV-CV", "kakkīšu", "kak.kī.šu¦"),
        ("VC-CVV-CV", "ezzūti", "ez.zū.ti¦"),
        ("CVV-CVV-CV", "qātāšu", "qā.tā.šu¦"),
        ("VC-CVV", "asmā", "as.mā¦"),
        
        # ===== HYPHEN TESTS =====
        ("Hyphenated word - preserve", "ḫendur-sanga", "ḫen.dur-san.ga¦"),
        ("Hyphenated word - merge", "ḫendur-sanga", "ḫen.dur.san.ga¦", True),
        ("Multiple hyphens - preserve", "amēlu-ša-īšum", "a.mē.lu-ša-ī.šum¦"),
        ("Multiple hyphens - merge", "amēlu-ša-īšum", "a.mē.lu.ša.ī.šum¦", True),
        ("Hyphen at beginning", "-šar", "-šar¦"),
        ("Hyphen at end", "šar-", "šar-¦"),
        
        # ===== DASH VS HYPHEN =====
        ("Dash with spaces", "ḫendur - sanga", "ḫen.dur¦[ - ]san.ga¦"),
        ("Hyphen+space", "ḫendur- sanga", "ḫen.dur-¦san.ga¦"),
        ("Space+hyphen", "ḫendur -sanga", "ḫen.dur¦-san.ga¦"),
        
        # ===== WHITESPACE BETWEEN WORDS =====
        ("Single space between words", "šar gimir", "šar¦gi.mir¦"),
        ("Multiple spaces between words", "šar   gimir", "šar¦gi.mir¦"),
        ("Tab between words", "šar\tgimir", "šar¦gi.mir¦"),
        ("Newline between words", "šar\ngimir", "šar¦\ngi.mir¦"),
        ("Double newline", "šar\n\ngimir", "šar¦\n\ngi.mir¦"),
        
        # ===== NUMBERS AND NON-AKKADIAN =====
        ("Number between words", "šar 123 gimir", "šar¦[ 123 ]gi.mir¦"),
        ("Number with commas", "šar 12,345 gimir", "šar¦[ 12,345 ]gi.mir¦"),
        ("Number with newline", "šar 123\n456 gimir", "šar¦[ 123]\n[456 ]gi.mir¦"),
        ("Number with spaces and newline", "šar 123\n  456 gimir", "šar¦[ 123]\n[  456 ]gi.mir¦"),
        ("Number with tab and dash", "šar 123  \t-  456 gimir", "šar¦[ 123  \t-  456 ]gi.mir¦"),
        
        # ===== PUNCTUATION =====
        ("Comma after word", "šar, gimir", "šar¦[, ]gi.mir¦"),
        ("Period after word", "šar. gimir", "šar¦[. ]gi.mir¦"),
        ("Em-dash", "šar — gimir", "šar¦[ — ]gi.mir¦"),
        ("Ellipsis", "šar … gimir", "šar¦[ … ]gi.mir¦"),
        
        # ===== FOREIGN CHARACTERS =====
        ("Chinese characters", "šar 国王 gimir", "šar¦[ 国王 ]gi.mir¦"),
        ("Mixed with brackets", "šar gimir[test]done", "šar¦gi.mir¦[[]test¦[]]d¦[o]ne¦"),
        
        # ===== REAL EXAMPLES =====
        ("Complex line", "ikkaru ina muḫḫi … — ibakki ṣarpiš", 
         "ik.ka.ru¦i.na¦muḫ.ḫi¦[ … — ]i.bak.ki¦ṣar.piš¦"),
        
        # ===== DIPHTHONG TESTS =====
        ("Diphthong ua", "ua", "u.ʾa¦"),
        ("Diphthong ai", "ai", "a.ʾi¦"),
        ("Diphthong iā", "iā", "i.ʾā¦"),
        ("Multiple diphthongs", "ua iā", "u.ʾa¦i.ʾā¦"),
        ("Diphthong with consonant", "šar ua", "šar¦u.ʾa¦"),

    ]
    
    passed = 0
    total = len(tests)
    
    print(f"\nRunning {total} tests...\n")
    for test in tests:
        if len(test) == 3:
            name, inp, expected = test
            merge = False
        else:
            name, inp, expected, merge = test
        
        result = syllabify_text(inp, merge_hyphen=merge)
        if result == expected:
            print(f"✅ {name}")
            passed += 1
        else:
            print(f"❌ {name}")
            print(f"   Input: '{inp}'\n   Expected: '{expected}'\n   Got: '{result}'")
    
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
    if len(sys.argv) == 1 or '--help' in sys.argv:
        print(__doc__)
        return
    
    if '--test' in sys.argv:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    input_file = None
    output_name = None
    outdir = '.'
    extra_vowels = ''
    extra_consonants = ''
    merge_hyphen = False
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-o' and i+1 < len(sys.argv):
            output_name = sys.argv[i+1]
            i += 2
        elif arg == '--outdir' and i+1 < len(sys.argv):
            outdir = sys.argv[i+1]
            i += 2
        elif arg == '--extra-vowels' and i+1 < len(sys.argv):
            extra_vowels = sys.argv[i+1]
            i += 2
        elif arg == '--extra-consonants' and i+1 < len(sys.argv):
            extra_consonants = sys.argv[i+1]
            i += 2
        elif arg == '--merge-hyphen':
            merge_hyphen = True
            i += 1
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
    
    if output_name:
        safe_output = simple_safe_filename(output_name)        
        output_file = Path(outdir) / f"{safe_output}_syl.txt"
    else:
        output_file = Path(outdir) / (input_path.stem + '_syl.txt')
    
    process_file(input_file, str(output_file), extra_vowels, extra_consonants, merge_hyphen)


if __name__ == "__main__":
    main()