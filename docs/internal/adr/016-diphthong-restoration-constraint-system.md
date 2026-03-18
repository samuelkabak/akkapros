---
Status: Accepted
Date: 2026-03-17
---

# 16. Diphthong Restoration Constraint System

## Plain Summary

When we restore diphthongs after prosody work, follow clear rules so mora counts and stress stay correct.
The rules avoid changing meaning while fixing rhythm.

## Context and Problem Statement

The pipeline splits diphthongs for unambiguous syllabification and later restores them for final outputs. Restoration is not a mechanical join: Akkadian phonotactics constrain vowel sequences, especially first-vowel shortening in hiatus contexts.

## Decision Drivers

- Keep syllabification deterministic while preserving linguistic plausibility
- Prevent illegal restored forms in final output
- Preserve tilde/accent information through restoration
- Make restoration logic explicit and testable

## Considered Options

- Simple string merge without phonotactic constraints
- Constraint-aware restoration with ordered rule tables
- Disable restoration and keep split diphthongs in final output

## Decision Outcome

Chosen option: Use a constraint-aware restoration system with generated, ordered regex rules that encode Akkadian-specific behavior (including first-vowel shortening and same-base/different-base handling).

## Pros and Cons of the Options

### Constraint-aware restoration (chosen)

- Good, because outputs stay compatible with documented Akkadian phonotactics
- Good, because tilde-bearing sequences are restored predictably
- Good, because rule ordering is explicit and maintainable
- Bad, because the rule table is larger and must be regression-tested carefully

### Simple merge

- Good, because implementation is short
- Bad, because it produces linguistically invalid or ambiguous outputs

### No restoration

- Good, because computation remains transparent
- Bad, because user-facing outputs are less natural and harder to interpret

## Implications and Consequences

- Any change to diphthong behavior must update generated replacement rules and tests together.
- Restoration ordering is part of the public behavior and should be treated as a compatibility-sensitive surface.

## Links

- Code: `src/akkapros/lib/diphthongs.py`
- Code: `src/akkapros/lib/prosody.py`
- Doc: `docs/akkapros/diphthong-processing.md`
- Research notes: `tmp/research-notes.md` (078-082)

## Reviewed By

- Akkapros maintainers


