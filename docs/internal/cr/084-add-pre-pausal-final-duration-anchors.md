---
cr_id: CR-084
status: Draft
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
implements: 'REQ-044'
---

# Change Request: Add Pre-Pausal Final Duration Anchors

# Summary

Add dedicated pre-pausal final anchors to the phonetizer timing table:

- `consonants.<class>.coda_final`
- `vowels.short_final`
- `vowels.long_final`

and use them only when the immediately following unit is a punctuation-owned
short or long pause. For long vowels in that position, ordinary downward drift
recovery shall use `long_final` as its floor instead of `long_min`.

Repository inspection on 2026-04-19 shows that the live phase-2 solver uses the
same coda and vowel anchors regardless of whether the syllable is clause-
internal or immediately pre-pausal. This CR adds the missing final-position row
without changing resync-pause behavior or pause-band selection itself.

---

# Motivation

The current solver distinguishes punctuation-owned pauses from ordinary segmental
timing, but it does not distinguish the segment that stands directly before a
punctuation-owned pause. That leaves no clean way to tune phrase-final codas
and vowels independently of clause-internal ones.

The requested change is localized. It does not create a new pause type and does
not redesign beat alignment. It only adds a context-sensitive anchor row for
segments directly before punctuation-owned pauses.

---

# Scope

## Included

- Add `coda_final` to each consonant class row.
- Add `short_final` and `long_final` to the vowels row.
- Apply those anchors only before punctuation-owned short or long pauses.
- Keep inserted resync pauses excluded from the final-anchor trigger.
- Update long-vowel ordinary recovery so the floor becomes `long_final` in that
  same pre-pausal context.
- Update config verification, default/help/demo surfaces, docs, and tests.

## Not Included

- Adding a `very_long_final` anchor.
- Retuning punctuation-owned pause bands.
- Changing row identity or intonation typing for pause rows.
- Applying final anchors before inserted resync pauses.

---

# Current Behavior

Observed current behavior on 2026-04-19:

- `_consonant_anchor(..., 'C')` always returns the ordinary class-local `coda`
  value
- `_vowel_anchor()` always returns the ordinary `short` or `long` vowel anchor
- `_vowel_bounds(..., ordinary_recovery=True)` uses `[long_min, ordinary_max]`
  for long vowels, with no special pre-pausal floor
- inserted recovery pauses and punctuation-owned pauses are distinguished by row
  type, but anchor selection does not currently react to that distinction

The runtime therefore lacks a dedicated final-position anchor row.

---

# Proposed Change

## 1. Extend the timing table

Each consonant class row gains `coda_final`, and the vowel row gains
`short_final` and `long_final`.

## 2. Make anchor selection context-aware

When the next realized unit is a punctuation-owned short or long pause:

- coda consonants use `coda_final`
- short vowels use `short_final`
- long vowels use `long_final`

Otherwise, the ordinary `coda`, `short`, and `long` anchors remain in force.

## 3. Keep inserted resync pauses out of the trigger condition

The new final anchors apply only before punctuation-owned pauses. Inserted
`MEN|...|MP|...` rows do not trigger them.

## 4. Change the long-vowel recovery floor in that same context

If an ordinary long vowel immediately precedes a punctuation-owned short or long
pause and is adjusted downward during ordinary recovery, the legal floor is
`long_final` rather than `long_min`.

---

# Technical Design

Concrete implementation surfaces:

- extend the default schema and `src/akkapros/config/default.yaml` with the new
  keys
- update `verify_phonetize_config()` to validate the new anchors alongside the
  existing vowel and consonant order relations
- introduce or reuse a pause-context helper in `src/akkapros/lib/phonetize.py`
  so `_consonant_anchor()`, `_vowel_anchor()`, and `_vowel_bounds()` can detect
  whether the immediately following unit is a punctuation-owned short or long
  pause
- keep resync-pause rows excluded from that branch
- refresh tests that pin final-position segment timing and docs that describe
  the duration table

Suggested verification coverage:

- default config exposes the new keys
- context-aware unit test for coda_final selection
- context-aware unit test for short_final/long_final selection
- long-vowel recovery test that proves the pre-pausal floor is `long_final`
- negative test showing inserted resync pauses do not activate final anchors

---

# Files Likely Affected

src/akkapros/lib/phonetize.py  
src/akkapros/config/default.yaml  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/confwriter.py  
tests/test_phonetize_lib.py  
tests/test_config_support.py  
tests/test_integration.py  
docs/akkapros/configuration.md  
docs/akkapros/phonetizer.md  
docs/akkapros/phonetizer-algorithm.md  
demo/akkapros/lexlinks/construct-demo.yaml  
demo/akkapros/prosmaker/corpus-demo.yaml  

---

# Acceptance Criteria

- [ ] Each consonant class row exposes `coda_final`.
- [ ] The vowels row exposes `short_final` and `long_final`.
- [ ] Preceding a punctuation-owned short or long pause selects final anchors.
- [ ] Preceding an inserted resync pause does not select final anchors.
- [ ] Ordinary long-vowel downward recovery before punctuation-owned pauses uses
      `long_final` as the floor.
- [ ] Config/help/demo/doc surfaces explain the new pre-pausal-only scope.
- [ ] Focused unit coverage pins the context-sensitive behavior.

---

# Risks / Edge Cases

- If the trigger condition is based only on silence rows generically, inserted
  resync pauses will be mistaken for punctuation-owned final pauses.
- Verification relations must be updated carefully so the new anchors do not
  create contradictory order expectations.
- Tests that currently assume uniform coda/long-vowel anchors across contexts
  will become stale.

---

# Testing Strategy

Unit tests:

- config surface includes the new keys
- coda_final selected before punctuation-owned pauses
- short_final and long_final selected before punctuation-owned pauses
- long_final is used as the pre-pausal ordinary-recovery floor
- inserted resync pause does not activate final anchors

Integration tests:

- emitted phone rows differ when final anchors are overridden through config

Manual checks:

- inspect config help and public docs to confirm the new keys are described as
  pre-punctuation-final only

---

# Rollback Plan

Remove the final-anchor keys and restore the uniform ordinary coda/vowel anchor
selection logic.

---

# Related Issues

- [REQ-044](../req/044-pre-pausal-final-duration-anchors.md)
- [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)

---

# Tasks

## Implementation

- [ ] Add `coda_final`, `short_final`, and `long_final`
- [ ] Make anchor selection context-aware for punctuation-owned pauses
- [ ] Use `long_final` as the pre-pausal long-vowel recovery floor

## Tests

- [ ] Update config/help surface tests
- [ ] Add context-aware anchor and recovery tests

## Documentation

- [ ] Update phonetizer/config docs and demo YAML examples

## Review

- [ ] Verify inserted resync pauses do not trigger final-anchor behavior

---

# Implementation Blockers
