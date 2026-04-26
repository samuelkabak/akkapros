"""
File I/O, script generation, and recording helpers for the Akkadian Diphone
Recording Script Generator.

Extracted from phoneprep.py during CR-092 split. All functions here handle
output formatting, file writing, manifest building, and recording support.
"""

import csv
import json
import logging
from pathlib import Path
import random
from typing import Callable, Dict, List, Optional, Set, Tuple

from akkapros.lib._phoneprep_html_template import PHONEPREP_HTML_TEMPLATE
from akkapros.lib.utils import format_path_for_logging
from akkapros.lib._phoneprep_phonology import (
    ALL_CONSONANTS,
    ALL_VOWELS,
    BOUNDARY,
    CoverageOptimizer,
    compute_reachable_diphone_inventory,
    extract_diphones_pattern1,
    extract_diphones_pattern2,
    extract_diphones_pattern3,
    is_consonant_emphatic,
    is_consonant_plain,
    is_plain_emphatic_alternating,
    is_vowel_plain,
    is_vowel_colored,
    is_vv_class_legal,
    is_vv_diphone,
    is_vowel_valid,
    map_diphones_symbols,
    map_word_symbols,
    random_valid_word,
    to_ipa_symbol,
    to_mbrola_symbol,
    unique_preserve_pairs,
    validate_pattern1,
    validate_pattern2,
    validate_pattern3,
)

LOGGER = logging.getLogger(__name__)


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
    LOGGER.info('Building reachable diphone inventory once...')
    reachable_diphones = compute_reachable_diphone_inventory()
    LOGGER.info('Reachable diphone inventory size: %d', len(reachable_diphones))

    # Initialize optimizer
    optimizer = CoverageOptimizer(
        target_coverage,
        possible_diphones=reachable_diphones,
        max_non_vv_occurrences=max_non_vv_occurrences,
        non_vv_target_ratio=non_vv_target_ratio,
        strict_non_vv_cap=strict_non_vv_cap,
    )

    LOGGER.info('Building minimal set with target coverage = %s...', target_coverage)
    if max_non_vv_occurrences is not None:
        if strict_non_vv_cap:
            LOGGER.info(
                'Applying STRICT non-VV max occurrences cap: %s (V-V unlimited)',
                max_non_vv_occurrences,
            )
        else:
            LOGGER.info(
                'Applying SOFT non-VV target around %s with completion ratio >= %s (V-V unlimited)',
                max_non_vv_occurrences,
                f'{non_vv_target_ratio:.0%}',
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

    LOGGER.info('Sampled candidates: %d', sampled)
    LOGGER.info('Candidate pool size per selection round: %d', candidate_pool_size)
    LOGGER.info('Accepted words: %d', accepted)
    LOGGER.info(
        'Accepted by pattern: P1=%d, P2=%d, P3=%d',
        pattern_counts[1],
        pattern_counts[2],
        pattern_counts[3],
    )

    if not optimizer.is_complete():
        LOGGER.warning(
            'Reached max iterations before completion target. Increase --max-iterations or relax constraints.'
        )

    return optimizer.selected_words, optimizer.coverage_summary()


# ============================================
# OUTPUT FORMATTING
# ============================================

def format_word(word: List[str], pattern: int) -> str:
    """Format a word as IPA with dotted syllable boundaries for easier reading."""
    ipa_word = map_word_symbols(word, to_ipa_symbol)

    # Make hiatus explicit for adjacent vowels (aa, uu, etc.) in display script.
    def _with_hiatus(vv: str) -> str:
        if len(vv) == 2 and vv[0] in ALL_VOWELS and vv[1] in ALL_VOWELS:
            return f"{vv[0]}.{vv[1]}"
        return vv

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
            ipa_word[0] + _with_hiatus(''.join(ipa_word[1:3])),
            ipa_word[3] + _with_hiatus(''.join(ipa_word[4:6])) + ipa_word[6],
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

    LOGGER.info('Manifest written to %s', format_path_for_logging(manifest_path))
    LOGGER.info('Diphone cursor file written to %s', format_path_for_logging(diphones_path))
    LOGGER.info('Word list (one per line) written to %s', format_path_for_logging(words_path))


def extract_recording_words(script_path: Path) -> List[str]:
    """Extract utterance lines from generated script file for the recorder helper."""
    words: List[str] = []
    for raw in script_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('_') and line.endswith('_'):
            words.append(line)
    return words


def write_recording_helper_html(
    output_script_path: str,
    prefix: str,
    max_words_per_recording: int,
) -> Path:
    """Write an interactive HTML page to guide chunked recording and timestamp logging."""
    script_path = Path(output_script_path)
    words = extract_recording_words(script_path)
    helper_path = script_path.with_name(f"{script_path.stem}_recording_helper.html")
    segmanifest_name = f"{prefix}_segmanifest.txt"

    # Use a plain (non-f) string with placeholders to avoid f-string brace-escaping issues
    html = PHONEPREP_HTML_TEMPLATE
    # Fill placeholders with proper JSON/string encodings
    html = html.replace('%%WORDS%%', json.dumps(words, ensure_ascii=False))
    html = html.replace('%%MAX_WORDS_PER_RECORDING%%', str(int(max_words_per_recording)))
    html = html.replace('%%PREFIX_JSON%%', json.dumps(prefix))
    html = html.replace('%%SEGMANIFEST_JSON%%', json.dumps(segmanifest_name))
    # Raw values for visible text (not JSON-quoted)
    html = html.replace('%%PREFIX_RAW%%', prefix)
    html = html.replace('%%SEGMANIFEST_RAW%%', segmanifest_name)
    helper_path.write_text(html, encoding='utf-8')
    LOGGER.info('Recording helper HTML written to %s', format_path_for_logging(helper_path))
    return helper_path


def write_script(words_with_patterns: List[Tuple[List[str], int]],
                 filename: str,
                 coverage: int):
    """Write the script to a file."""
    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Group by pattern
    pattern1_words = [(w, p) for w, p in words_with_patterns if p == 1]
    pattern2_words = [(w, p) for w, p in words_with_patterns if p == 2]
    pattern3_words = [(w, p) for w, p in words_with_patterns if p == 3]

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("# ============================================\n")
        f.write("# AKKADIAN DIPHONE RECORDING SCRIPT\n")
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
    out_path = Path(filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)

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

    with open(out_path, 'w', encoding='utf-8') as f:
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
