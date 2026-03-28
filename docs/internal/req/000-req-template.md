---
req_id: REQ-XXX
status: '{Draft | Approved | Rejected | Implemented}'
priority: '{Low | Medium | High}'
impact: '{Additive | Mutative}'
created: YYYY-MM-DD
updated: YYYY-MM-DD
related_adrs: 'ADR-xxx references if applicable'
implemented_by: 'CR-xxx references if applicable'
---

# Requirement: <Title>

# Summary

Short description of the requirement.

Explain the problem and the goal in 2–5 sentences.

Example:
The system shall allow authenticated users to reset their password via email verification.

---

# Motivation

Why is this requirement needed?

Describe the problem being solved.

Example:
Users frequently forget passwords; self-service reset reduces support tickets and improves user experience. This is a standard security feature expected by users.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given [context], when [action], then [expected result]
- [ ] Edge case: handles [specific scenario]
- [ ] Performance: completes within [X] seconds
- [ ] Error handling: displays [message] when [failure]

---

# User Story (optional)
> As a [user role], I want to [action] so that [benefit].

---

# Interface Notes
- Input: `[format/example]`
- Output: `[format/example]`
- Affected components: `[list]`

---

# Open Questions
- [ ] Question 1?
- [ ] Question 2?

---

# Implementation Notes (optional)
- Owner: @github-username or team
- Estimated effort: [small|medium|large]
- Migration: steps required to migrate or update downstream consumers (if applicable)

# Related
- Related ADRs: [ADR-xxx](../adr/ADR-xxx.md)
- Implementation CRs: [CR-xxx](../cr/xxx-change.md)

# Non-Goals
- What this requirement does NOT address (clarify scope)

# Security / Safety Considerations
- Any notes about security, data leakage, or safety relevant to this requirement

