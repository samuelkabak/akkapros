#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit - Moraic Prosody Realization System
"""

import re
import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple, Union, Dict, Set

from akkapros import __version__
from akkapros.lib.frontmatter import (
    build_output_frontmatter,
    build_prosody_stage_data,
    count_lines,
    count_prosodic_units,
    compose_text_document,
    resolve_file_title,
    read_text_file,
)
from akkapros.lib.utils import (
    format_path_for_logging,
    format_selftest_label,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
)


# shared constants
from akkapros.lib.constants import (
    AKKADIAN_VOWELS,
    AKKADIAN_CONSONANTS,
    LONG_VOWELS,
    SHORT_VOWELS,
    GLOTTAL,
    SYL_WORD_ENDING,
    SYL_SEPARATOR,
    OPEN_ESCAPE,
    CLOSE_ESCAPE,
    WORD_LINKER,
    CIRCUMFLEX_VOWELS,
    DIPH_SEPARATOR,
    FUNCTION_WORDS,
)

HYPHEN = '-'
LOGGER = logging.getLogger(__name__)

# ------------------------------------------------------------
# Phonetic inventory
# ------------------------------------------------------------
LONG = set(LONG_VOWELS)
SHORT = set(SHORT_VOWELS)
V = LONG | SHORT
C = set(AKKADIAN_CONSONANTS)
CIRCUMFLEX = set(CIRCUMFLEX_VOWELS)



# FUNCTION_WORDS imported from akkapros.lib.constants (see ADR-009)


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
        self.is_accentuated = False
        self.accentuation_type = None
        
        self.type, self.morae = self._classify(text)
        self.accentuated_morae = self.morae
        self.accentuated_text = text
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
                self.accentuated_text = self.text[:i+1] + '~' + self.text[i+1:]
                self.accentuated_morae = self.morae + 1
                self.is_accentuated = True
                self.accentuation_type = 'lengthen_vowel'
                return True
        return False
    
    def geminate_coda(self) -> bool:
        if not self.can_geminate_coda():
            return False
        self.accentuated_text = self.text + '~'
        self.accentuated_morae = self.morae + 1
        self.is_accentuated = True
        self.accentuation_type = 'geminate_coda'
        return True
    
    def geminate_onset(self) -> bool:
        if self.text[0] in C:
            self.accentuated_text = self.text[0] + '~' + self.text[1:]
            self.accentuated_morae = self.morae + 1
            self.is_accentuated = True
            self.accentuation_type = 'geminate_onset'
            return True
        elif self.text[0] in V:
            self.accentuated_text = '~' + self.text
            self.accentuated_morae = self.morae + 1
            self.is_accentuated = True
            self.accentuation_type = 'geminate_glottal'
            return True
        return False
    
    def last_resort_accentuation(self) -> bool:
        return self.geminate_onset()
    
    def __repr__(self):
        status = "~" if self.is_accentuated else ""
        return f"{self.text}{status}({self.morae}→{self.accentuated_morae})"


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
    def accentuated_morae(self) -> int:
        return sum(s.accentuated_morae for s in self.syllables)
    
    @property
    def needs_accentuation(self) -> bool:
        return self.accentuated_morae % 2 == 1
    
    def has_heavy_syllable(self) -> bool:
        """Check if word has any heavy syllable (CVC, CVV, etc.)"""
        return any(s.morae >= 2 for s in self.syllables)
    
    def get_accentuation_candidates(self, style: AccentStyle) -> List[Dict]:
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
    
    def get_best_accentuation(self, style: AccentStyle) -> Optional[Dict]:
        candidates = self.get_accentuation_candidates(style)
        return candidates[0] if candidates else None
    
    def apply_accentuation(self, accentuation: Dict) -> bool:
        if not accentuation:
            return False
        position = accentuation['position']
        syl = self.syllables[position]
        accentuation_type = accentuation['type']
        
        if accentuation_type == 'lengthen_vowel':
            return syl.lengthen_vowel()
        elif accentuation_type == 'geminate_coda':
            return syl.geminate_coda()
        elif accentuation_type == 'geminate_onset':
            return syl.geminate_onset()
        return False
    
    def get_text(self) -> str:
        """Get the word text with accentuations and original separators."""
        result = []
        for i, syl in enumerate(self.syllables):
            result.append(syl.accentuated_text)
            if i < len(self.separators):
                result.append(self.separators[i])
        return ''.join(result)
    
    def get_text_flat(self) -> str:
        """Get text without dots or hyphens (for function words)."""
        return ''.join(s.accentuated_text for s in self.syllables)
    
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
        # are ineligible for accentuation candidates.
        locked_prefix_words = max(0, min(locked_prefix_words, len(words)))
        ineligible_count = sum(len(w.syllables) for w in words[:locked_prefix_words])
        self.pre_linker_syllables = set(range(ineligible_count))
    
    @property
    def morae(self) -> int:
        return sum(s.accentuated_morae for s in self.syllables)
    
    @property
    def needs_accentuation(self) -> bool:
        return self.morae % 2 == 1
    
    def is_syllable_final_in_word(self, syl_idx: int) -> bool:
        return syl_idx in self.word_boundaries

    def is_syllable_before_linker(self, syl_idx: int) -> bool:
        return syl_idx in self.pre_linker_syllables
    
    def get_best_accentuation(self, style: AccentStyle) -> Optional[Dict]:
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
    
    def apply_accentuation(self, accentuation: Dict) -> bool:
        if not accentuation:
            return False
        position = accentuation['position']
        syl = self.syllables[position]
        accentuation_type = accentuation['type']
        
        if accentuation_type == 'lengthen_vowel':
            return syl.lengthen_vowel()
        elif accentuation_type == 'geminate_coda':
            return syl.geminate_coda()
        elif accentuation_type == 'geminate_onset':
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

    assembled = ''.join(result)
    # Join-time normalization avoids duplicate spacing introduced by escaped chunks.
    assembled = re.sub(r' {2,}', ' ', assembled)
    return assembled.strip()



# ------------------------------------------------------------
# Diphthong restoration (always applied in accentuation output)
# ------------------------------------------------------------

from akkapros.lib.diphthongs import ALL_REPLACEMENTS


def _pivot_diphthong_replacement(replacement: str) -> str:
    """Generated replacements already encode the exact pivot form to emit."""
    return replacement

def postprocess_restore_diphthongs(output_lines: List[str]) -> List[str]:
    """
    Restore diphthongs using generated regex patterns.

    The *_tilde pivot format keeps DIPH_SEPARATOR so downstream metrics and
    print rendering can still see restored diphthong-internal syllable breaks.
    """
    
    new_lines = []
    for line in output_lines:
        for pattern, repl in ALL_REPLACEMENTS:
            line = re.sub(pattern, _pivot_diphthong_replacement(repl), line)
        new_lines.append(line)
    
    return new_lines


#------------------------

class ProsodyEngine:
    def __init__(self, style: AccentStyle = AccentStyle.SOB, only_last: bool = True):
        self.style = style
        self.only_last = only_last
        self.stats = {
            'words': 0,
            'function_words': 0,
            'words_accentuated': 0,
            'merged_forward': 0,
            'merged_backward': 0,
            'last_resort': 0,
            'total_syllables': 0,
            'accentuated_syllables': 0,
            'accentuation_types': {
                'lengthen_vowel': 0,
                'geminate_coda': 0,
                'geminate_onset': 0,
                'geminate_glottal': 0
            }
        }
    
    def _update_last_resort_stats(self, syllable: Syllable):
        self.stats['last_resort'] += 1
        self.stats['accentuated_syllables'] += 1
        if syllable.text[0] in C:
            self.stats['accentuation_types']['geminate_onset'] += 1
        else:
            self.stats['accentuation_types']['geminate_glottal'] += 1
    
    def rollback_accentuation(self, word: Word) -> None:
        """Remove all accentuations from a word."""
        for syllable in word.syllables:
            syllable.is_accentuated = False
            syllable.accentuation_type = None
            syllable.accentuated_morae = syllable.morae
            syllable.accentuated_text = syllable.text

    def rollback_accentuation_stats(self, word: Word) -> None:
        """Revert accentuation counters for accentuations that are being rolled back."""
        accentuated_in_word = 0
        for syllable in word.syllables:
            if syllable.is_accentuated:
                accentuated_in_word += 1
                self.stats['accentuated_syllables'] = max(0, self.stats['accentuated_syllables'] - 1)
                accentuation_type = syllable.accentuation_type
                if accentuation_type and accentuation_type in self.stats['accentuation_types']:
                    self.stats['accentuation_types'][accentuation_type] = max(
                        0, self.stats['accentuation_types'][accentuation_type] - 1
                    )

        if accentuated_in_word > 0:
            self.stats['words_accentuated'] = max(0, self.stats['words_accentuated'] - 1)

    def _get_explicit_group_accentuation(self, unit: MergedUnit) -> Optional[Dict]:
        """Pick accentuation site for explicit '+' groups.

        - only_last=True: use standard model priorities, with pre-linker lock.
        - only_last=False: allow propagation and choose the rightmost legal site.
        """
        if self.only_last:
            return unit.get_best_accentuation(self.style)

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
    
    def accentuation_line(self, tokens: List[Union[Word, str]]) -> str:
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
                        result_parts.append(linked_word.get_text())
                        if k < len(words_group) - 1:
                            result_parts.append(WORD_LINKER)

                def resolve_group(words_group: List[Word]) -> Tuple[bool, bool]:
                    unit = MergedUnit(words_group, locked_prefix_words=explicit_tail_start)
                    if not unit.needs_accentuation:
                        return True, False
                    accentuation = self._get_explicit_group_accentuation(unit)
                    if accentuation:
                        unit.apply_accentuation(accentuation)
                        self.stats['words_accentuated'] += 1
                        self.stats['accentuated_syllables'] += 1
                        self.stats['accentuation_types'][accentuation['type']] += 1
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

                # If explicit group cannot be accentuated, keep merging forward
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
                    if last_word.syllables and last_word.syllables[0].last_resort_accentuation():
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
                            # Found a content word - need to rollback if it was accentuated
                            # Find the original word object for this content
                            matched_prev_word: Union[Word, None] = None
                            for word_idx in range(i-1, -1, -1):
                                prev_token = tokens[word_idx]
                                if not isinstance(prev_token, str) and not prev_token.is_function_word:
                                    if prev_token.get_text() in part or prev_token.get_text_flat() in part:
                                        # Rollback any accentuations on this word
                                        self.rollback_accentuation_stats(prev_token)
                                        self.rollback_accentuation(prev_token)
                                        matched_prev_word = prev_token
                                        break
                            
                            # Remove this content word and everything after it from result_parts
                            result_parts = result_parts[:idx]
                            
                            # Now add it back with underscores and all function words
                            base_part = matched_prev_word.get_text() if matched_prev_word else part
                            result_parts.append(base_part + WORD_LINKER)
                            for w in func_group:
                                result_parts.append(w.get_text())
                                result_parts.append(WORD_LINKER)
                            result_parts.pop()  # Remove last underscore
                            break
                    else:
                        # No content word found - just add function words
                        for w in func_group:
                            result_parts.append(w.get_text())
                            result_parts.append(WORD_LINKER)
                        result_parts.pop()
                    
                    i = j
                    continue
                
                # Default: add function words with underscores
                for w in func_group:
                    result_parts.append(w.get_text())
                    result_parts.append(WORD_LINKER)
                result_parts.pop()  # Remove trailing underscore
                i = j
                continue
            
            # ===== CONTENT WORD HANDLING =====
            
            # Check if word is already even
            if not word.needs_accentuation:
                result_parts.append(word.get_text())
                i += 1
                continue
            
            # Try internal accentuation
            accentuation = word.get_best_accentuation(self.style)
            if accentuation:
                word.apply_accentuation(accentuation)
                self.stats['words_accentuated'] += 1
                self.stats['accentuated_syllables'] += 1
                self.stats['accentuation_types'][accentuation['type']] += 1
                result_parts.append(word.get_text())
                i += 1
                continue
            
            # Try merging forward
            merged = [word]
            j = i + 1
            accentuated = False
            
            while j < n and not accentuated:
                next_token = tokens[j]
                if isinstance(next_token, str):
                    break
                
                merged.append(next_token)
                unit = MergedUnit(merged)
                
                if not unit.needs_accentuation:
                    for k, w in enumerate(merged):
                        result_parts.append(w.get_text())
                        if k < len(merged) - 1:
                            result_parts.append(WORD_LINKER)
                    i = j + 1
                    accentuated = True
                    self.stats['merged_forward'] += 1
                    break
                
                accentuation = unit.get_best_accentuation(self.style)
                if accentuation:
                    unit.apply_accentuation(accentuation)
                    self.stats['words_accentuated'] += 1
                    self.stats['accentuated_syllables'] += 1
                    self.stats['accentuation_types'][accentuation['type']] += 1
                    
                    for k, w in enumerate(merged):
                        result_parts.append(w.get_text())
                        if k < len(merged) - 1:
                            result_parts.append(WORD_LINKER)
                    i = j + 1
                    accentuated = True
                    self.stats['merged_forward'] += 1
                    break
                
                j += 1
            
            if accentuated:
                continue
            
            # Last resort
            if word.syllables[-1].last_resort_accentuation():
                self._update_last_resort_stats(word.syllables[-1])
                result_parts.append(word.get_text())
            else:
                result_parts.append(word.get_text())
            i += 1
        
        return assemble_line(result_parts, tokens)
    
    def process_file(self, input_file: str, output_file: str, *, options: dict | None = None):
        LOGGER.info('Source file: %s', format_path_for_logging(input_file))
        LOGGER.info('Style: %s', self.style.value.upper())
        LOGGER.info(
            'Explicit + mode: %s',
            'only-last' if self.only_last else 'allow-propagation',
        )
        LOGGER.info('Diphthong restore: always')
        
        input_frontmatter, text = read_text_file(input_file)
        lines = text.splitlines(keepends=True)
        
        output_lines = []
        
        for line_num, line in enumerate(lines):
            line = line.rstrip('\n')
            if not line.strip():
                output_lines.append('')
                continue
            tokens = parse_syl_line(line)
            accentuated_line = self.accentuation_line(tokens)
            output_lines.append(accentuated_line)
        output_lines = postprocess_restore_diphthongs(output_lines)

        output_body = '\n'.join(output_lines) + '\n'
        LOGGER.info('Computed line_count: %d', count_lines(output_body))
        LOGGER.info('Computed prosodic_unit_count: %d', count_prosodic_units(output_body))
        frontmatter = build_output_frontmatter(
            output_path=output_file,
            step='prosody',
            title=resolve_file_title(input_frontmatter),
            body=output_body,
            options=options,
            stage_data=build_prosody_stage_data(
                text,
                output_body,
                input_frontmatter=input_frontmatter,
                accentuated_syllable_count=self.stats['accentuated_syllables'],
            ),
            input_frontmatter=input_frontmatter,
            file_format='tilde',
        )
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(compose_text_document(frontmatter, output_body))
        LOGGER.info('Written file: %s', format_path_for_logging(output_file))
        
        self._print_stats()

    def _print_stats(self):
        LOGGER.info('Words processed:       %6d', self.stats['words'])
        LOGGER.info('  Function words:      %6d', self.stats['function_words'])
        LOGGER.info('  Content words:       %6d', self.stats['words'] - self.stats['function_words'])
        LOGGER.info('Words accentuated:        %6d', self.stats['words_accentuated'])
        LOGGER.info('Total syllables:       %6d', self.stats['total_syllables'])
        LOGGER.info('Accentuated syllables:    %6d', self.stats['accentuated_syllables'])
        
        if self.stats['total_syllables'] > 0:
            rate = self.stats['accentuated_syllables'] / self.stats['total_syllables'] * 100
            LOGGER.info('Accentuation rate:           %5.2f%%', rate)
        
        LOGGER.info('Accentuation types:')
        for rtype, count in self.stats['accentuation_types'].items():
            if count > 0:
                LOGGER.info('  %-20s %6d', rtype, count)
        
        LOGGER.info('Merge operations:')
        LOGGER.info('  Forward merges:      %6d', self.stats['merged_forward'])
        LOGGER.info('  Backward merges:     %6d', self.stats['merged_backward'])
        LOGGER.info('  Last resort accentuations: %6d', self.stats['last_resort'])


def test_diphthong_restoration() -> bool:
    """Test diphthong restoration using generated DIPH_SEPARATOR patterns."""
    logger = get_logger_with_fallback(__name__)

    def restore_one(text: str) -> str:
        return postprocess_restore_diphthongs([text])[0]

    test_cases = [
        (f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}a", f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}a", "Simple short u+a keeps pivot hiatus markers"),
        (f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā", f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā", "Short+long u+a keeps pivot hiatus markers"),
        (f"ū{SYL_SEPARATOR}{DIPH_SEPARATOR}a", f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā", "Long+short u+a preserves boundary while normalizing length"),
        (f"ū{SYL_SEPARATOR}{DIPH_SEPARATOR}ā", f"u{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~", "Long+long u+a preserves boundary and accent"),
        (f"i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē", f"i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē", "Different-vowel hiatus keeps separator"),
        (f"i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē~", f"i{SYL_SEPARATOR}{DIPH_SEPARATOR}ē~", "Different-vowel hiatus with accent keeps separator"),
        (f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}a", "â", "Identical short vowels -> circumflex"),
        (f"a{SYL_SEPARATOR}{DIPH_SEPARATOR}a~", "â~", "Identical short+tilde -> circumflex+tilde"),
        (f"ku{SYL_SEPARATOR}{DIPH_SEPARATOR}a", f"ku{SYL_SEPARATOR}{DIPH_SEPARATOR}a", "Consonant context preserved"),
        (f"ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu", f"ti{SYL_SEPARATOR}{DIPH_SEPARATOR}ā~m{SYL_SEPARATOR}tu", "Pivot example keeps clear syllable separation"),
        (f"ba{DIPH_SEPARATOR}ru", f"ba{DIPH_SEPARATOR}ru", "Existing diphthong memory is preserved"),
        (f"ta{SYL_SEPARATOR}{DIPH_SEPARATOR}a ki", "tâ ki", "In-line restoration in phrase"),
    ]
    
    total = len(test_cases)

    passed = 0
    for i, (inp, expected, desc) in enumerate(test_cases, 1):
        result = restore_one(inp)
        label = format_selftest_label(i, total, desc)
        if result == expected:
            passed += 1
            log_selftest_result(logger, True, 'Diphthongs', label)
        else:
            log_selftest_result(
                logger,
                False,
                'Diphthongs',
                label,
                details=[
                    f'input={inp!r}',
                    f'expected={expected!r}',
                    f'got={result!r}',
                ],
            )

    log_selftest_summary(logger, 'Diphthongs', passed, total)
    return passed == total


def run_tests():
    """Run comprehensive tests for all three accent models."""
    logger = get_logger_with_fallback(__name__)
    
    test_cases = [
        # ===== BASIC TESTS (original 6) =====
        {
            'name': 'Basic line with merge and accentuation',
            'input': 'šar¦gi·mir¦dad·mē¦bā·nû¦kib·rā·ti¦⟦ ···⟧',
            'expected': {
                'lob': 'šar gi·mir+dad~·mē bā·nû kib·rā~·ti ···',
                'sob': 'šar gi·mir+dad~·mē bā·nû kib·rā~·ti ···'
            }
        },
        {
            'name': 'Line with multiple accentuation operations',
            'input': 'ḫen·dur·san·ga¦a·pil¦el·lil¦rēš·tû¦⟦ ···⟧',
            'expected': {
                'lob': 'ḫen·dur·san~·ga a·pil+el~·lil rēš·tû~ ···',
                'sob': 'ḫen·dur·san~·ga a·pil+el~·lil rē~š·tû ···'
            }
        },
        {
            'name': 'Function words merge forward with content',
            'input': 'u¦a·na¦šar·ri¦',
            'expected': {
                'lob': 'u+a·na+šar·ri',
                'sob': 'u+a·na+šar·ri'
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
                'lob': 'u+a·na+i·na+šar·ri',
                'sob': 'u+a·na+i·na+šar·ri'
            }
        },
        
        # ===== HYPHEN TESTS =====
        {
            'name': 'Word with hyphen - even morae (no accentuation)',
            'input': 'kam-du·tûm-lû¦',  # 2+1+3+2 = 8 (EVEN)
            'expected': {
                'lob': 'kam-du·tûm-lû',
                'sob': 'kam-du·tûm-lû'
            }
        },
        {
            'name': 'Word with hyphen - odd morae (accentuation needed)',
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
            'name': 'Word with -ma enclitic - even morae (no accentuation)',
            'input': 'ip-pa-lis-ma¦',  # ip-pa-lis-ma = 2+1+2+1 = 6 (EVEN)
            'expected': {
                'lob': 'ip-pa-lis-ma',
                'sob': 'ip-pa-lis-ma'
            }
        },
        {
            'name': 'Word with -ma enclitic - odd morae (accentuation needed)',
            'input': 'ī·ris·sū-ma¦',  # ī·ris·sū-ma = 2+2+2+1 = 7 (ODD)
            'expected': {
                'lob': 'ī·ris·sū~-ma',
                'sob': 'ī·ris·sū~-ma'
            }
        },
        
        # ===== MIXED SEPARATORS =====
        {
            'name': 'Mixed dots and hyphens - odd morae (accentuation needed)',
            'input': 'hen·dur-san·ga¦',  # hen·dur-san·ga = 2+2+2+1 = 7 (ODD)
            'expected': {
                'lob': 'hen·dur-san~·ga',
                'sob': 'hen·dur-san~·ga'
            }
        },
        
        # ===== COMPLEX REAL EXAMPLES =====
        {
            'name': 'Line with -ma enclitic',
            'input': 'ī·ris·sū-ma¦lib·ba·šu¦⟦ — ⟧e·pēš¦tā·ḫā·zi¦',
            'expected': {
                'lob': 'ī·ris·sū~-ma lib·ba·šu — e·pēš tā·ḫā~·zi',
                'sob': 'ī·ris·sū~-ma lib·ba·šu — e·pēš tā·ḫā~·zi'
            }
        },
        {
            'name': 'Multiple hyphens and enclitics',
            'input': 'ī·tam·mi¦a·na¦kak·kī·šu¦⟦ — ⟧lit·pa·tā¦i·mat¦mū·ti¦',
            'expected': {
                'lob': 'ī·tam~·mi a·na+kak·kī·šu — lit~·pa·tā i·mat+mū·ti',
                'sob': 'ī·tam~·mi a·na+kak·kī·šu — lit~·pa·tā i·mat+mū·ti'
            }
        },

        # ===== EXPLICIT '+' FROM INPUT TESTS =====
        {
            'name': 'Explicit plus forms one accentuation unit',
            'input': 'a·pil+el·lil¦',
            'expected': {
                'lob': 'a·pil+el~·lil',
                'sob': 'a·pil+el~·lil'
            }
        },
        {
            'name': 'Explicit plus keeps accentuation on linked tail (default strict)',
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
            'input': 'šar+a·na·ku¦⟦ ···⟧',
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
                'lob': 'šar+bā·nû u+a·na+i·na+šar·ri',
                'sob': 'šar+bā·nû u+a·na+i·na+šar·ri'
            }
        },
        
    ]


    all_passed = True
    total_passed = 0
    
    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        engine = ProsodyEngine(style=style)
        
        passed = 0
        total = 0
        category = f'Prosody/{style.value.upper()}'
        
        for test in test_cases:
            total += 1
            tokens = parse_syl_line(test['input'])
            result = engine.accentuation_line(tokens)
            expected = test['expected'][style.value]
            
            # Normalize spaces for comparison
            result = ' '.join(result.split())
            expected = ' '.join(expected.split())
            label = format_selftest_label(total, len(test_cases), test['name'])
            
            if result == expected:
                passed += 1
                total_passed += 1
                log_selftest_result(logger, True, category, label)
            else:
                all_passed = False
                log_selftest_result(
                    logger,
                    False,
                    category,
                    label,
                    details=[
                        f'input={test["input"]!r}',
                        f'expected={expected!r}',
                        f'got={result!r}',
                    ],
                )

        log_selftest_summary(logger, category, passed, total)

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
            'name': 'relax_last still allows final linked accentuation in 3-word chain',
            'input': 'bā·nû+a·pil+el·lil¦',
            'expected': {
                'lob': 'bā·nû+a·pil+el~·lil',
                'sob': 'bā·nû+a·pil+el~·lil',
            }
        },
        {
            'name': 'relax_last may place accentuation before linked tail when legal',
            'input': 'bā·nû+a·na·ku¦šar·ri¦',
            'expected': {
                'lob': 'bā·nû~+a·na·ku šar~·ri',
                'sob': 'bā·nû~+a·na·ku šar~·ri',
            }
        },
        {
            'name': 'relax_last unresolved at punctuation uses last-resort on tail',
            'input': 'šar+a·na·ku¦⟦ ···⟧',
            'expected': {
                'lob': 'šar+~a·na·ku ···',
                'sob': 'šar+~a·na·ku ···',
            }
        },
    ]

    relaxed_total = len(relaxed_cases) * 2
    relaxed_passed = 0
    relaxed_index = 0
    for style in [AccentStyle.LOB, AccentStyle.SOB]:
        engine = ProsodyEngine(style=style, only_last=False)
        category = f'Prosody/{style.value.upper()}'
        for test in relaxed_cases:
            relaxed_index += 1
            tokens = parse_syl_line(test['input'])
            result = engine.accentuation_line(tokens)
            expected = test['expected'][style.value]

            result = ' '.join(result.split())
            expected = ' '.join(expected.split())
            label = format_selftest_label(relaxed_index, relaxed_total, f"Relax last {test['name']}")

            if result == expected:
                relaxed_passed += 1
                total_passed += 1
                log_selftest_result(logger, True, category, label)
            else:
                all_passed = False
                log_selftest_result(
                    logger,
                    False,
                    category,
                    label,
                    details=[
                        f'input={test["input"]!r}',
                        f'expected={expected!r}',
                        f'got={result!r}',
                    ],
                )

    log_selftest_summary(logger, 'Prosody relax', relaxed_passed, relaxed_total)
    total_cases = (len(test_cases) * 2) + relaxed_total
    log_selftest_summary(logger, 'Prosody', total_passed, total_cases)
    
    return all_passed




