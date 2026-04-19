---
cr_id: CR-076
status: Done
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
implements: 'ADR-050'
---

# Change Request: Optimize Governance Context Loading and Make the CR the Primary Execution Prompt

# Summary

Update the repository's governance-aware agent responsibilities and related governance process text so they use bounded, relevance-first context loading instead of broad historical reading.

This CR also makes the CR the primary execution prompt for implementation work. An implementing agent should normally be able to act on `implement CR-076` by reading the CR itself plus only any narrowly scoped references that the CR explicitly marks as required.

This CR replaces the current blanket sequencing rule with a dependency-based rule so later CRs are blocked only by directly relevant unresolved earlier CRs, not by unrelated historical records.

---

# Motivation

- Lower LLM token cost
- Faster governance-aware triage
- Decouple prompt authoring from prompt execution
- Reduce the amount of context that must be assembled before asking an agent to act
- Fewer false blockers
- Better signal-to-noise in prompt context

The current internal governance system is large enough that reading broad portions of `docs/internal/` by default is expensive and often unnecessary. In practice, the target CR, its direct references, index summaries, and a small number of recent directly relevant records are usually sufficient.

The current workflow also leaves too much implementation context outside the CR itself. That forces the prompt author or implementing agent to assemble scattered background before execution, which makes runs slower and costlier.

The current blanket rule that all earlier CRs must be `Done` is also too coarse. It can block unrelated work and create confusion when the unresolved earlier CR is historical noise rather than an actual dependency.

---

# Scope

## Included

- Update governance process text to make bounded context loading the default rule.
- Update governance process text to make minimal-disclosure and ask-for-more escalation the default rule.
- Update CR authoring expectations so the CR itself carries the implementation-ready contract.
- Update repository-specific custom agent instructions to use index-first, summary-first governance triage.
- Replace blanket CR sequencing checks in agent instructions with dependency-based blocking rules.
- Clarify when a governance-aware agent may read more than the default bounded set.
- Align spec-writer and CR-implementing agent responsibilities with the new bounded governance contract.

## Not Included

- Removing the governance system.
- Eliminating ADR/CR/REQ reading entirely.
- Changing the repository's numbering or indexing scheme.
- Changing production runtime behavior.

---

# Current Behavior

Current repository state shows a mixed policy:

- `docs/internal/README.md` already emphasizes direct relevance in some places, but it does not yet define a concrete bounded lookup budget.
- `.github/agents/internal-spec-writer.agent.md` already limits reading more than the CR implementing agent does, but still leaves the broader governance workflow implicit.
- `.github/agents/cr-implementing-agent.agent.md` currently contains a blanket sequencing rule that says a later CR is not implementable unless all earlier CRs are already `Done`.

Current authoring consequence:

- the CR is not yet treated as the main execution prompt
- the person invoking the agent may still have to assemble too much surrounding context

Current consequence:

- governance-aware agent runs can become more expensive than necessary
- agent behavior is inconsistent across the two custom agents
- unrelated old CRs can become false blockers

---

# Proposed Change

Adopt a bounded governance-context contract for repository-aware agents and contributors, and require CRs to be implementation-ready as standalone execution prompts.

## 1. Index-first and summary-first lookup

Default governance lookup should proceed in this order:

1. relevant `docs/internal/*/index.md` page
2. target ADR, CR, REQ, or review
3. records directly referenced by that target
4. only if still needed, up to 3 to 5 additional recent directly relevant CRs and only the directly relevant ADRs or REQs needed to resolve a named ambiguity or dependency

Agents must not scan governance history from the earliest records forward by default.

## 2. Bounded full-text reading budget

The default full-text read set should be bounded to:

- the target record
- directly referenced records
- at most 3 to 5 additional recent directly relevant CRs when necessary
- only the directly relevant ADRs and REQs required to resolve a concrete ambiguity, dependency, or conflict

If an agent exceeds that budget, it should be because it can name the ambiguity, dependency, or conflict that required more reading.

## 3. Minimal-disclosure and ask-for-more execution

When a governance-aware prompt or implementation request is sent to an LLM, the sender should provide the smallest sufficient slice first.

If the slice is insufficient, the next step is to request one additional targeted slice tied to a named ambiguity, dependency, file surface, or contract gap. Broad bulk context loading should be treated as the exception, not the default.

## 4. CR as the primary execution prompt

The CR should contain enough contract detail that an implementing agent can usually execute from the CR itself after receiving an instruction such as `implement CR-076`.

That means the CR should normally contain:

- the requested change in executable terms
- the scope boundaries and exclusions
- the acceptance criteria
- the likely implementation surfaces
- the verification path
- any truly required ADR or REQ references called out explicitly rather than implied broadly

ADRs and REQs remain valid supporting context, but they should not be bulk-loaded by default when the CR can carry the necessary implementation contract directly.

## 5. Dependency-based CR sequencing

The blanket rule that every earlier CR must already be `Done` must be removed from governance-aware agent instructions.

A later CR is blocked only when an earlier non-terminal CR:

- is explicitly referenced as a prerequisite or governing dependency
- controls the same active implementation surface in a way that leaves the contract unresolved or ambiguous
- is required by an accepted ADR or REQ that the target CR directly implements

Unrelated earlier CRs do not block later work solely because they have lower identifiers.

## 6. Consistent agent responsibilities

The custom agents under `.github/agents/` should use the same bounded governance contract:

- the spec writer stays documentation-only
- the implementing agent stays implementation-oriented
- both agents use the same summary-first and dependency-based lookup policy

- both agents use the same minimal-disclosure and ask-for-more policy

## 7. Escalation rule for ambiguous cases

If an agent cannot determine whether an older unresolved CR is directly relevant, it may inspect targeted additional records. It should not escalate straight to broad history scans.

---

# Technical Design

Architecture notes:

Components:
- `docs/internal/README.md`
- `.github/agents/cr-implementing-agent.agent.md`
- `.github/agents/internal-spec-writer.agent.md`
- any repository-level prompt text that duplicates the old blanket sequencing rule
- `docs/internal/cr/000-cr-template.md`

Implementation direction:

- codify the bounded lookup policy in `docs/internal/README.md`
- codify minimal-disclosure and CR self-containment rules in `docs/internal/README.md`
- update the two custom agent prompt files to use the same policy
- remove the blanket all-earlier-CRs-`Done` rule from the CR implementing agent
- replace it with explicit dependency-based blocking guidance
- update the CR template so new CRs are authored as implementation-ready prompts

Design constraints:

- retain governance awareness
- reduce prompt size and unnecessary document reads
- keep implementation requests executable from the CR itself in the common case
- keep older records as history without requiring blanket rereads

---

# Files Likely Affected

`docs/internal/README.md`
`.github/agents/cr-implementing-agent.agent.md`
`.github/agents/internal-spec-writer.agent.md`
`.github/copilot-instructions.md`
`docs/internal/cr/000-cr-template.md`

---

# Acceptance Criteria

- [x] `docs/internal/README.md` defines bounded governance lookup as the default workflow.
- [x] The README defines index-first and summary-first triage before broad document reading.
- [x] The README defines minimal-disclosure first and ask-for-more escalation instead of bulk context loading.
- [x] The README defines the CR as the primary implementation prompt in the common case.
- [x] The README replaces blanket CR sequencing with dependency-based CR blocking.
- [x] `.github/agents/cr-implementing-agent.agent.md` no longer instructs the agent to block on any earlier CR that is not `Done`.
- [x] `.github/agents/cr-implementing-agent.agent.md` instructs the agent to block only on directly relevant unresolved earlier CRs.
- [x] `.github/agents/internal-spec-writer.agent.md` explicitly follows the same bounded lookup policy.
- [x] New or updated CR authoring guidance requires sufficient self-contained implementation detail in the CR itself.
- [x] The two custom agents no longer instruct broad default reading of ADR/CR/REQ history.
- [x] The updated instructions still preserve governance awareness and precedence handling.

---

# Risks / Edge Cases

Possible issues:

- direct relevance can still require judgment in messy historical areas
- some ambiguous cases will still need targeted extra reading
- some legacy CRs will remain under-specified and may still require follow-up rewrites before they can serve as standalone prompts
- if the prompt text becomes too compressed, agents may lose useful governance context
- repository-level instructions outside `.github/agents/` may still contain broader rules and may need alignment

---

# Testing Strategy

Manual verification:

- inspect both custom agent prompt files and confirm they start with index-first and target-first lookup
- inspect the CR template and confirm it prompts authors to include implementation-ready detail in the CR itself
- confirm the implementing agent no longer applies a blanket all-earlier-CRs-`Done` rule
- confirm the spec writer still stays within `docs/internal/` but no longer implies broad default historical reading

Prompt-behavior checks:

- ask a governance-aware agent to implement a well-formed CR and confirm it does not request broad supporting history by default
- confirm that when the first slice is insufficient, the next request is for one targeted additional slice rather than a bulk dump

Behavior checks:

- ask each custom agent to handle a CR with unrelated older unfinished records and confirm it does not block by default
- ask each custom agent to handle a CR with an explicitly referenced unresolved prerequisite and confirm it does block

---

# Rollback Plan

If the bounded policy proves too narrow in practice, expand the lookup budget slightly while keeping the same relevance-first structure. Do not revert to blanket full-history reading or blanket sequencing blocks unless a later record explicitly approves that reversal.

---

# Related Issues

- [ADR-050](../adr/050-bounded-governance-context-and-dependency-based-cr-sequencing.md)
- [ADR-048](../adr/048-governance-housekeeping-tooling-must-match-documented-contract.md)
- [CR-071](071-governance-housekeeping-and-structuring.md)

---

# Tasks

## Implementation

- [x] Update the governance README language.
- [x] Update the CR template guidance.
- [x] Update the CR implementing agent prompt.
- [x] Update the internal spec writer prompt.
- [x] Check for broader duplicate sequencing rules in repository-level prompt text.

## Tests

- [x] Verify the new prompt instructions are internally consistent.
- [x] Verify the agents still preserve precedence and direct-reference reading.

## Documentation

- [x] Refresh internal indexes after adding this record.
- [x] Note any remaining repository-level prompt surfaces that still need manual alignment.

## Review

- [x] Confirm that the new policy lowers default governance context without removing needed governance awareness.

---

# Implementation Blockers

Leave empty.

---

# Notes

This CR is intentionally focused on governance-aware prompt behavior and governance-process text. It does not remove the governance system; it narrows how much of that system should be loaded by default.

It also changes the authoring expectation for CRs: the CR should normally be sufficient for the instruction `implement CR-NNN` to be actionable without bulk assembly of surrounding governance history.

Implementation completed on 2026-04-19 by updating the governance README, ADR-050, the CR template, and the two repository custom agent prompt files. A targeted grep verification confirmed that the blanket all-earlier-CRs-`Done` rule was removed from the custom agents and replaced by dependency-based, minimal-disclosure guidance.
