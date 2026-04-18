---
cr_id: CR-074
status: Draft
priority: High
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
implements: 'ADR-049, REQ-040'
---

# Change Request: Apply Accentuation Before Ordinary Long-Vowel Drift Recovery

## Summary

Change the Phase 2 syllable-operation order so accentuation is applied before
ordinary long-vowel drift recovery.

Under the current solver, a long nucleus may first be shortened or lengthened
by ordinary drift recovery and only afterward receive accentuation. That is
acceptable for non-accented syllables, but it can interfere with the intended
accentuation process when the same syllable is supposed to receive the fixed
accent increment defined by the active contract. This CR changes the order of
operations for accent-bearing syllables to `assign -> accentuate -> ordinary
long-vowel drift recovery`, and it also defines accent-sensitive long-vowel
recovery bounds: ordinary non-accented long vowels keep the narrower range
below `very_long_min`, while accent-bearing long vowels (`CVV:` and `CVV:C`)
may use the broader range up to `elongation_max`. The rest of the solver and
the reporting schema remain intact.

---

## Motivation

- Solver-contract change
- Accentuation-priority clarification
- Documentation and test synchronization

The active public algorithm currently documents the following order for each
syllable unit:

- assign baseline segment durations
- if unresolved drift exceeds tolerance, apply ordinary long-vowel correction
- if the syllable carries accentuation, apply the accent increment

That order means an accent-bearing long nucleus can be modified by ordinary
chrono recovery before the accentuation step executes. The user requirement is
to reverse that precedence: when a syllable must be accentuated, accentuation
must act on the baseline assignment first, and only then may ordinary long-
vowel flexibility be used to reduce any remaining drift.

The user also requires one explicit legality distinction that the current CR did
not spell out:

- non-accented long-vowel cleanup uses the ordinary long-vowel range bounded by
  `vowels.perception_limits.very_long_min - 1`
- accent-bearing long-vowel cleanup in `CVV:` and `CVV:C` may use the broader
  elongated range up to `vowels.perception_limits.elongation_max`
- `C:V` and `CVC:` do not participate in long-vowel cleanup because those
  accent models do not contain a long vowel

The activation rule also differs between the two cases. Ordinary non-accented
long-vowel cleanup remains gated by `drift_tolerance`, while accent-bearing
long-vowel cleanup is not activated by that ordinary tolerance threshold once
accentuation has already moved the vowel into elongated space.

This change is narrower than the broader accentuation-target rule already set by
[CR-069](069-replace-drift-aware-accentuation-with-ratio-preserving-shortfall-carry.md).
CR-069 remains the active contract for fixed half-foot target and preserved-ratio
shortfall carry. This new CR only changes the relative order between
accentuation and ordinary long-vowel recovery.

---

## Scope

### Included

- Change the Phase 2 step order for accent-bearing syllables so accentuation is
  applied before ordinary long-vowel drift recovery.
- Define accent-sensitive long-vowel recovery bounds for non-accented versus
  accent-bearing long-vowel syllables.
- Define the activation rule difference between ordinary non-accented long-vowel
  cleanup and post-accent long-vowel cleanup.
- Update the public algorithm description and any related user-facing prose that
  still documents the older order.
- Update unit/integration/regression tests that pin solver order or outputs
  affected by the changed order.
- Preserve existing reporting structures and statistic field meanings so the
  phonetizer metadata contract is not renamed or reinterpreted in the same CR.

### Not Included

- Changing the fixed accent target defined by CR-069.
- Changing the distribution-policy family or default ratios.
- Changing beat folding, mini-pause eligibility, pause-band selection, or pause
  discharge logic.
- Renaming or restructuring existing phonetizer statistics/reporting fields.
- Adding new statistics; that belongs to other records such as
  [CR-073](073-add-probability-oriented-phonetizer-diagnostic-statistics.md).

---

## Current Behavior

Repository inspection on 2026-04-18 shows the current live and documented order
still gives ordinary long-vowel drift recovery precedence over accentuation.

Observed runtime evidence in `src/akkapros/lib/phonetize.py`:

- baseline segment durations are assigned first
- `drift_after_assignment` is computed from the non-accentuated unit target
- if unresolved absolute drift exceeds tolerance and the nucleus is long,
  `_apply_vowel_correction(...)` runs before accentuation
- only afterward, if accentuation is allowed and the syllable is accent-bearing,
  `_apply_accent_increment(...)` runs

Observed config evidence in `src/akkapros/config/default.yaml`:

- the ordinary non-accented long-vowel contract is still documented under
  `vowels.perception_limits.very_long_min` and `elongation_max`
- current comments still describe ordinary non-accentual long-vowel recovery as
  stopping at `very_long_min - 1`

Observed documentation evidence in `docs/akkapros/phonetizer-algorithm.md`:

- the current numbered step order says ordinary long-vowel correction happens
  before accent increment distribution

Current consequence:

- long-vowel flexibility can partially absorb mismatch before the accent step
  executes on an accent-bearing syllable
- the accentuation process therefore no longer acts on the pure baseline
  assignment for that syllable
- the legal cleanup range and activation rule for accent-bearing `CVV:` / `CVV:C`
  remain under-specified in the current CR text

---

## Proposed Change

Adopt the following revised step order.

### 1. Baseline assignment remains first

For every syllable unit, the solver still begins by:

- assigning onset anchors
- assigning coda anchors if present
- assigning the nucleus anchor
- pre-assigning same-consonant next-onset timing where applicable
- computing the non-accentuated `shape_ref`
- computing initial `drift_after_assignment`

### 2. Accentuation precedes ordinary long-vowel recovery

If the stream is accentuated and the syllable carries accentuation:

- apply accentuation immediately after baseline assignment and initial drift
  computation
- use the existing accentuation contract from CR-069 for target quantity,
  preserved-ratio realization, and shortfall carry
- recompute post-accent drift from the emitted durations and accent target

Only after that accentuation result is known may ordinary long-vowel drift
recovery be considered.

### 3. Ordinary long-vowel recovery becomes post-accent cleanup with
accent-sensitive bounds

The solver must distinguish two long-vowel cleanup regimes.

#### A) Non-accent-bearing long vowels

If the syllable is not accent-bearing and the nucleus is long:

- ordinary long-vowel cleanup remains tolerance-gated
- if absolute drift does not exceed `drift_tolerance`, the long vowel is not
  modified
- if absolute drift exceeds `drift_tolerance`, the solver may adjust the long
  vowel within the ordinary non-accented range from
  `vowels.perception_limits.long_min` up to
  `vowels.perception_limits.very_long_min - 1`
- once activated, the cleanup target is zero residual drift within the legal
  ordinary range, not merely reduction down to the tolerance boundary

#### B) Accent-bearing long vowels

If the syllable is accent-bearing and its accent model is `CVV:` or `CVV:C`:

- accentuation runs first
- post-accent long-vowel cleanup may then use the broader long-vowel range from
  `vowels.perception_limits.long_min` up to
  `vowels.perception_limits.elongation_max`
- this post-accent cleanup is not activated by the ordinary `drift_tolerance`
  gate because the vowel is already in accentual elongation space
- the cleanup target is again zero residual drift within the legal accented
  range, leaving any irreducible remainder in drift only when the legal range is
  exhausted

#### C) Non-long accent models

If the accent model is `C:V` or `CVC:`:

- long-vowel cleanup rules do not apply because the syllable contains no long
  vowel

Normative consequences:

- on non-accent-bearing syllables, the current ordinary long-vowel recovery rule
  remains tolerance-gated and uses the ordinary non-accented range
- on accent-bearing `CVV:` and `CVV:C` syllables, long-vowel cleanup is no longer
  allowed to pre-empt the accentuation step and may use the wider accented
  range up to `elongation_max`
- `C:V` and `CVC:` remain governed purely by their consonant/vowel accentuation
  logic with no long-vowel cleanup path
- these cleanup rules do not redefine the accent target or ratio distribution
  rules from CR-069

### 4. Remaining downstream flow stays unchanged

After the revised accentuation/recovery sequence:

- completed-unit drift is folded only at eligible `F` closures as before
- mini-pause eligibility and insertion rules remain unchanged
- pause rows continue to try to discharge drift toward zero under their existing
  pause-band logic; this CR does not weaken pause recovery
- drift summary/statistics schema remains unchanged, although values may change
  naturally because the solver behavior changed

### 5. Statistics/reporting stability

This CR must not rename, remove, or reinterpret the existing reporting fields
in phone/ophone front matter or derived tables.

Clarification:

- values of existing statistics may legitimately change as a consequence of the
  new step order
- the reporting surface itself must remain stable unless a separate labeling or
  reporting CR changes it

This is the intended meaning of “statistics not perturbed” for this CR:
reporting-contract stability, not frozen numeric outputs.

---

## Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/config/default.yaml`
- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer.md`
- `tests/test_phonetize_lib.py`
- affected integration/regression tests and golds

Implementation direction:

- reorder the internal Phase 2 control flow so accentuation runs before
  ordinary long-vowel correction on accent-bearing syllables
- keep the non-accent-bearing path tolerance-gated, but make its cleanup target
  zero-drift within the legal ordinary range once activated
- give accent-bearing `CVV:` and `CVV:C` syllables the broader post-accent
  long-vowel cleanup range up to `elongation_max`
- keep `C:V` and `CVC:` outside the long-vowel cleanup path
- recompute drift in the revised order without changing the accepted formulas
  for accent target, shortfall carry, or completed-unit folding
- update docs/tests/golds to match the new order and legality-space change

Design constraint:

- no reporting-schema rename in the same change
- no separate retuning of defaults or policy families in the same change
- the existing config meanings of `long_min`, `very_long_min`, and
  `elongation_max` remain intact; this CR changes when and where they are used

Supersession note:

- This CR narrows the active solver-order part of [CR-063](063-tune-the-phonetizer-solver.md)
  and the active accentuation-runtime contract in [CR-069](069-replace-drift-aware-accentuation-with-ratio-preserving-shortfall-carry.md).
  Those records remain historical and still govern the rest of the solver where
  this CR does not replace them.

---

## Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/config/default.yaml`
`docs/akkapros/phonetizer-algorithm.md`
`docs/akkapros/phonetizer.md`
`tests/test_phonetize_lib.py`
`tests/test_integration.py`
`tests/test_metrics_stats.py`
`demo/akkapros/lexlinks/results/erra_construct_phone.txt`
`demo/akkapros/lexlinks/results/erra_construct_ophone.txt`

---

## Acceptance Criteria

- [ ] For accent-bearing syllables, the Phase 2 order is baseline assignment,
      accentuation, then ordinary long-vowel drift recovery.
- [ ] For non-accent-bearing long vowels, ordinary cleanup remains tolerance-
  gated and uses the legal range from `long_min` to `very_long_min - 1`.
- [ ] For accent-bearing `CVV:` and `CVV:C` syllables, post-accent long-vowel
  cleanup may use the legal range up to `elongation_max`.
- [ ] For accent-bearing `C:V` and `CVC:` syllables, the long-vowel cleanup path
  is not applied.
- [ ] Once long-vowel cleanup is activated on a non-accent-bearing long vowel,
  it targets zero residual drift within the legal range rather than merely
  reducing mismatch to the tolerance boundary.
- [ ] Accent-bearing `CVV:` and `CVV:C` cleanup is not gated by the ordinary
  `drift_tolerance` activation rule.
- [ ] Public algorithm documentation no longer states that ordinary long-vowel
      correction precedes accentuation.
- [ ] Public algorithm/config documentation explains the difference between
  ordinary and accent-bearing long-vowel recovery bounds.
- [ ] Tests are updated to pin the new step order explicitly.
- [ ] Integration/regression expectations affected by emitted timing changes are
      updated.
- [ ] Existing phonetizer statistics/reporting fields remain present and keep
      the same meanings, even if their values change.
- [ ] No unrelated retuning of timing defaults or policy families is included.

---

## Risks / Edge Cases

- Because accentuation now takes precedence on long accent-bearing syllables,
  emitted timing may change in ways that refresh corpus golds and downstream
  metrics expectations.
- Because accent-bearing `CVV:` / `CVV:C` now have a wider legal cleanup range,
  drift distribution between syllables and pauses may change relative to prior
  outputs.
- If the implementation reuses pre-accent drift values after reordering, the new
  contract could be only partially applied. Tests must pin the exact order.
- Documentation drift is likely unless both the algorithm page and smaller
  summary pages are updated in the same change.

---

## Testing Strategy

Unit tests:

- accent-bearing long-vowel syllable follows the new order
- non-accent-bearing long-vowel syllable uses the ordinary range and tolerance
  gate
- accent-bearing `CVV:` / `CVV:C` uses the widened accented range
- `C:V` and `CVC:` do not enter the long-vowel cleanup path
- non-accented long-vowel cleanup targets zero residual drift once activated
- post-accent ordinary recovery only runs on remaining unresolved drift

Integration tests:

- update emitted phone/ophone fixtures or golds where the reordered solver
  changes durations or drift values
- verify reporting fields remain schema-compatible across the change

Manual tests:

- compare one representative accent-bearing long-vowel case before/after and
  verify the accentuation step now precedes long-vowel chrono cleanup
- compare one non-accented long-vowel case and one accent-bearing `CVV:` case
  and verify the two paths use different legality ceilings

---

## Rollback Plan

Restore the older solver order if the new precedence introduces unacceptable
regressions, but keep any unrelated reporting/doc changes out of the rollback.

---

## Related Issues

- [CR-063](063-tune-the-phonetizer-solver.md)
- [CR-069](069-replace-drift-aware-accentuation-with-ratio-preserving-shortfall-carry.md)
- [REQ-040](../req/040-accentuation-first-long-vowel-recovery-and-accent-sensitive-bounds.md)
- [CR-072](072-rename-drift-reporting-to-post-unit-drift.md)
- [CR-073](073-add-probability-oriented-phonetizer-diagnostic-statistics.md)

---

## Tasks

### Implementation

- [ ] Reorder accent-bearing syllable processing so accentuation runs before
      ordinary long-vowel recovery
- [ ] Apply accent-sensitive long-vowel legality bounds for `CVV:` / `CVV:C`
- [ ] Keep non-accent-bearing long-vowel cleanup tolerance-gated but zero-targeted
- [ ] Preserve existing reporting schema and statistic meanings

### Tests

- [ ] Add/update unit tests for the revised order
- [ ] Refresh affected integration/regression expectations

### Documentation

- [ ] Update algorithm and phonetizer docs to reflect the new order

### Review

- [ ] Verify the change is limited to solver order and dependent gold refreshes
- [ ] Verify reporting structure remains stable

---

## Implementation Blockers

---

## Notes

- This CR changes solver behavior but not reporting schema.
- The numeric values of existing statistics may change as a downstream
  consequence of the new behavior; the field set and meanings must not.
