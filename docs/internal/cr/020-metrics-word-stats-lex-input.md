# Change Request: Add lexical-aware word indicators to metrics outputs and optional `--lex-input`

CR-ID: CR-020
Status: Draft
Priority: High
Impact: Mutative
Created: 2026-03-26
Updated: 2026-03-26
Implements: REQ-012
---

# Summary

Add three new word-level indicators to metrics outputs in all formats (table, JSON,
CSV) and in both `ORIGINAL` and `ACCENTUATED` sections under `Word statistics`:

- `Function words: <number> words`
- `User marked construct nouns: <number> words`
- `Prominence candidates: <Total words - Function words - construct nouns> words`

Introduce a new CLI option `--lex-input` for metrics/metrical processing so counts
can be derived from `<prefix>_lex.txt` when available and validated against the
corresponding `<prefix>_tilde.txt` input.

---

# Motivation

Current metrics word statistics do not distinguish function words and user-marked
construct nouns, which limits interpretability of prominence-oriented analyses.
Researchers need explicit, reproducible counts in all output formats and both
analysis sections (`ORIGINAL` and `ACCENTUATED`) to compare lexical eligibility
for prominence across corpora and runs.

---

# Scope

## Included

- Add the 3 new fields to `Word statistics` in:
  - human-readable table/text output,
  - JSON output,
  - CSV output.
- Populate these fields for both `ORIGINAL` and `ACCENTUATED` sections.
- Add `--lex-input` CLI option to metrics/metrical entrypoint(s) that consume
  `_tilde.txt`.
- `--lex-input` behavior:
  - If input is `<prefix>_tilde.txt`, resolve `<prefix>_lex.txt`.
  - Validate lexical file linkage before use.
- Fallback behavior when lexical input is unavailable.
- Add unit tests (`run_tests`) and pytest regression tests for all new numeric
  outputs and fallback logic.
- Update user documentation for new metrics fields and CLI option.

## Not Included

- Changes to prosody realization algorithm itself.
- Adding `--lex-input` to `fullprosmaker`.
- Backfilling historical output fixtures unrelated to metrics word-stat fields.

---

# Current Behavior

- Word statistics do not include explicit counts for:
  - function words,
  - user-marked construct nouns,
  - prominence candidates.
- Metrics processing does not consume `_lex.txt` as an optional lexical signal
  source for these counters.

---

# Proposed Change

1. Extend `Word statistics` in both `ORIGINAL` and `ACCENTUATED` with:
   - `Function words`
   - `User marked construct nouns`
   - `Prominence candidates`

2. Counting logic:
   - `Prominence candidates = Total words - Function words - User marked construct nouns`.
   - If lexical input is available and validated:
     - count words marked by superscript `ᶜ` as `User marked construct nouns`.
     - count words marked by superscript `ᶠ` as `Function words`.
   - If lexical input is not available:
     - `User marked construct nouns = 0`.
     - `Function words` computed from `_tilde.txt` using existing function-word
       inventory logic.

3. New CLI option:
   - `--lex-input` (metrics/metrical tool only; not `fullprosmaker`).
   - When `--lex-input` is set and input file is `<prefix>_tilde.txt`, the tool
     must look for `<prefix>_lex.txt`.
   - The tool must verify that `_lex` is related to `_tilde` before using it:
     - same number of lines,
     - strong similarity on up to first 10 lines.

4. Validation failure behavior:
   - If `_lex` is missing or fails relation checks, the tool must emit a clear,
     actionable error when `--lex-input` is explicitly requested.
   - If `--lex-input` is not used, proceed with fallback counters.

---

# Technical Design

## Data Sources

- Primary pipeline input remains `<prefix>_tilde.txt`.
- Optional lexical companion source: `<prefix>_lex.txt`.

## Relation Check (tilde vs lex)

- Required checks when lexical input is enabled:
  - Exact line-count match between `_tilde` and `_lex`.
  - Similarity check across first `min(10, total_lines)` lines after lightweight
    normalization (trim spaces; remove superscripts/word-boundary ornaments that
    differ by design).

## Similarity Rule (proposed)

- Define per-line token similarity with a deterministic threshold suitable for
  regression testing.
- Suggested baseline: token overlap ratio >= 0.80 for each checked line.
- If threshold is not met, lexical file is treated as unrelated.

## Output Mapping

- Table/text: append three lines under `Word statistics` for both sections.
- JSON: add explicit numeric keys in `original.word_statistics` and
  `accentuated.word_statistics`.
- CSV: add explicit columns for both sections using stable column naming
  convention consistent with existing metrics export.

## CLI Surface

- Add `--lex-input` to metrics/metrical CLI parser.
- `fullprosmaker`: no `--lex-input` option is added.

---

# Files Likely Affected

- Metrics/metrical CLI module(s) under `src/akkapros/cli/`.
- Metrics computation library module(s) under `src/akkapros/lib/`.
- Tests:
  - `run_tests()` in relevant metrics module(s),
  - pytest suites under `tests/` (unit + regression/integration fixtures).
- Documentation:
  - `docs/akkapros/metricalc.md`,
  - `docs/akkapros/metrics-computation.md`,
  - any CLI option reference pages that list metrics flags.

---

# Acceptance Criteria

- [ ] Table/text output includes all three new `Word statistics` fields in both
      `ORIGINAL` and `ACCENTUATED`.
- [ ] JSON output includes all three new fields for both sections.
- [ ] CSV output includes all three new fields for both sections.
- [ ] `Prominence candidates` equals `Total words - Function words - User marked construct nouns`.
- [ ] With valid lexical input, `ᶜ` and `ᶠ` markers drive construct/function counts.
- [ ] Without lexical input (or no `_lex.txt` found when not requested),
      construct count is `0` and function-word count is computed from `_tilde`.
- [ ] `--lex-input` performs `_lex` discovery and relation validation for
      `<prefix>_tilde.txt` inputs.
- [ ] Explicit `--lex-input` with missing/unrelated `_lex` fails with clear error.
- [ ] Unit tests (`run_tests`) cover normal, fallback, and failure paths.
- [ ] Pytest regression tests verify exact numeric outputs in table/JSON/CSV.
- [ ] Documentation updated for fields, formulas, and `--lex-input` behavior.

---

# Risks / Edge Cases

- Unicode handling for superscripts `ᶜ` and `ᶠ` across platforms and encodings.
- Ambiguous lexical similarity threshold could yield false acceptance/rejection.
- Potential mismatch between lexical tokenization and metrics tokenization rules.
- Backward compatibility risk for CSV consumers if column order or names change.

---

# Testing Strategy

Unit tests (`run_tests`):

- Count extraction from lexical lines with `ᶜ` and `ᶠ` markers.
- Fallback counters when lexical source is absent.
- `Prominence candidates` formula correctness.
- `_lex` relation checks:
  - matching line counts + passing similarity,
  - line-count mismatch,
  - low-similarity mismatch.

Pytest regression tests:

- Golden outputs for table/JSON/CSV containing new fields in both sections.
- Cases with:
  - valid `_lex` companion,
  - no `_lex` companion,
  - explicit `--lex-input` + invalid companion (expected error).

---

# Rollback Plan

- Remove `--lex-input` option.
- Remove lexical-aware counters and revert to previous word-stat schema.
- Revert docs and fixtures for the new fields.

---

# Related Issues

- Depends on lexical output convention introduced by [docs/internal/cr/018-lex-output.md](../cr/018-lex-output.md).
- Complements existing metrics-output CRs, including
  [docs/internal/cr/017-word-mora-statistics-reorg.md](../cr/017-word-mora-statistics-reorg.md)
  and
  [docs/internal/cr/019-metrics-deltac-meanc-dual-lines-and-varcoc-unitless.md](../cr/019-metrics-deltac-meanc-dual-lines-and-varcoc-unitless.md).
- `CR-012` is superseded by this CR for metrics word-stat output conventions
  and should remain unchanged for historical traceability.

---

# Tasks

## Implementation

- [ ] Add lexical-aware counters to metrics internals.
- [ ] Add `--lex-input` parsing and companion-file validation.
- [ ] Extend output serializers (table/JSON/CSV) for both sections.

## Tests

- [ ] Add/update `run_tests` coverage.
- [ ] Add pytest regression fixtures and assertions.

## Documentation

- [ ] Update metrics and CLI docs with field definitions and fallback rules.
- [ ] Add examples with and without lexical input.

## Review

- [ ] Verify formulas and section parity (`ORIGINAL` vs `ACCENTUATED`).
- [ ] Verify no behavior drift in existing metrics beyond added fields.

---

# Notes for CR-020

This CR defines specification-level behavior only. Implementation sequencing,
exact threshold tuning for similarity, and final error-message wording are
deferred to implementation and review.

JSON key convention: use lowercase section keys (`original`, `accentuated`).
Text-table headings remain uppercase (`ORIGINAL`, `ACCENTUATED`).
