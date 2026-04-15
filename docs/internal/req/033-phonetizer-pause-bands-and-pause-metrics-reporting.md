---
req_id: REQ-033
status: Implemented
priority: High
impact: Mutative
created: 2026-04-14
updated: 2026-04-15
related_adrs: 'ADR-046, ADR-041'
implemented_by: 'CR-059'
---

# Requirement: Phonetizer Timeline Drift Assignment with Hard Short Vowels

## Summary

The system shall keep the current phonetizer timeline model based on
`cvc_reference`, but it shall stop treating short vowels as ordinary
drift-recovery space.

Short vowels become hard timing anchors like singleton consonants. Long vowels
remain flexible inside their legal range, punctuation-owned pauses remain
flexible inside their legal ranges, and phonetizer-inserted mini pauses remain
available at eligible merged-unit boundaries. The default `drift_tolerance`
shall be `0`.

---

## Motivation

The live Phase 2 implementation already has a coherent timeline solver, but its
generic nucleus-correction step still allows short vowels to absorb ordinary
drift. That is broader than the requested model.

This requirement narrows the existing solver without replacing it. It keeps the
same syllable inventory, the same beat mapping, the same accentuation increment,
and the same pause logic family, but it makes the legal recovery space explicit:
short vowels are fixed, long vowels and pauses remain flexible.

---

## Acceptance Criteria

*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [x] Given Phase 2 timing is entered, when syllables are classified for timing,
      then the active non-accentuated classes remain exactly `CV`, `CVC`, `CVV`,
      and `CVVC` and the active accentuated classes remain exactly `C:V`,
      `CVC:`, `CVV:`, and `CVV:C`.
- [x] Given Phase 2 timing is entered, when the row stream is interpreted, then
      each syllable still begins with a consonant or pseudo-consonant in timing
      terms, including hiatus and vowel-transition rows.
- [x] Given nominal beat values are computed, when a non-accentuated syllable is
      targeted, then `CV = 0.5 * cvc_reference`, `CVC = 1.0 * cvc_reference`,
      `CVV = 1.0 * cvc_reference`, and `CVVC = 1.5 * cvc_reference` remain the
      active targets.
- [x] Given a syllable is accentuated, when its target is computed, then the
      solver still adds exactly `0.5 * cvc_reference` beyond the corresponding
      non-accentuated target.
- [x] Given a non-accentuated `CV` or `CVC` syllable is realized, when ordinary
      drift recovery is applied, then the short vowel duration is not changed.
- [x] Given a non-accentuated `CVV` or `CVVC` syllable is realized, when
      ordinary drift recovery is applied, then the long vowel may still move
      inside its legal range.
- [x] Given a punctuation-owned short or long pause is realized, when the solver
      chooses a pause duration, then it chooses one legal duration inside the
      configured band that brings signed drift as close to zero as that band
      allows.
- [x] Given a punctuation-owned pause cannot bring signed drift exactly to zero,
      when the pause is realized, then the realized pause duration is clamped
      inside the legal band and the residual drift is carried forward.
- [x] Given the stream reaches a merged-unit boundary with no punctuation-owned
      pause, when `drift_cursor <= -pauses.mini.min`, then the phonetizer may
      insert one mini pause to bring drift as close as possible to zero inside
      the configured mini band.
- [x] Given a mini pause is inserted, when its function is described, then it is
      treated as a non-voluntary phonetizer recovery gap rather than as lexical
      phoneme structure or punctuation-owned pause structure.
- [x] Given accentuation is realized, when the solver distributes the added
      `0.5 * cvc_reference`, then it does not use short vowels as accentuation
      targets.
- [x] Given the default phonetize timing config is inspected, when
      `drift_tolerance` is read, then the default value is `0`.
- [x] Given the implementation is reviewed, when tolerance handling is traced,
      then `drift_tolerance` is isolated enough that a later narrow change could
      remove it without redesigning the whole solver.
- [x] Given public phonetizer documentation is updated, when
      `docs/akkapros/phonetizer-algorithm.md` is read, then it explains the
      timeline model, the hard-short-vowel rule, the role of long vowels and
      pauses as remaining recovery space, and the mini-pause rule clearly.

---

## User Story (optional)

> As the maintainer of the phonetizer timing model, I want short vowels treated
> as hard anchors so the emitted rhythm reflects drift carried across the
> timeline instead of being hidden inside local short-vowel stretching.

---

## Interface Notes

- Timing reference:
  - `cvc_reference`
- Non-accentuated classes:
  - `CV`
  - `CVC`
  - `CVV`
  - `CVVC`
- Accentuated classes:
  - `C:V`
  - `CVC:`
  - `CVV:`
  - `CVV:C`
- Recovery-space contract:
  - singleton consonants: hard
  - short vowels: hard
  - long vowels: flexible inside legal range
  - pauses: flexible inside legal band
- Grouping model:
  - syllables belong to words
  - words belong to merged units
  - `&` marks algorithmic merge
  - `+` marks user-declared merge
- Pause interpretation:
  - punctuation and newlines create voluntary short or long pauses
  - mini pauses are phonetizer-inserted recovery gaps only

---

## Open Questions

- [ ] Should a later record introduce a separate mini-pause trigger parameter
      instead of reusing `pauses.mini.min` as the trigger threshold?
- [ ] After observing the solver with `drift_tolerance = 0`, should a later
      record remove `drift_tolerance` entirely?

---

## Implementation Notes (optional)

- Primary implementation target: `src/akkapros/lib/phonetize.py`
- Config default update: `src/akkapros/config/default.yaml`
- User-facing documentation obligation includes `docs/akkapros/phonetizer-algorithm.md`
- Implementation is by [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)

## Related

- Related ADRs: [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md), [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- Implementation CRs: [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)

## Non-Goals

- This requirement does not replace the current phonetizer architecture.
- This requirement does not change the syllable inventory or the beat mapping.
- This requirement does not remove `drift_tolerance`; it only changes the
  default and requires future-safe isolation.
- This requirement does not redefine downstream metrics output.

## Security / Safety Considerations

- None specific beyond the research-grade safety requirement that the solver be
  explicit and reproducible rather than silently changing timing behavior.
