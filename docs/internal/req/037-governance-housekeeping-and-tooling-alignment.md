---
req_id: REQ-037
status: Implemented
priority: Medium
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
related_adrs: 'ADR-048'
implemented_by: 'CR-071'
---

# Requirement: Governance Housekeeping and Tooling Alignment

## Summary

The internal governance folder and its housekeeping tools shall implement the
same documented contract for structure, numbering, indexing, and CR commit
handling.

This requirement turns the governance helper scripts into explicit contract
participants rather than best-effort utilities.

---

## Motivation

If the README, indexer, and CR commit helper disagree about valid identifiers or
record discovery, the governance folder cannot be trusted as a source of truth.

---

## Acceptance Criteria

- [ ] Given the documented governance numbering policy includes identifiers
      beyond `999`, when governance tooling processes records, then valid files
      under that policy are discovered and handled consistently.
- [ ] Given a governance file is malformed or unsupported, when the housekeeping
      scripts encounter it, then they surface the problem explicitly rather than
      silently omitting it.
- [ ] Given a valid CR identifier is supplied to the commit helper, when the
      helper resolves the CR, then it builds the canonical commit subject from
      the CR title.
- [ ] Given governance records are added, renamed, or removed, when the indexer
      runs, then the generated indexes remain complete under the active policy.

---

## User Story (optional)

> As a maintainer, I want governance tooling to match the documented rules so
> that internal records stay trustworthy and auditable.

---

## Interface Notes

- Input: governance files under `docs/internal/` and CR identifiers supplied to
  helper scripts
- Output: complete indexes and canonical commit messages
- Affected components: `docs/internal/README.md`, `scripts/update-indexes.py`,
  `scripts/git-commit-cr.py`

---

## Open Questions

- [ ] None at draft time.

---

## Implementation Notes (optional)

- Migration: update existing script tests that currently pin narrower identifier
  rules.

## Related

- Related ADRs: [ADR-048](../adr/048-governance-housekeeping-tooling-must-match-documented-contract.md)
- Implementation CRs: [CR-071](../cr/071-governance-housekeeping-and-structuring.md)

## Non-Goals

- Reorganizing the internal governance folder into a different set of top-level
  document types

## Security / Safety Considerations

- Silent omission of governance files is a process-integrity risk and must be
  treated as a tooling failure mode.
