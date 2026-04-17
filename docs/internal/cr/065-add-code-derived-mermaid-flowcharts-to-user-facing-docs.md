---
cr_id: CR-065
status: Done
priority: Medium
impact: Additive
created: 2026-04-17
updated: 2026-04-17
implements: None
---

# Change Request: Add Code-Derived Mermaid Flowcharts to User-Facing Docs

# Summary

Add a small, high-value set of Mermaid `flowchart` diagrams to user-facing
documentation pages whose current prose is structurally correct but hard to
follow without a visual workflow.

The diagrams must not be hand-authored from documentation prose alone. Each
diagram must instead be generated from code-owned workflow data or an adjacent
code-owned descriptor that is verified against the live implementation and then
embedded into the corresponding user-facing page at a user-appropriate level of
detail.

---

# Motivation

Why is this change needed?

- Documentation clarity
- Public-doc usability
- Drift prevention between implementation and diagrams

Several user-facing pages now explain multi-stage workflows entirely in prose or
tables even though the underlying runtime follows a stable ordered pipeline.
Those pages are accurate, but the reader must reconstruct the process mentally.
Adding Mermaid flowcharts would materially improve comprehension, especially for
stage order, branching, and artifact flow.

At the same time, prose-derived diagrams are risky. If a diagram is drawn from
doc wording instead of implementation truth, it can become a second contract
that drifts from the runtime. This CR therefore requires code-derived diagrams
with an explicit verification path.

---

# Scope

## Included

- Define a code-derived Mermaid flowchart workflow for selected user-facing
  docs.
- Add a first wave of user-facing diagrams only where the current code exposes
  stable ordered processing stages that can be represented cleanly.
- Require that each published diagram be generated from code-owned workflow
  data, or from a code-adjacent workflow descriptor maintained alongside the
  implementation it documents.
- Require a verification step that checks the generated diagram content against
  both the implementation source and the destination doc anchor or placeholder.
- Keep diagram detail at user-facing level: stage names, major decisions,
  artifact flow, and public outputs, not helper-level call graphs.

## Not Included

- Hand-written Mermaid blocks authored only from doc prose.
- General-purpose automatic call-graph extraction for the whole repository.
- Diagrams for pages whose workflow is too unstable, too interactive, or too
  detailed to present cleanly in user-facing docs.
- Production behavior changes in the runtime itself, except for any narrow,
  doc-supporting metadata or descriptor additions needed to generate verified
  diagrams.

---

# Current Behavior

Current user-facing docs are text-heavy and rely on the reader to reconstruct
workflow mentally.

The strongest candidate pages identified during review are:

- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/fullprosmaker.md`
- `docs/akkapros/diphthong-processing.md`
- `docs/akkapros/metrics-computation.md`

These pages already describe stable ordered behavior visible in current code:

- `phonetizer-algorithm.md` documents Phase 1 row building, Phase 2 duration
  solving, pause handling, optional mini-pause insertion, and Phase 3
  intonation.
- `fullprosmaker.md` documents the fixed five-stage pipeline implemented by
  `run_pipeline()`.
- `diphthong-processing.md` documents the four-step split -> prosody -> restore
  -> print workflow backed by the diphthong generator/runtime mapping.
- `metrics-computation.md` documents the phone-driven inputs -> interval
  normalization -> formula application -> report outputs workflow.

Secondary candidates exist but are weaker for an initial wave:

- `docs/akkapros/configuration.md` has clear override precedence and config
  materialization flow, but it is more table-like than process-heavy.
- `docs/akkapros/phoneprep.md` contains several workflows, but they are broad,
  partly interactive, and would require more selective scoping before a clean
  user-facing diagram could be specified.

No current contract requires Mermaid diagrams to be derived from code or to be
verified against implementation truth.

---

# Proposed Change

Add a first wave of code-derived Mermaid flowcharts to the highest-value
workflow pages.

Initial target pages:

- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/fullprosmaker.md`
- `docs/akkapros/diphthong-processing.md`
- `docs/akkapros/metrics-computation.md`

Optional later wave, only if the same code-derived verification standard is met:

- `docs/akkapros/configuration.md`
- selected subsections of `docs/akkapros/phoneprep.md`

The public-doc contract for these diagrams must be:

- each diagram is generated from implementation-owned workflow structure rather
  than drawn ad hoc from prose
- each diagram is inserted into a specific user-facing doc section with a
  stable heading or placeholder contract
- each diagram shows only public-stage detail needed to understand the page
- each diagram is regenerated and checked during documentation verification so
  drift is caught when implementation changes

Required first-wave diagram intent:

- `phonetizer-algorithm.md`: one flowchart showing the public phase flow from
  row building through duration solving, pause/mini-pause handling, and
  intonation assignment into finalized phone rows
- `fullprosmaker.md`: one flowchart showing the fixed stage order and emitted
  artifacts across the full pipeline
- `diphthong-processing.md`: one flowchart showing split, prosody processing,
  restoration, and final rendering roles
- `metrics-computation.md`: one flowchart showing phone inputs, interval
  normalization/coalescing, metric computation, and output reports

---

# Technical Design

Explain how it should be implemented.

Components:

- user-facing docs under `docs/akkapros/`
- code-owned workflow sources under `src/akkapros/` and/or a narrowly scoped
  code-adjacent doc-generation module
- a verification/generation command or script that emits Mermaid text from the
  code-owned workflow source and checks destination docs

Design rules:

1. Do not parse doc prose to invent the diagram.
2. Prefer extracting workflow from existing stable implementation structure when
   that structure is already explicit.
3. If direct extraction from executable structure would be too brittle or too
   low-level, define a code-adjacent workflow descriptor next to the owning
   implementation module and treat that descriptor as code-owned source.
4. The descriptor must still be verified against the live implementation shape
   it summarizes.
5. Publish only user-facing nodes and edges. Internal helper calls, temporary
   variables, and low-level branches stay out of the diagram.

Expected implementation shape:

- `fullprosmaker` diagram should be sourced from the fixed stage order and
  artifact writes in `src/akkapros/cli/fullprosmaker.py`.
- `phonetizer` diagram should be sourced from the public phase structure in
  `src/akkapros/lib/phonetize.py`, especially row building, realization, pause
  handling, optional mini-pause insertion, and intonation/finalization steps.
- `diphthong-processing` diagram should be sourced from the generator/runtime
  workflow represented by `src/akkapros/_gencode/lib_diphthongs.py`, the
  generated replacement table, and the documented stage handoff in the active
  pipeline.
- `metrics-computation` diagram should be sourced from the current metricalc
  runtime path in `src/akkapros/lib/metrics.py` and `src/akkapros/cli/metricalc.py`.

Verification requirements:

- A repository command must regenerate Mermaid blocks from the code-owned
  workflow source.
- Verification must fail if a target doc is missing the expected insertion
  anchor or placeholder.
- Verification must fail if the generated Mermaid block differs from the block
  currently published in the target doc.
- Verification must fail if the code-owned workflow descriptor is out of sync
  with the implementation facts it claims to summarize.

Doc integration requirements:

- Each target page should contain a single clearly labeled Mermaid flowchart in
  the section where readers currently need to reconstruct the process.
- The prose around the diagram must remain authoritative and readable on its
  own; the diagram is an aid, not a replacement for the text.
- Public docs must not mention internal governance artifacts when introducing
  the diagrams.

Preferred rollout order:

1. `phonetizer-algorithm.md`
2. `fullprosmaker.md`
3. `diphthong-processing.md`
4. `metrics-computation.md`

This order follows observed reader value and current workflow stability.

---

# Files Likely Affected

docs/akkapros/phonetizer-algorithm.md  
docs/akkapros/fullprosmaker.md  
docs/akkapros/diphthong-processing.md  
docs/akkapros/metrics-computation.md  
docs/akkapros/configuration.md  
docs/akkapros/phoneprep.md  
src/akkapros/cli/fullprosmaker.py  
src/akkapros/lib/phonetize.py  
src/akkapros/lib/metrics.py  
src/akkapros/_gencode/lib_diphthongs.py  
scripts/update-indexes.py  

The final implementation may use a dedicated doc-generation script or module if
that proves cleaner than embedding workflow descriptors directly in the owning
modules.

---

# Acceptance Criteria

- [x] A code-derived Mermaid generation/verification mechanism exists for this
      documentation workflow.
- [x] `docs/akkapros/phonetizer-algorithm.md` contains a Mermaid `flowchart`
      generated from code-owned phonetizer workflow data rather than from prose.
- [x] `docs/akkapros/fullprosmaker.md` contains a Mermaid `flowchart` generated
      from the fixed live pipeline order and artifact flow.
- [x] `docs/akkapros/diphthong-processing.md` contains a Mermaid `flowchart`
      generated from the active split/restore workflow source.
- [x] `docs/akkapros/metrics-computation.md` contains a Mermaid `flowchart`
      generated from the active phone-driven metrics workflow source.
- [x] Each generated flowchart remains at user-facing detail level and does not
      expose helper-level call graphs or internal governance records.
- [x] Repository verification fails when a generated Mermaid block in a target
      doc no longer matches the code-derived source.
- [x] Repository verification fails when a target doc expected by the flowchart
      system is missing its required insertion anchor or placeholder.

---

# Risks / Edge Cases

Possible issues:

- Trying to infer diagrams from raw AST or call graphs may produce diagrams that
  are technically precise but unreadable for users.
- A workflow descriptor that is too detached from code could become a second
  stale source of truth.
- Some pages, especially `phoneprep.md`, may contain multiple overlapping flows
  and need narrower scoping before a single user-facing diagram is appropriate.
- Mermaid syntax that is too dense can hurt readability even when technically
  correct.
- Overly detailed diagrams can violate the user-facing-doc style by exposing
  internal helper structure rather than conceptual stages.

---

# Testing Strategy

Specification-aligned verification should include:

- generator test: known workflow source emits the expected Mermaid block
- doc sync test: target doc contains the generated block at the required anchor
- implementation sync test: code-owned workflow source still matches the live
  stage order or public processing facts it summarizes
- smoke verification over all registered flowchart targets

Manual review should confirm:

- diagrams improve comprehension instead of duplicating tables verbatim
- labels and node counts remain understandable to non-implementer readers
- surrounding prose and diagram do not contradict each other

---

# Rollback Plan

If the generation approach proves too brittle or too intrusive, remove the
generated Mermaid blocks and any doc-insertion hooks, then fall back to prose
only until a cleaner code-derived mechanism is specified.

Do not replace the code-derived requirement with hand-maintained diagrams as a
silent fallback. Any such policy change would require a new CR.

---

# Related Issues

Related docs reviewed during proposal:

- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/fullprosmaker.md`
- `docs/akkapros/diphthong-processing.md`
- `docs/akkapros/metrics-computation.md`
- `docs/akkapros/configuration.md`

---

# Tasks

## Implementation

- [x] Define the code-owned workflow source for each first-wave diagram
- [x] Implement Mermaid generation for the registered targets
- [x] Add doc insertion anchors/placeholders where needed
- [x] Add repository verification for generated flowchart blocks

## Tests

- [x] Add generation tests
- [x] Add doc-sync verification tests
- [x] Add implementation-sync verification tests where applicable

## Documentation

- [x] Add first-wave Mermaid flowcharts to the selected user-facing pages
- [x] Explain the generated-diagram maintenance rule in developer-facing docs if needed

## Review

- [x] Confirm first-wave diagrams remain user-facing in scope
- [x] Verify acceptance criteria


---

# Implementation Blockers

Leave empty unless implementation later discovers that one or more target
workflows cannot be represented from code-owned data without a narrower or
revised contract.

---

# Notes

Review ranking from this CR proposal:

1. `docs/akkapros/phonetizer-algorithm.md`
2. `docs/akkapros/fullprosmaker.md`
3. `docs/akkapros/diphthong-processing.md`
4. `docs/akkapros/metrics-computation.md`
5. `docs/akkapros/configuration.md`
6. selective subsections of `docs/akkapros/phoneprep.md`

The first four pages are the best fit because they already expose stable,
ordered, user-facing workflows grounded in current code.

Implementation completed on 2026-04-17 with a repository-owned flowchart
registry in `src/akkapros/lib/docflow.py`, a sync/check command in
`scripts/sync_doc_flowcharts.py`, generated Mermaid blocks in the four first-
wave target docs, and focused pytest coverage for generation and sync checks.