---
cr_id: CR-040
status: Draft
priority: High
impact: Mutative
created: 2026-04-06
updated: 2026-04-08
implements: 'ADR-040, ADR-041, REQ-024, REQ-025, REQ-026, REQ-031'
---

# Change Request: Realize phonetizer phase 2 durations from prebuilt rows

# Summary

Implement the second phase of the phonetizer program and associated
`phonetize` library.

This CR adds duration realization over the already-built phone-row streams from
[CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md).
Phase 2 must operate only on the prebuilt row streams plus the effective
`phonetize` configuration. It must follow the current stability-first control
model: consonants are stable anchors by default, running drift is consumed
before vowel movement, vowel recovery is category-bounded, and unresolved
mismatch branches by `drift_policy`.

Under this CR:

- Phase 1 row generation remains unchanged
- Phase 2 updates `duration` values in place on the prebuilt row streams
- Phase 2 fills durations for both `_ophone` and `_phone`
- the original/deaccented stream is processed first without accentuation
- accentuation is then added only to the accentuated stream
- pauses use the configured short/long pause bands and short-pause policy
- same-consonant coda/onset handling follows `geminate_policy`
- accentuation mora distribution follows
  `accentuation_distribution_policy`

Big-picture requirement chain for implementation context:

- [REQ-024](../req/024-replacement-of-timing-model.md): umbrella program story
- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md): two-phase phonetizer architecture
- [REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md): stability-first timing-control boundary
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md): detailed Phase 2 local solver

---

# Motivation

[CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
correctly stopped after structure generation with `duration=0000`, but the
phonetizer is not yet a timing stage until those rows carry non-zero durations.

This next step is sensitive because it must preserve the architectural split:
once Phase 1 has materialized the row contract, Phase 2 should work as a local
traversal over explicit segment structure and config, not as a hidden second
parsing pass over `_tilde`.

The repository also needs one stable implementation target for Phase 2 before
shared verification work in [CR-042](042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md)
is implemented. That target is now the stability-first model fixed by
[ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
and [REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md).

---

# Scope

## Included

- Implement Phase 2 duration realization in the phonetize library over
  prebuilt phone-row streams.
- Implement CLI wiring so the phonetizer writes non-zero durations for both
  `<prefix>_ophone.txt` and `<prefix>_phone.txt` once Phase 2 is enabled.
- Require that Phase 2 does not consult `_tilde` or any other upstream text
  artifact after Phase 1 rows are built.
- Require that Phase 2 classifies segments and pauses from the CR-036 row
  fields already emitted by Phase 1 rather than from source-glyph reparsing.
- Define the nominal timing anchors derived from the current
  `phonetize.timing_model` surface.
- Define the stability-first recovery order: nominal anchors, running drift,
  legal vowel recovery, then policy branch.
- Define same-consonant coda/onset handling under
  `phonetize.process.geminate_policy`.
- Define accentuation mora distribution under
  `phonetize.process.accentuation_distribution_policy`.
- Define short/long pause timing under the current pause bands and
  `short_pause_policy`.
- Define unresolved-mismatch behavior under `drift_policy`.
- Require runtime reporting in extensible mode with at least
  `drift_extension_count` and `max_drift_extension`.
- Require heavy unit, integration, and regression coverage for the duration
  algorithm and its edge cases.

## Not Included

- Redefining the Phase 1 row schema from
  [CR-036](036-define-phonetizer-phoneme-framework.md).
- Building the shared semantic verification layer itself. That work belongs to
  [CR-042](042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md).
- Finalizing the long-term metricalc-only input story.
- Replacing the existing original/accentuated dual-output model.

---

# Current Behavior

The current phonetizer architecture is split into two phases by
[ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
and [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md).

[CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
implements only Phase 1:

- `<prefix>_tilde.txt` is read once
- original and accentuated row streams are built
- all non-duration row fields are populated
- every row uses `duration=0000`
- `<prefix>_ophone.txt` and `<prefix>_phone.txt` are emitted as structure-only
  artifacts

The repository does not yet have an implemented Phase 2 contract for turning
those prebuilt rows into finalized duration-bearing streams.

---

# Proposed Change

Implement Phase 2 as a row-traversal duration algorithm that reads only the
prebuilt row streams plus the effective `phonetize` config.

## 1. Phase 2 input discipline

Phase 2 must not refer back to `_tilde`, to the original source text, or to any
other upstream text artifact after Phase 1 has materialized the row lists.

Normative rules:

- all information used by duration realization must be recoverable from the
  current row and surrounding rows
- the algorithm may inspect adjacent rows before and after the current row
- that neighborhood inspection may cross ordinary word boundaries, explicit
  merge boundaries, and internal merge boundaries
- silence rows are the only mandatory stopping points for local look-behind or
  look-ahead traversal
- the algorithm may rely on the row fields defined by CR-036
- the algorithm may rely on the effective `phonetize` configuration from
  [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- the default implementation mode is in-place update of the Phase 1 row
  objects for memory optimization
- the algorithm must not reparse the input string to recover syllable shape,
  accent, merge state, or boundary semantics that Phase 1 already encoded into
  the rows

## 2. Nominal timing anchors

Phase 2 uses the current approved timing anchors from the phonetize config:

- `phonetize.timing_model.durations.cvc_reference = 305.0`
- `one_mora_ref = 0.5 * cvc_reference`
- `two_mora_ref = cvc_reference`
- `three_mora_ref = 1.5 * cvc_reference`
- onset, coda, and geminate anchors from the consonant-class rows
- `special_realization` anchors for hiatus and vowel-transition rows
- `vowels.short`, `vowels.long`, and `vowels.very_long`
- vowel `perception_limits`
- `segmental_ceiling`
- `pauses.short.{min,max}` and `pauses.long.{min,max}`

These anchors are the nominal reference points. They do not authorize an exact-
target solver that pushes every local shape directly to a target by arbitrary
redistribution.

## 3. Stability-first control order

The practical Phase 2 control order is:

1. compute or consult the nominal timing anchors for the current local case
2. carry mismatch in running drift first
3. if still needed, adjust vowels within their legal category range
4. if still unresolved, branch by `phonetize.process.drift_policy`

Interpretation rules:

- consonants are hard pillars by default
- vowels are the ordinary recovery space
- the solver must not target vowel modification as the first correction path
  before running drift has been consumed
- vowel movement is legal only inside the range of the vowel's current
  category
- same-consonant coda/onset handling and pause discharge still remain subject
  to legality and ceiling constraints

## 4. Baseline duration realization

Phase 2 processes the original/deaccented stream first and assigns legal
baseline durations without accentuation.

Baseline obligations:

- onset rows use their configured onset or `special_realization` anchors
- coda rows use their configured coda anchors
- pause rows use the configured short/long pause bands
- vowel rows begin from the nominal mora references implied by the local
  syllable shape
- any mismatch is first absorbed in running drift before vowel movement is
  attempted
- any vowel movement that remains necessary must keep the vowel inside the
  legal range of its current category

The Phase 2 implementation may use helper logic for local shape recognition,
but that logic must remain row-driven and must not reopen `_tilde`.

## 5. Same-consonant coda/onset handling

Phase 2 must detect same-consonant coda/onset pairs across a syllable
boundary. Only same-consonant pairs count as geminate-structured pairs under
this CR.

`phonetize.process.geminate_policy` controls the pair behavior:

- `corrective` means the pair is corrected toward the configured consonant-
  class geminate target, subject to legality and ceiling constraints
- `cumulative` means the pair preserves its cumulative coda-plus-onset timing
  rather than being normalized to the configured geminate target, still subject
  to legality and ceiling constraints

Additional rules:

- the combined pair duration must satisfy
  `len(coda) + len(onset) <= phonetize.timing_model.durations.segmental_ceiling`
- when compensation is needed to preserve the ceiling, the onset side is the
  first compensating target
- non-identical adjacent consonants are not treated as geminated pairs

## 6. Accentuation augmentation

Accentuation applies only to the accentuated stream.

Each accentuated syllable receives one additional mora:

- `added_mora = 0.5 * phonetize.timing_model.durations.cvc_reference`

`phonetize.process.accentuation_distribution_policy` controls the intended
split of that added mora between the accentuated segment and its adjacent
partner:

- `100_0`
- `85_15`
- `70_30`

Interpretation rules:

- the first number is the share assigned to the accentuated segment
- the second number is the share assigned to the adjacent segment
- the adjacent segment is the onset in onset-target cases and the coda in
  coda-target cases
- distribution stops when legality limits or the segmental ceiling would be
  violated
- the algorithm must not silently switch to another named policy
- if the configured policy cannot be completed legally, unresolved mismatch
  proceeds through the same drift-first control order and then branches by
  `drift_policy`

## 7. Pause behavior and drift policy

Pause rows are classified as short or long from the Phase 1 row contract, not
from punctuation reinspection.

`phonetize.process.short_pause_policy` controls short-pause discharge:

- `strict` means short-pause discharge must remain compatible with the
  configured short-pause band and a preferred legal target derived from the
  nearest integer multiple of `cvc_reference` while attempting to unload drift
  reserve through the pause
- `best_effort` means the pause may use any legal short-band realization that
  maximizes discharge and any remainder carries into the following phrase

Pause realization rules:

- each realized pause must include at least one integer multiple of
  `phonetize.timing_model.durations.cvc_reference`
- accumulated running drift before a pause becomes reserve for discharge at
  that pause
- long pauses must unload that drift reserve completely
- short pauses carry any remaining reserve into the following phrase if the
  configured short-pause band prevents complete unloading

`phonetize.process.drift_policy` controls unresolved mismatch after running
drift plus legal vowel recovery are exhausted:

- `strict` means fatal failure
- `extensible` means drift may extend beyond
  `phonetize.process.drift_tolerance`

When `drift_policy=extensible`, runtime reporting must expose at least:

- `drift_extension_count`
- `max_drift_extension`

## 8. Library and CLI responsibilities

Expected components:

- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`

Library responsibilities:

- row-neighborhood traversal
- local shape recognition from the row stream
- baseline duration assignment
- same-consonant pair handling
- accentuation augmentation
- running-drift bookkeeping
- in-place duration updates on the Phase 1 row objects as the preferred mode
- legality checks against config ranges and ceiling constraints

CLI responsibilities:

- loading effective config
- reading Phase 1 or `_tilde`-driven row streams through the library entry
  point
- writing finalized `_ophone.txt` and `_phone.txt`
- exposing any phase-selection or debug hooks approved by later records

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/config/default.yaml`
- `tests/`
- phonetizer docs under `docs/akkapros/`

Design requirements:

- Phase 2 must traverse the Phase 1 row streams instead of rebuilding them
  from `_tilde`.
- Phase 2 must treat row-local and neighboring-row context as the sole runtime
  source of structural information.
- Neighborhood traversal must be able to look backward and forward across word
  boundaries and may stop only at silence rows.
- Phase 2 must consume the exact CR-036 row schema as emitted, including the
  split `type` / `length` fields, explicit `boundary` provenance, and the
  `realization` field.
- Phase 2 must use `cvc_reference` as the controlling heavy-syllable value.
- Baseline realization, same-consonant pair handling, and accentuation
  augmentation must be implemented as distinct ordered behaviors under one
  stability-first control model.
- Legal vowel recovery must remain category-bounded.
- Same-consonant pair handling must honor `geminate_policy` and the
  `segmental_ceiling`.
- Accentuation distribution must honor
  `accentuation_distribution_policy` exactly.
- Short-pause behavior must honor `short_pause_policy`.
- Unresolved mismatch must honor `drift_policy` and `drift_tolerance`.
- Extensible-mode reporting must include `drift_extension_count` and
  `max_drift_extension`.
- Phase 2 tests must be strong enough to detect regressions in legality,
  drift-first control order, and row-only context dependence.

Suggested implementation direction:

- isolate nominal-anchor computation from mismatch-carrying behavior
- introduce explicit running-drift bookkeeping in Phase 2 state
- apply vowel recovery through category-bounded helper logic rather than ad
  hoc redistribution
- expose extensible-mode metrics in one consistent runtime reporting object

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/config/default.yaml`
`docs/akkapros/`
`tests/`

---

# Acceptance Criteria

- [ ] Phase 2 duration realization is implemented over prebuilt phone-row
      streams rather than by reparsing `_tilde` during timing assignment.
- [ ] The phonetizer writes non-zero durations for both `<prefix>_ophone.txt`
      and `<prefix>_phone.txt`.
- [ ] The algorithm derives `one_mora_ref`, `two_mora_ref`, and
      `three_mora_ref` from
  `phonetize.timing_model.durations.cvc_reference = 305`.
- [ ] Phase 2 reads `phonetize.process.geminate_policy`,
      `phonetize.process.accentuation_distribution_policy`,
      `phonetize.process.short_pause_policy`,
      `phonetize.process.drift_policy`, and
      `phonetize.process.drift_tolerance` from config.
- [ ] Phase 2 derives consonant subclass, vowel category, phonological length,
      and pause class from the CR-036 row fields rather than from raw-text
      reparsing.
- [ ] Phase 2 neighborhood traversal may cross word boundaries and stops only
      at silence rows.
- [ ] Baseline duration realization assigns onset, coda, and special-
      realization anchors from the phonetize config.
- [ ] Mismatch is carried in running drift before vowel recovery is attempted.
- [ ] Vowel recovery remains within category-bounded legal ranges.
- [ ] Same-consonant coda/onset pairs are the only pairs treated as geminate-
      structured pairs.
- [ ] When `geminate_policy=corrective`, same-consonant coda/onset pairs are
      corrected toward the configured geminate target, subject to legality and
      ceiling constraints.
- [ ] When `geminate_policy=cumulative`, same-consonant coda/onset pairs
      preserve cumulative coda-plus-onset duration instead of forcing the
      configured geminate target.
- [ ] Same-consonant coda/onset pairs remain at or below
      `phonetize.timing_model.durations.segmental_ceiling`.
- [ ] Accentuation augmentation applies only to the accentuated stream.
- [ ] Each accentuated syllable receives one additional mora equal to
      `0.5 * phonetize.timing_model.durations.cvc_reference`.
- [ ] Accentuation distribution follows the configured
      `phonetize.process.accentuation_distribution_policy`.
- [ ] If the configured accentuation distribution cannot be completed without
      violating legality or ceiling constraints, unresolved mismatch continues
      through the drift-first control order and then branches by
      `drift_policy`.
- [ ] When no integer `N >= 1` satisfies
  `phonetize.timing_model.durations.pauses.short.min <= N * phonetize.timing_model.durations.cvc_reference <= phonetize.timing_model.durations.pauses.short.max`,
  config verification emits a warning.
- [ ] When short-pause compatibility is verified, let `short_pause_gap` be the
  minimum interval distance between any integer multiple
  `N * phonetize.timing_model.durations.cvc_reference` for `N >= 1` and
  the configured short-pause band
  `[phonetize.timing_model.durations.pauses.short.min, phonetize.timing_model.durations.pauses.short.max]`,
  where interval distance is `0` for values inside the band and otherwise
  `min(abs(value - min), abs(value - max))`; if `short_pause_gap >`
  `phonetize.timing_model.durations.vowels.perception_limits.long_min - phonetize.timing_model.durations.vowels.perception_limits.short_min`,
  config verification fails.
- [ ] When `short_pause_policy=strict`, runtime short-pause handling uses a
  preferred legal short-pause target derived from the nearest integer
  multiple of `phonetize.timing_model.durations.cvc_reference`.
- [ ] Long-pause handling remains compatible with the existence of at least one
  integer `N >= 1` such that
  `N * phonetize.timing_model.durations.cvc_reference` lies inside the
  configured long-pause band.
- [ ] Each realized pause includes at least one integer multiple of
  `phonetize.timing_model.durations.cvc_reference`.
- [ ] Long pauses unload accumulated drift reserve completely.
- [ ] When `short_pause_policy=best_effort`, short pauses may choose any legal
  short-band realization that maximizes discharge and retain any remainder
  in the following phrase.
- [ ] When `drift_policy=strict`, unresolved mismatch after running drift plus
      legal vowel recovery is a fatal failure.
- [ ] When `drift_policy=extensible`, unresolved mismatch after running drift
      plus legal vowel recovery may extend drift beyond the preferred
      tolerance.
- [ ] Extensible-mode runtime reporting includes at least
      `drift_extension_count` and `max_drift_extension`.
- [ ] Pause rows are assigned durations from the configured short/long pause
      bands.
- [ ] Unit tests cover baseline realization, same-consonant pair handling,
      accentuation augmentation, legality enforcement, drift-first control
      order, and row-only context dependence.
- [ ] Integration tests cover CLI production of finalized `_ophone.txt` and
      `_phone.txt` with non-zero durations from representative `_tilde` input.
- [ ] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [ ] Documentation is updated in separate phonetizer and algorithm files,
  configuration/confwriter docs, and impacted downstream program docs such
  as fullprosmaker and metrics-facing pages.

---

# Risks / Edge Cases

Possible issues:

- the implementation may silently consult `_tilde` again and thereby break the
  two-phase contract
- local shape recognition from row neighborhoods may be wrong at word or
  prosodic boundaries
- running drift may be added informally rather than as explicit state,
  producing inconsistent behavior
- same-consonant pair handling may satisfy the geminate policy while breaking
  the segmental ceiling
- vowel recovery may accidentally cross category boundaries if legality checks
  are not centralized
- pause handling may become nondeterministic unless one stable in-band choice
  is defined and documented

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for
  baseline realization, same-consonant pair handling, drift-first control,
  legality limits, and finalized dual-output timing behavior

Unit tests:

- compute `one_mora_ref`, `two_mora_ref`, and `three_mora_ref` from
  `cvc_reference`
- read all Phase 2 process-policy values from config
- assign baseline onset, coda, and special-realization durations from config
- verify Phase 2 reads structural information from row fields alone
- verify local traversal can look backward and forward across word boundaries
  and stops only at silence rows
- verify mismatch is carried in drift before vowel recovery is attempted
- verify vowel recovery remains category-bounded
- detect same-consonant coda/onset pairs and distinguish them from non-
  identical adjacent consonants
- verify `geminate_policy=corrective` behavior
- verify `geminate_policy=cumulative` behavior
- verify same-consonant pairs remain at or below the segmental ceiling
- verify `100_0`, `85_15`, and `70_30` apply the configured split when legal
- verify an impossible configured accentuation distribution proceeds through
  the documented drift-policy branch behavior
- verify `short_pause_policy=strict` behavior
- verify `short_pause_policy=best_effort` behavior
- verify `drift_policy=strict` behavior
- verify `drift_policy=extensible` behavior and required reporting counters
- verify the duration algorithm reads only row/context data and does not depend
  on reparsing `_tilde`

Integration tests:

- CLI run produces finalized non-zero-duration `_ophone.txt` and `_phone.txt`
- CLI results remain parseable by row readers and downstream helpers
- representative fixtures cover ordinary shapes, same-consonant coda/onset
  cases, accentuated syllables, and short and long pauses
- include side-by-side original versus accentuated output comparison so the
  accentuation pass can be verified as additive rather than destructive

Manual review:

- inspect representative original and accentuated outputs side by side
- inspect same-consonant pair examples and pause examples
- inspect code paths to verify the duration traversal does not reopen `_tilde`
- inspect extensible-mode reporting for the required counters

---

# Rollback Plan

If the Phase 2 duration algorithm proves unstable, roll back to the Phase 1
structure-only outputs from CR-039 with `duration=0000` preserved, and defer
non-zero duration realization to a narrower follow-up CR. Partial rollback
that keeps only one portion of the control model is discouraged because it
would leave policy names, runtime behavior, and reporting out of sync.

---

# Related Issues

- [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- [REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
- [CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- [CR-036](036-define-phonetizer-phoneme-framework.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- [CR-042](042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md)
- [ADR-039](../adr/039-replacement-of-timing-model.md)

---

# Tasks

## Implementation

- [ ] Add Phase 2 duration-realization library logic over prebuilt phone rows
- [ ] Keep Phase 1 structure generation separate from Phase 2 timing traversal
- [ ] Implement baseline no-accent duration assignment for the original stream
- [ ] Implement same-consonant coda/onset handling under `geminate_policy`
- [ ] Implement accentuation augmentation under
      `accentuation_distribution_policy`
- [ ] Implement drift-first mismatch handling and `drift_policy` branching
- [ ] Implement deterministic pause-duration assignment from config
- [ ] Materialize finalized non-zero durations in `_ophone.txt` and
      `_phone.txt`
- [ ] Emit extensible-mode reporting with the required counters

## Tests

- [ ] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [ ] Add extensive pytest unit coverage for baseline, gemination-policy,
  drift, and accentuation behavior
- [ ] Add pytest regression coverage for row-only context dependence
- [ ] Add pytest integration coverage for representative CLI-generated dual
  outputs

## Documentation

- [ ] Create or update `docs/akkapros/phonetizer.md` for the Phase 2 CLI,
  runtime outputs, and stage contract
- [ ] Create or update `docs/akkapros/phonetizer-algorithm.md` for the Phase 2
  duration algorithm, control order, and legality model
- [ ] Update `docs/akkapros/configuration.md`, `docs/akkapros/confwriter.md`,
  and generated/default config comments where active controls and policies
  are explained
- [ ] Update impacted downstream program docs, including
  `docs/akkapros/fullprosmaker.md` and metrics-facing docs, for `_phone`
  timing readiness and pass-through behavior

## Review

- [ ] Verify acceptance criteria

---

# Notes for CR-040

Assumptions recorded in this CR:

- Phase 2 updates durations for both the original and accentuated row streams
  using the same baseline model, with accentuation added only to the
  accentuated stream.
- Phase 2 updates the in-memory Phase 1 row lists in place as the preferred
  execution model for memory optimization.
- Pause rows already carry enough row typing from Phase 1 to distinguish short
  versus long pause categories.
- Same-consonant coda/onset handling is a process policy decision, not a
  change to the row contract.
- Shared semantic verification remains a separate concern owned by CR-042.

Open questions for approval, but not blockers to drafting this CR:

- None at this time.