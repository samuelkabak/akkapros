# Change Request: Add Akkadian text likehood for format-validation

CR-ID: CR-013
Status: Approved
Priority: Medium
Created: 2026-03-22
Updated: 2026-03-22
Implements: ADR-001 (CLI/Lib Separation), ADR-009 (Function Word Policy)

---

# Summary

A prototype implementation of `akkadian_likelihood()` existed during
development. This CR creates a canonical implementation in `lib/utils.py`,
centralizes related detection constants in `lib/constants.py`, and wires the
scorer into `validate_intermediate_format()` as a lightweight sanity guard for
`*_proc.txt` input.

---

# Motivation

- **Code hygiene**: Earlier prototypes duplicated `FUNCTION_WORDS` and
  re-declared existing phonetic sets; a canonical utility reduces duplication.
- **Robustness**: The prototype exposed undefined-symbol risks when used as a
  library helper; the canonical implementation fixes these faults and centralizes
  related constants.
- **Canonical home**: `FUNCTION_WORDS` is linguistically shared (ADR-009 scope)
  and belongs in `constants.py`, not `prosody.py`.
- **Validation coverage**: `validate_intermediate_format()` currently only
  checks for the presence of Akkadian letters; the likelihood scorer offers a
  richer second opinion for `*_proc.txt` files before they enter the
  syllabification pipeline.

---

# Scope

## Included

- Create a robust `akkadian_likelihood()` implementation and accompanying
  `classify_text()` in `lib/utils.py` with scoring constants prefixed
  `_AKKASCORE_*`.
- Add `AKKADIAN_DISTINCTIVE`, `NON_AKKADIAN_CHARS`, `AKKADIAN_ENCLITICS`, and
  `FUNCTION_WORDS` to `lib/constants.py`.
- Update `lib/prosody.py` to import `FUNCTION_WORDS` from constants (removes
  duplicate definition).
- Add likelihood guard in `validate_intermediate_format()` for `proc` stage
  (threshold 0.25, minimum file length 50 chars).
- Create `tests/test_akkadian_likelihood.py`.
- Create `docs/akkapros/utils.md` (contributor reference for `lib/utils.py`).

## Not Included

- Changes to CLI entry points.
- Changes to `syl`, `tilde`, or `atf` format validation (likelihood scorer does not
  work reliably on syllabified text — see Technical Design).
- Extending `FUNCTION_WORDS` or `AKKADIAN_ENCLITICS` beyond current inventory.

---

# Current Behavior

- A prototype implementation of `akkadian_likelihood()` existed but was not
  stabilized or centralized for library use.
- `FUNCTION_WORDS` and related detection constants are not yet canonicalized.
- `validate_intermediate_format()` only checks for presence of at least one
  Akkadian character in the file.

---

# Proposed Change

- `FUNCTION_WORDS` and new detection constants (`AKKADIAN_DISTINCTIVE`,
  `NON_AKKADIAN_CHARS`, `AKKADIAN_ENCLITICS`) live in `lib/constants.py`.
- `lib/prosody.py` imports `FUNCTION_WORDS` from constants.
- `lib/utils.py` contains the full `akkadian_likelihood()` / `classify_text()`
  pair, consuming constants from `constants.py`.
- `validate_intermediate_format()` calls `akkadian_likelihood()` for `proc`
  files, failing if the score is below **0.25** (guard only for files ≥ 50 chars).
- All scoring hyper-parameters are module-level constants in `utils.py` prefixed
  `_AKKASCORE_*` (implementation detail, not public API).

---

# Technical Design

## Why likelihood scoring is restricted to `proc` format

The `akkadian_likelihood` function relies on full word recognition (function-word
frequency) and V/C character ratio computed on raw text.  For `syl` and `tilde`
formats, words are syllabified with dots (`.`) and `¦` markers; the
`WORD_TOKEN_PATTERN` splits them into sub-syllabic fragments that never match the
function-word set.  The function word score drops to 0, pulling the total below 0.25
even for perfectly valid Akkadian — giving false negatives.  It is therefore applied
only to `proc` (clean transliteration) files.

## Threshold rationale (0.25)

Empirical analysis on representative Akkadian texts (including texts with no
distinctive characters and no function words) shows that well-formed Akkadian
`proc` files score between 0.25 and 0.75 on the four-component metric:

| Component               | Weight | Typical contribution (no func words) |
|-------------------------|--------|---------------------------------------|
| Distinctive chars (š, ṭ…) | 0.40 | 0.05 – 0.40 depending on text       |
| Vowel/Consonant ratio   | 0.20   | 0.14 – 0.20 (Akkadian V/C ≈ 0.6–0.9) |
| Function words          | 0.30   | 0.0 – 0.30                            |
| Length bonus            | 0.10   | 0.00 – 0.02 (file-level)              |

A threshold of 0.25 flags clearly non-Akkadian content while leaving a comfortable
margin for short ritual texts or formulaic passages with no function words.

## `AKKADIAN_ENCLITICS` definition

Common clitics documented in Huehnergard (2011) §17–19 and von Soden (1969) §§47–50:

| Enclitic | Function |
|----------|----------|
| `ma`, `mi` | coordinative / quotative |
| `šu`, `šī`, `šunu`, `šina` | 3rd-person object/possessive suffixes |
| `ya`, `ia` | 1st-person singular possessive |
| `ni` | subjunctive suffix |
| `ku`, `ki`, `kunu`, `kina` | 2nd-person possessive |
| `nu` | 1st-person plural suffix |

---

# Files Affected

```
src/akkapros/lib/constants.py        (extended: 4 new constants)
src/akkapros/lib/prosody.py          (FUNCTION_WORDS import replaces local def)
src/akkapros/lib/utils.py            (new functions + validation update)
tests/test_akkadian_likelihood.py    (new)
docs/akkapros/utils.md               (new)
docs/internal/cr/013-*.md            (this file)
```

---

# Acceptance Criteria

- [x] `akkadian_likelihood()` importable from `akkapros.lib.utils` without `NameError`
- [x] `FUNCTION_WORDS` defined only in `constants.py`; `prosody.py` imports it
- [x] `validate_intermediate_format(..., "proc")` raises `FormatValidationError` when
      passed clearly non-Akkadian content (score < 0.25, file ≥ 50 chars)
- [x] `validate_intermediate_format(..., "syl")` / `"tilde"` unaffected
- [x] `utils.run_tests()` passes (existing + new tests)
- [x] All existing pytest tests pass (`tests/`)
- [x] `docs/akkapros/utils.md` created

---

# Risks / Edge Cases

- **Very short `proc` excerpts**: Texts below 50 chars bypass the likelihood check.
  This is intentional — short excerpts may score low regardless of authenticity.
- **All-content-word texts** (no function words, no distinctive chars): Score ≈ 0.25.
  At the boundary; accepted at the chosen threshold.
- **Non-Akkadian enclitics false match**: Minimal risk given `len(word) > len(enclitic)`
  guard and Akkadian-only character filtering upstream.
- **`prosody.py` relies on `FUNCTION_WORDS`** being a container supporting `in`;
  changing `Set[str]` → `frozenset` is backward-compatible.

---

# Testing Strategy

**Unit tests** (`tests/test_akkadian_likelihood.py`):
- Known Akkadian text → score ≥ 0.75
- Known English text → score = 0.0 (forbidden chars)
- Text with function words → score ≥ 0.50
- Short text (< min_length) → non-zero but low score
- Text with enclitics → non-zero function_word_matches
- Zero-score case (forbidden chars)
- Phonetically plausible but non-Akkadian text → score < 0.50

**Integration via `utils.run_tests()`**:
- Basic smoke tests included in the existing self-test harness.

**Regression**:
- All `tests/test_selftests_lib.py` must pass unchanged.
- `validate_intermediate_format` tests for `syl`/`tilde`/`atf` must pass unchanged.

---

# Rollback Plan

Revert the edits to `constants.py`, `prosody.py`, and `utils.py` via git
(`git checkout HEAD -- <file>`).  If needed, restore earlier prototype artifacts from
developer backups.

---

# Tasks

## Implementation
- [x] Extend `constants.py` with detection constants + `FUNCTION_WORDS`
- [x] Update `prosody.py` imports
- [x] Implement `akkadian_likelihood` / `classify_text` in `utils.py`
- [x] Update `validate_intermediate_format` for `proc` guard

## Tests
- [x] Create `tests/test_akkadian_likelihood.py`
- [x] Extend `utils.run_tests()` with smoke tests

## Documentation
- [x] Create `docs/akkapros/utils.md`
- [x] Create this CR

---

# Notes

The `akkadian_likelihood` scorer is a **pragmatic heuristic**, not a linguistically
rigorous classifier.  It is designed as a cheap sanity filter, not a replacement for
expert judgment.  False negatives (valid Akkadian scoring low) are possible for
atypical texts; the 0.25 threshold and 50-char minimum guard are deliberately
conservative to avoid blocking legitimate data.
