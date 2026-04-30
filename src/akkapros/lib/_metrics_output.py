from pathlib import Path
from typing import Dict

from akkapros.lib._metrics_stats import DISPLAY_SYLLABLE_TYPES
from akkapros.lib.utils import format_path_for_logging


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
    
    lines.append(f"\nSpeech metrics:")
    lines.append(f"  Total duration: {orig['speech']['total_duration_ms']} ms")
    lines.append(f"  Total pause duration: {orig['speech']['pause_duration_ms']} ms")
    lines.append(f"  Total articulate duration: {orig['speech']['articulation_duration_ms']} ms")
    lines.append(f"  Pause ratio: {orig['speech']['pause_ratio']:.2f}%")
    lines.append(f"  WPM: {orig['speech']['wpm']:.2f} word/minute")

    # Acoustic metrics (original)
    lines.append(f"\nAcoustic metrics (original):")
    lines.append(f"  %C: {orig['acoustic']['percent_c']:.2f}%")
    lines.append(f"  %V: {orig['acoustic']['percent_v']:.2f}%")
    lines.append(f"  meanC: {orig['acoustic']['mean_c_ms']:.2f} ms")
    lines.append(f"  meanV: {orig['acoustic']['mean_v_ms']:.2f} ms")
    lines.append(f"  ΔC: {orig['acoustic']['delta_c_ms']:.2f} ms")
    lines.append(f"  ΔV: {orig['acoustic']['delta_v_ms']:.2f} ms")
    lines.append(f"  VarcoC: {orig['acoustic']['varco_c']:.2f}")
    lines.append(f"  VarcoV: {orig['acoustic']['varco_v']:.2f}")
    lines.append(f"  rPVI-C: {orig['acoustic']['rpvi_c']:.2f}")
    lines.append(f"  nPVI-V: {orig['acoustic']['npvi_v']:.2f}")
    lines.append(f"  Unit drift max: {orig['unit_drift']['max']:.2f} ms")
    lines.append(f"  Unit drift mean: {orig['unit_drift']['mean']:.2f} ms")
    lines.append(f"  Unit drift stddev: {orig['unit_drift']['stddev']:.2f} ms")
    diagnostics = orig.get('phonetizer_diagnostics') or {}
    if diagnostics:
        lines.append(f"\nPhonetizer diagnostics:")
        if 'duration_scale' in diagnostics:
            lines.append(f"  Duration scale: {float(diagnostics['duration_scale']):.6g}")
        lines.append(
            f"  Total units: {diagnostics['total_unit_count']} = "
            f"{diagnostics['syllable_count']} syllables + {diagnostics['pause_count']} pauses + {diagnostics['resync_pause_count']} resync pauses"
        )
        lines.append(
            f"  Unit drift extension: {diagnostics['unit_drift_extension_count']} / "
            f"{diagnostics['syllable_count']} = {float(diagnostics['unit_drift_extension_rate']) * 100:.2f}%"
        )
        if 'non_accented_long_vowel_count' in diagnostics:
            lines.append(f"  Non-accented long vowels: {diagnostics['non_accented_long_vowel_count']}")
            lines.append(
                f"  Left-as-is non-accented long vowels: {diagnostics['left_as_is_non_accented_long_vowel_count']}"
            )
            lines.append(
                f"  Drift tolerance effect: {float(diagnostics['drift_tolerance_effect']) * 100:.2f}%"
            )
        lines.append(
            f"  Inserted resync pauses: {diagnostics['inserted_resync_pause_count']} / "
            f"{diagnostics['eligible_resync_pause_count']} = {float(diagnostics['resync_pause_insertion_rate']) * 100:.2f}%"
        )
        lines.append(
            f"  Pauses with residual drift: {diagnostics['pause_with_residual_drift_count']} / "
            f"{diagnostics['pause_count']} = {float(diagnostics['pause_with_residual_drift_rate']) * 100:.2f}%"
        )
    
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
    
    lines.append(f"\nSpeech metrics:")
    lines.append(f"  Total duration: {rep['speech']['total_duration_ms']} ms")
    lines.append(f"  Total pause duration: {rep['speech']['pause_duration_ms']} ms")
    lines.append(f"  Total articulate duration: {rep['speech']['articulation_duration_ms']} ms")
    lines.append(f"  Pause ratio: {rep['speech']['pause_ratio']:.2f}%")
    lines.append(f"  WPM: {rep['speech']['wpm']:.2f} word/minute")

    # Acoustic metrics (accentuated)
    lines.append(f"\nAcoustic metrics (accentuated):")
    lines.append(f"  %C: {rep['acoustic']['percent_c']:.2f}%")
    lines.append(f"  %V: {rep['acoustic']['percent_v']:.2f}%")
    lines.append(f"  meanC: {rep['acoustic']['mean_c_ms']:.2f} ms")
    lines.append(f"  meanV: {rep['acoustic']['mean_v_ms']:.2f} ms")
    lines.append(f"  ΔC: {rep['acoustic']['delta_c_ms']:.2f} ms")
    lines.append(f"  ΔV: {rep['acoustic']['delta_v_ms']:.2f} ms")
    lines.append(f"  VarcoC: {rep['acoustic']['varco_c']:.2f}")
    lines.append(f"  VarcoV: {rep['acoustic']['varco_v']:.2f}")
    lines.append(f"  rPVI-C: {rep['acoustic']['rpvi_c']:.2f}")
    lines.append(f"  nPVI-V: {rep['acoustic']['npvi_v']:.2f}")
    lines.append(f"  Unit drift max: {rep['unit_drift']['max']:.2f} ms")
    lines.append(f"  Unit drift mean: {rep['unit_drift']['mean']:.2f} ms")
    lines.append(f"  Unit drift stddev: {rep['unit_drift']['stddev']:.2f} ms")
    diagnostics = rep.get('phonetizer_diagnostics') or {}
    if diagnostics:
        lines.append(f"\nPhonetizer diagnostics:")
        if 'duration_scale' in diagnostics:
            lines.append(f"  Duration scale: {float(diagnostics['duration_scale']):.6g}")
        lines.append(
            f"  Total units: {diagnostics['total_unit_count']} = "
            f"{diagnostics['syllable_count']} syllables + {diagnostics['pause_count']} pauses + {diagnostics['resync_pause_count']} resync pauses"
        )
        lines.append(
            f"  Unit drift extension: {diagnostics['unit_drift_extension_count']} / "
            f"{diagnostics['syllable_count']} = {float(diagnostics['unit_drift_extension_rate']) * 100:.2f}%"
        )
        if 'non_accented_long_vowel_count' in diagnostics:
            lines.append(f"  Non-accented long vowels: {diagnostics['non_accented_long_vowel_count']}")
            lines.append(
                f"  Left-as-is non-accented long vowels: {diagnostics['left_as_is_non_accented_long_vowel_count']}"
            )
            lines.append(
                f"  Drift tolerance effect: {float(diagnostics['drift_tolerance_effect']) * 100:.2f}%"
            )
        lines.append(
            f"  Inserted resync pauses: {diagnostics['inserted_resync_pause_count']} / "
            f"{diagnostics['eligible_resync_pause_count']} = {float(diagnostics['resync_pause_insertion_rate']) * 100:.2f}%"
        )
        lines.append(
            f"  Pauses with residual drift: {diagnostics['pause_with_residual_drift_count']} / "
            f"{diagnostics['pause_count']} = {float(diagnostics['pause_with_residual_drift_rate']) * 100:.2f}%"
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
