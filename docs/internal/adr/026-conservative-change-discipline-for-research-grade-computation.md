---
Status: Accepted
Date: 2026-03-26
---

# 026. Conservative Change Discipline for Research-Grade Computation

## Plain Summary

Development in this project must stay conservative, sharply scoped, and explicit about what is known versus what is inferred. When a requested metric cannot be computed from preserved data, the implementation must not invent a workaround that changes existing indicators or introduces unapproved logic.

TL;DR: if the data is not there, preserve behavior, ask, or carry the missing fact explicitly.

## Context and Problem Statement

The Akkadian prosody pipeline combines several sensitive stages whose outputs feed downstream research metrics. Small changes in counting, segmentation, or merge interpretation can cascade into different target numbers and degrade trust in the results. A recent change attempt tried to solve missing provenance by inferring new behavior from incomplete output data and, in doing so, altered established indicators.

## Decision Drivers

- Research-grade result stability
- Conservative engineering in a sensitive pipeline
- Explicit provenance over reconstruction
- Minimize side effects across stages
- Clear approval boundaries for new logic

## Considered Options

- Option A — Infer missing facts from downstream text. Rejected because it can silently change established metrics and relies on assumptions not preserved in the data.
- Option B — Keep existing behavior and add explicit metadata sidecars when needed. Chosen because it preserves established outputs and carries missing provenance honestly.
- Option C — Block all new derived metrics unless the pivot format itself changes. Not chosen because a sidecar can often solve the provenance problem without changing visible pivot text.

## Decision Outcome

Choose Option B. New development must preserve existing logic unless a change is explicitly approved and clearly delimited. When downstream computation lacks provenance, the missing fact must be preserved explicitly upstream, for example in a sidecar, rather than reconstructed by new inference rules.

## Pros and Cons of the Options

### Chosen Option

- Pros: preserves existing metrics and contracts
- Pros: makes provenance explicit and auditable
- Pros: reduces accidental side effects in complex algorithms
- Cons: may require extra metadata files or explicit plumbing between stages

### Other Options

- Option A:
  - Pro: quick to implement
  - Con: high risk of hidden semantic change
  - Con: unsuitable for research-grade outputs
- Option C:
  - Pro: maximally strict
  - Con: may block useful additions that can be implemented safely with explicit metadata

## Implications and Consequences

- Existing indicators must not be redefined to satisfy a new request unless that semantic change is explicitly approved.
- If a feature depends on information not preserved in `_tilde.txt`, the preferred remedy is to add upstream metadata rather than infer it in metrics.
- CRs and REQs must document uncertainty and limitations precisely.
- When a technical obstacle prevents a faithful implementation, the user must be informed before introducing new logic.

## Links

- [docs/internal/adr/022-output-format-public-contract-boundaries.md](022-output-format-public-contract-boundaries.md)
- [docs/internal/adr/020-deterministic-merge-traversal.md](020-deterministic-merge-traversal.md)
- [docs/internal/req/012-structured-metrics-report-output.md](../req/012-structured-metrics-report-output.md)
- [docs/internal/cr/016-add-lexical-word-role-counts-to-metrics-output.md](../cr/016-add-lexical-word-role-counts-to-metrics-output.md)

## Implementation Notes (optional)

- Prefer sidecars or explicit command metadata over hidden reconstruction.
- Use the smallest effective change set.
- If a proposed solution would alter established metrics semantics, stop and get approval first.

## Reviewed By

- Project maintainer guidance captured through repository instructions and change discussion