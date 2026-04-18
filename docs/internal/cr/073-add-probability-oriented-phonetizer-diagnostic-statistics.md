---
cr_id: CR-073
status: Done
priority: Medium
impact: Additive
created: 2026-04-18
updated: 2026-04-18
implements: 'ADR-031, ADR-040, REQ-039'
---

# Change Request: Add Probability-Oriented Phonetizer Diagnostic Statistics

## Summary

Add denominator-aware phonetizer diagnostics so front matter and derived reports
can express how often key recovery mechanisms were needed, rather than exposing
raw counts without a population.

The current phonetizer metadata exposes values such as `drift_extension_count`
and `max_drift_extension`, but those counters are difficult to interpret as
research-facing evidence because the obvious available denominator,
`phone_row_count`, is a row count rather than the population that generated the
event. This CR adds explicit unit counts and probability-oriented derived
indicators for drift extension, vowel chrono correction, mini-pause recovery,
and pause residual-carry behavior, while leaving the timing algorithm itself
unchanged.

---

## Motivation

- Research-facing diagnostics improvement
- Probability-oriented reporting
- Metadata interpretability

The user requirement is not simply to add more counters. The requirement is to
make the counters interpretable as frequencies or probabilities over a clearly
defined population.

Current examples show the problem directly:

- `drift_extension_count: 2746`
- `phone_row_count: 7295`

Those values do not describe the same population. `phone_row_count` counts all
rows, including onset rows, nuclei, codas, pause rows, and inserted mini-pause
rows, while `drift_extension_count` is incremented in the syllable-realization
branch after completed-syllable evaluation. As a result, the current metadata
cannot safely support statements such as “the solver needed extension in 37.89%
of cases” unless the repository also emits the correct denominator.

The same issue applies to other research questions the user now wants answered:

- how often ordinary vowel correction was needed
- how often mini pauses successfully caught chrono mismatch
- how often pauses failed to consume the drift fully

These all require explicit event definitions and explicit denominator counts.

---

## Scope

### Included

- Add front matter counts for the core populations that generate phonetizer
  recovery events.
- Add front matter counts and rates for key timing-recovery events.
- Define denominator semantics for every new rate so values are interpretable as
  event frequencies over a known population.
- Update docs and tests so the new metadata is explained and pinned.
- Preserve the existing runtime timing behavior and numeric realization logic.

### Not Included

- Changing the timing algorithm.
- Redefining existing drift math.
- Introducing true segment-level drift metrics.
- Replacing the existing row-level drift column.
- Removing existing raw counts if they remain useful alongside rates.

---

## Current Behavior

The current phonetizer front matter includes at least:

- `phone_row_count`
- `silence_row_count`
- `phoneme_row_count`
- the drift summary group
- `drift_extension_count`
- `max_drift_extension`

Current implementation details in `src/akkapros/lib/phonetize.py`:

- `drift_extension_count` is incremented after completed-syllable realization
  when unresolved absolute post-unit drift exceeds tolerance.
- `max_drift_extension` is the maximum magnitude above tolerance encountered in
  that same completed-syllable path.
- `_apply_vowel_correction()` may shorten or lengthen the nucleus to reduce
  drift, but the current report does not expose how often that happened.
- `_maybe_insert_mini_pause()` may insert one mini pause after a completed `F`
  boundary syllable, but the current report does not expose how often that
  happened or how often it was attempted/eligible.
- `_pause_duration_and_drift()` may leave residual drift after a pause if the
  legal pause band cannot fully discharge the current mismatch, but the current
  report does not expose how often that happened.

Current consequence:

- raw counts exist for some chrono events, but not their populations
- several important recovery mechanisms have no counters at all
- the current metadata makes probability-style reading difficult or misleading

---

## Proposed Change

Adopt a denominator-aware phonetizer diagnostics contract.

### 1. Add explicit population counts

The phonetizer front matter must report at least these core populations:

- `syllable_unit_count`: count of realized syllable units
- `pause_unit_count`: count of realized pause units, excluding inserted mini
  pauses unless explicitly named otherwise
- `mini_pause_row_count`: count of inserted mini-pause rows
- `completed_unit_count`: `syllable_unit_count + pause_unit_count + mini_pause_row_count`

If the implementation needs separate populations for eligibility rather than all
realized units, it must emit them explicitly rather than overloading the core
counts.

### 2. Drift-extension frequency reporting

Current raw extension counters remain allowed, but they must be paired with the
correct denominator.

Required additions:

- raw count of post-unit drift extension events
- explicit denominator showing which population can generate that event
- derived rate over that denominator

Default contract:

- `post_unit_drift_extension_count`
- `post_unit_drift_extension_denominator`
- `post_unit_drift_extension_rate`

Unless a later narrower record says otherwise, the default denominator must be
the number of realized syllable units, because the current event is generated in
the completed-syllable branch.

### 3. Ordinary vowel chrono-correction frequency

The phonetizer must expose how often ordinary vowel correction actually changed
the realized vowel duration to reduce chrono mismatch.

Required additions:

- `ordinary_vowel_correction_count`
- `ordinary_vowel_correction_denominator`
- `ordinary_vowel_correction_rate`

Recommended companion counts when practical:

- `ordinary_vowel_correction_shorten_count`
- `ordinary_vowel_correction_lengthen_count`

Default denominator:

- long-vowel syllable units eligible for ordinary vowel correction

The CR does not require a second all-syllables rate, but allows it if clearly
named.

### 4. Mini-pause recovery frequency

The phonetizer must expose how often chrono mismatch was reduced by inserted
mini pauses.

Required additions:

- `mini_pause_insert_count`
- `mini_pause_insert_denominator`
- `mini_pause_insert_rate`

Recommended companion counts when practical:

- `mini_pause_eligible_count`
- `mini_pause_success_rate_over_eligible`

Default denominator:

- completed syllable units at eligible `F` boundaries where mini-pause insertion
  is structurally allowed to be considered

If the implementation cannot cheaply emit an eligibility denominator, it must
at minimum emit a clearly named all-syllable or `F`-boundary denominator rather
than using `phone_row_count`.

### 5. Pause residual-carry frequency

The phonetizer must expose how often ordinary pauses were unable to consume the
incoming drift fully.

Required additions:

- `pause_residual_post_unit_drift_count`
- `pause_residual_post_unit_drift_denominator`
- `pause_residual_post_unit_drift_rate`

Default event definition:

- after a non-mini pause is realized, the absolute post-pause drift remains
  above the zero-discharge ideal because the legal pause band could not fully
  absorb the mismatch

Default denominator:

- non-mini pause units

### 6. Other useful indicators to include

This CR also recommends adding one or more of the following front matter
diagnostics if the implementation cost is low and the denominators are clear:

- `on_beat_completed_unit_rate`
- `ahead_completed_unit_rate`
- `behind_completed_unit_rate`
- `folded_post_unit_drift_count` and rate over `F`-closing syllables
- `same_consonant_retiming_count` and rate over eligible same-consonant coda/onset pairs

These are optional in this CR unless promoted to required status during review.

### 7. Count-plus-rate rule

For every new diagnostic frequency added by this CR:

- emit the raw count
- emit the denominator count
- emit the derived rate

The rate must be defined as `count / denominator`, using a stable decimal form.
Percent rendering in user-facing tables is allowed, but front matter should keep
the rate as a machine-readable scalar.

### 8. No behavior change

- This CR adds reporting only.
- Existing phonetizer timing behavior, branch order, drift folding, pause
  realization, and accentuation logic must remain unchanged.

---

## Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/metrics.py`
- phonetizer and metrics docs
- tests that pin phonetizer front matter

Implementation direction:

- extend the Phase 2 report object with explicit event counts and denominator
  counts gathered during the existing realization walk
- carry those values into emitted front matter for `_ophone.txt` and `_phone.txt`
- update downstream readers/docs to surface the added diagnostics without
  changing existing timing calculations

Design constraint:

- counts and rates must be defined from already-existing control-flow events;
  avoid speculative recomputation from serialized row text when direct runtime
  bookkeeping is available

Naming note:

- If [CR-072](072-rename-drift-reporting-to-post-unit-drift.md) is accepted,
  the new diagnostics must use its explicit `post_unit_drift` terminology.

---

## Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/metrics.py`
`docs/akkapros/phonetizer.md`
`docs/akkapros/phonetizer-phone-file-guide.md`
`docs/akkapros/phonetizer-algorithm.md`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/metricalc.md`
`tests/test_phonetize_lib.py`
`tests/test_integration.py`
`tests/test_metrics_stats.py`

---

## Acceptance Criteria

- [x] Phonetizer front matter emits explicit denominator counts for the main
      chrono-event populations rather than relying on row counts as implicit
      denominators.
- [x] Post-unit drift extension reporting includes count, denominator, and rate.
- [x] Ordinary vowel chrono-correction reporting includes count, denominator,
      and rate.
- [x] Mini-pause recovery reporting includes count, denominator, and rate.
- [x] Pause residual-carry reporting includes count, denominator, and rate.
- [x] The meaning of each denominator is documented clearly.
- [x] The added diagnostics do not change any existing timing behavior.
- [x] User-facing docs explain the new fields in probability-oriented terms.
- [x] Tests pin at least one case where changing `drift_tolerance` changes the
      derived rates without changing the denominator semantics.

---

## Risks / Edge Cases

- Different events arise from different populations, so a sloppy “one
  denominator for everything” design would recreate the current ambiguity.
- Eligibility-based denominators may be more informative than all-unit
  denominators, but they also require clearer definitions and more bookkeeping.
- Front matter growth should remain controlled; add only interpretable
  diagnostics rather than every internal branch count.
- If rates are emitted without raw counts, debugging and manual verification
  become harder; both are needed.

---

## Testing Strategy

Unit tests:

- completed-unit population counts are correct on small fixtures
- drift-extension rate uses the documented denominator
- vowel-correction count increments only when the nucleus duration actually
  changes
- mini-pause rate reflects actual inserted mini pauses
- pause residual-carry count increments only when a non-mini pause leaves
  residual post-unit drift

Integration tests:

- `_phone.txt` and `_ophone.txt` front matter expose the new diagnostics
- changing `drift_tolerance` changes the relevant rates consistently with the
  unchanged denominator definition

Manual tests:

- inspect a corpus artifact and confirm that each probability-like statistic can
  be reconstructed from emitted count and denominator values

---

## Rollback Plan

If the added diagnostics prove too noisy or ambiguous, remove the new fields and
restore the previous minimal front matter without touching timing behavior.

---

## Related Issues

- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [CR-072](072-rename-drift-reporting-to-post-unit-drift.md)
- [review-012](../review/012-review.md)

---

## Tasks

### Implementation

- [x] Add core unit-population counts to phonetizer report output
- [x] Add count/denominator/rate diagnostics for drift extension
- [x] Add count/denominator/rate diagnostics for vowel correction
- [x] Add count/denominator/rate diagnostics for mini-pause recovery
- [x] Add count/denominator/rate diagnostics for pause residual carry

### Tests

- [x] Unit tests for event counting and denominator semantics
- [x] Integration tests for emitted front matter and unchanged timing behavior

### Documentation

- [x] Document each new diagnostic field and denominator
- [x] Explain why probability-oriented interpretation is preferred to raw counts

### Review

- [x] Verify no denominator mismatches remain between event counts and reported
      populations
- [x] Verify the added statistics remain understandable on corpus-sized outputs

---

## Implementation Blockers

---

## Notes

- This CR is additive reporting only.
- It is motivated by the mismatch between current event counters and currently
  exposed row counts, and by the user's request for probability-oriented
  diagnostics rather than isolated raw numbers.
