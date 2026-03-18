---
Status: Accepted
Date: 2026-03-10
---

# 4. Stage Pipeline and Pivot Format

## Plain Summary

Use a clear processing pipeline where each stage reads the previous stage's output.
Keep a pivot format (`*_tilde.txt`) between stages so tools stay simple and testable.

## Context and Problem Statement

The toolkit performs multiple transformations from ATF input to analysis and display outputs. Without a stable intermediate contract, stage coupling becomes fragile.

## Decision Drivers

- Deterministic stage interfaces
- Easy debugging of intermediate states
- Composable CLI pipeline

## Considered Options

- One monolithic processor with hidden internals
- Multi-stage pipeline with explicit intermediate files and pivot format

## Decision Outcome

Chosen option: Use explicit stage-by-stage files with `*_tilde.txt` as a central pivot for downstream metrics and rendering.

## Pros and Cons of the Options

### Explicit staged pipeline

- Good, because each stage can be tested and reasoned about independently
- Good, because failures are localized to stage boundaries
- Bad, because it creates more intermediate files

### Monolithic processor

- Good, because fewer user-visible files
- Bad, because harder to debug and validate stage logic
- Bad, because feature additions affect a larger blast radius

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/fullprosmaker.md`
- Related: `docs/akkapros/prosody-realization-algorithm.md`

## Reviewed By

- Akkapros maintainers

