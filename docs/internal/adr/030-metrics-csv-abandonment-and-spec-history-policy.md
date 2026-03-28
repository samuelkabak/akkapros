---
Status: Accepted
Date: 2026-03-28
---

# 030. Metrics CSV Abandonment and Spec History Policy

## Plain Summary

The project accepts removal of metrics CSV as a deliberate contract change and
records that decision in a new ADR rather than by retroactively rewriting older
accepted ADRs and requirements as though CSV had never been part of the public
surface. Earlier documents remain historical records of what was true when they
were written, while REQ-014 and CR-021 define the abandonment and migration
path.

TL;DR: legalize CSV removal with a new ADR, preserve prior records, and use
supersession or cross-references instead of rewriting history.

## Context and Problem Statement

Metrics CSV was previously part of the documented output contract. REQ-014 and
CR-021 introduced a controlled abandonment path in which JSON becomes the only
supported machine-readable metrics export. During implementation, multiple
earlier ADR and REQ documents were edited to remove or rewrite their prior CSV
statements.

That approach creates a change-management problem. In this repository, ADRs and
requirements are decision records as much as they are current guidance. If an
older accepted document is rewritten to match a newer decision, the repository
loses the ability to answer two important questions clearly:

- what used to be part of the contract,
- and when that changed.

REQ-014 therefore needs an explicit legalizing ADR that records the new
decision while preserving the older documents as historical context.

## Decision Drivers

- Preserve auditable decision history
- Avoid retroactive distortion of earlier accepted contracts
- Keep the CSV abandonment decision explicit and easy to trace
- Maintain clean links between ADR, REQ, and CR documents
- Reduce ambiguity for future reviewers about whether older CSV references were
  mistakes or formerly accepted behavior

## Considered Options

- Option A — Rewrite older ADRs and REQs so they no longer mention metrics CSV.
  Rejected because it erases historical contract state and makes it harder to
  audit why REQ-014 exists.
- Option B — Add a new ADR that legalizes REQ-014 and states that older
  documents remain historical unless explicitly superseded. Chosen because it
  preserves the record while giving the CSV abandonment an authoritative basis.
- Option C — Treat REQ-014 alone as sufficient and add no ADR. Not chosen
  because removal of a documented public output format is architectural and
  contract-significant enough to merit an ADR-level decision.

## Decision Outcome

Choose Option B.

The project accepts metrics CSV abandonment through this ADR, with REQ-014 as
the requirement-level contract and CR-021 as the implementation change record.
Older accepted ADRs and REQs that mention metrics CSV are not to be rewritten
as though CSV had never existed. They remain valid historical records unless
they are explicitly marked as superseded, narrowed by later ADRs, or annotated
with forward references.

For this topic specifically:

- ADR-030 legalizes the architectural decision to abandon metrics CSV.
- REQ-014 defines the behavioral requirement and migration expectations.
- CR-021 records implementation and rollout details.
- Earlier documents that mention metrics CSV remain historical context and may
  be annotated, but should not be silently rewritten to remove their original
  meaning.

## Pros and Cons of the Options

### Chosen Option

- Pros: preserves an auditable chronology of the contract change
- Pros: makes REQ-014 clearly grounded in an ADR-level decision
- Pros: avoids confusing future reviewers about whether CSV was ever supported
- Pros: aligns with conservative change discipline for research-grade outputs
- Cons: leaves some older documents mentioning CSV and therefore requires
  careful cross-linking or supersession notes

### Other Options

- Option A:
  - Pro: produces a cleaner-looking present-state document set
  - Con: rewrites history and weakens change-management traceability
  - Con: makes older CRs and requirements harder to interpret correctly
- Option C:
  - Pro: minimal documentation work
  - Con: under-documents a contract-breaking architectural decision
  - Con: leaves ambiguity about whether CSV removal was fully approved

## Implications and Consequences

- Future removals of documented public outputs should be legalized by a new ADR
  or an explicit superseding ADR, not by retroactively rewriting older accepted
  records.
- Older ADRs and REQs may receive short notes such as "later narrowed by
  ADR-030" or similar cross-references, but their original contract statements
  should remain intact unless the document is formally superseded.
- REQ-014 should cite ADR-030 as the legalizing decision.
- CR-021 should cite ADR-030 as the architectural authority for the removal.
- Reviewers should interpret older CSV references as formerly accepted behavior,
  not as current contract.

## Links

- [docs/internal/req/014-remove-metrics-csv-output.md](../req/014-remove-metrics-csv-output.md)
- [docs/internal/cr/021-remove-metrics-csv-output.md](../cr/021-remove-metrics-csv-output.md)
- [docs/internal/adr/022-output-format-public-contract-boundaries.md](022-output-format-public-contract-boundaries.md)
- [docs/internal/adr/026-conservative-change-discipline-for-research-grade-computation.md](026-conservative-change-discipline-for-research-grade-computation.md)
- [docs/internal/req/004-metrics-computation.md](../req/004-metrics-computation.md)
- [docs/internal/req/012-metrics-output-structure-and-layout.md](../req/012-metrics-output-structure-and-layout.md)

## Implementation Notes (optional)

- Prefer additive documentation changes for contract abandonment decisions:
  new ADR, updated REQ, updated CR, and light cross-references.
- Avoid editing older accepted ADRs or REQs to change past-tense truth claims
  unless the document is explicitly marked `Deprecated` or `Superseded`.
- If older documents need reader guidance, add a short note pointing forward to
  ADR-030 instead of rewriting their original contract statements.

## Reviewed By

- Repository maintainer direction captured through REQ-014 clarification and
  follow-up change-management review