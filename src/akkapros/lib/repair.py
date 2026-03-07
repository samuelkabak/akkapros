#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Moraic Repair System
Version: 1.0.0 - WITH HYPHEN SUPPORT
"""

import re
from enum import Enum
from typing import List, Optional, Tuple, Union, Dict, Set

__version__ = "1.0.0"


# shared constants
from akkapros.lib.constants import (
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    GLOTTAL,
    SYL_WORD_ENDING,
    SYL_SEPARATOR,
    OPEN_ESCAPE,
    CLOSE_ESCAPE,
    WORD_LINKER
)

HYPHEN = '-'

# ------------------------------------------------------------
# Phonetic inventory
# ------------------------------------------------------------
LONG = set('āēīūâêîû')
SHORT = set('aeiu')
V = LONG | SHORT
C = set('bdgkpṭqṣszšlmnrḥḫʿʾwyt')
CIRCUMFLEX = set('âêîû')



# ------------------------------------------------------------
# Function words
# ------------------------------------------------------------
FUNCTION_WORDS: Set[str] = {
    'ana', 'ina', 'ištu', 'itti', 'eli',
    'ul', 'ula', 'lā',
    'ša',
    'u', 'ū', 'lū',
    'anāku', 'nīnu', 'atta', 'atti', 'attunu', 'attina',
    'šū', 'šī', 'šunu', 'šina'
}


def is_function_word(word_text: str) -> bool:
    """Return True if word is a function word (ignoring dots and hyphens)."""
    return word_text.replace(SYL_SEPARATOR, '').replace(HYPHEN, '') in FUNCTION_WORDS


class AccentStyle(Enum):
    LOB = "lob"
    SOB = "sob"


class SyllableType(Enum):
    CV = 1
    V = 1
    CVC = 2
    VC = 2
    CVV = 2
    VV = 2
    CVVC = 3
    VVC = 3


class Syllable:
    def __init__(self, text: str, word_idx: int, position_in_word: int):
        self.text = text
        self.original_text = text
        self.word_idx = word_idx
        self.position_in_word = position_in_word
        self.is_repaired = False
        self.repair_type = None
        
        self.type, self.morae = self._classify(text)
        self.repaired_morae = self.morae
        self.repaired_text = text
        self.has_circumflex = any(c in CIRCUMFLEX for c in text)
    
    def _classify(self, text: str) -> Tuple[str, int]:
        vowels = [c for c in text if c in V]
        consonants = [c for c in text if c in C]
        
        has_long = any(c in LONG for c in vowels)
        has_coda = len(consonants) > 0 and text[-1] in C
        
        if text[0] in V:
            if has_coda:
                return ('VVC' if has_long else 'VC', 3 if has_long else 2)
            else:
                return ('VV' if has_long else 'V', 2 if has_long else 1)
        else:
            if has_coda:
                return ('CVVC' if has_long else 'CVC', 3 if has_long else 2)
            else:
                return ('CVV' if has_long else 'CV', 2 if has_long else 1)
    
    def can_lengthen_vowel(self) -> bool:
        return self.type in ('CVV', 'VV', 'CVVC', 'VVC')
    
    def can_geminate_coda(self) -> bool:
        return self.type in ('CVC', 'VC') and self.text[-1] in C
    
    def can_geminate_onset(self) -> bool:
        return True
    
    def is_final_in_word(self, total_syllables_in_word: int) -> bool:
        return self.position_in_word == total_syllables_in_word - 1
    
    def lengthen_vowel(self) -> bool:
        if not self.can_lengthen_vowel():
            return False
        for i, c in enumerate(self.text):
            if c in LONG:
                self.repaired_text = self.text[:i+1] + '~' + self.text[i+1:]
                self.repaired_morae = self.morae + 1
                self.is_repaired = True
                self.repair_type = 'lengthen_vowel'
                return True
        return False
    
    def geminate_coda(self) -> bool:
        if not self.can_geminate_coda():
            return False
        self.repaired_text = self.text + '~'
        self.repaired_morae = self.morae + 1
        self.is_repaired = True
        self.repair_type = 'geminate_coda'
        return True
    
    def geminate_onset(self) -> bool:
        if self.text[0] in C:
            self.repaired_text = self.text[0] + '~' + self.text[1:]
            self.repaired_morae = self.morae + 1
            self.is_repaired = True
            self.repair_type = 'geminate_onset'
            return True
        elif self.text[0] in V:
            self.repaired_text = '~' + self.text
            self.repaired_morae = self.morae + 1
            self.is_repaired = True
            self.repair_type = 'geminate_glottal'
            return True
        return False
    
    def last_resort_repair(self) -> bool:
        return self.geminate_onset()
    
    def __repr__(self):
        status = "~" if self.is_repaired else ""
        return f"{self.text}{status}({self.morae}→{self.repaired_morae})"


class Word:
    def __init__(self, text: str, word_idx: int):
        self.original_text = text
        self.word_idx = word_idx
        self.is_function_word = is_function_word(text)
        self.syllables = []
        self.separators = []  # Store separators between syllables
        
        # Parse syllables and track separators
        current = []
        for c in text:
            if c in (SYL_SEPARATOR, HYPHEN):
                if current:
                    self.syllables.append(''.join(current))
                    self.separators.append(c)
                    current = []
            else:
                current.append(c)
        if current:
            self.syllables.append(''.join(current))
        
        # Create Syllable objects
        for pos, syl_text in enumerate(self.syllables):
            self.syllables[pos] = Syllable(syl_text, word_idx, pos)
    
    @property
    def morae(self) -> int:
        return sum(s.morae for s in self.syllables)
    
    @property
    def repaired_morae(self) -> int:
        return sum(s.repaired_morae for s in self.syllables)
    
    @property
    def needs_repair(self) -> bool:
        return self.repaired_morae % 2 == 1
    
    def has_heavy_syllable(self) -> bool:
        """Check if word has any heavy syllable (CVC, CVV, etc.)"""
        return any(s.morae >= 2 for s in self.syllables)
    
    def get_repair_candidates(self, style: AccentStyle) -> List[Dict]:
        if self.is_function_word:
            return []
        
        candidates = []
        n_syllables = len(self.syllables)
        
        # Priority 1: Final superheavy (LOB only)
        if style == AccentStyle.LOB:
            final = self.syllables[-1]
            is_superheavy = (
                final.type in ('CVVC', 'VVC') or 
                (final.has_circumflex and final.type in ('CVV', 'VV'))
            )
            if is_superheavy and final.is_final_in_word(n_syllables):
                candidates.append({
                    'position': n_syllables - 1,
                    'type': 'lengthen_vowel',
                    'rule': f'{style.value.upper()}_final_superheavy',
                    'priority': 1
                })
        
        # Priority 2: Rightmost non-final heavy
        for i in range(n_syllables - 2, -1, -1):
            syl = self.syllables[i]
            if syl.can_lengthen_vowel():
                candidates.append({
                    'position': i,
                    'type': 'lengthen_vowel',
                    'rule': 'heavy_nonfinal',
                    'priority': 2
                })
            elif syl.can_geminate_coda():
                candidates.append({
                    'position': i,
                    'type': 'geminate_coda',
                    'rule': 'heavy_nonfinal',
                    'priority': 2
                })
        
        # Priority 3: Varies by model
        final = self.syllables[-1]
        
        if style == AccentStyle.LOB:
            if final.can_lengthen_vowel():
                candidates.append({
                    'position': n_syllables - 1,
                    'type': 'lengthen_vowel',
                    'rule': 'LOB_final_heavy',
                    'priority': 3
                })
        
        elif style == AccentStyle.SOB:
            if final.can_lengthen_vowel():
                candidates.append({
                    'position': n_syllables - 1,
                    'type': 'lengthen_vowel',
                    'rule': 'SOB_final_heavy',
                    'priority': 3
                })
                
        candidates.sort(key=lambda x: x['priority'])
        return candidates
    
    def get_best_repair(self, style: AccentStyle) -> Optional[Dict]:
        candidates = self.get_repair_candidates(style)
        return candidates[0] if candidates else None
    
    def apply_repair(self, repair: Dict) -> bool:
        if not repair:
            return False
        position = repair['position']
        syl = self.syllables[position]
        repair_type = repair['type']
        
        if repair_type == 'lengthen_vowel':
            return syl.lengthen_vowel()
        elif repair_type == 'geminate_coda':
            return syl.geminate_coda()
        elif repair_type == 'geminate_onset':
            return syl.geminate_onset()
        return False
    
    def get_text(self) -> str:
        """Get the word text with repairs and original separators."""
        result = []
        for i, syl in enumerate(self.syllables):
            result.append(syl.repaired_text)
            if i < len(self.separators):
                result.append(self.separators[i])
        return ''.join(result)
    
    def get_text_flat(self) -> str:
        """Get text without dots or hyphens (for function words)."""
        return ''.join(s.repaired_text for s in self.syllables)
    
    def __repr__(self):
        status = " (FUNC)" if self.is_function_word else ""
        return f"Word({self.original_text}{status})"


class MergedUnit:
    def __init__(self, words: List[Word], locked_prefix_words: int = 0):
        self.words = words
        self.syllables = []
        for w in words:
            self.syllables.extend(w.syllables)
        
        self.word_boundaries = []
        pos = 0
        for w in words:
            self.word_boundaries.append(pos + len(w.syllables) - 1)
            pos += len(w.syllables)

        # Optional explicit-link locking: words before the explicit-link tail
        # are ineligible for repair candidates.
        locked_prefix_words = max(0, min(locked_prefix_words, len(words)))
        ineligible_count = sum(len(w.syllables) for w in words[:locked_prefix_words])
        self.pre_linker_syllables = set(range(ineligible_count))
    
    @property
    def morae(self) -> int:
        return sum(s.repaired_morae for s in self.syllables)
    
    @property
    def needs_repair(self) -> bool:
        return self.morae % 2 == 1
    
    def is_syllable_final_in_word(self, syl_idx: int) -> bool:
        return syl_idx in self.word_boundaries

    def is_syllable_before_linker(self, syl_idx: int) -> bool:
        return syl_idx in self.pre_linker_syllables
    
    def get_best_repair(self, style: AccentStyle) -> Optional[Dict]:
        candidates = []
        n_syllables = len(self.syllables)
        
        if style == AccentStyle.LOB:
            final = self.syllables[-1]
            is_superheavy = (
                final.type in ('CVVC', 'VVC') or 
                (final.has_circumflex and final.type in ('CVV', 'VV'))
            )
            if is_superheavy:
                candidates.append({
                    'position': n_syllables - 1,
                    'type': 'lengthen_vowel',
                    'word_idx': final.word_idx,
                    'rule': f'{style.value.upper()}_final_superheavy',
                    'priority': 1
                })
        
        for i in range(n_syllables - 1, -1, -1):
            syl = self.syllables[i]
            if self.is_syllable_before_linker(i):
                continue
            is_final_in_word = self.is_syllable_final_in_word(i)
            
            if syl.can_lengthen_vowel():
                rule = 'heavy_nonfinal' if not is_final_in_word else 'final_heavy'
                priority = 2 if not is_final_in_word else 3
                candidates.append({
                    'position': i,
                    'type': 'lengthen_vowel',
                    'word_idx': syl.word_idx,
                    'rule': rule,
                    'priority': priority
                })
            elif syl.can_geminate_coda() and not is_final_in_word:
                candidates.append({
                    'position': i,
                    'type': 'geminate_coda',
                    'word_idx': syl.word_idx,
                    'rule': 'heavy_nonfinal',
                    'priority': 2
                })
        
        candidates.sort(key=lambda x: x['priority'])
        return candidates[0] if candidates else None
    
    def apply_repair(self, repair: Dict) -> bool:
        if not repair:
            return False
        position = repair['position']
        syl = self.syllables[position]
        repair_type = repair['type']
        
        if repair_type == 'lengthen_vowel':
            return syl.lengthen_vowel()
        elif repair_type == 'geminate_coda':
            return syl.geminate_coda()
        elif repair_type == 'geminate_onset':
            return syl.geminate_onset()
        return False


def parse_syl_line(line: str) -> List[Union[Word, str]]:
    if not line.strip():
        return []
    
    tokens = []
    i = 0
    n = len(line)
    word_count = 0
    
    while i < n:
        if line[i] == OPEN_ESCAPE:
            j = line.find(CLOSE_ESCAPE, i)
            if j == -1:
                j = n
            tokens.append(line[i:j+1])
            i = j + 1
        elif line[i].isspace():
            i += 1
        elif line[i] == WORD_LINKER:
            tokens.append(WORD_LINKER)
            i += 1
        elif line[i] == SYL_WORD_ENDING:
            i += 1
        else:
            start = i
            while i < n and line[i] != SYL_WORD_ENDING and line[i] != OPEN_ESCAPE and line[i] != WORD_LINKER:
                i += 1
            if start < i:
                word_text = line[start:i]
                if word_text:
                    tokens.append(Word(word_text, word_count))
                    word_count += 1
    
    return tokens

def assemble_line(parts: List[str], tokens: List[Union[Word, str]]) -> str:
    """
    Assemble the final line with proper underscore attachment.
    Underscores attach to the preceding word only.
    """
    if not parts:
        return ""
    
    # First pass: attach underscores to preceding words
    combined = []
    i = 0
    while i < len(parts):
        if parts[i] == WORD_LINKER:
            # Underscore attaches to previous word
            if combined:
                combined[-1] = combined[-1] + WORD_LINKER
            i += 1
        else:
            # Check if this part should be merged with previous (for multiple underscores)
            if combined and combined[-1].endswith(WORD_LINKER):
                # Previous word ended with underscore, attach this word directly
                combined[-1] = combined[-1] + parts[i]
            else:
                combined.append(parts[i])
            i += 1
    
    # Build Akkadian character set for word detection
    akkadian_chars = set()
    for token in tokens:
        if isinstance(token, Word):
            for syllable in token.syllables:
                for c in syllable.text:
                    if c not in (SYL_SEPARATOR, HYPHEN):  # Ignore separators
                        akkadian_chars.add(c)
    akkadian_chars.add('~')
    
    def is_word(text: str) -> bool:
        """Return True if text contains Akkadian letters."""
        return any(c in akkadian_chars for c in text)
    
    # Insert spaces only between two words
    result = []
    i = 0
    while i < len(combined):
        result.append(combined[i])
        if i < len(combined) - 1 and is_word(combined[i]) and is_word(combined[i + 1]):
            result.append(' ')
        i += 1
    
    return ''.join(result)



# ------------------------------------------------------------
# Diphthong Restoration (when --restore-diphthongs is used)
# ------------------------------------------------------------

# Vowel mappings
SHORT_VOWELS = {'a', 'i', 'u', 'e'}
MACRON_VOWELS = {'ā', 'ī', 'ū', 'ē'}
CIRCUMFLEX_VOWELS = {'â', 'î', 'û', 'ê'}

# Mapping from base vowel to long forms
MACRON_MAP = {'a': 'ā', 'i': 'ī', 'u': 'ū', 'e': 'ē'}
CIRCUMFLEX_MAP = {'a': 'â', 'i': 'î', 'u': 'û', 'e': 'ê'}

# For extra-long (with ~)
EXTRA_LONG_MACRON_MAP = {'a': 'ā~', 'i': 'ī~', 'u': 'ū~', 'e': 'ē~'}
EXTRA_LONG_CIRCUMFLEX_MAP = {'a': 'â~', 'i': 'î~', 'u': 'û~', 'e': 'ê~'}

import re

def postprocess_restore_diphthongs(output_lines: List[str]) -> List[str]:
    """
    Restore diphthongs using regex replacements.
    """
    print("\n⚠️  RESTORING DIPHTHONGS")
    
    # Replacement patterns based on your table
    replacements = [
        # Basic patterns
        (r'u\.ʾa', 'ua'),
        (r'u\.ʾā', 'uā'),
        (r'u\.ʾâ', 'uâ'),
        (r'u\.ʾā~', 'uā~'),
        (r'u\.ʾâ~', 'uâ~'),
        
        # First vowel long
        (r'ū\.ʾa', 'uā'),
        (r'û\.ʾa', 'uâ'),
        (r'ū\.ʾā', 'uā~'),
        (r'û\.ʾā', 'uâ~'),
        (r'ū\.ʾâ', 'uâ~'),
        (r'û\.ʾâ', 'uâ~'),
        (r'ū\.ʾā~', 'uā'),
        (r'û\.ʾā~', 'uâ'),
        (r'ū\.ʾâ~', 'uâ'),
        (r'û\.ʾâ~', 'uâ'),
        
        # First vowel extra-long
        (r'ū~\.ʾa', 'uā~'),
        (r'û~\.ʾa', 'uâ~'),
        (r'ū~\.ʾā', 'uā'),
        (r'û~\.ʾā', 'uâ'),
        (r'ū~\.ʾâ', 'uâ'),
        (r'û~\.ʾâ', 'uâ'),
        (r'ū~\.ʾā~', 'uā~'),
        (r'û~\.ʾā~', 'uâ~'),
        (r'ū~\.ʾâ~', 'uâ~'),
        (r'û~\.ʾâ~', 'uâ~'),
        
        # With consonant
        (r'([^aeiu]?)u\.ʾa', r'\1ua'),
        (r'([^aeiu]?)u\.ʾā', r'\1uā'),
        (r'([^aeiu]?)u\.ʾâ', r'\1uâ'),
    ]
    
    new_lines = []
    for line in output_lines:
        for pattern, repl in replacements:
            line = re.sub(pattern, repl, line)
        new_lines.append(line)
    
    return new_lines

#------------------------

class RepairEngine:
    def __init__(self, style: AccentStyle = AccentStyle.SOB, only_last: bool = True):
        self.style = style
        self.only_last = only_last
        self.stats = {
            'words': 0,
            'function_words': 0,
            'words_repaired': 0,
            'merged_forward': 0,
            'merged_backward': 0,
            'last_resort': 0,
            'total_syllables': 0,
            'repaired_syllables': 0,
            'repair_types': {
                'lengthen_vowel': 0,
                'geminate_coda': 0,
                'geminate_onset': 0,
                'geminate_glottal': 0
            }
        }
    
    def _update_last_resort_stats(self, syllable: Syllable):
        self.stats['last_resort'] += 1
        self.stats['repaired_syllables'] += 1
        if syllable.text[0] in C:
            self.stats['repair_types']['geminate_onset'] += 1
        else:
            self.stats['repair_types']['geminate_glottal'] += 1
    
    def rollback_repair(self, word: Word) -> None:
        """Remove all repairs from a word."""
        for syllable in word.syllables:
            syllable.is_repaired = False
            syllable.repair_type = None
            syllable.repaired_morae = syllable.morae
            syllable.repaired_text = syllable.text

    def rollback_repair_stats(self, word: Word) -> None:
        """Revert repair counters for repairs that are being rolled back."""
        repaired_in_word = 0
        for syllable in word.syllables:
            if syllable.is_repaired:
                repaired_in_word += 1
                self.stats['repaired_syllables'] = max(0, self.stats['repaired_syllables'] - 1)
                repair_type = syllable.repair_type
                if repair_type and repair_type in self.stats['repair_types']:
                    self.stats['repair_types'][repair_type] = max(
                        0, self.stats['repair_types'][repair_type] - 1
                    )

        if repaired_in_word > 0:
            self.stats['words_repaired'] = max(0, self.stats['words_repaired'] - 1)

    def _get_explicit_group_repair(self, unit: MergedUnit) -> Optional[Dict]:
        """Pick repair site for explicit '+' groups.

        - only_last=True: use standard model priorities, with pre-linker lock.
        - only_last=False: allow propagation and choose the rightmost legal site.
        """
        if self.only_last:
            return unit.get_best_repair(self.style)

        n_syllables = len(unit.syllables)
        for i in range(n_syllables - 1, -1, -1):
            syl = unit.syllables[i]
            if unit.is_syllable_before_linker(i):
                continue
            is_final_in_word = unit.is_syllable_final_in_word(i)

            if syl.can_lengthen_vowel():
                rule = 'heavy_nonfinal' if not is_final_in_word else 'final_heavy'
                priority = 2 if not is_final_in_word else 3
                return {
                    'position': i,
                    'type': 'lengthen_vowel',
                    'word_idx': syl.word_idx,
                    'rule': rule,
                    'priority': priority,
                }
            if syl.can_geminate_coda() and not is_final_in_word:
                return {
                    'position': i,
                    'type': 'geminate_coda',
                    'word_idx': syl.word_idx,
                    'rule': 'heavy_nonfinal',
                    'priority': 2,
                }

        return None
    
    def repair_line(self, tokens: List[Union[Word, str]]) -> str:
        if not tokens:
            return ""
        
        result_parts = []
        i = 0
        n = len(tokens)
        
        while i < n:
            token = tokens[i]
            
            # Handle explicit word linker from input
            if token == WORD_LINKER:
                i += 1
                continue

            # Handle bracketed text
            if isinstance(token, str):
                result_parts.append(token[1:-1])
                i += 1
                continue
            
            word = token

            # Handle user-provided explicit '+' links as mandatory prosodic units.
            forced_group = [word]
            j = i
            while (
                j + 2 < n
                and tokens[j + 1] == WORD_LINKER
                and not isinstance(tokens[j + 2], str)
            ):
                forced_group.append(tokens[j + 2])
                j += 2

            if len(forced_group) > 1:
                explicit_tail_start = (len(forced_group) - 1) if self.only_last else 0

                def append_group(words_group: List[Word]) -> None:
                    for k, linked_word in enumerate(words_group):
                        if linked_word.is_function_word:
                            result_parts.append(linked_word.get_text_flat())
                        else:
                            result_parts.append(linked_word.get_text())
                        if k < len(words_group) - 1:
                            result_parts.append(WORD_LINKER)

                def resolve_group(words_group: List[Word]) -> Tuple[bool, bool]:
                    unit = MergedUnit(words_group, locked_prefix_words=explicit_tail_start)
                    if not unit.needs_repair:
                        return True, False
                    repair = self._get_explicit_group_repair(unit)
                    if repair:
                        unit.apply_repair(repair)
                        self.stats['words_repaired'] += 1
                        self.stats['repaired_syllables'] += 1
                        self.stats['repair_types'][repair['type']] += 1
                        return True, True
                    return False, False

                for linked_word in forced_group:
                    self.stats['words'] += 1
                    self.stats['total_syllables'] += len(linked_word.syllables)
                    if linked_word.is_function_word:
                        self.stats['function_words'] += 1

                merged_group = list(forced_group)
                resolved, _ = resolve_group(merged_group)
                if resolved:
                    append_group(merged_group)
                    i = j + 1
                    continue

                # If explicit group cannot be repaired, keep merging forward
                # with following words until punctuation or successful resolution.
                k = j + 1
                merged_forward_used = False
                while k < n and not isinstance(tokens[k], str):
                    next_word = tokens[k]
                    merged_group.append(next_word)
                    self.stats['words'] += 1
                    self.stats['total_syllables'] += len(next_word.syllables)
                    if next_word.is_function_word:
                        self.stats['function_words'] += 1

                    merged_forward_used = True
                    resolved, _ = resolve_group(merged_group)
                    if resolved:
                        append_group(merged_group)
                        if merged_forward_used:
                            self.stats['merged_forward'] += 1
                        i = k + 1
                        break
                    k += 1
                else:
                    # Still unresolved at punctuation/end: last resort on the
                    # first syllable of the last word in the merged explicit group.
                    last_word = merged_group[-1]
                    if last_word.syllables and last_word.syllables[0].last_resort_repair():
                        self._update_last_resort_stats(last_word.syllables[0])
                    append_group(merged_group)
                    if merged_forward_used:
                        self.stats['merged_forward'] += 1
                    i = k
                continue

            self.stats['words'] += 1
            self.stats['total_syllables'] += len(word.syllables)
            
            if word.is_function_word:
                self.stats['function_words'] += 1
                
                # Collect all consecutive function words
                func_group = [word]
                j = i + 1
                while j < n and not isinstance(tokens[j], str) and tokens[j].is_function_word:
                    func_group.append(tokens[j])
                    j += 1
                
                # Check if next token is a content word
                has_content = j < n and not isinstance(tokens[j], str) and not tokens[j].is_function_word
                
                if has_content:
                    # Include the content word in the group
                    content_word = tokens[j]
                    func_group.append(content_word)
                    j += 1
                    
                    # Add all words with underscores
                    for k, w in enumerate(func_group):
                        if w.is_function_word:
                            result_parts.append(w.get_text_flat())
                        else:
                            result_parts.append(w.get_text())
                        if k < len(func_group) - 1:
                            result_parts.append(WORD_LINKER)
                    
                    i = j
                    continue
                
                # No content word following - check if we're at end or punctuation
                at_end_or_punct = j >= n or isinstance(tokens[j], str)
                
                if at_end_or_punct and i > 0:
                    # Need to merge backward with previous content word
                    # Find the last content word in result_parts
                    for idx in range(len(result_parts) - 1, -1, -1):
                        part = result_parts[idx]
                        if isinstance(part, str) and not part.endswith(WORD_LINKER) and not part.startswith(WORD_LINKER):
                            # Found a content word - need to rollback if it was repaired
                            # Find the original word object for this content
                            for word_idx in range(i-1, -1, -1):
                                prev_token = tokens[word_idx]
                                if not isinstance(prev_token, str) and not prev_token.is_function_word:
                                    if prev_token.get_text() in part or prev_token.get_text_flat() in part:
                                        # Rollback any repairs on this word
                                        self.rollback_repair_stats(prev_token)
                                        self.rollback_repair(prev_token)
                                        break
                            
                            # Remove this content word and everything after it from result_parts
                            result_parts = result_parts[:idx]
                            
                            # Now add it back with underscores and all function words
                            result_parts.append(prev_token.get_text() + WORD_LINKER)
                            for w in func_group:
                                result_parts.append(w.get_text_flat())
                                result_parts.append(WORD_LINKER)
                            result_parts.pop()  # Remove last underscore
                            break
                    else:
                        # No content word found - just add function words
                        for w in func_group:
                            result_parts.append(w.get_text_flat())
                            result_parts.append(WORD_LINKER)
                        result_parts.pop()
                    
                    i = j
                    continue
                
                # Default: add function words with underscores
                for w in func_group:
                    result_parts.append(w.get_text_flat())
                    result_parts.append(WORD_LINKER)
                result_parts.pop()  # Remove trailing underscore
                i = j
                continue
            
            # ===== CONTENT WORD HANDLING =====
            
            # Check if word is already even
            if not word.needs_repair:
                result_parts.append(word.get_text())
                i += 1
                continue
            
            # Try internal repair
            repair = word.get_best_repair(self.style)
            if repair:
                word.apply_repair(repair)
                self.stats['words_repaired'] += 1
                self.stats['repaired_syllables'] += 1
                self.stats['repair_types'][repair['type']] += 1
                result_parts.append(word.get_text())
                i += 1
                continue
            
            # Try merging forward
            merged = [word]
            j = i + 1
            repaired = False
            
            while j < n and not repaired:
                next_token = tokens[j]
                if isinstance(next_token, str):
                    break
                
                merged.append(next_token)
                unit = MergedUnit(merged)
                
                if not unit.needs_repair:
                    for k, w in enumerate(merged):
                        result_parts.append(w.get_text())
                        if k < len(merged) - 1:
                            result_parts.append(WORD_LINKER)
                    i = j + 1
                    repaired = True
                    self.stats['merged_forward'] += 1
                    break
                
                repair = unit.get_best_repair(self.style)
                if repair:
                    unit.apply_repair(repair)
                    self.stats['words_repaired'] += 1
                    self.stats['repaired_syllables'] += 1
                    self.stats['repair_types'][repair['type']] += 1
                    
                    for k, w in enumerate(merged):
                        result_parts.append(w.get_text())
                        if k < len(merged) - 1:
                            result_parts.append(WORD_LINKER)
                    i = j + 1
                    repaired = True
                    self.stats['merged_forward'] += 1
                    break
                
                j += 1
            
            if repaired:
                continue
            
            # Last resort
            if word.syllables[-1].last_resort_repair():
                self._update_last_resort_stats(word.syllables[-1])
                result_parts.append(word.get_text())
            else:
                result_parts.append(word.get_text())
            i += 1
        
        return assemble_line(result_parts, tokens)
    
    def process_file(self, input_file: str, output_file: str, 
                    restore_diphthongs: bool = False,
                    only_restore_diphthongs: bool = False):
        
        print(f"\n{'='*80}")
        print(f"AKKADIAN PROSODY TOOLKIT — REPAIR ENGINE v{__version__}")
        print(f"{'='*80}")
        print(f"Input:  {input_file}")
        print(f"Output: {output_file}")
        
        if only_restore_diphthongs:
            print(f"Mode:   DIPHTHONG RESTORATION ONLY")
        else:
            print(f"Style:  {self.style.value.upper()}")
            print(f"Explicit + mode: {'ONLY LAST LINKED WORD' if self.only_last else 'ALLOW PROPAGATION'}")
            if restore_diphthongs:
                print(f"Option: RESTORE DIPHTHONGS")
        
        print(f"{'='*80}\n")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Processing {len(lines)} lines...")
        
        output_lines = []
        
        if only_restore_diphthongs:
            # MODE 1: Only restore diphthongs (no repair)
            for line_num, line in enumerate(lines):
                line = line.rstrip('\n')
                if not line.strip():
                    output_lines.append('')
                    continue
                # Just pass through the line as-is (diphthong restoration will happen after)
                output_lines.append(line)
                
                if (line_num + 1) % 10 == 0:
                    print(f"  Processed {line_num + 1}/{len(lines)} lines...")
        else:
            # MODE 2: Normal repair (with or without diphthong restoration)
            for line_num, line in enumerate(lines):
                line = line.rstrip('\n')
                if not line.strip():
                    output_lines.append('')
                    continue
                tokens = parse_syl_line(line)
                repaired_line = self.repair_line(tokens)
                output_lines.append(repaired_line)
                
                if (line_num + 1) % 10 == 0:
                    print(f"  Processed {line_num + 1}/{len(lines)} lines...")
        
        # Restore diphthongs if requested (in either mode)
        if restore_diphthongs or only_restore_diphthongs:
            print(f"\nRestoring diphthongs...")
            output_lines = postprocess_restore_diphthongs(output_lines)
        
        print(f"\nWriting output...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        if not only_restore_diphthongs:
            self._print_stats()

    def _print_stats(self):
        print(f"\n{'='*80}")
        print("REPAIR STATISTICS")
        print(f"{'='*80}")
        print(f"Words processed:       {self.stats['words']:6d}")
        print(f"  Function words:      {self.stats['function_words']:6d}")
        print(f"  Content words:       {self.stats['words'] - self.stats['function_words']:6d}")
        print(f"Words repaired:        {self.stats['words_repaired']:6d}")
        print(f"Total syllables:       {self.stats['total_syllables']:6d}")
        print(f"Repaired syllables:    {self.stats['repaired_syllables']:6d}")
        
        if self.stats['total_syllables'] > 0:
            rate = self.stats['repaired_syllables'] / self.stats['total_syllables'] * 100
            print(f"Repair rate:           {rate:5.2f}%")
        
        print(f"\nRepair types:")
        for rtype, count in self.stats['repair_types'].items():
            if count > 0:
                print(f"  {rtype:20s} {count:6d}")
        
        print(f"\nMerge operations:")
        print(f"  Forward merges:      {self.stats['merged_forward']:6d}")
        print(f"  Backward merges:     {self.stats['merged_backward']:6d}")
        print(f"  Last resort repairs: {self.stats['last_resort']:6d}")
        print(f"{'='*80}\n")


def test_diphthong_restoration() -> bool:
    """Test diphthong restoration using regex replacements."""
    print("\n" + "="*80)
    print("DIPHTHONG RESTORATION — REGEX TESTS")
    print("="*80)
    
    # Define the same replacements as in postprocess_restore_diphthongs
    def apply_replacements(text: str) -> str:
        """Apply replacements from most specific to least specific."""
        result = text
        
        replacements = [
            # 1. Patterns with tilde on BOTH vowels (rarest, most specific)
            (r'ū~\.ʾā~', 'uā~'),
            (r'û~\.ʾā~', 'uâ~'),
            (r'ū~\.ʾâ~', 'uâ~'),
            (r'û~\.ʾâ~', 'uâ~'),
            
            # 2. Patterns with tilde on first vowel
            (r'ū~\.ʾā', 'uā'),
            (r'û~\.ʾā', 'uâ'),
            (r'ū~\.ʾâ', 'uâ'),
            (r'û~\.ʾâ', 'uâ'),
            (r'ū~\.ʾa', 'uā~'),
            (r'û~\.ʾa', 'uâ~'),
            
            # 3. Patterns with tilde on second vowel
            (r'ū\.ʾā~', 'uā'),
            (r'û\.ʾā~', 'uâ'),
            (r'ū\.ʾâ~', 'uâ'),
            (r'û\.ʾâ~', 'uâ'),
            (r'u\.ʾā~', 'uā~'),
            (r'u\.ʾâ~', 'uâ~'),
            
            # 4. Patterns without tilde, both vowels long
            (r'ū\.ʾā', 'uā~'),
            (r'û\.ʾā', 'uâ~'),
            (r'ū\.ʾâ', 'uâ~'),
            (r'û\.ʾâ', 'uâ~'),
            
            # 5. Patterns with first vowel long, second short
            (r'ū\.ʾa', 'uā'),
            (r'û\.ʾa', 'uâ'),
            
            # 6. Patterns with first vowel short, second long
            (r'u\.ʾā', 'uā'),
            (r'u\.ʾâ', 'uâ'),
            
            # 7. Basic pattern both short
            (r'u\.ʾa', 'ua'),
            
            # 8. With consonant (capture and preserve)
            (r'([^aeiu]?)u\.ʾa', r'\1ua'),
            (r'([^aeiu]?)u\.ʾā', r'\1uā'),
            (r'([^aeiu]?)u\.ʾâ', r'\1uâ'),
        ]
        
        for pattern, repl in replacements:
            result = re.sub(pattern, repl, result)
        
        return result

    test_cases = [
        # Basic cases
        ("u.ʾa", "ua", "Simple u.ʾa → ua"),
        ("u.ʾā", "uā", "u.ʾā → uā"),
        ("u.ʾâ", "uâ", "u.ʾâ → uâ"),
        ("u.ʾā~", "uā~", "u.ʾā~ → uā~"),
        ("u.ʾâ~", "uâ~", "u.ʾâ~ → uâ~"),
        
        # First vowel long
        ("ū.ʾa", "uā", "ū.ʾa → uā"),
        ("û.ʾa", "uâ", "û.ʾa → uâ"),
        ("ū.ʾā", "uā~", "ū.ʾā → uā~"),
        ("û.ʾā", "uâ~", "û.ʾā → uâ~"),
        ("ū.ʾâ", "uâ~", "ū.ʾâ → uâ~"),
        ("û.ʾâ", "uâ~", "û.ʾâ → uâ~"),
        ("ū.ʾā~", "uā", "ū.ʾā~ → uā"),
        ("û.ʾā~", "uâ", "û.ʾā~ → uâ"),
        ("ū.ʾâ~", "uâ", "ū.ʾâ~ → uâ"),
        ("û.ʾâ~", "uâ", "û.ʾâ~ → uâ"),
        
        # With consonant
        ("ku.ʾa", "kua", "ku.ʾa → kua"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    print(f"\nRunning {total} tests...\n")
    
    for i, (inp, expected, desc) in enumerate(test_cases, 1):
        result = apply_replacements(inp)
        if result == expected:
            print(f"✅ Test {i}: {desc}")
            passed += 1
        else:
            print(f"❌ Test {i}: {desc}")
            print(f"   Input:    '{inp}'")
            print(f"   Expected: '{expected}'")
            print(f"   Got:      '{result}'")
    
    print(f"\nPassed: {passed}/{total}")
    return passed == total


def run_tests():
    """Run comprehensive tests for all three accent models."""
    print("\n" + "="*80)
    print("REPAIR TOOL — COMPREHENSIVE TESTS")
    print("="*80)
    
    test_cases = [
        # ===== BASIC TESTS (original 6) =====
        {
            'name': 'Basic line with merge and repair',
            'input': 'šar¦gi·mir¦dad·mē¦bā·nû¦kib·rā·ti¦‹ ···›',
            'expected': {
                'lob': 'šar gi·mir+dad~·mē bā·nû kib·rā~·ti ···',
                'sob': 'šar gi·mir+dad~·mē bā·nû kib·rā~·ti ···'
            }
        },
        {
            'name': 'Line with multiple repairs',
            'input': 'ḫen·dur·san·ga¦a·pil¦el·lil¦rēš·tû¦‹ ···›',
            'expected': {
                'lob': 'ḫen·dur·san~·ga a·pil+el~·lil rēš·tû~ ···',
                'sob': 'ḫen·dur·san~·ga a·pil+el~·lil rē~š·tû ···'
            }
        },
        {
            'name': 'Function words merge forward with content',
            'input': 'u¦a·na¦šar·ri¦',
            'expected': {
                'lob': 'u+ana+šar·ri',
                'sob': 'u+ana+šar·ri'
            }
        },
        {
            'name': 'Function word at end merges backward',
            'input': 'šar·ru¦u¦',
            'expected': {
                'lob': 'šar·ru+u',
                'sob': 'šar·ru+u'
            }
        },
        {
            'name': 'Word with final superheavy',
            'input': 'rēš·tû¦',
            'expected': {
                'lob': 'rēš·tû~',
                'sob': 'rē~š·tû'
            }
        },
        {
            'name': 'Multiple function words with content',
            'input': 'u¦a·na¦i·na¦šar·ri¦',
            'expected': {
                'lob': 'u+ana+ina+šar·ri',
                'sob': 'u+ana+ina+šar·ri'
            }
        },
        
        # ===== HYPHEN TESTS =====
        {
            'name': 'Word with hyphen - even morae (no repair)',
            'input': 'kam-du·tûm-lû¦',  # 2+1+3+2 = 8 (EVEN)
            'expected': {
                'lob': 'kam-du·tûm-lû',
                'sob': 'kam-du·tûm-lû'
            }
        },
        {
            'name': 'Word with hyphen - odd morae (repair needed)',
            'input': 'kam-du·tûm-lû·ma¦',  # 2+1+3+2+1 = 9 (ODD)
            'expected': {
                'lob': 'kam-du·tûm-lû~·ma',
                'sob': 'kam-du·tûm-lû~·ma'
            }
        },
        {
            'name': 'Word with multiple hyphens - already syllabified',
            'input': 'a·mē·lu-ša-ī·šum¦',  # From syllabify·py: 1+2+1+1+2+2 = 9 (ODD)
            'expected': {
                'lob': 'a·mē·lu-ša-ī~·šum',
                'sob': 'a·mē·lu-ša-ī~·šum'
            }
        },
        
        # ===== ENCLITIC -MA TESTS =====
        {
            'name': 'Word with -ma enclitic - even morae (no repair)',
            'input': 'ip-pa-lis-ma¦',  # ip-pa-lis-ma = 2+1+2+1 = 6 (EVEN)
            'expected': {
                'lob': 'ip-pa-lis-ma',
                'sob': 'ip-pa-lis-ma'
            }
        },
        {
            'name': 'Word with -ma enclitic - odd morae (repair needed)',
            'input': 'ī·ris·sū-ma¦',  # ī·ris·sū-ma = 2+2+2+1 = 7 (ODD)
            'expected': {
                'lob': 'ī·ris·sū~-ma',
                'sob': 'ī·ris·sū~-ma'
            }
        },
        
        # ===== MIXED SEPARATORS =====
        {
            'name': 'Mixed dots and hyphens - odd morae (repair needed)',
            'input': 'hen·dur-san·ga¦',  # hen·dur-san·ga = 2+2+2+1 = 7 (ODD)
            'expected': {
                'lob': 'hen·dur-san~·ga',
                'sob': 'hen·dur-san~·ga'
            }
        },
        
        # ===== COMPLEX REAL EXAMPLES =====
        {
            'name': 'Line with -ma enclitic',
            'input': 'ī·ris·sū-ma¦lib·ba·šu¦‹ — ›e·pēš¦tā·ḫā·zi¦',
            'expected': {
                'lob': 'ī·ris·sū~-ma lib·ba·šu — e·pēš tā·ḫā~·zi',
                'sob': 'ī·ris·sū~-ma lib·ba·šu — e·pēš tā·ḫā~·zi'
            }
        },
        {
            'name': 'Multiple hyphens and enclitics',
            'input': 'ī·tam·mi¦a·na¦kak·kī·šu¦‹ — ›lit·pa·tā¦i·mat¦mū·ti¦',
            'expected': {
                'lob': 'ī·tam~·mi ana+kak·kī·šu — lit~·pa·tā i·mat+mū·ti',
                'sob': 'ī·tam~·mi ana+kak·kī·šu — lit~·pa·tā i·mat+mū·ti'
            }
        },

        # ===== EXPLICIT '+' FROM INPUT TESTS =====
        {
            'name': 'Explicit plus forms one repair unit',
            'input': 'a·pil+el·lil¦',
            'expected': {
                'lob': 'a·pil+el~·lil',
                'sob': 'a·pil+el~·lil'
            }
        },
        {
            'name': 'Explicit plus keeps repair on linked tail (default strict)',
            'input': 'bā·nû+a·pil¦',
            'expected': {
                'lob': 'bā·nû+~a·pil',
                'sob': 'bā·nû+~a·pil'
            }
        },
        {
            'name': 'Multiple explicit plus links: only last word eligible',
            'input': 'bā·nû+a·pil+el·lil¦',
            'expected': {
                'lob': 'bā·nû+a·pil+el~·lil',
                'sob': 'bā·nû+a·pil+el~·lil'
            }
        },
        {
            'name': 'Explicit plus resolves internally before propagating further',
            'input': 'bā·nû+a·na·ku¦šar·ri¦',
            'expected': {
                'lob': 'bā·nû+a·na·ku+šar·ri',
                'sob': 'bā·nû+a·na·ku+šar·ri'
            }
        },
        {
            'name': 'Explicit plus unresolved at punctuation uses last-resort on last word',
            'input': 'šar+a·na·ku¦‹ ···›',
            'expected': {
                'lob': 'šar+~a·na·ku ···',
                'sob': 'šar+~a·na·ku ···'
            }
        },
        {
            'name': 'Explicit plus coexists with algorithmic plus',
            'input': 'a·pil+el·lil¦gi·mir¦dad·mē¦',
            'expected': {
                'lob': 'a·pil+el~·lil gi·mir+dad~·mē',
                'sob': 'a·pil+el~·lil gi·mir+dad~·mē'
            }
        },
        {
            'name': 'Explicit plus then function words with content',
            'input': 'šar+bā·nû¦u¦a·na¦i·na¦šar·ri¦',
            'expected': {
                'lob': 'šar+bā·nû u+ana+ina+šar·ri',
                'sob': 'šar+bā·nû u+ana+ina+šar·ri'
            }
        },
        
    ]


    all_passed = True
    
    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        print(f"\n--- Testing {style.value.upper()} ---")
        engine = RepairEngine(style=style)
        
        passed = 0
        total = 0
        
        for test in test_cases:
            total += 1
            tokens = parse_syl_line(test['input'])
            result = engine.repair_line(tokens)
            expected = test['expected'][style.value]
            
            # Normalize spaces for comparison
            result = ' '.join(result.split())
            expected = ' '.join(expected.split())
            
            if result == expected:
                print(f"  ✅ Test {total}: {test['name']}")
                passed += 1
            else:
                print(f"  ❌ Test {total}: {test['name']}")
                print(f"     Input:    {test['input']}")
                print(f"     Expected: {expected}")
                print(f"     Got:      {result}")
                all_passed = False
        
        print(f"  Passed: {passed}/{total}")

    # Verify relaxed behavior with only_last=False for explicit '+' groups.
    relaxed_cases = [
        {
            'name': 'relax_last allows propagation to previous linked word',
            'input': 'bā·nû+a·pil¦',
            'expected': {
                'lob': 'bā·nû~+a·pil',
                'sob': 'bā·nû~+a·pil',
            }
        },
        {
            'name': 'relax_last still allows final linked repair in 3-word chain',
            'input': 'bā·nû+a·pil+el·lil¦',
            'expected': {
                'lob': 'bā·nû+a·pil+el~·lil',
                'sob': 'bā·nû+a·pil+el~·lil',
            }
        },
        {
            'name': 'relax_last may repair before linked tail when legal',
            'input': 'bā·nû+a·na·ku¦šar·ri¦',
            'expected': {
                'lob': 'bā·nû~+a·na·ku šar~·ri',
                'sob': 'bā·nû~+a·na·ku šar~·ri',
            }
        },
        {
            'name': 'relax_last unresolved at punctuation uses last-resort on tail',
            'input': 'šar+a·na·ku¦‹ ···›',
            'expected': {
                'lob': 'šar+~a·na·ku ···',
                'sob': 'šar+~a·na·ku ···',
            }
        },
    ]

    print("\n--- Testing RELAX_LAST mode ---")
    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        engine = RepairEngine(style=style, only_last=False)
        for test in relaxed_cases:
            tokens = parse_syl_line(test['input'])
            result = engine.repair_line(tokens)
            expected = test['expected'][style.value]

            result = ' '.join(result.split())
            expected = ' '.join(expected.split())

            if result == expected:
                print(f"  ✅ {style.value.upper()}: {test['name']}")
            else:
                print(f"  ❌ {style.value.upper()}: {test['name']}")
                print(f"     Input:    {test['input']}")
                print(f"     Expected: {expected}")
                print(f"     Got:      {result}")
                all_passed = False
    
    print(f"\n{'='*80}")
    print(f"Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print(f"{'='*80}\n")
    
    return all_passed

