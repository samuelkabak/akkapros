---
Status: Accepted
Date: 2026-03-17
---

# 20. Deterministic Merge Traversal

## Plain Summary

Make merging rules deterministic so the same input always yields the same merged groups.
Determinism helps testing and reproducible analysis.

## Context and Problem Statement

Prosody realization must handle odd-mora units and function-word attachment in connected speech. A traversal strategy is required to decide merge order and fallback behavior while preserving deterministic outputs.

## Decision Drivers

- Deterministic and reproducible processing
- Linguistic plausibility for online speech flow
- Guaranteed termination and bounded complexity
- Clear semantics for explicit linker chains (`+`)

## Considered Options

- Global optimization with full lookahead/backtracking
- Deterministic left-to-right traversal with constrained backward recovery
- Randomized or heuristic non-deterministic merge selection

## Decision Outcome

Chosen option: Use deterministic left-to-right traversal with forward merge as default, targeted backward merge for stranded function-word edge cases, explicit `+` handling, and last-resort repair only when legal options fail.

## Pros and Cons of the Options

### Deterministic traversal (chosen)

- Good, because results are stable across runs and easy to test
- Good, because implementation mirrors incremental speech production logic
- Good, because termination is guaranteed under one-mora-add operations
- Bad, because global optimum is not explicitly searched

### Global optimization

- Good, because could improve objective fit in some cases
- Bad, because complexity and explainability costs are high

### Non-deterministic heuristics

- Good, because easy to prototype
- Bad, because harms reproducibility and scientific traceability

## Implications and Consequences

- Merge direction and fallback order are compatibility-sensitive behavior and require regression tests.
- Future algorithmic extensions should preserve determinism unless a new ADR supersedes this one.

## Links

- Code: `src/akkapros/lib/prosody.py`
- CLI: `src/akkapros/cli/prosmaker.py`
- Doc: `docs/akkapros/prosody-realization-algorithm.md`
- Research notes: `tmp/research-notes.md` (066-074)

## Reviewed By

- Akkapros maintainers

