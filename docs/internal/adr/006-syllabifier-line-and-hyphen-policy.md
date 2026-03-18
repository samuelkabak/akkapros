---
Status: Accepted
Date: 2026-03-06
---

# 6. Syllabifier Line and Hyphen Policy

## Plain Summary

Keep original line breaks and treat hyphens as special markers.
This preserves prosodic information that matters later in the pipeline.

## Context and Problem Statement

Line breaks and hyphens carry prosodic and editorial meaning. Over-normalization can destroy phrasing cues needed by later stages.

## Decision Drivers

- Preserve useful textual structure
- Avoid accidental loss of prosodic information
- Keep behavior explicit via options

## Considered Options

- Normalize all whitespace and punctuation aggressively
- Preserve lines/hyphens by default, expose opt-in merge modes

## Decision Outcome

Chosen option: Keep original lines by default and preserve hyphens unless explicitly merged (`--merge-lines`, `--merge-hyphen`).

## Pros and Cons of the Options

### Preserve-by-default policy

- Good, because line-based phrasing survives
- Good, because users can still request normalization
- Bad, because defaults may look less "clean" for generic text

### Aggressive normalization

- Good, because uniform output shape
- Bad, because meaningful boundaries may be erased
- Bad, because reconstruction becomes harder

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/syllabifier.md`
- Related: `src/akkapros/lib/syllabify.py`

## Reviewed By

- Akkapros maintainers

