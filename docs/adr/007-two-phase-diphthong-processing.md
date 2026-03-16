#---
Status: Accepted
Date: 2026-03-12
---

# 7. Two-Phase Diphthong Processing

## Context and Problem Statement

Prosody operations require unambiguous syllable boundaries, while final outputs should retain linguistically familiar diphthong forms.

## Decision Drivers

- Unambiguous internal syllabification
- Preserve user-facing linguistic readability
- Keep mora accounting consistent

## Considered Options

- Keep diphthongs untouched throughout pipeline
- Expand diphthongs for processing and restore later

## Decision Outcome

Chosen option: Use a two-phase approach: split during syllabification, restore after prosody realization where requested.

## Pros and Cons of the Options

### Two-phase split/restore

- Good, because internal processing is less ambiguous
- Good, because surface form can remain familiar
- Bad, because restoration logic adds complexity

### Keep diphthongs untouched

- Good, because fewer transformation steps
- Bad, because syllable boundary detection is less robust
- Bad, because downstream logic must handle more ambiguity

## Links

- Related: `docs/akkapros/diphthong-processing.md`
- Related: `docs/akkapros/prosmaker.md`
