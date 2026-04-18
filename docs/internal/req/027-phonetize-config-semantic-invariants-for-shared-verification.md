---
req_id: REQ-027
status: Implemented
priority: High
impact: Mutative
created: 2026-04-07
updated: 2026-04-18
related_adrs: 'ADR-041'
implemented_by: 'CR-042, CR-067, CR-068, CR-069'
---

# Requirement: Phonetize Config Semantic Invariants for Shared Verification

# Summary

The system shall treat a defined set of phonetize timing-config relations as
required blocking semantic invariants for shared verification, plus a small
warning-only deviation layer. This requirement narrows and makes explicit the
baseline semantic-validation boundary introduced by
[REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
without pretending that every mathematically possible check is part of the
current model.

The purpose of this requirement is to record the exact relations that the
active timing model depends on, using full dotted config paths so that later
verification work in `confwriter --verify` and phonetizer preflight can remain
specific, consistent, and auditable.

This requirement also preserves the current project stance that consonant onset
and coda anchors are the hard lower-side pillars, that the exposed
consonant-side legality surface now spans `geminate_min` through
`gemination_max`, and that pauses and
`phonetize.timing_model.durations.cvc_reference` are empirically grounded but
speech-rate-sensitive, and that runtime isochrony may use these values
internally without claiming that the empirical pause studies directly measured
the same relation.

---

# Motivation

[REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
requires shared baseline semantic verification, but it intentionally stops at a
high-level boundary. The repository now needs one short, testable requirement
that names the actual invariants the active phonetize timing model depends on.

Without this narrower requirement, later verification work risks becoming
underspecified in exactly the places where the model needs explicit relations:
policy inventories, integer timing representation, threshold ordering,
pause-band compatibility, warning policy, and failure reporting. This document
keeps that invariant set concrete while still avoiding overreach into
unaccepted absolute hard limits.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given phonetize process-policy values are verified, when enum membership
      is checked, then `phonetize.process.geminate_policy` is restricted to
      `cumulative | corrective`.
- [ ] Given phonetize process-policy values are verified, when enum membership
      is checked, then `phonetize.process.accentuation_distribution_policy` is
  restricted to `100_0 | 95_05 | 90_10 | 85_15 | 80_20 | 75_25 | 70_30`.
- [ ] Given phonetize timing config is verified, when the integer timing
      representation is checked, then `phonetize.process.drift_tolerance` and
      every numeric value under `phonetize.timing_model.durations` are positive
      integers measured in milliseconds.
- [ ] Given phonetize timing config is verified, when speech-control scalars
      are checked, then `phonetize.timing_model.speech.wpm` is a positive
      integer and `phonetize.timing_model.speech.pause_ratio` satisfies
      `0 < phonetize.timing_model.speech.pause_ratio < 100`.
- [ ] Given segment and vowel timing values are verified, when the shared
  validation bounds are checked, then
  `phonetize.timing_model.durations.vowels.perception_limits.elongation_max` and each
  `phonetize.timing_model.durations.consonants.<class>.perception_limits.gemination_max`
  are less than or equal to
  `phonetize.timing_model.durations.segmental_ceiling`.
- [ ] Given lower timing bounds are verified, when the shared validation floor
  is checked, then
  `phonetize.timing_model.durations.vowels.perception_limits.short_min`,
  `phonetize.timing_model.durations.vowels.perception_limits.long_min`,
  `phonetize.timing_model.durations.vowels.perception_limits.very_long_min`,
  each consonant-class `onset`, `coda`, and `perception_limits.geminate_min`,
  plus `phonetize.timing_model.durations.consonants.closure.special_realization.hiatus`
  and
  `phonetize.timing_model.durations.consonants.sonorant.special_realization.vowel_transition`
  are greater than or equal to
  `phonetize.timing_model.durations.segmental_floor`.
- [ ] Given a consonant class `K` in `{closure, fricative, sonorant}` is
      verified, when its core timing row is checked, then all of the following
      hold:
  `phonetize.timing_model.durations.consonants.K.onset < phonetize.timing_model.durations.consonants.K.perception_limits.geminate_min <= phonetize.timing_model.durations.consonants.K.geminate <= phonetize.timing_model.durations.consonants.K.perception_limits.gemination_max <= phonetize.timing_model.durations.segmental_ceiling`, and
  `phonetize.timing_model.durations.consonants.K.coda < phonetize.timing_model.durations.consonants.K.perception_limits.geminate_min <= phonetize.timing_model.durations.consonants.K.geminate <= phonetize.timing_model.durations.consonants.K.perception_limits.gemination_max <= phonetize.timing_model.durations.segmental_ceiling`.
- [ ] Given `phonetize.timing_model.durations.consonants.closure.special_realization.hiatus`
      is verified, when its ordering is checked, then it is a positive integer
      in ms and it is less than both
      `phonetize.timing_model.durations.consonants.closure.onset` and
      `phonetize.timing_model.durations.consonants.closure.coda`.
- [ ] Given `phonetize.timing_model.durations.consonants.sonorant.special_realization.vowel_transition`
      is verified, when its ordering is checked, then it is a positive integer
      in ms and it is less than both
      `phonetize.timing_model.durations.consonants.sonorant.onset` and
      `phonetize.timing_model.durations.consonants.sonorant.coda`.
- [ ] Given vowel timings are verified, when category ordering is checked, then
      all of the following hold:
      `phonetize.timing_model.durations.vowels.perception_limits.short_min < phonetize.timing_model.durations.vowels.short < phonetize.timing_model.durations.vowels.perception_limits.long_min < phonetize.timing_model.durations.vowels.long < phonetize.timing_model.durations.vowels.perception_limits.very_long_min < phonetize.timing_model.durations.vowels.very_long < phonetize.timing_model.durations.vowels.perception_limits.elongation_max`.
- [ ] Given pause timings are verified, when band ordering is checked, then all
      of the following hold:
      `phonetize.timing_model.durations.pauses.short.min < phonetize.timing_model.durations.pauses.short.max`,
      `phonetize.timing_model.durations.pauses.long.min < phonetize.timing_model.durations.pauses.long.max`, and
      `phonetize.timing_model.durations.pauses.short.max < phonetize.timing_model.durations.pauses.long.min`.
- [ ] Given short-pause target compatibility is verified, when the pause-band
  relation is checked, then a warning is emitted if there does not exist
  an integer `N >= 1` such that
  `phonetize.timing_model.durations.pauses.short.min <= N * phonetize.timing_model.durations.cvc_reference <= phonetize.timing_model.durations.pauses.short.max`.
- [ ] Given short-pause target compatibility is verified, when the nearest
  integer multiple of `phonetize.timing_model.durations.cvc_reference` to
  the configured short-pause band is checked, then let
  `short_pause_gap` be the minimum interval distance between any integer
  multiple `N * phonetize.timing_model.durations.cvc_reference` for
  `N >= 1` and the band
  `[phonetize.timing_model.durations.pauses.short.min, phonetize.timing_model.durations.pauses.short.max]`,
  where interval distance is `0` for values inside the band and otherwise
  `min(abs(value - min), abs(value - max))`; a blocking failure is raised
  if `short_pause_gap > phonetize.timing_model.durations.vowels.perception_limits.long_min - phonetize.timing_model.durations.vowels.perception_limits.short_min`.
- [ ] Given long-pause target compatibility is verified, when the pause-band
  relation is checked, then there exists an integer `N >= 1` such that
  `phonetize.timing_model.durations.pauses.long.min <= N * phonetize.timing_model.durations.cvc_reference <= phonetize.timing_model.durations.pauses.long.max`.
- [ ] Given pause realization behavior is documented for the active model, when
  a pause is described, then its realized duration includes at least one
  integer multiple of `phonetize.timing_model.durations.cvc_reference`.
- [ ] Given long-pause realization behavior is documented for the active
  model, when accumulated drift reaches a long pause, then that drift is
  unloaded completely at the pause.
- [ ] Given short-pause realization behavior is documented for the active
  model, when accumulated drift reaches a short pause and the configured
  short-pause band prevents complete unloading, then the remaining drift is
  carried into the following phrase.
- [ ] Given `phonetize.timing_model.speech.pause_ratio` is verified, when the
      current warning boundary is checked, then a warning is emitted if
      `phonetize.timing_model.speech.pause_ratio > 70` and no blocking failure
      is required solely because of that warning.
- [ ] Given a consonant class `K` in `{closure, fricative, sonorant}` is
      verified, when onset-coda similarity is checked, then a warning is
      emitted if
      `abs(phonetize.timing_model.durations.consonants.K.onset - phonetize.timing_model.durations.consonants.K.coda) / phonetize.timing_model.durations.consonants.K.onset >= 0.5`.
- [ ] Given any of the following parameters is verified before project-wide
      hard limits are added:
      `phonetize.timing_model.speech.wpm`,
      `phonetize.timing_model.durations.segmental_ceiling`,
  `phonetize.timing_model.durations.segmental_floor`,
      `phonetize.timing_model.durations.cvc_reference`,
      `phonetize.timing_model.durations.consonants.<class>.perception_limits.geminate_min`,
  `phonetize.timing_model.durations.consonants.<class>.perception_limits.gemination_max`,
      `phonetize.timing_model.durations.vowels.perception_limits.long_min`,
      `phonetize.timing_model.durations.vowels.perception_limits.very_long_min`,
  `phonetize.timing_model.durations.vowels.perception_limits.elongation_max`,
      `phonetize.timing_model.durations.pauses.short.min`, and
      `phonetize.timing_model.durations.pauses.long.min`,
      when relative deviation from the documented default is checked, then a
      warning is emitted if `abs(value - default) / default >= 0.5`.
- [ ] Given semantic verification fails for one of these blocking invariants,
      when failure output is rendered, then it identifies the exact full dotted
  path or paths involved, the failed relation in readable form, and the
  severity as blocking failure, and for pause-compatibility failures it
  states that the algorithm establishes isochrony from the
  `phonetize.timing_model.durations.cvc_reference` foot and that the
  configured pause ranges no longer support that coherence.
- [ ] Given warning output is rendered for one of these warning rules, when it
      is shown to the user, then it identifies the exact full dotted path, the
      warning threshold or formula that was exceeded, the severity as warning,
  and a configuration-wide summary that presents the warning source as a
  hint rather than as a blocking error, and for short-pause compatibility
  warnings it states that the algorithm's isochrony target is organized by
  the `phonetize.timing_model.durations.cvc_reference` foot and is not
  cleanly supported by the configured pause band.
- [ ] Given the invariant boundary is documented, when non-invariants are
      listed, then the documentation does not introduce any of the following as
      current blocking rules: a global rule `onset < coda` or `coda < onset`
      across all consonant classes, a claim that empirical pause studies proved
      `pause = N * cvc_reference`, a separate exposed `singleton_min` check in
      the active model surface, or absolute hard limits that the project has
      not yet accepted explicitly.
- [ ] Given exposed consonant timing rows are documented, when the validator's
      supported surface is described, then each consonant row is described in
      terms of the full dotted paths under
      `phonetize.timing_model.durations.consonants.closure.*`,
      `phonetize.timing_model.durations.consonants.fricative.*`, and
  `phonetize.timing_model.durations.consonants.sonorant.*` with exposed
  `onset`, `coda`, `geminate`, `perception_limits.geminate_min`, and
  `perception_limits.gemination_max`, and
      without introducing an exposed `singleton_min` requirement.

---

# User Story (optional)
> As the maintainer of shared phonetize config verification, I want the active
> semantic invariants written down as exact dotted-path relations so that
> `confwriter --verify` and phonetizer preflight can enforce the same model
> without guesswork or drift.

---

# Interface Notes
- Input:
  - grouped YAML config under `phonetize.process` and
    `phonetize.timing_model`
- Active accepted process surface:
  - `phonetize.process.geminate_policy: cumulative | corrective`
  - `phonetize.process.accentuation_distribution_policy: 100_0 | 95_05 | 90_10 | 85_15 | 80_20 | 75_25 | 70_30`
  - `phonetize.process.drift_tolerance` as an integer-millisecond value
- Active numeric representation:
  - every numeric value under `phonetize.timing_model.durations` is an
    integer number of milliseconds
  - `phonetize.timing_model.speech.wpm` is a positive integer
  - `phonetize.timing_model.speech.pause_ratio` is a percentage
- Consonant-row methodology:
  - consonant onset and coda anchors are the hard lower-side pillars
  - the exposed operative consonant-side legality band spans
    `phonetize.timing_model.durations.consonants.<class>.perception_limits.geminate_min`
    through
    `phonetize.timing_model.durations.consonants.<class>.perception_limits.gemination_max`
  - the active surface does not expose `singleton_min`
- Pause and CVC methodology:
  - pause-band bounds and `phonetize.timing_model.durations.cvc_reference`
    are configured values whose compatibility is checked by explicit
    relations rather than by subjective reasonableness language
  - runtime isochrony may use these values internally without claiming that
    empirical pause studies directly measured
    `pause = N * phonetize.timing_model.durations.cvc_reference`
- Output:
  - pass/fail semantic verification result for blocking invariants with exact
    dotted-path references, readable failed relations, and model-specific
    reason text
  - warning output for non-blocking deviation rules with exact dotted-path
    references, readable threshold text, and a configuration-wide summary with
    the warning source presented as a hint
- Affected components:
  - `src/akkapros/cli/confwriter.py`
  - `src/akkapros/cli/phonetizer.py`
  - shared validation helpers under `src/akkapros/lib/`
- Requirement relationship:
  - this requirement narrows the baseline validation boundary in
    [REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
  - this requirement is intended to guide implementation work under
    [CR-042](../cr/042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md)

---

# Open Questions
- [ ] Should long-pause alignment compatibility remain conditional on runtime
      alignment being active, or should a later record make it mandatory in all
      supported timing modes?
- [ ] Which absolute hard limits should replace or supplement the current
      relative-deviation warning rules after this baseline is in place?

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - preserve REQ-026 as the broader baseline-validation requirement
  - implement this narrower invariant inventory additively under CR-042 or a
    direct follow-up verification CR
  - keep failure output path-specific and readable rather than reducing errors
    to generic pass/fail messages

# Related
- Related ADRs: [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
- Parent Requirement: [REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
- Related CRs: [CR-042](../cr/042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md), [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md), [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md)

# Non-Goals
- This requirement does not enumerate every mathematically possible semantic
  check.
- This requirement does not redefine the stability-first Phase 2 runtime model.
- This requirement does not require proof of every accent redistribution case.
- This requirement does not require warning-only deviation rules to fail
  verification before the project accepts corresponding hard limits.
- This requirement does not paraphrase required key paths into shortened alias
  forms for the normative invariant statements.
- This requirement does not rewrite earlier ADRs, REQs, or CRs as though these
  invariants had always been stated this way.

# Security / Safety Considerations
- Shared invariant enforcement reduces the chance that config authoring and
  runtime preflight diverge on timing-model validity.
- Path-specific failure output lowers the risk of unsafe manual guessing when a
  timing configuration is rejected.
- Restricting the invariant inventory to model-dependent relations reduces the
  risk of enforcing invented rules that the project has not actually accepted.
