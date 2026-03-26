# Requirement: Lexical Output from Prosmaker

REQ-ID: REQ-013
Status: Draft
Priority: Medium
Impact: Additive
Created: 2026-03-26
Updated: 2026-03-26
---

# Summary

The system shall emit a lexical output file named `<prefix>_lex.txt` from the
prosody pipeline. This file shall preserve the syllabification structure of the
input lexical material while remaining independent from accentuation and
bimoraic prosody processing.

It shall preserve `·` syllable separators, `¨` diphthong markers, and `-`
sub-word boundaries; replace user pre-merge `+` with `ᶜ `; and mark function
words with a trailing superscript `ᶠ` while preserving the following space.

---

# Motivation

Researchers need a stable lexical export that preserves syllabified word shape
and user lexical annotations without applying accentuation or merge logic.
This output supports lexical inspection, annotation workflows, and regression
testing for the pre-prosodic representation.

---

# Acceptance Criteria

- [ ] Given a `_syl` input line, when `prosmaker` runs, then a corresponding
      `<prefix>_lex.txt` file is always written.
- [ ] Given a `_syl` token containing `+`, when written to `_lex.txt`, then the
      `+` is rendered as `ᶜ ` and lexical token boundaries are preserved.
- [ ] Given a function word in the existing function-word inventory, when
      written to `_lex.txt`, then the word is suffixed with `ᶠ` and its
      following space is preserved.
- [ ] Given lexical output, when inspected, then it contains no `~` markers and
      no automatic prosodic merging beyond user-provided `+` markers.
- [ ] Given lexical output, when diphthongs and hyphenated subparts are shown,
      then `¨` and `-` are preserved.
- [ ] The lexical-output behavior is covered by built-in `run_tests()`, pytest,
      and integration fixtures.

---

# User Story (optional)
> As a researcher reviewing syllabified Akkadian text, I want a lexical export
> that preserves my manual pre-merge annotations and function-word marking
> without prosodic repairs so that I can inspect lexical structure directly.

---

# Interface Notes
- Input: `<prefix>_syl.txt` as consumed by the prosody stage.
- Output: `<prefix>_lex.txt`.
- Affected components: `src/akkapros/lib/prosody.py`,
  `src/akkapros/cli/prosmaker.py`, `docs/akkapros/prosmaker.md`.

---

# Open Questions
- [ ] Should `_lex.txt` include a minimal header line documenting that it is a
      lexical, non-accentuated export, or should it remain raw content only?

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration: additive output only; no downstream migration required unless
  external tooling wants to consume the new file.

# Related
- Related ADRs: [ADR-001](../adr/001-pipeline-architecture-and-stage-contracts.md)
- Implementation CRs: [CR-018](../cr/018-lex-output.md)

# Non-Goals
- This requirement does not change prosody realization, merge policy, or
  accentuation algorithms.
- This requirement does not replace `_tilde.txt`; it adds a separate lexical
  export.

# Security / Safety Considerations
- Unicode superscripts must be emitted and tested under UTF-8 so the lexical
  file remains portable across supported platforms and editors.