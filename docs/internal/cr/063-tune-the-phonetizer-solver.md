---
cr_id: CR-063
status: Done
priority: High
impact: Mutative
created: 2026-04-15
updated: 2026-04-17
implements: ADR-046, REQ-031, REQ-033, REQ-035
---

# Change Request: Tune the phonetizer solver

## Summary

This CR is the single merged solver-tuning record for the phonetizer Phase 2
development effort.

The merged contract covers the connected set of changes made in one solver pass:

- clarified step order and drift-aware accentuation distribution
- updated the default timing reference to `cvc_reference = 306`
- capped ordinary non-accentual long-vowel extension at
  `very_long_min - 1`
- preserved residual mismatch as drift when that cap is reached
- restored hard-coded beat folding as part of the solver rather than as a user
  option
- defined mini pauses against equivalent beat checkpoints for both ahead and
  behind drift when a legal mini duration exists
- deferred beat folding until the prosodic-unit-final `F` boundary so merged
  units preserve their theoretical moraic length until completion

This record fully absorbs the temporary split that had briefly been described
across CR-064 through CR-066.

## Motivation

- Prevent repeated implementation drift caused by under-specified solver prose.
- Keep the public algorithm description aligned with the actual rhythm model
  based on `cvc_reference` checkpoints.
- Separate ordinary long-vowel recovery from accentual very-long outcomes.
- Make beat folding and mini-pause behavior understandable as one connected
  synchronization system.
- Preserve the moraic integrity of merged prosodic units by forbidding internal
  fold points before the closing `F` boundary.

## Scope

### Included

- Rewrite and stabilize the solver contract in
  `docs/akkapros/phonetizer-algorithm.md`.
- Update the default timing-reference contract to `cvc_reference = 306`.
- Define drift-aware accentuation increment routing and rounding.
- Define shortest-path beat folding modulo the current `cvc_reference`.
- Cap ordinary non-accentual long-vowel extension at `very_long_min - 1`.
- Keep residual mismatch in drift when the long-vowel cap prevents full local
  recovery.
- Remove the temporary `drift_rotate` user-policy surface and treat beat
  folding as hard-coded solver logic.
- Define mini-pause insertion as equivalent-checkpoint synchronization.
- Defer beat folding to the prosodic-unit-final `F` boundary.
- Update related phone-file documentation and required unit-test coverage.

### Not Included

- New behavior outside the phonetizer solver and its downstream phone-row
  contract.
- Changes to punctuation-owned pause bands beyond their interaction with the
  tuned solver.
- Reopening the accepted architecture of the phonetizer pipeline itself.

## Current Behavior

Repository inspection for the merged solver-tuning effort showed that the live
runtime, tests, and documentation were converging through one connected set of
changes rather than four independent design efforts.

The affected code and documentation paths included:

- `src/akkapros/lib/phonetize.py`
- `src/akkapros/config/default.yaml`
- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `tests/test_phonetize_lib.py`
- selected integration and metrics gold tests

The resulting behavior forms one coherent solver contract and is better
maintained as one merged CR.

## Proposed Change

The phonetizer solver contract shall be documented and maintained as one tuned
runtime model with the following rules.

### A) Step order and drift-aware accentuation

The public algorithm must define an explicit step order covering:

1. baseline segment assignment
2. drift computation from the `cvc_reference` timeline
3. ordinary long-vowel correction only when the nucleus is long
4. drift-aware accentuation increment distribution with
   `AA = round_half_up(0.5 * cvc_reference) - drift_portion`
5. beat folding at the prosodic-unit-final fold point
6. mini-pause eligibility and pause realization

Accentuation routing remains structure-specific and deterministic for `C:V`,
`CVV:`, `CVC:`, and `CVV:C`, including legality spillover and residual-drift
handling.

### B) Default timing reference and rounding

The tuned default timing reference is:

- `phonetize.process.timing_model.durations.cvc_reference = 306`

Rounding of half-foot and one-and-half-foot values is performed at the
target-computation level using `round_half_up`.

### C) Ordinary non-accentual long-vowel cap

For `CVV` and `CVVC` syllables where the long vowel is not accentuated:

- ordinary recovery may use the long vowel as flexible space
- extension must stop at `very_long_min - 1`
- any unresolved remainder after that cap stays in drift

This restriction applies to ordinary recovery only. It does not redefine the
broader legality space for accent-bearing long-vowel outcomes.

### D) Hard-coded beat folding

Beat folding is part of the solver itself, not a user option.

Folding is always modulo the current `cvc_reference`:

- if `drift > +round_half_up(0.5 * cvc_reference)`, normalize with
  `drift <- drift - cvc_reference`
- if `drift < -round_half_up(0.5 * cvc_reference)`, normalize with
  `drift <- drift + cvc_reference`

Equivalent checkpoints are therefore separated by integer multiples of the
current `cvc_reference`.

### E) Mini-pause synchronization

Mini pauses remain non-punctuation recovery gaps evaluated only at plain `F`
boundaries followed by another syllable.

Their timing follows the same equivalent-checkpoint logic:

- for negative drift, target `0`
- for positive drift, target `+cvc_reference`
- insert a mini pause only when the exact needed duration lies inside the legal
  mini band

### F) Deferred fold point for merged units

Beat folding must not happen inside a merged prosodic unit.

For internal syllables with boundary codes such as `L`, `X`, `E`, or `I`:

- raw drift is carried forward
- no fold is applied yet

For the closing syllable whose final row has `boundary = 'F'`:

- the syllable is completed first
- only then is the completed-unit drift folded into the canonical interval

This preserves the theoretical moraic length of the full merged unit until the
prosodic unit is actually complete.

## Technical Design

Normative implementation-facing documentation must keep the following aligned:

- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `src/akkapros/config/default.yaml`
- solver-facing tests that use numbered path identifiers

The merged CR requires the algorithm page to explain:

- step order
- accentuation routing
- long-vowel cap semantics
- modulo-beat folding
- equivalent-checkpoint mini pauses
- deferred fold point at `F`
- the `DEBUG_CHRONO` checkpoint invariant

## Files Likely Affected

- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/config/default.yaml`
- `tests/test_phonetize_lib.py`
- selected integration and metrics gold tests

## Acceptance Criteria

- [x] The algorithm documentation explicitly defines the tuned step order,
      including drift-aware accentuation and the unit-final fold point.
- [x] The default timing reference in the relevant solver documentation is
      `cvc_reference = 306`.
- [x] Ordinary non-accentual long-vowel extension is documented and verified as
      capped at `very_long_min - 1`, with residual mismatch preserved in drift.
- [x] Beat folding is documented and verified as hard-coded solver behavior,
      not a user-configurable option.
- [x] Mini-pause synchronization is documented and verified for equivalent beat
      checkpoints, including the positive-drift case targeting the next
      checkpoint.
- [x] Beat folding is documented and verified as deferred until the
      prosodic-unit-final `F` boundary.
- [x] The phone-file guide explains how raw drift may appear on internal
      merged-unit boundaries while folded drift appears at completed-unit
      checkpoints.
- [x] Numbered path tests cover the tuned solver rules.

## Risks / Edge Cases

- Solver prose can drift again if future edits describe fold timing, mini-pause
  targeting, or long-vowel legality independently instead of as one connected
  system.
- Gold metrics and integration expectations may need refresh whenever the tuned
  solver changes emitted timing.
- Readers may incorrectly assume equivalent checkpoints are interchangeable
  across different `cvc_reference` values; the modulo relation is always with
  the current active reference only.

## Testing Strategy

The merged solver CR relies on:

- numbered path tests in `tests/test_phonetize_lib.py`
- focused integration checks for emitted phone rows and mini pauses
- metrics gold verification where solver timing affects downstream outputs
- explicit documentation checks during CR review

## Related

- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- [REQ-033](../req/033-phonetizer-pause-bands-and-pause-metrics-reporting.md)
- [REQ-035](../req/035-phonetizer-phase2-path-complete-unit-test-coverage.md)

## Notes

- This merged CR replaces the temporary documentation split that had briefly
  described parts of the same solver-tuning effort separately.