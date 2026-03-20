# Change Request: Fix xfail in syllabifier tests, clean CR-004 untracked files

CR-ID: CR-006
Status: Done
Priority: High
Created: 2026-03-20
Updated: 2026-03-20

---

# Summary

Resolve the `xfail` suppression and restore failing syllabifier unit tests. The
failures included the diphthong-separation bug and additional tokenization issues
caused by an incomplete implementation of CR-003 (escape delimiter changes) and
by spacing/escape handling for reserved markers ({{ }}). This CR records the
work: capture failing cases as focused regression tests, complete the CR-003
fixes in syllabifier tokenization, apply minimal code fixes in
`src/akkapros/lib/syllabify.py`, and remove the `xfail` so CLI self-tests run
green in CI.

---

# Motivation

Multiple syllabifier unit-tests were failing and had been temporarily suppressed
via `pytest.xfail(...)`. Root causes included:

- A regression in diphthong separation / vowel-adjacency handling.
- An incomplete CR-003 escape-delimiter change that left inconsistent tokenization
  paths.
- A spacing/escape processing bug around reserved delimiters (`{{ }}`) that
  produced unexpected tokens in the syllabifier self-tests.

Fixing these issues is required to restore test coverage, ensure correct mora
counting and prosody outputs, and avoid masking regressions in CI.

---

# Scope

## Included

- Add focused regression tests that reproduce the failing cases.
- Complete the incomplete CR-003 implementation in syllabifier tokenization.
- Fix spacing/escape handling for reserved delimiters (`{{ }}`) when encountered
  by the syllabifier path.
- Implement targeted fixes in `src/akkapros/lib/syllabify.py` (tokenization,
  diphthong-expansion, and adjacent code paths) so tests pass.
- Remove the runtime `pytest.xfail()` calls and confirm the CLI self-tests pass
  in CI.

## Not Included

- Large refactors to syllabification beyond the minimal fixes.
- Changes to prosody realization logic unless the regression explicitly requires it.

---

# Current Behavior

- The test-suite contained a runtime `pytest.xfail(...)` that masked multiple
  syllabifier-related failures (diphthong separation, tokenization inconsistencies
  with CR-003, and reserved-delimiter spacing bugs).
- Affected CI runs reported xfailed rather than failed and therefore did not
  surface the regressions to maintainers.

---

# Proposed Change

- Add focused regression tests for all failing syllabifier cases (including the
  diphthong separator and the CR-003/`{{ }}`-related tokens).
- Finish the CR-003 implementation in the syllabifier code paths so escape
  delimiter handling is consistent across the pipeline.
- Apply minimal, well-tested fixes in `src/akkapros/lib/syllabify.py`.
- Remove the runtime `pytest.xfail()` and ensure the CLI self-tests pass in CI.
- Clean remaining repair terminology from CR-004 in untracked files

---

# Technical Design

Investigate and remedy the following code paths (typical hotspots):

- `tokenize_line()` — tokenization and bracket/diphthong/escape handling.
- `syllabify_text()` — syllable boundary logic and morpheme joining.
- Spacing and escape processing for reserved delimiters `{{ }}` used by CR-005
  (ensure spaces inside delimiters are handled consistently).

Implementation notes:

- Preserve the two-phase diphthong processing design: expand with a separator
  for syllabification, then optionally restore diphthongs after prosody
  realization.
- Ensure escape delimiters and reserved markers are tokenized consistently with
  surrounding whitespace handling.
- Add regression tests that cover: `ua`, `iā`, `VV`, reserved delimiters with
  surrounding spaces, hyphen/dash edge cases, bracketed foreign text, and
  boundary cases (line starts / line ends).

---

# Files Likely Affected

src/akkapros/lib/syllabify.py
src/akkapros/cli/syllabifier.py
tests/test_selftests_cli.py
tests/test_selftests_lib.py

---

# Acceptance Criteria

- [ ] Focused regression tests reproduce prior failures and initially fail.
- [ ] Minimal fixes implemented in `src/akkapros/lib/syllabify.py`.
- [ ] `akkapros.cli.syllabifier --test` returns exit code 0 and passes self-tests.
- [ ] `tests/test_selftests_cli.py` no longer triggers a dynamic `pytest.xfail()`
  for syllabifier-related tests.
- [ ] CR-003 incomplete implementation completed in syllabifier tokenization.
- [ ] Spacing/escape handling for `{{ }}` corrected and CR-005 notes updated.
- [ ] CR-004 remaining mechanical rename actions executed for tracked files.
- [ ] Untracked legacy `repair` terminology identified and addressed.

---

# Risks / Edge Cases

- Over-eager insertion of separators could mis-handle real diphthong notation.
- Changes to tokenization may interact with bracketed foreign text handling.
- Tests must include bracketed and hyphenated edge cases to avoid regressions.

---

# Testing Strategy

- Add unit tests for minimal failing inputs.
- Run CLI self-tests:

```
python -m akkrapros.cli.syllabifier --test
python -m akkrapros.cli.fullprosmaker --test-all
```

- Run full pytest suite.

---

# Rollback Plan

- Revert the commit that introduced the fix and re-enable the `pytest.xfail()`
  (temporary) if side effects appear in CI.

---

# Related Issues

- tests/test_selftests_cli.py — contains the runtime xfail call.
