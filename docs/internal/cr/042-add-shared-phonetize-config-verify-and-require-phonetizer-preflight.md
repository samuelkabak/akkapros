---
cr_id: CR-042
status: Draft
priority: High
impact: Mutative
created: 2026-04-07
updated: 2026-04-08
implements: 'ADR-041, REQ-024, REQ-026, REQ-027'
---

# Change Request: Add shared phonetize config verify and require phonetizer preflight

# Summary

Add a shared phonetize-config verification layer and use it from both
`confwriter --verify` and phonetizer preflight.

This CR introduces one baseline semantic-validation path for grouped YAML
config files. It is intentionally narrow: it covers the current explicit
blocking invariants and warning rules needed to keep the phonetize config
usable, and to stop phonetizer processing before Phase 2 or later work begins
when verification fails. It does not attempt to define the final exhaustive
solver-validation regime.

Big-picture requirement chain for implementation context:

- [REQ-024](../req/024-replacement-of-timing-model.md): umbrella program story
- [REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md): timing-control and validation boundary
- [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md): concrete shared invariant inventory

---

# Motivation

[ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md),
[REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md),
and [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
establish that semantic config validation belongs to a shared layer used by
both config-authoring verification and phonetizer runtime preflight. The
repository now needs one implementation CR that defines that shared verify path,
its current boundary, and how failures surface.

Without this CR, the likely failure mode is duplication:

- `confwriter` and `phonetizer` each grow their own partially overlapping
  rule sets
- authoring-time checks and runtime checks drift apart
- vague "reasonableness" language gets translated differently in different
  call sites, producing inconsistent blocking behavior

---

# Scope

## Included

- Add a `confwriter --verify` capability for grouped YAML config validation.
- Require phonetizer to run the same validation logic before continuing into
  Phase 2 or later processing.
- Prefer one shared validation library/function rather than duplicating the
  rules in separate implementations.
- Keep the validation layer intentionally narrow for now: obvious and necessary
  semantic checks only.
- Require failure output to identify the failing full dotted path or paths,
  the failed relation, and why it failed.
- Require the shared verification result to distinguish blocking failures from
  warnings.
- Require `confwriter --verify` to report failure without mutating config.
- Require phonetizer preflight to fail before proceeding if verification fails.
- Add baseline semantic checks for the active invariant inventory under
  [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md), including:
  - approved enum-like policy inventories
  - integer timing representation for millisecond values
  - explicit numeric ordering relations needed by the model
  - pause ordering relations
  - short-pause and long-pause integer-multiple compatibility with the
    configured pause bands
  - pause-time drift discharge behavior at short and long pauses
  - warning-only deviation checks where the project has not yet accepted hard
    absolute limits
- Update docs and tests for the new verify and preflight behavior.

## Not Included

- Exhaustive future solver validation.
- Full runtime diagnostics beyond reporting path-specific verification failures
  and warnings.
- Replacing the existing schema-validity layer. This CR builds on it.
- Redefining the phonetizer Phase 2 control model itself. That work belongs to
  [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md).

---

# Current Behavior

The current internal records describe schema-driven config handling and the
revised phonetize config surface, but they do not yet define one shared
semantic verification layer used by both config-authoring verification and
phonetizer preflight.

As a result:

- key paths and basic types may be schema-valid without being semantically
  usable
- `confwriter` has no defined verify operation for grouped phonetize configs
- phonetizer preflight is not yet required to stop early on shared semantic
  verification failure
- the repository does not yet say how to surface failing paths, relations,
  severities, and reasons in a consistent way

---

# Proposed Change

Adopt the following verification contract.

## Shared validation layer

- implement one shared validation library/function for phonetize semantic
  verification
- `confwriter --verify` uses that shared validation path
- phonetizer preflight uses that same shared validation path before Phase 2 or
  any later processing continues
- schema-validity checks remain prerequisites, not replacements, for semantic
  verification

## Verification boundary

The current verify layer is intentionally narrow.

It must cover only the obvious and necessary checks needed to keep the config
usable. Every rule in this baseline must be expressible as an explicit dotted
path, threshold, relation, or formula. It must not be treated as the final
exhaustive solver-validation regime.

The specific invariant inventory for the current model is defined by
[REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md).

## Baseline semantic checks

At minimum, verification must enforce:

- key paths and value types are already schema-valid under the existing config
  system before semantic verification continues
- enum-like policy values are restricted to the approved inventories:
  - `geminate_policy: cumulative | corrective`
  - `accentuation_distribution_policy: 100_0 | 85_15 | 70_30`
  - `short_pause_policy: strict | best_effort`
  - `drift_policy: strict | extensible`
- millisecond timing values are represented as positive integers in ms
- `phonetize.timing_model.speech.pause_ratio` is validated as a percentage with
  a blocking domain check `0 < pause_ratio < 100`
- explicit numeric ordering relations hold where the model depends on them
- pause ordering relations hold
- there exists at least one integer `N >= 1` such that the corresponding
  pause-alignment relation remains compatible with the configured long-pause
  band, expressed as
  `phonetize.timing_model.durations.pauses.long.min <= N * phonetize.timing_model.durations.cvc_reference <= phonetize.timing_model.durations.pauses.long.max`
- the short-pause nearest-multiple gap remains less than or equal to
  `phonetize.timing_model.durations.vowels.perception_limits.long_min - phonetize.timing_model.durations.vowels.perception_limits.short_min`,
  where the short-pause nearest-multiple gap is defined as the minimum
  interval distance between any integer multiple
  `N * phonetize.timing_model.durations.cvc_reference` for `N >= 1` and the
  configured short-pause band, with interval distance equal to `0` inside the
  band and otherwise equal to the smaller distance to the band's `min` or
  `max` boundary
- pause realization uses integer multiples of
  `phonetize.timing_model.durations.cvc_reference` at each pause
- accumulated running drift is discharged through pauses
- long pauses must discharge accumulated running drift completely
- short pauses may carry remaining drift into the following phrase if the
  configured short-pause band prevents complete discharge
- warning-only deviation rules are applied where the project has not yet
  accepted hard absolute limits

At minimum, warning output must cover:

- `phonetize.timing_model.speech.pause_ratio > 70`
- lack of any integer `N >= 1` satisfying the configured short-pause band
  relation for `phonetize.timing_model.durations.cvc_reference`
  and therefore warning that the algorithm's isochrony target cannot be set up
  cleanly from the `cvc_reference` foot inside the configured short-pause band
- onset/coda similarity warnings when
  `abs(onset - coda) / onset >= 0.5` for a supported consonant class
- relative-deviation warnings only for the selected parameters named in
  [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
  when `abs(value - default) / default >= 0.5`

The repository may add more semantic rules later, but this CR does not require
all possible semantic or algorithmic validations now.

## Failure surfacing

### `confwriter --verify`

- reports pass, pass-with-warnings, or failure without mutating the config file
- when verification fails, identifies the failing full dotted path or paths,
  the failed relation, and the reason, including when relevant that the pause
  ranges no longer allow coherent isochrony based on the `cvc_reference` foot
- when warnings are emitted without blocking failure, identifies the warning
  dotted path, warning threshold or formula, reason, and a configuration-wide
  summary that presents the warning source as a hint, including when relevant
  that pause-band settings weaken the algorithm's coherent isochrony target
  based on the `cvc_reference` foot
- may report multiple failures in one run, but must still exit as failure if
  any verification rule fails

### Phonetizer preflight

- runs the shared verification path before continuing into Phase 2 or later
  processing
- fails before processing continues if verification fails
- reports the failing full dotted path or paths, the failed relation, and the
  reason for failure, including when relevant that the pause ranges break the
  algorithm's coherent isochrony target based on the `cvc_reference` foot
- may continue when warnings are emitted without blocking failure, but must
  report those warnings distinctly from failures and present their source as
  hints in a configuration-wide warning summary, including when relevant that
  the configured pause ranges no longer support equal-duration setup from the
  `cvc_reference` foot

Practical examples of failure messages may vary, but the output contract must
be specific enough that users can identify the broken key without guessing.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/cli/confwriter.py`
- `src/akkapros/cli/phonetizer.py`
- shared config and validation helpers under `src/akkapros/lib/`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/config/default.yaml`
- phonetizer and configuration docs under `docs/akkapros/`

Design requirements:

- shared semantic verification must be factored into reusable library code
  rather than duplicated in CLI-specific branches
- `confwriter --verify` must call the shared semantic verification path
- phonetizer preflight must call the same shared semantic verification path
- schema validation and semantic validation must remain conceptually distinct:
  semantic verification runs after schema-validity checks succeed
- the verification path must identify failures and warnings in a structured,
  deterministic way
- current semantic checks should focus on:
  - enum membership
  - integer timing representation
  - explicit numeric ordering dependencies
  - pause-band consistency
  - warning-level short-pause in-band compatibility and blocking short-pause
    nearest-multiple gap threshold
  - blocking long-pause alignment compatibility
  - pause-time drift discharge behavior
  - warning-only onset/coda similarity reporting
  - warning-only selected-parameter default-deviation reporting where hard
    limits are not yet accepted
- the verification path must remain extensible so later CRs can add narrower
  or deeper solver validations without replacing the current shared layer

Suggested validation categories:

- schema prerequisites already satisfied
- policy inventory validation
- integer timing representation validation
- numeric ordering validation
- pause-compatibility validation
- warning-threshold validation

Suggested implementation direction:

- expose one reusable result object or error collection that can be rendered by
  both `confwriter` and `phonetizer`
- model result severity explicitly so CLI behavior can distinguish blocking
  failures from warnings
- keep rendering concerns in the CLIs and rule evaluation in the shared
  library
- ensure `confwriter --verify` is read-only even when the config fails

---

# Files Likely Affected

`src/akkapros/cli/confwriter.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/lib/phonetize.py`
`src/akkapros/config/default.yaml`
`docs/akkapros/configuration.md`
`docs/akkapros/phonetizer.md`
`tests/`

---

# Acceptance Criteria

- [ ] `confwriter` exposes a `--verify` capability for grouped YAML config
      validation.
- [ ] `confwriter --verify` uses the shared phonetize semantic verification
      layer.
- [ ] `confwriter --verify` reports failure without mutating the config file.
- [ ] Phonetizer preflight uses the same shared semantic verification layer
      before Phase 2 or later processing continues.
- [ ] Phonetizer preflight fails before processing continues if verification
      fails.
- [ ] Validation output identifies the failing full dotted path or paths, the
  failed relation, and why it failed, including for pause-compatibility
  failures that coherent isochrony based on the `cvc_reference` foot can no
  longer be maintained.
- [ ] Warning output identifies the warning full dotted path, the warning
  threshold or formula, why it was emitted, and the warning source as a
  hint in a configuration-wide summary, including for short-pause
  compatibility warnings that the algorithm's isochrony target based on the
  `cvc_reference` foot is weakened or unavailable inside the configured band.
- [ ] Baseline semantic verification requires schema-valid key paths and value
      types before semantic checks continue.
- [ ] Enum-like policy values are restricted to the approved inventories.
- [ ] Millisecond timing values in the validated phonetize timing surface are
  positive integers in ms.
- [ ] `phonetize.timing_model.speech.pause_ratio` is blocked unless it
  satisfies `0 < pause_ratio < 100`.
- [ ] Explicit numeric ordering relations are verified where the current model
  depends on them.
- [ ] `phonetize.timing_model.durations.segmental_ceiling` is verified as an
  upper bound for all validated consonant and vowel timing values.
- [ ] For each consonant class under
  `phonetize.timing_model.durations.consonants`, verification enforces
  `geminate > perception_limits.geminate_min > onset` and
  `geminate > perception_limits.geminate_min > coda`.
- [ ] For each consonant class under
  `phonetize.timing_model.durations.consonants`, verification emits a warning
  when `abs(onset - coda) / onset >= 0.5`.
- [ ] `phonetize.timing_model.durations.consonants.closure.special_realization.hiatus`
      is verified as less than
      `phonetize.timing_model.durations.consonants.closure.onset`.
- [ ] `phonetize.timing_model.durations.consonants.sonorant.special_realization.vowel_transition`
      is verified as less than
      `phonetize.timing_model.durations.consonants.sonorant.onset`.
- [ ] Vowel ordering is verified as
  `short_min < short < long_min < long < very_long_min < very_long < max`.
- [ ] Pause ordering relations are verified.
- [ ] Verification emits a warning when no integer `N >= 1` satisfies
  `phonetize.timing_model.durations.pauses.short.min <= N * phonetize.timing_model.durations.cvc_reference <= phonetize.timing_model.durations.pauses.short.max`.
- [ ] Verification fails when the minimum interval distance between any
  integer multiple `N * phonetize.timing_model.durations.cvc_reference`
  for `N >= 1` and the configured short-pause band exceeds
  `phonetize.timing_model.durations.vowels.perception_limits.long_min - phonetize.timing_model.durations.vowels.perception_limits.short_min`.
- [ ] Verification confirms that there exists at least one integer `N >= 1`
  such that `N * phonetize.timing_model.durations.cvc_reference` remains
  inside the configured long-pause band
  `phonetize.timing_model.durations.pauses.long.min - phonetize.timing_model.durations.pauses.long.max`.
- [ ] Pause realization is specified to add at least one integer multiple of
  `phonetize.timing_model.durations.cvc_reference` at each pause.
- [ ] Long-pause realization is specified to unload accumulated drift
  completely.
- [ ] Short-pause realization is specified to carry remaining drift into the
  following phrase when the configured short-pause band prevents complete
  unloading.
- [ ] `phonetize.timing_model.speech.pause_ratio > 70` emits a warning but is
  not by itself a blocking failure.
- [ ] Until project-wide hard limits are added explicitly, only the selected
  parameters named in [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
  emit a warning when `abs(value - default) / default >= 0.5`.
- [ ] `confwriter --verify` exits success when warnings are present without
  blocking failures and exits failure when any blocking invariant fails.
- [ ] The current verify layer is documented as baseline semantic validation,
      not as the final exhaustive solver-validation regime.
- [ ] Tests cover shared verification behavior for both `confwriter --verify`
      and phonetizer preflight.
- [ ] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [ ] Documentation is updated in separate phonetizer and algorithm files,
  confwriter/configuration docs, generated/default config comments where
  relevant, and impacted downstream program docs such as fullprosmaker.

---

# Risks / Edge Cases

Possible issues:

- if shared verification is not factored properly, `confwriter` and phonetizer
  may drift into separate rule inventories
- if the validation boundary expands too aggressively here, the CR will freeze
  rules that the project has not actually decided yet
- if output formatting is not consistent, users may know verification failed but
  still not know which dotted path or relation caused it
- if `confwriter --verify` reuses mutation code paths carelessly, failure could
  accidentally rewrite config state

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for shared
  semantic verification, deterministic error reporting, and phonetizer
  preflight behavior

Unit tests:

- `confwriter --verify` uses the shared validation function
- phonetizer preflight uses the shared validation function
- enum inventory validation for each policy key
- integer timing representation checks for validated millisecond values
- explicit numeric ordering checks for the current timing-model dependencies
- pause ordering validation
- warning-level short-pause in-band compatibility using the configured
  short-pause band
- blocking short-pause nearest-multiple gap threshold using the configured
  short-pause band and vowel perception-limit difference
- long-pause alignment compatibility using the configured long-pause band
- pause-time drift discharge behavior for short and long pauses
- warning emission for `pause_ratio > 70`
- warning emission for onset/coda similarity when
  `abs(onset - coda) / onset >= 0.5`
- warning emission for selected-parameter default deviation when
  `abs(value - default) / default >= 0.5`
- failure rendering includes the failing full dotted path or paths, the failed
  relation, and the reason
- warning rendering includes the warning full dotted path, warning threshold or
  formula, the reason, and a configuration-wide summary hint
- `confwriter --verify` does not mutate config on success or failure

Integration tests:

- run `confwriter --verify` against a valid grouped config
- run `confwriter --verify` against a grouped config with invalid policy value
- run `confwriter --verify` against a grouped config with a blocking invariant
  violation at a supported dotted path
- run `confwriter --verify` against a grouped config that emits warnings only
- run phonetizer with a valid config and confirm preflight passes
- run phonetizer with a blocking-invalid config and confirm preflight fails
  before Phase 2 or later processing begins
- run phonetizer with a warnings-only config and confirm preflight reports
  warnings without blocking

Manual review:

- inspect verify output for clarity of failing full dotted path, failed
   relation, and reason
- inspect warning output for clarity of warning full dotted path, threshold or
  formula, and reason
- inspect docs to confirm the current boundary is described as baseline rather
  than exhaustive validation
- inspect code structure to confirm the rules are shared rather than duplicated

---

# Rollback Plan

Remove `confwriter --verify` and phonetizer preflight semantic verification in
one coordinated rollback, restoring the earlier no-shared-verify state. Partial
rollback is discouraged because it would leave one CLI using semantic
verification while the other silently bypasses it.

---

# Related Issues

- [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
- [REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
- [CR-034](034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)

---

# Tasks

## Implementation

- [ ] Add shared phonetize semantic verification helpers in library code
- [ ] Add `confwriter --verify`
- [ ] Wire phonetizer preflight to the shared verification helpers
- [ ] Implement baseline blocking invariants and warning rules only
- [ ] Implement deterministic failure and warning reporting with full dotted
  paths, relations or thresholds, and reasons

## Tests

- [ ] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [ ] Add pytest unit coverage for shared verify rules and rendering
- [ ] Add pytest integration coverage for `confwriter --verify`
- [ ] Add pytest integration coverage for phonetizer preflight failure and
  success

## Documentation

- [ ] Create or update `docs/akkapros/confwriter.md` and
  `docs/akkapros/configuration.md` for `confwriter --verify` and the shared
  validation boundary
- [ ] Create or update `docs/akkapros/phonetizer.md` for required preflight
  verification and failure behavior
- [ ] Create or update `docs/akkapros/phonetizer-algorithm.md` for the current
  semantic-validation boundary and rule categories
- [ ] Update generated/default config comments where verification-related
  semantics are described
- [ ] Update impacted downstream program docs, including
  `docs/akkapros/fullprosmaker.md`, wherever phonetizer preflight or shared
  verification affects orchestration

## Review

- [ ] Verify acceptance criteria

---

# Notes for CR-042

This CR intentionally does not try to solve every validation question. Its job
is to create one shared, implementation-ready verify path for the obvious and
necessary semantic checks that the current timing-control model already depends
on. Later CRs may add deeper solver-aware validations once the baseline shared
layer exists.