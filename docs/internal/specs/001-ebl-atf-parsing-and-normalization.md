# Requirement: eBL ATF Parsing and Normalization

REQ-ID: REQ-001
Status: Implemented
Priority: High
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall accept eBL ATF-formatted Akkadian texts and convert them to clean,
phonetically usable text suitable for downstream syllabification and prosody realization.
The parser must strip editorial markup while preserving linguistically meaningful content,
line structure, and morpheme boundary markers.

---

# Motivation

eBL ATF files mix linguistic content with extensive editorial apparatus (restorations,
cuneiform sign indices, uncertainty markers, transliteration metadata). Processing
these files with prosodic analysis tools requires a stable, transparent normalization
step that keeps pronunciation-relevant material and removes noise. Without this step,
every downstream module would need its own ad-hoc cleanup, leading to fragile and
inconsistent behaviour.

The research corpus (Enūma Eliš, Erra and Išum, Marduk's Address to the Demons)
is delivered in eBL ATF format; automated normalization is therefore the entry gate
to the whole analysis pipeline.

---

# Acceptance Criteria

- [ ] Given an eBL ATF file, when parsed, then `%n` Akkadian lines are extracted and
      written to `<prefix>_proc.txt`.
- [ ] Given `( )`, `[ ]`, `< >` delimiters in the input, when parsed, then delimiters
      are removed but enclosed content is kept.
- [ ] Given `{ }` braces (Sumerian or glosses), when parsed, then the entire `{ }` span
      is removed including its content.
- [ ] Given `|` (single pipe) in a line, when parsed, then it is converted to a space.
- [ ] Given `||`, `‡`, `—`, `–` in a line, when parsed, then they are normalised to `:`.
- [ ] Given `x` broken-sign markers, when parsed, then they are collapsed to `…`.
- [ ] Given uncertainty markers `? ! * °`, when parsed, then they are removed.
- [ ] Given `#tr.en:` lines, when parsed, then they are written to `<prefix>_trans.txt`
      and do not appear in the cleaned text.
- [ ] Given metadata/archive lines (e.g. `HuzNA1 i 1.`), when parsed, then they are
      ignored completely.
- [ ] Given original `%n` lines with markup preserved, `<prefix>_orig.txt` is written.
- [ ] Line breaks from the ATF source are preserved in `_proc.txt` (each ATF line maps
      to one output line); multi-line verse structure is not collapsed.
- [ ] When `--append` is used and an output file already exists, new content is appended
      after a clean newline; no partial-line appends occur.
- [ ] When `--preserve-h` is NOT used, `h` in the input is mapped to `ḫ` and `H` to `Ḫ`.
- [ ] When `--strict` is set, unexpected markup patterns trigger a warning.
- [ ] `--test` runs built-in self-tests and exits with code 0 on pass, 1 on failure.
- [ ] All output files are UTF-8 encoded; Unicode Akkadian characters are never
      stripped, normalised, or replaced by ASCII equivalents.

---

# User Story (optional)
> As an Assyriologist, I want to feed a raw eBL ATF file into the toolkit and receive
> clean Akkadian transcription lines so that I can proceed to syllabification without
> manually removing editorial markup.

---

# Interface Notes
- Input: eBL ATF file (`.atf`), UTF-8.
- Outputs: `<prefix>_orig.txt`, `<prefix>_proc.txt`, `<prefix>_trans.txt`.
- Affected components: `src/akkapros/cli/atfparser.py`, `src/akkapros/lib/atfparse.py`.
- CLI invocation: `python src/akkapros/cli/atfparser.py <file.atf> -p <prefix> --outdir <dir>`.

---

# Open Questions
- [ ] Should `h` normalisation be reversed by a future flag for non-Akkadian passages?
- [ ] Should cuneiform sign `x` become `…` always, or should a configurable placeholder
      be supported?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature)
- Migration: normalization rule table is in `docs/akkapros/atfparser.md`; downstream
  consumers must be updated if any rule changes.

# Related
- Related ADRs: [ADR-005](../adr/005-ebl-atf-normalization-policy.md)
- Implementation CRs: none currently open

# Non-Goals
- This requirement does NOT address full scholarly ATF re-serialisation; the parser
  is one-directional (ATF → clean text, not ATF → ATF).
- Does NOT validate orthographic conventions or historical periods of the source text.
- Does NOT perform syllabification or prosody realisation (handled by REQ-002 and REQ-003).

# Security / Safety Considerations
- Input files may contain arbitrary Unicode. The parser must not execute any embedded
  content. File paths are sanitised via `simple_safe_filename()` before use.
- Output directory is created if absent; no world-writable directories should be used.
