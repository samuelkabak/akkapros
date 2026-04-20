---
req_id: REQ-044
status: Implemented
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-20
related_adrs: 'ADR-045, ADR-046'
implemented_by: 'CR-084'
---

# Requirement: Pre-Pausal Final Duration Anchors

# Summary

The phonetizer shall add explicit pre-pausal final duration anchors for vowels
and codas that immediately precede punctuation-owned short or long pauses.

The approved config surface shall gain `coda_final` inside each consonant class
row and `short_final` / `long_final` inside the vowels row. These final anchors
shall apply only when the immediately following unit is a punctuation-owned
short or long pause. They shall not apply before inserted resync pauses.

Historical note:

- This requirement narrows the generalized non-final anchor usage currently
  implied by [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
  and the hard-short-vowel timing model retained through
  [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md).
- The active contract after this change is that clause-internal and
  pre-punctuation-final positions may use different base anchors.

---

# Motivation

Repository inspection on 2026-04-19 shows that `_consonant_anchor(..., 'C')`
always returns the ordinary coda anchor, `_vowel_anchor()` always returns the
ordinary short or long anchor, and `_vowel_bounds(..., ordinary_recovery=True)`
uses `long_min` as the ordinary floor for long-vowel recovery. The current
runtime therefore has no dedicated pre-pausal final timing row.

The requested change introduces that missing distinction without redesigning the
whole solver. It lets phrase-final segments before punctuation-owned pauses use
their own anchors and, for long vowels, their own downward-recovery floor.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the approved grouped config surface is materialized, when consonant
      class rows are inspected, then each class exposes `coda_final` alongside
      `coda`.
- [ ] Given the approved grouped config surface is materialized, when the vowel
      row is inspected, then it exposes `short_final` and `long_final`.
- [ ] Given a coda consonant immediately precedes a punctuation-owned short or
      long pause, when its anchor is selected, then `coda_final` is used for the
      corresponding consonant class instead of the ordinary `coda` anchor.
- [ ] Given a short or long vowel nucleus immediately precedes a punctuation-
      owned short or long pause, when its anchor is selected, then
      `short_final` or `long_final` is used instead of the ordinary `short` or
      `long` anchor.
- [ ] Given a long vowel immediately precedes a punctuation-owned short or long
      pause and ordinary long-vowel recovery adjusts it downward, when the legal
      floor is computed, then the floor is `long_final` instead of `long_min`.
- [ ] Given the immediately following pause is an inserted resync pause, when
      anchors or long-vowel recovery bounds are selected, then the new final
      anchors are not used.
- [ ] Given default/help/demo/doc surfaces are updated, when the timing table is
      inspected, then the new final-anchor keys are present and documented as
      pre-punctuation-final only.

---

# User Story (optional)
> As a phonetizer maintainer, I want phrase-final segments before punctuation
> pauses to have explicit final anchors so clause-final timing can be tuned
> without perturbing clause-internal anchors.

---

# Interface Notes
- New consonant keys:
  - `phonetize.process.timing_model.durations.consonants.<class>.coda_final`
- New vowel keys:
  - `phonetize.process.timing_model.durations.vowels.short_final`
  - `phonetize.process.timing_model.durations.vowels.long_final`
- Application scope:
  - only before punctuation-owned short/long pauses
  - never before inserted resync pauses
  - affects anchor selection and long-vowel downward-recovery floor
- Affected components:
  - phonetizer timing-model defaults and verification
  - coda and vowel anchor helpers in `src/akkapros/lib/phonetize.py`
  - pause-context detection in the phase-2 solver
  - phonetizer docs, config docs, tests, and demo YAML files

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - add the new final-anchor keys to the canonical timing table
  - make anchor helpers context-aware for punctuation-owned short/long pauses
  - keep inserted resync pauses out of the final-anchor trigger condition
  - update ordinary long-vowel recovery so pre-pausal long vowels use
    `long_final` as their recovery floor

# Related
- Related ADRs: [ADR-045](../adr/045-three-pass-phonetizer-intonation-and-row-derived-mbrola.md), [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- Implementation CRs: [CR-084](../cr/084-add-pre-pausal-final-duration-anchors.md)

# Non-Goals
- This requirement does not change the row identity or duration band of the
  short/long punctuation pauses themselves.
- This requirement does not apply to inserted resync pauses.
- This requirement does not add a `very_long_final` anchor unless a later record
  explicitly requires it.

# Security / Safety Considerations
- The pre-pausal trigger condition must be explicit because applying final
  anchors before inserted resync pauses would blur the distinction between
  punctuation-owned phrasing and algorithmic recovery.
