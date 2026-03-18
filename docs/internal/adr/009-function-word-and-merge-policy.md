---
Status: Accepted
Date: 2026-03-14
---

# 9. Function Word and Merge Policy

## Plain Summary

Function words (like prepositions and particles) join nearby content words so they don't get their own stress.
Merging keeps prosody natural and avoids isolated weak words.

## Context and Problem Statement

Certain words and explicit links require prosodic grouping decisions across word boundaries to satisfy realization constraints.

## Decision Drivers

- Handle function-word behavior consistently
- Resolve odd-mora groups without ad hoc exceptions
- Preserve explicit user-marked links

## Considered Options

- Treat all words independently
- Allow controlled forward/backward merge behavior and explicit linker handling

## Decision Outcome

Chosen option: Support merge-forward and merge-backward logic, function-word constraints, and explicit `+` group behavior.

## Pros and Cons of the Options

### Controlled merge policy

- Good, because unresolved units can be repaired systematically
- Good, because explicit user structure can be respected
- Bad, because edge-case behavior needs careful tests

### Fully independent words

- Good, because simpler algorithm
- Bad, because many real contexts remain unresolved or unnatural

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/prosody-realization-algorithm.md`
- Related: `src/akkapros/lib/prosody.py`

## Reviewed By

- Akkapros maintainers

