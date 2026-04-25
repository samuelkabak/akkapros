---
cr_id: CR-091
status: Done
priority: Medium
impact: Mutative
created: 2026-04-23
updated: 2026-04-25
implements: 'CR-087'
---

# Change Request: Phase 2 Module Splitting for LLM Cost

# Summary

Split the remaining large library modules (>1000 lines, >40 KB) into focused submodules following the move-only pattern established by CR-087. This reduces per-file token cost for LLM-assisted editing and keeps each file focused on a single responsibility.

CR-087 split `phonetize.py`, `prosody.py`, and `syllabify.py`. This CR extends the same treatment to `metrics.py`, `phoneprep.py`, `print.py`, `config.py`, and the two largest test files.

## Implementation Status (as of 2026-04-25)

**None of the splits proposed in this CR have been implemented.** All source files remain monolithic at their original sizes. The `_prosody_types.py` → `_prosody_text.py` consolidation (a CR-087 deviation) is the only related change in the repo, but it is not part of this CR's scope.

All `# Tasks` checkboxes remain unchecked. This CR is ready for implementation.

---

# Motivation

After CR-087, several files remain over 1000 lines with 38–79 functions each. These files are expensive to load into LLM context and hard to navigate. Splitting them reduces token cost and makes each submodule easier to maintain.

Current sizes (verified by code inspection on 2026-04-25):

| File | Lines | KB | Funcs/Classes |
|------|-------|----|---------------|
| `metrics.py` | 1780 | 67 | 78 funcs, 1 class |
| `phoneprep.py` | 1880 | 71 | 44 funcs, 1 class |
| `print.py` | 1701 | 59 | 38 funcs |
| `config.py` | 1066 | 41 | 55 funcs |
| `test_phonetize_lib.py` | 2128 | 74 | — |
| `test_integration.py` | 1792 | 66 | — |

Note: `phonetize.py` was already split by CR-087 and is NOT in scope for this CR.

---

# Scope

## Included

- Split `metrics.py` into `_metrics_stats.py` + `_metrics_output.py`
- Split `phoneprep.py` into `_phoneprep_phonology.py` + `_phoneprep_io.py`
- Split `print.py` into `_print_ipa.py` + `_print_pho.py`
- Split `config.py` → extract `_config_io.py` for I/O concerns
- Split `test_phonetize_lib.py` into domain-focused test files
- Split `test_integration.py` into CLI-focused test files
- Update facade re-exports in all parent modules
- Run full pytest suite to verify no regressions

## Not Included

- Behavioral changes to any function
- API changes to public facades (`akkapros.lib.*`)
- Renaming of public symbols
- Splitting `phonetize.py` (already done in CR-087)
- Splitting files under 500 lines (`utils.py`, `frontmatter.py`, `syllabify.py`, `prosody_engine.py`, `prosody_model.py`, `_phonetize_config.py`)
- Splitting CLI wrappers in `src/akkapros/cli/`
- Splitting test infrastructure files

---

# Current Behavior

All functions live in single monolithic files. Editing any one function requires loading the entire file into LLM context.

---

# Proposed Change

Each large module gets a focused submodule split. The parent module becomes a thin facade that imports and re-exports from submodules. Public import paths (`from akkapros.lib.metrics import ...`) remain unchanged.

## Split Map (code-grounded)

### 1. `metrics.py` → `_metrics_stats.py` + `_metrics_output.py`

Current function inventory (79 total):

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

### 2. `phoneprep.py` → `_phoneprep_phonology.py` + `_phoneprep_io.py`

Current function inventory (45 total):

**`_phoneprep_phonology.py`** — phonological rules, segment transformation, diphone extraction:
- `unique_preserve_order`, `normalize_long_vowels_to_short`
- `to_ipa_symbol`, `to_mbrola_symbol`, `map_word_symbols`, `map_diphones_symbols`
- `unique_preserve_pairs`, `parse_symbol_list`, `set_active_inventory`
- `is_vowel_plain`, `is_vowel_colored`, `is_consonant_plain`, `is_consonant_emphatic`
- `is_vv_diphone`, `is_vv_class_legal`, `is_vowel_valid`
- `extract_diphones_pattern1`, `extract_diphones_pattern2`, `extract_diphones_pattern3`
- `consonants_for_pattern`, `is_plain_emphatic_alternating`
- `validate_pattern1`, `validate_pattern2`, `validate_pattern3`
- `generate_all_pattern1_words`, `generate_all_pattern2_words`, `generate_all_pattern3_words`
- `vowel_pool_for_context`, `compute_reachable_diphone_inventory`
- `random_valid_word`
- `CoverageOptimizer` class

**`_phoneprep_io.py`** — file I/O, script generation, recording helpers:
- `generate_script`, `format_word`, `inventory_as_ipa`, `ipa_to_mbrola_mapping_list`
- `word_diphones`, `build_manifest_rows`, `write_alignment_sidecars`
- `extract_recording_words`, `write_recording_helper_html`
- `write_script`, `write_script_batched`, `validate_word_list`
- `run_tests`, `main`

### 3. `print.py` → `_print_ipa.py` + `_print_pho.py`

Current function inventory (38 total):

**`_print_ipa.py`** — IPA rendering, transliteration, accent markup:
- `_render_visible_merge_connector`, `_insert_glottal_stops`, `_insert_glottal_stops_with_indices`
- `_is_emphatic_adjacent`, `_row_vowel_is_emphatic`, `_to_ipa_vowel`, `_to_xar_vowel`
- `_convert_word_xar`
- `_is_punctuation`, `_detect_ipa_tag`, `_append_ipa_tag`, `_is_strong_ipa_tag`
- `_append_ipa_tag_cluster`, `_append_ipa_escape`, `_normalize_ipa_spacing`
- `_flush_syllable`, `_convert_word`, `_is_word_char`
- `_convert_non_bracket_part`, `_convert_non_bracket_part_ipa`
- `_append_non_word_char`, `_is_escape_segment`, `_convert_escape_segment`
- `_dearmor_pivot_punctuation`
- `convert_line`, `convert_text`, `convert_text_with_ipa`, `convert_text_with_ipa_xar`
- `_convert_bold_markdown_lines`, `_preserve_markdown_lineation`

**`_print_pho.py`** — `.pho` export, MBROLA format, phone row rendering:
- `_load_phone_rows`, `_resolve_original_phone_path`
- `_render_ipa_pause_row`, `_render_pause_row`, `_normalize_ipa_text`
- `_render_phone_rows`, `process_file`
- `run_tests`

### 4. `config.py` → extract `_config_io.py`

Current function inventory (55 total):

**`_config_io.py`** — YAML serialization, file I/O, config loading/saving:
- Functions related to reading/writing YAML files
- Config file discovery and path resolution
- Config merge/save operations

The parent `config.py` retains: schema definitions, validation logic, default values, CLI help text generation.

### 5. `test_phonetize_lib.py` → domain-split test files

- `test_phonetize_config.py`: config verification tests (extracted from the config-related test functions)
- `test_phonetize_realization.py`: realization/timing tests (extracted from the realization-related test functions)
- Parent file retains integration-level tests that span multiple domains

### 6. `test_integration.py` → CLI-split test files

- `test_integration_phonetizer.py`: phonetizer integration tests
- `test_integration_fullprosmaker.py`: full pipeline integration tests
- Parent file retains shared integration tests

---

# Technical Design

## Pattern (same as CR-087)

Each split follows this pattern:

1. Create `_<module>_<focus>.py` in the same directory as the parent.
2. Move the relevant functions into the submodule, keeping imports self-contained.
3. In the parent module, add `from ._<module>_<focus> import <symbols>` at the top.
4. Keep the parent's public API surface identical.
5. Do not change function signatures, class names, or behavior.

## Import Strategy

- Submodules import from sibling submodules using relative imports (`from ._metrics_stats import ...`).
- The parent module re-exports all public symbols from submodules.
- External code imports from the parent module only (`from akkapros.lib.metrics import ...`).

## Test Split Pattern

- New test files follow the same naming convention as existing tests.
- Each new test file imports from the parent module (not from submodules directly).
- Test fixtures remain in `tests/conftest.py` or in the test file itself.

---

# Files Likely Affected

```
src/akkapros/lib/metrics.py          → + _metrics_stats.py, _metrics_output.py
src/akkapros/lib/phoneprep.py        → + _phoneprep_phonology.py, _phoneprep_io.py
src/akkapros/lib/print.py            → + _print_ipa.py, _print_pho.py
src/akkapros/lib/config.py           → + _config_io.py
tests/test_phonetize_lib.py          → + test_phonetize_config.py, test_phonetize_realization.py
tests/test_integration.py            → + test_integration_phonetizer.py, test_integration_fullprosmaker.py
```

---

# Acceptance Criteria

- [ ] `metrics.py` public API unchanged: all existing imports from `akkapros.lib.metrics` still work
- [ ] `phoneprep.py` public API unchanged
- [ ] `print.py` public API unchanged
- [ ] `config.py` public API unchanged
- [ ] All existing tests pass (`python -m pytest`)
- [ ] No behavioral changes detected in integration test gold outputs
- [ ] Each new submodule is under 1000 lines
- [ ] Each new submodule has a single clear responsibility

---

# Risks / Edge Cases

- **Circular imports**: Submodules may import from each other. Use relative imports and defer imports inside functions if needed.
- **Missed re-exports**: A function used externally but not re-exported from the parent will break. Audit all imports of the parent module before splitting.
- **Test discovery**: New test files must match `test_*.py` pattern for pytest discovery.
- **CR-087 precedent**: This CR follows the same pattern. Review CR-087 implementation for exact split mechanics.
- **`phonetize.py` already split**: Do not re-split `phonetize.py` — it was handled by CR-087.

---

# Precautions

## Before Splitting

- **Verify current test baseline**: Run `python -m pytest` and confirm all tests pass before making any changes. Record the pass count.
- **Audit external imports**: For each module to split, grep all `from akkapros.lib.<module> import` across `src/` and `tests/` to know exactly which symbols are public API. Every symbol imported externally must be re-exported from the parent facade.
- **Check for module-level state**: Scan for module-level variables, singletons, or cached state that submodules might need to share. These must stay in the parent facade or be moved to a shared location.

## During Splitting

- **One module at a time**: Split one module completely (create submodules, update facade, run tests) before moving to the next. Do not batch splits.
- **Move functions, don't rewrite**: Copy-paste functions verbatim into submodules. Do not refactor, rename, or reformat during the move.
- **Keep self-tests in the parent facade**: Do not move `_test_*` functions or `run_tests` into submodules — they import from the parent and would create circular dependencies. If a module has many self-tests, move them to `src/akkapros/lib/tests/` following CR-087's pattern.
- **Use relative imports between submodules**: `from ._metrics_stats import ...` not `from akkapros.lib._metrics_stats import ...`.
- **Re-export everything from the parent**: The parent facade must import and re-export every public symbol. Use `from ._submodule import SymbolName` for each symbol, or use `__all__` if the submodule defines it.

## After Each Split

- **Run full pytest suite**: `python -m pytest` — all tests must pass.
- **Run library self-tests**: `python -m pytest tests/test_selftests_lib.py -q`.
- **Check gold outputs**: Run integration tests that compare against gold files and confirm no drift.
- **Verify imports from other modules still work**: Run a quick smoke test — import the parent module in Python and check that all expected symbols are accessible.

## If Something Breaks

- **Revert immediately**: Delete the submodule file(s) and restore the original parent module. The split is a move-only refactor with zero data migration — reverting is safe.
- **Isolate the broken symbol**: Identify which symbol causes the import error or test failure. Check whether it was re-exported from the parent and whether its internal imports are correct.
- **Do not patch behavior**: If a test fails because of a behavioral difference, the split introduced an unintended change. Revert and re-examine the moved code rather than patching the test.

---

# Testing Strategy

- Run full pytest suite before and after each split to confirm zero regressions.
- Run integration tests with gold output comparison to confirm no behavioral drift.
- Run library self-tests (`python -m pytest tests/test_selftests_lib.py -q`).

---

# Rollback Plan

Each split is a move-only refactor. Revert by restoring the original file and deleting the submodule files. No data migration needed.

---

# Related Issues

- CR-087: Original split of `phonetize.py`, `prosody.py`, `syllabify.py` (establishes the pattern)

---

# Tasks

## Implementation

- [ ] Split `metrics.py` into `_metrics_stats.py` + `_metrics_output.py`
- [ ] Split `phoneprep.py` into `_phoneprep_phonology.py` + `_phoneprep_io.py`
- [ ] Split `print.py` into `_print_ipa.py` + `_print_pho.py`
- [ ] Split `config.py` → add `_config_io.py`
- [ ] Split `test_phonetize_lib.py` into domain-focused test files
- [ ] Split `test_integration.py` into CLI-focused test files
- [ ] Update facade re-exports in all parent modules

## Tests

- [ ] Full pytest suite passes after each split
- [ ] Integration gold outputs unchanged
- [ ] Library self-tests pass

## Documentation

- [ ] Update `.github/copilot-instructions.md` if new submodule patterns are established
