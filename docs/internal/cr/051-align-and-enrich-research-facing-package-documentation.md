---
cr_id: CR-051
status: Done
priority: High
impact: Additive
created: 2026-04-11
updated: 2026-04-11
implements: 'ADR-034, ADR-045, REQ-019, REQ-030, REQ-032'
---

# Change Request: Align and enrich research-facing package documentation

# Summary

Add a documentation-focused change that reviews package documentation against the
current runtime and enriches the public docs so researchers can understand what
the toolkit does, how the core algorithms work, what each stage reads and
writes, and how to interpret the main outputs.

The goal is not to change runtime behavior. The goal is to make the existing
behavior legible, current, and internally consistent across the package docs,
especially for the prosody, phonetizer, and metrics stages.

---

# Motivation

The repository already contains substantial documentation, but the explanation
is spread across public docs, ADRs, REQs, CRs, and code. That makes the project
harder to evaluate as a research tool, because important rationale and active
behavior are discoverable only by cross-reading governance records and source
files.

The current public docs also have uneven depth and audience targeting. Some
pages already explain algorithmic behavior well, while others remain terse,
partly outdated, or too implementation-shaped for the main researcher audience.
This CR creates a focused documentation pass that brings the package docs back
in line with the live code and active internal contracts.

---

# Scope

## Included

- Review the main package documentation under `docs/akkapros/` against the live
  code and currently active ADR/REQ/CR records.
- Update researcher-facing docs so they explain stage purpose, algorithm shape,
  usage, inputs, outputs, and interpretation in accessible language.
- Consolidate currently scattered explanations for the prosody realization
  algorithm, the phonetizer pipeline, and the metrics model.
- Add or reorganize public documentation files under `docs/akkapros/` when a
  cross-cutting explanation cannot be kept clear inside the existing pages.
- Preserve a clearer split between general package docs and library-facing
  technical reference material.

## Not Included

- Changing accepted runtime behavior in `src/` or redefining existing output
  contracts.
- Reopening accepted policy decisions from ADR-034, ADR-045, REQ-019,
  REQ-030, or REQ-032.
- Writing new developer-focused implementation guides outside the library docs.

---

# Current Behavior

The repository already ships public documentation for `prosmaker`,
`phonetizer`, `metricalc`, the prosody algorithm, and metrics computation, but
the explanation is fragmented.

Concrete current issues include:

- key algorithm explanations are split between public docs and internal records
  instead of being readable in one researcher-facing path
- some active runtime details introduced by recent records are not yet explained
  consistently across all related pages
- stage usage and stage outputs are documented per page, but the package-level
  workflow remains harder to follow than necessary for new research users
- some pages are still more implementation-shaped than audience-shaped

Examples of active behavior that documentation must now reflect consistently:

- prosody documentation must explain the active `bi` and `mono` mora modes,
  explicit `+` linking, automatic `&` merging, and the role of `_tilde.txt`
- phonetizer documentation must explain the current three-pass model, the
  canonical 11-field phone-row contract, typed pauses, symbolic intonation
  tokens, and row-derived MBROLA export
- metrics documentation must explain that metricalc now consumes paired
  `_phone.txt` and `_ophone.txt` artifacts directly rather than using
  `_tilde.txt` as the active downstream metrics input

---

# Proposed Change

- Perform a targeted documentation alignment review for the main public package
  docs against the current runtime and active governance.
- Update the package docs so a researcher can understand, without reading code,
  the following:
  - what each major stage does
  - what each stage consumes and emits
  - how the accentuation and phonetizer algorithms proceed step by step
  - what the principal metrics mean and how to read them
  - which outputs are pivots, intermediate artifacts, or user-facing outputs
- Rework wording so most public docs stay researcher-facing and explanatory,
  while developer-oriented detail is kept mainly in library reference pages.
- Where necessary, add one or more new documentation pages under
  `docs/akkapros/` to hold cross-cutting explanations that currently do not fit
  cleanly into stage-specific CLI pages.

---

# Technical Design

Architecture notes:

Components:
- public package docs under `docs/akkapros/`
- internal source-of-truth records under `docs/internal/`
- live runtime behavior in `src/akkapros/lib/` and `src/akkapros/cli/`

Documentation model:
- stage guides should explain purpose, command usage, inputs, outputs, and
  artifact roles
- algorithm pages should explain behavior, decision flow, and representative
  worked examples in researcher-facing language
- library-facing reference material may retain field tables, row schemas,
  and contract-level terminology where needed

Verification basis:
- compare public docs against the active behavior in:
  - `src/akkapros/lib/prosody.py`
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/lib/metrics.py`
  - relevant CLI wrappers and current tests
- resolve documentation conflicts in favor of the newer directly relevant
  accepted internal record when older text remains as history only

Implementation constraints:
- documentation changes only
- no production code or test behavior changes required by this CR
- if an example depends on an active artifact contract, it must match the live
  code and accepted internal records

---

# Files Likely Affected

docs/akkapros/prosmaker.md
docs/akkapros/prosody-realization-algorithm.md
docs/akkapros/phonetizer.md
docs/akkapros/phonetizer-algorithm.md
docs/akkapros/phonetizer-phone-file-guide.md
docs/akkapros/metricalc.md
docs/akkapros/metrics-computation.md
docs/akkapros/fullprosmaker.md
docs/akkapros/configuration.md
docs/internal/cr/index.md

One or more new files under `docs/akkapros/` may also be added if needed.

---

# Acceptance Criteria

- [x] The main package docs for prosody, phonetizer, metrics, and full-pipeline
      usage are reviewed against current runtime behavior and active governance.
- [x] Public documentation no longer contradicts the active contracts from
      ADR-034, ADR-045, REQ-019, REQ-030, or REQ-032.
- [x] The prosody documentation explains the current accentuation workflow,
      including style choice, mora mode, grouping behavior, merge notation, and
      the role of `_tilde.txt`, using researcher-facing language.
- [x] The phonetizer documentation explains the current three-pass model,
      canonical phone-row fields, typed pause behavior, intonation token system,
      and emitted artifacts (`_ophone.txt`, `_phone.txt`, `_ombrola.pho`,
      `_mbrola.pho`) in a way a non-developer researcher can follow.
- [x] The metrics documentation explains the active input contract, the core
      rhythmic metrics, what those metrics mean, how to interpret them, and the
      limits of those interpretations.
- [x] Stage-oriented docs clearly explain command usage, expected inputs,
      produced outputs, and how each artifact participates in the pipeline.
- [x] General public docs minimize developer-facing jargon; library reference
      docs may remain more technical where contract detail is required.
- [x] If new documentation pages are added, they integrate cleanly with the
      existing docs structure instead of duplicating or fragmenting the same
      explanation again.
- [x] The CR is satisfied without changing production runtime behavior.

---

# Risks / Edge Cases

Possible issues:

- documentation may restate behavior inaccurately if examples are copied from
  superseded internal wording rather than from the live runtime
- the documentation pass may become too code-shaped and lose the intended
  researcher-facing tone
- new explanatory pages may duplicate existing material unless page roles are
  assigned clearly
- reviewers may try to treat documentation gaps as an excuse to reopen accepted
  runtime decisions that this CR does not change

---

# Testing Strategy

Documentation review:

- compare updated public docs against the current code paths and active ADR/REQ
  records
- verify that examples, field descriptions, and artifact flows match the live
  contracts already covered by tests

Command verification:

- when command examples or output references are updated, verify them against
  current CLI help, current artifact naming, and existing passing test coverage

Manual review:

- review the final docs for audience fit, especially whether general package
  docs remain researcher-facing rather than implementation-facing

---

# Rollback Plan

If the documentation rewrite introduces confusion or factual drift, revert the
documentation-only changes and keep the current runtime behavior unchanged.

---

# Related Issues

- [ADR-034](../adr/034-prosody-mora-modes-and-explicit-link-locking.md)
- [ADR-045](../adr/045-three-pass-phonetizer-intonation-and-row-derived-mbrola.md)
- [REQ-019](../req/019-prosody-mora-mode-selection.md)
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md)
- [REQ-032](../req/032-phonetizer-intonation-and-three-pass-finalization.md)
- [CR-041](041-add-phonetizer-phase-2-follow-up-docs-and-test-coverage.md)
- [CR-046](046-redesign-metricalc-around-phone-ophone-interval-metrics.md)
- [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)

---

# Tasks

## Implementation

- [x] Review the relevant public docs against live runtime behavior
- [x] Rewrite or expand the affected package docs
- [x] Add new public documentation pages if cross-cutting explanation requires
      them

## Tests

- [x] Verify documentation examples and artifact descriptions against current
      runtime contracts and passing tests

## Documentation

- [x] Clarify package-level workflow and stage handoff explanations
- [x] Enrich the prosody algorithm explanation for researchers
- [x] Enrich the phonetizer algorithm and phone-table explanation for
      researchers
- [x] Enrich the metrics explanation, including interpretation and limitations

## Review

- [x] Confirm the updated docs stay aligned with active governance
- [x] Confirm the public-doc tone remains appropriate for researchers
- [x] Verify acceptance criteria


---

# Implementation Blockers

Use this section when implementation or verification cannot proceed safely.

Leave the section empty if no blockers are known.

---

# Notes

This CR is grounded in a documentation review of the current public docs and
the live phonetizer and metrics contracts, including the active three-pass
phonetizer runtime and phone/ophone-driven metrics pipeline.

The change should consolidate currently scattered explanation, not duplicate
internal governance records wholesale. Internal records remain the normative
history and contract layer; public docs should translate that material into a
clear researcher-facing narrative.