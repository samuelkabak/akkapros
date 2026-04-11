---
cr_id: CR-054
status: Done
priority: Medium
impact: Additive
created: 2026-04-11
updated: 2026-04-12
implements: 'REQ-030'
---

# Change Request: Add Single-Line Manual Metrics Verification Test

## Summary

Add a dedicated metrics regression test that uses the single Akkadian input line
`šazu šuḫgurim ina rebî : šākin tašmê ana ilī abbīšu` as the only textual
fixture and validates the active metrics indicator set against manually derived
reference values.

The goal is not just to check that indicator labels appear in table output. The
goal is to lock one concrete end-to-end sample where the expected metrics are
explained outside the implementation under test and then compared against the
program's current phone/ophone-driven computation path.

---

## Motivation

The repository already contains metrics coverage, but the current tests do not
provide the exact evidence requested here:

- no existing test uses this exact sample line as the sole textual input
- no existing end-to-end test locks the full indicator block to a manually
  documented reference calculation for this sample
- the current strongest manual-value metrics test is a low-level synthetic row
  case, not a real Akkadian line carried through the active rhythm pipeline

That leaves a gap between the formulas approved in REQ-030 and a human-audited
reference example that future maintainers can inspect when the metrics code is
changed.

---

## Scope

### Included

- Add a focused automated metrics test for the single textual fixture
  `šazu šuḫgurim ina rebî : šākin tašmê ana ilī abbīšu`.
- Define expected values from manually documented reference arithmetic rather
  than by regenerating expectations through the same metrics implementation.
- Validate the active metrics indicator set for the sample, including:
  `%C`, `%V`, `meanC`, `meanV`, `ΔC`, `ΔV`, `VarcoC`, `VarcoV`, `rPVI-C`,
  `nPVI-V`, and drift summary fields.
- Keep the reference documentation in a dedicated user-facing verification page
  under `docs/akkapros/` so users and maintainers can inspect how the expected
  values were obtained.
- Require that the user-facing verification page explicitly lists every timing
  parameter used by the sample so a reader can recompute the metrics manually
  without needing to inspect hidden defaults in source code or config files.

### Not Included

- Redesigning the metrics formulas or the phone/ophone input contract.
- Broad replacement of the existing metrics test suite.
- Treating this one sample as the only required metrics coverage.

---

## Current Behavior

Current tests already cover several parts of the metrics contract:

- `tests/test_metrics_stats.py` checks that the metrics table surfaces the
  active indicator labels and reflects computed result fields.
- `tests/test_metrics_stats.py` also includes one manual synthetic
  `compute_interval_metrics()` row example with hand-checkable values.
- integration coverage checks selected metrics behavior on broader corpora.

However, there is currently no automated test that:

- starts from this exact textual sample line
- derives the active phone/ophone-based metrics path for that one line
- compares the resulting indicators against manually documented reference
  values for the full requested indicator set

---

## Proposed Change

- Add a new automated test in the metrics test suite for the exact sample line.
- Keep the textual fixture limited to:

  `šazu šuḫgurim ina rebî : šākin tašmê ana ilī abbīšu`

- Drive the sample through the active repository behavior needed to obtain the
  metrics inputs under REQ-030.
- Compare the computed indicators with fixed expected values copied from a
  manually reviewed verification document rather than from helper functions in
  the metrics implementation.
- Treat drift verification as a passthrough/frontmatter contract check when the
  test is implemented, consistent with REQ-030.

---

## Technical Design

Architecture notes:

Components:

- `tests/test_metrics_stats.py` or a new narrow metrics test module
- `src/akkapros/lib/metrics.py`
- active upstream helpers needed to produce paired phone/ophone inputs for the
  sample under the current contract
- `docs/akkapros/varco-verification.md`

Verification design:

- the manual reference source is the fixed interval arithmetic documented in
  `docs/akkapros/varco-verification.md`
- expected values must be hard-coded in the automated test once approved
- the automated test must not compute its expected values by calling the same
  metrics formulas under test
- if the test needs to derive phone/ophone rows from the sample line at runtime,
  that derivation is acceptable so long as the asserted metrics values remain
  fixed and manually sourced
- the public verification page must enumerate the timing parameters and runtime
  assumptions used for the sample, including the effective phonetizer timing
  settings that determine the emitted interval durations

---

## Files Likely Affected

tests/test_metrics_stats.py
docs/akkapros/varco-verification.md
docs/internal/cr/054-add-single-line-manual-metrics-verification-test.md

---

## Acceptance Criteria

- [x] The repository contains an automated metrics regression test for the exact
      textual fixture `šazu šuḫgurim ina rebî : šākin tašmê ana ilī abbīšu`.
- [x] The test validates the active indicator set for the sample: `%C`, `%V`,
      `meanC`, `meanV`, `ΔC`, `ΔV`, `VarcoC`, `VarcoV`, `rPVI-C`, `nPVI-V`,
      and drift summary fields.
- [x] The expected values asserted by the test are copied from a manually
      documented reference calculation and are not regenerated by the metrics
      implementation under test.
- [x] The user-facing verification page `docs/akkapros/varco-verification.md`
  explains the sample, the interval lists, the formulas, the manual
  arithmetic, and the program outputs used to justify the test expectations.
- [x] The user-facing verification page `docs/akkapros/varco-verification.md`
  lists all timing parameters and effective runtime assumptions used for
  the sample so a user can redo the computation independently.
- [x] The implementation remains aligned with REQ-030's phone/ophone-only
      metrics contract.

---

## Risks / Edge Cases

Possible issues:

- upstream prosody or phonetizer behavior may change the sample's interval lists
  even when the metrics formulas themselves remain stable
- drift values are sourced from phonetizer/frontmatter rather than recomputed
  from interval lists, so the automated test must distinguish formula checks
  from passthrough checks
- a one-line sample is useful for verification clarity but may still be too
  small to detect every regression pattern
- if the public page omits effective timing parameters or leaves them implicit,
  users will not be able to reproduce the interval arithmetic from the document
  alone

---

## Testing Strategy

Unit/regression tests:

- add one focused test for the exact textual fixture
- assert the fixed expected metric values to at least the precision already used
  elsewhere in the suite
- keep the sample and asserted values stable so future changes surface as a real
  review event

Manual verification:

- use `docs/akkapros/varco-verification.md` as the public reference record for
  why the expected values are correct
- ensure that page states the timing inputs explicitly enough that a user can
  recompute the interval durations and derived indicators without reading the
  implementation

---

## Rollback Plan

If the sample proves unstable because upstream contracts are still moving,
revert the automated test and keep the verification note while a narrower,
more durable fixture is chosen in a follow-up CR.

---

## Related Issues

- [CR-046](046-redesign-metricalc-around-phone-ophone-interval-metrics.md)
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md)
- public verification page: `docs/akkapros/varco-verification.md`

---

## Tasks

### Implementation

- [x] Add the single-line automated metrics verification test
- [x] Encode the fixed expected values from the manual verification note

### Tests

- [x] Run the metrics test suite after the new sample test is added

### Documentation

- [x] Keep the public verification page synchronized with the approved expected values
- [x] Document all timing parameters used by the sample on the public verification page

### Review

- [x] Verify acceptance criteria

---

## Implementation Blockers

Use this section when implementation or verification cannot proceed safely.

Leave the section empty if no blockers are known.

---

## Notes

This CR responds to a verification gap, not to evidence that the current
metrics formulas are wrong. The immediate problem is the lack of one compact,
human-auditable sample test that ties the active formulas to a real Akkadian
line under the current phone/ophone contract.

The verification artifact for this CR is intentionally user-facing. It belongs
under `docs/akkapros/`, not under `docs/internal/review/`.

For reproducibility, that public page must not rely on hidden defaults. It must
state the effective timing parameters used to produce the sample's phone/ophone
durations so a reader can redo the computation independently.

Verification completed on 2026-04-12:

- added a focused regression test to `tests/test_metrics_stats.py` for the exact
  sample line `šazu šuḫgurim ina rebî : šākin tašmê ana ilī abbīšu`
- kept the asserted metrics values fixed and manual-sourced rather than
  regenerating expected indicator values through the metrics implementation
- verified drift as a frontmatter passthrough surface by writing paired
  `_ophone.txt` and `_phone.txt` fixtures with their distinct original and
  accentuated phonetize drift summary metadata and asserting the reported
  `max`, `mean`, and `stddev` values
- added the public reference page `docs/akkapros/varco-verification.md` with
  the sample, formulas, interval lists, worked manual arithmetic for every
  indicator, raw program output, equality checks, and the effective timing
  parameters needed for independent recomputation
- ran the targeted metrics test slice to confirm the new sample test passes
