#---
Status: Accepted
Date: 2026-03-10
---

# 4. Stage Pipeline and Pivot Format

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

## Links

- Related: `docs/akkapros/fullprosmaker.md`
- Related: `docs/akkapros/prosody-realization-algorithm.md`
