---
review_id: review-007
status: Done
created: 2026-04-07
updated: 2026-04-07
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  docs/internal/cr/033-remove-long-pause-weight-from-conf-and-cli-options.md,
  docs/internal/cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md,
  docs/internal/cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md,
  docs/internal/cr/036-define-phonetizer-phoneme-framework.md,
  docs/internal/cr/037-preserve-punctuation-armor-in-tilde-pivot.md,
  docs/internal/cr/038-distinguish-explicit-and-internal-merge-connectors-in-tilde-pivot.md,
  docs/internal/cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md,
  docs/internal/cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md,
  docs/internal/cr/042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md,
  their linked ADR and REQ parents, and current repo surfaces under
  src/akkapros/cli/confwriter.py, src/akkapros/lib/config.py, and
  src/akkapros/config/default.yaml.
---

# Code and Project Review — Draft CR Coherence Across Phonetizer and Confwriter Work

## 1. Executive Summary

The current draft CR family is now internally coherent as one pre-implementation
story. The phonetize configuration contract, the two-phase phonetizer
architecture, the Phase 2 duration model, and the shared verification boundary
all point at the same stable end state. The earlier duplicate Phase 2 control
record has been removed, the parent ADR and REQ records have been synchronized
to the current schema, and the confwriter-facing records no longer advertise
obsolete phonetize keys as active examples.

The main remaining gap is not specification coherence. It is implementation
lag: the live codebase still exposes the older metrics-era config and current
confwriter interface, so the repository is correctly in a state where the specs
describe the target system rather than the currently implemented one.

## 2. Architecture Assessment

### 2.1 Strengths

- The phonetize story now has one clear contract chain:
  [ADR-039](../adr/039-replacement-of-timing-model.md) as umbrella,
  [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
  for two-phase structure,
  [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
  for timing-control architecture,
  [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md)
  for config and stage surface,
  [CR-036](../cr/036-define-phonetizer-phoneme-framework.md) for row contract,
  [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
  for Phase 1,
  [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
  for the active Phase 2 implementation target, and
  [CR-042](../cr/042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md)
  for shared verification.
- The confwriter-facing records now align with the approved phonetize schema
  rather than with provisional draft keys.
- The Phase 2 story now has one active implementation record instead of a split
  between structural traversal and a separate correction-layer CR.

### 2.2 Areas for Improvement

- The draft stack is coherent, but it is still spread across many records. A
  later researcher-facing synthesis document would still be useful once the
  implementation lands.
- The umbrella records remain intentionally broad. That is acceptable, but the
  implementation CRs should continue to be the place where runtime details are
  fixed.

## 3. Code Quality Assessment

- The live repo surface is still on the pre-phonetize config model. The checked-
  in default config still exposes `metrics.wpm`, `metrics.pause_ratio`, and
  `metrics.long_punct_weight` at
  [src/akkapros/config/default.yaml](../../src/akkapros/config/default.yaml#L83),
  [src/akkapros/config/default.yaml](../../src/akkapros/config/default.yaml#L85), and
  [src/akkapros/config/default.yaml](../../src/akkapros/config/default.yaml#L87).
- The live shared schema still materializes those keys and forwards them into
  `fullprosmaker` at
  [src/akkapros/lib/config.py](../../src/akkapros/lib/config.py#L87),
  [src/akkapros/lib/config.py](../../src/akkapros/lib/config.py#L91),
  [src/akkapros/lib/config.py](../../src/akkapros/lib/config.py#L92),
  [src/akkapros/lib/config.py](../../src/akkapros/lib/config.py#L93),
  [src/akkapros/lib/config.py](../../src/akkapros/lib/config.py#L145),
  [src/akkapros/lib/config.py](../../src/akkapros/lib/config.py#L146), and
  [src/akkapros/lib/config.py](../../src/akkapros/lib/config.py#L147).
- The live `confwriter` CLI still implements the older flag-per-key surface,
  not the schema-operation model described in
  [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md),
  at [src/akkapros/cli/confwriter.py](../../src/akkapros/cli/confwriter.py#L50),
  [src/akkapros/cli/confwriter.py](../../src/akkapros/cli/confwriter.py#L83),
  [src/akkapros/cli/confwriter.py](../../src/akkapros/cli/confwriter.py#L90), and
  [src/akkapros/cli/confwriter.py](../../src/akkapros/cli/confwriter.py#L101).
- These are implementation gaps, not spec conflicts. They should be handled by
  implementation work against the now-synchronized draft set.

## 4. Documentation Assessment

- The draft records now present one stable phonetizer/confwriter target state.
- Obsolete phonetize key names are no longer required reading in the active
  draft contract stack.
- The older review set no longer blocks understanding because the current
  coherence review supersedes it for draft-family alignment.

## 5. Research / Functional Assessment

- The phonetizer process remains research-legible:
  structure is built first, durations are realized later, and timing behavior
  is controlled through declared process policies and shared validation.
- The model is now easier to implement consistently because the active Phase 2
  control story is concentrated in one record.
- The downstream metrics transition remains explicitly transitional in
  [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md),
  which is correct and should remain visible until implementation catches up.

## 6. Process and Engineering Practices

- The draft set now uses the internal-doc process pragmatically: where nothing
  has been implemented yet, the records were synchronized directly rather than
  preserving unnecessary draft-era churn.
- Removing the redundant Phase 2 correction CR reduces implementation
  complexity and avoids circular interpretation.
- The remaining engineering task is straightforward: implement against the
  current synchronized records rather than against a mixed historical stack.

## 7. Recommendations (Priority Order)

1. High: Treat the current synchronized draft stack as the implementation
   baseline. Minimal next step: implement the config and phonetizer changes
   against [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md),
   [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md),
   [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md),
   [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md), and
   [CR-042](../cr/042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md).
2. High: Keep implementation sequencing aligned with the current codebase gap.
   Minimal next step: land config-surface and confwriter changes before or with
   the phonetizer CLI so the runtime and schema move together.
3. Medium: After implementation, regenerate indexes and produce one
   researcher-facing synthesis document. Minimal next step: defer that writing
   until the code matches the synchronized specs.

## 8. Summary Verdict

The draft CR family is now review-clean as a single pre-implementation
specification set. Remaining work is implementation and later consolidation,
not additional coherence repair.