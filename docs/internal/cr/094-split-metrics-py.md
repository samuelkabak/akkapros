---
cr_id: CR-094
status: Done
priority: Medium
impact: Mutative
created: 2026-04-29
updated: 2026-04-29
implements: 'CR-087'
supersedes: 'CR-091 (partial — metrics split only)'
---

# Change Request: Split `metrics.py` into `_metrics_stats.py` + `_metrics_output.py`

## Summary

Split `metrics.py` (~1780 lines, 78 functions) into two focused submodules following the move-only pattern established by CR-087 and CR-092. This reduces per-file token cost for LLM-assisted editing and keeps each file focused on a single responsibility.

This CR covers only the `metrics.py` split that was originally proposed in CR-091 but never implemented. CR-092 handled the other splits (`phoneprep`, `print`, `config`) from CR-091's scope.

---

## Motivation

`metrics.py` is the largest remaining monolithic file in `src/akkapros/lib/` at ~1780 lines with 78 functions and 1 class. It mixes statistics computation, pause analysis, interval metrics, and output formatting in a single file. Splitting it reduces LLM context cost and makes each submodule easier to navigate and maintain.

---

## Scope

### Included

- Split `metrics.py` into `_metrics_stats.py` (statistics computation) + `_metrics_output.py` (output formatting)
- Update `metrics.py` to become a thin facade that imports and re-exports from submodules
- Run full pytest suite to verify no regressions

### Not Included

- Behavioral changes to any function
- API changes to public facades (`akkapros.lib.metrics`)
- Renaming of public symbols
- Splitting any other files (handled by CR-087, CR-092)
- Splitting test files

---

## Current Behavior

All 78 functions and 1 class live in a single `metrics.py` file. Editing any one function requires loading the entire file into LLM context.

---

## Proposed Change

### Split Map

**`_metrics_stats.py`** — statistics computation, aggregation, mora counting, pause calculation:
- `_compile_pause_patterns`, `configure_pause_punctuation_rules`, `update_character_sets`
- `is_vowel`, `is_vowel_processing`, `is_consonant`, `is_consonant_processing`, `is_akkadian`
- `build_word_pattern`, `tokenize_line`, `process_word`, `extract_words`, `count_merged_units`
- `_vowel_morae_in_syllable`, `classify_syllable`
- `compute_percent_v_from_stats`, `compute_percent_v_with_pauses`
- `analyze_text`, `compute_accentuation_stats`, `extract_segments`
- `vowel_length`, `compute_consonant_distances`, `std_dev`, `compute_acoustic_metrics`
- `preprocess_text`, `compute_speech_metrics_from_rows`
- `_population_std_dev`, `_mean`, `_rpvi`, `_npvi`
- `_phone_row_duration_ms`, `_normalize_interval_class`, `_coalesce_intervals`, `compute_interval_metrics`
- `_extract_unit_drift_summary`, `_extract_phonetizer_diagnostics`
- `_count_explicit_word_links_from_rows`, `_count_pause_rows`
- `_load_phone_rows`, `_resolve_original_phone_path`, `_prominence_counts_from_phone_rows`
- `process_phone_pair`
- `_gap_has_long_pause`, `_gap_has_short_pause`, `_unknown_gap_punctuation_chars`, `_gap_has_any_punctuation`
- `_iter_pause_punctuation_tokens`, `_normalize_pause_punctuation_token`, `_classify_pause_punctuation_token`
- `count_spaces_and_punctuation`, `compute_pause_metrics`
- `process_file`, `build_prominence_statistics`, `process_filetext`

**`_metrics_output.py`** — output formatting and reporting:
- `format_table`
- All `_test_*` functions (test helpers stay with the parent facade)
- `run_tests`

The parent `metrics.py` retains: imports, re-exports, `__all__`, and any module-level state.

---

## Technical Design

### Pattern (same as CR-087, CR-092)

1. Create `_metrics_stats.py` and `_metrics_output.py` in `src/akkapros/lib/`.
2. Move the relevant functions into each submodule, keeping imports self-contained.
3. In `metrics.py`, add `from ._metrics_stats import <symbols>` and `from ._metrics_output import <symbols>` at the top.
4. Keep `metrics.py`'s public API surface identical.
5. Do not change function signatures, class names, or behavior.

### Import Strategy

- Submodules import from sibling submodules using relative imports (`from ._metrics_stats import ...`).
- The parent `metrics.py` re-exports all public symbols from submodules.
- External code imports from `akkapros.lib.metrics` only.

---

## Files Likely Affected

```
src/akkapros/lib/metrics.py          → + _metrics_stats.py, _metrics_output.py
```

---

## Acceptance Criteria

- [ ] `metrics.py` public API unchanged: all existing imports from `akkapros.lib.metrics` still work
- [ ] All existing tests pass (`python -m pytest`)
- [ ] No behavioral changes detected in integration test gold outputs
- [ ] Each new submodule is under 1000 lines
- [ ] Each new submodule has a single clear responsibility

---

## Risks / Edge Cases

- **Circular imports**: Submodules may import from each other. Use relative imports and defer imports inside functions if needed.
- **Missed re-exports**: A function used externally but not re-exported from `metrics.py` will break. Audit all imports of `akkapros.lib.metrics` across `src/` and `tests/` before splitting.
- **Module-level state**: Check for module-level variables, singletons, or cached state that submodules might need to share. These must stay in `metrics.py` or be moved to a shared location.

---

## Precautions

### Before Splitting

- **Verify current test baseline**: Run `python -m pytest` and confirm all tests pass before making any changes. Record the pass count.
- **Audit external imports**: Grep all `from akkapros.lib.metrics import` across `src/` and `tests/` to know exactly which symbols are public API. Every symbol imported externally must be re-exported from the parent facade.

### During Splitting

- **Move functions, don't rewrite**: Copy-paste functions verbatim into submodules. Do not refactor, rename, or reformat during the move.
- **Keep self-tests in the parent facade**: Do not move `_test_*` functions or `run_tests` into submodules — they import from the parent and would create circular dependencies.
- **Use relative imports between submodules**: `from ._metrics_stats import ...` not `from akkapros.lib._metrics_stats import ...`.
- **Re-export everything from the parent**: The parent facade must import and re-export every public symbol.

### After Split

- **Run full pytest suite**: `python -m pytest` — all tests must pass.
- **Run library self-tests**: `python -m pytest tests/test_selftests_lib.py -q`.
- **Check gold outputs**: Run integration tests that compare against gold files and confirm no drift.
- **Verify imports from other modules still work**: Run a quick smoke test — import `akkapros.lib.metrics` in Python and check that all expected symbols are accessible.

### If Something Breaks

- **Revert immediately**: Delete the submodule files and restore the original `metrics.py`. The split is a move-only refactor with zero data migration — reverting is safe.
- **Isolate the broken symbol**: Identify which symbol causes the import error or test failure. Check whether it was re-exported from the parent and whether its internal imports are correct.
- **Do not patch behavior**: If a test fails because of a behavioral difference, the split introduced an unintended change. Revert and re-examine the moved code rather than patching the test.

---

## Testing Strategy

- Run full pytest suite before and after the split to confirm zero regressions.
- Run integration tests with gold output comparison to confirm no behavioral drift.
- Run library self-tests (`python -m pytest tests/test_selftests_lib.py -q`).

---

## Rollback Plan

The split is a move-only refactor. Revert by restoring the original `metrics.py` and deleting `_metrics_stats.py` and `_metrics_output.py`. No data migration needed.

---

## Related Issues

- CR-087: Original split of `phonetize.py`, `prosody.py`, `syllabify.py` (establishes the pattern)
- CR-091: Original proposal for this split (now superseded)
- CR-092: Phase 2 splits for `phoneprep`, `print`, `config` (follows same pattern)

---

## Tasks

### Implementation

- [ ] Audit external imports of `akkapros.lib.metrics` across `src/` and `tests/`
- [ ] Create `_metrics_stats.py` with statistics computation functions
- [ ] Create `_metrics_output.py` with output formatting functions
- [ ] Update `metrics.py` to import and re-export from submodules
- [ ] Verify all public symbols are re-exported

### Tests

- [ ] Full pytest suite passes after split
- [ ] Integration gold outputs unchanged
- [ ] Library self-tests pass

### Documentation

- [ ] Update `.github/copilot-instructions.md` if new submodule patterns are established
