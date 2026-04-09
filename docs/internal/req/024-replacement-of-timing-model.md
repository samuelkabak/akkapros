---
req_id: REQ-024
status: Implemented
priority: High
impact: Mutative
created: 2026-04-03
updated: 2026-04-09
related_adrs: 'ADR-039'
implemented_by: 'CR-033, CR-035, CR-036, CR-037, CR-038'
---

# Requirement: Replacement of timing model

# Summary

The system shall support replacement of the current timing model used by the
metrics stage and the surrounding pipeline contracts. This requirement is the
umbrella record for the larger phonetizer-and-metricalc redesign story and is
intended to be the big-picture requirement an implementation agent can use when
working from a narrower CR.

The immediate purpose of this REQ is to reserve a stable requirement record for
the timing-model replacement program and to anchor early CRs that begin
removing assumptions from the current metrics and printer ordering, including
the introduction of a new phonetize stage between prosody and metrics.

At the current stage, REQ-024 also serves as the umbrella step for making the
new timing parameters available to the system before later narrower REQs split
the replacement story into more implementation-ready slices.

---

# Motivation

The current timing model and current placement of metrics in the pipeline are no
longer expected to remain final. The forthcoming work will change the
computation algorithm substantially, move metrics into an earlier stage role,
and require downstream consumers such as print/printer to read metrics-derived
output rather than recomputing or assuming the existing layout.

Because this is a multi-CR story, the project needs a stable parent
requirement that can accumulate scoped child changes without rewriting history
or pretending the final design is already settled.

The repository also needs one umbrella requirement that later CRs can cite
directly so an implementation agent asked to implement a single CR still has a
clear entry point to the broader program.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [x] Given the timing-model replacement program is underway, when internal
      documents are reviewed, then a stable umbrella requirement exists for the
      work.
- [x] Given follow-up CRs refine the timing-model replacement, when this
      requirement is updated, then it remains additive and historically
      consistent with earlier documented decisions.
- [x] Given the pipeline contract changes over time, when the requirement is
      expanded, then it can describe both stage-order changes and data-contract
      changes without needing to rename the parent record.
- [x] Given early CRs land before the final timing model is specified, when
      those CRs are linked, then they can reference this requirement as the
      umbrella requirement for the broader story.
- [x] Given the timing-model replacement is refined incrementally, when timing
  parameters are formalized, then the work can move out of the metrics
  config surface into a dedicated phonetize-stage config section without
  changing the umbrella requirement identity.
- [x] Given phonetize timing parameters are formalized, when their canonical
  shape is documented, then it uses the current approved `phonetize.process`
  and `phonetize.timing_model` structure, including process policies,
  `cvc_reference`, `segmental_ceiling`, consonant-class anchors with
  `perception_limits.geminate_min`, vowel perception limits, and explicit
  pause bands.
- [x] Given the timing-model replacement is refined incrementally, when timing
  defaults and parameter metadata are introduced, then they can be grouped
  in one canonical library location rather than duplicated across runtime,
  config, and CLI surfaces.
- [x] Given the new phonetize stage is introduced, when pipeline stages are
  documented, then the replacement story can include a new intermediate
  `<prefix>_phone.txt` artifact between prosody and metrics.
- [x] Given `_phone` artifact typing is refined, when phonetizer-facing records
  distinguish internal transition markers, then `˙` and `¨` remain separate
  consonant-like markers rather than collapsing `¨` into the sonorant class.
- [x] Given `_phone` is expected to support reverse reconstruction of `_tilde`,
  when phonetizer-facing boundary codes are defined, then they preserve the
  distinction between ordinary internal syllable separator `·`, enclitic dash
  `-`, internal merge `&`, explicit merge `+`, and prosodic-final termination.
- [x] Given the first timing-model parameterization step is introduced, when
  timing parameters are made available to users, then REQ-024 can act as
  the umbrella requirement for that availability step until narrower REQs
  are created.
- [x] Given the phonetize config skeleton is revised by child CRs, when later
  CLI help, config docs, or config-emission work is updated, then those
  surfaces propagate the exact approved key names and defaults rather than
  introducing divergent variants.
- [x] Given timing-model CRs change user-facing surfaces, when the work is
  specified, then each CR includes both unit-test and integration-test
  expectations for the affected timing-model paths.

---

# User Story (optional)
> As the maintainer of the timing-model redesign, I want one stable umbrella
> requirement so that multiple CRs can incrementally reshape the computation
> model without losing architectural continuity.

---

# Interface Notes
- Current scope: placeholder only; no final runtime interface is defined here
  yet.
- Anticipated affected components:
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/cli/phonetizer.py`
  - `src/akkapros/lib/metrics.py`
  - `src/akkapros/cli/metricalc.py`
  - `src/akkapros/lib/print.py`
  - `src/akkapros/cli/printer.py`
  - `src/akkapros/cli/fullprosmaker.py`
  - pipeline front matter and intermediate-output contracts
- Emerging direction already captured by child CRs:
  - removal of the configurable long-pause-weight surface from config and CLI
  - movement of timing-parameter configuration into a dedicated `phonetize`
    section rather than the `metrics` section
  - alignment of the `phonetize` section with the approved `process` and
    `timing_model` structure, including process policies, `cvc_reference`,
    `segmental_ceiling`, consonant-class anchors with
    `perception_limits.geminate_min`, vowel perception limits, and pause
    min/max bands
  - centralization of timing-model defaults and parameter metadata in shared
    library code
  - introduction of a new `phonetizer`/`phonetize` stage and `<prefix>_phone.txt`
    artifact
  - distinction inside `_phone` contracts between hiatus marker `˙` and
    vowel-transition marker `¨`
  - boundary coding inside `_phone` that is rich enough to reproduce input
    `_tilde` structure, including ordinary internal syllable separators versus
    enclitic dashes
  - temporary hard-coding of `wpm` and `pause_ratio` inside metrics until the
    phonetize-to-metrics contract is fully operational
  - propagation of approved phonetize config shapes into CLI help, config docs,
    and related stage documentation
- Child requirement map for implementation work:
  - [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md):
    two-phase phonetizer architecture and dual phone outputs
  - [REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md):
    stability-first timing-control boundary and baseline validation
  - [REQ-027](027-phonetize-config-semantic-invariants-for-shared-verification.md):
    shared phonetize semantic invariants for verification and preflight
  - [REQ-030](030-phone-ophone-only-metrics-and-interval-rhythm-computation.md):
    metricalc redesign around paired phone/ophone artifacts
  - [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md):
    detailed local Phase 2 syllable-and-pause duration solver
- Relationship to follow-up CRs:
  - this REQ is expected to be expanded incrementally as the replacement plan
    becomes concrete
  - narrower CRs may cite this REQ as the big-picture umbrella while using the
    child REQs above as implementation-ready contracts

---

# Open Questions
- [ ] What will be the final replacement timing algorithm and its governing
      data model?
- [ ] What exact metrics output artifact will become the printer input contract?
- [x] Additional narrower REQs will be needed once the umbrella scope is split
  into implementation-ready slices.
- [x] REQ-024 is the stable umbrella requirement to cite from narrower timing,
  phonetizer, verification, and metricalc CRs when implementation needs the
  broader story.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: large
- Migration: expected to proceed via multiple CRs; this placeholder does not
  authorize implementation details by itself

# Related
- Related ADRs: [ADR-039](../adr/039-replacement-of-timing-model.md)
- Child REQs: [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md), [REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md), [REQ-027](027-phonetize-config-semantic-invariants-for-shared-verification.md), [REQ-030](030-phone-ophone-only-metrics-and-interval-rhythm-computation.md), [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- Implementation CRs: [CR-033](../cr/033-remove-long-pause-weight-from-conf-and-cli-options.md),
  [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md),
  [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md),
  [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md),
  [CR-042](../cr/042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md),
  [CR-046](../cr/046-redesign-metricalc-around-phone-ophone-interval-metrics.md)

# Non-Goals
- This requirement does not define the final replacement timing algorithm yet.
- This requirement does not settle the final metrics-to-printer file format.
- This requirement does not finalize the long-term division of responsibility
  between `_phone` and `_tilde` inputs inside metricalc.
- This requirement does not itself authorize source-code changes beyond what is
  later scoped by specific CRs.

# Security / Safety Considerations
- The staged replacement should avoid partially documented transitions that
  leave pipeline consumers with ambiguous contracts.
- Intermediate records must state assumptions explicitly so later CRs do not
  silently reinterpret earlier behavior.