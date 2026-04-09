---
cr_id: CR-041
status: Done
priority: Medium
impact: Additive
created: 2026-04-09
updated: 2026-04-09
implements: 'ADR-041, REQ-026, REQ-031'
---

# Change Request: Add phonetizer Phase 2 follow-up docs and test coverage

# Summary

Add focused follow-up documentation and test coverage for the implemented
phonetizer Phase 2 runtime.

This CR exists for two reasons: it closes the internal CR numbering gap after
CR-040 without renumbering later records, and it captures a small additive
follow-up that strengthens the repository's explanation and verification of the
new Phase 2 duration solver without reopening the Phase 2 behavior contract.

---

# Motivation

[CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
implemented the Phase 2 runtime itself. A smaller follow-up is still useful to:

- expand phonetizer-algorithm documentation with concrete worked examples
- pin additional representative tests around pause discharge, drift reporting,
  and edge-case interpretation
- keep the internal CR numbering contiguous without the higher-risk renumbering
  of CR-042 and later references

This CR does not redefine the solver. It documents and tests the accepted
behavior more explicitly.

---

# Scope

## Included

- Add follow-up user-facing documentation for the implemented Phase 2
  phonetizer behavior.
- Add or refine tests for representative Phase 2 edge cases that improve
  confidence in the accepted runtime model.
- Clarify examples around drift carry, short-pause discharge, long-pause reset,
  and same-consonant handling where current docs remain terse.

## Not Included

- Redefining the Phase 2 solver contract from CR-040.
- Adding shared semantic config verification or phonetizer preflight. That work
  remains owned by [CR-042](042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md).
- Reopening accepted ADR or REQ behavior.

---

# Current Behavior

The repository now contains an implemented Phase 2 phonetizer runtime, but its
explanatory material and regression coverage can still be improved in targeted
ways without changing runtime behavior.

There is also an internal documentation numbering gap between CR-040 and
CR-042. This CR closes that gap with a legitimate narrow follow-up instead of a
bulk renumber.

---

# Proposed Change

- Expand the phonetizer algorithm documentation with at least one worked
  example showing baseline realization and one worked example showing drift
  discharge through pauses.
- Add representative tests for currently under-explained but accepted behavior,
  especially around:
  - short-pause versus long-pause drift handling
  - drift summary emission
  - same-consonant follow-up cases
- Keep all new material additive and consistent with ADR-041, REQ-026, and
  REQ-031.

---

# Technical Design

Architecture notes:

Components:
- phonetizer user docs under `docs/akkapros/`
- phonetizer tests under `tests/`
- internal cross-references under `docs/internal/`

Implementation constraints:
- no runtime contract change
- no new policy surface
- no migration of CR-042 verification scope into this CR

---

# Files Likely Affected

`docs/akkapros/phonetizer.md`
`docs/akkapros/phonetizer-algorithm.md`
`tests/test_phonetize_lib.py`
`tests/test_integration.py`
`docs/internal/cr/index.md`

---

# Acceptance Criteria

- [x] Follow-up documentation adds concrete examples for implemented Phase 2
      timing behavior without redefining the runtime contract.
- [x] Test coverage is extended for at least one short-pause case, one
      long-pause case, and one drift-reporting case.
- [x] The new documentation and tests remain consistent with CR-040, ADR-041,
      REQ-026, and REQ-031.
- [x] CR-042 ownership of shared semantic config verification remains explicit.

---

# Risks / Edge Cases

Possible issues:

- follow-up docs may accidentally restate behavior inconsistently with CR-040
- added tests may overfit one implementation detail instead of the accepted
  contract
- reviewers may misread this CR as reopening Phase 2 design rather than
  documenting and hardening it

---

# Testing Strategy

Unit tests:

- extend targeted phonetizer-library tests for pause and drift cases

Integration tests:

- extend one representative CLI-generated dual-output scenario if needed

Manual review:

- compare added examples against the accepted CR-040 wording

---

# Rollback Plan

If the follow-up documentation or tests prove misleading, revert the additive
documentation and regression changes without touching the accepted CR-040
runtime behavior.

---

# Related Issues

- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [CR-042](042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md)
- [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
- [REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)

---

# Tasks

## Implementation

- [x] Add follow-up phonetizer Phase 2 documentation examples
- [x] Add targeted regression tests for pause and drift cases

## Tests

- [x] Verify the added tests pass with the accepted Phase 2 runtime

## Documentation

- [x] Cross-check wording against CR-040 and ADR-041

## Review

- [x] Verify acceptance criteria

---

# Notes for CR-041

- This CR is intentionally additive.
- This CR closes the numbering gap between CR-040 and CR-042 without requiring
  renumbering of later records.