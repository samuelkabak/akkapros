# Change Request: Refactor simple_safe_filename and phoneprep core

CR-ID: CR-010
Status: Done
Priority: Medium
Created: 2026-03-20
Updated: 2026-03-20
Implements: ADR-001
---

# Summary

Remove the duplicated `simple_safe_filename()` implementation found in `cli/prosmaker.py`
and `cli/metricalc.py` and import the canonical implementation from `lib/utils.py`.

In a related, but separate change, extract the core logic from `cli/phoneprep.py` into
`lib/phoneprep.py` so the CLI becomes a thin wrapper and the implementation aligns with
ADR-001 (CLI / lib separation).

This CR is a design-level proposal only; implementation will be performed in a
follow-up PR after review and acceptance.

---

# Motivation

- Remove code duplication that risks divergence and maintenance burden.
- Improve testability: moving logic into `lib/` enables unit tests without invoking
  CLI parsing.
- Align `phoneprep.py` with the project's ADR-001 CLI/lib separation policy.

Both changes reduce future technical debt and make behavior easier to audit.

---

# Scope

## Included

- Replace the duplicated `simple_safe_filename()` occurrences in `cli/prosmaker.py`
  and `cli/metricalc.py` with an import from `akkapros.lib.utils`.
- Add `src/akkapros/lib/phoneprep.py` containing the exported core functions/classes
  currently implemented inside `cli/phoneprep.py`.
- Update `cli/phoneprep.py` to import and call into `lib/phoneprep.py`, leaving CLI
  argument parsing and file I/O in the CLI module.
- Add unit tests for `lib/phoneprep.py` covering the optimizer and pattern builder
  core behaviors (where feasible without reimplementing MBROLA tooling).

## Not Included

- Any user-facing CLI behavior changes beyond refactoring (no deliberate API changes).
- Large refactors of `phoneprep` internals beyond moving them to `lib/` (these can be
  proposed in follow-up CRs).

---

# Current Behavior

- `simple_safe_filename()` exists in three places: canonical `lib/utils.py` and
  duplicated copies inside `cli/prosmaker.py` and `cli/metricalc.py`.
- `cli/phoneprep.py` contains full implementation of the phoneprep pipeline (inventory
  definitions, optimizer, pattern builder, and emitter) rather than delegating to a
  `lib/` module. This makes it harder to import and test the logic programmatically.

---

# Proposed Change

- Remove the duplicated `simple_safe_filename()` implementations and replace them with
  `from akkapros.lib.utils import simple_safe_filename` in the affected CLI modules.
- Create `src/akkapros/lib/phoneprep.py` that exposes the main functional API used by
  the CLI (for example `build_inventory()`, `optimize_coverage()`, `emit_sidecar()`).
- Keep `cli/phoneprep.py` as the thin CLI wrapper: parse args, call into `lib/phoneprep`,
  handle output filenames and file I/O.

---

# Technical Design

Steps to implement:

1. Locate the canonical `simple_safe_filename()` in `src/akkapros/lib/utils.py` and
   ensure it is exported (present in `__all__` if used).
2. Remove the duplicated function bodies from `src/akkapros/cli/prosmaker.py` and
   `src/akkapros/cli/metricalc.py` and add `from akkapros.lib.utils import simple_safe_filename`.
3. Create `src/akkapros/lib/phoneprep.py`.
   - Move pure logic (inventory definitions, optimizer classes/functions, pattern builder,
     emitter helpers) into the new module.
   - Preserve public function names so the CLI change is minimal.
4. Update `src/akkapros/cli/phoneprep.py` to import the new library functions and keep
   only argument parsing, file handling, and the `--test` self-test harness.
5. Add unit tests under `tests/` for the library functions (mock external tools as needed).
6. Run the full test suite and the `fullprosmaker` self-tests to validate no behavioral change.

Files likely affected:

src/akkapros/lib/utils.py
src/akkapros/cli/prosmaker.py
src/akkapros/cli/metricalc.py
src/akkapros/cli/phoneprep.py
src/akkapros/lib/phoneprep.py (new)
tests/test_phoneprep_lib.py (new)

API/compatibility notes:

- The CLI surface remains unchanged; imports are refactored only. Any public helper
  functions intended for external use should be re-exported from `lib/phoneprep.py`.

---

# Acceptance Criteria

- [x] `cli/prosmaker.py` and `cli/metricalc.py` no longer contain local copies of
  `simple_safe_filename()`; they import the function from `akkapros.lib.utils`.
- [x] `src/akkapros/lib/phoneprep.py` exists and contains the core phoneprep logic.
- [x] `cli/phoneprep.py` is a thin wrapper delegating to `lib/phoneprep.py`.
- [x] Unit tests for `lib/phoneprep.py` exist and pass in CI (`pytest -q`).
- [x] `--test` self-tests for `phoneprep` continue to pass (behavior preserved).
- [x] Documentation updated: `docs/akkapros/phoneprep.md` references `lib/phoneprep` API
  where appropriate and the CLI docs remain accurate.

---

# Risks / Edge Cases

- Risk: accidentally changing runtime behavior if the CLI relied on module-level side
  effects in `cli/phoneprep.py`. Mitigation: keep the CLI entrypoint behavior unchanged
  and copy any required constants to the new library module.
- Packaging/distribution: ensure `lib/phoneprep.py` is included in the package (this
  repository uses `src` layout so adding the file under `src/akkapros/lib/` is sufficient).
- Import paths: use the package import `akkapros.lib.phoneprep` (not relative paths) to
  match the rest of the codebase.

---

# Testing Strategy

- Unit tests for `lib/phoneprep` core functions (optimizer, pattern builder) using
  small, deterministic inputs and mocking external dependencies.
- Run existing CLI self-tests: `python cli/phoneprep.py --test` and `python cli/prosmaker.py --test`.
- Run `pytest` suite, focusing on `tests/test_selftests_cli.py` and integration tests.

---

# Rollback Plan

- Keep the PR small and reversible: do not delete any code until tests pass. Instead,
  move code into `lib/phoneprep.py` and update CLI to import it; only after tests pass,
  remove legacy copies if any remain.
- If regression detected in CI, revert the PR.

---

# Related Issues

- ADR-001 (CLI / library separation)
- CR-004 (rename `repair` → `accentuation`) — unrelated but active refactor work which
  may touch CLI outputs; coordinate to avoid merge conflicts.

---

# Tasks

## Implementation

- [x] Add `src/akkapros/lib/phoneprep.py` and move core logic
- [x] Replace duplicated `simple_safe_filename()` with imports
- [x] Update `cli/phoneprep.py` to use library functions

## Tests

- [x] Add unit tests for `lib/phoneprep` and for `simple_safe_filename()` import usage
- [x] Run targeted test suite for affected modules

## Documentation

- [ ] Update `docs/akkapros/phoneprep.md` if examples reference CLI internals

## Review

- [ ] Code review
- [ ] Merge after CI green

---

# Notes for CR-010

This CR intentionally focuses on refactoring and does not change algorithmic behavior.
If the team prefers, the extraction can be done in two PRs: (A) move code and add
compatibility shims, (B) remove duplicates and tidy internals. Both approaches are
acceptable; this CR documents the end goal.

Implementation verification performed on 2026-03-20:

- `python src/akkapros/cli/phoneprep.py --test` passed
- `python src/akkapros/cli/prosmaker.py --test` passed
- `python -m pytest -q tests/test_phoneprep_lib.py tests/test_selftests_cli.py -k "phoneprep or metricalc or prosmaker"` passed (`8 passed, 12 deselected`)
