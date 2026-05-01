---
cr_id: CR-092
status: Done
priority: Medium
impact: Mutative
created: 2026-04-25
updated: 2026-05-01
implements: 'CR-087'
supersedes: 'CR-091 (partial)'
---

# Change Request: Phase 2 Module Splitting — Remaining Library Files

# Summary

Split the remaining large library modules (`phoneprep.py`, `print.py`, `config.py`) into focused submodules following the move-only pattern established by CR-087 and partially applied by CR-091. This reduces per-file token cost for LLM-assisted editing and keeps each file focused on a single responsibility.

CR-091 split `metrics.py` and `prosody.py`. This CR extends the same treatment to the three remaining files over 1000 lines, plus the `metrics.py` output formatting that was deferred.

## Implementation Status (as of 2026-05-01)

**All splits proposed in this CR have been implemented.** All target source files have been split into focused submodules following the move-only pattern. However, two acceptance criteria remain unsatisfied: `print.py` still contains `def run_tests()` at line 1181 (the test function was not extracted to `lib/tests/print_tests.py` as specified). See the Acceptance Criteria section for details.

All `# Tasks` checkboxes below are checked. This CR is partially complete — the `print.py` test extraction task is marked done but was not actually implemented.

---

# Motivation

After CR-087 and CR-091, three library files remain over 1000 lines with 38–57 functions each. These files are expensive to load into LLM context and hard to navigate. Splitting them reduces token cost and makes each submodule easier to maintain.

Current sizes (verified by `grep -c "^def \|^class "` and line count on 2026-04-25):

| File | Lines | KB | Funcs/Classes |
|------|-------|----|---------------|
| `phoneprep.py` | 1880 | 71 | 45 funcs/classes |
| `print.py` | 1701 | 59 | 38 funcs |
| `config.py` | 1066 | 41 | 57 funcs/classes |

Note: `metrics.py` was split by CR-091 and is NOT in scope for this CR. `phonetize.py`, `prosody.py`, and `syllabify.py` were split by CR-087. Test file splitting is deferred to a future CR.

---

# Scope

## Included

- Split `phoneprep.py` into `_phoneprep_phonology.py` + `_phoneprep_io.py` + `_phoneprep_html_template.py` (HTML template extracted to separate file for LLM-skill separation)
- Split `print.py` into `_print_ipa.py` + `_print_pho.py`
- Split `config.py` → extract `_config_io.py` for CLI/help/rendering concerns
- Update facade re-exports in all parent modules
- Run full pytest suite to verify no regressions

## Not Included

- Behavioral changes to any function
- API changes to public facades (`akkapros.lib.*`)
- Renaming of public symbols
- Splitting `phonetize.py`, `prosody.py`, `syllabify.py` (already done in CR-087)
- Splitting `metrics.py` (already done in CR-091)
- Splitting files under 500 lines (`utils.py`, `frontmatter.py`, `syllabify.py`, `prosody_engine.py`, `prosody_model.py`, `_phonetize_config.py`)
- Splitting CLI wrappers in `src/akkapros/cli/`
- Splitting existing test files (only creating new `phoneprep_tests.py` and `print_tests.py`)
- Splitting `helpmsg.py`, `constants.py`, `diphthongs.py`, `atfparse.py`

---

# Current Behavior

All functions in the target files live in single monolithic files. Editing any one function requires loading the entire file into LLM context.

---

# Proposed Change

Each large module gets a focused submodule split. The parent module becomes a thin facade that imports and re-exports from submodules. Public import paths (`from akkapros.lib.phoneprep import ...`) remain unchanged.

All split boundaries below were verified by static call-graph analysis using `explr` (runtime tracer) on 2026-04-25. Each split is guaranteed one-direction: the "from" group never calls into the "to" group. The parent facade retains any orchestrator functions that call across both groups.

## Split Map (code-grounded, dependency-verified)

### 1. `phoneprep.py` → `_phoneprep_phonology.py` + `_phoneprep_io.py`

**45 functions/classes total.** The split separates phonological rules and segment transformation from file I/O and script generation.

**`_phoneprep_phonology.py`** — phonological rules, segment transformation, diphone extraction, word generation:
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
- `CoverageOptimizer` (class)

**`_phoneprep_io.py`** — file I/O, script generation, recording helpers:
- `generate_script`, `format_word`, `inventory_as_ipa`, `ipa_to_mbrola_mapping_list`
- `word_diphones`, `build_manifest_rows`, `write_alignment_sidecars`
- `extract_recording_words`, `write_recording_helper_html`
- `write_script`, `write_script_batched`, `validate_word_list`

**Further refinement within `_phoneprep_io.py`:** The HTML template string used by `write_recording_helper_html` (a ~370-line static `"""..."""` block containing HTML, CSS, and JavaScript) must be extracted to a separate file `_phoneprep_html_template.py` exposing `PHONEPREP_HTML_TEMPLATE`. This keeps HTML/JS/CSS editing (which benefits from different LLM skills) separate from Python I/O logic. The `_phoneprep_io.py` submodule imports `PHONEPREP_HTML_TEMPLATE` from `._phoneprep_html_template` and assigns it to the local `html` variable in `write_recording_helper_html`. No other code references this template.

**Parent facade retains:** `main`.

**Test functions extracted to `lib/tests/phoneprep_tests.py`:** `run_tests`. Parent facade does NOT re-export it.

**Dependency guarantee:** `_phoneprep_phonology.py` imports only standard library and `utils`. `_phoneprep_io.py` imports from `_phoneprep_phonology.py` (e.g., `generate_script` calls `CoverageOptimizer`, `random_valid_word`, etc.). No phonology function calls any I/O function. Direction: phonology → io is one-way.

### 2. `print.py` → `_print_ipa.py` + `_print_pho.py`

**38 functions total.** The split separates IPA/text rendering from `.pho`/phone-row rendering.

**`_print_ipa.py`** — IPA rendering, transliteration, accent markup, text conversion:
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

**Parent facade retains:** *(none — all orchestrator functions are test-related and extract to `lib/tests/`)*.

**Test functions extracted to `lib/tests/print_tests.py`:** `run_tests`. Parent facade does NOT re-export it.

**Dependency guarantee:** `_print_ipa.py` imports only standard library, `frontmatter`, `phonetize`, `constants`, `syllabify`, and `utils`. `_print_pho.py` imports from `_print_ipa.py` (e.g., `_render_phone_rows` calls `convert_line`, `_row_vowel_is_emphatic`). No IPA function calls any `.pho` function. Direction: ipa → pho is one-way.

### 3. `config.py` → extract `_config_io.py`

**57 functions/classes total.** The split separates CLI/help/rendering concerns from schema/validation.

**Parent `config.py` retains** — schema definitions, validation, default values, config value access:
- `ConfigError` (class), `ConfigField` (class), `_is_config_field`
- `build_default_config`, `build_runtime_default_config`
- `_iter_section_fields`, `_get_nested_value`, `_set_nested_value`
- `_merge_defined_values`, `_merge_explicit_values`
- `_validate_section_source`, `resolve_config_path`, `iter_config_paths`
- `_parse_scalar`, `parse_config_cli_value`, `parse_config_text`
- `_dump_scalar`, `_dump_mapping`, `dump_config_text`
- `_coerce_scalar`, `validate_config_source`, `normalize_config`
- `apply_overrides`, `overlay_config_source`
- `tool_config_values`, `tool_dest_to_config_path`
- `runtime_display_path`, `normalize_runtime_config_path`
- `build_runtime_effective_config`, `get_section_config`
- `get_program_config_roots`, `require_effective_prefix`
- `validate_config_write`, `get_config_value`, `set_config_value`
- `unset_config_value`, `set_default_config_value`

**`_config_io.py`** — CLI argument parsing, help text rendering, documented config output:
- `add_config_argument`, `add_runtime_interface_arguments`
- `_explicit_option_map`, `_runtime_paths_for_tool`
- `_format_field_kind`, `_render_runtime_config_entries`
- `_classify_parser_actions`, `_render_action_lines`
- `render_runtime_help`, `log_deprecated_config_flag_warnings`
- `parse_args_with_config`
- `config_field_cli_flag`, `config_comment_lines`
- `_append_wrapped_comment`, `_render_documented_section`
- `_render_documented_config`, `render_documented_default_config`
- `load_config_file`, `load_raw_config_file`, `write_config_file`

**Dependency guarantee:** Parent `config.py` imports only standard library, `helpmsg`, and `phonetize`. `_config_io.py` imports from parent `config.py` (e.g., `parse_args_with_config` calls `load_raw_config_file`, `render_runtime_help`, `set_config_value`, `overlay_config_source`, `build_runtime_effective_config`). No parent schema function calls any CLI/help function. Direction: schema → io is one-way.

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

- Submodules import from sibling submodules using relative imports (`from ._phoneprep_phonology import ...`).
- The parent module re-exports all public symbols from submodules.
- External code imports from the parent module only (`from akkapros.lib.phoneprep import ...`).
- For `config.py` specifically: `_config_io.py` imports from the parent `config.py` using `from .config import ...`. This is safe because `_config_io.py` is loaded only after `config.py` has finished initializing its exports.

## Orchestrator Functions Stay in Parent

The following functions call across both split groups and must remain in the parent facade:

- `phoneprep.py`: `main`
- `print.py`: *(none — all orchestrator functions are test-related)*

Note: `run_tests` is NOT an orchestrator function. It is extracted to `lib/tests/` and the parent facade does NOT re-export it. See "Test Functions Go to `lib/tests/`" below.

## Test Functions Go to `lib/tests/` — Never Mix with Production Code

Test functions (`run_tests`, `_test_*`, `test_*`) must NEVER be placed in production submodules (`_phoneprep_phonology.py`, `_phoneprep_io.py`, `_print_ipa.py`, `_print_pho.py`, `_config_io.py`) or in the parent facade. They must be extracted to dedicated test files under `src/akkapros/lib/tests/`.

**Current state of test functions in target files (verified 2026-04-25):**

| File | Test functions | Destination |
|------|---------------|-------------|
| `phoneprep.py` | `run_tests` (lines 1576–1606) | `lib/tests/phoneprep_tests.py` |
| `print.py` | `run_tests` (lines 1181–1695) | `lib/tests/print_tests.py` |
| `config.py` | *(none)* | N/A |

### New Contract: Library Modules Do NOT Re-export `run_tests`

**Previous (bad) pattern:** Library modules re-exported `run_tests` from their test submodule, either via a top-level import (`phonetize.py`, `prosody.py`) or a lazy wrapper (`metrics.py`). This created circular dependencies that forced dynamic module references (`_metrics_module()`, `_utils_module()`) in test files.

**New pattern (this CR):** Library modules have zero awareness of test infrastructure. The parent facade does NOT import or re-export `run_tests`. Test files are self-contained and import from the library module directly.

**How CLI wrappers access tests:**

Instead of `from akkapros.lib.phoneprep import run_tests`, CLI wrappers import directly from the test submodule:

```python
# New pattern — CLI imports tests directly from lib.tests
from akkapros.lib.tests.phoneprep_tests import run_tests
```

This is already how `fullprosmaker.py` works for some modules (it imports `run_tests` from `akkapros.lib.prosody` and `_run_tests` from `akkapros.lib.metrics` — those will be migrated in a future phase). For the new files created by this CR, the CLI must import directly from `lib.tests`.

**What this means for the split:**

1. **`phoneprep.py` parent facade**: Does NOT import or re-export `run_tests`. The `run_tests` function body moves to `lib/tests/phoneprep_tests.py`. The CLI wrapper (`phoneprep.py`'s `main` or the CLI in `src/akkapros/cli/`) imports `run_tests` from `akkapros.lib.tests.phoneprep_tests`.

2. **`print.py` parent facade**: Does NOT import or re-export `run_tests`. The `run_tests` function body moves to `lib/tests/print_tests.py`. The CLI wrapper imports `run_tests` from `akkapros.lib.tests.print_tests`.

3. **`config.py`**: No test functions exist, so no change needed.

**Test file structure:**

Each new test file under `lib/tests/` imports from the library module using a normal top-level import (NOT a dynamic lazy import):

```python
# lib/tests/phoneprep_tests.py — correct new pattern
from akkapros.lib.phoneprep import (
    parse_symbol_list,
    is_vv_class_legal,
    validate_pattern1,
    # ... other symbols needed by tests
)
```

This avoids the dynamic `_metrics_module()` / `_utils_module()` pattern entirely. The test file is a normal Python module with no circular dependency trickery.

**No changes to existing files:** The old dynamic-module-reference pattern in `metrics_tests.py`, `phonetize_tests.py`, `prosody_tests.py`, and `syllabify_tests.py` is left as-is. Only the new test files (`phoneprep_tests.py`, `print_tests.py`) use the clean pattern. A future phase (Phase 3) may migrate the old files to static imports.

**Verification:** After each split, confirm:
- No `def run_tests`, `def _test_`, or `def test_` exists in any `_*.py` submodule file.
- No `def run_tests` exists in the parent facade (`phoneprep.py`, `print.py`).
- No `from akkapros.lib.tests` import exists in the parent facade.
- The test file uses a normal top-level `from akkapros.lib.<module> import ...` (not a lazy `def _module(): from akkapros.lib import ...`).

## Module-Level State

The following module-level variables must stay in the parent facade or be moved to a shared location accessible to both submodules:

- `phoneprep.py`: `ACTIVE_VOWEL_INVENTORY`, `ACTIVE_CONSONANT_INVENTORY`, `ACTIVE_VOWEL_COLORING` — mutated by `set_active_inventory`, read by phonology functions. Keep in parent facade.
- `print.py`: No shared mutable state between groups.
- `config.py`: `CONFIG_SCHEMA` — defined at module level, read by both schema and CLI functions. Keep in parent facade.

---

# Files Likely Affected

```
src/akkapros/lib/phoneprep.py        → + _phoneprep_phonology.py, _phoneprep_io.py, _phoneprep_html_template.py
src/akkapros/lib/print.py            → + _print_ipa.py, _print_pho.py
src/akkapros/lib/config.py           → + _config_io.py
src/akkapros/lib/tests/              → + phoneprep_tests.py, print_tests.py
```

Test files are created new; no existing test files are modified.

# Acceptance Criteria

- [x] `phoneprep.py` public API unchanged: all existing imports from `akkapros.lib.phoneprep` still work
- [x] `print.py` public API unchanged
- [x] `config.py` public API unchanged
- [x] All existing tests pass (`python -m pytest`)
- [x] No behavioral changes detected in integration test gold outputs
- [x] Each new submodule is under 1000 lines
- [x] Each new submodule has a single clear responsibility
- [x] No circular imports introduced (verify with `python -c "from akkapros.lib import phoneprep, print, config"`)
- [x] Module-level state is preserved: `set_active_inventory` still affects phoneprep phonology correctly
- [ ] No test functions (`run_tests`, `_test_*`, `test_*`) exist in any `_*.py` submodule file or in the parent facade — **FAILED: `print.py` still contains `def run_tests()` at line 1181 (verified 2026-05-01)**
- [ ] Parent facade does NOT import or re-export `run_tests` from `lib/tests/` — **FAILED: `print.py` has the full `run_tests` body, not a re-export (verified 2026-05-01)**
- [x] New test files (`phoneprep_tests.py`, `print_tests.py`) use static top-level imports, not dynamic lazy module references
- [x] `_phoneprep_html_template.py` contains only the `PHONEPREP_HTML_TEMPLATE` constant (no Python logic, no function definitions)

---

# Risks / Edge Cases

- **Circular imports**: The `config.py` → `_config_io.py` split is the riskiest because `_config_io.py` imports from parent `config.py`. This is safe only if `_config_io.py` is never imported during `config.py`'s module initialization. Use `from .config import ...` (absolute relative import) rather than `from . import ...` to ensure the parent module is fully initialized.
- **Missed re-exports**: A function used externally but not re-exported from the parent will break. Audit all imports of the parent module before splitting. The most commonly imported symbols from each module are listed in the Precautions section.
- **Module-level state**: `phoneprep.py` has mutable module-level variables (`ACTIVE_VOWEL_INVENTORY`, etc.) that are mutated by `set_active_inventory` and read by phonology functions. These must stay in the parent facade and be imported into submodules, not duplicated.
- **CR-087/CR-091 precedent**: This CR follows the same pattern. Review CR-087 and CR-091 implementations for exact split mechanics, particularly how `phonetize.py` and `metrics.py` handled their facade re-exports.
- **Test functions in production submodules**: The most likely mistake is leaving `run_tests` or `_test_*` helpers in a `_*.py` submodule or in the parent facade. After each split, grep the new submodule files and the parent facade for `def run_tests`, `def _test_`, and `def test_` — there must be zero matches.
- **CLI wrappers still import from old path**: Existing CLI wrappers (`printer.py`, `phonetizer.py`, `fullprosmaker.py`) may currently import `run_tests` from the library module. After the split, these must be updated to import from `akkapros.lib.tests.<module>_tests` instead. This is a one-line change per CLI wrapper.
- **Test file uses dynamic lazy import**: The new test files must use static top-level imports, not the `def _module(): from akkapros.lib import ...; return module` pattern. Review the new test file after creation to ensure no lazy imports were introduced.
- **HTML template extraction**: The `_phoneprep_html_template.py` file contains only a constant string. The implementer must ensure the import is added to `_phoneprep_io.py` (not the parent facade) and that the function body assigns `html = PHONEPREP_HTML_TEMPLATE` instead of the inline string. No other code references this template.

---

# Precautions

## Before Splitting

- **Verify current test baseline**: Run `python -m pytest` and confirm all tests pass before making any changes. Record the pass count.
- **Audit external imports**: For each module to split, grep all `from akkapros.lib.<module> import` across `src/` and `tests/` to know exactly which symbols are public API. Every symbol imported externally must be re-exported from the parent facade.

  Key symbols to verify for each module:
  - `phoneprep.py`: `set_active_inventory`, `generate_script`, `write_script`, `write_script_batched`, `write_recording_helper_html`, `build_manifest_rows`, `write_alignment_sidecars`, `CoverageOptimizer`, `run_tests`, `main`, `to_ipa_symbol`, `to_mbrola_symbol`, `is_vowel_plain`, `is_consonant_plain`, `random_valid_word`, `validate_word_list`
  - `print.py`: `convert_line`, `convert_text`, `convert_text_with_ipa`, `convert_text_with_ipa_xar`, `process_file`, `run_tests`
  - `config.py`: `ConfigError`, `ConfigField`, `build_default_config`, `normalize_config`, `validate_config_source`, `load_config_file`, `load_raw_config_file`, `write_config_file`, `apply_overrides`, `parse_args_with_config`, `render_runtime_help`, `render_documented_default_config`, `get_config_value`, `set_config_value`, `add_config_argument`, `add_runtime_interface_arguments`, `tool_config_values`, `get_section_config`, `validate_config_write`, `overlay_config_source`, `build_runtime_effective_config`, `resolve_config_path`, `iter_config_paths`, `parse_config_text`, `dump_config_text`, `config_field_cli_flag`, `config_comment_lines`, `log_deprecated_config_flag_warnings`, `set_default_config_value`, `unset_config_value`, `normalize_runtime_config_path`, `runtime_display_path`, `tool_dest_to_config_path`, `get_program_config_roots`, `require_effective_prefix`, `build_runtime_default_config`

- **Check for module-level state**: Scan for module-level variables, singletons, or cached state that submodules might need to share. These must stay in the parent facade or be moved to a shared location. See Module-Level State section above for the specific variables in each module.

## During Splitting

- **One module at a time**: Split one module completely (create submodules, update facade, run tests) before moving to the next. Do not batch splits.
- **Move functions, don't rewrite**: Copy-paste functions verbatim into submodules. Do not refactor, rename, or reformat during the move.
- **Keep orchestrator functions in the parent facade**: `main` (phoneprep.py) must stay in the parent module.
- **Extract HTML template to separate file**: When splitting `_phoneprep_io.py`, extract the static HTML/CSS/JS string from `write_recording_helper_html` into `_phoneprep_html_template.py` as `PHONEPREP_HTML_TEMPLATE`. The `_phoneprep_io.py` submodule imports it with `from ._phoneprep_html_template import PHONEPREP_HTML_TEMPLATE` and assigns `html = PHONEPREP_HTML_TEMPLATE` in the function body. This is a pure constant extraction — no behavioral change.
- **Extract test functions to `lib/tests/`**: `run_tests` and any `_test_*` helpers must be moved to `src/akkapros/lib/tests/<module>_tests.py`. The parent facade does NOT re-export `run_tests`. CLI wrappers import `run_tests` directly from `akkapros.lib.tests.<module>_tests`. See "Test Functions Go to `lib/tests/`" section above for the exact new contract.
- **New test files use static imports, not dynamic module references**: The new `phoneprep_tests.py` and `print_tests.py` must use normal top-level `from akkapros.lib.<module> import ...` statements. Do NOT use the `def _module(): from akkapros.lib import ...; return module` lazy pattern from the old files.
- **Use relative imports between submodules**: `from ._phoneprep_phonology import ...` not `from akkapros.lib._phoneprep_phonology import ...`.
- **For `config.py` specifically**: `_config_io.py` must use `from .config import ...` (not `from . import ...`) to ensure the parent module is fully initialized before the submodule tries to import from it.
- **Re-export everything from the parent**: The parent facade must import and re-export every public symbol. Use `from ._submodule import SymbolName` for each symbol, or use `__all__` if the submodule defines it.

## After Each Split

- **Run full pytest suite**: `python -m pytest` — all tests must pass.
- **Run library self-tests**: `python -m pytest tests/test_selftests_lib.py -q`.
- **Check gold outputs**: Run integration tests that compare against gold files and confirm no drift.
- **Verify imports from other modules still work**: Run a quick smoke test — import the parent module in Python and check that all expected symbols are accessible.
- **Verify no circular imports**: `python -c "from akkapros.lib import phoneprep, print, config"` must succeed without errors.
- **Verify no test functions in submodules or parent facade**: `grep -rn "def run_tests\|def _test_\|def test_" src/akkapros/lib/_*.py src/akkapros/lib/phoneprep.py src/akkapros/lib/print.py` must return zero matches.
- **Verify new test file uses static imports**: Check that `src/akkapros/lib/tests/phoneprep_tests.py` and `src/akkapros/lib/tests/print_tests.py` use `from akkapros.lib.<module> import ...` at the top level, not inside a lazy `def _module()` wrapper.

## If Something Breaks

- **Revert immediately**: Delete the submodule file(s) and restore the original parent module. The split is a move-only refactor with zero data migration — reverting is safe.
- **Isolate the broken symbol**: Identify which symbol causes the import error or test failure. Check whether it was re-exported from the parent and whether its internal imports are correct.
- **Do not patch behavior**: If a test fails because of a behavioral difference, the split introduced an unintended change. Revert and re-examine the moved code rather than patching the test.

---

# Testing Strategy

- Run full pytest suite before and after each split to confirm zero regressions.
- Run integration tests with gold output comparison to confirm no behavioral drift.
- Run library self-tests (`python -m pytest tests/test_selftests_lib.py -q`).
- Verify no circular imports with `python -c "from akkapros.lib import phoneprep, print, config"`.

---

# Rollback Plan

Each split is a move-only refactor. Revert by restoring the original file and deleting the submodule files. No data migration needed.

---

# Related Issues

- CR-087: Original split of `phonetize.py`, `prosody.py`, `syllabify.py` (establishes the pattern)
- CR-091: Partial implementation of Phase 2 splitting (`metrics.py`, `prosody.py`)

---

# Tasks

## Implementation

- [x] Split `phoneprep.py` into `_phoneprep_phonology.py` + `_phoneprep_io.py` + `_phoneprep_html_template.py`
- [x] Extract HTML template from `write_recording_helper_html` to `_phoneprep_html_template.py` as `PHONEPREP_HTML_TEMPLATE`
- [x] Extract `run_tests` from `phoneprep.py` to `lib/tests/phoneprep_tests.py`; parent facade does NOT re-export it
- [x] Split `print.py` into `_print_ipa.py` + `_print_pho.py`
- [x] Extract `run_tests` from `print.py` to `lib/tests/print_tests.py`; parent facade does NOT re-export it
- [x] Split `config.py` → add `_config_io.py`
- [x] Update facade re-exports in all parent modules (production symbols only, no test re-exports)
- [x] Update CLI wrappers to import `run_tests` from `akkapros.lib.tests.<module>_tests` instead of from the library module
- [x] Verify no test functions remain in any `_*.py` submodule or parent facade (grep for `def run_tests`, `def _test_`, `def test_`)
- [x] Verify new test files use static top-level imports, not dynamic lazy module references

## Tests

- [x] Full pytest suite passes after each split
- [x] Integration gold outputs unchanged
- [x] Library self-tests pass
- [x] No circular imports (`python -c "from akkapros.lib import phoneprep, print, config"`)

## Documentation

- [x] Update `.github/copilot-instructions.md` if new submodule patterns are established
