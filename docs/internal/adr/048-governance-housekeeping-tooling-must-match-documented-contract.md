---
adr_id: ADR-048
status: Proposed
created: 2026-04-18
updated: 2026-04-18
superseded_by: null
---

# 48. Governance Housekeeping Tooling Must Match Documented Contract

## Plain Summary

The repository's internal governance folder is now a working engineering
system, not just a loose collection of notes. The documented rules for
numbering, indexing, and CR commit handling must therefore be implemented by
the helper scripts that maintain those records.

TL;DR: if `docs/internal/README.md` says a governance rule exists, the indexer
and commit helper must support it instead of silently narrowing it.

## Context and Problem Statement

`docs/internal/README.md` already defines the authoritative structure and
numbering rules for ADRs, CRs, REQs, and reviews. The current repository also
ships helper scripts such as `scripts/update-indexes.py` and
`scripts/git-commit-cr.py` that maintain the governance folder.

Those tools are now part of the effective governance surface. When their
behavior diverges from the documented contract, the repository ends up with a
mixed state: the docs promise one rule, while the helper scripts enforce a
smaller or different one. This is especially visible in identifier handling and
generated index completeness.

## Decision Drivers

- Governance reliability
- Low-ambiguity tooling behavior
- Maintainability of internal records
- Explicit rather than silent failure when governance files are unsupported

## Considered Options

- Option A — Keep the README as aspirational guidance and let helper scripts
  implement only a narrower subset when convenient.
- Option B — Treat the documented governance contract as authoritative and
  require helper scripts to match it or fail explicitly. (Chosen)
- Option C — Reduce the documented governance contract to whatever the current
  scripts already support.

## Decision Outcome

We choose Option B.

The internal governance README remains the authoritative human-readable record
for governance layout, numbering, and housekeeping expectations. Repository
scripts that generate indexes or help maintain governance records must either
support the documented contract or fail explicitly when an unsupported case is
encountered. Silent omission is not acceptable for governance artifacts.

## Pros and Cons of the Options

### Chosen Option

- Pros:
  - keeps governance records auditable and trustworthy
  - prevents documented-but-unenforced numbering rules
  - reduces silent omission of internal records from indexes
- Cons:
  - requires maintenance of tooling when governance rules evolve
  - may surface more warnings or failures during transition periods

### Other Options

- Option A:
  - Pro: less immediate tooling work
  - Con: makes the governance folder unreliable as an engineering contract
- Option C:
  - Pro: reduces implementation pressure on scripts
  - Con: weakens the repository's documented governance process

## Implications and Consequences

- `CR-071` must define the concrete housekeeping/tooling changes needed to align
  scripts with the documented contract.
- Governance scripts should surface malformed or unsupported files explicitly
  instead of skipping them silently.
- Future governance-rule changes should update both the docs and the supporting
  scripts in the same change set.

## Links

- [docs/internal/README.md](../README.md)
- [CR-071](../cr/071-governance-housekeeping-and-structuring.md)
- [REQ-037](../req/037-governance-housekeeping-and-tooling-alignment.md)

## Implementation Notes (optional)

- The main initial scope is numbering, discovery, index generation, and CR
  commit-helper behavior.

## Reviewed By

- Internal governance review pending implementation.
