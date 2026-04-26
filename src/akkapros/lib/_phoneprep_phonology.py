"""
Phonological rules, segment transformation, diphone extraction, and word generation
for the Akkadian Diphone Recording Script Generator.

Extracted from phoneprep.py during CR-092 split. All functions here are
phonology-only — no file I/O, no script generation, no recording helpers.
"""

import random
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Set, Tuple


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
PHONEPREP_COLORED_PREDECESSOR_EXCLUSIONS = {'t', 'd', 'k'}
DEFAULT_MAX_WORDS_PER_RECORDING = 1000

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

    Colored vowels remain legal after emphatic onsets and additionally become
    legal before emphatic codas when the predecessor is not in the dedicated
    phoneprep recording-exclusion set.
    """
    left_is_consonant = left is not None and (is_consonant_plain(left) or is_consonant_emphatic(left))
    right_is_consonant = right is not None and (is_consonant_plain(right) or is_consonant_emphatic(right))

    colored_licensed = False
    if left_is_consonant and is_consonant_emphatic(left):
        colored_licensed = True
    elif left_is_consonant and right_is_consonant and is_consonant_emphatic(right):
        colored_licensed = left not in PHONEPREP_COLORED_PREDECESSOR_EXCLUSIONS

    # Word-initial (left is boundary): no preceding emphatic exists, so only plain vowels are legal.
    if left == BOUNDARY:
        return is_vowel_plain(v) and right_is_consonant

    # Word-final (right is boundary): quality depends on left consonant only.
    if right == BOUNDARY:
        if not left_is_consonant:
            return False
        if colored_licensed:
            return is_vowel_colored(v)
        return is_vowel_plain(v)

    # Word-medial (both sides consonants): quality depends on onset licensing
    # plus the extended coda-conditioned recording coverage rule.
    if not (left_is_consonant and right_is_consonant):
        return False

    if colored_licensed:
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


def vowel_pool_for_context(left: str, right: str) -> List[str]:
    """Return the legal vowel class for a concrete consonantal frame."""
    if left == BOUNDARY:
        return ALL_PLAIN_VOWELS
    if is_consonant_emphatic(left):
        return ALL_COLORED_VOWELS
    if is_consonant_emphatic(right) and left not in PHONEPREP_COLORED_PREDECESSOR_EXCLUSIONS:
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
        for v in vowel_pool_for_context(c, BOUNDARY):
            diphones.add(f"{v}-{BOUNDARY}")

    # C-C is unconstrained by vowel legality in patterns 1/2
    for c1 in ALL_CONSONANTS:
        for c2 in ALL_CONSONANTS:
            diphones.add(f"{c1}-{c2}")

    # V-C and C-V with onset and coda-conditioned emphatic licensing
    for c_left in ALL_CONSONANTS:
        for c_right in ALL_CONSONANTS:
            for v in vowel_pool_for_context(c_left, c_right):
                diphones.add(f"{c_left}-{v}")  # C-V
                diphones.add(f"{v}-{c_right}")  # V-C

    # Initial V-C from pattern 1 starts plain only
    for v in ALL_PLAIN_VOWELS:
        for c in ALL_CONSONANTS:
            diphones.add(f"{v}-{c}")

    # V-V from pattern 3: same class only
    for c_left in ALL_CONSONANTS:
        for c_right in ALL_CONSONANTS:
            pool = vowel_pool_for_context(c_left, c_right)
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
        V2 = random.choice(vowel_pool_for_context(C3, C4))
        V3 = random.choice(vowel_pool_for_context(C5, BOUNDARY))
        return [V1, C2, C3, V2, C4, C5, V3]

    if pattern == 2:
        C1 = random.choice(ALL_CONSONANTS)
        C3 = random.choice(ALL_CONSONANTS)
        C5 = random.choice(ALL_CONSONANTS)
        C6 = random.choice(ALL_CONSONANTS)
        C8 = random.choice(ALL_CONSONANTS)
        V2 = random.choice(vowel_pool_for_context(C1, C3))
        V4 = random.choice(vowel_pool_for_context(C3, C5))
        V7 = random.choice(vowel_pool_for_context(C6, C8))
        return [C1, V2, C3, V4, C5, C6, V7, C8]

    C1 = random.choice(ALL_CONSONANTS)
    C4 = random.choice(ALL_CONSONANTS)
    C7 = random.choice(ALL_CONSONANTS)
    pool1 = vowel_pool_for_context(C1, C4)
    pool2 = vowel_pool_for_context(C4, C7)
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
