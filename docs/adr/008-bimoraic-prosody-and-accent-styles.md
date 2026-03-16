#---
Status: Accepted
Date: 2026-03-14
---

# 8. Bimoraic Prosody and Accent Styles

## Context and Problem Statement

The project models connected-speech rhythm beyond lexical stress eligibility rules. Implementation must remain explicit and reproducible.

## Decision Drivers

- Linguistically motivated rhythm model
- Deterministic algorithmic behavior
- Support for documented accent hierarchies

## Considered Options

- Keep only lexical stress marking with no realization mechanism
- Implement bimoraic prosody realization with selectable accent styles

## Decision Outcome

Chosen option: Implement bimoraic prosody realization with LOB/SOB style selection (and documented hierarchy behavior) in `prosmaker`.

## Pros and Cons of the Options

### Bimoraic realization model

- Good, because it provides explicit connected-speech mechanism
- Good, because outputs are testable and reproducible
- Bad, because algorithmic rules are necessarily complex

### Lexical-only stress marking

- Good, because implementation is simpler
- Bad, because it does not address rhythm realization in running text

## Links

- Related: `docs/akkapros/prosody-realization-algorithm.md`
- Related: `docs/akkapros/prosmaker.md`
