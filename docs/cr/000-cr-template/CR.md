# Change Request: <Title>

CR-ID: CR-XXX
Status: Draft | Approved | In Progress | Done
Priority: Low | Medium | High
Created: YYYY-MM-DD
Updated: YYYY-MM-DD

---

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