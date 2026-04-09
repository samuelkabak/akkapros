---
adr_id: ADR-039
status: Accepted
created: 2026-04-03
updated: 2026-04-09
superseded_by: null
---

# 39. Replacement of timing model

## Plain Summary

The project is opening a new architecture track to replace the current timing
model and to rework the position of metrics in the processing pipeline. This
ADR is intentionally a placeholder parent decision: it records that the current
timing-model architecture is no longer assumed final, while leaving the exact
replacement design to later CR-backed increments.

The immediate value of this ADR is governance, not implementation detail. It
creates a stable architectural home for the upcoming redesign so later decisions
can be added without renaming the parent story. The current active direction is
now clear enough to summarize at a high level: prune obsolete flat metrics
timing knobs, introduce a dedicated phonetize stage, centralize timing defaults
and config metadata, and treat Phase 2 as a stability-first control model over
prebuilt phone rows.

## Context and Problem Statement

The current metrics computation and current stage ordering were designed around
the existing timing model. The next development phase will replace that model
substantially and will likely change how metrics artifacts participate in the
pipeline, including a new phonetize stage between prosody and metrics and a
likely later shift where print/printer consumes a metrics-stage output rather
than operating only on the current upstream artifact shape.

That work is too large to specify correctly in a single CR or a single narrow
REQ. The repository therefore needs an umbrella ADR that acknowledges the
architectural direction change while deferring specific algorithm and file-
contract details to later additive records.

## Decision Drivers

- Preserve architectural history while the timing model is being replaced.
- Avoid pretending the current metrics ordering is final.
- Create a stable parent ADR for multiple future CRs and narrower REQs.
- Keep early transition steps documentable even before the final algorithm is
  fully specified.

## Considered Options

- Keep using the existing ADR set without creating a parent record for the new
  timing-model story.
- Write one fully specified replacement ADR now before the algorithm and stage
  contracts are settled.
- Create a placeholder parent ADR now and refine the replacement architecture
  through follow-up CRs and additional ADR/REQ records.

## Decision Outcome

Chosen option: create a placeholder parent ADR now and refine the timing-model
replacement architecture additively through follow-up CRs and further internal
records.

This ADR does not define the final replacement algorithm. It defines the
documentation strategy and acknowledges that the current timing-model
architecture is entering a replacement phase.

Near-term child CRs may therefore:

- remove flat metrics timing/config knobs that are no longer strategic
- introduce a dedicated `phonetize` config section for timing parameters
- align that `phonetize` section with the approved `process` and
  `timing_model` shape, including process policies, `cvc_reference`,
  `segmental_ceiling`, consonant-class anchors, vowel perception limits, and
  explicit pause bands
- add a new `phonetizer` / `phonetize` pipeline stage and `<prefix>_phone.txt`
  artifact
- split phonetizer work into a structure-first pass and a later duration pass,
  with dual original/accentuated phone outputs
- keep room for `_phone` contracts that distinguish hiatus marker `˙` from
  vowel-transition marker `¨` rather than flattening both into one consonant
  subclass
- centralize timing defaults and parameter metadata in shared library code
- temporarily hard-code residual metrics timing inputs until the phonetize-stage
  contract is fully wired through
- require later CLI-help, config-doc, and schema-emission changes to propagate
  the approved phonetize key shapes exactly

## Pros and Cons of the Options

### Chosen Option

- Pros: gives the redesign a stable architectural anchor immediately.
- Pros: keeps future changes additive and historically honest.
- Pros: allows early contract-pruning CRs before the final model is complete.
- Cons: leaves substantive algorithm details unresolved for now.
- Cons: requires discipline so placeholder status is not mistaken for design
  completion.

### Other Options

- Keep using only the existing ADR set:
  - Pro: no new placeholder record needed.
  - Con: later CRs would lack a clear parent architecture record.
- Write the final replacement ADR immediately:
  - Pro: would give one complete target design.
  - Con: would force premature decisions before the algorithm and data
    contracts are ready.

## Implications and Consequences

- Future timing-model changes should reference this ADR until narrower ADRs or
  superseding decisions are created.
- Early transition steps may remove or freeze existing configuration knobs even
  before the final replacement model is specified.
- Early transition steps may also move timing parameters out of metrics config
  and into a dedicated phonetize-stage section while preserving canonical
  library-side defaults.
- The phonetize-stage section now serves as the active home for timing-model
  configuration and should be kept synchronized with the current child records
  rather than with earlier draft key experiments.
- Because the grouped config feature has not been published yet, these early
  timing-model config changes do not need a backward-compatibility preservation
  layer for unpublished config-file layouts.
- At least one additional ADR is expected later once the replacement algorithm,
  metrics artifact contract, and printer-consumption contract are concrete.
- Timing-model CRs should carry explicit unit-test and integration-test
  expectations so each transition step remains verifiable despite the larger
  architecture still being in flux.
- Config-aware follow-up work should update CLI help text, confwriter output,
  default config materialization, and user/developer docs together so the
  approved phonetize schema does not drift across surfaces.

## Links

- Related REQ: [REQ-024](../req/024-replacement-of-timing-model.md)
- First implementation CR: [CR-033](../cr/033-remove-long-pause-weight-from-conf-and-cli-options.md)
- Related implementation CR: [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- Related phonetizer ADR: [ADR-040](040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Related phonetizer REQ: [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- Related implementation CR: [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- Existing timing-related context: [ADR-010](010-metrics-from-text-and-dual-percent-v.md)
- Existing pipeline context: [ADR-004](004-stage-pipeline-and-pivot-format.md)

## Implementation Notes (optional)

- Near-term work starts with contract-pruning CRs that remove assumptions from
  the current metrics CLI/config surface.
- A later ADR may still be needed for the final metrics-to-printer handoff if
  that downstream contract changes materially.

## Reviewed By

- Accepted during CR-033 through CR-038 verification and contract audit.