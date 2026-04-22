from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple, Union

from akkapros.lib._prosody_text import assemble_line, parse_syl_line, postprocess_restore_diphthongs
from akkapros.lib._prosody_types import AccentStyle, MoraMode
from akkapros.lib.constants import INTERNAL_WORD_LINKER, MERGE_LINKERS, WORD_LINKER
from akkapros.lib.frontmatter import (
    build_output_frontmatter,
    build_prosody_stage_data,
    compose_text_document,
    count_lines,
    count_prosodic_units,
    read_text_file,
    resolve_file_title,
)
from akkapros.lib.prosody_model import C, MergedUnit, Syllable, Word
from akkapros.lib.utils import format_path_for_logging


LOGGER = logging.getLogger(__name__)


class ProsodyEngine:
    def __init__(
        self,
        style: AccentStyle = AccentStyle.SOB,
        only_last: bool = True,
        mora_mode: MoraMode = MoraMode.BI,
    ):
        self.style = style
        self.only_last = only_last
        self.mora_mode = mora_mode
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
                'geminate_glottal': 0,
            },
        }

    def _can_emit_without_accentuation(self, unit: Union[Word, MergedUnit]) -> bool:
        return self.mora_mode == MoraMode.BI and not unit.should_attempt_accentuation(self.mora_mode)

    def _update_last_resort_stats(self, syllable: Syllable):
        self.stats['last_resort'] += 1
        self.stats['accentuated_syllables'] += 1
        if syllable.text[0] in C:
            self.stats['accentuation_types']['geminate_onset'] += 1
        else:
            self.stats['accentuation_types']['geminate_glottal'] += 1

    def rollback_accentuation(self, word: Word) -> None:
        for syllable in word.syllables:
            syllable.is_accentuated = False
            syllable.accentuation_type = None
            syllable.accentuated_morae = syllable.morae
            syllable.accentuated_text = syllable.text

    def rollback_accentuation_stats(self, word: Word) -> None:
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
            return ''

        result_parts = []
        i = 0
        n = len(tokens)

        while i < n:
            token = tokens[i]
            if token == WORD_LINKER:
                i += 1
                continue

            if isinstance(token, str):
                result_parts.append(token)
                i += 1
                continue

            word = token
            forced_group = [word]
            j = i
            while j + 2 < n and tokens[j + 1] == WORD_LINKER and not isinstance(tokens[j + 2], str):
                forced_group.append(tokens[j + 2])
                j += 2

            if len(forced_group) > 1:
                explicit_tail_start = (len(forced_group) - 1) if self.only_last else 0

                def append_group(words_group: List[Word]) -> None:
                    for k, linked_word in enumerate(words_group):
                        result_parts.append(linked_word.get_text())
                        if k < len(words_group) - 1:
                            linker = WORD_LINKER if k < len(forced_group) - 1 else INTERNAL_WORD_LINKER
                            result_parts.append(linker)

                def resolve_group(words_group: List[Word]) -> Tuple[bool, bool]:
                    unit = MergedUnit(words_group, locked_prefix_words=explicit_tail_start)
                    if self._can_emit_without_accentuation(unit):
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

                if self.mora_mode == MoraMode.MONO:
                    last_word = merged_group[-1]
                    if last_word.syllables and last_word.syllables[0].last_resort_accentuation():
                        self._update_last_resort_stats(last_word.syllables[0])
                    append_group(merged_group)
                    i = j + 1
                    continue

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
                func_group = [word]
                j = i + 1
                while j < n and not isinstance(tokens[j], str) and tokens[j].is_function_word:
                    func_group.append(tokens[j])
                    j += 1

                has_content = j < n and not isinstance(tokens[j], str) and not tokens[j].is_function_word

                if has_content:
                    content_word = tokens[j]
                    func_group.append(content_word)
                    j += 1

                    unit = MergedUnit(func_group, locked_prefix_words=len(func_group) - 1)
                    if not self._can_emit_without_accentuation(unit):
                        accentuation = unit.get_best_accentuation(self.style)
                        if accentuation:
                            unit.apply_accentuation(accentuation)
                            self.stats['words_accentuated'] += 1
                            self.stats['accentuated_syllables'] += 1
                            self.stats['accentuation_types'][accentuation['type']] += 1
                        elif content_word.syllables and content_word.syllables[0].last_resort_accentuation():
                            self._update_last_resort_stats(content_word.syllables[0])

                    for k, grouped_word in enumerate(func_group):
                        result_parts.append(grouped_word.get_text())
                        if k < len(func_group) - 1:
                            result_parts.append(INTERNAL_WORD_LINKER)

                    i = j
                    continue

                at_end_or_punct = j >= n or isinstance(tokens[j], str)
                if at_end_or_punct and i > 0:
                    for idx in range(len(result_parts) - 1, -1, -1):
                        part = result_parts[idx]
                        if isinstance(part, str) and not part.endswith(tuple(MERGE_LINKERS)) and not part.startswith(tuple(MERGE_LINKERS)):
                            matched_prev_word: Union[Word, None] = None
                            for word_idx in range(i - 1, -1, -1):
                                prev_token = tokens[word_idx]
                                if not isinstance(prev_token, str) and not prev_token.is_function_word:
                                    if prev_token.get_text() in part or prev_token.get_text_flat() in part:
                                        self.rollback_accentuation_stats(prev_token)
                                        self.rollback_accentuation(prev_token)
                                        matched_prev_word = prev_token
                                        break

                            result_parts = result_parts[:idx]
                            base_part = matched_prev_word.get_text() if matched_prev_word else part
                            result_parts.append(base_part + INTERNAL_WORD_LINKER)
                            for grouped_word in func_group:
                                result_parts.append(grouped_word.get_text())
                                result_parts.append(INTERNAL_WORD_LINKER)
                            result_parts.pop()
                            break
                    else:
                        for grouped_word in func_group:
                            result_parts.append(grouped_word.get_text())
                            result_parts.append(INTERNAL_WORD_LINKER)
                        result_parts.pop()

                    i = j
                    continue

                for grouped_word in func_group:
                    result_parts.append(grouped_word.get_text())
                    result_parts.append(INTERNAL_WORD_LINKER)
                result_parts.pop()
                i = j
                continue

            if self._can_emit_without_accentuation(word):
                result_parts.append(word.get_text())
                i += 1
                continue

            accentuation = word.get_best_accentuation(self.style)
            if accentuation:
                word.apply_accentuation(accentuation)
                self.stats['words_accentuated'] += 1
                self.stats['accentuated_syllables'] += 1
                self.stats['accentuation_types'][accentuation['type']] += 1
                result_parts.append(word.get_text())
                i += 1
                continue

            if self.mora_mode == MoraMode.MONO:
                if word.syllables[-1].last_resort_accentuation():
                    self._update_last_resort_stats(word.syllables[-1])
                result_parts.append(word.get_text())
                i += 1
                continue

            merged = [word]
            j = i + 1
            accentuated = False

            while j < n and not accentuated:
                next_token = tokens[j]
                if isinstance(next_token, str):
                    break

                merged.append(next_token)
                unit = MergedUnit(merged)

                if self._can_emit_without_accentuation(unit):
                    for k, grouped_word in enumerate(merged):
                        result_parts.append(grouped_word.get_text())
                        if k < len(merged) - 1:
                            result_parts.append(INTERNAL_WORD_LINKER)
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

                    for k, grouped_word in enumerate(merged):
                        result_parts.append(grouped_word.get_text())
                        if k < len(merged) - 1:
                            result_parts.append(INTERNAL_WORD_LINKER)
                    i = j + 1
                    accentuated = True
                    self.stats['merged_forward'] += 1
                    break

                j += 1

            if accentuated:
                continue

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
        LOGGER.info('Mora mode: %s', self.mora_mode.value)
        LOGGER.info('Explicit + mode: %s', 'only-last' if self.only_last else 'allow-propagation')
        LOGGER.info('Diphthong restore: always')

        input_frontmatter, text = read_text_file(input_file)
        lines = text.splitlines(keepends=True)

        output_lines = []
        for line in lines:
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
        with open(output_file, 'w', encoding='utf-8') as handle:
            handle.write(compose_text_document(frontmatter, output_body))
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