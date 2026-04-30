#!/usr/bin/env python3
"""
Akkadian Prosody Toolkit — Metrics Calculator (Facade)

This module is a thin facade that imports and re-exports from submodules.
Public API: import from akkapros.lib.metrics as before.
"""

# Import and re-export from submodules
from akkapros import __version__

from akkapros.lib._metrics_stats import (
    PunctuationConfigError,
    SYLLABLE_TYPES,
    DISPLAY_SYLLABLE_TYPES,
    SYLLABLE_MORA_TOTAL,
    SYLLABLE_VOWEL_MORA_TOTAL,
    UNCLASSIFIED_SYLLABLE_TYPE,
    update_character_sets,
    is_vowel,
    is_vowel_processing,
    is_consonant,
    is_consonant_processing,
    is_akkadian,
    build_word_pattern,
    tokenize_line,
    process_word,
    extract_words,
    count_merged_units,
    classify_syllable,
    compute_percent_v_from_stats,
    compute_percent_v_with_pauses,
    analyze_text,
    compute_accentuation_stats,
    extract_segments,
    vowel_length,
    compute_consonant_distances,
    std_dev,
    compute_acoustic_metrics,
    preprocess_text,
    compute_speech_metrics_from_rows,
    compute_interval_metrics,
    count_spaces_and_punctuation,
    compute_pause_metrics,
    process_file,
    build_prominence_statistics,
    process_filetext,
    process_phone_pair,
    configure_pause_punctuation_rules,
    _compile_pause_patterns,
    _vowel_morae_in_syllable,
    _population_std_dev,
    _mean,
    _rpvi,
    _npvi,
    _phone_row_duration_ms,
    _normalize_interval_class,
    _coalesce_intervals,
    _extract_unit_drift_summary,
    _extract_phonetizer_diagnostics,
    _count_explicit_word_links_from_rows,
    _count_pause_rows,
    _load_phone_rows,
    _resolve_original_phone_path,
    _prominence_counts_from_phone_rows,
    _gap_has_long_pause,
    _gap_has_short_pause,
    _unknown_gap_punctuation_chars,
    _gap_has_any_punctuation,
    _iter_pause_punctuation_tokens,
    _normalize_pause_punctuation_token,
    _classify_pause_punctuation_token,
    ACTIVE_SHORT_PAUSE_PUNCTUATION_CHARS,
    ACTIVE_LONG_PAUSE_PUNCTUATION_CHARS,
    ACTIVE_SHORT_PAUSE_PUNCTUATION_PATTERNS,
    ACTIVE_LONG_PAUSE_PUNCTUATION_PATTERNS,
    ACTIVE_SHORT_PAUSE_PUNCT_REGEX,
    ACTIVE_LONG_PAUSE_PUNCT_REGEX,
    ALL_VOWELS,
    ALL_CONSONANTS,
    ALL_AKKADIAN,
    FOREIGN_VOWELS,
    FOREIGN_CONSONANTS,
    EXTRA_VOWELS,
    EXTRA_CONSONANTS,
    PROCESSING_VOWELS,
    EXTRA_LONG_VOWELS,
    LENGTH_MARKER,
    WORD_BOUNDARY,
    LOGGER,
)

from akkapros.lib._metrics_output import (
    format_table,
)

# Re-export frontmatter symbols that were previously imported directly
from akkapros.lib.frontmatter import (
    compose_text_document,
    count_function_words,
    read_text_file,
    with_inherited_punctuation_options,
)

# Re-export phonetize symbols that were previously imported directly
from akkapros.lib.phonetize import (
    build_phone_rows,
    build_default_phonetize_config,
    parse_phone_row,
    realize_phone_streams,
    reconstruct_tilde_from_phone_rows,
    serialize_phone_rows,
)

# Re-export utils symbols that were previously imported directly
from akkapros.lib.utils import (
    compile_contextual_regex,
    format_path_for_logging,
    get_logger_with_fallback,
)


def _run_tests():
    from akkapros.lib.tests.metrics_tests import run_tests
    return run_tests
