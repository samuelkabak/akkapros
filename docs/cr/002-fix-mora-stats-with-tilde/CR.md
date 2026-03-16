# Change Request: Fix mora statistics when repairs add `~`

CR-ID: CR-002
Status: Draft
Priority: High
Created: 2026-03-17
Updated: 2026-03-17

---

# Summary

Fix incorrect mora statistics in metrics outputs where repaired text (`~` markers) did not increase total morae and morae-per-word values. This caused original and repaired mora statistics to appear identical in many outputs, which is linguistically incorrect.

---

# Motivation

In repaired text, `~` marks an added mora (vowel lengthening or consonant gemination). Therefore, repaired totals must be higher whenever repairs occur. Current behavior undercounts repaired morae in `analyze_text()` and propagates wrong values to table/JSON/CSV outputs.

---

# Scope

## Included

- Count `~` as +1 mora in `analyze_text()` mora accumulation logic.
- Ensure repaired `mora_stats.total` differs from original when repairs are present.
- Ensure repaired `word_stats.morae_per_word` reflects added morae.
- Add regression tests using a controlled string where expected totals are known.

## Not Included

- Reworking acoustic interval extraction logic.
- Any change to prosody realization algorithm itself.

---

# Current Behavior

- `analyze_text()` ignores `~` during mora counting.
- Repaired and original mora totals can be identical even when repaired text clearly adds morae.

---

# Proposed Change

In `src/akkapros/lib/metrics.py`, within `analyze_text()` mora loop:

- Add explicit branch: `elif c == '~': morae += 1`

This ensures repaired syllables contribute the added mora represented by `~`.

---

# Files Likely Affected

src/akkapros/lib/metrics.py
tests/test_selftests_lib.py

---

# Acceptance Criteria

- [ ] Repaired `mora_stats.total` increases by number of repair mora additions.
- [ ] Repaired `morae_per_word` differs from original when repairs are present.
- [ ] Regression test passes for sample: `tā·ḫā~·za ik~·ta·ṣar` with totals 10 (original) and 12 (repaired).
- [ ] Metrics self-tests and CLI metrics self-tests pass.

---

# Risks / Edge Cases

- Inputs that contain `~` in unexpected positions should still count as one added mora and not crash.

---

# Testing Strategy

- Unit test with controlled known totals.
- Run metrics self-tests.
- Run `metricalc.py --test`.

---

# Rollback Plan

Revert the single counting branch and related regression test if needed.
