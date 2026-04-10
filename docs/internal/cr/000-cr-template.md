---
cr_id: CR-XXX
status: '{Draft | Blocked | Approved | Rejected | Done}'
priority: '{Low | Medium | High}'
impact: '{Additive | Mutative}'
created: YYYY-MM-DD
updated: YYYY-MM-DD
implements: 'ADR-NNN, REQ-NNN ... (only references)'
---

# Change Request: <Title>

# Summary

Short description of the requested change.

Explain the problem and the goal in 2–5 sentences.

Example:
Add rate limiting to the login endpoint to prevent brute force attacks.

---

# Motivation

Why is this change needed?

Examples:
- Bug fix
- Feature request
- Performance improvement
- Refactoring
- Security improvement

Describe the problem being solved.

---

# Scope

## Included

- item
- item
- item

## Not Included

- item
- item

---

# Current Behavior

Describe how the system currently works.

Example:

/login endpoint accepts unlimited requests  
No throttling or IP protection exists

---

# Proposed Change

Describe the desired behavior.

Example:

- Limit login attempts per IP
- Reset counter after X minutes
- Return HTTP 429 when exceeded

---

# Technical Design

Explain how it should be implemented.

Architecture notes:

Components:
- component name

Storage:
- database / redis / memory

API changes:
- endpoint updates

Example:

Middleware: RateLimitMiddleware

Storage:
Redis counter per IP

Key format:
login_attempts:{ip}

TTL:
10 minutes

---

# Files Likely Affected

src/auth/login.ts  
src/middleware/rateLimiter.ts  
config/security.ts  
tests/auth/login.test.ts  

---

# Acceptance Criteria

- [ ] Login endpoint limits requests to X/min
- [ ] HTTP 429 returned when limit exceeded
- [ ] Counter resets after timeout
- [ ] Tests added
- [ ] Documentation updated

---

# Risks / Edge Cases

Possible issues:

- Shared IPs behind NAT
- Redis outage
- Rate limit bypass

---

# Testing Strategy

Unit tests:

- login rate limit reached
- counter reset

Integration tests:

- repeated login attempts

Manual tests:

- simulate attack

---

# Rollback Plan

Explain how to revert if needed.

Example:

Disable rate limiter via configuration flag.

---

# Related Issues

GitHub issues  
PRs  
other CRs

---

# Tasks

## Implementation

- [ ] Implement core feature
- [ ] Integrate with existing system
- [ ] Add configuration options

## Tests

- [ ] Unit tests
- [ ] Integration tests

## Documentation

- [ ] Update README
- [ ] Update API docs

## Review

- [ ] Code review
- [ ] Verify acceptance criteria


---

# Implementation Blockers

Use this section when implementation or verification cannot proceed safely.

Leave the section empty if no blockers are known.

When a blocker is present, set the front matter status to `Blocked` and add one entry per blocker using this structure:

## YYYY-MM-DD - <Short blocker title>

- Type: `{spec weakness | code/spec mismatch | governance conflict | missing dependency | external dependency | other}`
- Observed: concise description of the concrete problem
- Why blocked: why safe implementation or verification cannot continue
- Needed to unblock: the minimum clarification, decision, dependency, or spec rewrite required
- Owner: `{spec writer | implementer | maintainer | external}`
- Related refs: ADR-NNN, REQ-NNN, CR-NNN, files, tests, or commits as applicable

Example:

## YYYY-MM-DD - Acceptance criteria do not define output shape

- Type: `spec weakness`
- Observed: the CR requires a new metrics artifact but does not define the output schema or filename contract
- Why blocked: implementation would be speculative and acceptance criteria cannot be verified objectively
- Needed to unblock: specify the artifact path, schema, and verification expectations
- Owner: `spec writer`
- Related refs: CR-XXX, REQ-XXX


---

# Notes

This section contains optional design notes related to the Change Request.

Possible contents:

- design discussions
- architecture sketches
- research
- alternative approaches
- links to references
