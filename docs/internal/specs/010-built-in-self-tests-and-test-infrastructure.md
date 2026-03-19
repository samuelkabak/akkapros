# Requirement: Built-in Self-Tests and CLI Test Infrastructure

REQ-ID: REQ-010
Status: Implemented
Priority: Medium
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

Every CLI module in `src/akkapros/cli/` shall expose a `--test` flag that runs
built-in self-tests and exits with code 0 on pass or code 1 on failure.  Library
modules in `src/akkapros/lib/` shall expose corresponding `run_tests()` functions.
Pipeline-level regression tests shall be organized under `tests/` and runnable
via `pytest`.

---

# Motivation

The pipeline operates on ancient-language data with complex Unicode characters and
intricate phonological rules. Regressions in any stage can produce subtly wrong
outputs that appear plausible to a non-specialist. Built-in self-tests catch
regressions at the point of use, without requiring test harness setup. They also
make the toolkit usable in sandboxed environments where pytest may not be installed.

The syllabifier test suite is especially critical (≈40 cases);
`tokenize_line()` and `syllabify_text()` have been hard-won through days of
debugging edge cases.

---

# Acceptance Criteria

## Per-CLI `--test`

- [ ] `atfparser.py --test`: runs parser self-tests; exits 0/1.
- [ ] `syllabifier.py --test`: runs syllabifier test suite (≥40 cases); exits 0/1.
- [ ] `prosmaker.py --test`: runs prosody engine tests; exits 0/1.
- [ ] `prosmaker.py --test-diphthongs`: runs diphthong restoration tests; exits 0/1.
- [ ] `metricalc.py --test`: runs metrics tests; exits 0/1.
- [ ] `printer.py --test`: runs printer test cases (IPA mode resolution); exits 0/1.
- [ ] `fullprosmaker.py --test`: runs fullprosmaker CLI resolution tests; exits 0/1.
- [ ] `phoneprep.py --test`: runs phoneprep self-tests; exits 0/1.

## Library `run_tests()` functions

- [ ] Each library module (`atfparse.py`, `syllabify.py`, `prosody.py`, `metrics.py`,
      `print.py`) exposes a `run_tests() -> bool` function.
- [ ] `run_tests()` returns `True` on full pass, `False` when at least one case fails.
- [ ] Test cases use `PASS` / `FAIL` console output with one line per test case.

## Pytest integration

- [ ] `tests/test_selftests_cli.py` and `tests/test_selftests_lib.py` delegate to
      the respective CLI `run_tests()` and library `run_tests()` calls.
- [ ] `pytest tests/ -v` runs all tests and reports failures clearly.
- [ ] `pytest.ini` or `pyproject.toml` configures test discovery correctly.

## Test case quality

- [ ] For the syllabifier suite: at least one test per syllable type (CV, CVC, CVV,
      CVVC, VC, V, VV, VVC), hyphen handling, dash handling, whitespace normalization,
      diphthong expansion, bracket preservation, numbers, punctuation.
- [ ] For the prosody suite: at least one test per accent style (LOB, SOB), per
      legal operation type (vowel lengthening, coda gemination, onset last resort),
      and for forward/backward merge.

---

# User Story (optional)
> As a contributor making a change to the syllabifier library, I want to run
> `python syllabifier.py --test` immediately and see a pass/fail for every
> known-good case so that I can detect regressions before committing.

---

# Interface Notes
- `--test` is a standard flag on all CLI modules.
- Affected components: all `src/akkapros/cli/*.py`, all `src/akkapros/lib/*.py`,
  `tests/test_selftests_cli.py`, `tests/test_selftests_lib.py`.

---

# Open Questions
- [ ] Should a `--test-all` flag be added to `fullprosmaker.py` to run all suite
      tests in sequence?
- [ ] TO_BE_CONFIRMED: will test output be captured as XML/JUnit for CI reporting?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature)
- DO NOT rewrite `tokenize_line()` or `syllabify_text()` without first adding
  a failing test case and verifying all existing 40+ cases still pass.

# Related
- Related ADRs: [ADR-014](../adr/014-cli-built-in-self-tests.md)
- Implementation CRs: none currently open

# Non-Goals
- Does NOT perform integration or end-to-end corpus tests automatically in CI.
- Does NOT measure test coverage percentage (TO_BE_CONFIRMED whether coverage is
  tracked in a CI pipeline).
- Does NOT generate test reports in HTML format without additional tooling.

# Security / Safety Considerations
- Test execution must not write to production output directories; tests should use
  temporary directories.
- Test fixtures containing Akkadian Unicode must be stored as UTF-8 files or
  inline Python string literals; platform encoding assumptions must be avoided.
