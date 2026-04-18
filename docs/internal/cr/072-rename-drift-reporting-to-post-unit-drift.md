---
cr_id: CR-072
status: Draft
priority: Medium
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
implements: 'ADR-031, REQ-038'
---

# Change Request: Rename Drift Reporting to Post-Unit Drift

## Summary

Rename ambiguous phonetizer drift-reporting labels so the emitted metadata and
user-facing report titles clearly identify the reported quantity as post-unit
drift rather than segmental drift.

This CR is labeling-only. It does not change solver behavior, drift math,
sampling points, or the meaning of any reported numeric value. It narrows the
older reporting contract from [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
by clarifying that the phonetizer report and front matter describe
completed-unit drift history.

---

## Motivation

- Documentation precision
- Metadata naming clarity
- Research-facing terminology cleanup

The current repository already behaves as documented in
[docs/internal/review/012-review.md](../review/012-review.md): the row-level
drift token and the front matter drift summary represent completed-unit
post-syllable/post-pause drift, not segment-by-segment drift.

However, the currently emitted names remain ambiguous:

- `metadata.data.phonetize.drift`
- `drift_extension_count`
- `max_drift_extension`
- report labels such as `Drift max`, `Drift mean`, and `Drift stddev`

Those names do not tell the reader whether the quantity is segmental,
syllable-final, pause-final, or broader prosodic-unit drift. The repository
needs an explicit naming contract so research-facing artifacts cannot be read
as segment-level timing traces.

---

## Scope

### Included

- Rename front matter reporting labels from ambiguous `drift` naming to
  explicit `post_unit_drift` naming.
- Rename the related extension counters so it is explicit that they refer to
  post-unit drift extension, not a segment-by-segment measure.
- Rename any user-facing report headings, table labels, or section titles that
  would still be ambiguous after the front matter rename.
- Update docs and tests so the active terminology is consistent across runtime
  metadata, public docs, and verification fixtures.
- Preserve the current numeric values and sampling semantics exactly.

### Not Included

- Any change to phonetizer solver behavior.
- Any change to drift sampling points.
- Any new segment-level drift metric.
- Any reinterpretation of the current drift values.
- Any change to duration allocation, fold logic, pause discharge, or
  accentuation behavior.

---

## Current Behavior

Current runtime behavior uses the following naming surface for the phonetizer
report and emitted front matter:

- `metadata.data.phonetize.drift.max`
- `metadata.data.phonetize.drift.mean`
- `metadata.data.phonetize.drift.stddev`
- `metadata.data.phonetize.drift.current`
- `metadata.data.phonetize.drift.label`
- `metadata.data.phonetize.drift_extension_count`
- `metadata.data.phonetize.max_drift_extension`

Current user-facing docs and report outputs also use headings such as:

- `Drift Reporting`
- `Drift max`
- `Drift mean`
- `Drift stddev`

The live implementation does not report segment-by-segment drift. As reviewed in
[docs/internal/review/012-review.md](../review/012-review.md), the current
statistics and extension counters are based on completed-unit drift history.

Current problem:

- the labels are shorter than the meaning
- readers can reasonably misread the metadata as segmental drift reporting
- `drift_extension_count` and `max_drift_extension` are especially ambiguous
  because they do not say what unit's drift is being extended

---

## Proposed Change

Adopt the following label-renaming contract.

### 1. Front matter group rename

- Rename `metadata.data.phonetize.drift` to
  `metadata.data.phonetize.post_unit_drift`.
- Keep the scalar members within that map unchanged in meaning:
  `max`, `mean`, `stddev`, `current`, and `label` remain the same quantities,
  now under the explicit `post_unit_drift` group.

### 2. Extension-counter rename

- Rename `metadata.data.phonetize.drift_extension_count` to
  `metadata.data.phonetize.post_unit_drift_extension_count`.
- Rename `metadata.data.phonetize.max_drift_extension` to
  `metadata.data.phonetize.max_post_unit_drift_extension`.

These names must be interpreted as counters/statistics about unresolved
post-unit drift beyond the tolerated band, not as segment-level extension
measurements.

### 3. User-facing label rename

- Rename ambiguous headings and labels in user-facing reports and docs to use
  `Post-unit drift` terminology.

Examples of the intended label family:

- `Post-unit drift reporting`
- `Post-unit drift max`
- `Post-unit drift mean`
- `Post-unit drift stddev`
- `Post-unit drift current`
- `Post-unit drift extension count`
- `Max post-unit drift extension`

### 4. No behavior change

- The numeric values must not change solely because of this CR.
- Sampling remains tied to completed syllable/pause units exactly as in the
  current runtime.
- This CR is satisfied only if the rename is semantic/labeling-only.

### 5. Row-schema boundary

- This CR is mainly about front matter and report labeling.
- The row-level `_phone.txt` / `_ophone.txt` column name `drift` may remain as
  is if changing the flat row schema would be disproportionately disruptive.
- If the row-column label is left unchanged, docs must explicitly state that the
  column is the post-unit drift token.

---

## Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/metrics.py`
- user-facing phonetizer and metrics docs
- tests/fixtures that assert current front matter key names or labels

Implementation direction:

- Change the stage-data key names emitted by phonetizer/front matter builders to
  the explicit `post_unit_drift` family.
- Update downstream consumers that read front matter summaries to use the new
  keys.
- Update human-readable metrics/phonetizer table labels and headings to reflect
  post-unit drift terminology.
- Update tests and fixtures that pin current key names.

Design constraint:

- No numerical recomputation or algorithm change is allowed in the same change.

Compatibility note:

- Because this is a label rename on emitted metadata, the implementation should
  make the migration path explicit in docs/tests. If temporary backward-compat
  aliases are introduced during implementation, they must be documented as a
  transition aid rather than a new long-term dual contract.

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
`docs/akkapros/varco-verification.md`
`tests/test_metrics_stats.py`
`tests/test_integration.py`

---

## Acceptance Criteria

- [ ] Front matter no longer uses ambiguous top-level reporting key
      `metadata.data.phonetize.drift`; it uses
      `metadata.data.phonetize.post_unit_drift` instead.
- [ ] Front matter no longer uses ambiguous keys `drift_extension_count` and
      `max_drift_extension`; they are renamed to explicit post-unit-drift forms.
- [ ] User-facing headings and table labels that present these statistics use
      `Post-unit drift` terminology.
- [ ] The rename does not change any reported numeric values for the same input.
- [ ] Docs explicitly state that the statistics and extension counters refer to
      post-unit drift rather than segmental drift.
- [ ] Tests are updated to pin the renamed labels/keys and unchanged values.
- [ ] Any remaining use of bare `drift` in public docs is either row-column
      specific or clearly defined as post-unit drift.

---

## Risks / Edge Cases

- Downstream readers that currently consume `metadata.data.phonetize.drift` will
  break if the rename is made without a clear migration note.
- The row-level column still being named `drift` could remain a source of mild
  confusion unless the docs state clearly that it is the post-unit token.
- A mixed state where some docs say `drift` and others say `post-unit drift`
  would be worse than the current state if not updated consistently.

---

## Testing Strategy

Unit tests:

- front matter builders emit `post_unit_drift`
- extension counters use the renamed keys
- numeric values for identical inputs remain unchanged after the rename

Integration tests:

- phonetizer/fullprosmaker outputs expose the renamed front matter keys
- metricalc reads the renamed front matter summary successfully

Manual tests:

- inspect one `_phone.txt` or `_ophone.txt` front matter block and verify the
  new labels remove ambiguity around post-unit vs segmental drift

---

## Rollback Plan

Revert the rename if downstream tooling cannot be updated in sync, but do not
change solver behavior. A rollback would restore the old labels only.

---

## Related Issues

- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [review-012](../review/012-review.md)

---

## Tasks

### Implementation

- [ ] Rename front matter drift group to `post_unit_drift`
- [ ] Rename extension counters to explicit post-unit-drift names
- [ ] Update human-readable report labels/headings

### Tests

- [ ] Update fixtures and assertions for renamed keys
- [ ] Verify identical numeric values before/after the rename

### Documentation

- [ ] Update phonetizer and metrics docs to use `Post-unit drift` terminology
- [ ] Add one explicit sentence distinguishing post-unit drift from segmental
      drift

### Review

- [ ] Verify no behavior change accompanied the rename
- [ ] Verify no ambiguous residual titles remain in user-facing artifacts

---

## Implementation Blockers

---

## Notes

- This CR is intentionally narrow and label-focused.
- The semantic basis for the rename is established in
  [docs/internal/review/012-review.md](../review/012-review.md).
