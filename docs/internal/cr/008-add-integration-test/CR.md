# Change Request: Add end-to-end integration test with gold-standard metrics

CR-ID: CR-008
Status: Draft
Priority: High
Created: 2026-03-20
Updated: 2026-03-20
Implements: ADR-025

---

# Summary

Add a reproducible end-to-end integration test that runs the full processing
pipeline (ATF parse → syllabify → prosody realization → metrics → printer)
on a small, pinned sample and asserts key gold-standard outputs: a pinned
VarcoC value (within tolerance), an expected accentuation rate, and a sample
line of `_tilde.txt` output. The test should live at
`tests/test_integration.py`.

**Related ADR:** [ADR 025: Integration Test Coverage for CLI and Outputs](docs/internal/adr/025-integration-test-coverage.md)

---

# Motivation

Unit/self-tests validate individual stages, but regressions that span stages can
remain undetected. A single, small end-to-end test will catch pipeline
integration issues (format/IO regressions, pivot-format changes, merge logic
breakage) and provide a reproducible regression test with pinned expected
metrics.

---

# Scope

## Included

- Add `tests/test_integration.py` with an idempotent test that runs the pipeline
  on a short sample from `data/samples/` and asserts metrics and a sample
  `_tilde.txt` line.
- Document the gold-standard values and acceptable tolerances in the test.
- Ensure the test can run in CI without network access and uses repository
  sample data only.

## Not Included

- Extensive new fixtures or heavy test data. Keep the sample small (≈5–10
  lines), using an existing sample file where possible.

---

# Current Behavior

No end-to-end integration test exists. Cross-stage regressions have to be found
manually or via user reports; the CI suite only runs per-module self-tests and
unit tests.

---

# Proposed Change

- Add `tests/test_integration.py` containing one or two integration tests:
  - `test_pipeline_end_to_end()` runs the pipeline and asserts VarcoC and
    accentuation rate (within tolerances) and checks for a canonical line in
    the produced `_tilde.txt` output.
  - Optionally, `test_pipeline_idempotent()` asserts that running the pipeline
    twice produces the same `_tilde.txt` output.
- Use temporary directories for outputs and clean up after test.

---

# Technical Design

Implementation notes:

- Prefer importing library entry points (e.g., `akkapros.lib.atfparser`,
  `akkapros.lib.syllabify`, `akkapros.lib.prosmaker`, `akkapros.lib.metrics`) and
  invoking the library functions rather than shelling out to CLIs. This makes
  tests faster and avoids shell dependency on platform-specific entrypoints.
- Use an existing small sample such as
  `data/samples/L_I.5_Erra_and_Isum_SB_I.atf` scaled down to a short excerpt or
  create a test fixture that contains 3–6 lines derived from it.
- Pin expected metrics (VarcoC, accentuation rate) and set tolerances (e.g.,
  ±2.5 for VarcoC, ±1.5% for accentuation rate) to avoid brittle failures.

Example assertions:

- `assert abs(result['varco_c'] - GOLD_VARCOC) < 2.5`
- `assert abs(result['accentuation_rate_pct'] - GOLD_ACC_RATE) < 1.5`
- `assert expected_line in produced_tilde_lines`

---

# Files Likely Affected

tests/test_integration.py
docs/internal/cr/008-add-integration-test/CR.md
docs/internal/cr/008-add-integration-test/tasks.md

---

# Acceptance Criteria

- [ ] `tests/test_integration.py` exists and runs in CI.
- [ ] The test asserts VarcoC within the prescribed tolerance.
- [ ] The test asserts accentuation rate within the prescribed tolerance.
- [ ] The test checks for a canonical `_tilde.txt` sample line.

---

# Risks / Edge Cases

- The gold-standard numbers may need updating if upstream algorithm changes are
  intentionally made; keep values documented and reviewable.
- Running full pipeline in tests can be slower; keep the sample small to limit
  test runtime.

---

# Testing Strategy

- Add the test as a standard pytest test under `tests/`.
- Run locally and in CI; if the test increases CI time noticeably, mark it as
  a separate slow test or gate it behind an environment variable.

---

# Rollback Plan

- Remove or mark the test as skipped if it proves too brittle or slows CI
  unacceptably.

---

# Related Issues

- See review-001 recommendations (docs/internal/reviews/001-review.md)
