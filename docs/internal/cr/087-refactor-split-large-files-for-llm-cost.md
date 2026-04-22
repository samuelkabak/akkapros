---
cr_id: CR-087
status: 'Done'
priority: 'Medium'
impact: 'Mutative'
created: 2026-04-22
updated: 2026-04-22
implements: ''
---

# Change Request: Business-zone split of large library modules to reduce LLM token costs

## Summary

Refactor a fixed phase-1 set of large modules under `src/akkapros/lib/` into smaller, responsibility-focused files so that
localized edits and LLM-assisted patch requests require sending fewer tokens of surrounding context.

This CR reduces the size of frequently edited library files by splitting them into business-logic zones so localized
changes do not require sending unrelated algorithm regions to the LLM. The split remains move-only: preserve behavior,
preserve names, keep the original module path as the public facade, and isolate self-tests away from runtime code.

---

## Motivation

- Reduce token cost and turnaround time when using LLMs to perform targeted edits.
- Improve readability, testability, and reviewer velocity by grouping related code.
- Decrease the chance of large, noisy diffs for small semantic changes.

Care must be taken not to fragment tightly-coupled logic in ways that make reasoning harder or that introduce
runtime hazards (for example: circular imports, or splitting modules that rely on module-level singletons).

---

## Scope

## Included

- Perform a move-only business-zone split for exactly these three primary modules:
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/lib/prosody.py`
  - `src/akkapros/lib/syllabify.py`
- Create internal submodules under `src/akkapros/lib/` and keep the original module files as public facades.
- Move library self-tests out of runtime modules into `src/akkapros/lib/tests/` and re-export stable `run_tests` entrypoints from the original module paths.
- Preserve all behavior and all currently used symbol names and casing.
- Preserve the current in-tree import contract for callers in `src/` and `tests/`.
- Add only the smallest verification edits needed to prove that imports and behavior are unchanged.

## Not Included

- Any behavioural changes to core algorithms (no algorithmic rewrites or tuning).
- Large API redesigns or removals of public symbols. Public API must remain stable during the migration.
- Splitting `metrics.py`, `phoneprep.py`, `print.py`, or `utils.py` in this CR.
- Deep extraction of high-risk solver or parser cores beyond the exact move-only slices named below.
- Permanent removal of old modules before a deprecation period (facades + re-exports are required).

---

## Current Behavior

- `src/akkapros/lib/phonetize.py` contains config/schema helpers, verification logic, row-building/runtime logic, I/O helpers, and self-tests in one file.
- `src/akkapros/lib/prosody.py` mixes enums, text/token helpers, model classes, engine logic, and self-tests in one file.
- `src/akkapros/lib/syllabify.py` mixes mutable punctuation/configuration state, character helpers, escape parsing, preprocessing, tokenization, and self-tests in one file.
- Current in-tree callers import these modules from multiple locations, including:
  - `src/akkapros/cli/phonetizer.py`
  - `src/akkapros/cli/fullprosmaker.py`
  - `src/akkapros/cli/prosmaker.py`
  - `src/akkapros/lib/config.py`
  - `src/akkapros/lib/metrics.py`
  - `src/akkapros/lib/print.py`
  - `tests/test_phonetize_lib.py`
  - `tests/test_metrics_stats.py`
  - `tests/test_prosody_mora_mode.py`
  - `tests/test_integration.py`
- These import sites make the original module paths part of the practical contract that must remain stable.

---

## Proposed Change

Perform an incremental, low-risk, move-only extraction in business-logic zones.

Required implementation order:

1. `phonetize.py` phase-1 split.
2. `prosody.py` phase-1 split.
3. `syllabify.py` phase-1 split.

The CR is complete when and only when those three module families are split by business zone and validated, including self-tests isolated under `src/akkapros/lib/tests/`.

Migration Constraints (required)

The following constraints are mandatory for each extraction commit. They exist to minimise risk from the
refactor and to guarantee that behaviour is preserved exactly during migration.

- **No renames:** Symbols (functions, methods, classes, dataclass names, and public variables) must keep
  their exact names and casing. For example, a function named `abc` must remain `abc` — it must not be
  split into `abc1`, renamed to `Abc`, or otherwise renamed.
- **No rewrites:** Implementations must not be rewritten or refactored during the extraction. Code may be
  moved verbatim between files and may have surrounding imports adjusted, but its logic and symbol names
  must remain unchanged. Small whitespace or docstring updates are allowed only when necessary for the
  file move (e.g., module docstrings or import re-ordering), but algorithmic changes are prohibited in this CR.
- **Move-only refactor:** The only permitted transformation is gathering functionally-similar functions,
  methods, and small type definitions into new submodules and importing them from the original module (facade).
  Facades must re-export public names so existing callers need no changes.
- **Filename convention:** Submodule filenames must use underscores (snake_case). Business-logic support modules may use a leading underscore for internal helpers; self-test modules must live under `src/akkapros/lib/tests/` and do not require a leading underscore.
- **Caller-path stability:** Callers outside the target module file must continue importing from the original
  module path (`akkapros.lib.phonetize`, `akkapros.lib.prosody`, `akkapros.lib.syllabify`). The original file
  becomes a facade and must continue to expose the same names used by in-tree callers and tests.
- **High-risk core retention:** `tokenize_line()` and `syllabify_text()` must stay in `syllabify.py`. The main phonetizer runtime row-building and realization core may remain in `phonetize.py`. `ProsodyEngine` may move to its own business-zone module while still being re-exported from `prosody.py`.

The intent is to produce small, well-named modules so that a future LLM-assisted change only needs the specific small module
plus a couple of directly-related files (types/facade), not a 1000-line file.

Function placement and locality guidance

The refactor is allowed to redistribute functions and methods non-contiguously: implementers may extract individual
symbols from anywhere in a file and group them into a logically-cohesive submodule. For example, given a file that
defines `func1`, `func2`, and `func3`, it is acceptable to move `func1` and `func3` to `module_a` and `func2` to
`module_b`. Physical interleaving in the original source must not be used as a reason to avoid splitting.

Locality heuristics (safety guidance)

- Small helper functions that are called by only a single caller should generally remain colocated with that caller
  unless there is a clear intent to maintain the helper independently (for example: the helper will be shared by
  future callers or is itself frequently edited). Moving single-call, tiny helpers to a separate submodule can
  increase the set of files an LLM must receive for a localized change, negating the goal of reducing token cost.
- When in doubt, prefer grouping a helper with its primary caller (keep locality), or move both caller and helper
  together into the same new submodule so that focused edits still remain small.
- Implementers should run a lightweight call-graph scan (static `git grep` or an ad-hoc script) to identify single-caller
  helpers before moving them; document exceptions in the commit message explaining why the move improves clarity
  or reusability.

Document such placement decisions in the PR description to aid reviewers and to make token-impact reasoning explicit.

---

## Technical Design

This CR defines three exact module families and their required business-zone extractions.

## Slice 1: `src/akkapros/lib/phonetize.py`

Create these internal submodules:

- `src/akkapros/lib/_phonetize_config.py`
- `src/akkapros/lib/tests/phonetize_tests.py`

Move to `_phonetize_config.py` without renaming or rewriting:

- `PhonetizeField`
- `VerificationIssue`
- `PhonetizeVerificationResult`
- `_field`
- `_is_field`
- `build_default_phonetize_config`
- `build_default_phonetize_verification_config`
- `iter_phonetize_fields`
- `get_phonetize_field`
- `validate_phonetize_source`
- `normalize_phonetize_config`
- `render_documented_phonetize_section`
- `get_relative_value`
- `set_relative_value`
- `apply_timing_override`
- `_merge_phonetize_config`
- `_runtime_view_phonetize_config`
- `_scale_duration_values`
- `_derive_effective_durations`
- `_make_issue`
- `_interval_distance`
- `_nearest_multiple_gap`
- `_round_sync_precision`
- `_resolve_mora_mode`
- `_resolve_synchronization_basis`
- `_supported_synchronization_bases`
- `_iter_numeric_leaves`
- `verify_phonetize_config`
- `render_phonetize_verification_lines`

Keep in `phonetize.py` for this phase:

- public constants currently imported by callers/tests
- row-building/runtime realization functions
- the main phonetizer realization core
- phone-row serialization and reconstruction helpers, because this slice is too small to justify an extra file hop
- facade re-exports for `run_tests`

`phonetize.py` must remain the public import surface and re-export all moved names.

## Slice 2: `src/akkapros/lib/prosody.py`

Create these internal submodules:

- `src/akkapros/lib/_prosody_types.py`
- `src/akkapros/lib/_prosody_text.py`
- `src/akkapros/lib/prosody_model.py`
- `src/akkapros/lib/prosody_engine.py`
- `src/akkapros/lib/tests/prosody_tests.py`

Move to `_prosody_types.py` without renaming or rewriting:

- `AccentStyle`
- `MoraMode`
- `SyllableType`

Move to `_prosody_text.py` without renaming or rewriting:

- `is_function_word`
- `parse_syl_line`
- `assemble_line`
- `_pivot_diphthong_replacement`
- `postprocess_restore_diphthongs`

Move to `prosody_model.py` without renaming or rewriting:

- `Syllable`
- `Word`
- `MergedUnit`

Move to `prosody_engine.py` without renaming or rewriting:

- `ProsodyEngine`

Move to `src/akkapros/lib/tests/prosody_tests.py` without renaming or rewriting:

- `test_diphthong_restoration`
- `run_tests`

`prosody.py` must remain the public import surface and re-export all moved names.

## Slice 3: `src/akkapros/lib/syllabify.py`

Create these internal submodules:

- `src/akkapros/lib/_syllabify_escape.py`
- `src/akkapros/lib/tests/syllabify_tests.py`

Move to `_syllabify_escape.py` without renaming or rewriting:

- `parse_escape_at`
- `split_by_escape_segments`
- `split_by_brackets_level3`

Keep in `syllabify.py` for this phase:

- all mutable punctuation/configuration globals and caches
- `PunctuationConfigError`
- `_compile_regex_patterns`
- `configure_punctuation_rules`
- punctuation-validation helpers
- character classification helpers
- `preprocess_diphthongs`
- `text_preprocess_boundaries`
- `syllabify_word`
- `tokenize_line`
- `syllabify_text`
- facade re-export for `run_tests`

`syllabify.py` must remain the public import surface and re-export all moved names.

Design rules for all three slices:

- Prefer moving cohesive helper groups that are independently readable and frequently consulted during local edits.
- Do not move tiny single-caller helpers into separate files unless the caller moves with them or the helper forms part of one of the explicit slices above.
- Do not update downstream callers to import the new underscore submodules directly.
- Prefer absolute imports from underscore submodules inside facades and sibling submodules.

---

## Files Likely Affected

- `src/akkapros/lib/phonetize.py`
- `src/akkapros/lib/_phonetize_config.py`
- `src/akkapros/lib/tests/phonetize_tests.py`
- `src/akkapros/lib/prosody.py`
- `src/akkapros/lib/_prosody_types.py`
- `src/akkapros/lib/_prosody_text.py`
- `src/akkapros/lib/prosody_model.py`
- `src/akkapros/lib/prosody_engine.py`
- `src/akkapros/lib/tests/prosody_tests.py`
- `src/akkapros/lib/syllabify.py`
- `src/akkapros/lib/_syllabify_escape.py`
- `src/akkapros/lib/tests/syllabify_tests.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/cli/prosmaker.py`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/lib/print.py`
- `tests/test_phonetize_lib.py`
- `tests/test_metrics_stats.py`
- `tests/test_prosody_mora_mode.py`
- `tests/test_integration.py`

---

## Acceptance Criteria

- [x] `phonetize.py` has been split by business zone and still exports the moved names and `run_tests` from `akkapros.lib.phonetize`.
- [x] `prosody.py` has been split by business zone and still exports the moved names, `test_diphthong_restoration`, and `run_tests` from `akkapros.lib.prosody`.
- [x] `syllabify.py` has been split by business zone and still exports the moved names and `run_tests` from `akkapros.lib.syllabify`.
- [x] Library self-tests for `phonetize`, `prosody`, and `syllabify` live under `src/akkapros/lib/tests/` instead of runtime modules.
- [x] No symbol renaming or algorithmic rewrites occurred during the refactor.
- [x] No caller outside the target module files imports underscore submodules directly.
- [x] No new circular imports are introduced.
- [x] The existing in-tree import sites listed in this CR continue to run without changing their import statements.
- [x] Focused tests for the touched slices pass after each slice.
- [x] The full suite passes locally with `python -m pytest` after all three slices are complete.
- [x] A short developer note is added under `docs/internal/` or the CR notes describing the facade-plus-underscore-submodule pattern for future follow-up CRs.

---

## Risks / Edge Cases

- Circular imports between facades and underscore submodules. Mitigation: keep the moved slices one-directional and avoid submodules importing back through the public facade.
- Module-level mutable globals in `syllabify.py`. Mitigation: keep state and state-owning functions in `syllabify.py` during this phase.
- Public API churn and downstream imports that refer to internal names. Mitigation: keep facades and re-export every moved name still used by in-tree callers/tests.
- Slightly increased package import latency (negligible for CLI runs).

---

## Testing Strategy

Unit tests and integration tests must be used as the primary verification path.

Required validation order:

1. After Slice 1, run the smallest phonetize-focused slice that covers facade imports and moved helpers.
2. After Slice 2, run the smallest prosody-focused slice that covers facade imports and moved helpers.
3. After Slice 3, run the smallest syllabify/print/metrics slice that covers facade imports and moved helpers.
4. After all slices, run the fast developer loop and then the full safety gate.

Minimum required commands:

```powershell
python -m pytest tests/test_phonetize_lib.py tests/test_selftests_lib.py -q
python -m pytest tests/test_prosody_mora_mode.py tests/test_selftests_lib.py tests/test_metrics_stats.py -q
python -m pytest tests/test_selftests_lib.py tests/test_metrics_stats.py tests/test_print_merger.py -q
python -m pytest -m "not integration and not slow"
python -m pytest
```

Optional token-impact note:

- This CR may include a small measurement note in the PR description comparing pre/post line counts for the three target files and the new submodules.
- A dedicated token-estimation script is not required for this CR and should be deferred to a follow-up CR if still desired.

---

## Rollback Plan

- Each slice is performed in its own self-contained commit. To rollback a problematic extraction, revert that slice commit and rerun the focused tests plus the full gate if needed.
- If a post-merge problem is discovered, revert only the affected slice and keep the remaining slices intact when possible.

---

## Related Issues

- CR-086 (optimize-test-execution-with-markers-fast-fullprosmaker-and-tagged-code-index)

---

## Tasks

## Implementation

- [x] Implement the phonetize business-zone split, including `lib/tests/phonetize_tests.py`.
- [x] Implement the prosody business-zone split, including model, engine, and `lib/tests/prosody_tests.py`.
- [x] Implement the syllabify business-zone split, including `lib/tests/syllabify_tests.py`.

## Tests

- [x] Add only the smallest tests needed to prove facade imports and moved-symbol behavior remain unchanged.
- [x] Run the required focused slices after each implementation slice.
- [x] Run `python -m pytest -m "not integration and not slow"`.
- [x] Run `python -m pytest`.

## Documentation

- [x] Add a short note describing the facade-plus-underscore-submodule pattern and the move-only rule.

## Review

- [x] Review each slice commit for import graph safety, no-renames, and no-rewrites.
- [x] Confirm callers outside the target modules do not import underscore submodules.

---

## Implementation Blockers

## 2026-04-22 - Completion boundary is not executable

- Type: `spec weakness`
- Observed: the CR names several candidate modules (`phonetize.py`, `syllabify.py`, `prosody.py`, `phoneprep.py`, `utils.py`, `print.py`, `metrics.py`) but does not define the exact required target set for implementation. Acceptance criteria require that "each targeted file" be split, but the CR leaves the target list and stopping point to the implementer.
- Why blocked: safe implementation cannot be declared done because the CR does not define which modules are mandatory in scope for completion and which are optional follow-on work.
- Needed to unblock: rewrite the CR to name the exact required module set and extraction order, or split this umbrella CR into smaller executable CRs such as one CR per target module family.
- Owner: `spec writer`
- Related refs: `src/akkapros/lib/phonetize.py`, `src/akkapros/lib/syllabify.py`, `src/akkapros/lib/prosody.py`, `src/akkapros/lib/metrics.py`
- Resolved on: 2026-04-22
- Resolution: rewrote the CR around an exact three-module target set and three ordered move-only slices with explicit completion criteria.

## 2026-04-22 - Module-level singleton / global-state coupling (syllabify punctuation caches)

- Type: `code/spec mismatch`
- Observed: `syllabify.py` contains module-level globals and compiled regex caches used by multiple functions and tests.
- Why blocked: naive extraction of helpers into a separate file may break the implicit singleton behaviour expected by callers.
- Needed to unblock: decision on whether to keep configuration functions and the cache in the facade module or to centralise state into an explicit `syllabify_state.py` used by all submodules.
- Owner: `implementer`
- Related refs: `src/akkapros/lib/syllabify.py`
- Resolved on: 2026-04-22
- Resolution: specified that mutable punctuation/configuration state and state-owning functions remain in `syllabify.py` for this phase; only escape helpers move.

## 2026-04-22 - Public API import surface is not exhaustively catalogued

- Type: `spec weakness`
- Observed: some tests and CLI modules import internal helpers directly; a complete migration requires an inventory of those imports.
- Why blocked: without an inventory the implementer risks breaking callers.
- Needed to unblock: run an automatic import-usage scan (e.g., `git grep "from akkapros.lib"`) and produce a short list of files that import internal names.
- Owner: `implementer`
- Resolved on: 2026-04-22
- Resolution: documented the current in-tree caller set in `src/` and `tests/` and made preservation of those import paths an explicit acceptance criterion.

## 2026-04-22 - Scope should be decomposed into move-only implementation slices

- Type: `spec weakness`
- Observed: `phonetize.py` alone exposes a very large public and internal surface, while `syllabify.py` and `prosody.py` each have their own constraints and high-risk contracts. The current CR combines multiple large move-only refactors into one acceptance gate.
- Why blocked: the requested no-rewrite / no-rename rule is defensible only when each slice is small and independently verifiable. Bundling several large modules into one CR makes root-cause verification and rollback ambiguous.
- Needed to unblock: decompose the work into a sequence of smaller CRs, for example: one CR for `phonetize.py`, one CR for `syllabify.py`, one CR for `prosody.py`, and optional follow-up CRs for secondary modules.
- Owner: `spec writer`
- Related refs: `src/akkapros/lib/phonetize.py`, `src/akkapros/lib/syllabify.py`, `src/akkapros/lib/prosody.py`
- Resolved on: 2026-04-22
- Resolution: decomposed the implementation into three explicit phase-1 slices within this CR and moved secondary modules out of scope.

---

## Notes

- This CR is intentionally conservative around the highest-risk parser/runtime cores, but it does require isolating library self-tests and the prosody model layer so edits can target smaller business zones.
- Implemented on 2026-04-22 with the facade-plus-underscore-submodule pattern:
  - `phonetize.py` now re-exports helpers from `_phonetize_config.py`
  - `phonetize.py` now re-exports `run_tests` from `lib/tests/phonetize_tests.py`
  - `prosody.py` now re-exports helpers from `_prosody_types.py` and `_prosody_text.py`, model/engine types from `prosody_model.py` and `prosody_engine.py`, and self-tests from `lib/tests/prosody_tests.py`
  - `syllabify.py` now re-exports helpers from `_syllabify_escape.py` and `run_tests` from `lib/tests/syllabify_tests.py`
- Follow-up CRs may target deeper splits of `phonetize.py`, `prosody.py`, `syllabify.py`, or secondary modules once the phase-1 pattern is proven safe.

Implementation complete. This document records the executable contract and the verified business-zone split result for `CR-087`.
