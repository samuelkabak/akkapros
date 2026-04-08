---
review_id: review-006
status: Done
created: 2026-04-06
updated: 2026-04-06
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  docs/internal/req/025-two-phase-phonetizer-structure-and-duration-pipeline.md,
  docs/internal/cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md,
  docs/internal/cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md,
  docs/internal/cr/036-define-phonetizer-phoneme-framework.md,
  docs/internal/cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md,
  and docs/internal/cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md.
---

# Code and Project Review — Phonetizer Process and Algorithm

## 1. Executive Summary

The current phonetizer spec family is substantially coherent and is now strong
enough to support research verification of the intended process, even though a
single public-facing explanatory document has not yet been built. The design is
especially strong in three areas: the strict two-phase split, the explicit
`_phone` row contract, and the increasingly precise treatment of gemination,
accentuation, hiatus, and vowel-transition timing. The main remaining weakness
is not algorithmic ambiguity but documentation fragmentation: the model can be
verified from the internal records, but a researcher still has to assemble that
understanding across multiple documents. The highest-value next step is to keep
the internal phonetizer records stable and later build one researcher-facing
document from them without changing the underlying contract again.

## 2. Architecture Assessment

### 2.1 Strengths

- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md) and [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md) establish a clean two-phase architecture in which structure is materialized before timing is assigned.
- [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md) correctly treats Phase 2 as a row-traversal algorithm rather than as a second parsing pass over `_tilde`.
- [CR-036](../cr/036-define-phonetizer-phoneme-framework.md) now serves as a stable contract layer rather than mixing inventory definition with runtime selection behavior.
- [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md) places realization selection in the correct phase and resolves the important one-to-many mapping cases already identified.
- [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md) gives the timing model and process controls one canonical home under `phonetize`, which is important for later reproducibility.
- [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md) correctly keeps config editing schema-driven, which reduces the chance of research-facing examples drifting from the actual config contract.

### 2.2 Areas for Improvement

- The phonetizer story is now internally coherent, but the explanatory burden is spread across too many records for a researcher-facing read-through.
- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md) still captures the phase split at a high level but does not itself summarize later refinements such as process-level config controls, same-consonant ceiling handling, or special onset-marker timing. This is not a contradiction, but it means verification requires reading the child CRs, not the REQ alone.
- The transition note in [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md) that metrics still consumes both `_tilde` and `_phone` remains important and should be kept prominent in any later research-facing synthesis, because the phonetizer contract is stronger than the current downstream transition state.
- The process is now specified more precisely than it is narrated. In other words, the contract is clearer than the walkthrough.

## 3. Code Quality Assessment

- From a spec-quality standpoint, the phonetizer family now follows a defensible separation of concerns:
  - [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md) owns stage and config contract,
  - [CR-036](../cr/036-define-phonetizer-phoneme-framework.md) owns the row and inventory contract,
  - [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md) owns Phase 1 row construction,
  - [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md) owns Phase 2 duration realization.
- The recent removal of the badly-unbalanced heuristic from [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md) improved spec quality. The current legality-first, configured-strategy model is easier to reason about and easier to verify.
- The treatment of same-consonant gemination is now materially stronger because the spec distinguishes true geminated pairs from merely adjacent consonants.
- The explicit handling of accentuated hiatus and accentuated vowel-transition rows is a major quality improvement because it prevents silent reinterpretation of placeholder rows as ordinary lexical consonants.

## 4. Documentation Assessment

- The internal records are now sufficient to reconstruct the intended phonetizer process in research terms.
- The missing piece is consolidation, not content generation from scratch.
- A later public document should be able to explain the phonetizer faithfully by summarizing the current internal records rather than inventing new behavior.
- The most important items to preserve in any future synthesis are:
  - the distinction between `_tilde`, `_ophone`, and `_phone`,
  - the strict split between Phase 1 and Phase 2,
  - the role of row-local and neighboring-row context in Phase 2,
  - the difference between baseline timing anchors and accentuated special-case timing,
  - the role of the phonetize process-policy surface and its declared runtime
    alternatives.
- For research verification, the current docs are better read as one coherent dossier than as independent standalone texts.

## 5. Research / Functional Assessment

From a research-verification perspective, the phonetizer model is now in a good state.

- The process is explicit enough to be falsifiable:
  - input artifact,
  - structural parsing,
  - realization selection,
  - duration assignment,
  - config-controlled alternatives,
  - constraints on legal outcomes.
- The algorithm no longer relies on hidden reparsing in Phase 2, which is important for reproducibility.
- The use of hiatus placeholders to force onset-bearing structural representations is now clearly integrated into the functional model.
- The distinction between same-consonant gemination and non-geminate adjacency improves phonological credibility.
- The addition of process-level controls makes variation auditable. A reviewer can now ask not only “what does the algorithm do?” but also “under which declared process settings was this output produced?”

The main research-side limitation is that the internal docs still describe a system under staged construction. The phonetizer process itself is well specified, but the downstream metrics transition remains explicitly temporary in [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md). That limitation should be stated whenever the phonetizer is described in research prose.

## 6. Process and Engineering Practices

- ADR / REQ / CR layering is being used correctly here.
- The phonetizer work has improved over time by moving runtime rules out of contract records and into phase-owning CRs, which is good spec hygiene.
- Config surfacing through [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md) is a strong practice because it makes the research knobs explicit and editable through one schema-controlled path.
- The phonetizer records are now close to a stable internal baseline. Further changes should be made conservatively and only where they materially improve the model rather than merely rephrase it.

## 7. Recommendations (Priority Order)

1. High: Treat the current phonetizer internal records as the verification baseline for research use. Minimal next step: freeze conceptual churn unless a real algorithmic gap is discovered.
2. High: When a later documentation-build record is created, make it a synthesis-only task. Minimal next step: require the future public document to summarize [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md), [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md), [CR-036](../cr/036-define-phonetizer-phoneme-framework.md), [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md), and [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md) rather than extending them.
3. Medium: Keep the transitional metrics note prominent in any research-facing explanation. Minimal next step: ensure future phonetizer writeups clearly distinguish the phonetizer contract from the still-transitional phonetizer-to-metrics handoff.
4. Medium: Preserve the active process-control wording exactly unless there is a substantive model change. Minimal next step: keep the phonetize process-policy surface synchronized across the config contract, Phase 2 contract, and review docs.
5. Low: Later add one consolidated algorithm walkthrough for human readers. Minimal next step: produce a prose-first walkthrough with one worked example after the current internal records are accepted.

## 8. Summary Verdict

The phonetizer process and algorithm are now internally coherent enough for serious research verification, with the remaining need being consolidation into later reader-facing documentation rather than further conceptual redesign.