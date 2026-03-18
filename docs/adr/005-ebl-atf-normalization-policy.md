---
Status: Accepted
Date: 2026-03-10
---

# 5. eBL ATF Normalization Policy

## Plain Summary

Clean ATF input to keep only the text needed for phonetic processing.
Remove editorial markup but keep line breaks and morpheme markers that matter.

## Context and Problem Statement

Raw ATF includes editorial and structural markup not suitable for phonological processing. The parser must preserve pronunciation-relevant content and remove noise.

## Decision Drivers

- Reliable phonetic preprocessing
- Reproducible cleanup rules
- Compatibility with eBL line conventions

## Considered Options

- Keep most markup and parse later
- Normalize early in `atfparser` with explicit rule set

## Decision Outcome

Chosen option: Normalize ATF at parser stage with explicit transformations (retain linguistic content, drop non-phonetic markup, preserve phrase structure signals).

## Pros and Cons of the Options

### Early explicit normalization

- Good, because downstream tools receive stable clean text
- Good, because parser behavior is transparent and testable
- Bad, because parser must track markup edge cases

### Defer normalization downstream

- Good, because parser is simpler
- Bad, because every downstream stage repeats cleanup assumptions
- Bad, because inconsistencies are more likely

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/atfparser.md`
- Related: `src/akkapros/lib/atfparse.py`

## Reviewed By

- Akkapros maintainers
