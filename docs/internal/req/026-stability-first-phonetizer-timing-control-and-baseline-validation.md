---
req_id: REQ-026
status: Draft
priority: High
impact: Mutative
created: 2026-04-07
updated: 2026-04-08
related_adrs: 'ADR-041, ADR-040, ADR-039'
implemented_by: 'Follow-up CRs to CR-035 and CR-040'
---

# Requirement: Stability-First Phonetizer Timing Control and Baseline Validation

# Summary

The system shall treat phonetizer Phase 2 timing control as a stability-first
model. This requirement narrows the active interpretation of the timing-model
replacement story under
[REQ-024](024-replacement-of-timing-model.md) and the two-phase phonetizer
story under [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md)
without over-specifying every later runtime detail.

At this stage, the requirement covers only the current timing-control boundary
and one baseline semantic-validation layer shared by config authoring and
runtime preflight. That layer must separate blocking invariants from
non-blocking warnings. It does not attempt to mandate every mathematically
imaginable validation or every later diagnostic surface.

---

# Motivation

The revised phonetize config surface in
[CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md)
needs one short, testable requirement that fixes the current control model and
the minimum semantic validation boundary.

This is also the smallest useful place to require shared semantic verification.
Both config authoring and runtime preflight need one implementable, auditable
rule set. The repository should leave room for later finer-grained validation
work, but the current baseline must still be precise enough to translate
directly into code without subjective "reasonableness" checks.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the current phonetize config contract is inspected, when accepted
      process keys are listed, then they are exactly:
      `phonetize.process.geminate_policy: cumulative | corrective`,
      `phonetize.process.accentuation_distribution_policy: 100_0 | 85_15 | 70_30`,
      `phonetize.process.short_pause_policy: strict | best_effort`,
      `phonetize.process.drift_policy: strict | extensible`, and
      `phonetize.process.drift_tolerance` as an integer-millisecond tolerance.
- [ ] Given the current phonetize timing-model contract is inspected, when the
      timing-value representation is described, then millisecond timing values
      are represented as positive integers in ms and
      `phonetize.timing_model.speech.pause_ratio` is represented as a
      percentage value rather than a millisecond duration.
- [ ] Given Phase 2 timing control is described by internal docs or later
      implementation records, when the ordinary recovery order is explained,
      then consonants are treated as hard pillars by default, running drift is
      used before vowel movement, and vowels are the ordinary recovery space.
- [ ] Given `phonetize.process.drift_tolerance = 0` and
      `phonetize.process.drift_policy = extensible`, when the active correction
      order is described, then the practical behavior is documented as
      vowel-first followed by unlimited drift extension because bounded drift is
      unavailable.
- [ ] Given vowel recovery is attempted, when a duration mismatch is corrected,
      then vowel adjustment remains inside the legal range of the vowel's
      current category rather than silently changing the vowel category.
- [ ] Given running drift plus legal vowel movement are exhausted, when
      `phonetize.process.drift_policy` is `strict`, then the mismatch becomes a
      fatal failure.
- [ ] Given running drift plus legal vowel movement are exhausted, when
      `phonetize.process.drift_policy` is `extensible`, then drift may extend
      beyond the preferred tolerance and the runtime reports that extension.
- [ ] Given any supported phonetizer process policy is active, when finalized
      phone or ophone frontmatter is emitted, then drift reporting still
      includes `data.drift.max`, `data.drift.mean`, and `data.drift.stddev`.
- [ ] Given short-pause behavior is documented or verified, when pause-band
      compatibility is described, then lack of any integer `N >= 1` such that
      `N * phonetize.timing_model.durations.cvc_reference` lies inside the
      configured short-pause band is treated as a warning rather than as a
      blocking invariant, and is not described as a directly observed
      empirical pause-to-`cvc_reference` relation.
- [ ] Given short-pause behavior is documented or verified, when the nearest
      integer multiple of `phonetize.timing_model.durations.cvc_reference` to
      the configured short-pause band is evaluated, then a blocking invariant
      requires the interval distance from that nearest multiple to the band to
      be less than or equal to
      `phonetize.timing_model.durations.vowels.perception_limits.long_min - phonetize.timing_model.durations.vowels.perception_limits.short_min`.
- [ ] Given long-pause behavior is documented or verified, when pause-band
      compatibility is described, then it is expressed as the existence of at
      least one integer `N >= 1` such that
      `N * phonetize.timing_model.durations.cvc_reference` lies inside the
      configured long-pause band, is treated as a blocking invariant, and is
      not described as a directly observed empirical pause-to-`cvc_reference`
      relation.
- [ ] Given the runtime may still keep a preferred pause-alignment target,
      when that preferred target is described, then it is treated as runtime
      alignment behavior inside the relevant pause band rather than as a new
      empirical claim about the band itself.
- [ ] Given pause realization is described, when a pause duration is assigned,
      then the runtime is able to add at least one integer multiple of
      `phonetize.timing_model.durations.cvc_reference` at that pause.
- [ ] Given a long pause is realized, when running drift has accumulated before
      the pause, then the runtime unloads that drift reserve completely.
- [ ] Given a short pause is realized, when running drift has accumulated
      before the pause and the configured short-pause band prevents complete
      unloading, then the runtime carries the remaining drift into the
      following phrase.
- [ ] Given semantic config verification is performed, when it is run through
      `confwriter --verify` or phonetizer preflight, then both use the same
      shared validation layer for the blocking invariants and warnings defined
      by [REQ-027](027-phonetize-config-semantic-invariants-for-shared-verification.md).
- [ ] Given shared semantic verification runs, when a blocking invariant fails,
      then verification fails and phonetizer preflight stops before Phase 2 or
      later processing begins, and pause-compatibility failures are described
      as loss of coherent isochrony based on the
      `phonetize.timing_model.durations.cvc_reference` foot.
- [ ] Given shared semantic verification runs, when only warning rules fire,
      then verification reports the warnings with their exact dotted paths and
      thresholds, plus a configuration-wide summary that presents the warning
      source as a hint, but does not fail solely because of those warnings;
      short-pause compatibility warnings must explain that pause-band settings
      no longer support clean equal-duration setup from the
      `phonetize.timing_model.durations.cvc_reference` foot.
- [ ] Given semantic validation is described at this stage, when the boundary
      is stated, then the repository requires explicit paths, relations,
      thresholds, and formulas for the current baseline rather than subjective
      reasonableness checks or every mathematically imaginable validation.

---

# User Story (optional)
> As the maintainer of the phonetizer timing-model redesign, I want a short,
> testable requirement for the current stability-first control model and
> baseline semantic verification so that later CRs can implement the runtime
> from one stable baseline.

---

# Interface Notes
- Accepted process controls:
  - `phonetize.process.geminate_policy: cumulative | corrective`
  - `phonetize.process.accentuation_distribution_policy: 100_0 | 85_15 | 70_30`
  - `phonetize.process.short_pause_policy: strict | best_effort`
  - `phonetize.process.drift_policy: strict | extensible`
  - `phonetize.process.drift_tolerance` as an integer-millisecond tolerance
- Accepted timing representation:
  - millisecond timing values represented as positive integers in ms
  - `phonetize.timing_model.speech.pause_ratio` represented as a percentage
- Special drift interaction:
      - if `phonetize.process.drift_tolerance = 0` and
            `phonetize.process.drift_policy = extensible`, the practical correction
            order becomes vowel-first and then unbounded drift extension
- Required drift reporting across policies:
      - finalized frontmatter must report `data.drift.max`
      - finalized frontmatter must report `data.drift.mean`
      - finalized frontmatter must report `data.drift.stddev`
- Pause-band interpretation:
  - runtime may keep an internal alignment target represented as
    `N * phonetize.timing_model.durations.cvc_reference` for some integer
    `N >= 1`
  - that runtime preference must not be described as a directly observed
    empirical pause-to-`cvc_reference` relation
- Validation boundary:
  - shared semantic verification layer used by `confwriter --verify` and
    phonetizer preflight
  - blocking invariants and warning rules are kept distinct
  - the exact invariant inventory is defined by
    [REQ-027](027-phonetize-config-semantic-invariants-for-shared-verification.md)
  - later records may add finer-grained semantic validations and runtime
    diagnostics
- Affected components:
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/cli/phonetizer.py`
  - `src/akkapros/cli/confwriter.py`
  - shared config and validation helpers under `src/akkapros/lib/`

---

# Open Questions
- [ ] None for now. Additional semantic validations or hard limits may be
      introduced after implementation experience if needed.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - preserve REQ-024 and REQ-025 as umbrella records
  - implement this requirement additively in later CRs that refine CR-035 and
    CR-040
  - keep the baseline validation layer shared between config verification and
    phonetizer preflight

# Related
- Related ADRs: [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md), [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md), [ADR-039](../adr/039-replacement-of-timing-model.md)
- Parent REQs: [REQ-024](024-replacement-of-timing-model.md), [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- Related CRs: [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md), [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md), [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md)

# Non-Goals
- This requirement does not fully specify the later Phase 2 solver.
- This requirement does not enumerate every future semantic validation rule.
- This requirement does not settle the full runtime diagnostics format beyond
      the required drift summary fields `max`, `mean`, and `stddev`.

# Security / Safety Considerations
- Shared semantic verification reduces the chance that config authoring and
  runtime preflight accept different timing-model values silently.
- Separating blocking invariant failures from warning-only deviations reduces
      the risk of silent acceptance on one side and subjective rejection on the
      other.
- The requirement boundary is intentionally conservative so later validation
  work can expand from a stable baseline rather than from implicit assumptions.