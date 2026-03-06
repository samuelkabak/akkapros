#!/usr/bin/env python3
"""
Akkadian Diphone Recording Script Generator
Generates minimal set of words for MBROLATOR voice building
"""

import itertools
import random
import csv
from collections import defaultdict, Counter
from typing import Callable, Dict, List, Set, Tuple, Optional
import argparse
from pathlib import Path

# ============================================
# PHONEME INVENTORY
# ============================================

# Plain consonants (20)
PLAIN_CONSONANTS = ['b', 'd', 'g', 'k', 'p', 't', 's', 'z', 'š', 'l', 'm', 'n', 'r', 'w', 'y', 'ʾ', 'ḥ', 'ḫ', 'ʿ']

# Emphatic consonants (3)
EMPHATIC_CONSONANTS = ['q', 'ṣ', 'ṭ']

# All consonants
ALL_CONSONANTS = PLAIN_CONSONANTS + EMPHATIC_CONSONANTS

# Plain vowels (short and long)
PLAIN_VOWELS_SHORT = ['a', 'i', 'u', 'e']
PLAIN_VOWELS_LONG = ['ā', 'ī', 'ū', 'ē']
ALL_PLAIN_VOWELS = PLAIN_VOWELS_SHORT + PLAIN_VOWELS_LONG

# Colored vowels (short and long)
COLORED_VOWELS_SHORT = ['ɑ', 'ɨ', 'ʊ', 'ɛ']
COLORED_VOWELS_LONG = ['ɑ̄', 'ɨ̄', 'ʊ̄', 'ɛ̄']
ALL_COLORED_VOWELS = COLORED_VOWELS_SHORT + COLORED_VOWELS_LONG

# All vowels
ALL_VOWELS = ALL_PLAIN_VOWELS + ALL_COLORED_VOWELS

# Boundary symbol
BOUNDARY = '#'

# Long vowels are represented as repeated short vowels (x x), not single symbols.
LONG_TO_SHORT = {
    'ā': 'a',
    'ī': 'i',
    'ū': 'u',
    'ē': 'e',
    'ɑ̄': 'ɑ',
    'ɨ̄': 'ɨ',
    'ʊ̄': 'ʊ',
    'ɛ̄': 'ɛ',
}

# IPA output for human recording script (dataset.txt)
IPA_CONSONANT_MAP = {
    'ʾ': 'ʔ',
    'ʿ': 'ʕ',
    'ḥ': 'ħ',
    'ḫ': 'χ',
    'š': 'ʃ',
    'ṣ': 'sˤ',
    'ṭ': 'tˤ',
}

IPA_VOWEL_MAP = {
    'a': 'a', 'i': 'i', 'u': 'u', 'e': 'e',
    'ā': 'aː', 'ī': 'iː', 'ū': 'uː', 'ē': 'eː',
    'â': 'aː', 'î': 'iː', 'û': 'uː', 'ê': 'eː',
    'ɑ': 'ɑ', 'ɨ': 'ɨ', 'ʊ': 'ʊ', 'ɛ': 'ɛ',
    'ɑ̄': 'ɑː', 'ɨ̄': 'ɨː', 'ʊ̄': 'ʊː', 'ɛ̄': 'ɛː',
}

# MBROLA/X-SAMPA-like symbols for machine sidecars.
MBROLA_CONSONANT_MAP = {
    'ʾ': '?', 'ʿ': 'H',
    'b': 'b', 'd': 'd', 'g': 'g', 'k': 'k', 'p': 'p',
    'q': 'q', 't': 't', 's': 's', 'z': 'z', 'l': 'l', 'm': 'm', 'n': 'n',
    'r': 'r', 'w': 'w', 'y': 'j',
    'ḥ': 'X', 'ḫ': 'x', 'š': 'S', 'ṣ': 's.', 'ṭ': 't.',
}

MBROLA_VOWEL_MAP = {
    'a': 'a', 'i': 'i', 'u': 'u', 'e': 'e',
    'ā': 'a a', 'ī': 'i i', 'ū': 'u u', 'ē': 'e e',
    'â': 'a a', 'î': 'i i', 'û': 'u u', 'ê': 'e e',
    'ɑ': 'a.', 'ɨ': 'i.', 'ʊ': 'u.', 'ɛ': 'e.',
    'ɑ̄': 'a. a.', 'ɨ̄': 'i. i.', 'ʊ̄': 'u. u.', 'ɛ̄': 'e. e.',
}


def unique_preserve_order(items: List[str]) -> List[str]:
    """Return unique values preserving first-seen order."""
    seen = set()
    out: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def normalize_long_vowels_to_short(short_list: List[str], long_list: List[str]) -> List[str]:
    """Fold one-symbol long vowels into short inventory (longs are realized as x x)."""
    folded_longs = [LONG_TO_SHORT.get(v, v) for v in long_list]
    return unique_preserve_order(short_list + folded_longs)


def to_ipa_symbol(symbol: str) -> str:
    if symbol in IPA_VOWEL_MAP:
        return IPA_VOWEL_MAP[symbol]
    if symbol in IPA_CONSONANT_MAP:
        return IPA_CONSONANT_MAP[symbol]
    return symbol


def to_mbrola_symbol(symbol: str) -> str:
    if symbol == BOUNDARY:
        return '_'
    if symbol in MBROLA_VOWEL_MAP:
        return MBROLA_VOWEL_MAP[symbol]
    if symbol in MBROLA_CONSONANT_MAP:
        return MBROLA_CONSONANT_MAP[symbol]
    return symbol


def map_word_symbols(word: List[str], mapper: Callable[[str], str]) -> List[str]:
    return [mapper(sym) for sym in word]


def map_diphones_symbols(diphones: List[str], mapper: Callable[[str], str]) -> List[str]:
    mapped: List[str] = []
    for dip in diphones:
        left, right = dip.split('-', 1)
        mapped.append(f"{mapper(left)}-{mapper(right)}")
    return mapped


def unique_preserve_pairs(items: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Return unique pair values preserving first-seen order."""
    seen: Set[Tuple[str, str]] = set()
    out: List[Tuple[str, str]] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def parse_symbol_list(raw: str) -> List[str]:
    """Parse comma or whitespace separated symbols into a list."""
    return [tok.strip() for tok in raw.replace(',', ' ').split() if tok.strip()]


def set_active_inventory(
    plain_consonants: List[str],
    emphatic_consonants: List[str],
    plain_vowels_short: List[str],
    plain_vowels_long: List[str],
    colored_vowels_short: List[str],
    colored_vowels_long: List[str],
) -> None:
    """Replace module-level inventory lists for runtime debug/experiments."""
    global PLAIN_CONSONANTS, EMPHATIC_CONSONANTS, ALL_CONSONANTS
    global PLAIN_VOWELS_SHORT, PLAIN_VOWELS_LONG, ALL_PLAIN_VOWELS
    global COLORED_VOWELS_SHORT, COLORED_VOWELS_LONG, ALL_COLORED_VOWELS, ALL_VOWELS

    PLAIN_CONSONANTS = plain_consonants
    EMPHATIC_CONSONANTS = emphatic_consonants
    ALL_CONSONANTS = PLAIN_CONSONANTS + EMPHATIC_CONSONANTS

    PLAIN_VOWELS_SHORT = normalize_long_vowels_to_short(plain_vowels_short, plain_vowels_long)
    # Long vowels are represented as doubled shorts, so no one-symbol longs stay active.
    PLAIN_VOWELS_LONG = []
    ALL_PLAIN_VOWELS = PLAIN_VOWELS_SHORT

    COLORED_VOWELS_SHORT = normalize_long_vowels_to_short(colored_vowels_short, colored_vowels_long)
    # Long vowels are represented as doubled shorts, so no one-symbol longs stay active.
    COLORED_VOWELS_LONG = []
    ALL_COLORED_VOWELS = COLORED_VOWELS_SHORT

    ALL_VOWELS = ALL_PLAIN_VOWELS + ALL_COLORED_VOWELS


# ============================================
# VALIDITY RULES
# ============================================

def is_vowel_plain(v: str) -> bool:
    return v in ALL_PLAIN_VOWELS

def is_vowel_colored(v: str) -> bool:
    return v in ALL_COLORED_VOWELS

def is_consonant_plain(c: str) -> bool:
    return c in PLAIN_CONSONANTS

def is_consonant_emphatic(c: str) -> bool:
    return c in EMPHATIC_CONSONANTS


def is_vv_diphone(diphone: str) -> bool:
    """True if both sides of the diphone are vowels (V-V)."""
    left, right = diphone.split('-', 1)
    return left in ALL_VOWELS and right in ALL_VOWELS


def is_vv_class_legal(left_vowel: str, right_vowel: str) -> bool:
    """V-V is legal only when both vowels share the same class (plain/plain or colored/colored)."""
    return (is_vowel_plain(left_vowel) and is_vowel_plain(right_vowel)) or (
        is_vowel_colored(left_vowel) and is_vowel_colored(right_vowel)
    )

def is_vowel_valid(v: str, left: Optional[str], right: Optional[str]) -> bool:
    """
    Check if a vowel is valid in its context.

    Updated rule: coloring is post-emphatic only.
    A vowel is colored only when the PRECEDING consonant is emphatic (q/ṣ/ṭ).
    Colored vowels before emphatics are illegal.
    """
    # Word-initial (left is boundary): no preceding emphatic exists, so only plain vowels are legal.
    if left == BOUNDARY:
        return is_vowel_plain(v) and right is not None and (is_consonant_plain(right) or is_consonant_emphatic(right))

    # Word-final (right is boundary): quality depends on left consonant only.
    if right == BOUNDARY:
        if not (left is not None and (is_consonant_plain(left) or is_consonant_emphatic(left))):
            return False
        if is_consonant_emphatic(left):
            return is_vowel_colored(v)
        return is_vowel_plain(v)

    # Word-medial (both sides consonants): quality depends on left consonant only.
    left_valid = left is not None and (is_consonant_plain(left) or is_consonant_emphatic(left))
    right_valid = right is not None and (is_consonant_plain(right) or is_consonant_emphatic(right))
    if not (left_valid and right_valid):
        return False

    if is_consonant_emphatic(left):
        return is_vowel_colored(v)
    return is_vowel_plain(v)


# ============================================
# DIPHONE EXTRACTION
# ============================================

def extract_diphones_pattern1(word: List[str]) -> List[str]:
    """
    Extract diphones from Pattern 1: _ V C C V C C V _
    Positions: [V1, C2, C3, V2, C4, C5, V3]
    """
    diphones = []
    
    # _-V1
    diphones.append(f"{BOUNDARY}-{word[0]}")
    
    # V1-C2
    diphones.append(f"{word[0]}-{word[1]}")
    
    # C2-C3
    diphones.append(f"{word[1]}-{word[2]}")
    
    # C3-V2
    diphones.append(f"{word[2]}-{word[3]}")
    
    # V2-C4
    diphones.append(f"{word[3]}-{word[4]}")
    
    # C4-C5
    diphones.append(f"{word[4]}-{word[5]}")
    
    # C5-V3
    diphones.append(f"{word[5]}-{word[6]}")
    
    # V3-_
    diphones.append(f"{word[6]}-{BOUNDARY}")
    
    return diphones


def extract_diphones_pattern2(word: List[str]) -> List[str]:
    """
    Extract diphones from Pattern 2: _ C V C V C C V C _
    Positions: [C1, V2, C3, V4, C5, C6, V7, C8]
    """
    diphones = []
    
    # _-C1
    diphones.append(f"{BOUNDARY}-{word[0]}")
    
    # C1-V2
    diphones.append(f"{word[0]}-{word[1]}")
    
    # V2-C3
    diphones.append(f"{word[1]}-{word[2]}")
    
    # C3-V4
    diphones.append(f"{word[2]}-{word[3]}")
    
    # V4-C5
    diphones.append(f"{word[3]}-{word[4]}")
    
    # C5-C6
    diphones.append(f"{word[4]}-{word[5]}")
    
    # C6-V7
    diphones.append(f"{word[5]}-{word[6]}")
    
    # V7-C8
    diphones.append(f"{word[6]}-{word[7]}")
    
    # C8-_
    diphones.append(f"{word[7]}-{BOUNDARY}")
    
    return diphones


def extract_diphones_pattern3(word: List[str]) -> List[str]:
    """
    Extract diphones from Pattern 3: _ C V V C V V C _
    Positions: [C1, V2, V3, C4, V5, V6, C7]
    """
    diphones = []
    
    # _-C1
    diphones.append(f"{BOUNDARY}-{word[0]}")
    
    # C1-V2
    diphones.append(f"{word[0]}-{word[1]}")
    
    # V2-V3
    diphones.append(f"{word[1]}-{word[2]}")
    
    # V3-C4
    diphones.append(f"{word[2]}-{word[3]}")
    
    # C4-V5
    diphones.append(f"{word[3]}-{word[4]}")
    
    # V5-V6
    diphones.append(f"{word[4]}-{word[5]}")
    
    # V6-C7
    diphones.append(f"{word[5]}-{word[6]}")
    
    # C7-_
    diphones.append(f"{word[6]}-{BOUNDARY}")
    
    return diphones


def consonants_for_pattern(word: List[str], pattern: int) -> List[str]:
    """Return consonant sequence in left-to-right order for a generated word."""
    if pattern == 1:
        return [word[1], word[2], word[4], word[5]]
    if pattern == 2:
        return [word[0], word[2], word[4], word[5], word[7]]
    return [word[0], word[3], word[6]]


def is_plain_emphatic_alternating(word: List[str], pattern: int) -> bool:
    """True if adjacent consonants alternate plain/emphatic classes."""
    consonants = consonants_for_pattern(word, pattern)
    if not consonants:
        return False

    has_plain = any(is_consonant_plain(c) for c in consonants)
    has_emphatic = any(is_consonant_emphatic(c) for c in consonants)
    if not (has_plain and has_emphatic):
        return False

    for left, right in zip(consonants, consonants[1:]):
        if (is_consonant_plain(left) and is_consonant_plain(right)) or (
            is_consonant_emphatic(left) and is_consonant_emphatic(right)
        ):
            return False
    return True


# ============================================
# WORD VALIDATION
# ============================================

def validate_pattern1(word: List[str]) -> bool:
    """Validate a Pattern 1 word: _ V C C V C C V _"""
    if len(word) != 7:
        return False
    
    V1, C2, C3, V2, C4, C5, V3 = word
    
    # Check each vowel in its context
    if not is_vowel_valid(V1, BOUNDARY, C2):
        return False
    if not is_vowel_valid(V2, C3, C4):
        return False
    if not is_vowel_valid(V3, C5, BOUNDARY):
        return False
    
    return True


def validate_pattern2(word: List[str]) -> bool:
    """Validate a Pattern 2 word: _ C V C V C C V C _"""
    if len(word) != 8:
        return False
    
    C1, V2, C3, V4, C5, C6, V7, C8 = word
    
    # Check each vowel in its context
    if not is_vowel_valid(V2, C1, C3):
        return False
    if not is_vowel_valid(V4, C3, C5):
        return False
    if not is_vowel_valid(V7, C6, C8):
        return False
    
    return True


def validate_pattern3(word: List[str]) -> bool:
    """Validate a Pattern 3 word: _ C V V C V V C _"""
    if len(word) != 7:
        return False
    
    C1, V2, V3, C4, V5, V6, C7 = word

    # In CVVC units, V-V must not mix plain and colored classes.
    if not is_vv_class_legal(V2, V3):
        return False
    if not is_vv_class_legal(V5, V6):
        return False
    
    # In CVVC, both vowels are evaluated against the same surrounding consonants.
    if not is_vowel_valid(V2, C1, C4):
        return False
    if not is_vowel_valid(V3, C1, C4):
        return False
    if not is_vowel_valid(V5, C4, C7):
        return False
    if not is_vowel_valid(V6, C4, C7):
        return False
    
    return True


# ============================================
# WORD GENERATORS
# ============================================

def generate_all_pattern1_words() -> List[Tuple[List[str], int]]:
    """Generate all valid Pattern 1 words."""
    words = []
    
    # For each combination of vowels and consonants
    for V1 in ALL_VOWELS:
        for C2 in ALL_CONSONANTS:
            # Early prune: check V1 with C2
            if not is_vowel_valid(V1, BOUNDARY, C2):
                continue
                
            for C3 in ALL_CONSONANTS:
                for V2 in ALL_VOWELS:
                    # Check V2 with C3 and upcoming C4 (will check fully later)
                    for C4 in ALL_CONSONANTS:
                        for C5 in ALL_CONSONANTS:
                            for V3 in ALL_VOWELS:
                                word = [V1, C2, C3, V2, C4, C5, V3]
                                if validate_pattern1(word):
                                    words.append((word, 1))
    
    return words


def generate_all_pattern2_words() -> List[Tuple[List[str], int]]:
    """Generate all valid Pattern 2 words."""
    words = []
    
    for C1 in ALL_CONSONANTS:
        for V2 in ALL_VOWELS:
            for C3 in ALL_CONSONANTS:
                if not is_vowel_valid(V2, C1, C3):
                    continue
                for V4 in ALL_VOWELS:
                    for C5 in ALL_CONSONANTS:
                        for C6 in ALL_CONSONANTS:
                            for V7 in ALL_VOWELS:
                                for C8 in ALL_CONSONANTS:
                                    word = [C1, V2, C3, V4, C5, C6, V7, C8]
                                    if validate_pattern2(word):
                                        words.append((word, 2))
    
    return words


def generate_all_pattern3_words() -> List[Tuple[List[str], int]]:
    """Generate all valid Pattern 3 words."""
    words = []
    
    for C1 in ALL_CONSONANTS:
        for V2 in ALL_VOWELS:
            for V3 in ALL_VOWELS:
                for C4 in ALL_CONSONANTS:
                    # First CVVC chunk must be valid against consonantal frame C1...C4.
                    if not is_vowel_valid(V2, C1, C4):
                        continue
                    if not is_vowel_valid(V3, C1, C4):
                        continue
                    for V5 in ALL_VOWELS:
                        for V6 in ALL_VOWELS:
                            for C7 in ALL_CONSONANTS:
                                if not is_vowel_valid(V5, C4, C7):
                                    continue
                                if not is_vowel_valid(V6, C4, C7):
                                    continue
                                word = [C1, V2, V3, C4, V5, V6, C7]
                                if validate_pattern3(word):
                                    words.append((word, 3))
    
    return words


def vowel_pool_for_left(left: str) -> List[str]:
    """Return legal vowel class after left segment under post-emphatic rule."""
    if left == BOUNDARY:
        return ALL_PLAIN_VOWELS
    if is_consonant_emphatic(left):
        return ALL_COLORED_VOWELS
    return ALL_PLAIN_VOWELS


def compute_reachable_diphone_inventory() -> Set[str]:
    """Compute reachable diphones from inventory/rules without enumerating all words."""
    diphones: Set[str] = set()

    # Boundary-consonant (patterns 2/3)
    for c in ALL_CONSONANTS:
        diphones.add(f"{BOUNDARY}-{c}")
        diphones.add(f"{c}-{BOUNDARY}")

    # Boundary-vowel / vowel-boundary (pattern 1)
    for v in ALL_PLAIN_VOWELS:
        diphones.add(f"{BOUNDARY}-{v}")

    for c in ALL_CONSONANTS:
        for v in vowel_pool_for_left(c):
            diphones.add(f"{v}-{BOUNDARY}")

    # C-C is unconstrained by vowel legality in patterns 1/2
    for c1 in ALL_CONSONANTS:
        for c2 in ALL_CONSONANTS:
            diphones.add(f"{c1}-{c2}")

    # V-C and C-V with post-emphatic conditioning
    for c_left in ALL_CONSONANTS:
        for v in vowel_pool_for_left(c_left):
            diphones.add(f"{c_left}-{v}")  # C-V
            for c_right in ALL_CONSONANTS:
                diphones.add(f"{v}-{c_right}")  # V-C

    # Initial V-C from pattern 1 starts plain only
    for v in ALL_PLAIN_VOWELS:
        for c in ALL_CONSONANTS:
            diphones.add(f"{v}-{c}")

    # V-V from pattern 3: same class only
    for c in ALL_CONSONANTS:
        pool = vowel_pool_for_left(c)
        for v1 in pool:
            for v2 in pool:
                diphones.add(f"{v1}-{v2}")

    return diphones


def random_valid_word(pattern: int) -> List[str]:
    """Sample a valid word for a pattern directly from legality constraints."""
    if pattern == 1:
        C2 = random.choice(ALL_CONSONANTS)
        C3 = random.choice(ALL_CONSONANTS)
        C4 = random.choice(ALL_CONSONANTS)
        C5 = random.choice(ALL_CONSONANTS)
        V1 = random.choice(ALL_PLAIN_VOWELS)
        V2 = random.choice(vowel_pool_for_left(C3))
        V3 = random.choice(vowel_pool_for_left(C5))
        return [V1, C2, C3, V2, C4, C5, V3]

    if pattern == 2:
        C1 = random.choice(ALL_CONSONANTS)
        C3 = random.choice(ALL_CONSONANTS)
        C5 = random.choice(ALL_CONSONANTS)
        C6 = random.choice(ALL_CONSONANTS)
        C8 = random.choice(ALL_CONSONANTS)
        V2 = random.choice(vowel_pool_for_left(C1))
        V4 = random.choice(vowel_pool_for_left(C3))
        V7 = random.choice(vowel_pool_for_left(C6))
        return [C1, V2, C3, V4, C5, C6, V7, C8]

    C1 = random.choice(ALL_CONSONANTS)
    C4 = random.choice(ALL_CONSONANTS)
    C7 = random.choice(ALL_CONSONANTS)
    pool1 = vowel_pool_for_left(C1)
    pool2 = vowel_pool_for_left(C4)
    V2 = random.choice(pool1)
    V3 = random.choice(pool1)
    V5 = random.choice(pool2)
    V6 = random.choice(pool2)
    return [C1, V2, V3, C4, V5, V6, C7]


# ============================================
# COVERAGE OPTIMIZER
# ============================================

class CoverageOptimizer:
    def __init__(
        self,
        target_coverage: int = 3,
        possible_diphones: Optional[Set[str]] = None,
        max_non_vv_occurrences: Optional[int] = None,
        non_vv_target_ratio: float = 0.8,
        strict_non_vv_cap: bool = False,
    ):
        self.target_coverage = target_coverage
        self.max_non_vv_occurrences = max_non_vv_occurrences
        self.non_vv_target_ratio = non_vv_target_ratio
        self.strict_non_vv_cap = strict_non_vv_cap
        self.coverage = defaultdict(int)
        self.selected_words = []
        self.seen_words: Set[Tuple[int, Tuple[str, ...]]] = set()
        self.all_diphones = possible_diphones if possible_diphones is not None else set()

    def word_key(self, word: List[str], pattern: int) -> Tuple[int, Tuple[str, ...]]:
        return (pattern, tuple(word))

    def effective_target(self, diphone: str) -> int:
        """Target coverage for a diphone after applying optional non-VV cap."""
        if is_vv_diphone(diphone):
            # In capped mode, V-V diphones are optional and may exceed target freely.
            if self.max_non_vv_occurrences is not None:
                return 0
            return self.target_coverage
        if self.max_non_vv_occurrences is None:
            return self.target_coverage
        return min(self.target_coverage, self.max_non_vv_occurrences)

    def can_add_word(self, word: List[str], pattern: int) -> bool:
        """Check whether adding this word would violate non-VV max-occurrence limits."""
        if self.word_key(word, pattern) in self.seen_words:
            return False
        if self.max_non_vv_occurrences is None or not self.strict_non_vv_cap:
            return True
        for d in self.word_diphones(word, pattern):
            if not is_vv_diphone(d) and self.coverage[d] >= self.max_non_vv_occurrences:
                return False
        return True

    def required_diphones(self) -> List[str]:
        """Diphones that count toward the completion objective."""
        if self.max_non_vv_occurrences is not None:
            return [d for d in self.all_diphones if not is_vv_diphone(d)]
        return [d for d in self.all_diphones if self.effective_target(d) > 0]

    def target_met_count(self) -> int:
        """How many required diphones reached effective target."""
        required = self.required_diphones()
        return sum(1 for d in required if self.coverage[d] >= self.effective_target(d))

    def target_met_ratio(self) -> float:
        """Share of required diphones that reached target."""
        required = self.required_diphones()
        if not required:
            return 1.0
        return self.target_met_count() / len(required)
    
    def word_diphones(self, word: List[str], pattern: int) -> List[str]:
        """Get diphones from a word."""
        if pattern == 1:
            return extract_diphones_pattern1(word)
        elif pattern == 2:
            return extract_diphones_pattern2(word)
        else:
            return extract_diphones_pattern3(word)
    
    def word_score(self, word: List[str], pattern: int) -> float:
        """Score a word based on needed diphones."""
        if not self.can_add_word(word, pattern):
            return -1.0

        diphones = self.word_diphones(word, pattern)

        score = 0.0
        needed_hits = 0
        for d in diphones:
            current = self.coverage[d]
            target = self.effective_target(d)
            if current < target:
                needed_hits += 1
                # Prefer words that cover currently underrepresented required diphones.
                score += (target - current) * 20.0
                # Small rarity bonus so low-count diphones get lifted earlier.
                score += 1.0 / (1.0 + current)

        # Reject words that do not advance required diphone coverage.
        if needed_hits == 0:
            return -1.0

        score += needed_hits * 5.0
        return score
    
    def add_word(self, word: List[str], pattern: int):
        """Add a word and update coverage."""
        if not self.can_add_word(word, pattern):
            return
        self.selected_words.append((word, pattern))
        self.seen_words.add(self.word_key(word, pattern))
        for d in self.word_diphones(word, pattern):
            self.coverage[d] += 1
    
    def is_complete(self) -> bool:
        """Check if all diphones have reached target coverage."""
        if self.max_non_vv_occurrences is not None and not self.strict_non_vv_cap:
            return self.target_met_ratio() >= self.non_vv_target_ratio

        for d in self.all_diphones:
            if self.coverage[d] < self.effective_target(d):
                return False
        return True
    
    def coverage_summary(self) -> Dict:
        """Return coverage statistics."""
        required = self.required_diphones()
        values = [self.coverage[d] for d in required]
        total = len(required)
        complete = sum(1 for d in required if self.coverage[d] >= self.effective_target(d))
        vv_total = sum(1 for d in self.all_diphones if is_vv_diphone(d))
        vv_avg = (
            sum(self.coverage[d] for d in self.all_diphones if is_vv_diphone(d)) / vv_total
            if vv_total
            else 0
        )
        
        return {
            'total': total,
            'complete': complete,
            'below': total - complete,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0,
            'avg': sum(values) / total if values else 0,
            'vv_total': vv_total,
            'vv_avg': vv_avg,
            'ratio': (complete / total) if total else 1.0,
        }


# ============================================
# MAIN GENERATION
# ============================================

def generate_script(
    target_coverage: int = 3,
    max_non_vv_occurrences: Optional[int] = None,
    non_vv_target_ratio: float = 0.8,
    strict_non_vv_cap: bool = False,
    candidate_filter: Optional[Callable[[List[str], int], bool]] = None,
    max_iterations: int = 200000,
    candidate_pool_size: int = 32,
) -> List[Tuple[List[str], int]]:
    """Generate minimal recording script."""
    print("Building reachable diphone inventory once...")
    reachable_diphones = compute_reachable_diphone_inventory()
    print(f"Reachable diphone inventory size: {len(reachable_diphones)}")
    
    # Initialize optimizer
    optimizer = CoverageOptimizer(
        target_coverage,
        possible_diphones=reachable_diphones,
        max_non_vv_occurrences=max_non_vv_occurrences,
        non_vv_target_ratio=non_vv_target_ratio,
        strict_non_vv_cap=strict_non_vv_cap,
    )
    
    print(f"\nBuilding minimal set with target coverage = {target_coverage}...")
    if max_non_vv_occurrences is not None:
        if strict_non_vv_cap:
            print(f"Applying STRICT non-VV max occurrences cap: {max_non_vv_occurrences} (V-V unlimited)")
        else:
            print(
                f"Applying SOFT non-VV target around {max_non_vv_occurrences} "
                f"with completion ratio >= {non_vv_target_ratio:.0%} (V-V unlimited)"
            )
    
    sampled = 0
    accepted = 0
    pattern_counts = {1: 0, 2: 0, 3: 0}

    # Stochastic greedy selection from valid-by-construction words.
    # In each round, pick the best candidate from a random pool.
    for _ in range(max_iterations):
        if optimizer.is_complete():
            break

        best_score = -1.0
        best_candidate: Optional[Tuple[List[str], int]] = None

        for _candidate in range(candidate_pool_size):
            pattern = random.choice([1, 2, 3])
            word = random_valid_word(pattern)
            sampled += 1

            if candidate_filter is not None and not candidate_filter(word, pattern):
                continue

            score = optimizer.word_score(word, pattern)
            if score > best_score:
                best_score = score
                best_candidate = (word, pattern)

        if best_candidate is None or best_score <= 0:
            continue

        before = len(optimizer.selected_words)
        optimizer.add_word(best_candidate[0], best_candidate[1])
        if len(optimizer.selected_words) > before:
            accepted += 1
            pattern_counts[best_candidate[1]] += 1

    print(f"Sampled candidates: {sampled}")
    print(f"Candidate pool size per selection round: {candidate_pool_size}")
    print(f"Accepted words: {accepted}")
    print(
        f"Accepted by pattern: P1={pattern_counts[1]}, "
        f"P2={pattern_counts[2]}, P3={pattern_counts[3]}"
    )

    if not optimizer.is_complete():
        print(
            "WARNING: Reached max iterations before completion target. "
            "Increase --max-iterations or relax constraints."
        )
    
    return optimizer.selected_words, optimizer.coverage_summary()


# ============================================
# OUTPUT FORMATTING
# ============================================

def format_word(word: List[str], pattern: int) -> str:
    """Format a word as IPA with dotted syllable boundaries for easier reading."""
    ipa_word = map_word_symbols(word, to_ipa_symbol)

    if pattern == 1:
        # Pattern 1: VC.CVC.CV
        syllables = [
            ''.join(ipa_word[0:2]),
            ''.join(ipa_word[2:5]),
            ''.join(ipa_word[5:7]),
        ]
    elif pattern == 2:
        # Pattern 2: CV.CVC.CVC
        syllables = [
            ''.join(ipa_word[0:2]),
            ''.join(ipa_word[2:5]),
            ''.join(ipa_word[5:8]),
        ]
    else:
        # Pattern 3: CVV.CVVC
        syllables = [
            ''.join(ipa_word[0:3]),
            ''.join(ipa_word[3:7]),
        ]

    return f"_{'.'.join(syllables)}_"


def inventory_as_ipa(symbols: List[str]) -> List[str]:
    """Map inventory symbols to IPA for human-readable console summaries."""
    return [to_ipa_symbol(sym) for sym in symbols]


def ipa_to_mbrola_mapping_list() -> List[Tuple[str, str]]:
    """Return IPA -> MBROLA mapping pairs used by this script."""
    inventory = ALL_CONSONANTS + ALL_VOWELS
    pairs = [(to_ipa_symbol(sym), to_mbrola_symbol(sym)) for sym in inventory]
    return unique_preserve_pairs(pairs)


def word_diphones(word: List[str], pattern: int) -> List[str]:
    """Extract diphones for one generated word."""
    if pattern == 1:
        return extract_diphones_pattern1(word)
    if pattern == 2:
        return extract_diphones_pattern2(word)
    return extract_diphones_pattern3(word)


def build_manifest_rows(
    words_with_patterns: List[Tuple[List[str], int]],
    batch: str,
    start_utterance_id: int = 1,
) -> List[Dict[str, str]]:
    """Build MBROLA-symbol rows for downstream alignment/segmentation tools."""
    rows: List[Dict[str, str]] = []
    utterance_id = start_utterance_id
    for word, pattern in words_with_patterns:
        dips = map_diphones_symbols(word_diphones(word, pattern), to_mbrola_symbol)
        word_mbrola = map_word_symbols(word, to_mbrola_symbol)
        rows.append(
            {
                'utterance_id': str(utterance_id),
                'batch': batch,
                'pattern': str(pattern),
                'word_spaced': ' '.join(word_mbrola),
                'word_script': f"_{' '.join(word_mbrola)}_",
                'diphone_count': str(len(dips)),
                'diphones': ' '.join(dips),
            }
        )
        utterance_id += 1
    return rows


def write_alignment_sidecars(output_script_path: str, manifest_rows: List[Dict[str, str]]) -> None:
    """Write sidecar files used by silence-chunk matching and segment cursor building."""
    out_path = Path(output_script_path)
    stem = out_path.with_suffix('')
    manifest_path = stem.with_name(f"{stem.name}_manifest.tsv")
    diphones_path = stem.with_name(f"{stem.name}_diphones.tsv")
    words_path = stem.with_name(f"{stem.name}_words.txt")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                'utterance_id',
                'batch',
                'pattern',
                'word_spaced',
                'word_script',
                'diphone_count',
                'diphones',
            ],
            delimiter='\t',
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    with diphones_path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.writer(fh, delimiter='\t')
        writer.writerow(['utterance_id', 'batch', 'pattern', 'diphone_index', 'diphone'])
        for row in manifest_rows:
            dips = row['diphones'].split()
            for i, dip in enumerate(dips, 1):
                writer.writerow([
                    row['utterance_id'],
                    row['batch'],
                    row['pattern'],
                    str(i),
                    dip,
                ])

    with words_path.open('w', encoding='utf-8') as fh:
        for row in manifest_rows:
            fh.write(f"{row['word_script']}\n")

    print(f"Manifest written to {manifest_path}")
    print(f"Diphone cursor file written to {diphones_path}")
    print(f"Word list (one per line) written to {words_path}")


def write_script(words_with_patterns: List[Tuple[List[str], int]], 
                 filename: str, 
                 coverage: int):
    """Write the script to a file."""
    
    # Group by pattern
    pattern1_words = [(w, p) for w, p in words_with_patterns if p == 1]
    pattern2_words = [(w, p) for w, p in words_with_patterns if p == 2]
    pattern3_words = [(w, p) for w, p in words_with_patterns if p == 3]
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# ============================================\n")
        f.write(f"# AKKADIAN DIPHONE RECORDING SCRIPT\n")
        f.write(f"# Target coverage: {coverage}\n")
        f.write("# ============================================\n\n")
        
        f.write("# Patterns:\n")
        f.write("# Pattern 1: _ V C C V C C V _  -> VC.CVC.CV\n")
        f.write("# Pattern 2: _ C V C V C C V C _  -> CV.CVC.CVC\n")
        f.write("# Pattern 3: _ C V V C V V C _  -> CVV.CVVC\n\n")
        
        f.write("# Instructions:\n")
        f.write("# - Speak each line naturally\n")
        f.write("# - Pause 1 second before and after each word\n")
        f.write("# - Record at 16kHz, 16-bit, mono\n\n")
        
        # Pattern 1
        f.write("# ========== PATTERN 1 (VCCVCCV) ==========\n")
        f.write(f"# {len(pattern1_words)} words\n\n")
        for i, (word, _) in enumerate(pattern1_words, 1):
            if i % 20 == 1:
                f.write(f"# Block {i//20 + 1}\n")
            f.write(f"{format_word(word, 1)}\n")
        
        # Pattern 2
        f.write("\n# ========== PATTERN 2 (CVCVCCVC) ==========\n")
        f.write(f"# {len(pattern2_words)} words\n\n")
        for i, (word, _) in enumerate(pattern2_words, 1):
            if i % 20 == 1:
                f.write(f"# Block {i//20 + 1}\n")
            f.write(f"{format_word(word, 2)}\n")
        
        # Pattern 3
        f.write("\n# ========== PATTERN 3 (CVVCVVC) ==========\n")
        f.write(f"# {len(pattern3_words)} words\n\n")
        for i, (word, _) in enumerate(pattern3_words, 1):
            if i % 20 == 1:
                f.write(f"# Block {i//20 + 1}\n")
            f.write(f"{format_word(word, 3)}\n")
        
        # Summary
        f.write("\n# ============================================\n")
        f.write("# SUMMARY\n")
        f.write("# ============================================\n")
        f.write(f"# Total words: {len(words_with_patterns)}\n")
        f.write(f"# Pattern 1: {len(pattern1_words)} words\n")
        f.write(f"# Pattern 2: {len(pattern2_words)} words\n")
        f.write(f"# Pattern 3: {len(pattern3_words)} words\n")


def write_script_batched(
    batch1_words: List[Tuple[List[str], int]],
    batch2_words: List[Tuple[List[str], int]],
    filename: str,
    coverage: int,
) -> None:
    """Write output grouped as two explicit recording batches."""

    def _write_pattern_group(fh, words_with_patterns: List[Tuple[List[str], int]], title: str):
        fh.write(f"# ===== {title} =====\n")

        pattern1_words = [(w, p) for w, p in words_with_patterns if p == 1]
        pattern2_words = [(w, p) for w, p in words_with_patterns if p == 2]
        pattern3_words = [(w, p) for w, p in words_with_patterns if p == 3]

        fh.write("# ========== PATTERN 1 (VCCVCCV) ==========\n")
        fh.write(f"# {len(pattern1_words)} words\n\n")
        for i, (word, _) in enumerate(pattern1_words, 1):
            if i % 20 == 1:
                fh.write(f"# Block {i//20 + 1}\n")
            fh.write(f"{format_word(word, 1)}\n")

        fh.write("\n# ========== PATTERN 2 (CVCVCCVC) ==========\n")
        fh.write(f"# {len(pattern2_words)} words\n\n")
        for i, (word, _) in enumerate(pattern2_words, 1):
            if i % 20 == 1:
                fh.write(f"# Block {i//20 + 1}\n")
            fh.write(f"{format_word(word, 2)}\n")

        fh.write("\n# ========== PATTERN 3 (CVVCVVC) ==========\n")
        fh.write(f"# {len(pattern3_words)} words\n\n")
        for i, (word, _) in enumerate(pattern3_words, 1):
            if i % 20 == 1:
                fh.write(f"# Block {i//20 + 1}\n")
            fh.write(f"{format_word(word, 3)}\n")

        fh.write("\n")

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# ============================================\n")
        f.write("# AKKADIAN DIPHONE RECORDING SCRIPT (TWO BATCHES)\n")
        f.write(f"# Target coverage: {coverage}\n")
        f.write("# ============================================\n\n")

        f.write("# Batch 1: plain consonants only, plain vowels only\n")
        f.write("# Batch 2: plain+emphatic consonants, mixed plain/colored vowels with post-emphatic legality, alternating plain/emphatic consonants\n\n")

        _write_pattern_group(f, batch1_words, "BATCH 1")
        _write_pattern_group(f, batch2_words, "BATCH 2")

        f.write("# ============================================\n")
        f.write("# SUMMARY\n")
        f.write("# ============================================\n")
        f.write(f"# Batch 1 words: {len(batch1_words)}\n")
        f.write(f"# Batch 2 words: {len(batch2_words)}\n")
        f.write(f"# Total words: {len(batch1_words) + len(batch2_words)}\n")


def validate_word_list(
    words_with_patterns: List[Tuple[List[str], int]],
    require_alternation: bool = False,
) -> List[str]:
    """Validate generated words against current inventory constraints."""
    issues: List[str] = []
    for idx, (word, pattern) in enumerate(words_with_patterns, 1):
        ok = (
            validate_pattern1(word)
            if pattern == 1
            else validate_pattern2(word)
            if pattern == 2
            else validate_pattern3(word)
        )
        if not ok:
            issues.append(f"#{idx} pattern={pattern} illegal context: {' '.join(word)}")
            continue

        if require_alternation and not is_plain_emphatic_alternating(word, pattern):
            issues.append(f"#{idx} pattern={pattern} non-alternating consonants: {' '.join(word)}")

        # Safety check: V-V diphones must not mix plain and colored classes.
        for dip in word_diphones(word, pattern):
            if not is_vv_diphone(dip):
                continue
            left, right = dip.split('-', 1)
            if not is_vv_class_legal(left, right):
                issues.append(
                    f"#{idx} pattern={pattern} mixed-class V-V illegal: {dip} in {' '.join(word)}"
                )
                break

    return issues


# ============================================
# MAIN
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Generate Akkadian diphone recording script")
    parser.add_argument("--coverage", "-c", type=int, default=3, 
                       choices=[1, 2, 3, 4],
                       help="Target coverage for each diphone (default: 3)")
    parser.add_argument("--max-non-vv", type=int, default=None,
                       choices=[1, 2, 3],
                       help="Target count for non-VV diphones (soft by default, strict only with --strict-max-non-vv)")
    parser.add_argument("--non-vv-target-ratio", type=float, default=0.8,
                       help="In soft mode, stop when this ratio of non-VV diphones reach target (default: 0.8)")
    parser.add_argument("--strict-max-non-vv", action="store_true",
                       help="Use strict hard cap for non-VV diphones (disables soft around-num behavior)")
    parser.add_argument("--two-batch-emphatic", action="store_true",
                       help="Generate two batches: plain-only, then alternating plain/emphatic with mixed vowels (post-emphatic legality)")
    parser.add_argument("--no-sidecars", action="store_true",
                       help="Do not write manifest/diphone cursor sidecar files")
    parser.add_argument("--output", "-o", type=str, default="akkadian_script.txt",
                       help="Output filename")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility")
    parser.add_argument("--max-iterations", type=int, default=200000,
                       help="Maximum sampled candidates in stochastic generator (default: 200000)")
    parser.add_argument("--candidate-pool-size", type=int, default=32,
                       help="Number of random candidates scored per selection round (default: 32)")
    parser.add_argument("--debug-reduced-set", action="store_true",
                       help="Use reduced inventory for debugging: C={m,q}, V={a,ā,ɑ,ɑ̄}")
    parser.add_argument("--plain-consonants", type=str, default="",
                       help="Override plain consonants (comma/space separated)")
    parser.add_argument("--emphatic-consonants", type=str, default="",
                       help="Override emphatic consonants (comma/space separated)")
    parser.add_argument("--plain-vowels-short", type=str, default="",
                       help="Override short plain vowels (comma/space separated)")
    parser.add_argument("--plain-vowels-long", type=str, default="",
                       help="Override long plain vowels (comma/space separated)")
    parser.add_argument("--colored-vowels-short", type=str, default="",
                       help="Override short colored vowels (comma/space separated)")
    parser.add_argument("--colored-vowels-long", type=str, default="",
                       help="Override long colored vowels (comma/space separated)")
    
    args = parser.parse_args()

    if not 0.0 < args.non_vv_target_ratio <= 1.0:
        parser.error("--non-vv-target-ratio must be in (0, 1]")
    if args.candidate_pool_size <= 0:
        parser.error("--candidate-pool-size must be >= 1")

    if args.debug_reduced_set:
        set_active_inventory(
            plain_consonants=['m'],
            emphatic_consonants=['q'],
            plain_vowels_short=['a'],
            plain_vowels_long=['ā'],
            colored_vowels_short=['ɑ'],
            colored_vowels_long=['ɑ̄'],
        )

    if args.plain_consonants:
        PLAIN = parse_symbol_list(args.plain_consonants)
    else:
        PLAIN = PLAIN_CONSONANTS
    if args.emphatic_consonants:
        EMPH = parse_symbol_list(args.emphatic_consonants)
    else:
        EMPH = EMPHATIC_CONSONANTS
    if args.plain_vowels_short:
        PVS = parse_symbol_list(args.plain_vowels_short)
    else:
        PVS = PLAIN_VOWELS_SHORT
    if args.plain_vowels_long:
        PVL = parse_symbol_list(args.plain_vowels_long)
    else:
        PVL = PLAIN_VOWELS_LONG
    if args.colored_vowels_short:
        CVS = parse_symbol_list(args.colored_vowels_short)
    else:
        CVS = COLORED_VOWELS_SHORT
    if args.colored_vowels_long:
        CVL = parse_symbol_list(args.colored_vowels_long)
    else:
        CVL = COLORED_VOWELS_LONG

    set_active_inventory(
        plain_consonants=PLAIN,
        emphatic_consonants=EMPH,
        plain_vowels_short=PVS,
        plain_vowels_long=PVL,
        colored_vowels_short=CVS,
        colored_vowels_long=CVL,
    )
    
    random.seed(args.seed)
    
    print(f"Akkadian Diphone Script Generator")
    print(f"=================================")
    print(f"Target coverage: {args.coverage}")
    if args.max_non_vv is not None:
        if args.strict_max_non_vv:
            print(f"Non-VV strict max occurrences: {args.max_non_vv} (V-V unlimited)")
        else:
            print(
                f"Non-VV soft target: {args.max_non_vv}, "
                f"required ratio: {args.non_vv_target_ratio:.0%} (V-V unlimited)"
            )
    print(f"Output file: {args.output}")
    print(f"Plain consonants (IPA): {', '.join(inventory_as_ipa(PLAIN_CONSONANTS))}")
    print(f"Emphatic consonants (IPA): {', '.join(inventory_as_ipa(EMPHATIC_CONSONANTS))}")
    print(
        "Plain vowels short/long (IPA): "
        f"{', '.join(inventory_as_ipa(PLAIN_VOWELS_SHORT))} / "
        f"{', '.join(inventory_as_ipa(PLAIN_VOWELS_LONG))}"
    )
    print(
        "Colored vowels short/long (IPA): "
        f"{', '.join(inventory_as_ipa(COLORED_VOWELS_SHORT))} / "
        f"{', '.join(inventory_as_ipa(COLORED_VOWELS_LONG))}"
    )
    mapping_pairs = ipa_to_mbrola_mapping_list()
    mapping_text = ', '.join([f"{ipa}->{mb}" for ipa, mb in mapping_pairs])
    print(f"Mbrola X-SAMPA mapping: [{mapping_text}]")
    print()

    if args.two_batch_emphatic:
        base_plain_consonants = list(PLAIN_CONSONANTS)
        base_emphatic_consonants = list(EMPHATIC_CONSONANTS)
        base_plain_vowels_short = list(PLAIN_VOWELS_SHORT)
        base_plain_vowels_long = list(PLAIN_VOWELS_LONG)
        base_colored_vowels_short = list(COLORED_VOWELS_SHORT)
        base_colored_vowels_long = list(COLORED_VOWELS_LONG)

        print("Running two-batch mode...")

        # Batch 1: no emphatics, no colored vowels.
        set_active_inventory(
            plain_consonants=base_plain_consonants,
            emphatic_consonants=[],
            plain_vowels_short=base_plain_vowels_short,
            plain_vowels_long=base_plain_vowels_long,
            colored_vowels_short=[],
            colored_vowels_long=[],
        )
        print("\n[BATCH 1] Plain-only inventory")
        batch1_words, batch1_stats = generate_script(
            target_coverage=args.coverage,
            max_non_vv_occurrences=args.max_non_vv,
            non_vv_target_ratio=args.non_vv_target_ratio,
            strict_non_vv_cap=args.strict_max_non_vv,
            max_iterations=args.max_iterations,
            candidate_pool_size=args.candidate_pool_size,
        )
        batch1_issues = validate_word_list(batch1_words, require_alternation=False)
        if batch1_issues:
            print(f"WARNING: Batch 1 validation found {len(batch1_issues)} issue(s). First:")
            print(f"  {batch1_issues[0]}")

        # Batch 2: mixed plain/colored vowels + mixed consonants (no alternation filter).
        set_active_inventory(
            plain_consonants=base_plain_consonants,
            emphatic_consonants=base_emphatic_consonants,
            plain_vowels_short=base_plain_vowels_short,
            plain_vowels_long=base_plain_vowels_long,
            colored_vowels_short=base_colored_vowels_short,
            colored_vowels_long=base_colored_vowels_long,
        )
        print("\n[BATCH 2] Mixed consonants + mixed vowels (post-emphatic legality)")
        batch2_words, batch2_stats = generate_script(
            target_coverage=args.coverage,
            max_non_vv_occurrences=args.max_non_vv,
            non_vv_target_ratio=args.non_vv_target_ratio,
            strict_non_vv_cap=args.strict_max_non_vv,
            candidate_filter=None,
            max_iterations=args.max_iterations,
            candidate_pool_size=args.candidate_pool_size,
        )
        batch2_issues = validate_word_list(batch2_words, require_alternation=False)
        if batch2_issues:
            print(f"WARNING: Batch 2 validation found {len(batch2_issues)} issue(s). First:")
            print(f"  {batch2_issues[0]}")

        # Restore active inventory for any later operations.
        set_active_inventory(
            plain_consonants=base_plain_consonants,
            emphatic_consonants=base_emphatic_consonants,
            plain_vowels_short=base_plain_vowels_short,
            plain_vowels_long=base_plain_vowels_long,
            colored_vowels_short=base_colored_vowels_short,
            colored_vowels_long=base_colored_vowels_long,
        )

        print("\n" + "="*50)
        print("BATCHED COVERAGE SUMMARY")
        print("="*50)
        print(f"Batch 1 words: {len(batch1_words)} | target-hit ratio: {batch1_stats['ratio']:.2%}")
        print(f"Batch 2 words: {len(batch2_words)} | target-hit ratio: {batch2_stats['ratio']:.2%}")
        print(f"Total words: {len(batch1_words) + len(batch2_words)}")

        write_script_batched(batch1_words, batch2_words, args.output, args.coverage)
        print(f"\nScript written to {args.output}")

        if not args.no_sidecars:
            batch1_rows = build_manifest_rows(batch1_words, batch='batch1', start_utterance_id=1)
            batch2_rows = build_manifest_rows(
                batch2_words,
                batch='batch2',
                start_utterance_id=len(batch1_rows) + 1,
            )
            write_alignment_sidecars(args.output, batch1_rows + batch2_rows)
        return
    
    words, stats = generate_script(
        target_coverage=args.coverage,
        max_non_vv_occurrences=args.max_non_vv,
        non_vv_target_ratio=args.non_vv_target_ratio,
        strict_non_vv_cap=args.strict_max_non_vv,
        max_iterations=args.max_iterations,
        candidate_pool_size=args.candidate_pool_size,
    )
    issues = validate_word_list(words, require_alternation=False)
    if issues:
        print(f"WARNING: Validation found {len(issues)} issue(s). First:")
        print(f"  {issues[0]}")
    
    print("\n" + "="*50)
    print("COVERAGE SUMMARY")
    print("="*50)
    print(f"Required diphones: {stats['total']}")
    print(f"Fully covered: {stats['complete']}")
    print(f"Below target: {stats['below']}")
    print(f"Coverage range: {stats['min']} - {stats['max']}")
    print(f"Average coverage: {stats['avg']:.2f}")
    print(f"Target-hit ratio: {stats['ratio']:.2%}")
    print(f"V-V diphones tracked: {stats['vv_total']} (avg coverage {stats['vv_avg']:.2f})")
    print(f"Words generated: {len(words)}")
    
    write_script(words, args.output, args.coverage)
    print(f"\nScript written to {args.output}")

    if not args.no_sidecars:
        rows = build_manifest_rows(words, batch='single', start_utterance_id=1)
        write_alignment_sidecars(args.output, rows)


if __name__ == "__main__":
    main()