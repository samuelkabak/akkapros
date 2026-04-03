#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Metrics Calculator

Computes comprehensive metrics from Akkadian text with proper handling of:
- Vowel length: short (a), long (ā/â), extra-long (à/ì/ù/è)
- Consonant gemination: marked with : (e.g., mas:ta)
- Glottal stops: ʾ for initial vowels
- Distance-based ΔC calculation
- Punctuation boundaries marked with $
- Pause metrics for punctuation only (short vs long pause classes)
"""

import logging
import re
import random
import statistics
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from collections import Counter
import math

from akkapros.lib.frontmatter import read_text_file, resolve_metrics_prominence_counts

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
    SHORT_PAUSE_PUNCTUATION_CHARS,
    SHORT_PAUSE_PUNCTUATION_PATTERNS,
    LONG_PAUSE_PUNCTUATION_CHARS,
    LONG_PAUSE_PUNCTUATION_PATTERNS,
    LONG_PAUSE_INCLUDES_NEWLINE,
    LONG_PAUSE_INCLUDES_FINAL_EOF,
    DIPH_SEPARATOR,
    HIATUS_MARKER,
)
from akkapros.lib.utils import (
    compile_contextual_regex,
    format_path_for_logging,
    format_selftest_label,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
    run_simple_selftest_suite,
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
LOGGER = logging.getLogger(__name__)

class PunctuationConfigError(ValueError):
    """Raised when pause punctuation rules are invalid."""


ACTIVE_SHORT_PAUSE_PUNCTUATION_CHARS = set(SHORT_PAUSE_PUNCTUATION_CHARS)
ACTIVE_LONG_PAUSE_PUNCTUATION_CHARS = set(LONG_PAUSE_PUNCTUATION_CHARS)
ACTIVE_SHORT_PAUSE_PUNCTUATION_PATTERNS = tuple(SHORT_PAUSE_PUNCTUATION_PATTERNS)
ACTIVE_LONG_PAUSE_PUNCTUATION_PATTERNS = tuple(LONG_PAUSE_PUNCTUATION_PATTERNS)
ACTIVE_SHORT_PAUSE_PUNCT_REGEX: List[re.Pattern] = []
ACTIVE_LONG_PAUSE_PUNCT_REGEX: List[re.Pattern] = []


def _compile_pause_patterns(patterns: List[str], option_name: str) -> List[re.Pattern]:
    compiled: List[re.Pattern] = []
    for idx, pattern in enumerate(patterns, start=1):
        try:
            compiled.append(compile_contextual_regex(pattern, option_name, idx))
        except ValueError as exc:
            raise PunctuationConfigError(
                f"Invalid regex for {option_name} (item {idx}): {pattern!r}. Error: {exc}"
            ) from exc
    return compiled


def configure_pause_punctuation_rules(
    *,
    short_punct_chars: str = '',
    long_punct_chars: str = '',
    short_punct_patterns: Optional[List[str]] = None,
    long_punct_patterns: Optional[List[str]] = None,
) -> None:
    """Configure pause punctuation rules and validate regex before processing."""
    global ACTIVE_SHORT_PAUSE_PUNCTUATION_CHARS, ACTIVE_LONG_PAUSE_PUNCTUATION_CHARS
    global ACTIVE_SHORT_PAUSE_PUNCTUATION_PATTERNS, ACTIVE_LONG_PAUSE_PUNCTUATION_PATTERNS
    global ACTIVE_SHORT_PAUSE_PUNCT_REGEX, ACTIVE_LONG_PAUSE_PUNCT_REGEX

    ACTIVE_SHORT_PAUSE_PUNCTUATION_CHARS = set(SHORT_PAUSE_PUNCTUATION_CHARS) | set(short_punct_chars or '')
    ACTIVE_LONG_PAUSE_PUNCTUATION_CHARS = set(LONG_PAUSE_PUNCTUATION_CHARS) | set(long_punct_chars or '')

    short_patterns = list(SHORT_PAUSE_PUNCTUATION_PATTERNS)
    if short_punct_patterns:
        short_patterns.extend(short_punct_patterns)
    long_patterns = list(LONG_PAUSE_PUNCTUATION_PATTERNS)
    if long_punct_patterns:
        long_patterns.extend(long_punct_patterns)

    ACTIVE_SHORT_PAUSE_PUNCT_REGEX = _compile_pause_patterns(short_patterns, '--extra-short-punct-pattern')
    ACTIVE_LONG_PAUSE_PUNCT_REGEX = _compile_pause_patterns(long_patterns, '--extra-long-punct-pattern')

    ACTIVE_SHORT_PAUSE_PUNCTUATION_PATTERNS = tuple(short_patterns)
    ACTIVE_LONG_PAUSE_PUNCTUATION_PATTERNS = tuple(long_patterns)


# Initialize with default punctuation classes/patterns.
configure_pause_punctuation_rules()

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
UNCLASSIFIED_SYLLABLE_TYPE = 'OTHER'
DISPLAY_SYLLABLE_TYPES = SYLLABLE_TYPES + [UNCLASSIFIED_SYLLABLE_TYPE]

# Total morae per classified syllable type.
SYLLABLE_MORA_TOTAL = {
    'CV': 1,
    'CVC': 2,
    'CVV': 2,
    'CVVC': 3,
    'VC': 2,
    'V': 1,
    'VV': 2,
    'VVC': 3,
    'C:V': 2,
    'CVC:': 3,
    'CVV:': 3,
    'CVV:C': 4,
    'VC:': 3,
    'ʔ:V': 2,
    'VV:': 3,
    'VV:C': 4,
}

SYLLABLE_VOWEL_MORA_TOTAL = {
    'CV': 1,
    'CVC': 1,
    'CVV': 2,
    'CVVC': 2,
    'VC': 1,
    'V': 1,
    'VV': 2,
    'VVC': 2,
    'C:V': 1,
    'CVC:': 1,
    'CVV:': 2,
    'CVV:C': 3,
    'VC:': 1,
    'ʔ:V': 1,
    'VV:': 2,
    'VV:C': 3,
}


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
    return (c in ALL_CONSONANTS and c != DIPH_SEPARATOR) or c == GLOTTAL


def is_consonant_processing(c: str) -> bool:
    """Return True if character is a consonant for processing purposes."""
    return (c in ALL_CONSONANTS and c != DIPH_SEPARATOR) or c == GLOTTAL


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
    internal_consonants_class = ''.join(sorted(ALL_CONSONANTS - {HIATUS_MARKER}))
    
    # CLASS_SYLLABLE_COMPLEMENT := (CONSONANTS or VOWELS or '~')
    complement_class = f'[{consonants_class}{vowels_class}~]*'
    
    # CLASS_WORD_FIRST_SYLLABLE_FIRST_LETTER := (CONSONANTS or VOWELS or '~')
    first_letter_class = f'[{consonants_class}{vowels_class}~]'
    
    # CLASS_WORD_INTERNAL_SYLLABLE_FIRST_LETTER := CONSONANTS
    internal_first_class = f'[{internal_consonants_class}]'
    
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
    # Diphthong memory is relevant for syllable statistics, not acoustic spacing.
    word = word.replace(DIPH_SEPARATOR, '')
    word = word.replace(HIATUS_MARKER, '')

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


def _vowel_morae_in_syllable(syl: str) -> int:
    replacements = [
        ('ā~', 'à'), ('â~', 'à'),
        ('ī~', 'ì'), ('î~', 'ì'),
        ('ū~', 'ù'), ('û~', 'ù'),
        ('ē~', 'è'), ('ê~', 'è'),
    ]
    for old, new in replacements:
        syl = syl.replace(old, new)

    total = 0
    i = 0
    n = len(syl)

    while i < n:
        ch = syl[i]
        if ch not in ALL_VOWELS:
            i += 1
            continue

        cluster_len = 1
        cluster_has_extra = ch in EXTRA_LONG_VOWELS
        cluster_has_length = False
        single_vowel_morae = 3 if ch in EXTRA_LONG_VOWELS else 2 if ch in LONG_VOWELS else 1
        i += 1

        while i < n:
            next_char = syl[i]
            if next_char in ('~', LENGTH_MARKER):
                cluster_has_length = True
                i += 1
                continue
            if next_char in ALL_VOWELS:
                cluster_len += 1
                cluster_has_extra = cluster_has_extra or next_char in EXTRA_LONG_VOWELS
                i += 1
                continue
            break

        if cluster_len > 1:
            total += 3 if cluster_has_extra or cluster_has_length else 2
        else:
            total += single_vowel_morae
            if cluster_has_length and ch not in EXTRA_LONG_VOWELS:
                total += 1

    return total


# ------------------------------------------------------------
# Syllable classification
# ------------------------------------------------------------
def classify_syllable(syl: str, is_accentuated: bool = False) -> str:
    """
    Classify a syllable into one of the types.
    """
    if not syl:
        return UNCLASSIFIED_SYLLABLE_TYPE
    
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
    

    if syl.startswith(':'):
        return 'ʔ:V'

    if len(syl) > 1 and syl[1] == ':' and is_consonant_processing(syl[0]):
        return 'C:V'

    core = syl.replace(LENGTH_MARKER, '')
    vowel_positions = [idx for idx, ch in enumerate(core) if is_vowel_processing(ch)]
    if not vowel_positions:
        return UNCLASSIFIED_SYLLABLE_TYPE

    first_vowel = vowel_positions[0]
    last_vowel = vowel_positions[-1]
    onset_present = any(is_consonant_processing(ch) for ch in core[:first_vowel])
    coda_present = any(is_consonant_processing(ch) for ch in core[last_vowel + 1:])
    vowel_morae = _vowel_morae_in_syllable(syl)
    coda_geminated = syl.endswith(LENGTH_MARKER)

    if coda_geminated:
        if onset_present and coda_present:
            if vowel_morae == 1:
                return 'CVC:'
            if vowel_morae == 2:
                return 'CVV:C'
            return UNCLASSIFIED_SYLLABLE_TYPE
        if onset_present and not coda_present:
            if vowel_morae == 1:
                return 'C:V'
            if vowel_morae == 2:
                return 'CVV:'
            return UNCLASSIFIED_SYLLABLE_TYPE
        if not onset_present and coda_present:
            if vowel_morae == 1:
                return 'VC:'
            if vowel_morae == 2:
                return 'VV:C'
            return UNCLASSIFIED_SYLLABLE_TYPE
        if vowel_morae == 1:
            return 'ʔ:V'
        if vowel_morae == 2:
            return 'VV:'
        return UNCLASSIFIED_SYLLABLE_TYPE

    if onset_present and coda_present:
        if vowel_morae == 1:
            return 'CVC'
        if vowel_morae == 2:
            return 'CVVC'
        if vowel_morae == 3:
            return 'CVV:C'
        return UNCLASSIFIED_SYLLABLE_TYPE
    if onset_present and not coda_present:
        if vowel_morae == 1:
            return 'CV'
        if vowel_morae == 2:
            return 'CVV'
        if vowel_morae == 3:
            return 'CVV:'
        return UNCLASSIFIED_SYLLABLE_TYPE
    if not onset_present and coda_present:
        if vowel_morae == 1:
            return 'VC'
        if vowel_morae == 2:
            return 'VVC'
        if vowel_morae == 3:
            return 'VV:C'
        return UNCLASSIFIED_SYLLABLE_TYPE
    if vowel_morae == 1:
        return 'V'
    if vowel_morae == 2:
        return 'VV'
    if vowel_morae == 3:
        return 'VV:'
    return UNCLASSIFIED_SYLLABLE_TYPE

# ------------------------------------------------------------
# Text analysis
# ------------------------------------------------------------
def compute_percent_v_from_stats(stats: Dict) -> float:
    """Compute %V from syllable statistics."""
    syllable_counts = stats.get('syllable_counts', {})
    total_morae = stats.get('mora_stats', {}).get('total', 0)
    vowel_morae_total = stats.get('vowel_morae_total')
    if total_morae > 0 and vowel_morae_total is not None:
        return (vowel_morae_total / total_morae) * 100

    if total_morae <= 0:
        total_morae = sum(
            SYLLABLE_MORA_TOTAL.get(typ, 0) * count
            for typ, count in syllable_counts.items()
        )

    if vowel_morae_total is None:
        vowel_morae_total = sum(
            SYLLABLE_VOWEL_MORA_TOTAL.get(typ, 0) * count
            for typ, count in syllable_counts.items()
        )

    return (vowel_morae_total / total_morae * 100) if total_morae > 0 else 0


def compute_percent_v_with_pauses(percent_v_articulate: float, pause_ratio: float) -> float:
    """Convert articulate %V to normal-speech %V by adding pause morae to denominator.

    If pause_ratio is 35, total morae are scaled by x1.35, so %V is divided by 1.35.
    """
    scale = 1.0 + (pause_ratio / 100.0)
    if scale <= 0:
        return percent_v_articulate
    return percent_v_articulate / scale

def analyze_text(text: str, is_accentuated: bool = False) -> Dict:
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
    vowel_morae_list = []
    
    # Process each word
    for word in words:
        # Split into syllables (on . or -)
        syllables = re.split(rf'[\{SYL_SEPARATOR}\{HYPHEN}\{WORD_LINKER}\{DIPH_SEPARATOR}]+', word)

        # Count syllables in this word
        word_syllable_count = 0
        word_mora_count = 0
        
        for syl in syllables:
            if not syl:
                continue
            syl = syl.replace(HIATUS_MARKER, '')
            
            word_syllable_count += 1
            
            # Classify syllable
            syl_type = classify_syllable(syl, is_accentuated)
            syllable_counts[syl_type] = syllable_counts.get(syl_type, 0) + 1

            # Count morae from syllable type so totals stay consistent with %V and
            # accentuated categories (e.g., CVC:, CVV:, CVV:C).
            morae = SYLLABLE_MORA_TOTAL.get(syl_type)
            if morae is None:
                # Fallback for unexpected/unclassified patterns.
                morae = 0
                for c in syl:
                    if c in LONG_VOWELS:
                        morae += 2
                    elif c in EXTRA_LONG_VOWELS:
                        morae += 3
                    elif c == LENGTH_MARKER or c == '~':
                        morae += 1
                    elif c in SHORT_VOWELS:
                        morae += 1
            vowel_morae = _vowel_morae_in_syllable(syl)
            vowel_morae_list.append(vowel_morae)
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

    # Grouped syllable statistics for machine-readable outputs.
    syllable_statistics = {
        'types': {
            typ: {
                'count': count,
                'percent': syllable_percentages.get(typ, 0.0),
            }
            for typ, count in syllable_counts.items()
        },
        'count': total_syllables,
    }
    
    # Mora statistics
    total_morae = sum(morae_list)
    mora_mean = statistics.mean(morae_list) if morae_list else 0
    mora_std = statistics.stdev(morae_list) if len(morae_list) > 1 else 0

    # Word statistics
    total_words = len(words)
    syllables_per_word_mean = statistics.mean(syllables_per_word) if syllables_per_word else 0
    syllables_per_word_std = statistics.stdev(syllables_per_word) if len(syllables_per_word) > 1 else 0
    morae_per_word_mean = statistics.mean(morae_per_word) if morae_per_word else 0
    morae_per_word_std = statistics.stdev(morae_per_word) if len(morae_per_word) > 1 else 0

    mora_stats = {
        'mean': mora_mean,
        'std': mora_std,
        'total': total_morae,
    }
    word_stats = {
        'total_words': total_words,
        'syllables_per_word': {
            'mean': syllables_per_word_mean,
            'std': syllables_per_word_std,
        },
        'morae_per_word': {
            'mean': morae_per_word_mean,
            'std': morae_per_word_std,
        }
    }
    word_statistics = {
        'total_words': total_words,
        'syllables_per_word': {
            'mean': syllables_per_word_mean,
            'stddev': syllables_per_word_std,
        },
    }
    mora_statistics = {
        'mean_morae_per_syllable': {
            'mean': mora_mean,
            'stddev': mora_std,
        },
        'mean_morae_per_word': {
            'mean': morae_per_word_mean,
            'stddev': morae_per_word_std,
        },
        'total_morae': total_morae,
    }
    
    # Merge statistics
    merge_stats = count_merged_units(words)
    
    return {
        'syllable_statistics': syllable_statistics,
        'syllable_counts': syllable_counts,
        'syllable_percentages': syllable_percentages,
        'total_syllables': total_syllables,
        'vowel_morae_total': sum(vowel_morae_list),
        'mora_stats': mora_stats,
        'mora_statistics': mora_statistics,
        'word_stats': word_stats,
        'word_statistics': word_statistics,
        'merge_stats': merge_stats
    }


# ------------------------------------------------------------
# Accentuation statistics
# ------------------------------------------------------------
def compute_accentuation_stats(original_stats: Dict, accentuated_stats: Dict) -> Dict:
    """
    Compute accentuation-specific statistics by comparing original and accentuated.
    """
    # Count accentuated syllables by comparing counts
    accentuation_types = {}
    total_accentuated = 0
    
    all_types = set(original_stats['syllable_counts'].keys()) | set(accentuated_stats['syllable_counts'].keys())
    
    for typ in all_types:
        orig_count = original_stats['syllable_counts'].get(typ, 0)
        accentuated_count = accentuated_stats['syllable_counts'].get(typ, 0)
        if accentuated_count > orig_count:
            # This type increased due to accentuation.
            diff = accentuated_count - orig_count
            accentuation_types[typ] = diff
            total_accentuated += diff
    
    # Accentuation rate
    accentuation_rate = (total_accentuated / original_stats['total_syllables'] * 100) if original_stats['total_syllables'] > 0 else 0
    
    return {
        'accentuated_syllables': total_accentuated,
        'accentuation_rate': accentuation_rate,
        'accentuation_types': accentuation_types,
        'merged_words': accentuated_stats['merge_stats']['total_merged_words'],
        'merged_units': accentuated_stats['merge_stats']['merged_units'],
        'avg_unit_size': accentuated_stats['merge_stats']['avg_unit_size']
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


def enrich_acoustic_metrics(acoustic: Dict, speech: Dict) -> Dict:
    """Add explicit seconds and mora views for acoustic interval metrics."""
    delta_c_mora = acoustic['delta_c']
    mean_c_mora = acoustic['mean_interval']
    mora_duration = speech['mora_duration']

    acoustic['delta_c_seconds'] = delta_c_mora * mora_duration
    acoustic['delta_c_mora'] = delta_c_mora
    acoustic['mean_c_seconds'] = mean_c_mora * mora_duration
    acoustic['mean_c_mora'] = mean_c_mora
    return acoustic


# ------------------------------------------------------------
# Pause metrics
# ------------------------------------------------------------
def _gap_has_long_pause(gap: str) -> bool:
    """Return True when a boundary gap contains long-pause punctuation cues."""
    if LONG_PAUSE_INCLUDES_NEWLINE and '\n' in gap:
        return True
    if any(rx.search(gap) for rx in ACTIVE_LONG_PAUSE_PUNCT_REGEX):
        return True
    # Standalone ellipsis tokens (space + .../… + space|EOF) are short pauses;
    # remove them before char-level long-class checks.
    sanitized_gap = re.sub(r'(?<=\s)\.\.\.(?=\s|$)', '', gap)
    sanitized_gap = re.sub(r'(?<=\s)…(?=\s|$)', '', sanitized_gap)
    return any(ch in ACTIVE_LONG_PAUSE_PUNCTUATION_CHARS for ch in sanitized_gap)


def _gap_has_short_pause(gap: str) -> bool:
    """Return True when a boundary gap contains short-pause punctuation cues."""
    if any(rx.search(gap) for rx in ACTIVE_SHORT_PAUSE_PUNCT_REGEX):
        return True
    # Ignore non-pause structural markers that may appear if word parsing
    # leaves residual intra-word separators in a gap.
    punctuation_chars = [
        ch for ch in gap
        if (not ch.isspace()) and ch not in {WORD_LINKER, SYL_SEPARATOR, HYPHEN}
    ]
    if not punctuation_chars:
        return False
    if _gap_has_long_pause(gap):
        return False
    return any(ch in ACTIVE_SHORT_PAUSE_PUNCTUATION_CHARS for ch in punctuation_chars)


def _unknown_gap_punctuation_chars(gap: str) -> List[str]:
    """Return punctuation chars in a gap that are not declared in active rules."""
    punctuation_chars = [
        ch for ch in gap
        if (not ch.isspace()) and ch not in {WORD_LINKER, SYL_SEPARATOR, HYPHEN}
    ]
    declared = ACTIVE_SHORT_PAUSE_PUNCTUATION_CHARS | ACTIVE_LONG_PAUSE_PUNCTUATION_CHARS
    unknown: List[str] = []
    seen = set()
    for ch in punctuation_chars:
        if ch not in declared and ch not in seen:
            seen.add(ch)
            unknown.append(ch)
    return unknown


def _gap_has_any_punctuation(gap: str) -> bool:
    """Return True when a gap contains at least one non-space, non-linker marker."""
    return any(
        (not ch.isspace()) and ch not in {WORD_LINKER, SYL_SEPARATOR, HYPHEN}
        for ch in gap
    )


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
                unknown = _unknown_gap_punctuation_chars(gap)
                unknown_repr = ''.join(unknown) if unknown else gap
                raise PunctuationConfigError(
                    "Undeclared punctuation in metrics input gap "
                    f"{gap!r} (unknown chars: {unknown_repr!r}). "
                    "Declare upstream via syllabifier/fullprosmaker --extra-short-punct-chars/--extra-long-punct-chars or matching --extra-*-punct-pattern options."
                )
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
    explicit_link_count_override: str | int | None = None,
) -> Dict:
    """Process a single file and return all metrics."""
    input_frontmatter, text = read_text_file(filename)

    return process_filetext(
        text,
        wpm,
        pause_ratio,
        long_punct_weight,
        filename,
        prominence_statistics=resolve_metrics_prominence_counts(
            text,
            input_frontmatter=input_frontmatter,
            explicit_link_count_override=explicit_link_count_override,
        ),
    )


def build_prominence_statistics(total_words: int, prominence_counts: Dict[str, int]) -> Dict[str, int]:
    """Build prominence statistics for the ORIGINAL metrics section."""
    function_word_count = int(prominence_counts['function_word_count'])
    explicit_word_link_count = int(prominence_counts['explicit_word_link_count'])
    prominence_candidate_word_count = total_words - function_word_count - explicit_word_link_count

    if prominence_candidate_word_count < 0:
        raise ValueError(
            "metrics front matter counts are inconsistent: "
            f"total_words={total_words}, function_word_count={function_word_count}, "
            f"explicit_word_link_count={explicit_word_link_count}"
        )

    return {
        'function_word_count': function_word_count,
        'explicit_word_link_count': explicit_word_link_count,
        'prominence_candidate_word_count': prominence_candidate_word_count,
    }


def process_filetext(
    text: str,
    wpm: float,
    pause_ratio: float,
    long_punct_weight: float = DEFAULT_LONG_PAUSE_PUNCT_WEIGHT,
    filesrc: str = 'in-memory',
    prominence_statistics: Optional[Dict[str, int]] = None,
) -> Dict:

    # Analyze original (with ~ removed)
    original_stats = analyze_text(text.replace('~', ''), is_accentuated=False)
    resolved_prominence_statistics = None
    if prominence_statistics is not None:
        resolved_prominence_statistics = build_prominence_statistics(
            total_words=original_stats['word_stats']['total_words'],
            prominence_counts=prominence_statistics,
        )
    
    # Analyze accentuated (with ~ present)
    accentuated_stats = analyze_text(text, is_accentuated=True)
    
    # Compute accentuation stats
    accentuation_stats = compute_accentuation_stats(original_stats, accentuated_stats)
    
    # Compute %V from syllable statistics
    original_percent_v = compute_percent_v_from_stats(original_stats)
    accentuated_percent_v = compute_percent_v_from_stats(accentuated_stats)
    
    # Preprocess for acoustic metrics (ΔC, etc.)
    preprocessed_original = preprocess_text(text.replace('~', ''))
    preprocessed_accentuated = preprocess_text(text)
    
    # Compute acoustic metrics (excluding %V)
    acoustic_original = compute_acoustic_metrics(preprocessed_original)
    acoustic_accentuated = compute_acoustic_metrics(preprocessed_accentuated)
    
    # Override %V with mora-based values and expose both speaking conditions.
    acoustic_original['percent_v'] = original_percent_v
    acoustic_original['percent_v_articulate'] = original_percent_v
    acoustic_original['percent_v_speech'] = compute_percent_v_with_pauses(original_percent_v, pause_ratio)
    acoustic_accentuated['percent_v'] = accentuated_percent_v
    acoustic_accentuated['percent_v_articulate'] = accentuated_percent_v
    acoustic_accentuated['percent_v_speech'] = compute_percent_v_with_pauses(accentuated_percent_v, pause_ratio)
    
    # Compute speech rate for original and accentuated text
    speech_original = compute_speech_rate(preprocessed_original, original_stats, wpm, pause_ratio)
    speech_accentuated = compute_speech_rate(preprocessed_accentuated, accentuated_stats, wpm, pause_ratio)

    enrich_acoustic_metrics(acoustic_original, speech_original)
    enrich_acoustic_metrics(acoustic_accentuated, speech_accentuated)
    
    # Compute pause metrics
    pause_metrics = compute_pause_metrics(text, accentuated_stats)
    pause_durations = compute_pause_durations(
        pause_metrics,
        speech_accentuated,
        pause_ratio,
        long_punct_weight,
    )

    return {
        'file': format_path_for_logging(filesrc),
        'original': {
            'stats': original_stats,
            'speech': speech_original,
            'acoustic': acoustic_original,
            'prominence_statistics': resolved_prominence_statistics,
        },
        'accentuated': {
            'stats': accentuated_stats,
            'acoustic': acoustic_accentuated,
            'speech': speech_accentuated,
            'pause_metrics': pause_metrics,
            'pause_durations': pause_durations
        },
        'accentuation_stats': accentuation_stats
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
            value = run_context[key]
            if key == 'input' and isinstance(value, (str, Path)):
                value = format_path_for_logging(value)
            lines.append(f"  {key}: {value}")
    
    # --- ORIGINAL TEXT ---
    lines.append("\n--- ORIGINAL TEXT ---")
    orig = result['original']
    
    # Syllable statistics
    lines.append("\nSyllable statistics:")
    lines.append("  Syllable types:")
    for typ in DISPLAY_SYLLABLE_TYPES:
        count = orig['stats']['syllable_counts'].get(typ, 0)
        pct = orig['stats']['syllable_percentages'].get(typ, 0)
        if count > 0:
            lines.append(f"    {typ:6}: {count:4d} syllables ({pct:5.2f}%)")

    lines.append(f"  Total syllables: {orig['stats']['total_syllables']} syllables")
    
    # Word statistics
    lines.append(f"\nWord statistics:")
    lines.append(f"  Total words: {orig['stats']['word_stats']['total_words']} words")
    lines.append(f"  Syllables per word: {orig['stats']['word_stats']['syllables_per_word']['mean']:.3f} ± {orig['stats']['word_stats']['syllables_per_word']['std']:.3f} syllable/word")

    prominence_stats = orig.get('prominence_statistics')
    if prominence_stats:
        lines.append(f"\nProminence statistics:")
        lines.append(f"  Function words: {prominence_stats['function_word_count']} words")
        lines.append(f"  Explicitly linked words: {prominence_stats['explicit_word_link_count']} words")
        lines.append(f"  Prominence candidates: {prominence_stats['prominence_candidate_word_count']} words")

    # Mora statistics
    lines.append(f"\nMora statistics:")
    lines.append(f"  Mean morae per syllable: {orig['stats']['mora_stats']['mean']:.3f} ± {orig['stats']['mora_stats']['std']:.3f} mora/syllable")
    lines.append(f"  Mean morae per word: {orig['stats']['word_stats']['morae_per_word']['mean']:.3f} ± {orig['stats']['word_stats']['morae_per_word']['std']:.3f} mora/word")
    lines.append(f"  Total morae: {orig['stats']['mora_stats']['total']} mora")
    
    # Speech rate (original)
    lines.append(f"\nSpeech rate (original):")
    lines.append(f"  WPM: {orig['speech']['wpm']} words/min")
    lines.append(f"  Pause ratio: {orig['speech']['pause_ratio']}%")
    lines.append(f"  SPS (speech): {orig['speech']['sps_speech']:.3f} syllable/s")
    lines.append(f"  SPS (articulation): {orig['speech']['sps_articulation']:.3f} syllable/s")
    lines.append(f"  Average syllable duration: {orig['speech']['syllable_duration']:.3f} s/syllable")
    lines.append(f"  Mora duration: {orig['speech']['mora_duration']:.3f} s/mora")
    lines.append(f"  Word duration: {orig['speech']['word_duration']:.3f} s/word")

    # Acoustic metrics (original)
    lines.append(f"\nAcoustic metrics (original):")
    lines.append(f"  %V (articulate): {orig['acoustic']['percent_v_articulate']:.2f}%")
    lines.append(f"  %V (normal speech, incl. pauses): {orig['acoustic']['percent_v_speech']:.2f}%")
    lines.append(f"  ΔC: {orig['acoustic']['delta_c_seconds']:.4f} s")
    lines.append(f"  ΔC_mora: {orig['acoustic']['delta_c_mora']:.4f} mora")
    lines.append(f"  MeanC: {orig['acoustic']['mean_c_seconds']:.4f} s")
    lines.append(f"  MeanC_mora: {orig['acoustic']['mean_c_mora']:.4f} mora")
    lines.append(f"  VarcoC: {orig['acoustic']['varco_c']:.2f}")
    
    # --- ACCENTUATED TEXT ---
    lines.append("\n--- ACCENTUATED TEXT ---")
    rep = result['accentuated']
    
    # Syllable statistics
    lines.append("\nSyllable statistics:")
    lines.append("  Syllable types:")
    for typ in DISPLAY_SYLLABLE_TYPES:
        count = rep['stats']['syllable_counts'].get(typ, 0)
        pct = rep['stats']['syllable_percentages'].get(typ, 0)
        if count > 0:
            lines.append(f"    {typ:6}: {count:4d} syllables ({pct:5.2f}%)")

    lines.append(f"  Total syllables: {rep['stats']['total_syllables']} syllables")
    
    # Word statistics
    lines.append(f"\nWord statistics:")
    lines.append(f"  Total words: {rep['stats']['word_stats']['total_words']} words")
    lines.append(f"  Syllables per word: {rep['stats']['word_stats']['syllables_per_word']['mean']:.3f} ± {rep['stats']['word_stats']['syllables_per_word']['std']:.3f} syllable/word")

    # Mora statistics
    lines.append(f"\nMora statistics:")
    lines.append(f"  Mean morae per syllable: {rep['stats']['mora_stats']['mean']:.3f} ± {rep['stats']['mora_stats']['std']:.3f} mora/syllable")
    lines.append(f"  Mean morae per word: {rep['stats']['word_stats']['morae_per_word']['mean']:.3f} ± {rep['stats']['word_stats']['morae_per_word']['std']:.3f} mora/word")
    lines.append(f"  Total morae: {rep['stats']['mora_stats']['total']} mora")
    
    # Merge statistics
    lines.append(f"\nMerge statistics:")
    lines.append(f"  Merged words: {rep['stats']['merge_stats']['total_merged_words']} words")
    lines.append(f"  Merged units: {rep['stats']['merge_stats']['merged_units']} units")
    lines.append(f"  Average unit size: {rep['stats']['merge_stats']['avg_unit_size']:.2f} words")
    
    # Speech rate (accentuated)
    lines.append(f"\nSpeech rate (accentuated):")
    lines.append(f"  WPM: {rep['speech']['wpm']} words/min")
    lines.append(f"  Pause ratio: {rep['speech']['pause_ratio']}%")
    lines.append(f"  SPS (speech): {rep['speech']['sps_speech']:.3f} syllable/s")
    lines.append(f"  SPS (articulation): {rep['speech']['sps_articulation']:.3f} syllable/s")
    lines.append(f"  Average syllable duration: {rep['speech']['syllable_duration']:.3f} s/syllable")
    lines.append(f"  Mora duration: {rep['speech']['mora_duration']:.3f} s/mora")
    lines.append(f"  Word duration: {rep['speech']['word_duration']:.3f} s/word")

    # Acoustic metrics (accentuated)
    lines.append(f"\nAcoustic metrics (accentuated):")
    lines.append(f"  %V (articulate): {rep['acoustic']['percent_v_articulate']:.2f}%")
    lines.append(f"  %V (normal speech, incl. pauses): {rep['acoustic']['percent_v_speech']:.2f}%")
    lines.append(f"  ΔC: {rep['acoustic']['delta_c_seconds']:.4f} s")
    lines.append(f"  ΔC_mora: {rep['acoustic']['delta_c_mora']:.4f} mora")
    lines.append(f"  MeanC: {rep['acoustic']['mean_c_seconds']:.4f} s")
    lines.append(f"  MeanC_mora: {rep['acoustic']['mean_c_mora']:.4f} mora")
    lines.append(f"  VarcoC: {rep['acoustic']['varco_c']:.2f}")
    
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

    # --- ACCENTUATION STATISTICS ---
    lines.append("\n--- ACCENTUATION STATISTICS ---")
    rs = result['accentuation_stats']
    lines.append(f"  Accentuated syllables: {rs['accentuated_syllables']} syllables")
    lines.append(f"  Accentuation rate: {rs['accentuation_rate']:.2f}%")
    lines.append(f"\n  Accentuation types:")
    for typ, count in sorted(rs['accentuation_types'].items()):
        if count > 0:
            lines.append(f"    {typ:8}: {count:4d} syllables")
    
    lines.append("\n" + "="*80)
    return '\n'.join(lines) + '\n'


METRICS_CSV_DEPRECATION_MESSAGE = "--csv option is not anymore supported, the csv file will not be generated."


# ------------------------------------------------------------
# Unit tests
# ------------------------------------------------------------
def test_small_text() -> bool:
    """Test syllable counting on a small sample."""
    logger = get_logger_with_fallback(__name__)
    test_text = "šar gi·mir+dad~·mē bā·nû kib·rā~·ti"

    # Expected original counts (without accentuation)
    expected_original = {
        'CV': 2,   # gi, ti
        'CVC': 4,  # šar, mir, dad, kib
        'CVV': 4,  # mē, bā, nû, rā
        'total': 10
    }
    
    # Expected accentuated counts (with accentuation)
    expected_accentuated = {
        'CV': 2,      # gi, ti
        'CVC': 3,     # šar, mir, kib
        'CVV': 3,     # mē, bā, nû
        'CVC:': 1,    # dad~
        'CVV:': 1,    # rā~
        'total': 10
    }

    ok = True

    # Test original
    original_stats = analyze_text(test_text.replace('~', ''), is_accentuated=False)

    # Verify original counts
    for typ, expected in expected_original.items():
        if typ == 'total':
            continue
        actual = original_stats['syllable_counts'].get(typ, 0)
        if actual != expected:
            ok = False
            log_selftest_result(
                logger,
                False,
                'Metrics sample',
                f'Original {typ}',
                details=[
                    f'text={test_text!r}',
                    f'got={actual}',
                    f'expected={expected}',
                ],
            )

    total = sum(original_stats['syllable_counts'].values())
    if total != expected_original['total']:
        ok = False
        log_selftest_result(
            logger,
            False,
            'Metrics sample',
            'Original total',
            details=[
                f'text={test_text!r}',
                f'got={total}',
                f'expected={expected_original["total"]}',
            ],
        )

    # Test accentuated
    accentuated_stats = analyze_text(test_text, is_accentuated=True)

    # Verify accentuated counts
    for typ, expected in expected_accentuated.items():
        if typ == 'total':
            continue
        actual = accentuated_stats['syllable_counts'].get(typ, 0)
        if actual != expected:
            ok = False
            log_selftest_result(
                logger,
                False,
                'Metrics sample',
                f'Accentuated {typ}',
                details=[
                    f'text={test_text!r}',
                    f'got={actual}',
                    f'expected={expected}',
                ],
            )

    total = sum(accentuated_stats['syllable_counts'].values())
    if total != expected_accentuated['total']:
        ok = False
        log_selftest_result(
            logger,
            False,
            'Metrics sample',
            'Accentuated total',
            details=[
                f'text={test_text!r}',
                f'got={total}',
                f'expected={expected_accentuated["total"]}',
            ],
        )

    if ok:
        log_selftest_result(logger, True, 'Metrics sample', 'Small text syllable counting')
    return ok

def debug_mean_calculation(text: str, label: str):
    """Debug mean interval calculation."""
    logger = get_logger_with_fallback(__name__)
    logger.info('Debug MeanC | %s | text=%r', label, text)
    
    preprocessed = preprocess_text(text)
    logger.info('Debug MeanC | %s | preprocessed=%r', label, preprocessed)
    
    # Get segments and distances
    consonants, vowels = extract_segments(preprocessed)
    logger.info('Debug MeanC | %s | consonants=%s', label, consonants)
    logger.info('Debug MeanC | %s | vowels_after=%s', label, vowels)
    
    distances = compute_consonant_distances(consonants, vowels)
    logger.info('Debug MeanC | %s | distances=%s', label, distances)
    
    if distances:
        mean = sum(distances) / len(distances)
        logger.info('Debug MeanC | %s | mean=%.4f', label, mean)
    else:
        logger.info('Debug MeanC | %s | no distances', label)
    
    return distances
def _test_word_pattern_matching() -> bool:
    """Unit test: word pattern matching."""
    word_pattern = build_word_pattern()
    full_word_pattern = re.compile(f'^(?:{word_pattern.pattern})$')
    test_cases = [
        ('at·tā', True),
        ('˙a·na', True),
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
    for inp, should in test_cases:
        if bool(full_word_pattern.match(inp)) != should:
            return False
    return True


def _test_tokenizer() -> bool:
    """Unit test: tokenizer."""
    word_pattern = build_word_pattern()
    cases = [
        ('at·tā ā·lik', [('WORD', 'at·tā'), ('SPACES', ' '), ('WORD', 'ā·lik')]),
        ('at·tā, ā·lik!', [('WORD', 'at·tā'), ('PUNCT', ','), ('SPACES', ' '), ('WORD', 'ā·lik'), ('PUNCT', '!')]),
        ('ana+kâ·ša lu·ṣī-ma', [('WORD', 'ana+kâ·ša'), ('SPACES', ' '), ('WORD', 'lu·ṣī-ma')]),
        ('at·tā   ā·lik', [('WORD', 'at·tā'), ('SPACES', '   '), ('WORD', 'ā·lik')]),
        ('  at·tā ā·lik', [('SPACES', '  '), ('WORD', 'at·tā'), ('SPACES', ' '), ('WORD', 'ā·lik')]),
        ('at·tā ā·lik  ', [('WORD', 'at·tā'), ('SPACES', ' '), ('WORD', 'ā·lik'), ('SPACES', '  ')]),
    ]
    for inp, expected in cases:
        if tokenize_line(inp, word_pattern) != expected:
            return False
    return True


def _test_word_processing() -> bool:
    cases = [
        ('at·tā', 'ʾat·tā'),
        ('˙a·na', 'ʾa·na'),
        ('ā·lik', 'ʾā·lik'),
        ('maḫ·rim~-ma', 'maḫ·rim:-ma'),
        ('~a', ':a'),
        ('k~a', 'k:a'),
        ('dad~', 'dad:'),
    ]
    for inp, expected in cases:
        if process_word(inp) != expected:
            return False
    return True


def _test_preprocessing() -> bool:
    cases = [
        ('at·tā ā·lik', 'ʾat·tāʾā·lik'),
        ('˙a·na i·lī', 'ʾa·naʾi·lī'),
        ('maḫ·rim~-ma dad~', 'maḫ·rim:-madad:'),
        ('ana+kâ·ša lu·ṣī-ma', 'ʾana+kâ·šalu·ṣī-ma'),
    ]
    for inp, expected in cases:
        if preprocess_text(inp) != expected:
            return False
    return True


def _test_segment_extraction() -> bool:
    cases = [
        ('mas·ta', ['m', 's', 't'], ['a', '', 'a']),
        ('mas~·ta', ['m', 's', 't'], ['a', ':', 'a']),
        ('˙a·na', ['ʾ', 'n'], ['a', 'a']),
    ]
    for inp, exp_cons, exp_vows in cases:
        pre = preprocess_text(inp)
        cons, vows = extract_segments(pre)
        if cons != exp_cons or vows != exp_vows:
            return False
    return True


def _test_distance_calculation() -> bool:
    cases = [
        ('mas·ta', [1, 0, 1]),
        ('mas~·ta', [1, 1, 1]),
        ('a·na', [1, 1]),
    ]
    for inp, expected in cases:
        pre = preprocess_text(inp)
        cons, vows = extract_segments(pre)
        d = compute_consonant_distances(cons, vows)
        if d != expected:
            return False
    return True


def _test_consonant_distance_definitions() -> bool:
    """Regression test for core consonant-distance definitions used by DeltaC.

    Target definitions (between two consonants):
    - CC = 0
    - C:C = 1
    - CVC = 1
    - CVVC = 2
    - CVV:C = 3
    """
    # CC: use the s->t pair inside mas·ta (distances = [1, 0, 1]).
    pre = preprocess_text('mas·ta')
    cons, vows = extract_segments(pre)
    d = compute_consonant_distances(cons, vows)
    if len(d) < 2 or d[1] != 0:
        return False

    # C:C: s->t pair inside mas~·ta (mas:·ta after preprocessing).
    pre = preprocess_text('mas~·ta')
    cons, vows = extract_segments(pre)
    d = compute_consonant_distances(cons, vows)
    if len(d) < 2 or d[1] != 1:
        return False

    # CVC: m->s in ma·sa.
    pre = preprocess_text('ma·sa')
    cons, vows = extract_segments(pre)
    d = compute_consonant_distances(cons, vows)
    if not d or d[0] != 1:
        return False

    # CVVC: m->s in mā·sa.
    pre = preprocess_text('mā·sa')
    cons, vows = extract_segments(pre)
    d = compute_consonant_distances(cons, vows)
    if not d or d[0] != 2:
        return False

    # CVV:C: m->s in mà·sa.
    pre = preprocess_text('mà·sa')
    cons, vows = extract_segments(pre)
    d = compute_consonant_distances(cons, vows)
    if not d or d[0] != 3:
        return False

    return True


def _test_punctuation_marks_segment_boundaries() -> bool:
    """Punctuation must create WORD_BOUNDARY markers in preprocessing."""
    pre = preprocess_text('ab,ta')
    if WORD_BOUNDARY not in pre:
        return False
    return True


def _test_pause_metrics_grouping() -> bool:
    text = "at·tā ?!!! ā·lik ), i·lī ... bā·nû"
    stats = analyze_text(text, is_accentuated=True)
    pm = compute_pause_metrics(text, stats)
    if pm['raw_counts']['spaces'] != 0:
        return False
    if pm['raw_counts']['short_punctuation'] != 2:
        return False
    if pm['raw_counts']['long_punctuation'] != 2:
        return False
    return True


def _test_unknown_punctuation_raises() -> bool:
    text = "at·tā @ ā·lik"
    stats = analyze_text(text, is_accentuated=True)
    try:
        _ = compute_pause_metrics(text, stats)
        return False
    except PunctuationConfigError:
        return True


def _test_mora_totals_and_original_speech() -> bool:
    """Unit test: total morae and original speech metrics are exposed."""
    text = "tā·ḫā~·za ik~·ta·ṣar"
    result = process_filetext(
        text,
        wpm=165,
        pause_ratio=35.0,
        prominence_statistics={
            'function_word_count': 0,
            'explicit_word_link_count': 0,
        },
    )

    orig_total = result['original']['stats']['mora_stats']['total']
    accentuated_total = result['accentuated']['stats']['mora_stats']['total']
    if not isinstance(orig_total, int) or not isinstance(accentuated_total, int):
        return False
    # Original (without ~): tā·ḫā·za ik·ta·ṣar = 10 morae.
    if orig_total != 10:
        return False
    # Accentuated (with two ~): tā·ḫā~·za ik~·ta·ṣar = 12 morae.
    if accentuated_total != 12:
        return False
    if accentuated_total <= orig_total:
        return False

    orig_speech = result['original'].get('speech', {})
    accentuated_speech = result['accentuated'].get('speech', {})
    required = {'wpm', 'pause_ratio', 'sps_speech', 'sps_articulation', 'syllable_duration', 'mora_duration', 'word_duration'}
    if set(orig_speech.keys()) != required:
        return False
    if set(accentuated_speech.keys()) != required:
        return False

    # Morae per word must differ when accentuation adds morae.
    orig_mpw = result['original']['stats']['word_stats']['morae_per_word']['mean']
    accentuated_mpw = result['accentuated']['stats']['word_stats']['morae_per_word']['mean']
    if accentuated_mpw <= orig_mpw:
        return False

    return True


def _test_table_new_fields_and_no_csv() -> bool:
    """Unit test: table exposes current fields and CSV writer is removed."""
    text = "šar gi·mir+dad~·mē bā·nû kib·rā~·ti"
    result = process_filetext(
        text,
        wpm=165,
        pause_ratio=35.0,
        prominence_statistics={
            'function_word_count': 1,
            'explicit_word_link_count': 1,
        },
    )

    table = format_table(result)
    if "Syllable statistics:" not in table:
        return False
    if "Total morae:" not in table:
        return False
    if "Std dev morae per syllable:" in table:
        return False
    if "Total syllables:" not in table:
        return False
    if "Speech rate (original):" not in table:
        return False
    if "Speech rate (accentuated):" not in table:
        return False
    if "Prominence statistics:" not in table:
        return False
    if "Function words: 1 words" not in table:
        return False
    if "Explicitly linked words: 1 words" not in table:
        return False
    if "Prominence candidates: 2 words" not in table:
        return False
    if "ΔC_mora:" not in table or "MeanC_mora:" not in table:
        return False
    if "VarcoC: " not in table or "%" in "\n".join(
        line for line in table.splitlines() if "VarcoC:" in line
    ):
        return False

    # Ordering checks: word statistics must precede prominence and mora statistics.
    if table.find("Word statistics:") > table.find("Prominence statistics:"):
        return False
    if table.find("Prominence statistics:") > table.find("Mora statistics:"):
        return False

    # Ordering checks: speech blocks should come before acoustic blocks.
    if table.find("Speech rate (original):") > table.find("Acoustic metrics (original):"):
        return False
    if table.find("Speech rate (accentuated):") > table.find("Acoustic metrics (accentuated):"):
        return False
    return 'format_csv' not in globals()


def _test_small_corpus_metrics_consistency() -> bool:
    """Unit test: all core metrics equations stay consistent on a small corpus."""
    from akkapros.lib.prosody import AccentStyle, ProsodyEngine, parse_syl_line, postprocess_restore_diphthongs
    from akkapros.lib.syllabify import syllabify_text

    sample_proc = (
        "appūnā-ma ištēn-ešret : kīma šuāti uštabši\n"
        "ina ilī bukrīša : šūt iškunūši puḫra\n"
        "ušašqi qingu : ina birīšunu šâšu ušrabbīš\n"
        "ālikūt maḫri pān ummāni muʾerrūt puḫri\n"
    )

    syllabified = syllabify_text(sample_proc, preserve_lines=True)
    engine = ProsodyEngine(style=AccentStyle.LOB)
    accentuated_lines = []
    for line in syllabified.splitlines():
        if not line.strip():
            accentuated_lines.append('')
            continue
        accentuated_lines.append(engine.accentuation_line(parse_syl_line(line)))
    tilde_text = '\n'.join(postprocess_restore_diphthongs(accentuated_lines)) + '\n'

    result = process_filetext(
        tilde_text,
        wpm=165,
        pause_ratio=35.0,
        prominence_statistics={
            'function_word_count': 2,
            'explicit_word_link_count': 1,
        },
    )

    for section in ('original', 'accentuated'):
        stats = result[section]['stats']
        speech = result[section]['speech']
        total_syllables = stats['total_syllables']
        total_words = stats['word_stats']['total_words']
        total_morae = stats['mora_stats']['total']
        if sum(stats['syllable_counts'].values()) != total_syllables:
            return False
        if total_words <= 0:
            return False
        if not math.isclose(
            stats['word_stats']['syllables_per_word']['mean'],
            total_syllables / total_words,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            return False
        if not math.isclose(
            stats['word_stats']['morae_per_word']['mean'],
            total_morae / total_words,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            return False
        if not math.isclose(
            speech['sps_speech'],
            (speech['wpm'] / 60.0) * stats['word_stats']['syllables_per_word']['mean'],
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            return False

    pause_metrics = result['accentuated']['pause_metrics']
    accentuated_total_syllables = result['accentuated']['stats']['total_syllables']
    if not math.isclose(
        pause_metrics['punctuation_per_syllable'],
        pause_metrics['raw_counts']['punctuation'] / accentuated_total_syllables,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        return False

    accentuation_stats = result['accentuation_stats']
    original_total_syllables = result['original']['stats']['total_syllables']
    if not math.isclose(
        accentuation_stats['accentuation_rate'],
        accentuation_stats['accentuated_syllables'] / original_total_syllables * 100.0,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        return False

    table = format_table(result)
    if "Syllable statistics:" not in table:
        return False
    if f"Total syllables: {result['original']['stats']['total_syllables']} syllables" not in table:
        return False
    if f"Total syllables: {result['accentuated']['stats']['total_syllables']} syllables" not in table:
        return False
    if "Word statistics:" not in table or "Mora statistics:" not in table:
        return False
    if "Prominence statistics:" not in table:
        return False
    if table.find("Word statistics:") > table.find("Prominence statistics:"):
        return False
    if table.find("Prominence statistics:") > table.find("Mora statistics:"):
        return False
    if "Total morae number:" in table:
        return False

    return True


def _test_process_file_requires_frontmatter_prominence_counts() -> bool:
    document = (
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Metrics Test\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-28\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "    prosody:\n"
        "      explicit_word_link_count: 1\n"
        "---\n\n"
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n"
    )
    with tempfile.NamedTemporaryFile('w+', suffix='_tilde.txt', encoding='utf-8', delete=False) as handle:
        handle.write(document)
        temp_path = handle.name
    try:
        result = process_file(temp_path, wpm=165, pause_ratio=35.0)
    finally:
        Path(temp_path).unlink(missing_ok=True)

    prominence = result['original'].get('prominence_statistics') or {}
    return prominence == {
        'function_word_count': 0,
        'explicit_word_link_count': 1,
        'prominence_candidate_word_count': 3,
    }


def _test_process_file_missing_frontmatter_prominence_counts_fails() -> bool:
    document = (
        "---\n"
        "package:\n"
        "  name: \"akkapros\"\n"
        "  version: \"2.0.0\"\n"
        "pipeline: \"pipeline\"\n"
        "step: \"prosody\"\n"
        "file:\n"
        "  id: \"tilde-id\"\n"
        "  title: \"Metrics Test\"\n"
        "  format: \"tilde\"\n"
        "  version: \"1.0.0\"\n"
        "  date: \"2026-03-28\"\n"
        "metadata:\n"
        "  input_file_id: \"syl-id\"\n"
        "  options:\n"
        "    style: \"lob\"\n"
        "  data:\n"
        "---\n\n"
        "šar gi·mir+dad~·mē bā·nû kib·rā~·ti\n"
    )
    with tempfile.NamedTemporaryFile('w+', suffix='_tilde.txt', encoding='utf-8', delete=False) as handle:
        handle.write(document)
        temp_path = handle.name
    try:
        try:
            process_file(temp_path, wpm=165, pause_ratio=35.0)
            return False
        except ValueError as exc:
            return "missing required field" in str(exc)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _test_percent_v_fallback_safe() -> bool:
    """Unit test: %V fallback remains correct without cached mora totals."""
    stats = {
        'syllable_counts': {
            'CV': 2,
            'VC:': 1,
            'VV:C': 1,
            UNCLASSIFIED_SYLLABLE_TYPE: 5,
        },
        'mora_stats': {},
    }

    expected_vowel_morae = 2 * 1 + 1 * 1 + 1 * 3
    expected_total_morae = 2 * 1 + 1 * 3 + 1 * 4
    expected_percent_v = expected_vowel_morae / expected_total_morae * 100

    return math.isclose(
        compute_percent_v_from_stats(stats),
        expected_percent_v,
        rel_tol=0.0,
        abs_tol=1e-12,
    )


def run_tests():
    """Run the full test suite by composing unit chunks.

    This preserves the original `run_tests()` entrypoint while allowing
    pytest to import and execute individual `_test_...` functions.
    """
    suites = [
        ("Word pattern matching", _test_word_pattern_matching),
        ("Tokenizer", _test_tokenizer),
        ("Word processing", _test_word_processing),
        ("Preprocessing", _test_preprocessing),
        ("Segment extraction", _test_segment_extraction),
        ("Distance calculation", _test_distance_calculation),
        ("Consonant distance definitions", _test_consonant_distance_definitions),
        ("Punctuation segment boundaries", _test_punctuation_marks_segment_boundaries),
        ("Pause metrics grouping", _test_pause_metrics_grouping),
        ("Unknown punctuation strict error", _test_unknown_punctuation_raises),
        ("Mora totals and original speech", _test_mora_totals_and_original_speech),
        ("Table fields and CSV removal", _test_table_new_fields_and_no_csv),
        ("Small corpus metrics consistency", _test_small_corpus_metrics_consistency),
        ("Frontmatter prominence counts", _test_process_file_requires_frontmatter_prominence_counts),
        ("Missing frontmatter prominence fails", _test_process_file_missing_frontmatter_prominence_counts_fails),
        ("%V fallback safety", _test_percent_v_fallback_safe),
    ]

    logger = get_logger_with_fallback(__name__)
    return run_simple_selftest_suite(logger, 'Metrics', suites)


