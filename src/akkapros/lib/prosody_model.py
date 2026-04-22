from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from akkapros.lib._prosody_text import is_function_word
from akkapros.lib._prosody_types import AccentStyle, MoraMode
from akkapros.lib.constants import (
    AKKADIAN_CONSONANTS,
    CIRCUMFLEX_VOWELS,
    LONG_VOWELS,
    SHORT_VOWELS,
    SYL_SEPARATOR,
)


HYPHEN = '-'
LONG = set(LONG_VOWELS)
SHORT = set(SHORT_VOWELS)
V = LONG | SHORT
C = set(AKKADIAN_CONSONANTS)
CIRCUMFLEX = set(CIRCUMFLEX_VOWELS)


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
            return ('VV' if has_long else 'V', 2 if has_long else 1)

        if has_coda:
            return ('CVVC' if has_long else 'CVC', 3 if has_long else 2)
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
                self.accentuated_text = self.text[: i + 1] + '~' + self.text[i + 1 :]
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
        if self.text[0] in V:
            self.accentuated_text = '~' + self.text
            self.accentuated_morae = self.morae + 1
            self.is_accentuated = True
            self.accentuation_type = 'geminate_glottal'
            return True
        return False

    def last_resort_accentuation(self) -> bool:
        return self.geminate_onset()

    def __repr__(self):
        status = '~' if self.is_accentuated else ''
        return f'{self.text}{status}({self.morae}→{self.accentuated_morae})'


class Word:
    def __init__(self, text: str, word_idx: int):
        self.original_text = text
        self.word_idx = word_idx
        self.is_function_word = is_function_word(text)
        self.syllables = []
        self.separators = []

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

    def should_attempt_accentuation(self, mora_mode: MoraMode) -> bool:
        if self.is_function_word:
            return False
        if mora_mode == MoraMode.MONO:
            return True
        return self.needs_accentuation

    def has_heavy_syllable(self) -> bool:
        return any(s.morae >= 2 for s in self.syllables)

    def get_accentuation_candidates(self, style: AccentStyle) -> List[Dict]:
        if self.is_function_word:
            return []

        candidates = []
        n_syllables = len(self.syllables)

        if style == AccentStyle.LOB:
            final = self.syllables[-1]
            is_superheavy = final.type in ('CVVC', 'VVC') or (
                final.has_circumflex and final.type in ('CVV', 'VV')
            )
            if is_superheavy and final.is_final_in_word(n_syllables):
                candidates.append(
                    {
                        'position': n_syllables - 1,
                        'type': 'lengthen_vowel',
                        'rule': f'{style.value.upper()}_final_superheavy',
                        'priority': 1,
                    }
                )

        for i in range(n_syllables - 2, -1, -1):
            syl = self.syllables[i]
            if syl.can_lengthen_vowel():
                candidates.append(
                    {
                        'position': i,
                        'type': 'lengthen_vowel',
                        'rule': 'heavy_nonfinal',
                        'priority': 2,
                    }
                )
            elif syl.can_geminate_coda():
                candidates.append(
                    {
                        'position': i,
                        'type': 'geminate_coda',
                        'rule': 'heavy_nonfinal',
                        'priority': 2,
                    }
                )

        final = self.syllables[-1]
        if style == AccentStyle.LOB:
            if final.can_lengthen_vowel():
                candidates.append(
                    {
                        'position': n_syllables - 1,
                        'type': 'lengthen_vowel',
                        'rule': 'LOB_final_heavy',
                        'priority': 3,
                    }
                )
        elif style == AccentStyle.SOB:
            if final.can_lengthen_vowel():
                candidates.append(
                    {
                        'position': n_syllables - 1,
                        'type': 'lengthen_vowel',
                        'rule': 'SOB_final_heavy',
                        'priority': 3,
                    }
                )

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
        if accentuation_type == 'geminate_coda':
            return syl.geminate_coda()
        if accentuation_type == 'geminate_onset':
            return syl.geminate_onset()
        return False

    def get_text(self) -> str:
        result = []
        for i, syl in enumerate(self.syllables):
            result.append(syl.accentuated_text)
            if i < len(self.separators):
                result.append(self.separators[i])
        return ''.join(result)

    def get_text_flat(self) -> str:
        return ''.join(s.accentuated_text for s in self.syllables)

    def __repr__(self):
        status = ' (FUNC)' if self.is_function_word else ''
        return f'Word({self.original_text}{status})'


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

        locked_prefix_words = max(0, min(locked_prefix_words, len(words)))
        ineligible_count = sum(len(w.syllables) for w in words[:locked_prefix_words])
        self.pre_linker_syllables = set(range(ineligible_count))

    @property
    def morae(self) -> int:
        return sum(s.accentuated_morae for s in self.syllables)

    @property
    def needs_accentuation(self) -> bool:
        return self.morae % 2 == 1

    def should_attempt_accentuation(self, mora_mode: MoraMode) -> bool:
        if mora_mode == MoraMode.MONO:
            return True
        return self.needs_accentuation

    def is_syllable_final_in_word(self, syl_idx: int) -> bool:
        return syl_idx in self.word_boundaries

    def is_syllable_before_linker(self, syl_idx: int) -> bool:
        return syl_idx in self.pre_linker_syllables

    def get_best_accentuation(self, style: AccentStyle) -> Optional[Dict]:
        candidates = []
        n_syllables = len(self.syllables)

        if style == AccentStyle.LOB:
            final = self.syllables[-1]
            is_superheavy = final.type in ('CVVC', 'VVC') or (
                final.has_circumflex and final.type in ('CVV', 'VV')
            )
            if is_superheavy:
                candidates.append(
                    {
                        'position': n_syllables - 1,
                        'type': 'lengthen_vowel',
                        'word_idx': final.word_idx,
                        'rule': f'{style.value.upper()}_final_superheavy',
                        'priority': 1,
                    }
                )

        for i in range(n_syllables - 1, -1, -1):
            syl = self.syllables[i]
            if self.is_syllable_before_linker(i):
                continue
            is_final_in_word = self.is_syllable_final_in_word(i)

            if syl.can_lengthen_vowel():
                rule = 'heavy_nonfinal' if not is_final_in_word else 'final_heavy'
                priority = 2 if not is_final_in_word else 3
                candidates.append(
                    {
                        'position': i,
                        'type': 'lengthen_vowel',
                        'word_idx': syl.word_idx,
                        'rule': rule,
                        'priority': priority,
                    }
                )
            elif syl.can_geminate_coda() and not is_final_in_word:
                candidates.append(
                    {
                        'position': i,
                        'type': 'geminate_coda',
                        'word_idx': syl.word_idx,
                        'rule': 'heavy_nonfinal',
                        'priority': 2,
                    }
                )

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
        if accentuation_type == 'geminate_coda':
            return syl.geminate_coda()
        if accentuation_type == 'geminate_onset':
            return syl.geminate_onset()
        return False