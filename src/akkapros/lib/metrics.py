#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Metrics Calculator
Version: 2.0.0

Computes comprehensive metrics from Akkadian text with proper handling of:
- Vowel length: short (a), long (ā/â), extra-long (à/ì/ù/è)
- Consonant gemination: marked with : (e.g., mas:ta)
- Glottal stops: ʾ for initial vowels
- Distance-based ΔC calculation
- Punctuation boundaries marked with $
- Pause metrics for punctuation only (short vs long pause classes)
"""

import re
import random
import statistics
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from collections import Counter
import math

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
    WORD_LINKER,
    SHORT_VOWELS,
    LONG_VOWELS,
)

HYPHEN = '-'
EXTRA_LONG_VOWELS = set('àìùè')

# ------------------------------------------------------------
# Phonetic inventory — Akkadian core
# ------------------------------------------------------------

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

# Pause class configuration (scientific, explicit, and centralized)
# Short pause punctuation: minor/inner punctuation marks.
SHORT_PAUSE_PUNCTUATION_CHARS = {
    ',', ';', ':', '—', '–', '…',
    '(', ')', '«', '»', '“', '”', '‘', '’', '"', "'",
    '/', '\\', '&', '†', '‡', '|'
}
# Standalone ellipsis (surrounded by spaces/newline/EOF) is treated as short,
# typically representing missing words in source editions.
SHORT_PAUSE_PUNCTUATION_PATTERNS = (
    r'\s\.\.\.(?=\s|$)',
    r'\s…(?=\s|$)',
)

# Long pause punctuation: final/major boundaries.
LONG_PAUSE_PUNCTUATION_CHARS = {
    '.', '?', '!', '[', ']', '{', '}', '<', '>', '-', '*', '+'
}
# Ellipsis attached directly to a word ending is sentence-final/major.
LONG_PAUSE_PUNCTUATION_PATTERNS = (
    r'^\.\.\.',
    r'^…',
)
LONG_PAUSE_INCLUDES_NEWLINE = True
LONG_PAUSE_INCLUDES_FINAL_EOF = True

# Pause weights: long is expressed relative to short.
SHORT_PAUSE_PUNCT_WEIGHT = 1.0
DEFAULT_LONG_PAUSE_PUNCT_WEIGHT = 2.0

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
    
    # CLASS_UNIT_WORD_SEPARATOR := WORD_LINKER
    unit_sep = WORD_LINKER
    
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
        if WORD_LINKER in word:
            merged_units += 1
            total_merged_words += word.count(WORD_LINKER) + 1
    
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


def compute_percent_v_with_pauses(percent_v_articulate: float, pause_ratio: float) -> float:
    """Convert articulate %V to normal-speech %V by adding pause morae to denominator.

    If pause_ratio is 35, total morae are scaled by x1.35, so %V is divided by 1.35.
    """
    scale = 1.0 + (pause_ratio / 100.0)
    if scale <= 0:
        return percent_v_articulate
    return percent_v_articulate / scale

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
        syllables = re.split(rf'[\{SYL_SEPARATOR}\{HYPHEN}\{WORD_LINKER}]+', word)

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
        if c in (WORD_BOUNDARY, SYL_SEPARATOR, HYPHEN, WORD_LINKER):
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
            'percent_v_articulate': 0.0,
            'percent_v_speech': 0.0,
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
        'percent_v_articulate': percent_v,
        'percent_v_speech': percent_v,
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

    Connected-speech rule for acoustic distances:
    - spaces and WORD_LINKER (+) do not create WORD_BOUNDARY ($)
    - punctuation creates WORD_BOUNDARY ($)
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
def _gap_has_long_pause(gap: str) -> bool:
    """Return True when a boundary gap contains long-pause punctuation cues."""
    if LONG_PAUSE_INCLUDES_NEWLINE and '\n' in gap:
        return True
    if any(re.search(pattern, gap) for pattern in LONG_PAUSE_PUNCTUATION_PATTERNS):
        return True
    # Standalone ellipsis tokens (space + .../… + space|EOF) are short pauses;
    # remove them before char-level long-class checks.
    sanitized_gap = re.sub(r'(?<=\s)\.\.\.(?=\s|$)', '', gap)
    sanitized_gap = re.sub(r'(?<=\s)…(?=\s|$)', '', sanitized_gap)
    return any(ch in LONG_PAUSE_PUNCTUATION_CHARS for ch in sanitized_gap)


def _gap_has_short_pause(gap: str) -> bool:
    """Return True when a boundary gap contains short-pause punctuation cues."""
    if any(re.search(pattern, gap) for pattern in SHORT_PAUSE_PUNCTUATION_PATTERNS):
        return True
    punctuation_chars = [ch for ch in gap if (not ch.isspace()) and ch != WORD_LINKER]
    if not punctuation_chars:
        return False
    if _gap_has_long_pause(gap):
        return False
    return any(ch in SHORT_PAUSE_PUNCTUATION_CHARS for ch in punctuation_chars)


def _gap_has_any_punctuation(gap: str) -> bool:
    """Return True when a gap contains at least one non-space, non-linker marker."""
    return any((not ch.isspace()) and ch != WORD_LINKER for ch in gap)


def count_spaces_and_punctuation(text: str) -> Dict:
    """
    Count pause events between words.

    In the updated model, spaces and WORD_LINKER do not create pauses.
    Only punctuation creates pauses, split into short and long classes.
    """
    word_pattern = build_word_pattern()
    
    spaces = 0  # Kept for compatibility; always remains 0 in pause model.
    punctuation = 0
    short_punctuation = 0
    long_punctuation = 0
    defaulted_long_punctuation = 0
    merged_boundaries = 0
    
    i = 0
    n = len(text)
    last_was_word = False
    
    while i < n:
        # First, try to match a word
        match = word_pattern.match(text[i:])
        if match:
            word = match.group()
            word_underscores = word.count(WORD_LINKER)
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
            
            # Determine pause class for the gap.
            gap = text[start:i]
            if _gap_has_long_pause(gap):
                long_punctuation += 1
                punctuation += 1
            elif _gap_has_short_pause(gap):
                short_punctuation += 1
                punctuation += 1
            elif _gap_has_any_punctuation(gap):
                # Fallback policy: unknown punctuation defaults to LONG pause.
                long_punctuation += 1
                defaulted_long_punctuation += 1
                punctuation += 1
            else:
                # Pure spacing/linking gap: connected speech with no pause.
                pass
            
            last_was_word = False
        else:
            # Skip anything at start (shouldn't happen in valid text)
            i += 1

    # Treat file end after a final word as an implicit line-end pause.
    if LONG_PAUSE_INCLUDES_FINAL_EOF and last_was_word:
        long_punctuation += 1
        punctuation += 1
    
    return {
        'spaces': spaces,
        'punctuation': punctuation,
        'short_punctuation': short_punctuation,
        'long_punctuation': long_punctuation,
        'defaulted_long_punctuation': defaulted_long_punctuation,
        'merged_boundaries': merged_boundaries
    }


def compute_pause_metrics(text: str, stats: Dict) -> Dict:
    """
    Compute punctuation pause ratios per syllable.
    
    Args:
        text: Original text (before preprocessing)
        stats: Statistics from analyze_text (contains syllable counts)
    
    Returns:
        {
            'short_punctuation_per_syllable': float,
            'long_punctuation_per_syllable': float,
            'total_boundaries': int,
            'pauseable_boundaries': int,
            'short_pauseable_boundaries': int,
            'long_pauseable_boundaries': int
        }
    """
    counts = count_spaces_and_punctuation(text)
    total_syllables = stats['total_syllables']
    
    if total_syllables == 0:
        return {
            'spaces_per_syllable': 0,
            'punctuation_per_syllable': 0,
            'short_punctuation_per_syllable': 0,
            'long_punctuation_per_syllable': 0,
            'total_boundaries': 0,
            'pauseable_boundaries': 0,
            'short_pauseable_boundaries': 0,
            'long_pauseable_boundaries': 0,
            'raw_counts': counts
        }
    
    spaces_per_syllable = 0.0
    punctuation_per_syllable = counts['punctuation'] / total_syllables
    short_punctuation_per_syllable = counts['short_punctuation'] / total_syllables
    long_punctuation_per_syllable = counts['long_punctuation'] / total_syllables
    total_boundaries = counts['spaces'] + counts['punctuation'] + counts['merged_boundaries']
    pauseable_boundaries = counts['punctuation']  # spaces/linkers do not pause
    
    return {
        'spaces_per_syllable': spaces_per_syllable,
        'punctuation_per_syllable': punctuation_per_syllable,
        'short_punctuation_per_syllable': short_punctuation_per_syllable,
        'long_punctuation_per_syllable': long_punctuation_per_syllable,
        'total_boundaries': total_boundaries,
        'pauseable_boundaries': pauseable_boundaries,
        'short_pauseable_boundaries': counts['short_punctuation'],
        'long_pauseable_boundaries': counts['long_punctuation'],
        'raw_counts': counts
    }


def compute_pause_durations(
    pause_metrics: Dict,
    speech_metrics: Dict,
    pause_ratio: float,
    long_punct_weight: float = DEFAULT_LONG_PAUSE_PUNCT_WEIGHT,
) -> Dict:
    """
    Compute duration per short and long punctuation pause based on pause ratio.
    
    Args:
        pause_metrics: Output from compute_pause_metrics
        speech_metrics: Output from compute_speech_rate
        pause_ratio: Total pause ratio percentage
        long_punct_weight: Relative weight for long punctuation pauses,
            normalized by short pause weight (=1.0)
    
    Returns:
        Dictionary with space and punctuation durations
    """
    # Get metrics
    short_per_syllable = pause_metrics['short_punctuation_per_syllable']
    long_per_syllable = pause_metrics['long_punctuation_per_syllable']
    short_event_count = pause_metrics['raw_counts']['short_punctuation']
    long_event_count = pause_metrics['raw_counts']['long_punctuation']
    
    # Speech metrics
    syllable_duration = speech_metrics['syllable_duration']
    sps_speech = speech_metrics['sps_speech']
    
    # Total time per syllable including pauses
    total_time_per_syllable = 1 / sps_speech
    
    # Pause time per syllable
    pause_time_per_syllable = total_time_per_syllable - syllable_duration
    
    # Distribute pause time using short/long punctuation weights (initial model).
    total_pause_units = (
        short_per_syllable * SHORT_PAUSE_PUNCT_WEIGHT
        + long_per_syllable * long_punct_weight
    )
    if total_pause_units == 0:
        initial_short_duration = 0.0
        initial_long_duration = 0.0
        initial_short_contribution = 0.0
        initial_long_contribution = 0.0
    else:
        unit_duration = pause_time_per_syllable / total_pause_units
        initial_short_duration = unit_duration * SHORT_PAUSE_PUNCT_WEIGHT
        initial_long_duration = unit_duration * long_punct_weight
        initial_short_contribution = short_per_syllable * initial_short_duration
        initial_long_contribution = long_per_syllable * initial_long_duration

    # Correct short pause duration to nearest multiple of 2 morae.
    mora_duration = speech_metrics.get('mora_duration', 0.0)
    if mora_duration > 0 and initial_short_duration > 0:
        short_mora_ratio = initial_short_duration / mora_duration
        corrected_short_mora_multiple = int(round(short_mora_ratio / 2.0) * 2)
        corrected_short_duration = corrected_short_mora_multiple * mora_duration
    else:
        short_mora_ratio = 0.0
        corrected_short_mora_multiple = 0
        corrected_short_duration = initial_short_duration

    # Keep total punctuation pause time conserved across event counts.
    initial_total_from_counts = (
        initial_short_duration * short_event_count
        + initial_long_duration * long_event_count
    )

    if long_event_count > 0:
        corrected_long_duration = (
            initial_total_from_counts - corrected_short_duration * short_event_count
        ) / long_event_count
        if corrected_long_duration < 0:
            corrected_long_duration = 0.0
    else:
        corrected_long_duration = initial_long_duration

    corrected_short_contribution = short_per_syllable * corrected_short_duration
    corrected_long_contribution = long_per_syllable * corrected_long_duration

    if corrected_short_duration > 0:
        corrected_long_weight = corrected_long_duration / corrected_short_duration
    else:
        corrected_long_weight = 0.0
    
    return {
        # Initial model outputs
        'initial_short_punctuation_duration': initial_short_duration,
        'initial_long_punctuation_duration': initial_long_duration,
        'initial_short_punctuation_contribution': initial_short_contribution,
        'initial_long_punctuation_contribution': initial_long_contribution,
        'initial_short_punctuation_percent': (initial_short_contribution / pause_time_per_syllable * 100) if pause_time_per_syllable > 0 else 0,
        'initial_long_punctuation_percent': (initial_long_contribution / pause_time_per_syllable * 100) if pause_time_per_syllable > 0 else 0,
        'short_punct_weight': SHORT_PAUSE_PUNCT_WEIGHT,
        'initial_long_punct_weight': long_punct_weight,
        # Corrected model outputs
        'short_mora_ratio_initial': short_mora_ratio,
        'corrected_short_mora_multiple': corrected_short_mora_multiple,
        'corrected_short_punctuation_duration': corrected_short_duration,
        'corrected_long_punctuation_duration': corrected_long_duration,
        'corrected_short_punctuation_contribution': corrected_short_contribution,
        'corrected_long_punctuation_contribution': corrected_long_contribution,
        'corrected_short_punctuation_percent': (corrected_short_contribution / pause_time_per_syllable * 100) if pause_time_per_syllable > 0 else 0,
        'corrected_long_punctuation_percent': (corrected_long_contribution / pause_time_per_syllable * 100) if pause_time_per_syllable > 0 else 0,
        'corrected_long_punct_weight': corrected_long_weight,
        # Shared
        'total_pause_time': pause_time_per_syllable,
        'pause_time_per_syllable': pause_time_per_syllable,
        'short_event_count': short_event_count,
        'long_event_count': long_event_count,
        # Backward-compatible aliases removed: keep canonical field names only
    }


# ------------------------------------------------------------
# Main processing
# ------------------------------------------------------------
def process_file(
    filename: str,
    wpm: float,
    pause_ratio: float,
    long_punct_weight: float = DEFAULT_LONG_PAUSE_PUNCT_WEIGHT,
) -> Dict:
    """Process a single file and return all metrics."""
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    return process_filetext(text, wpm, pause_ratio, long_punct_weight, filename)


def process_filetext(
    text: str,
    wpm: float,
    pause_ratio: float,
    long_punct_weight: float = DEFAULT_LONG_PAUSE_PUNCT_WEIGHT,
    filesrc: str = 'in-memory',
) -> Dict:

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
    
    # Override %V with mora-based values and expose both speaking conditions.
    acoustic_original['percent_v'] = original_percent_v
    acoustic_original['percent_v_articulate'] = original_percent_v
    acoustic_original['percent_v_speech'] = compute_percent_v_with_pauses(original_percent_v, pause_ratio)
    acoustic_repaired['percent_v'] = repaired_percent_v
    acoustic_repaired['percent_v_articulate'] = repaired_percent_v
    acoustic_repaired['percent_v_speech'] = compute_percent_v_with_pauses(repaired_percent_v, pause_ratio)
    
    # Compute speech rate for repaired text
    speech_repaired = compute_speech_rate(preprocessed_repaired, repaired_stats, wpm, pause_ratio)
    
    # Compute pause metrics
    pause_metrics = compute_pause_metrics(text, repaired_stats)
    pause_durations = compute_pause_durations(
        pause_metrics,
        speech_repaired,
        pause_ratio,
        long_punct_weight,
    )

    return {
        'file': filesrc,
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


def format_table(result: Dict, run_context: Dict | None = None) -> str:
    """Format results as human-readable table."""
    lines = []
    lines.append("="*80)
    lines.append(f"METRICS SUMMARY: {result['file']}")
    lines.append("="*80)

    if run_context:
        lines.append("\n--- RUN CONFIGURATION ---")
        for key in sorted(run_context.keys()):
            lines.append(f"  {key}: {run_context[key]}")
    
    # --- ORIGINAL TEXT ---
    lines.append("\n--- ORIGINAL TEXT ---")
    orig = result['original']
    
    # Syllable counts
    lines.append("\nSyllable types:")
    for typ in SYLLABLE_TYPES:
        count = orig['stats']['syllable_counts'].get(typ, 0)
        pct = orig['stats']['syllable_percentages'].get(typ, 0)
        if count > 0:
            lines.append(f"  {typ:6}: {count:4d} syllables ({pct:5.2f}%)")
    
    # Mora statistics
    lines.append(f"\nMora statistics:")
    lines.append(f"  Mean morae per syllable: {orig['stats']['mora_stats']['mean']:.3f} mora/syllable")
    lines.append(f"  Std dev morae per syllable: {orig['stats']['mora_stats']['std']:.3f} mora/syllable")
    
    # Word statistics
    lines.append(f"\nWord statistics:")
    lines.append(f"  Total words: {orig['stats']['word_stats']['total_words']} words")
    lines.append(f"  Syllables per word: {orig['stats']['word_stats']['syllables_per_word']['mean']:.3f} ± {orig['stats']['word_stats']['syllables_per_word']['std']:.3f} syllable/word")
    lines.append(f"  Morae per word: {orig['stats']['word_stats']['morae_per_word']['mean']:.3f} ± {orig['stats']['word_stats']['morae_per_word']['std']:.3f} mora/word")
    
    # Acoustic metrics (original)
    lines.append(f"\nAcoustic metrics (original):")
    lines.append(f"  %V (articulate): {orig['acoustic']['percent_v_articulate']:.2f}%")
    lines.append(f"  %V (normal speech, incl. pauses): {orig['acoustic']['percent_v_speech']:.2f}%")
    lines.append(f"  ΔC: {orig['acoustic']['delta_c']:.4f} mora (consonant-interval SD)")
    lines.append(f"  MeanC: {orig['acoustic']['mean_interval']:.4f} mora (mean consonant interval)")
    lines.append(f"  VarcoC: {orig['acoustic']['varco_c']:.2f} %")
    
    # --- REPAIRED TEXT ---
    lines.append("\n--- REPAIRED TEXT ---")
    rep = result['repaired']
    
    # Syllable counts
    lines.append("\nSyllable types:")
    for typ in SYLLABLE_TYPES:
        count = rep['stats']['syllable_counts'].get(typ, 0)
        pct = rep['stats']['syllable_percentages'].get(typ, 0)
        if count > 0:
            lines.append(f"  {typ:6}: {count:4d} syllables ({pct:5.2f}%)")
    
    # Mora statistics
    lines.append(f"\nMora statistics:")
    lines.append(f"  Mean morae per syllable: {rep['stats']['mora_stats']['mean']:.3f} mora/syllable")
    lines.append(f"  Std dev morae per syllable: {rep['stats']['mora_stats']['std']:.3f} mora/syllable")
    
    # Word statistics
    lines.append(f"\nWord statistics:")
    lines.append(f"  Total words: {rep['stats']['word_stats']['total_words']} words")
    lines.append(f"  Syllables per word: {rep['stats']['word_stats']['syllables_per_word']['mean']:.3f} ± {rep['stats']['word_stats']['syllables_per_word']['std']:.3f} syllable/word")
    lines.append(f"  Morae per word: {rep['stats']['word_stats']['morae_per_word']['mean']:.3f} ± {rep['stats']['word_stats']['morae_per_word']['std']:.3f} mora/word")
    
    # Merge statistics
    lines.append(f"\nMerge statistics:")
    lines.append(f"  Merged words: {rep['stats']['merge_stats']['total_merged_words']} words")
    lines.append(f"  Merged units: {rep['stats']['merge_stats']['merged_units']} units")
    lines.append(f"  Average unit size: {rep['stats']['merge_stats']['avg_unit_size']:.2f} words")
    
    # Acoustic metrics (repaired)
    lines.append(f"\nAcoustic metrics (repaired):")
    lines.append(f"  %V (articulate): {rep['acoustic']['percent_v_articulate']:.2f}%")
    lines.append(f"  %V (normal speech, incl. pauses): {rep['acoustic']['percent_v_speech']:.2f}%")
    lines.append(f"  ΔC: {rep['acoustic']['delta_c']:.4f} mora (consonant-interval SD)")
    lines.append(f"  MeanC: {rep['acoustic']['mean_interval']:.4f} mora (mean consonant interval)")
    lines.append(f"  VarcoC: {rep['acoustic']['varco_c']:.2f} %")
    
    # Speech rate
    lines.append(f"\nSpeech rate (repaired text only):")
    lines.append(f"  WPM: {rep['speech']['wpm']} words/min")
    lines.append(f"  Pause ratio: {rep['speech']['pause_ratio']}%")
    lines.append(f"  SPS (speech): {rep['speech']['sps_speech']:.3f} syllable/s")
    lines.append(f"  SPS (articulation): {rep['speech']['sps_articulation']:.3f} syllable/s")
    lines.append(f"  Average syllable duration: {rep['speech']['syllable_duration']:.3f} s/syllable")
    lines.append(f"  Mora duration: {rep['speech']['mora_duration']:.3f} s/mora")
    lines.append(f"  Word duration: {rep['speech']['word_duration']:.3f} s/word")
    
    # Pause metrics
    pm = rep['pause_metrics']
    pd = rep['pause_durations']
    # Keep ratio audit-consistent with displayed durations by using the same rounded values.
    avg_syllable_duration_display = round(rep['speech']['syllable_duration'], 3)
    initial_short_punctuation_duration_display = round(pd['initial_short_punctuation_duration'], 3)
    initial_long_punctuation_duration_display = round(pd['initial_long_punctuation_duration'], 3)
    corrected_short_punctuation_duration_display = round(pd['corrected_short_punctuation_duration'], 3)
    corrected_long_punctuation_duration_display = round(pd['corrected_long_punctuation_duration'], 3)
    initial_short_pause_syllable_ratio = (
        initial_short_punctuation_duration_display / avg_syllable_duration_display
        if avg_syllable_duration_display > 0 else 0
    )
    initial_long_pause_syllable_ratio = (
        initial_long_punctuation_duration_display / avg_syllable_duration_display
        if avg_syllable_duration_display > 0 else 0
    )
    corrected_short_pause_syllable_ratio = (
        corrected_short_punctuation_duration_display / avg_syllable_duration_display
        if avg_syllable_duration_display > 0 else 0
    )
    corrected_long_pause_syllable_ratio = (
        corrected_long_punctuation_duration_display / avg_syllable_duration_display
        if avg_syllable_duration_display > 0 else 0
    )
    
    lines.append(f"\nPause metrics:")
    lines.append(f"  Short pause punctuation per syllable: {pm['short_punctuation_per_syllable']:.3f} pause/syllable")
    lines.append(f"  Long pause punctuation per syllable: {pm['long_punctuation_per_syllable']:.3f} pause/syllable")
    lines.append(f"  Total punctuation pauses per syllable: {pm['punctuation_per_syllable']:.3f} pause/syllable")
    lines.append(f"  Total boundaries: {pm['total_boundaries']} boundaries")
    lines.append(f"  Pauseable boundaries: {pm['pauseable_boundaries']} boundaries")
    lines.append(f"  Short pauseable boundaries: {pm['short_pauseable_boundaries']} boundaries")
    lines.append(f"  Long pauseable boundaries: {pm['long_pauseable_boundaries']} boundaries")
    
    lines.append(f"\nPause duration allocation (total pause: {pd['pause_time_per_syllable']:.3f} s/syllable):")
    lines.append(f"  Short pause punctuation weight: always {pd['short_punct_weight']:.1f} (no unit)")
    lines.append(f"  Initial long pause punctuation weight relative to short: {pd['initial_long_punct_weight']:.1f} (no unit)")
    lines.append(
        f"  Initial short pause punctuation duration: {initial_short_punctuation_duration_display:.3f} s/pause "
        f"({initial_short_pause_syllable_ratio:.4f} average syllable duration) "
        f"({pd['initial_short_punctuation_percent']:.1f}% of pause time)"
    )
    lines.append(
        f"  Initial average long pause punctuation duration: {initial_long_punctuation_duration_display:.3f} s/pause "
        f"({initial_long_pause_syllable_ratio:.4f} average syllable duration) "
        f"({pd['initial_long_punctuation_percent']:.1f}% of pause time)"
    )
    lines.append(
        f"  Corrected (multiple of 2*morae) short pause punctuation duration: {corrected_short_punctuation_duration_display:.3f} s/pause "
        f"({corrected_short_pause_syllable_ratio:.4f} average syllable duration) "
        f"({pd['corrected_short_punctuation_percent']:.1f}% of pause time)"
    )
    lines.append(
        f"  Corrected average long pause punctuation duration: {corrected_long_punctuation_duration_display:.3f} s/pause "
        f"({corrected_long_pause_syllable_ratio:.4f} average syllable duration) "
        f"({pd['corrected_long_punctuation_percent']:.1f}% of pause time)"
    )
    lines.append(
        f"  Corrected average long pause punctuation weight relative to short: {pd['corrected_long_punct_weight']:.1f} (no unit)"
    )

    # --- REPAIR STATISTICS ---
    lines.append("\n--- REPAIR STATISTICS ---")
    rs = result['repair_stats']
    lines.append(f"  Repaired syllables: {rs['repaired_syllables']} syllables")
    lines.append(f"  Repair rate: {rs['repair_rate']:.2f}%")
    lines.append(f"\n  Repair types:")
    for typ, count in rs['repair_types'].items():
        if count > 0:
            lines.append(f"    {typ:8}: {count:4d} syllables")
    
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
        add_row("%V_articulate", [f"{a['percent_v_articulate']:.2f}" for a in ac])
        add_row("%V_normal_speech", [f"{a['percent_v_speech']:.2f}" for a in ac])
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
        add_row("rep_%V_articulate", [f"{a['percent_v_articulate']:.2f}" for a in ac_rep])
        add_row("rep_%V_normal_speech", [f"{a['percent_v_speech']:.2f}" for a in ac_rep])
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
            
            values = [f"{pm['short_punctuation_per_syllable']:.3f}" for r in results]
            add_row("short_pause_punct_per_syllable", values)
            values = [f"{pm['long_punctuation_per_syllable']:.3f}" for r in results]
            add_row("long_pause_punct_per_syllable", values)
            values = [f"{pm['punctuation_per_syllable']:.3f}" for r in results]
            add_row("total_punct_per_syllable", values)
            values = [r['repaired']['pause_metrics']['short_pauseable_boundaries'] for r in results]
            add_row("short_pauseable_boundaries", values)
            values = [r['repaired']['pause_metrics']['long_pauseable_boundaries'] for r in results]
            add_row("long_pauseable_boundaries", values)
            values = [f"{r['repaired']['pause_durations']['initial_long_punct_weight']:.4f}" for r in results]
            add_row("initial_long_pause_punct_weight_rel_to_short", values)
            values = [f"{r['repaired']['pause_durations']['initial_short_punctuation_duration']:.4f}" for r in results]
            add_row("initial_short_pause_punct_duration", values)
            values = [f"{r['repaired']['pause_durations']['initial_long_punctuation_duration']:.4f}" for r in results]
            add_row("initial_avg_long_pause_punct_duration", values)
            values = [f"{r['repaired']['pause_durations']['corrected_short_punctuation_duration']:.4f}" for r in results]
            add_row("corrected_short_pause_punct_duration", values)
            values = [f"{r['repaired']['pause_durations']['corrected_long_punctuation_duration']:.4f}" for r in results]
            add_row("corrected_avg_long_pause_punct_duration", values)
            values = [f"{r['repaired']['pause_durations']['corrected_long_punct_weight']:.4f}" for r in results]
            add_row("corrected_avg_long_pause_punct_weight_rel_to_short", values)
            values = [f"{r['repaired']['pause_durations']['corrected_short_punctuation_percent']:.1f}" for r in results]
            add_row("corrected_short_pause_punct_percent", values)
            values = [f"{r['repaired']['pause_durations']['corrected_long_punctuation_percent']:.1f}" for r in results]
            add_row("corrected_long_pause_punct_percent", values)
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
        ('at·tā', 'ʾat·tā'),
        ('ā·lik', 'ʾā·lik'),
        ('maḫ·rim~-ma', 'maḫ·rim:-ma'),
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
            'expected': 'ʾat·tāʾā·lik'
        },
        {
            'name': 'Line with repairs',
            'input': 'maḫ·rim~-ma dad~',
            'expected': 'maḫ·rim:-madad:'
        },
        {
            'name': 'Complex line with punctuation',
            'input': 'at·tā, ā·lik! maḫ·rim~-ma || dad~ ···',
            'expected': 'ʾat·tā$ʾā·lik$maḫ·rim:-ma$dad:$'
        },
        {
            'name': 'Line with merged words',
            'input': 'ana+kâ·ša lu·ṣī-ma',
            'expected': 'ʾana+kâ·šalu·ṣī-ma'
        },
        {
            'name': 'Line with multiple spaces',
            'input': 'at·tā   ā·lik',
            'expected': 'ʾat·tāʾā·lik'
        },
        {
            'name': 'Line with leading spaces',
            'input': '  at·tā ā·lik',
            'expected': 'ʾat·tāʾā·lik'
        },
        {
            'name': 'Line with trailing spaces',
            'input': 'at·tā ā·lik  ',
            'expected': 'ʾat·tāʾā·lik'
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
        {
            'name': 'Across space behaves as connected speech',
            'input': 'mas ta',
            'expected_distances': [1, 0, 1]
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

    # ===== TEST 7: Pause Metrics (grouping + class priority) =====
    print("\n--- Test 7: Pause Metrics (grouping + class priority) ---")
    tests_total += 1

    test_text = "at·tā ?!!! ā·lik ), i·lī ... bā·nû"
    stats = analyze_text(test_text, is_repaired=True)
    pause_metrics = compute_pause_metrics(test_text, stats)

    # Expected counts:
    # - "?!!!" = one LONG punctuation gap
    # - ")," = one SHORT punctuation gap
    # - " ... " (standalone ellipsis) = one SHORT punctuation gap
    # - final EOF after terminal word = one LONG punctuation gap

    passed = True
    if pause_metrics['raw_counts']['spaces'] != 0:
        print(f"  ❌ Space pause count: got {pause_metrics['raw_counts']['spaces']}, expected 0")
        passed = False
    if pause_metrics['raw_counts']['short_punctuation'] != 2:
        print(f"  ❌ Short punctuation count: got {pause_metrics['raw_counts']['short_punctuation']}, expected 2")
        passed = False
    if pause_metrics['raw_counts']['long_punctuation'] != 2:
        print(f"  ❌ Long punctuation count: got {pause_metrics['raw_counts']['long_punctuation']}, expected 2")
        passed = False
    if pause_metrics['raw_counts']['punctuation'] != 4:
        print(f"  ❌ Punctuation count: got {pause_metrics['raw_counts']['punctuation']}, expected 4")
        passed = False
    if pause_metrics['raw_counts']['merged_boundaries'] != 0:
        print(f"  ❌ Merged boundaries: got {pause_metrics['raw_counts']['merged_boundaries']}, expected 0")
        passed = False
    if pause_metrics['short_pauseable_boundaries'] != 2:
        print(f"  ❌ Short pauseable boundaries: got {pause_metrics['short_pauseable_boundaries']}, expected 2")
        passed = False
    if pause_metrics['long_pauseable_boundaries'] != 2:
        print(f"  ❌ Long pauseable boundaries: got {pause_metrics['long_pauseable_boundaries']}, expected 2")
        passed = False

    if passed:
        print("  ✅ All pause metrics tests passed")
        tests_passed += 1
    else:
        print(f"  Raw counts: {pause_metrics['raw_counts']}")

    # ===== TEST 7B: Unknown punctuation defaults to long =====
    print("\n--- Test 7B: Unknown punctuation defaults to long ---")
    tests_total += 1

    test_text = "at·tā @ ā·lik"
    stats = analyze_text(test_text, is_repaired=True)
    pause_metrics = compute_pause_metrics(test_text, stats)

    passed = True
    if pause_metrics['raw_counts']['defaulted_long_punctuation'] != 1:
        print(
            "  ❌ Defaulted long punctuation count: "
            f"got {pause_metrics['raw_counts']['defaulted_long_punctuation']}, expected 1"
        )
        passed = False
    if pause_metrics['raw_counts']['short_punctuation'] != 0:
        print(f"  ❌ Short punctuation count: got {pause_metrics['raw_counts']['short_punctuation']}, expected 0")
        passed = False
    if pause_metrics['raw_counts']['long_punctuation'] != 2:
        print(f"  ❌ Long punctuation count: got {pause_metrics['raw_counts']['long_punctuation']}, expected 2")
        passed = False

    if passed:
        print("  ✅ Unknown-punctuation fallback tests passed")
        tests_passed += 1

    # ===== TEST 8: %V with pauses =====
    print("\n--- Test 8: %V with pauses ---")
    tests_total += 1

    passed = True
    articulate = 80.0
    speech = compute_percent_v_with_pauses(articulate, 35.0)
    expected = articulate / 1.35
    if abs(speech - expected) > 1e-9:
        print(f"  ❌ %V conversion: got {speech}, expected {expected}")
        passed = False

    # Use in-memory processing instead of filesystem-based process_file
    text = "šar gi·mir+dad~·mē\n"
    result = process_filetext(text, wpm=165, pause_ratio=35.0, filesrc='test-sample')

    for key in ('original', 'repaired'):
        acoustic = result[key]['acoustic']
        if abs(acoustic['percent_v'] - acoustic['percent_v_articulate']) > 1e-9:
            print(f"  ❌ {key}: percent_v alias mismatch")
            passed = False
        expected_speech = acoustic['percent_v_articulate'] / 1.35
        if abs(acoustic['percent_v_speech'] - expected_speech) > 1e-9:
            print(
                f"  ❌ {key}: %V speech mismatch "
                f"(got {acoustic['percent_v_speech']}, expected {expected_speech})"
            )
            passed = False

    if passed:
        print("  ✅ %V articulate/speech tests passed")
        tests_passed += 1

    # ===== TEST 9: Corrected pause duration conservation =====
    print("\n--- Test 9: Corrected pause duration conservation ---")
    tests_total += 1

    passed = True
    # Use in-memory processing instead of filesystem-based process_file
    text = "šar gi·mir+dad~·mē || bā·nû kib·rā~·ti ...\n"
    result = process_filetext(text, wpm=165, pause_ratio=35.0, filesrc='test-sample')
    pm = result['repaired']['pause_metrics']
    pd = result['repaired']['pause_durations']

    initial_total = (
        pd['initial_short_punctuation_duration'] * pm['raw_counts']['short_punctuation']
        + pd['initial_long_punctuation_duration'] * pm['raw_counts']['long_punctuation']
    )
    corrected_total = (
        pd['corrected_short_punctuation_duration'] * pm['raw_counts']['short_punctuation']
        + pd['corrected_long_punctuation_duration'] * pm['raw_counts']['long_punctuation']
    )
    if abs(initial_total - corrected_total) > 1e-9:
        print(f"  ❌ Corrected total pause mismatch: got {corrected_total}, expected {initial_total}")
        passed = False

    # If short events exist, corrected short duration must be an even number of morae.
    if pm['raw_counts']['short_punctuation'] > 0 and result['repaired']['speech']['mora_duration'] > 0:
        corrected_short_morae = pd['corrected_short_punctuation_duration'] / result['repaired']['speech']['mora_duration']
        if abs(corrected_short_morae - round(corrected_short_morae)) > 1e-9:
            print(f"  ❌ Corrected short morae not integral: got {corrected_short_morae}")
            passed = False
        elif int(round(corrected_short_morae)) % 2 != 0:
            print(f"  ❌ Corrected short morae not even: got {corrected_short_morae}")
            passed = False

    if passed:
        print("  ✅ Corrected pause duration tests passed")
        tests_passed += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"{'='*80}\n")
    
    return tests_passed == tests_total

