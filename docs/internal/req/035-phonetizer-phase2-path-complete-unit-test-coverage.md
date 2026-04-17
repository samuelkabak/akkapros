---
req_id: REQ-035
status: Implemented
priority: High
impact: Mutative
created: 2026-04-16
updated: 2026-04-17
related_adrs: 'ADR-046, ADR-041'
implemented_by: 'CR-063'
---

# Requirement: Phonetizer Phase 2 Path-Complete Unit Test Coverage

## Summary

The repository shall include unit tests that cover all decision paths in the
Phase 2 phonetizer timing solver, based on the clarified algorithm contract in
CR-063.

Coverage is path-complete, not line-count based. The goal is to ensure every
branch and legality rule in the step order, beat normalization, accentuation
distribution, pause realization, and drift-token semantics has explicit test
evidence.

---

## Motivation

The phonetizer algorithm combines multiple interacting controls (normalization,
long-vowel correction, accent distribution, mini pauses, punctuation pauses,
and drift encoding). Missing one branch allows regressions that are difficult to
notice from aggregate metrics alone.

Path-complete unit tests reduce implementation ambiguity, prevent silent
behavior drift, and provide reproducible checks for future maintenance.

---

## Acceptance Criteria

*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [x] Given a unit produces `drift_after_assignment` inside
      `[-round_half_up(0.5*cvc_reference), +round_half_up(0.5*cvc_reference)]`,
      when normalization is applied, then drift remains unchanged.
- [x] Given `drift_after_assignment > round_half_up(0.5*cvc_reference)`, when
      normalization is applied, then drift is reduced by exactly one
      `cvc_reference`.
- [x] Given `drift_after_assignment < -round_half_up(0.5*cvc_reference)`, when
      normalization is applied, then drift is increased by exactly one
      `cvc_reference`.
- [x] Given drift equals exactly the positive or negative normalization
      threshold, when normalization is applied, then no branch triggers.
- [x] Given `abs(drift_after_assignment) <= drift_tolerance`, when the solver
      runs ordinary correction, then long-vowel correction is skipped.
- [x] Given `abs(drift_after_assignment) > drift_tolerance` and nucleus is long,
      when ordinary correction runs, then the nucleus is adjusted inside legal
      long-vowel bounds and absolute drift decreases or remains unchanged when
      no legal room exists.
- [x] Given nucleus is short, when ordinary correction runs, then the short
      vowel duration remains unchanged.
- [x] Given accentuation is inactive for a unit, when the unit is solved, then
      no accent increment is applied.
- [x] Given accentuation is active and shape is `C:V`, when routing is applied,
      then primary and adjacent target segments match CR-063 mapping.
- [x] Given accentuation is active and shape is `CVV:`, when routing is applied,
      then primary and adjacent target segments match CR-063 mapping.
- [x] Given accentuation is active and shape is `CVC:`, when routing is applied,
      then primary and adjacent target segments match CR-063 mapping.
- [x] Given accentuation is active and shape is `CVV:C`, when routing is
      applied, then primary and adjacent target segments match CR-063 mapping.
- [x] Given accentuation is active, when increment quantity is computed, then
      `AA = round_half_up(0.5*cvc_reference) - drift_portion` is used.
- [x] Given policy `100_0`, when accent increment is distributed, then all legal
      consumable increment is attempted on the primary segment first.
- [x] Given policy `85_15`, when accent increment is distributed, then initial
      share targets are 85% primary and 15% adjacent before legality spillover.
- [x] Given policy `70_30`, when accent increment is distributed, then initial
      share targets are 70% primary and 30% adjacent before legality spillover.
- [x] Given the primary target cannot absorb its planned share due to legality,
      when distribution runs, then residual increment is transferred to adjacent
      target if legal capacity exists.
- [x] Given both primary and adjacent targets saturate legally before full
      increment is consumed, when distribution completes, then residual remains
      in drift and no illegal duration is emitted.
- [x] Given a consonant is the accent target, when legality is evaluated, then
      class mapping (`closure`, `fricative`, `sonorant`, hiatus-as-closure,
      transition-as-sonorant) is enforced.
- [x] Given a consonant receives an adjacent-share increment only, when legality
      is evaluated, then singleton-preservation threshold is respected.
- [x] Given a same-consonant coda/onset chain is present, when consonant
      elongation is applied, then pairwise ceiling handling follows the contract
      and does not exceed legal totals.
- [x] Given mini pause conditions are all true, when boundary is evaluated, then
      exactly one mini pause may be inserted at that boundary.
- [x] Given any mini pause precondition is false (drift sign, magnitude,
      boundary type, or next-unit type), when boundary is evaluated, then no
      mini pause is inserted.
- [x] Given a short punctuation pause, when duration is selected, then chosen
      value is legal and nearest-discharge in band.
- [x] Given a long punctuation pause, when duration is selected, then chosen
      value is legal and nearest-discharge in band.
- [x] Given pause band cannot discharge drift to zero, when duration is
      selected, then pause is clamped in band and residual drift is carried.
- [x] Given row-level drift tokens are emitted, when unit is non-final row,
      then last completed-unit drift token is preserved.
- [x] Given row-level drift tokens are emitted, when unit closes, then emitted
      token matches post-unit drift using signed three-digit format.
- [x] Given half-value rounding inputs (for example `2.5`), when half-up
      rounding is used by timing references and `AA`, then result rounds upward
      (for example `3`).
- [x] Given implementation PR updates phonetizer behavior, when unit tests run,
      then all above path categories are represented by explicit named tests.

---

## User Story (optional)

> As a maintainer of the phonetizer, I want branch-complete unit tests for
> Phase 2 so that future updates cannot silently change timing behavior.

---

## Interface Notes

- Input focus: row-level units and config combinations that trigger each branch.
- Output focus: durations, drift transitions, pause decisions, and drift tokens.
- Affected components:
  - `src/akkapros/lib/phonetize.py`
  - `tests/test_phonetize_lib.py`
  - `tests/test_integration.py`

---

## Open Questions

- [ ] Should path coverage be enforced by a dedicated marker or naming
      convention (for example `test_path_*`) in addition to behavioral checks?

---

## Implementation Notes (optional)

- Owner: maintainer
- Estimated effort: medium
- Migration: existing tests may be retained but must be expanded to satisfy
  path-complete criteria listed above.

## Related

- Related ADRs: [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md), [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- Implementation CRs: [CR-063](../cr/063-clarify-phonetizer-step-order-accentuation-and-beat-folding.md)

## Non-Goals

- This requirement does not itself implement runtime code changes.
- This requirement does not replace integration tests; it defines required unit
  path coverage.
- This requirement does not define coverage by percentage thresholds.

## Security / Safety Considerations

- Deterministic tests for all control paths reduce safety risk from unnoticed
  timing regressions and ambiguous algorithm interpretation.
