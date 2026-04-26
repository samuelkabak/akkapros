#!/usr/bin/env python3
"""
Akkadian Diphone Recording Script Generator
Generates minimal set of words for MBROLATOR voice building
"""


import logging
import argparse
import random
import sys
from pathlib import Path

from akkapros.lib.utils import (
    add_standard_logging_arguments,
    add_standard_version_argument,
    format_selftest_label,
    format_path_for_logging,
    get_logger_with_fallback,
    log_selftest_result,
    log_selftest_summary,
    log_startup_banner,
    setup_cli_logging,
)

from akkapros.lib._phoneprep_phonology import (
    ALL_CONSONANTS,
    ALL_VOWELS,
    BOUNDARY,
    COLORED_VOWELS_LONG,
    COLORED_VOWELS_SHORT,
    DEFAULT_MAX_WORDS_PER_RECORDING,
    EMPHATIC_CONSONANTS,
    IPA_CONSONANT_MAP,
    IPA_VOWEL_MAP,
    LONG_TO_SHORT,
    MBROLA_CONSONANT_MAP,
    MBROLA_VOWEL_MAP,
    PHONEPREP_COLORED_PREDECESSOR_EXCLUSIONS,
    PLAIN_CONSONANTS,
    PLAIN_VOWELS_LONG,
    PLAIN_VOWELS_SHORT,
    ALL_PLAIN_VOWELS,
    ALL_COLORED_VOWELS,
    CoverageOptimizer,
    compute_reachable_diphone_inventory,
    consonants_for_pattern,
    extract_diphones_pattern1,
    extract_diphones_pattern2,
    extract_diphones_pattern3,
    generate_all_pattern1_words,
    generate_all_pattern2_words,
    generate_all_pattern3_words,
    is_consonant_emphatic,
    is_consonant_plain,
    is_vowel_colored,
    is_vowel_plain,
    is_vowel_valid,
    is_vv_class_legal,
    is_vv_diphone,
    map_diphones_symbols,
    map_word_symbols,
    normalize_long_vowels_to_short,
    parse_symbol_list,
    random_valid_word,
    set_active_inventory,
    to_ipa_symbol,
    to_mbrola_symbol,
    unique_preserve_order,
    unique_preserve_pairs,
    validate_pattern1,
    validate_pattern2,
    validate_pattern3,
    vowel_pool_for_context,
)

from akkapros.lib._phoneprep_io import (
    build_manifest_rows,
    extract_recording_words,
    format_word,
    generate_script,
    inventory_as_ipa,
    ipa_to_mbrola_mapping_list,
    validate_word_list,
    word_diphones,
    write_alignment_sidecars,
    write_recording_helper_html,
    write_script,
    write_script_batched,
)

LOGGER = logging.getLogger(__name__)

# ============================================
# PHONEME INVENTORY (mutable state)
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
DEFAULT_MAX_WORDS_PER_RECORDING = 1000
PHONEPREP_COLORED_PREDECESSOR_EXCLUSIONS = {'t', 'd', 'k'}

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


def set_active_inventory(
    plain_consonants,
    emphatic_consonants,
    plain_vowels_short,
    plain_vowels_long,
    colored_vowels_short,
    colored_vowels_long,
):
    """Replace module-level inventory lists for runtime debug/experiments."""
    global PLAIN_CONSONANTS, EMPHATIC_CONSONANTS, ALL_CONSONANTS
    global PLAIN_VOWELS_SHORT, PLAIN_VOWELS_LONG, ALL_PLAIN_VOWELS
    global COLORED_VOWELS_SHORT, COLORED_VOWELS_LONG, ALL_COLORED_VOWELS, ALL_VOWELS

    PLAIN_CONSONANTS = plain_consonants
    EMPHATIC_CONSONANTS = emphatic_consonants
    ALL_CONSONANTS = PLAIN_CONSONANTS + EMPHATIC_CONSONANTS

    PLAIN_VOWELS_SHORT = normalize_long_vowels_to_short(plain_vowels_short, plain_vowels_long)
    PLAIN_VOWELS_LONG = []
    ALL_PLAIN_VOWELS = PLAIN_VOWELS_SHORT

    COLORED_VOWELS_SHORT = normalize_long_vowels_to_short(colored_vowels_short, colored_vowels_long)
    COLORED_VOWELS_LONG = []
    ALL_COLORED_VOWELS = COLORED_VOWELS_SHORT

    ALL_VOWELS = ALL_PLAIN_VOWELS + ALL_COLORED_VOWELS

    # Sync the submodule's namespace so phonology functions see the updated values.
    import akkapros.lib._phoneprep_phonology as _phonology
    _phonology.PLAIN_CONSONANTS = PLAIN_CONSONANTS
    _phonology.EMPHATIC_CONSONANTS = EMPHATIC_CONSONANTS
    _phonology.ALL_CONSONANTS = ALL_CONSONANTS
    _phonology.PLAIN_VOWELS_SHORT = PLAIN_VOWELS_SHORT
    _phonology.PLAIN_VOWELS_LONG = PLAIN_VOWELS_LONG
    _phonology.ALL_PLAIN_VOWELS = ALL_PLAIN_VOWELS
    _phonology.COLORED_VOWELS_SHORT = COLORED_VOWELS_SHORT
    _phonology.COLORED_VOWELS_LONG = COLORED_VOWELS_LONG
    _phonology.ALL_COLORED_VOWELS = ALL_COLORED_VOWELS
    _phonology.ALL_VOWELS = ALL_VOWELS



def main():
    parser = argparse.ArgumentParser(description="Generate Akkadian diphone recording script")
    add_standard_version_argument(parser, 'akkapros-phoneprep')
    add_standard_logging_arguments(parser)
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
    parser.add_argument("--with-html-recording-helper", action="store_true",
                       help="Write an interactive HTML page for chunked recording and timestamp logging")
    parser.add_argument("--recording-max-words", type=int, default=DEFAULT_MAX_WORDS_PER_RECORDING,
                       help="Max accepted words per recording chunk in helper HTML (default: 1000)")
    parser.add_argument("--output", "-o", type=str, default="outputs/akkadian_script.txt",
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
    parser.add_argument("--test", action="store_true", help="Run unit tests")
    
    args = parser.parse_args()

    if args.test:
        logger = setup_cli_logging(args, 'akkapros.lib.phoneprep')
        log_startup_banner(logger, 'akkapros-phoneprep', 'library-main', args)
        from akkapros.lib.tests.phoneprep_tests import run_tests
        sys.exit(0 if run_tests() else 1)

    logger = setup_cli_logging(args, 'akkapros.lib.phoneprep')
    log_startup_banner(logger, 'akkapros-phoneprep', 'library-main', args)

    if not 0.0 < args.non_vv_target_ratio <= 1.0:
        logger.error('--non-vv-target-ratio must be in (0, 1]')
        sys.exit(2)
    if args.candidate_pool_size <= 0:
        logger.error('--candidate-pool-size must be >= 1')
        sys.exit(2)
    if args.recording_max_words <= 0:
        logger.error('--recording-max-words must be >= 1')
        sys.exit(2)

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
    
    logger.info('Akkadian Diphone Script Generator')
    logger.info('=================================')
    logger.info('Target coverage: %s', args.coverage)
    if args.max_non_vv is not None:
        if args.strict_max_non_vv:
            logger.info('Non-VV strict max occurrences: %s (V-V unlimited)', args.max_non_vv)
        else:
            logger.info(
                'Non-VV soft target: %s, required ratio: %s (V-V unlimited)',
                args.max_non_vv,
                f'{args.non_vv_target_ratio:.0%}',
            )
    logger.info('Output file: %s', format_path_for_logging(args.output))
    logger.info('Plain consonants (IPA): %s', ', '.join(inventory_as_ipa(PLAIN_CONSONANTS)))
    logger.info('Emphatic consonants (IPA): %s', ', '.join(inventory_as_ipa(EMPHATIC_CONSONANTS)))
    logger.info(
        'Plain vowels short/long (IPA): %s / %s',
        ', '.join(inventory_as_ipa(PLAIN_VOWELS_SHORT)),
        ', '.join(inventory_as_ipa(PLAIN_VOWELS_LONG)),
    )
    logger.info(
        'Colored vowels short/long (IPA): %s / %s',
        ', '.join(inventory_as_ipa(COLORED_VOWELS_SHORT)),
        ', '.join(inventory_as_ipa(COLORED_VOWELS_LONG)),
    )
    mapping_pairs = ipa_to_mbrola_mapping_list()
    mapping_text = ', '.join([f"{ipa}->{mb}" for ipa, mb in mapping_pairs])
    logger.info('Mbrola X-SAMPA mapping: [%s]', mapping_text)

    if args.two_batch_emphatic:
        base_plain_consonants = list(PLAIN_CONSONANTS)
        base_emphatic_consonants = list(EMPHATIC_CONSONANTS)
        base_plain_vowels_short = list(PLAIN_VOWELS_SHORT)
        base_plain_vowels_long = list(PLAIN_VOWELS_LONG)
        base_colored_vowels_short = list(COLORED_VOWELS_SHORT)
        base_colored_vowels_long = list(COLORED_VOWELS_LONG)

        # Batch 1: no emphatics, no colored vowels.
        set_active_inventory(
            plain_consonants=base_plain_consonants,
            emphatic_consonants=[],
            plain_vowels_short=base_plain_vowels_short,
            plain_vowels_long=base_plain_vowels_long,
            colored_vowels_short=[],
            colored_vowels_long=[],
        )
        logger.info('[BATCH 1] Plain-only inventory')
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
            logger.warning('Batch 1 validation found %d issue(s). First:', len(batch1_issues))
            logger.warning('  %s', batch1_issues[0])

        # Batch 2: mixed plain/colored vowels + mixed consonants (no alternation filter).
        set_active_inventory(
            plain_consonants=base_plain_consonants,
            emphatic_consonants=base_emphatic_consonants,
            plain_vowels_short=base_plain_vowels_short,
            plain_vowels_long=base_plain_vowels_long,
            colored_vowels_short=base_colored_vowels_short,
            colored_vowels_long=base_colored_vowels_long,
        )
        logger.info('[BATCH 2] Mixed consonants + mixed vowels (post-emphatic legality)')
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
            logger.warning('Batch 2 validation found %d issue(s). First:', len(batch2_issues))
            logger.warning('  %s', batch2_issues[0])

        # Restore active inventory for any later operations.
        set_active_inventory(
            plain_consonants=base_plain_consonants,
            emphatic_consonants=base_emphatic_consonants,
            plain_vowels_short=base_plain_vowels_short,
            plain_vowels_long=base_plain_vowels_long,
            colored_vowels_short=base_colored_vowels_short,
            colored_vowels_long=base_colored_vowels_long,
        )

        logger.info('%s', '=' * 50)
        logger.info('BATCHED COVERAGE SUMMARY')
        logger.info('%s', '=' * 50)
        logger.info('Batch 1 words: %d | target-hit ratio: %.2f%%', len(batch1_words), batch1_stats['ratio'] * 100)
        logger.info('Batch 2 words: %d | target-hit ratio: %.2f%%', len(batch2_words), batch2_stats['ratio'] * 100)
        logger.info('Total words: %d', len(batch1_words) + len(batch2_words))

        write_script_batched(batch1_words, batch2_words, args.output, args.coverage)
        logger.info('Script written to %s', format_path_for_logging(args.output))

        if not args.no_sidecars:
            batch1_rows = build_manifest_rows(batch1_words, batch='batch1', start_utterance_id=1)
            batch2_rows = build_manifest_rows(
                batch2_words,
                batch='batch2',
                start_utterance_id=len(batch1_rows) + 1,
            )
            write_alignment_sidecars(args.output, batch1_rows + batch2_rows)
        if args.with_html_recording_helper:
            write_recording_helper_html(
                output_script_path=args.output,
                prefix=Path(args.output).stem,
                max_words_per_recording=args.recording_max_words,
            )
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
        logger.warning('Validation found %d issue(s). First:', len(issues))
        logger.warning('  %s', issues[0])
    
    logger.info('%s', '=' * 50)
    logger.info('COVERAGE SUMMARY')
    logger.info('%s', '=' * 50)
    logger.info('Required diphones: %s', stats['total'])
    logger.info('Fully covered: %s', stats['complete'])
    logger.info('Below target: %s', stats['below'])
    logger.info('Coverage range: %s - %s', stats['min'], stats['max'])
    logger.info('Average coverage: %.2f', stats['avg'])
    logger.info('Target-hit ratio: %.2f%%', stats['ratio'] * 100)
    logger.info('V-V diphones tracked: %s (avg coverage %.2f)', stats['vv_total'], stats['vv_avg'])
    logger.info('Words generated: %d', len(words))
    
    write_script(words, args.output, args.coverage)
    logger.info('Script written to %s', format_path_for_logging(args.output))

    if not args.no_sidecars:
        rows = build_manifest_rows(words, batch='single', start_utterance_id=1)
        write_alignment_sidecars(args.output, rows)
    if args.with_html_recording_helper:
        write_recording_helper_html(
            output_script_path=args.output,
            prefix=Path(args.output).stem,
            max_words_per_recording=args.recording_max_words,
        )



if __name__ == '__main__':
    main()