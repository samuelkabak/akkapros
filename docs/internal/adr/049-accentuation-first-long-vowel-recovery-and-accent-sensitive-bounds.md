---
adr_id: ADR-049
status: Proposed
created: 2026-04-18
updated: 2026-04-18
superseded_by: null
---

# 49. Accentuation-First Long-Vowel Recovery and Accent-Sensitive Bounds

## Plain Summary

When a syllable carries accentuation, the phonetizer should apply the
accentuation operation before ordinary long-vowel chrono cleanup. Once an
accent-bearing long vowel has entered the elongated space, the legal recovery
range is wider than for an ordinary non-accented long vowel and should be
treated differently.

TL;DR: on accent-bearing long-vowel syllables, accent first, then long-vowel
cleanup; non-accented long vowels keep the narrower ordinary range.

## Context and Problem Statement

The current solver architecture already fixes several important timing
principles: short vowels are hard anchors, long vowels and pauses remain the
ordinary flexible spaces, and accentuation adds a fixed half-foot target whose
shortfall remains in drift.

What is still underspecified is the interaction between accentuation and
ordinary long-vowel recovery when the same syllable has both a long vowel and
accentuation. If ordinary long-vowel recovery runs first, it can consume some
of the timing space before the accentuation step is applied. That weakens the
intended priority of accentuation.

The current records also distinguish ordinary non-accentual long-vowel space
from broader elongated outcomes. That distinction now needs one explicit rule:
accent-bearing long vowels may use the wider elongated range, while ordinary
non-accented long vowels remain capped below `very_long_min`.

## Decision Drivers

- Accentuation priority
- Phonological coherence of long-vowel categories
- Minimal change to the existing solver structure
- Clear separation between ordinary and accent-bearing recovery space

## Considered Options

- Option A — Keep ordinary long-vowel recovery before accentuation for all long
  nuclei.
- Option B — Apply accentuation first on accent-bearing syllables, then perform
  long-vowel cleanup with accent-sensitive legal bounds. (Chosen)
- Option C — Remove long-vowel cleanup from accent-bearing syllables entirely
  and rely only on pauses and drift carry.

## Decision Outcome

We choose Option B.

The solver keeps baseline assignment first. On non-accent-bearing syllables,
ordinary long-vowel recovery remains a tolerance-gated cleanup using the
ordinary long-vowel range bounded above by `very_long_min - 1`.

On accent-bearing long-vowel syllables (`CVV:` and `CVV:C`), accentuation must
run before long-vowel cleanup. After accentuation, long-vowel cleanup may use
the broader accented long-vowel range up to
`vowels.perception_limits.elongation_max`, and it is not activated by the same
ordinary tolerance gate because the vowel is already in an accentually
elongated state.

Syllable models without a long vowel (`C:V` and `CVC:`) do not participate in
this long-vowel cleanup rule.

## Pros and Cons of the Options

### Chosen Option

- Pros:
  - preserves accentuation priority on accent-bearing long vowels
  - keeps the current distinction between ordinary and elongated vowel space
  - gives the solver more legal room to absorb mismatch where accentual
    elongation already exists
- Cons:
  - emitted timings and drift values may change for accent-bearing long-vowel
    cases
  - requires more explicit tests and docs around vowel-bound selection

### Other Options

- Option A:
  - Pro: minimal implementation disturbance
  - Con: lets ordinary cleanup interfere with accentuation priority
- Option C:
  - Pro: conceptually simple
  - Con: removes a useful legal recovery space the user explicitly wants to keep

## Implications and Consequences

- `CR-074` must update the solver order and define accent-sensitive long-vowel
  bounds clearly.
- `REQ-040` must state the tolerance-gated ordinary range and the broader
  accent-bearing range in a testable way.
- Public phonetizer algorithm documentation must describe the revised order and
  the difference between ordinary and accent-bearing long-vowel cleanup.

## Links

- [ADR-041](041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
- [ADR-046](046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- [REQ-040](../req/040-accentuation-first-long-vowel-recovery-and-accent-sensitive-bounds.md)
- [CR-074](../cr/074-apply-accentuation-before-ordinary-long-vowel-drift-recovery.md)

## Implementation Notes (optional)

- The widened accented-vowel range is a legality-space change for recovery, not
  a new accent target.

## Reviewed By

- Internal phonetizer specification review pending implementation.
