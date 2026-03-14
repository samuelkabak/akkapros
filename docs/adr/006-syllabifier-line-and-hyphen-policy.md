# 6. Syllabifier Line and Hyphen Policy

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

## Links

- Related: `docs/akkapros/syllabifier.md`
- Related: `src/akkapros/lib/syllabify.py`
