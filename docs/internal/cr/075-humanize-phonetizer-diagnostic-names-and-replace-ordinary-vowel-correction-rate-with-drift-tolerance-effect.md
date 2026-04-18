---
cr_id: CR-075
status: Done
priority: High
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
implements: 'ADR-026'
---

# Change Request: Humanize Phonetizer Diagnostic Names and Replace Ordinary Vowel Correction Rate with Drift Tolerance Effect

# Summary

Rename the phonetizer diagnostic field family so emitted metadata is more
human-readable, and replace the useless ordinary-vowel-correction rate family
with a new `drift_tolerance_effect` indicator that directly shows the effect of
`drift_tolerance` on non-accented long vowels.

The current schema is technically precise but not readable enough for direct
human inspection. Names such as `post_unit_drift_extension_denominator`,
`completed_unit_count`, and `ordinary_vowel_correction_count` require source
code knowledge before a reader can tell what is being counted. In addition, the
current ordinary-vowel-correction rate family does not answer the user question
it appears to answer, because its denominator is branch-local rather than the
full non-accented long-vowel population.

This CR keeps phonetizer timing behavior unchanged. It changes only the
research-facing diagnostic contract.

This CR narrows the naming and diagnostics contracts approved by
[CR-072](072-rename-drift-reporting-to-post-unit-drift.md) and
[CR-073](073-add-probability-oriented-phonetizer-diagnostic-statistics.md).

---

# Motivation

- Human-readable research artifacts
- Metadata terminology cleanup
- Remove a misleading indicator
- Add a drift-tolerance-sensitive long-vowel metric

The user requirement is that the words themselves must have meaning. A reader
should be able to inspect emitted front matter and infer the counted event and
population directly from the field name.

The current field family has several problems:

- the repeated `post_unit_` prefix is longer than necessary once the schema is
  already scoped to phonetizer unit-level diagnostics
- `*_denominator` names expose formula structure instead of naming the actual
  population being counted
- `completed_unit_count` does not tell the reader what action was completed
- `ordinary_vowel_correction_*` is misleading because the live implementation
  only counts long-vowel adjustment in the ordinary non-accent recovery path;
  short vowels are ordinary in plain language but are not counted there
- the current ordinary-vowel-correction rate often collapses to `1.0` while
  still not measuring the effect of `drift_tolerance` on the corpus
- `mini_pause_success_rate_over_eligible` and `mini_pause_insert_rate` are the
  same quantity under the live implementation and should not survive as two
  long-term fields

The repository needs one coherent CR that both humanizes the names and replaces
the misleading long-vowel indicator with one that measures the intended effect.

---

# Scope

## Included

- Rename phonetizer diagnostic fields to shorter, human-readable names.
- Replace generic `*_denominator` field names with explicit population names.
- Rename core population counters so the counted entity is legible.
- Remove redundant alias fields that are semantically duplicated.
- Remove the current ordinary-vowel-correction rate family from the active
  diagnostics surface.
- Add `drift_tolerance_effect` based on the full non-accented long-vowel
  population.
- Update public docs, tests, and report labels to use the new naming surface.
- Define a compatibility and migration rule for older artifacts.

## Not Included

- Any change to phonetizer timing behavior.
- Any change to drift math, pause legality, accentuation, or duration bounds.
- Any change to the row-body field order in `_phone.txt` / `_ophone.txt`.
- Adding unrelated diagnostics beyond the renamed and replacement current set.
- Reinterpreting the meaning of the underlying measured events.

---

# Current Behavior

The active metadata surface currently exposes names such as:

- `post_unit_drift`
- `syllable_unit_count`
- `pause_unit_count`
- `mini_pause_row_count`
- `completed_unit_count`
- `post_unit_drift_extension_count`
- `post_unit_drift_extension_denominator`
- `post_unit_drift_extension_rate`
- `ordinary_vowel_correction_count`
- `ordinary_vowel_correction_denominator`
- `ordinary_vowel_correction_rate`
- `ordinary_vowel_correction_shorten_count`
- `ordinary_vowel_correction_lengthen_count`
- `mini_pause_insert_count`
- `mini_pause_insert_denominator`
- `mini_pause_insert_rate`
- `mini_pause_success_rate_over_eligible`
- `pause_residual_post_unit_drift_count`
- `pause_residual_post_unit_drift_denominator`
- `pause_residual_post_unit_drift_rate`

Current consequences:

- readers must already know that `post_unit_drift_extension_denominator` is
  just the syllable population for this event
- readers must already know that `ordinary_vowel_correction_*` means adjustable
  long-vowel correction, not ordinary vowels in general
- the schema mixes population names, formula names, and implementation-path
  names in one surface
- the ordinary-vowel-correction denominator is incremented only after the solver
  has already entered the ordinary long-vowel correction branch, so the
  resulting rate can be numerically correct yet still useless for comparing
  `drift_tolerance` settings
- a value of `1.0` can be misread as “100% of long vowels were corrected,”
  which is false

The current names were approved incrementally for precision, but the resulting
surface is not sufficiently human-readable and one required indicator does not
measure the intended corpus-level effect.

---

# Proposed Change

Adopt a human-readable phonetizer diagnostics naming contract and replace the
ordinary-vowel-correction rate family with a drift-tolerance-effect family.

## 1. Shorten the drift family from `post_unit` to `unit`

Rename the front matter drift summary group:

- `post_unit_drift` -> `unit_drift`

Rename related extension statistics:

- `post_unit_drift_extension_count` -> `unit_drift_extension_count`
- `post_unit_drift_extension_rate` -> `unit_drift_extension_rate`
- `max_post_unit_drift_extension` -> `max_unit_drift_extension`

Rationale:

- within the phonetizer diagnostics surface, the unit is already the operative
  counting level
- `unit_drift` remains meaningful while removing avoidable visual noise
- this CR narrows CR-072's wording from the more verbose `post-unit drift`
  label to a shorter but still non-segmental `unit drift` label

The row-level flat-body column name `drift` may remain unchanged, but docs must
describe it as the latest unit-drift token.

## 2. Rename core population counters to direct nouns

Rename:

- `syllable_unit_count` -> `syllable_count`
- `pause_unit_count` -> `pause_count`
- `mini_pause_row_count` -> `mini_pause_count`
- `completed_unit_count` -> `total_unit_count`

Interpretation:

- `syllable_count` counts realized syllable units
- `pause_count` counts non-mini realized pause units
- `mini_pause_count` counts inserted mini pauses
- `total_unit_count` is `syllable_count + pause_count + mini_pause_count`

The word `completed` must not remain in the field name because the action is
not obvious from the metadata alone.

## 3. Replace generic denominator names with explicit population names

The generic `*_denominator` naming pattern must be removed from the public
front-matter surface. A field that names only its arithmetic role is not a good
human-facing label when the actual population can be named directly.

Apply this rule as follows:

- remove `post_unit_drift_extension_denominator`
  use `syllable_count` as the explicit population for
  `unit_drift_extension_rate`
- rename `mini_pause_insert_denominator` -> `eligible_mini_pause_count`
- rename `pause_residual_post_unit_drift_denominator` -> `pause_count`

Interpretation rule:

- when the denominator is already one of the core population counters, do not
  duplicate it under a second field name
- when the denominator is a special eligibility population not otherwise named,
  expose it with a direct population name rather than `*_denominator`

## 4. Replace the ordinary-vowel-correction rate family

Remove from the active emitted front-matter contract:

- `ordinary_vowel_correction_count`
- `ordinary_vowel_correction_denominator`
- `ordinary_vowel_correction_rate`

Do not keep a renamed equivalent of that same branch-local rate. The user has
judged the indicator itself useless, not merely the wording.

Add instead:

- `non_accented_long_vowel_count`
- `left_as_is_non_accented_long_vowel_count`
- `drift_tolerance_effect`

Definition:

- `drift_tolerance_effect = left_as_is_non_accented_long_vowel_count / non_accented_long_vowel_count`

Interpretation:

- higher values mean more non-accented long vowels were left unchanged under the
  current tolerance setting
- lower values mean more non-accented long vowels were adjusted

This is the intended research-facing indicator for comparing different
`drift_tolerance` runs.

Population rule:

- `non_accented_long_vowel_count` counts non-accented long-vowel syllables,
  not the narrower subset that actually crossed the drift-tolerance gate
- `left_as_is_non_accented_long_vowel_count` counts members of that population
  whose nucleus duration was not changed by ordinary long-vowel adjustment
- accent-bearing long-vowel post-accent cleanup cases are excluded from both
  numerator and denominator

Optional companion counts may be emitted if clearly documented:

- `adjusted_non_accented_long_vowel_count`
- `shortened_non_accented_long_vowel_count`
- `lengthened_non_accented_long_vowel_count`

If emitted, these are supporting details only. They must not replace
`drift_tolerance_effect` as the primary tolerance-effect indicator.

## 5. Rename the mini-pause family

Rename:

- `mini_pause_insert_count` -> `inserted_mini_pause_count`
- `mini_pause_insert_rate` -> `mini_pause_insertion_rate`
- `mini_pause_eligible_count` -> `eligible_mini_pause_count`

Remove:

- `mini_pause_success_rate_over_eligible`

Rationale:

- `mini_pause_success_rate_over_eligible` is an alias of the same ratio already
  reported by `mini_pause_insert_rate` in the live implementation
- the retained names should say what happened and over which eligibility set

## 6. Rename the pause-residual family

Rename:

- `pause_residual_post_unit_drift_count` -> `pause_with_residual_drift_count`
- `pause_residual_post_unit_drift_rate` -> `pause_with_residual_drift_rate`

Population:

- `pause_count`

This family should read as a pause-level event count, not as a chained noun
stack assembled from implementation internals.

## 7. Human-readable report labels

Metrics and phonetizer reports must use prose labels that mirror the renamed
fields, for example:

- `Unit drift max`
- `Unit drift mean`
- `Unit drift stddev`
- `Total units`
- `Non-accented long vowels`
- `Left-as-is non-accented long vowels`
- `Drift tolerance effect`
- `Inserted mini pauses`
- `Eligible mini pauses`
- `Pauses with residual drift`

If a label still requires internal jargon to decode, the rename is incomplete.

## 8. Compatibility and migration rule

This CR is a naming-and-diagnostic-contract change. Numeric values and event
semantics remain the same except for removal of the retired
ordinary-vowel-correction rate family and addition of the new
`drift_tolerance_effect` family.

Migration rules:

- newly emitted artifacts must use only the new names and the new replacement
  tolerance-effect metric
- downstream readers may support a temporary read-compatibility fallback for the
  older CR-072/073 names during migration
- docs and tests must treat the new names and the new tolerance-effect metric as
  the only active contract
- compatibility aliases, if temporarily supported in code, must be documented as
  migration-only and not as a permanent dual schema

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/metrics.py`
- phonetizer and metrics docs
- integration and library tests that pin front matter names or metrics labels

Implementation direction:

- replace the emitted front-matter keys with the new human-readable names
- update downstream metadata readers to consume the new names
- add temporary legacy read fallbacks where older artifacts are still expected
- remove redundant duplicate rate fields rather than renaming both copies
- count the full non-accented long-vowel population separately from the old
  branch-local ordinary-correction population
- count the subset left unchanged by ordinary long-vowel adjustment
- emit the new rate as `left_as_is_non_accented_long_vowel_count / non_accented_long_vowel_count`
- update rendered report labels to the same human-readable vocabulary

Design constraints:

- no numerical recomputation outside the renamed or replacement diagnostic
  contract
- no solver-behavior changes in the same change
- no permanent dual-schema output mode

Governance note:

- this CR explicitly narrows the contracts approved by CR-072 and CR-073

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/metrics.py`
`docs/akkapros/phonetizer.md`
`docs/akkapros/phonetizer-phone-file-guide.md`
`docs/akkapros/phonetizer-algorithm.md`
`docs/akkapros/metricalc.md`
`tests/test_phonetize_lib.py`
`tests/test_integration.py`
`tests/test_metrics_stats.py`

---

# Acceptance Criteria

- [x] Newly emitted phonetizer front matter uses `unit_drift` instead of
      `post_unit_drift`.
- [x] Newly emitted phonetizer front matter uses `syllable_count`,
      `pause_count`, `mini_pause_count`, and `total_unit_count` instead of the
      current `*_unit_count` / `*_row_count` names.
- [x] The generic `*_denominator` field family no longer appears in newly
      emitted front matter.
- [x] Eligibility populations that are not already represented by a core count
      use explicit population names such as `eligible_mini_pause_count`.
- [x] Newly emitted artifacts do not use the current
      `ordinary_vowel_correction_count / denominator / rate` family as part of
      the active diagnostics contract.
- [x] Newly emitted artifacts expose `non_accented_long_vowel_count`.
- [x] Newly emitted artifacts expose `left_as_is_non_accented_long_vowel_count`.
- [x] Newly emitted artifacts expose `drift_tolerance_effect`.
- [x] `drift_tolerance_effect` equals
      `left_as_is_non_accented_long_vowel_count / non_accented_long_vowel_count`.
- [x] Accent-bearing long-vowel post-accent cleanup cases are excluded from the
      numerator and denominator.
- [x] The mini-pause family uses `inserted_mini_pause_count`,
      `eligible_mini_pause_count`, and `mini_pause_insertion_rate`.
- [x] The redundant alias `mini_pause_success_rate_over_eligible` is removed
      from newly emitted artifacts.
- [x] The pause-residual family uses `pause_with_residual_drift_count` and
      `pause_with_residual_drift_rate`.
- [x] Human-readable metrics/phonetizer report labels mirror the renamed field
      family and the new tolerance-effect metric.
- [x] Tests and fixtures assert the new names as the active contract.
- [x] Public docs describe the new names directly and explain any temporary
      legacy-read compatibility only as migration behavior.

---

# Risks / Edge Cases

Possible issues:

- downstream readers or gold fixtures may still expect the CR-072/073 names
- older artifacts in the repository may need explicit migration or regeneration
- some renamed fields may still need one line of explanatory prose when the
  counted event itself is domain-specific
- the exact counting point for `left_as_is` must be stated carefully so tests
  do not mix baseline assignment with later accent-bearing cleanup logic

Specific caution:

- this CR is about the ordinary non-accented long-vowel path only
- it must not be misread as a general measure of all vowel immobility in the
  text

---

# Testing Strategy

Unit tests:

- emitted phonetizer report uses the renamed keys
- legacy-read fallback accepts older artifacts if such fallback is retained
- duplicate-rate removal does not change retained numeric values
- controlled examples where non-accented long vowels remain unchanged at higher
  `drift_tolerance`
- controlled examples where the same vowels are adjusted at lower
  `drift_tolerance`
- explicit verification that accent-bearing long-vowel cleanup cases are not
  counted in the new metric

Integration tests:

- phonetizer and fullprosmaker outputs expose only the new names in fresh
  artifacts
- metrics text uses the new human-readable labels
- sample runs with at least two `drift_tolerance` values show the expected
  direction of change in `drift_tolerance_effect`

Regression tests:

- numeric values remain unchanged for the same sample inputs aside from the
  renamed, removed, and replacement metadata fields

Manual checks:

- inspect a generated `_phone.txt` or `_ophone.txt` front matter block and
  confirm the field names are self-explanatory without opening source code
- inspect generated front matter and confirm the new rate can be read directly
  as “share of non-accented long vowels left unchanged”

---

# Rollback Plan

If implementation causes downstream breakage, temporarily restore legacy read
fallbacks while keeping the new names and `drift_tolerance_effect` as the target
contract. Do not reintroduce the older names or the retired
ordinary-vowel-correction rate family as a permanent dual-output schema unless a
later CR explicitly approves that reversal.

---

# Related Issues

- [CR-072](072-rename-drift-reporting-to-post-unit-drift.md)
- [CR-073](073-add-probability-oriented-phonetizer-diagnostic-statistics.md)
- [CR-074](074-apply-accentuation-before-ordinary-long-vowel-drift-recovery.md)
- [ADR-049](../adr/049-accentuation-first-long-vowel-recovery-and-accent-sensitive-bounds.md)

---

# Tasks

## Implementation

- [x] Rename emitted phonetizer metadata keys to the new human-readable names.
- [x] Update downstream consumers and report builders.
- [x] Remove semantically redundant duplicate rate fields.
- [x] Remove the current ordinary-vowel-correction rate family from the active
      emitted schema.
- [x] Add counts for the full non-accented long-vowel population and the left-
      unchanged subset.
- [x] Emit `drift_tolerance_effect`.
- [x] Add temporary legacy-read fallback only where needed.

## Tests

- [x] Update unit tests for phonetizer metadata naming and the new metric
      family.
- [x] Update integration tests and fixtures.
- [x] Verify numeric stability under the rename.
- [x] Add comparison tests across multiple `drift_tolerance` values.

## Documentation

- [x] Update public phonetizer and metrics docs.
- [x] Update examples or demo artifacts that surface the renamed fields.

## Review

- [x] Verify the renamed contract against current implementation terminology.
- [x] Confirm migration language is sufficient for downstream artifact readers.

---

# Implementation Blockers

Leave empty.

---

# Notes

This CR consolidates the diagnostics rename and metric replacement work into a
single active record under the lower available identifier so the CR sequence
remains contiguous.