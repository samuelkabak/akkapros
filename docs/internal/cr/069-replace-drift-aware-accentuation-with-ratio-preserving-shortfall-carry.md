---
cr_id: CR-069
status: Done
priority: High
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
implements: REQ-022, REQ-027, REQ-031
---

# Change Request: Replace Drift-Aware Accentuation With Ratio-Preserving Shortfall Carry

## Summary

The live phonetizer currently reduces the accentuation increment by the drift
present at accent-distribution entry and then tries to realize the reduced
increment locally. That is the contract currently reflected in the runtime,
the default config comments, and the user-facing phonetizer algorithm page.

This CR replaces that rule with a fixed half-foot accent target that is
independent of entry drift. Accentuation must always target exactly
`round_half_up(0.5 * cvc_reference)` of extra syllable weight, distribute that
target according to the configured ratio family, and preserve the configured
ratio when legality limits prevent full local realization. Any unrecoverable
shortfall becomes additional running drift instead of reducing the requested
accent increment up front.

This CR updates the active solver contract documented in [CR-063](063-tune-the-phonetizer-solver.md)
and the timing-default surface last retuned in [CR-068](068-ratio-based-parameters.md).
CR-063 remains the historical source for the broader solver-tuning pass, and
CR-068 remains the historical source for the current timing table, but CR-069
becomes the active contract for accent-target quantity, ratio-preserving
partial realization, and the allowed/default distribution-policy family.

---

## Motivation

- Solver-contract change
- Config-default change
- Documentation and test synchronization
- Ratio-preservation clarification

The current runtime in `src/akkapros/lib/phonetize.py` computes accentuation as
`round_half_up(0.5 * cvc_reference) - drift_portion`, so the amount of accent
added to a syllable is reduced whenever drift is already present at
accent-distribution entry.

The requested rule rejects that behavior. Entry drift must still be tracked and
reported, but it must no longer shrink the intended accent increment. Instead,
the solver should attempt the full half-foot increment, preserve the chosen
distribution ratio as far as the legal capacities of the accentuated and
adjacent segments allow, and carry any remaining deficit forward in drift.

The change also requires extending the allowed policy family beyond the current
`100_0`, `85_15`, and `70_30` options so users can select finer distributions,
with `80_20` becoming the new default across runtime defaults, YAML surfaces,
help text, and documentation.

---

## Scope

## Included

- Replace the current drift-aware accent-target formula with a fixed target of
  `round_half_up(0.5 * cvc_reference)`
- Keep entry drift as runtime state, but do not subtract it from the intended
  accent increment before distribution
- Require ratio-preserving partial realization when legality limits prevent the
  full target from being assigned locally
- Define the preserved-ratio cap algorithm for all supported
  `accentuation_distribution_policy` values
- Carry the unrecoverable accent shortfall into running drift after local
  realization
- Keep the syllable-weight objective unchanged: an accentuated syllable still
  wants to gain exactly `0.5 * cvc_reference` relative to its non-accentuated
  class even when some of that target remains unrealized locally
- Extend the allowed policy inventory to:
  `100_0`, `95_05`, `90_10`, `85_15`, `80_20`, `75_25`, and `70_30`
- Change the default policy from `85_15` to `80_20`
- Update runtime defaults, schema/default-emission help, and all tracked YAML
  files carrying the phonetizer timing model
- Update affected public and internal documentation that describes the
  accentuation rule, policy inventory, or default policy
- Update tests so they pin the new default policy, the expanded allowed-value
  inventory, and ratio-preserving shortfall behavior

## Not Included

- Retuning `cvc_reference`, vowel anchors, consonant anchors, pause bands, or
  other timing defaults not directly required by the new accentuation rule
- Changing the accepted phonetizer schema shape or renaming
  `accentuation_distribution_policy`
- Reintroducing removed user-facing drift policies or pause policies
- Changing beat folding, mini-pause eligibility, or pause-band selection logic
  beyond the downstream effect of the new drift produced by accentuation

---

## Current Behavior

Repository inspection on 2026-04-18 shows the live accentuation contract is
still drift-aware in the older sense that this CR now replaces.

Observed runtime evidence in `src/akkapros/lib/phonetize.py`:

- the allowed policy family is hard-coded as only `100_0`, `85_15`, and `70_30`
- `_apply_accent_increment(...)` maps those three ratios through `share_map`
- the live target is computed as
  `total_increment = max(0.0, round_half_up(0.5 * cvc_reference) - drift_portion)`
- after the initial ratio split, the runtime may spend remaining local slack on
  the primary segment first and then again on the adjacent segment, which means
  the final realized local distribution can move away from the configured ratio
  in order to maximize local assignment

Observed config and doc evidence:

- `src/akkapros/config/default.yaml` currently documents the allowed values as
  `100_0, 85_15, 70_30`
- `src/akkapros/config/default.yaml` currently defaults
  `accentuation_distribution_policy` to `85_15`
- `docs/akkapros/phonetizer-algorithm.md` currently documents
  `AA = round_half_up(0.5 * cvc_reference) - drift_portion`
- `docs/akkapros/phonetizer-algorithm.md`, `docs/akkapros/phonetizer.md`,
  `docs/akkapros/fullprosmaker.md`, and `docs/akkapros/varco-verification.md`
  currently describe or expose the older policy inventory and default

This means the live repository still treats drift as a quantity that reduces
the accent target before distribution and still treats ratio policy as an
initial preference that may be abandoned in favor of any additional legal local
slack.

---

## Proposed Change

The phonetizer shall treat accentuation as a fixed half-foot target plus a
ratio-preserving legality cap.

### A) Fixed accent target independent of entry drift

For any accentuated syllable, define:

- `accent_target = round_half_up(0.5 * cvc_reference)`

Normative rules:

- the solver must not subtract `entry_drift`, `drift_portion`, or any other
  drift value from `accent_target` before ratio distribution begins
- entry drift remains part of runtime state and must still contribute to the
  post-syllable drift computation after durations are emitted
- the syllable-level objective remains the baseline syllable target plus the
  full `accent_target`, even when the full target cannot be realized locally

### B) Ratio-preserving partial realization

Let the configured policy provide shares `(p_primary, p_adjacent)` with
`p_primary + p_adjacent = 1.0`.

Let:

- `primary_capacity` be the legal additional space on the accentuated segment
- `adjacent_capacity` be the legal additional space on the adjacent segment
  under the existing legality rules for that syllable shape; if there is no
  adjacent segment, treat the adjacent share as unavailable

The solver must compute the largest realizable total increment
`realizable_increment` that preserves the configured ratio:

- if both shares are non-zero, then
  `realizable_increment` is the minimum of:
  `accent_target`, `primary_capacity / p_primary`, and
  `adjacent_capacity / p_adjacent`
- if the adjacent share is zero, then `realizable_increment` is the minimum of
  `accent_target` and `primary_capacity`
- if the primary share is non-zero and there is no legal adjacent segment for a
  non-zero adjacent share, then only the largest total consistent with the full
  configured ratio is realizable, which may be `0` when the ratio requires a
  non-zero adjacent contribution that cannot legally exist

The emitted local gains are then:

- `primary_gain = realizable_increment * p_primary`
- `adjacent_gain = realizable_increment * p_adjacent`

Normative rules:

- the solver must not assign extra overflow to the primary or adjacent segment
  in a way that breaks the configured ratio merely to consume more local slack
- the preserved ratio governs the realized local pair whenever a non-zero total
  is assigned
- legality checks remain unchanged: short vowels must remain short, long vowels
  may extend only within their legal accentual range, and singleton consonants
  may rise only inside their legal geminate-like range

### C) Shortfall becomes drift

Define:

- `accent_shortfall = accent_target - realizable_increment`

Normative rules:

- `accent_shortfall` must be added to the running drift as unrealized timing
  debt from the accent target
- under the current sign convention, an unrealized positive target increases
  ahead-of-beat deficit, so the resulting drift update must be equivalent to
  subtracting `accent_shortfall` from the post-accent local drift result
- the solver must not fail merely because the full accent target cannot be
  realized locally if the preserved-ratio maximum legal increment has been
  assigned correctly and the remaining mismatch is carried in drift
- `drift_tolerance` continues to govern the final mismatch check after the new
  drift value is computed; this CR does not remove the tolerance gate

### D) Allowed ratios and default

The allowed `accentuation_distribution_policy` inventory becomes:

- `100_0`
- `95_05`
- `90_10`
- `85_15`
- `80_20`
- `75_25`
- `70_30`

The default becomes:

- `phonetize.process.timing_model.accentuation_distribution_policy = 80_20`

### E) Surface synchronization

The following surfaces must be updated together in the same implementation
slice:

- runtime internal defaults and validation inventory in
  `src/akkapros/lib/phonetize.py`
- the canonical YAML default file in `src/akkapros/config/default.yaml`
- the tracked YAML examples in
  `demo/akkapros/lexlinks/construct-demo.yaml` and
  `demo/akkapros/prosmaker/corpus-demo.yaml`
- public phonetizer documentation that enumerates the policy family, default,
  or accentuation algorithm
- affected internal records that explicitly describe the superseded
  drift-aware formula
- unit and integration tests that pin the default, the allowed inventory, or
  accentuation-path timing outputs

---

## Technical Design

Implementation-facing documentation and tests must align on the following
algorithmic contract.

1. Realize the baseline syllable and compute the pre-accent local drift exactly
   as before.
2. Compute `accent_target = round_half_up(0.5 * cvc_reference)` with no drift
   subtraction.
3. Resolve legal capacities for the accentuated and adjacent segments using the
   existing class and syllable-shape legality rules.
4. Compute the largest realizable total increment that preserves the configured
   ratio.
5. Apply only that preserved-ratio increment locally.
6. Compute `accent_shortfall = accent_target - realizable_increment`.
7. Carry the shortfall into the running drift instead of failing the syllable
   merely because the full accent target was not locally realizable.
8. Continue with existing drift folding, mini-pause eligibility, and final
   tolerance checks.

Required design consequences:

- the old runtime branch that spends leftover slack on the primary and then the
  adjacent segment after the initial share split must be replaced, because it
  violates the preserved-ratio rule
- schema/default validation must accept the four newly added ratio strings
- config help, CLI docs, and YAML comments must show `80_20` as the default and
  the full seven-value inventory as the allowed set
- solver-facing tests must pin both full-success and partial-success cases,
  including a case where preserved-ratio scaling limits the total local
  increment below what an unconstrained greedy spill would have assigned

---

## Files Likely Affected

- `docs/internal/cr/069-replace-drift-aware-accentuation-with-ratio-preserving-shortfall-carry.md`
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/config/default.yaml`
- `demo/akkapros/lexlinks/construct-demo.yaml`
- `demo/akkapros/prosmaker/corpus-demo.yaml`
- `tests/test_config_support.py`
- `tests/test_phonetize_lib.py`
- `tests/test_integration.py`
- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer.md`
- `docs/akkapros/fullprosmaker.md`
- `docs/akkapros/varco-verification.md`
- any additional config or help pages that enumerate the allowed policy family
  or default policy

---

## Acceptance Criteria

- [x] The phonetizer no longer computes accentuation as
      `round_half_up(0.5 * cvc_reference) - drift_portion`; it always targets
      the full `round_half_up(0.5 * cvc_reference)` increment.
- [x] Entry drift is still tracked and still contributes to the final drift
      result after accentuation, but it does not reduce the intended accent
      increment before distribution.
- [x] The allowed
      `phonetize.process.timing_model.accentuation_distribution_policy`
      inventory is exactly
      `100_0`, `95_05`, `90_10`, `85_15`, `80_20`, `75_25`, and `70_30`.
- [x] The default
      `phonetize.process.timing_model.accentuation_distribution_policy` is
      `80_20` in runtime defaults, `default.yaml`, and both tracked demo YAML
      files.
- [x] When legality limits prevent the full accent target from being assigned,
      the solver scales the total local increment down to the largest value that
      preserves the configured ratio instead of greedily consuming extra slack
      on one segment.
- [x] When the preserved-ratio realizable increment is smaller than the full
      accent target, the unassigned remainder is carried into running drift and
      does not itself cause immediate fatal Phase 2 failure.
- [x] Existing legality rules remain in force: adjacent short vowels stay below
      `long_min`, long-vowel accent extension stays within the configured legal
      range, and consonants stay within the applicable geminate-like bounds.
- [x] `src/akkapros/config/default.yaml` comments and help text list the full
      seven-value policy inventory and describe the new shortfall-to-drift rule.
- [x] Public phonetizer documentation no longer describes accentuation as a
      drift-reduced target and instead documents the fixed target plus
      ratio-preserving shortfall carry rule.
- [x] Unit and integration tests pin at least one full-success example and one
      partial-success preserved-ratio example for the new algorithm.

---

## Risks / Edge Cases

- The preserved-ratio rule is stricter than the current greedy spill logic, so
  existing gold outputs may change even when the same legality bands are kept.
- A policy with a non-zero adjacent share can realize less total local timing
  than the current greedy algorithm in cases where the adjacent segment is the
  bottleneck.
- Any documentation or help surface that still says
  `AA = round_half_up(0.5 * cvc_reference) - drift_portion` would become
  directly misleading after implementation.
- The illustrative arithmetic supplied with this request appears internally
  inconsistent: a total target of `150 ms` with an `80/20` split and capacities
  of `60 ms` and `30 ms` yields a preserved-ratio realizable increment of
  `75 ms`, leaving a shortfall of `75 ms`; a shortfall of `25 ms` corresponds
  instead to a `100 ms` total target. The normative rule in this CR follows the
  general preserved-ratio formula rather than the inconsistent example text.

---

## Testing Strategy

Unit tests:

- verify the allowed policy inventory includes the four new ratio strings
- verify the default policy resolves to `80_20`
- verify the accent target is computed independently of entry drift
- verify a partial-success case scales the total increment to the largest
  preserved-ratio legal value instead of using greedy overflow assignment
- verify the resulting shortfall is carried into drift with the current sign
  convention

Integration tests:

- verify config-driven phonetizer runs accept all seven policy strings
- verify emitted row durations and drift tokens match the new behavior for at
  least one preserved-ratio bottleneck example
- verify the tracked demo YAML files load and expose `80_20` as the default

Manual verification:

- inspect `src/akkapros/config/default.yaml` and confirm the comment block and
  default value reflect the seven-policy family with `80_20` default
- inspect phonetizer and fullprosmaker user docs for the updated policy family
  and the replacement of the older drift-reduced formula

---

## Rollback Plan

Restore the previous accentuation contract by reverting the policy inventory to
`100_0`, `85_15`, and `70_30`, restoring `85_15` as the default, reinstating
the drift-reduced target formula, and restoring the previous tests and docs
that describe the greedy local-spill behavior.

---

## Related Issues

- [CR-063](063-tune-the-phonetizer-solver.md)
- [CR-068](068-ratio-based-parameters.md)
- [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)
- [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)

---

## Tasks

## Implementation

- [x] Replace the drift-reduced accent-target computation with a fixed
      half-foot target
- [x] Replace greedy leftover spill with preserved-ratio capped realization
- [x] Extend the policy inventory to the seven allowed values
- [x] Change the default policy to `80_20` in runtime defaults and all tracked
      YAML surfaces

## Tests

- [x] Update config-support tests for the new allowed inventory and default
- [x] Add or update phonetizer path tests for preserved-ratio shortfall carry
- [x] Refresh affected integration golds if emitted timing changes

## Documentation

- [x] Update public phonetizer docs, config comments, and any help surfaces that
      enumerate the policy family or formula
- [x] Update directly affected internal records if they explicitly restate the
      superseded formula as active behavior

## Review

- [x] Verify the new drift-sign treatment of accent shortfall matches the live
      row-level drift-token convention
- [x] Verify acceptance criteria against runtime outputs and config surfaces

---

## Implementation Blockers

## 2026-04-18 - Earlier CR in sequence is not Done

- Type: `governance conflict`
- Observed: [CR-068](068-ratio-based-parameters.md) remains `Draft`, and the
  repository workflow states that a later CR must not be implemented while an
  earlier CR in sequence remains not `Done`.
- Why blocked: safe implementation sequencing for CR-069 is not satisfied yet
  under the current `docs/internal/README.md` CR-order rule.
- Needed to unblock: mark CR-068 `Done` after its implementation lands, reject
  it, or otherwise resolve its sequencing status explicitly before implementing
  CR-069.
- Owner: `maintainer`
- Related refs: `docs/internal/README.md`, CR-068, CR-069
- Resolved on: 2026-04-18
- Resolution: CR-068 was verified as already implemented in the repository and
  its status was updated to `Done` before CR-069 implementation and
  verification were completed.

---

## Notes

- Assumption used in this draft: the user's intent is to keep the existing
  legality bands and drift sign convention, changing only the accent-target
  formula, ratio-preservation rule, allowed policy values, and default policy.
- Implementation landed on 2026-04-18 across runtime, config, tests, and
  user-facing documentation.
