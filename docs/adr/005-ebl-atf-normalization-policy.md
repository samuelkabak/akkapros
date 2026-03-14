# 5. eBL ATF Normalization Policy

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

## Links

- Related: `docs/akkapros/atfparser.md`
- Related: `src/akkapros/lib/atfparse.py`
