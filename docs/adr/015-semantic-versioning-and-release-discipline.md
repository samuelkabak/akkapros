#---
Status: Accepted
Date: 2026-03-14
---

# 15. Semantic Versioning and Release Discipline

## Context and Problem Statement

The project exposes CLI contracts and output formats that users rely on in scripted workflows. Unclear versioning would break reproducibility.

## Decision Drivers

- Predictable compatibility expectations
- Clear release communication
- Research reproducibility

## Considered Options

- Ad hoc version bumps without explicit rules
- Keep-a-Changelog + Semantic Versioning + release checklist

## Decision Outcome

Chosen option: Follow Semantic Versioning, maintain `CHANGELOG.md`, and use release strategy/checklist documentation.

## Pros and Cons of the Options

### SemVer + changelog discipline

- Good, because users can reason about upgrade risk
- Good, because release behavior is documented and auditable
- Bad, because release management is more process-heavy

### Ad hoc release style

- Good, because lower short-term overhead
- Bad, because compatibility expectations are unclear

## Links

- Related: `CHANGELOG.md`
- Related: `docs/akkapros/release-strategy.md`
