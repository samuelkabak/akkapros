#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Metrics Calculator
Version: 2.0.0

Computes comprehensive metrics from Akkadian text with proper handling of:
- Vowel length: short (a), long (ā/â), extra-long (à/ì/ù/è)
- Consonant gemination: marked with : (e.g., mas:ta)
- Glottal stops: ʾ for initial vowels
- Distance-based ΔC calculation
- Word boundaries marked with $
- Pause metrics for spaces and punctuation
"""

import re
import random
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from collections import Counter

__version__ = "2.0.0"


# shared constants
from akkapros.lib.constants import (
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    GLOTTAL,
    SYL_WORD_ENDING,
    SYL_SEPARATOR,
    OPEN_ESCAPE,
    CLOSE_ESCAPE,
    TIL_WORD_LINKER,
    SHORT_VOWELS,
    LONG_VOWELS,
    EXTRA_LONG_VOWELS
)

HYPHEN = '-'

# ------------------------------------------------------------
# Phonetic inventory — Akkadian core
# ------------------------------------------------------------

#AKKADIAN_VOWELS = set('āēīūâêîûaeiu')
#AKKADIAN_CONSONANTS = set('bdgkpṭqṣszšlmnrḥḫʿʾwyt')

# Vowel length categories
#SHORT_VOWELS = set('aeiu')
#LONG_VOWELS = set('āēīūâêîû')
#EXTRA_LONG_VOWELS = set('àìùè')

#GLOTTAL = 'ʾ'  # Glottal stop symbol (U+02BE)


# Foreign characters (from command line)
FOREIGN_VOWELS = set()
FOREIGN_CONSONANTS = set()
EXTRA_VOWELS = set()
EXTRA_CONSONANTS = set()


# All vowels for processing (including extra-long)
ALL_VOWELS = AKKADIAN_VOWELS | FOREIGN_VOWELS | EXTRA_VOWELS | EXTRA_LONG_VOWELS
ALL_CONSONANTS = AKKADIAN_CONSONANTS | FOREIGN_CONSONANTS | EXTRA_CONSONANTS
ALL_AKKADIAN = ALL_VOWELS | ALL_CONSONANTS

# Processing-specific sets
PROCESSING_VOWELS = EXTRA_LONG_VOWELS

LENGTH_MARKER = ':'
WORD_BOUNDARY = '$'

# All possible syllable types
SYLLABLE_TYPES = [
    'CV', 'CVC', 'CVV', 'CVVC',
    'VC', 'V', 'VV', 'VVC',
    'C:V', 'CVC:', 'CVV:', 'CVV:C',
    'VC:', 'ʔ:V', 'VV:', 'VV:C'
]


def update_character_sets(extra_consonants='', extra_vowels=''):
    """Update global character sets with user-provided extras."""
    global FOREIGN_VOWELS, FOREIGN_CONSONANTS, EXTRA_VOWELS, EXTRA_CONSONANTS
    global ALL_VOWELS, ALL_CONSONANTS, ALL_AKKADIAN
    
    EXTRA_CONSONANTS = set(extra_consonants)
    EXTRA_VOWELS = set(extra_vowels)
    
    ALL_VOWELS = AKKADIAN_VOWELS | FOREIGN_VOWELS | EXTRA_VOWELS | EXTRA_LONG_VOWELS
    ALL_CONSONANTS = AKKADIAN_CONSONANTS | FOREIGN_CONSONANTS | EXTRA_CONSONANTS
    ALL_AKKADIAN = ALL_VOWELS | ALL_CONSONANTS


def is_vowel(c: str) -> bool:
    """Return True if character is a vowel (including extra-long)."""
    return c in ALL_VOWELS


def is_vowel_processing(c: str) -> bool:
    """Return True if character is a vowel for processing purposes (includes extra-long)."""
    return c in ALL_VOWELS or c in PROCESSING_VOWELS


def is_consonant(c: str) -> bool:
    """Return True if character is a consonant."""
    return c in ALL_CONSONANTS or c == GLOTTAL


def is_consonant_processing(c: str) -> bool:
    """Return True if character is a consonant for processing purposes."""
    return c in ALL_CONSONANTS or c == GLOTTAL


def is_akkadian(c: str) -> bool:
    """Return True if character is an Akkadian letter."""
    return c in ALL_AKKADIAN


# ------------------------------------------------------------
# Word pattern builder
# ------------------------------------------------------------
def build_word_pattern() -> re.Pattern:
    """Build regex pattern for MERGED_WORD based on the spec."""
    # Build regex classes - sort for consistency
    vowels_class = ''.join(sorted(ALL_VOWELS))
    consonants_class = ''.join(sorted(ALL_CONSONANTS))
    
    # CLASS_SYLLABLE_COMPLEMENT := (CONSONANTS or VOWELS or '~')
    complement_class = f'[{consonants_class}{vowels_class}~]*'
    
    # CLASS_WORD_FIRST_SYLLABLE_FIRST_LETTER := (CONSONANTS or VOWELS or '~')
    first_letter_class = f'[{consonants_class}{vowels_class}~]'
    
    # CLASS_WORD_INTERNAL_SYLLABLE_FIRST_LETTER := CONSONANTS
    internal_first_class = f'[{consonants_class}]'
    
    # CLASS_SYLLABLE_SEPARATOR := SYL_SEPARATOR or HYPHEN
    syl_sep = rf'[\{SYL_SEPARATOR}\{HYPHEN}]'
    
    # CLASS_UNIT_WORD_SEPARATOR := TIL_WORD_LINKER
    unit_sep = TIL_WORD_LINKER
    
    # CLASS_FIRST_SYLLABLE := FIRST_LETTER + COMPLEMENT*
    first_syl = first_letter_class + complement_class
    
    # CLASS_INTERNAL_SYLLABLE := INTERNAL_FIRST_LETTER + COMPLEMENT*
    internal_syl = internal_first_class + complement_class
    
    # CLASS_UNIT_WORD := FIRST_SYLLABLE + (SEPARATOR + INTERNAL_SYLLABLE)*
    unit_word = first_syl + f'(?:{syl_sep}{internal_syl})*'
    
    # CLASS_MERGED_WORD := UNIT_WORD + (UNIT_SEPARATOR + UNIT_WORD)*
    merged_word = unit_word + rf'(?:\{unit_sep}{unit_word})*'
    
    return re.compile(merged_word)


# ------------------------------------------------------------
# Tokenizer
# ------------------------------------------------------------
def tokenize_line(line: str, word_pattern: re.Pattern) -> List[Tuple[str, str]]:
    """
    Tokenize a line into WORD, SPACES, and PUNCT tokens using re.search.
    
    Args:
        line: Input line
        word_pattern: Compiled regex pattern for Akkadian words
    
    Returns:
        List of (type, value) tuples where type is 'WORD', 'SPACES', or 'PUNCT'
    """
    tokens = []
    i = 0
    n = len(line)
    
    while i < n:
        # Check for spaces
        if line[i].isspace():
            start = i
            while i < n and line[i].isspace():
                i += 1
            tokens.append(('SPACES', line[start:i]))
            continue
        
        # Search for a word starting at current position
        match = word_pattern.search(line, i)
        if match and match.start() == i:
            # Word starts exactly at current position
            word = match.group()
            tokens.append(('WORD', word))
            i = match.end()
        else:
            # No word at current position, it's punctuation
            tokens.append(('PUNCT', line[i]))
            i += 1
    
    return tokens


# ------------------------------------------------------------
# Word processing
# ------------------------------------------------------------
def process_word(word: str) -> str:
    """
    Process a single word:
    1. Replace vowel + ~ with extra-long vowels (à, ì, ù, è)
    2. Replace remaining ~ with : (length marker)
    3. Add ʾ if word starts with a vowel
    """
    # Step 1: Replace vowel + ~ with extra-long vowels
    replacements = [
        ('ā~', 'à'), ('â~', 'à'),
        ('ī~', 'ì'), ('î~', 'ì'),
        ('ū~', 'ù'), ('û~', 'ù'),
        ('ē~', 'è'), ('ê~', 'è'),
    ]
    for old, new in replacements:
        word = word.replace(old, new)
    
    # Step 2: Replace remaining ~ with :
    word = word.replace('~', LENGTH_MARKER)
    
    # Step 3: Add ʾ if word starts with a vowel
    # Get first character ignoring syllable boundaries
    first_char = word[0]
    if first_char in ALL_VOWELS:
        word = GLOTTAL + word
    
    return word


# ------------------------------------------------------------
# Extract words
# ------------------------------------------------------------
def extract_words(text: str, word_pattern: re.Pattern) -> List[str]:
    """Extract all Akkadian words from text using the word pattern."""
    return word_pattern.findall(text)


def count_merged_units(words: List[str]) -> Dict:
    """
    Count merged words and units.
    
    Returns:
        {
            'total_merged_words': number of words attached with _
            'merged_units': number of groups with _
            'avg_unit_size': average words per merged group
        }
    """
    total_merged_words = 0
    merged_units = 0
    
    for word in words:
        if TIL_WORD_LINKER in word:
            merged_units += 1
            total_merged_words += word.count(TIL_WORD_LINKER) + 1
    
    avg = total_merged_words / merged_units if merged_units > 0 else 0
    
    return {
        'total_merged_words': total_merged_words,
        'merged_units': merged_units,
        'avg_unit_size': avg
    }


# ------------------------------------------------------------
# Syllable classification
# ------------------------------------------------------------
def classify_syllable(syl: str, is_repaired: bool = False) -> str:
    """
    Classify a syllable into one of the types.
    """
    if not syl:
        return 'UNKNOWN'
    
    # Replace vowel + ~ with extra-long vowels
    replacements = [
        ('ā~', 'à'), ('â~', 'à'),
        ('ī~', 'ì'), ('î~', 'ì'),
        ('ū~', 'ù'), ('û~', 'ù'),
        ('ē~', 'è'), ('ê~', 'è'),
    ]
    for old, new in replacements:
        syl = syl.replace(old, new)
    
    # Replace remaining ~ with :
    syl = syl.replace('~', LENGTH_MARKER)
    

    # Now classify : based on the processed syllable
    if ':' in syl:
        if syl.startswith(':'):   
            # :V only V in SHORT 
            return 'ʔ:V'
        if syl.endswith(':'):
            # CVC: and VC: only , CV:C; never happen
            if len(syl) == 4:
                return 'CVC:'
            else:
                return 'VC:'
        if ':' in syl[1:2]:
            return 'C:V'
        else:
            pass # Never happen

        
    # Rest of classification 
    clean = syl
    if len(syl) == 1:
        # āēīūâêîûaeiuàìùè
        if syl[0] in SHORT_VOWELS: 
            return 'V'
        if syl[0] in LONG_VOWELS: 
            return 'VV'
        if syl[0] in EXTRA_LONG_VOWELS: 
            return 'VV:'
    elif  len(syl) == 2:
        # c+āēīūâêîûaeiuàìùè or āēīūâêîûaeiuàìùè+C
        if syl[0] in SHORT_VOWELS: 
            return 'VC'
        if syl[0] in LONG_VOWELS: 
            return 'VVC'
        if syl[0] in EXTRA_LONG_VOWELS: 
            return 'VV:C'
        if syl[1] in SHORT_VOWELS: 
            return 'CV'
        if syl[1] in LONG_VOWELS: 
            return 'CVV'
        if syl[1] in EXTRA_LONG_VOWELS: 
            return 'CVV:'
    elif  len(syl) == 3:
        # c+āēīūâêîûaeiuàìùè+c
        if syl[1] in SHORT_VOWELS: 
            return 'CVC'
        if syl[1] in LONG_VOWELS: 
            return 'CVVC'
        if syl[1] in EXTRA_LONG_VOWELS: 
            return 'CVV:C'
    else:
        pass # Never happen

    return '???'

# ------------------------------------------------------------
# Text analysis
# ------------------------------------------------------------
def compute_percent_v_from_stats(stats: Dict) -> float:
    """Compute %V from syllable statistics."""
    # Mora per syllable type: (vowel morae, total morae)
    mora_table = {
        'CV': (1, 1),
        'CVC': (1, 2),
        'CVV': (2, 2),
        'CVVC': (2, 3),
        'VC': (1, 2),
        'V': (1, 1),
        'VV': (2, 2),
        'VVC': (2, 3),
        'C:V': (1, 2),
        'CVC:': (1, 3),
        'CVV:': (2, 3),
        'CVV:C': (3, 4),
        'VC:': (1, 2),
        'ʔ:V': (1, 2),
        'VV:': (2, 3),
        'VV:C': (3, 4),
    }
    
    vowel_morae = 0
    total_morae = 0
    
    for typ, count in stats['syllable_counts'].items():
        if typ in mora_table:
            v, t = mora_table[typ]
            vowel_morae += v * count
            total_morae += t * count
    
    return (vowel_morae / total_morae * 100) if total_morae > 0 else 0

def analyze_text(text: str, is_repaired: bool = False) -> Dict:
    """
    Analyze a text and compute all metrics.
    """
    # Build word pattern
    word_pattern = build_word_pattern()
    
    # Extract words
    words = extract_words(text, word_pattern)

    # Initialize counters
    syllable_counts = {}
    morae_list = []
    syllables_per_word = []
    morae_per_word = []
    
    # Process each word
    for word in words:
        # Split into syllables (on . or -)
        syllables = re.split(rf'[\{SYL_SEPARATOR}\{HYPHEN}\{TIL_WORD_LINKER}]+', word)

        # Count syllables in this word
        word_syllable_count = 0
        word_mora_count = 0
        
        for syl in syllables:
            if not syl:
                continue
            
            word_syllable_count += 1
            
            # Classify syllable
            syl_type = classify_syllable(syl, is_repaired)
            syllable_counts[syl_type] = syllable_counts.get(syl_type, 0) + 1
            
            # Count morae
            morae = 0
            for c in syl:
                if c in LONG_VOWELS:
                    morae += 2
                elif c in EXTRA_LONG_VOWELS:
                    morae += 3
                elif c == LENGTH_MARKER:
                    morae += 1
                elif c in SHORT_VOWELS or c in ALL_CONSONANTS or c == GLOTTAL:
                    morae += 1
            morae_list.append(morae)
            word_mora_count += morae
        
        syllables_per_word.append(word_syllable_count)
        morae_per_word.append(word_mora_count)
    
    # Calculate statistics
    total_syllables = sum(syllable_counts.values())
    
    # Syllable percentages
    syllable_percentages = {}
    for typ, count in syllable_counts.items():
        if total_syllables > 0:
            syllable_percentages[typ] = (count / total_syllables) * 100
        else:
            syllable_percentages[typ] = 0.0
    
    # Mora statistics
    mora_stats = {
        'mean': statistics.mean(morae_list) if morae_list else 0,
        'std': statistics.stdev(morae_list) if len(morae_list) > 1 else 0,
    }
    
    # Word statistics
    word_stats = {
        'total_words': len(words),
        'syllables_per_word': {
            'mean': statistics.mean(syllables_per_word) if syllables_per_word else 0,
            'std': statistics.stdev(syllables_per_word) if len(syllables_per_word) > 1 else 0
        },
        'morae_per_word': {
            'mean': statistics.mean(morae_per_word) if morae_per_word else 0,
            'std': statistics.stdev(morae_per_word) if len(morae_per_word) > 1 else 0
        }
    }
    
    # Merge statistics
    merge_stats = count_merged_units(words)
    
    return {
        'syllable_counts': syllable_counts,
        'syllable_percentages': syllable_percentages,
        'total_syllables': total_syllables,
        'mora_stats': mora_stats,
        'word_stats': word_stats,
        'merge_stats': merge_stats
    }


# ------------------------------------------------------------
# Repair statistics
# ------------------------------------------------------------
def compute_repair_stats(original_stats: Dict, repaired_stats: Dict) -> Dict:
    """
    Compute repair-specific statistics by comparing original and repaired.
    """
    # Count repaired syllables by comparing counts
    repair_types = {}
    total_repaired = 0
    
    all_types = set(original_stats['syllable_counts'].keys()) | set(repaired_stats['syllable_counts'].keys())
    
    for typ in all_types:
        orig_count = original_stats['syllable_counts'].get(typ, 0)
        rep_count = repaired_stats['syllable_counts'].get(typ, 0)
        if rep_count > orig_count:
            # This type increased - repairs created it
            diff = rep_count - orig_count
            repair_types[typ] = diff
            total_repaired += diff
    
    # Repair rate
    repair_rate = (total_repaired / original_stats['total_syllables'] * 100) if original_stats['total_syllables'] > 0 else 0
    
    return {
        'repaired_syllables': total_repaired,
        'repair_rate': repair_rate,
        'repair_types': repair_types,
        'merged_words': repaired_stats['merge_stats']['total_merged_words'],
        'merged_units': repaired_stats['merge_stats']['merged_units'],
        'avg_unit_size': repaired_stats['merge_stats']['avg_unit_size']
    }


# ------------------------------------------------------------
# Segment extraction
# ------------------------------------------------------------
def extract_segments(text: str) -> Tuple[List[str], List[str]]:
    """
    Extract consonant and vowel sequences from preprocessed text.
    Returns (consonants, vowels_after) where vowels_after[i] is the vowel after consonant i.
    """
    # Remove word boundaries and syllable boundaries
    all_segments = []
    for c in text:
        if c in (WORD_BOUNDARY, SYL_SEPARATOR, HYPHEN, TIL_WORD_LINKER):
            continue
        all_segments.append(c)
    
    consonants = []
    vowels_after = []
    
    i = 0
    n = len(all_segments)
    
    while i < n:
        c = all_segments[i]
        
        if is_consonant_processing(c):
            consonants.append(c)
            i += 1
            
            # Look ahead for vowels/length markers after this consonant
            if i < n and (is_vowel_processing(all_segments[i]) or all_segments[i] == LENGTH_MARKER):
                start = i
                while i < n and (is_vowel_processing(all_segments[i]) or all_segments[i] == LENGTH_MARKER):
                    i += 1
                vowels_after.append(''.join(all_segments[start:i]))
            else:
                vowels_after.append('')
        elif is_vowel_processing(c) or c == LENGTH_MARKER:
            # This is a vowel at start (shouldn't happen with glottal stops)
            if not consonants:
                consonants.append(GLOTTAL)
            start = i
            while i < n and (is_vowel_processing(all_segments[i]) or all_segments[i] == LENGTH_MARKER):
                i += 1
            vowels_after.append(''.join(all_segments[start:i]))
        else:
            i += 1
    
    while len(vowels_after) < len(consonants):
        vowels_after.append('')
    
    return consonants, vowels_after


# ------------------------------------------------------------
# Distance calculation
# ------------------------------------------------------------
def vowel_length(v: str) -> int:
    """Return the mora count of a vowel string."""
    if not v:
        return 0
    total = 0
    for c in v:
        if c in SHORT_VOWELS:
            total += 1
        elif c in LONG_VOWELS:
            total += 2
        elif c in EXTRA_LONG_VOWELS:
            total += 3
        elif c == LENGTH_MARKER:
            total += 1
    return total


def compute_consonant_distances(consonants: List[str], vowels_after: List[str]) -> List[int]:
    """
    Compute distances between consonants based on vowel morae.
    """
    distances = []
    
    # Distances between consonants
    for i in range(len(consonants) - 1):
        if i < len(vowels_after):
            distances.append(vowel_length(vowels_after[i]))
        else:
            distances.append(0)
    
    # Distance after last consonant
    if consonants and vowels_after:
        distances.append(vowel_length(vowels_after[-1]))
    
    return distances


def std_dev(values: List[float]) -> float:
    """Calculate standard deviation without numpy."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


# ------------------------------------------------------------
# Acoustic metrics
# ------------------------------------------------------------
def compute_acoustic_metrics(text: str) -> Dict:
    """
    Compute acoustic metrics from preprocessed text.
    """
    consonants, vowels_after = extract_segments(text)
    
    # Total segments
    total_consonants = len(consonants)
    total_vowels = sum(len(v) for v in vowels_after)
    total_segments = total_consonants + total_vowels
    
    if total_segments == 0:
        return {
            'percent_v': 0.0,
            'delta_c': 0.0,
            'mean_interval': 0.0,
            'varco_c': 0.0,
            'distances': []
        }
    
    percent_v = total_vowels / total_segments * 100
    
    distances = compute_consonant_distances(consonants, vowels_after)
    
    if not distances:
        delta_c = 0.0
        mean_interval = 0.0
        varco_c = 0.0
    else:
        delta_c = std_dev(distances) if len(distances) > 1 else 0.0
        mean_interval = sum(distances) / len(distances)
        varco_c = (delta_c / mean_interval) * 100 if mean_interval > 0 else 0.0
    
    return {
        'percent_v': percent_v,
        'delta_c': delta_c,
        'mean_interval': mean_interval,
        'varco_c': varco_c,
        'distances': distances
    }


# ------------------------------------------------------------
# Preprocessing pipeline
# ------------------------------------------------------------
def preprocess_text(text: str) -> str:
    """
    Complete preprocessing pipeline using tokenization.
    """
    # Remove bracketed content first
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Build word pattern
    word_pattern = build_word_pattern()
    
    # Process line by line
    lines = text.split('\n')
    result_lines = []
    
    for line in lines:
        if not line.strip():
            result_lines.append('')
            continue
        
        tokens = tokenize_line(line, word_pattern)
        result_parts = []
        prev_was_word = False
        
        for typ, val in tokens:
            if typ == 'WORD':
                processed = process_word(val)
                if prev_was_word:
                    result_parts.append(WORD_BOUNDARY)
                result_parts.append(processed)
                prev_was_word = True
            elif typ == 'SPACES':
                # Spaces handled by boundaries
                if prev_was_word:
                    # Will add boundary before next word
                    pass
            else:  # PUNCT
                # Always add boundary for punctuation, even at start/end
                result_parts.append(WORD_BOUNDARY)
                prev_was_word = False
        
        # Join the line - don't strip trailing boundaries
        result_line = ''.join(result_parts)
        # Remove leading boundary only (trailing preserved)
        if result_line.startswith(WORD_BOUNDARY):
            result_line = result_line[1:]
        # Collapse multiple boundaries
        while WORD_BOUNDARY * 2 in result_line:
            result_line = result_line.replace(WORD_BOUNDARY * 2, WORD_BOUNDARY)
        result_lines.append(result_line)
    
    return '\n'.join(result_lines)


# ------------------------------------------------------------
# Speech rate calculation
# ------------------------------------------------------------
def compute_speech_rate(text: str, stats: Dict, wpm: float, pause_ratio: float) -> Dict:
    """
    Compute speech rate metrics.
    
    Args:
        text: The text (not used directly, kept for API consistency)
        stats: Statistics from analyze_text containing syllables_per_word
        wpm: Words per minute (input parameter)
        pause_ratio: Percentage of time spent in pauses (e.g., 35 for 35%)
    
    Returns:
        Dictionary with speech rate metrics
    """
    spw = stats['word_stats']['syllables_per_word']['mean']
    
    # Syllables per second (speech rate - INCLUDING pauses)
    # This comes directly from WPM and SPW
    sps_speech = (wpm / 60) * spw
    
    # Syllables per second (articulation rate - EXCLUDING pauses)
    # If pause_ratio% of time is pauses, then articulation time = (100 - pause_ratio)% of total time
    # So articulation rate = speech rate / (1 - pause_ratio/100)
    sps_articulation = sps_speech / (1 - (pause_ratio / 100))
    
    # Durations
    syllable_duration = 1 / sps_articulation
    mora_duration = syllable_duration / stats['mora_stats']['mean'] if stats['mora_stats']['mean'] > 0 else 0
    word_duration = 60 / wpm
    
    return {
        'wpm': wpm,
        'pause_ratio': pause_ratio,
        'sps_speech': sps_speech,
        'sps_articulation': sps_articulation,
        'syllable_duration': syllable_duration,
        'mora_duration': mora_duration,
        'word_duration': word_duration
    }


# ------------------------------------------------------------
# Pause metrics
# ------------------------------------------------------------
def count_spaces_and_punctuation(text: str) -> Dict:
    """
    Count pause events between words.
    
    A pause event is:
    - SPACE: only spaces between two words (no punctuation)
    - PUNCT: any punctuation with surrounding spaces (all captured as one unit)
    """
    word_pattern = build_word_pattern()
    
    spaces = 0
    punctuation = 0
    merged_boundaries = 0
    
    i = 0
    n = len(text)
    last_was_word = False
    
    while i < n:
        # First, try to match a word
        match = word_pattern.match(text[i:])
        if match:
            word = match.group()
            word_underscores = word.count(TIL_WORD_LINKER)
            if word_underscores > 0:
                merged_boundaries += word_underscores
            i += len(word)
            last_was_word = True
            continue
        
        # Not a word - check for spaces/punctuation between words
        if last_was_word:
            # Remember start position
            start = i
            
            # Skip all spaces and punctuation until next word or end
            while i < n and not word_pattern.match(text[i:]):
                i += 1
            
            # Determine if this gap contains any punctuation
            gap = text[start:i]
            has_punctuation = any(c not in ' \t' for c in gap)
            
            if has_punctuation:
                punctuation += 1  # One punctuation pause (includes all spaces)
            else:
                spaces += 1  # Pure spaces pause
            
            last_was_word = False
        else:
            # Skip anything at start (shouldn't happen in valid text)
            i += 1
    
    return {
        'spaces': spaces,
        'punctuation': punctuation,
        'merged_boundaries': merged_boundaries
    }


def compute_pause_metrics(text: str, stats: Dict) -> Dict:
    """
    Compute space and punctuation ratios per syllable.
    
    Args:
        text: Original text (before preprocessing)
        stats: Statistics from analyze_text (contains syllable counts)
    
    Returns:
        {
            'spaces_per_syllable': float,
            'punctuation_per_syllable': float,
            'total_boundaries': int,
            'pauseable_boundaries': int
        }
    """
    counts = count_spaces_and_punctuation(text)
    total_syllables = stats['total_syllables']
    
    if total_syllables == 0:
        return {
            'spaces_per_syllable': 0,
            'punctuation_per_syllable': 0,
            'total_boundaries': 0,
            'pauseable_boundaries': 0,
            'raw_counts': counts
        }
    
    spaces_per_syllable = counts['spaces'] / total_syllables
    punctuation_per_syllable = counts['punctuation'] / total_syllables
    total_boundaries = counts['spaces'] + counts['punctuation'] + counts['merged_boundaries']
    pauseable_boundaries = counts['spaces'] + counts['punctuation']  # Merged boundaries have no pause
    
    return {
        'spaces_per_syllable': spaces_per_syllable,
        'punctuation_per_syllable': punctuation_per_syllable,
        'total_boundaries': total_boundaries,
        'pauseable_boundaries': pauseable_boundaries,
        'raw_counts': counts
    }


def compute_pause_durations(pause_metrics: Dict, speech_metrics: Dict, pause_ratio: float, punct_weight: float = 2.0) -> Dict:
    """
    Compute duration per space and per punctuation based on pause ratio.
    
    Args:
        pause_metrics: Output from compute_pause_metrics
        speech_metrics: Output from compute_speech_rate
        pause_ratio: Total pause ratio percentage
        punct_weight: How many times longer punctuation is than space
    
    Returns:
        Dictionary with space and punctuation durations
    """
    # Get metrics
    spaces_per_syllable = pause_metrics['spaces_per_syllable']
    punct_per_syllable = pause_metrics['punctuation_per_syllable']
    
    # Speech metrics
    syllable_duration = speech_metrics['syllable_duration']
    sps_speech = speech_metrics['sps_speech']
    
    # Total time per syllable including pauses
    total_time_per_syllable = 1 / sps_speech
    
    # Pause time per syllable
    pause_time_per_syllable = total_time_per_syllable - syllable_duration
    
    # Distribute pause time using the weight
    total_pause_units = spaces_per_syllable + punct_per_syllable * punct_weight
    if total_pause_units == 0:
        space_duration = 0
        punct_duration = 0
        space_contribution = 0
        punct_contribution = 0
    else:
        space_duration = pause_time_per_syllable / total_pause_units
        punct_duration = space_duration * punct_weight
        space_contribution = spaces_per_syllable * space_duration
        punct_contribution = punct_per_syllable * punct_duration
    
    return {
        'space_duration': space_duration,
        'punctuation_duration': punct_duration,
        'total_pause_time': pause_time_per_syllable,
        'pause_time_per_syllable': pause_time_per_syllable,
        'space_contribution': space_contribution,
        'punct_contribution': punct_contribution,
        'space_percent': (space_contribution / pause_time_per_syllable * 100) if pause_time_per_syllable > 0 else 0,
        'punct_percent': (punct_contribution / pause_time_per_syllable * 100) if pause_time_per_syllable > 0 else 0,
        'punct_weight': punct_weight
    }


# ------------------------------------------------------------
# Main processing
# ------------------------------------------------------------
def process_file(filename: str, wpm: float, pause_ratio: float, punct_weight: float = 2.0) -> Dict:
    """Process a single file and return all metrics."""
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Analyze original (with ~ removed)
    original_stats = analyze_text(text.replace('~', ''), is_repaired=False)
    
    # Analyze repaired (with ~ present)
    repaired_stats = analyze_text(text, is_repaired=True)
    
    # Compute repair stats
    repair_stats = compute_repair_stats(original_stats, repaired_stats)
    
    # Compute %V from syllable statistics
    original_percent_v = compute_percent_v_from_stats(original_stats)
    repaired_percent_v = compute_percent_v_from_stats(repaired_stats)
    
    # Preprocess for acoustic metrics (ΔC, etc.)
    preprocessed_original = preprocess_text(text.replace('~', ''))
    preprocessed_repaired = preprocess_text(text)
    
    # Compute acoustic metrics (excluding %V)
    acoustic_original = compute_acoustic_metrics(preprocessed_original)
    acoustic_repaired = compute_acoustic_metrics(preprocessed_repaired)
    
    # Override %V with the correct value from syllable stats
    acoustic_original['percent_v'] = original_percent_v
    acoustic_repaired['percent_v'] = repaired_percent_v
    
    # Compute speech rate for repaired text
    speech_repaired = compute_speech_rate(preprocessed_repaired, repaired_stats, wpm, pause_ratio)
    
    # Compute pause metrics
    pause_metrics = compute_pause_metrics(text, repaired_stats)
    pause_durations = compute_pause_durations(pause_metrics, speech_repaired, pause_ratio, punct_weight)

    return {
        'file': filename,
        'original': {
            'stats': original_stats,
            'acoustic': acoustic_original
        },
        'repaired': {
            'stats': repaired_stats,
            'acoustic': acoustic_repaired,
            'speech': speech_repaired,
            'pause_metrics': pause_metrics,
            'pause_durations': pause_durations
        },
        'repair_stats': repair_stats
    }


def format_table(result: Dict) -> str:
    """Format results as human-readable table."""
    lines = []
    lines.append("="*80)
    lines.append(f"METRICS SUMMARY: {result['file']}")
    lines.append("="*80)
    
    # --- ORIGINAL TEXT ---
    lines.append("\n--- ORIGINAL TEXT ---")
    orig = result['original']
    
    # Syllable counts
    lines.append("\nSyllable types:")
    for typ in SYLLABLE_TYPES:
        count = orig['stats']['syllable_counts'].get(typ, 0)
        pct = orig['stats']['syllable_percentages'].get(typ, 0)
        if count > 0:
            lines.append(f"  {typ:6}: {count:4d} ({pct:5.2f}%)")
    
    # Mora statistics
    lines.append(f"\nMora statistics:")
    lines.append(f"  Mean morae per syllable: {orig['stats']['mora_stats']['mean']:.3f}")
    lines.append(f"  Std dev morae per syllable: {orig['stats']['mora_stats']['std']:.3f}")
    
    # Word statistics
    lines.append(f"\nWord statistics:")
    lines.append(f"  Total words: {orig['stats']['word_stats']['total_words']}")
    lines.append(f"  Syllables per word: {orig['stats']['word_stats']['syllables_per_word']['mean']:.3f} ± {orig['stats']['word_stats']['syllables_per_word']['std']:.3f}")
    lines.append(f"  Morae per word: {orig['stats']['word_stats']['morae_per_word']['mean']:.3f} ± {orig['stats']['word_stats']['morae_per_word']['std']:.3f}")
    
    # Acoustic metrics (original)
    lines.append(f"\nAcoustic metrics (original):")
    lines.append(f"  %V: {orig['acoustic']['percent_v']:.2f}%")
    lines.append(f"  ΔC: {orig['acoustic']['delta_c']:.4f}")
    lines.append(f"  MeanC: {orig['acoustic']['mean_interval']:.4f}")    
    lines.append(f"  VarcoC: {orig['acoustic']['varco_c']:.2f}")
    
    # --- REPAIRED TEXT ---
    lines.append("\n--- REPAIRED TEXT ---")
    rep = result['repaired']
    
    # Syllable counts
    lines.append("\nSyllable types:")
    for typ in SYLLABLE_TYPES:
        count = rep['stats']['syllable_counts'].get(typ, 0)
        pct = rep['stats']['syllable_percentages'].get(typ, 0)
        if count > 0:
            lines.append(f"  {typ:6}: {count:4d} ({pct:5.2f}%)")
    
    # Mora statistics
    lines.append(f"\nMora statistics:")
    lines.append(f"  Mean morae per syllable: {rep['stats']['mora_stats']['mean']:.3f}")
    lines.append(f"  Std dev morae per syllable: {rep['stats']['mora_stats']['std']:.3f}")
    
    # Word statistics
    lines.append(f"\nWord statistics:")
    lines.append(f"  Total words: {rep['stats']['word_stats']['total_words']}")
    lines.append(f"  Syllables per word: {rep['stats']['word_stats']['syllables_per_word']['mean']:.3f} ± {rep['stats']['word_stats']['syllables_per_word']['std']:.3f}")
    lines.append(f"  Morae per word: {rep['stats']['word_stats']['morae_per_word']['mean']:.3f} ± {rep['stats']['word_stats']['morae_per_word']['std']:.3f}")
    
    # Merge statistics
    lines.append(f"\nMerge statistics:")
    lines.append(f"  Merged words: {rep['stats']['merge_stats']['total_merged_words']}")
    lines.append(f"  Merged units: {rep['stats']['merge_stats']['merged_units']}")
    lines.append(f"  Average unit size: {rep['stats']['merge_stats']['avg_unit_size']:.2f} words")
    
    # Acoustic metrics (repaired)
    lines.append(f"\nAcoustic metrics (repaired):")
    lines.append(f"  %V: {rep['acoustic']['percent_v']:.2f}%")
    lines.append(f"  ΔC: {rep['acoustic']['delta_c']:.4f}")
    lines.append(f"  MeanC: {rep['acoustic']['mean_interval']:.4f}")    
    lines.append(f"  VarcoC: {rep['acoustic']['varco_c']:.2f}")
    
    # Speech rate
    lines.append(f"\nSpeech rate (repaired text only):")
    lines.append(f"  WPM: {rep['speech']['wpm']}")
    lines.append(f"  Pause ratio: {rep['speech']['pause_ratio']}%")
    lines.append(f"  SPS (speech): {rep['speech']['sps_speech']:.3f}")
    lines.append(f"  SPS (articulation): {rep['speech']['sps_articulation']:.3f}")
    lines.append(f"  Syllable duration: {rep['speech']['syllable_duration']:.3f}s")
    lines.append(f"  Mora duration: {rep['speech']['mora_duration']:.3f}s")
    lines.append(f"  Word duration: {rep['speech']['word_duration']:.3f}s")
    
    # Pause metrics
    pm = rep['pause_metrics']
    pd = rep['pause_durations']
    
    lines.append(f"\nPause metrics:")
    lines.append(f"  Spaces per syllable: {pm['spaces_per_syllable']:.3f}")
    lines.append(f"  Punctuation per syllable: {pm['punctuation_per_syllable']:.3f}")
    lines.append(f"  Total boundaries: {pm['total_boundaries']}")
    lines.append(f"  Pauseable boundaries: {pm['pauseable_boundaries']}")
    
    lines.append(f"\nPause duration allocation (total pause: {pd['pause_time_per_syllable']:.4f}s per syllable):")
    lines.append(f"  Punctuation weight: {pd['punct_weight']:.1f}× space")
    lines.append(f"  Space duration: {pd['space_duration']:.4f}s per space ({pd['space_percent']:.1f}% of pause)")
    lines.append(f"  Punctuation duration: {pd['punctuation_duration']:.4f}s per punctuation ({pd['punct_percent']:.1f}% of pause)")

    # --- REPAIR STATISTICS ---
    lines.append("\n--- REPAIR STATISTICS ---")
    rs = result['repair_stats']
    lines.append(f"  Repaired syllables: {rs['repaired_syllables']}")
    lines.append(f"  Repair rate: {rs['repair_rate']:.2f}%")
    lines.append(f"\n  Repair types:")
    for typ, count in rs['repair_types'].items():
        if count > 0:
            lines.append(f"    {typ:8}: {count:4d}")
    
    lines.append("\n" + "="*80)
    return '\n'.join(lines)


def format_csv(results: List[Dict], output_file: Path):
    """Format results as CSV with first column as filename."""
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("Metric," + ",".join([r['file'] for r in results]) + "\n")
        
        # Helper to add a row
        def add_row(name, values):
            f.write(f"{name}," + ",".join(str(v) for v in values) + "\n")
        
        # Original text metrics
        add_row("--- ORIGINAL TEXT ---", [""] * len(results))
        
        # Syllable counts
        for typ in SYLLABLE_TYPES:
            values = [r['original']['stats']['syllable_counts'].get(typ, 0) for r in results]
            add_row(f"count_{typ}", values)
        
        # Syllable percentages
        for typ in SYLLABLE_TYPES:
            values = [f"{r['original']['stats']['syllable_percentages'].get(typ, 0):.2f}" for r in results]
            add_row(f"pct_{typ}", values)
        
        # Mora stats
        values = [f"{r['original']['stats']['mora_stats']['mean']:.3f}" for r in results]
        add_row("mora_mean", values)
        values = [f"{r['original']['stats']['mora_stats']['std']:.3f}" for r in results]
        add_row("mora_std", values)
        
        # Word stats
        values = [r['original']['stats']['word_stats']['total_words'] for r in results]
        add_row("total_words", values)
        values = [f"{r['original']['stats']['word_stats']['syllables_per_word']['mean']:.3f}" for r in results]
        add_row("spw_mean", values)
        values = [f"{r['original']['stats']['word_stats']['syllables_per_word']['std']:.3f}" for r in results]
        add_row("spw_std", values)
        values = [f"{r['original']['stats']['word_stats']['morae_per_word']['mean']:.3f}" for r in results]
        add_row("mpw_mean", values)
        values = [f"{r['original']['stats']['word_stats']['morae_per_word']['std']:.3f}" for r in results]
        add_row("mpw_std", values)
        
        # Acoustic metrics (original)
        ac = [r['original']['acoustic'] for r in results]
        add_row("%V", [f"{a['percent_v']:.2f}" for a in ac])
        add_row("ΔC", [f"{a['delta_c']:.4f}" for a in ac])
        add_row("VarcoC", [f"{a['varco_c']:.2f}" for a in ac])
        
        # --- REPAIRED TEXT ---
        add_row("--- REPAIRED TEXT ---", [""] * len(results))
        
        # Syllable counts (repaired)
        for typ in SYLLABLE_TYPES:
            values = [r['repaired']['stats']['syllable_counts'].get(typ, 0) for r in results]
            add_row(f"rep_count_{typ}", values)
        
        # Syllable percentages (repaired)
        for typ in SYLLABLE_TYPES:
            values = [f"{r['repaired']['stats']['syllable_percentages'].get(typ, 0):.2f}" for r in results]
            add_row(f"rep_pct_{typ}", values)
        
        # Mora stats (repaired)
        values = [f"{r['repaired']['stats']['mora_stats']['mean']:.3f}" for r in results]
        add_row("rep_mora_mean", values)
        values = [f"{r['repaired']['stats']['mora_stats']['std']:.3f}" for r in results]
        add_row("rep_mora_std", values)
        
        # Word stats (repaired)
        values = [r['repaired']['stats']['word_stats']['total_words'] for r in results]
        add_row("rep_total_words", values)
        values = [f"{r['repaired']['stats']['word_stats']['syllables_per_word']['mean']:.3f}" for r in results]
        add_row("rep_spw_mean", values)
        values = [f"{r['repaired']['stats']['word_stats']['syllables_per_word']['std']:.3f}" for r in results]
        add_row("rep_spw_std", values)
        values = [f"{r['repaired']['stats']['word_stats']['morae_per_word']['mean']:.3f}" for r in results]
        add_row("rep_mpw_mean", values)
        values = [f"{r['repaired']['stats']['word_stats']['morae_per_word']['std']:.3f}" for r in results]
        add_row("rep_mpw_std", values)
        
        # Merge stats
        values = [r['repaired']['stats']['merge_stats']['total_merged_words'] for r in results]
        add_row("merged_words", values)
        values = [r['repaired']['stats']['merge_stats']['merged_units'] for r in results]
        add_row("merged_units", values)
        values = [f"{r['repaired']['stats']['merge_stats']['avg_unit_size']:.2f}" for r in results]
        add_row("avg_unit_size", values)
        
        # Acoustic metrics (repaired)
        ac_rep = [r['repaired']['acoustic'] for r in results]
        add_row("rep_%V", [f"{a['percent_v']:.2f}" for a in ac_rep])
        add_row("rep_ΔC", [f"{a['delta_c']:.4f}" for a in ac_rep])
        add_row("rep_VarcoC", [f"{a['varco_c']:.2f}" for a in ac_rep])
        
        # Speech rate (repaired)
        sp_rep = [r['repaired']['speech'] for r in results]
        add_row("sps_speech", [f"{s['sps_speech']:.3f}" for s in sp_rep])
        add_row("sps_articulation", [f"{s['sps_articulation']:.3f}" for s in sp_rep])
        add_row("syllable_duration", [f"{s['syllable_duration']:.3f}" for s in sp_rep])
        add_row("mora_duration", [f"{s['mora_duration']:.3f}" for s in sp_rep])
        add_row("word_duration", [f"{s['word_duration']:.3f}" for s in sp_rep])
        
        # Pause metrics
        add_row("--- PAUSE METRICS ---", [""] * len(results))
        
        for r in results:
            pm = r['repaired']['pause_metrics']
            pd = r['repaired']['pause_durations']
            
            values = [f"{pm['spaces_per_syllable']:.3f}" for r in results]
            add_row("spaces_per_syllable", values)
            values = [f"{pm['punctuation_per_syllable']:.3f}" for r in results]
            add_row("punct_per_syllable", values)
            values = [f"{pd['space_duration']:.4f}" for r in results]
            add_row("space_duration", values)
            values = [f"{pd['punctuation_duration']:.4f}" for r in results]
            add_row("punct_duration", values)
            values = [f"{pd['space_percent']:.1f}" for r in results]
            add_row("space_percent", values)
            values = [f"{pd['punct_percent']:.1f}" for r in results]
            add_row("punct_percent", values)
            break  # Only do once since we're looping over results
        
        # --- REPAIR STATISTICS ---
        add_row("--- REPAIR STATISTICS ---", [""] * len(results))
        
        values = [r['repair_stats']['repaired_syllables'] for r in results]
        add_row("repaired_syllables", values)
        values = [f"{r['repair_stats']['repair_rate']:.2f}" for r in results]
        add_row("repair_rate", values)
        
        for typ in SYLLABLE_TYPES:
            values = [r['repair_stats']['repair_types'].get(typ, 0) for r in results]
            add_row(f"repair_{typ}", values)


# ------------------------------------------------------------
# Unit tests
# ------------------------------------------------------------
def test_small_text():
    """Test syllable counting on a small sample."""
    print("\n" + "="*80)
    print("TEST: Small text syllable counting")
    print("="*80)
    
    test_text = "šar gi·mir+dad~·mē bā·nû kib·rā~·ti"
    
    # Expected original counts (without repairs)
    expected_original = {
        'CV': 2,   # gi, ti
        'CVC': 4,  # šar, mir, dad, kib
        'CVV': 4,  # mē, bā, nû, rā
        'total': 10
    }
    
    # Expected repaired counts (with repairs)
    expected_repaired = {
        'CV': 2,      # gi, ti
        'CVC': 3,     # šar, mir, kib
        'CVV': 3,     # mē, bā, nû
        'CVC:': 1,    # dad~
        'CVV:': 1,    # rā~
        'total': 10
    }
    
    print(f"\nTest text: {test_text}")
    
    # Test original
    print("\n--- ORIGINAL (without ~) ---")
    original_stats = analyze_text(test_text.replace('~', ''), is_repaired=False)
    
    print("Syllable counts:")
    for typ in ['CV', 'CVC', 'CVV', 'CVVC', 'VC', 'V', 'VV', 'VVC']:
        count = original_stats['syllable_counts'].get(typ, 0)
        if count > 0:
            print(f"  {typ}: {count}")
    
    # Verify original counts
    for typ, expected in expected_original.items():
        if typ == 'total':
            continue
        actual = original_stats['syllable_counts'].get(typ, 0)
        if actual != expected:
            print(f"  ❌ [{typ}]: got {actual}, expected {expected}")
    
    total = sum(original_stats['syllable_counts'].values())
    if total != expected_original['total']:
        print(f"  ❌ total: got {total}, expected {expected_original['total']}")
    
    # Test repaired
    print("\n--- REPAIRED (with ~) ---")
    repaired_stats = analyze_text(test_text, is_repaired=True)
    
    print("Syllable counts:")
    for typ in ['CV', 'CVC', 'CVV', 'CVC:', 'CVV:', 'VV:', 'VV:C' ,'CVV:', 'CVC:' ]:
        count = repaired_stats['syllable_counts'].get(typ, 0)
        if count > 0:
            print(f"  [{typ}]: {count}")
    
    # Verify repaired counts
    for typ, expected in expected_repaired.items():
        if typ == 'total':
            continue
        actual = repaired_stats['syllable_counts'].get(typ, 0)
        if actual != expected:
            print(f"  ❌ [{typ}]: got {actual}, expected {expected}")
    
    total = sum(repaired_stats['syllable_counts'].values())
    if total != expected_repaired['total']:
        print(f"  ❌ total: got {total}, expected {expected_repaired['total']}")

def debug_mean_calculation(text: str, label: str):
    """Debug mean interval calculation."""
    print(f"\n--- DEBUG MeanC for {label} ---")
    print(f"Text: {text}")
    
    preprocessed = preprocess_text(text)
    print(f"Preprocessed: {preprocessed}")
    
    # Get segments and distances
    consonants, vowels = extract_segments(preprocessed)
    print(f"Consonants: {consonants}")
    print(f"Vowels after: {vowels}")
    
    distances = compute_consonant_distances(consonants, vowels)
    print(f"Distances: {distances}")
    
    if distances:
        mean = sum(distances) / len(distances)
        print(f"MeanC = {mean:.4f}")
    else:
        print("No distances")
    
    return distances

def run_tests():
    """Run comprehensive unit tests."""
    print("\n" + "="*80)
    print("METRICS CALCULATOR — COMPREHENSIVE UNIT TESTS")
    print("="*80)
    
    tests_passed = 0
    tests_total = 0
    
    test_small_text()

    # ===== TEST 1: Word Pattern Matching =====
    print("\n--- Test 1: Word Pattern Matching ---")
    tests_total += 1
    
    word_pattern = build_word_pattern()
    # Create anchored version for testing whole words
    full_word_pattern = re.compile(f'^(?:{word_pattern.pattern})$')
    
    test_cases = [
        ('at·tā', True),
        ('ā·lik', True),
        ('maḫ·rim~-ma', True),
        ('i·lū~', True),
        ('~a', True),
        ('ana+kâ·ša', True),
        ('ka+', False),
        ('$word', False),
        ('word$', False),
        ('_word', False),
        ('word+', False),
    ]
    
    passed = True
    for inp, should_match in test_cases:
        match = full_word_pattern.match(inp)
        if bool(match) != should_match:
            print(f"  ❌ full_word_pattern.match('{inp}') = {bool(match)}, expected {should_match}")
            passed = False
    if passed:
        print("  ✅ All word pattern tests passed")
        tests_passed += 1
    
    # ===== TEST 2: Tokenizer =====
    print("\n--- Test 2: Tokenizer ---")
    tests_total += 1
    
    test_cases = [
        {
            'name': 'Simple line',
            'input': 'at·tā ā·lik',
            'expected': [
                ('WORD', 'at·tā'),
                ('SPACES', ' '),
                ('WORD', 'ā·lik')
            ]
        },
        {
            'name': 'Line with punctuation',
            'input': 'at·tā, ā·lik!',
            'expected': [
                ('WORD', 'at·tā'),
                ('PUNCT', ','),
                ('SPACES', ' '),
                ('WORD', 'ā·lik'),
                ('PUNCT', '!')
            ]
        },
        {
            'name': 'Line with merged words',
            'input': 'ana+kâ·ša lu·ṣī-ma',
            'expected': [
                ('WORD', 'ana+kâ·ša'),
                ('SPACES', ' '),
                ('WORD', 'lu·ṣī-ma')
            ]
        },
        {
            'name': 'Line with multiple spaces',
            'input': 'at·tā   ā·lik',
            'expected': [
                ('WORD', 'at·tā'),
                ('SPACES', '   '),
                ('WORD', 'ā·lik')
            ]
        },
        {
            'name': 'Line with leading spaces',
            'input': '  at·tā ā·lik',
            'expected': [
                ('SPACES', '  '),
                ('WORD', 'at·tā'),
                ('SPACES', ' '),
                ('WORD', 'ā·lik')
            ]
        },
        {
            'name': 'Line with trailing spaces',
            'input': 'at·tā ā·lik  ',
            'expected': [
                ('WORD', 'at·tā'),
                ('SPACES', ' '),
                ('WORD', 'ā·lik'),
                ('SPACES', '  ')
            ]
        },
    ]
    
    passed = True
    for tc in test_cases:
        tokens = tokenize_line(tc['input'], word_pattern)
        if tokens != tc['expected']:
            print(f"  ❌ {tc['name']}: got {tokens}, expected {tc['expected']}")
            passed = False
    if passed:
        print("  ✅ All tokenizer tests passed")
        tests_passed += 1
    
    # ===== TEST 3: Word Processing =====
    print("\n--- Test 3: Word Processing ---")
    tests_total += 1
    
    test_cases = [
        ('rā~', 'rà'),
        ('nā~š', 'nàš'),
        ('bī~t', 'bìt'),
        ('mâ~r', 'màr'),
        ('kû~n', 'kùn'),
        ('at·tā', 'ʾat·tā'),
        ('ā·lik', 'ʾā·lik'),
        ('maḫ·rim~-ma', 'maḫ·rim:-ma'),
        ('i·lū~', 'ʾi·lù'),
        ('~a', ':a'),
        ('k~a', 'k:a'),
        ('dad~', 'dad:'),
    ]
    
    passed = True
    for inp, expected in test_cases:
        result = process_word(inp)
        if result != expected:
            print(f"  ❌ process_word('{inp}') = '{result}', expected '{expected}'")
            passed = False
    if passed:
        print("  ✅ All word processing tests passed")
        tests_passed += 1
    
    # ===== TEST 4: Full Preprocessing =====
    print("\n--- Test 4: Full Preprocessing ---")
    tests_total += 1
    
    test_cases = [
        {
            'name': 'Simple line',
            'input': 'at·tā ā·lik',
            'expected': 'ʾat·tā$ʾā·lik'
        },
        {
            'name': 'Line with repairs',
            'input': 'maḫ·rim~-ma i·lū~',
            'expected': 'maḫ·rim:-ma$ʾi·lù'
        },
        {
            'name': 'Complex line with punctuation',
            'input': 'at·tā, ā·lik! maḫ·rim~-ma || i·lū~ ···',
            'expected': 'ʾat·tā$ʾā·lik$maḫ·rim:-ma$ʾi·lù$'
        },
        {
            'name': 'Line with merged words',
            'input': 'ana+kâ·ša lu·ṣī-ma',
            'expected': 'ʾana+kâ·ša$lu·ṣī-ma'
        },
        {
            'name': 'Line with multiple spaces',
            'input': 'at·tā   ā·lik',
            'expected': 'ʾat·tā$ʾā·lik'
        },
        {
            'name': 'Line with leading spaces',
            'input': '  at·tā ā·lik',
            'expected': 'ʾat·tā$ʾā·lik'
        },
        {
            'name': 'Line with trailing spaces',
            'input': 'at·tā ā·lik  ',
            'expected': 'ʾat·tā$ʾā·lik'
        },
    ]
    
    passed = True
    for tc in test_cases:
        result = preprocess_text(tc['input'])
        if result != tc['expected']:
            print(f"  ❌ {tc['name']}: '{result}', expected '{tc['expected']}'")
            passed = False
    if passed:
        print("  ✅ All preprocessing tests passed")
        tests_passed += 1
    
    # ===== TEST 5: Segment Extraction =====
    print("\n--- Test 5: Segment Extraction ---")
    tests_total += 1
    
    test_cases = [
        {
            'name': 'masta (no repair)',
            'input': 'mas·ta',
            'expected_consonants': ['m', 's', 't'],
            'expected_vowels': ['a', '', 'a']
        },
        {
            'name': 'mas:ta (with gemination)',
            'input': 'mas~·ta',
            'expected_consonants': ['m', 's', 't'],
            'expected_vowels': ['a', ':', 'a']
        },
        {
            'name': 'ʾana',
            'input': 'a·na',
            'expected_consonants': ['ʾ', 'n'],
            'expected_vowels': ['a', 'a']
        },
        {
            'name': 'Word with onset gemination',
            'input': 'k~a',
            'expected_consonants': ['k'],
            'expected_vowels': [':a']
        },
        {
            'name': 'Word with coda gemination',
            'input': 'dad~',
            'expected_consonants': ['d', 'd'],
            'expected_vowels': ['a', ':']
        },
        {
            'name': 'Word with vowel lengthening',
            'input': 'rā~',
            'expected_consonants': ['r'],
            'expected_vowels': ['à']
        },
    ]
    
    passed = True
    for tc in test_cases:
        preprocessed = preprocess_text(tc['input'])
        consonants, vowels = extract_segments(preprocessed)
        if consonants != tc['expected_consonants'] or vowels != tc['expected_vowels']:
            print(f"  ❌ {tc['name']}: got cons={consonants}, vowels={vowels}, "
                  f"expected cons={tc['expected_consonants']}, vowels={tc['expected_vowels']}")
            passed = False
    if passed:
        print("  ✅ All segment extraction tests passed")
        tests_passed += 1
    
    # ===== TEST 6: Distance Calculation =====
    print("\n--- Test 6: Distance Calculation ---")
    tests_total += 1
    
    test_cases = [
        {
            'name': 'masta (no repair)',
            'input': 'mas·ta',
            'expected_distances': [1, 0, 1]
        },
        {
            'name': 'mas:ta (with gemination)',
            'input': 'mas~·ta',
            'expected_distances': [1, 1, 1]
        },
        {
            'name': 'ʾana',
            'input': 'a·na',
            'expected_distances': [1, 1]
        },
        {
            'name': 'Word with onset gemination',
            'input': 'k~a',
            'expected_distances': [2]
        },
        {
            'name': 'Word with coda gemination',
            'input': 'dad~',
            'expected_distances': [1, 1]
        },
        {
            'name': 'Word with vowel lengthening',
            'input': 'rā~',
            'expected_distances': [3]
        },
    ]
    
    passed = True
    for tc in test_cases:
        preprocessed = preprocess_text(tc['input'])
        consonants, vowels = extract_segments(preprocessed)
        distances = compute_consonant_distances(consonants, vowels)
        if distances != tc['expected_distances']:
            print(f"  ❌ {tc['name']}: distances {distances}, expected {tc['expected_distances']}")
            passed = False
    if passed:
        print("  ✅ All distance tests passed")
        tests_passed += 1

    # ===== TEST 7: Pause Metrics =====
    print("\n--- Test 7: Pause Metrics ---")
    tests_total += 1
    
    test_text = "šar gi·mir+dad~·mē || bā·nû kib·rā~·ti ···"
    stats = analyze_text(test_text, is_repaired=True)
    pause_metrics = compute_pause_metrics(test_text, stats)

    # Expected counts:
    # - spaces: between šar and gi.mir_dad~.mē, between bā.nû and kib.rā~.ti = 2 spaces
    # - punctuation: || and ... = 2 punctuation units
    # - merged boundaries: _ in gi.mir_dad~.mē = 1

    passed = True
    if pause_metrics['raw_counts']['spaces'] != 2:
        print(f"  ❌ Space count: got {pause_metrics['raw_counts']['spaces']}, expected 2")
        passed = False
    if pause_metrics['raw_counts']['punctuation'] != 2:
        print(f"  ❌ Punctuation count: got {pause_metrics['raw_counts']['punctuation']}, expected 2")
        passed = False
    if pause_metrics['raw_counts']['merged_boundaries'] != 1:
        print(f"  ❌ Merged boundaries: got {pause_metrics['raw_counts']['merged_boundaries']}, expected 1")
        passed = False

    if passed:
        print("  ✅ All pause metrics tests passed")
        tests_passed += 1
    else:
        print(f"  Raw counts: {pause_metrics['raw_counts']}")

    # Summary
    print(f"\n{'='*80}")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"{'='*80}\n")
    
    return tests_passed == tests_total


