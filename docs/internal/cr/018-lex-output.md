# Change Request: Add lexical output file `<prefix>_lex.txt` from prosmaker

CR-ID: CR-018
Status: Draft
Priority: Medium
Impact: Additive
Created: 2026-03-26
Updated: 2026-03-26
Implements: REQ-013
---

# Summary

Emit a new lexical output file `<prefix>_lex.txt` from `prosmaker`. The file
is a lexical view of the `_syl`/`_tilde` stages that preserves syllable
separators and user pre-merge annotations but does not perform any accent
realization, bimoraic repairs, or automatic merging beyond user-provided
`+` markers. The file annotates user pre-merge `+` with `ᶜ ` and marks function
words with `ᶠ` for human-readable lexical inspection.

---

# Motivation

Provide researchers with a stable lexical export that mirrors syllabification
and user annotations without prosodic repairs. This view is useful for
lexicographic tasks, manual review, and as a stable input to downstream
linguistic tools that must not depend on prosody realization.

---

# Scope

## Included

- Produce `<prefix>_lex.txt` for every run of `prosmaker`.
- Convert `+` to `ᶜ ` (superscript c + space) and preserve token boundaries.
- Suffix function words from the existing inventory with `ᶠ` (superscript f),
  preserving trailing whitespace.
- Preserve `·` syllable separators, `¨` diphthong markers, and `-` hyphens.

## Not Included

- Any prosody realization, gemination, vowel lengthening, or automatic
  prosodic merging beyond `+` markers.

---

# Current Behavior

No `_lex.txt` file is emitted. Researchers must infer lexical structure from
other pipeline outputs that may include prosodic repairs or merging.

---

# Proposed Change

- Always emit `<prefix>_lex.txt` with the lexical conventions described.
- Document the file in `docs/akkapros/prosmaker.md` and add integration
  fixture(s) demonstrating expected output.

Examples:

```
syl input:  aḫ·râ·taš¦e·li+ap·sî¦
lex output: aḫ·râ·taš e·liᶜ ap·sî

syl input:  a·na¦e·¨a¦ip·taš·rū¦
lex output: a·naᶠ e¨a ip·taš·rū
```

---

# Technical Design

- Implement a writer that runs immediately after `_syl` is parsed and before
  any prosody realization.
- Transformations per line:
  - Replace `¦` word delimiter with a space.
  - Replace user-attached `+` with `ᶜ ` and split tokens accordingly.
  - Detect function words and append `ᶠ` before the following space.
  - Do not emit `~` characters.

---

# Files Likely Affected

`src/akkapros/lib/prosody.py` (writer), `src/akkapros/cli/prosmaker.py`, test
files and integration fixtures under `tests/` and `demo/.../results/`.

---

# Acceptance Criteria

- `<prefix>_lex.txt` is produced by `prosmaker`.
- `+` markers are replaced with `ᶜ `, function words annotated with `ᶠ`.
- No `~` markers and no prosody-induced merges beyond user `+` markers.
- Unit and integration tests validate behavior.

---

# Risks / Edge Cases

- Unicode superscript handling (`ᶜ`, `ᶠ`) must be verified on all supported
  platforms and test environments.
- Function-word detection must use the existing inventory consistently and must
  not accidentally reclassify non-function words.
- User-provided `+` markers inside unexpected contexts must remain lexical only
  and must not trigger prosodic merging.

---

# Testing Strategy

- Add unit tests to `src/akkapros/lib/prosody.py::run_tests()` ensuring
  `_lex.txt` transformations work for representative `_syl` fixtures.
- Add pytest tests (`tests/test_prosmaker_lex.py`) asserting exact expected
  output lines (including Unicode superscripts).
- Add integration fixture under `tests/integration_refs/fullprosmaker/` and
  include the `_lex.txt` expected output in `demo/.../results/`.

---

# Rollback Plan

Remove the `_lex.txt` writer and its tests and documentation. Existing outputs
remain unchanged because this CR is additive.

---

# Related Issues

- This CR legalizes a new lexical export alongside the existing outputs covered
  by `REQ-003`, `REQ-005`, and `REQ-007`.

---

# Tasks

## Implementation

- [ ] Add `_lex.txt` writer to `prosmaker` and default-enable it.

## Tests

- [ ] Add `run_tests()` unit checks.
- [ ] Add pytest tests and integration fixtures.

## Documentation

- [ ] Document in `docs/akkapros/prosmaker.md` and `docs/akkapros/syllabifier.md`.

## Review

- [ ] Verify exact lexical examples against the approved prompt text.
- [ ] Verify no existing outputs change apart from the new `_lex.txt` file.

---

# Notes for CR-018

This is an additive, non-breaking enhancement designed to improve researcher
workflows and maintain a stable lexical export. Reviewers should pay
attention to UTF-8 handling and tests for superscript characters.
