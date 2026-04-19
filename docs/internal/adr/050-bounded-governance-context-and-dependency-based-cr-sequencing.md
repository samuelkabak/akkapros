---
adr_id: ADR-050
status: Accepted
created: 2026-04-19
updated: 2026-04-19
superseded_by: null
---

# 50. Bounded Governance Context, CR Self-Containment, and Dependency-Based CR Sequencing

## Plain Summary

Governance-aware work in this repository should use the smallest context that is actually needed. Agents and contributors should begin from indexes, summaries, the target record, and directly referenced records instead of reading large portions of `docs/internal/` by default.

CRs should be written as the primary execution prompt for implementation work. An instruction like `implement CR-076` should normally require reading the CR itself, not reconstructing the contract from many separate records.

Later CRs should no longer be blocked just because some unrelated earlier CR is not `Done`. A later CR is blocked only when an earlier non-terminal CR is a real dependency or leaves the same implementation surface unresolved.

TL;DR: use relevance-first, summary-first lookup; make the CR the main implementation prompt; block only on real dependencies, not on unrelated history.

## Context and Problem Statement

The repository's internal governance system has grown large enough that blanket retrieval of ADRs, CRs, and REQs imposes a real cost on LLM-assisted work. The current process and agent instructions already aim for targeted reading in some places, but two practical problems remain:

- governance-aware agents can still drift toward expensive, low-yield historical reading
- the current sequencing rule is broader than necessary and can block work for unrelated reasons, such as an old unresolved CR on a different surface

This produces both cost and confusion. The repository needs an explicit governance policy that preserves context where it matters while avoiding full-history scans and blanket sequencing gates.

The repository also needs a clearer separation between prompt authoring and prompt execution. The CR should carry enough contract detail that an implementing agent can execute from the CR itself, with ADRs and REQs serving as supporting context rather than mandatory bulk prerequisites.

## Decision Drivers

- Lower LLM token cost
- Faster agent triage
- Decouple CR authoring from CR execution
- Make CRs usable as direct implementation prompts
- Preserve useful governance context
- Reduce false blockers from unrelated historical CRs
- Keep governance auditable and incremental

## Considered Options

- Option A — Keep the current broad sequencing rule and let agents decide ad hoc how much governance history to read.
- Option B — Adopt a bounded, summary-first lookup policy, require CR self-containment for implementation, and block later CRs only on directly relevant unresolved dependencies. (Chosen)
- Option C — Remove governance lookups almost entirely from agent workflows.

## Decision Outcome

Choose Option B.

Governance-aware workflows must be relevance-first and summary-first. The default read set is the target record, its directly referenced records, and only a small number of additional recent directly relevant records when a concrete ambiguity or dependency requires them.

When governance or implementation context is sent to an LLM, the sender should provide the smallest sufficient slice first and request additional targeted slices only if the model identifies a concrete unresolved need.

CRs must be authored to function as the primary execution prompt. A well-formed CR should contain the requested outcome, boundaries, acceptance criteria, likely touched surfaces, and verification path in one place so an implementing agent can start from the CR alone in the common case.

CR sequencing is now dependency-based rather than globally identifier-based. A later CR is blocked only when an earlier non-terminal CR is a direct prerequisite, is explicitly referenced as governing or prerequisite, or leaves the same active implementation surface in an unresolved ambiguous state.

## Pros and Cons of the Options

### Chosen Option

- Pros:
  - reduces prompt size and cost without discarding governance
  - makes implementation requests like `implement CR-NNN` practical without large prompt assembly
  - makes agent behavior easier to justify and audit
  - removes false blockers from unrelated unfinished CRs
  - preserves the incremental precedence model
- Cons:
  - requires judgment about what counts as directly relevant
  - requires CR authors to be more disciplined about completeness
  - requires agent prompt updates and clearer README language

### Other Options

- Option A:
  - Pro: no immediate process change
  - Con: keeps both token waste and confusing blockers
- Option C:
  - Pro: cheapest prompt footprint
  - Con: loses too much governance context and invites incorrect implementations

## Implications and Consequences

- `docs/internal/README.md` must describe bounded lookup and dependency-based CR blocking as the active governance workflow.
- `docs/internal/README.md` must also define minimal-disclosure and CR self-containment as the active contract.
- Repository-specific agent instructions should be updated to use index-first and summary-first triage rather than broad historical reading.
- The CR implementing agent should stop enforcing a blanket rule that every earlier CR must be `Done`.
- Spec-writing guidance should keep the lookback rule, but make it explicitly bounded and relevance-first.
- CR authors should assume the CR itself is the implementation prompt and include enough executable contract detail accordingly.

## Links

- [docs/internal/README.md](../README.md)
- [ADR-048](048-governance-housekeeping-tooling-must-match-documented-contract.md)
- [CR-071](../cr/071-governance-housekeeping-and-structuring.md)
- [CR-076](../cr/076-optimize-governance-context-loading-and-agent-cr-responsibilities.md)

## Implementation Notes (optional)

- The first implementation step is prompt and responsibility changes in `.github/agents/`.
- Index pages should be the default navigation entrypoint for governance-aware agents.

## Reviewed By

- Repository maintainer request captured on 2026-04-19.
