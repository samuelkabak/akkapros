---
adr_id: ADR-046
status: Accepted
created: 2026-04-14
updated: 2026-04-15
superseded_by: null
---

# 46. Phonetizer Timeline Drift Assignment with Hard Short Vowels

## Plain Summary

The phonetizer timing model remains a timeline organized by `cvc_reference`
beat units, but short vowels are no longer part of the ordinary drift-recovery
space. They become hard anchors like singleton consonants. Long vowels and
pauses remain the legal spaces where the solver may absorb mismatch, and the
mini-pause recovery idea remains available between merged units.

TL;DR: keep the existing timeline solver, keep the same syllable classes and
accentuation increment, but stop using short vowels as elastic timing repair.

## Context and Problem Statement

[ADR-041](041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
already fixed the broader stability-first architecture: consonants are stable,
drift is consumed before vowel movement, and pause discharge operates on the
same beat reference. The live implementation in `src/akkapros/lib/phonetize.py`
still follows that architecture, but it currently leaves one ambiguity that now
needs to be resolved more narrowly.

At present, `_apply_vowel_correction()` can move any nucleus within its legal
category bounds, and `_vowel_bounds()` gives short vowels a flexible band. That
means short vowels still function as ordinary local drift-recovery space.

The requested change does not replace the current solver. It narrows one part
of it: short vowels must be treated as hard anchors, while long vowels and
pauses remain flexible. The mini-pause idea already associated with CR-059
remains part of the architecture and now matters more, because some mismatch
that was previously hidden inside short-vowel correction will instead remain in
drift until a later compensating site is reached.

## Decision Drivers

- Clarity: the repository needs one unambiguous statement of where drift may and
  may not be discharged.
- Minimal change: preserve the current solver structure instead of opening a new
  timing model.
- Phonological coherence: short vowels should behave like fixed short units,
  not like elastic local repair buffers.
- Research legibility: the difference between the old and new solver must be
  easy to explain and test.
- Refactorability: `drift_tolerance` may later be removed, so the change should
  not make tolerance central to the solver design.

## Considered Options

- Option A: keep the current generic vowel-correction model in which short and
  long vowels both remain ordinary recovery space.
- Option B: preserve the current solver but harden short vowels, keeping long
  vowels and pauses as the remaining ordinary recovery space. (Chosen)
- Option C: remove `drift_tolerance` immediately and redesign the whole solver
  around pause-only discharge.

## Decision Outcome

We choose Option B.

The phonetizer continues to realize timing on a timeline divided into
`cvc_reference` units. The syllable classes and their nominal beat values do not
change:

- `CV = 0.5 * cvc_reference`
- `CVC = 1.0 * cvc_reference`
- `CVV = 1.0 * cvc_reference`
- `CVVC = 1.5 * cvc_reference`

Accentuation also does not change. It still adds exactly
`0.5 * cvc_reference` and still uses accentable consonants or long-vowel space,
not short vowels, as its realization targets.

What changes is the ordinary recovery-space contract:

- singleton consonants remain hard anchors
- short vowels also become hard anchors
- long vowels remain flexible within their legal bounds
- punctuation-owned pauses remain flexible within their legal bands
- mini pauses remain available as phonetizer-inserted recovery gaps where no
  punctuation-owned pause already exists and drift reaches the configured mini
  threshold

The default `drift_tolerance` is changed to `0`. The parameter stays in the
architecture for now, but it must remain an isolated policy layer so a later
record can remove it cleanly if repository experience shows that the tolerance
band is no longer needed.

## Pros and Cons of the Options

### Chosen Option

- Pros:
  - keeps the current solver recognizable and testable
  - makes the requested change very small and explicit
  - avoids hiding timing mismatch inside short-vowel stretching
  - works naturally with punctuation-owned pause discharge and mini-pause
    recovery
- Cons:
  - more drift will remain visible after `CV` and `CVC` syllables
  - timings and diagnostics will change for existing examples and tests

### Other Options

- Option A:
  - Pro: minimal implementation disturbance
  - Con: preserves the exact behavior the new decision is trying to forbid
- Option C:
  - Pro: conceptually cleaner in the long term
  - Con: larger than the requested change and therefore too speculative here

## Implications and Consequences

- `CR-059` must describe both the extracted current algorithm and the requested
  new algorithm side by side.
- `REQ-033` must state the hard-short-vowel rule directly and testably.
- The implementation in `src/akkapros/lib/phonetize.py` will need a narrower
  ordinary correction path that excludes short vowels.
- The default config must set `drift_tolerance` to `0`.
- Public phonetizer documentation, especially
  `docs/akkapros/phonetizer-algorithm.md`, must explain the timeline model, the
  new hard-short-vowel rule, and the role of mini pauses clearly.
- The implementation should keep tolerance handling isolated so later removal is
  low risk.

## Links

- [ADR-041](041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
- [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- [REQ-033](../req/033-phonetizer-pause-bands-and-pause-metrics-reporting.md)

## Implementation Notes (optional)

- The implementation should separate short-vowel immutability from long-vowel
  correction and from pause discharge instead of keeping one undifferentiated
  vowel-correction step.
- The future possible removal of `drift_tolerance` is explicitly deferred, not
  rejected.

## Reviewed By

- Internal phonetizer specification review pending implementation.
