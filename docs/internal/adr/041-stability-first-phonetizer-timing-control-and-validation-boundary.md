---
adr_id: ADR-041
status: Accepted
created: 2026-04-07
updated: 2026-04-09
superseded_by: null
---

# 41. Stability-First Phonetizer Timing Control and Validation Boundary

## Plain Summary

The project uses a stability-first Phase 2 timing-control model in which
consonants act as hard pillars by default, vowels provide the ordinary recovery
space, and running drift is consumed before vowel movement is attempted.

This ADR does not finalize every validation rule or later solver refinement.
It freezes the current architectural interpretation so later CRs can implement
timing behavior and config verification without silently inheriting the older
midpoint-solver reading from the earlier record state.

## Context and Problem Statement

[ADR-039](039-replacement-of-timing-model.md) opened the timing-model
replacement track, [ADR-040](040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
fixed the two-phase phonetizer architecture, and
[CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md)
defines the current phonetize config surface. The repository now needs one ADR
that fixes the active Phase 2 control model and the ownership boundary for
shared validation.

## Decision Drivers

- Freeze the current timing-control architecture clearly enough for later CRs
  to implement it.
- Keep the model operationally simple: consonants stable first, vowels as the
  ordinary recovery space.
- Establish a shared validation boundary for config verification and runtime
  preflight.
- Leave room for later diagnostics, narrower validations, and solver
  refinements without reopening the architectural baseline.

## Considered Options

- Leave the Phase 2 control model implicit inside child CRs only.
- Add a dedicated ADR that fixes the stability-first model and validation
  ownership boundary.

## Decision Outcome

Chosen option: add a dedicated ADR that fixes the stability-first model and
validation ownership boundary.

Under this decision:

- The operative control value is the configured
  `phonetize.timing_model.durations.cvc_reference`, but that value is not a
  license to treat every local mismatch as a local exact-target solve problem.
- Consonants are hard pillars by default.
- Vowels are the ordinary recovery space.
- Running drift is consumed before vowel movement is attempted.
- Vowel adjustment is allowed only inside the legal range of the vowel's
  current category.
- Pause realization uses integer multiples of
  `phonetize.timing_model.durations.cvc_reference`.
- Long pauses must unload accumulated running drift completely.
- Short pauses may carry remaining drift into the following phrase when the
  configured short-pause band prevents complete unloading.
- After running drift plus legal vowel movement are exhausted, control branches
  by `phonetize.process.drift_policy`.
- `strict` means fatal failure at that point.
- `extensible` allows drift extension beyond the preferred tolerance and
  requires runtime reporting of that extension.
- Semantic config validation belongs to one shared validation layer used by
  both `confwriter --verify` and phonetizer preflight.
- That shared validation layer is split into:
  - blocking invariant checks that fail verification and stop preflight before
    Phase 2 or later processing
  - non-blocking warning checks that report suspicious deviation but do not by
    themselves fail verification
- Short-pause pause-band compatibility may surface first as a warning when no
  integer multiple of `phonetize.timing_model.durations.cvc_reference` falls
  inside the configured short-pause band, and becomes blocking only when the
  nearest-multiple gap exceeds the explicitly documented vowel perception-gap
  threshold.
- Validation rules must be stated as explicit paths, relations, thresholds, or
  formulas; vague categories such as "obviously unreasonable" are not
  sufficient on their own.
- Diagnostic messages for pause-compatibility warnings and failures must state
  that the algorithm's coherence comes from isochrony organized by the
  `phonetize.timing_model.durations.cvc_reference` foot, and that pause ranges
  which cannot support equal-duration setup from that foot undermine that
  coherence.
- The active timing-config surface uses integer millisecond values for timing
  parameters and percentage values for pause share.

This ADR intentionally does not define every future validation rule. It sets
the architecture and ownership boundary for those validations.

## Pros and Cons of the Options

### Chosen Option

- Pros: makes the active runtime interpretation explicit.
- Pros: gives later implementation CRs a clearer control order: drift first,
  then legal vowel recovery, then policy branch.
- Pros: creates one shared home for semantic config verification instead of
  letting authoring and runtime validation drift apart.
- Pros: forces later CRs and REQs to express validation in implementable,
  auditable relations rather than subjective reasonableness language.
- Cons: leaves some future validation rules intentionally unspecified.
- Cons: requires later CRs to implement the control order carefully so the
  runtime does not drift back into ad hoc redistribution.

### Other Options

- Leave the model implicit in child CRs only:
  - Pro: fewer documents.
  - Con: no clear architecture boundary for timing control and validation.

## Implications and Consequences

- Later implementation CRs must treat consonants as stable anchors by default
  rather than as the normal first recovery space.
- Later implementation CRs must treat legal vowel movement as category-bounded:
  short remains short, long remains long, very long remains very long.
- Running drift becomes a first-class timing-control mechanism rather than a
  secondary leftover after exact-target solving.
- `strict` versus `extensible` drift behavior must remain visible runtime
  policy, not hidden internal fallback.
- The validation layer must be shared between config-authoring verification and
  phonetizer runtime preflight, even if the exact rule inventory grows later.
- Blocking failures must identify the exact dotted path or paths, failed
  relation, and reason.
- Warning-only conditions must also identify the exact dotted path and the
  warning threshold that was exceeded, and they should be surfaced as hints in
  a configuration-wide warning summary.
- Later records may add finer-grained semantic validations, runtime diagnostics,
  and solver refinements, but they should not reopen the stability-first
  architectural baseline without another additive decision record.

## Links

- Parent ADR: [ADR-039](039-replacement-of-timing-model.md)
- Parent phonetizer ADR: [ADR-040](040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Parent REQ: [REQ-024](../req/024-replacement-of-timing-model.md)
- Parent phonetizer REQ: [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- Related CR: [CR-033](../cr/033-remove-long-pause-weight-from-conf-and-cli-options.md)
- Related CR: [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md)
- Related CR: [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- Related CR: [CR-036](../cr/036-define-phonetizer-phoneme-framework.md)
- Related CR: [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- Earlier Phase 2 record being narrowed: [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- Narrowing requirement created under this ADR: [REQ-026](../req/026-stability-first-phonetizer-timing-control-and-baseline-validation.md)

## Implementation Notes (optional)

- Near-term follow-up work should treat this ADR as the architectural baseline
  for the active Phase 2 implementation record.
- A later validation-focused CR or REQ may add absolute hard limits once the
  project accepts them explicitly.

## Reviewed By

- Accepted during CR-040 implementation and verification.