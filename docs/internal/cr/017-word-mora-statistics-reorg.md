# Change Request: Reorder Word/Mora statistics and inline mean ± stddev notation

CR-ID: CR-017
Status: Draft
Priority: Medium
Impact: Mutative
Created: 2026-03-26
Updated: 2026-03-26
Implements: REQ-012
---

# Summary

Reorder the human-readable metrics table so `Word statistics` appears before
`Mora statistics`. Move `Morae per word` into the `Mora statistics` block,
rename it `Mean morae per word`, and show `Mean morae per syllable` as a
single inline mean ± stddev line (e.g., `1.547 ± 0.551 mora/syllable`).
Apply to both `ORIGINAL TEXT` and `ACCENTUATED TEXT` outputs and mirror the
change in JSON and CSV emitters.

---

# Motivation

Place all mora-related metrics together for semantic clarity and easier
auditing. Inline ± notation reduces verbosity and matches existing per-word
formatting conventions. The reordering also makes the textual table read from
word-level counts to mora-level aggregates in a more natural sequence.

---

# Scope

## Included

- Restructure textual table layout and labels.
- Move numeric field `Morae per word` to `Mora statistics` and rename.
- Emit JSON keys `word_statistics` and `mora_statistics` with mean/stddev
  fields.
- Update CSV schema to include mean and stddev columns for mora/word metrics.
- Add unit and integration tests.

## Not Included

- Any change to metric computation logic or numerical values.

---

# Current Behavior

`Morae per word` is currently printed in the `Word statistics` block and
`Std dev morae per syllable` is printed as a separate line. JSON/CSV do not
fully reflect the requested grouped `mora_statistics` presentation labels.

---

# Proposed Change

- Textual table: new ordering and inline ± formatting.
- JSON: provide structured objects:

```json
"word_statistics": { "total_words": 4916, "syllables_per_word": {"mean": 3.134, "stddev": 1.231} },
"mora_statistics": { "mean_morae_per_syllable": {"mean":1.547,"stddev":0.551}, "mean_morae_per_word": {"mean":4.847,"stddev":1.676}, "total_morae":23826 }
```

- CSV: add rows with `section,metric,mean,stddev,unit` or equivalent.

Example target layout:

```
Word statistics:
  Total words: 4916 words
  Syllables per word: 3.134 ± 1.231 syllable/word

Mora statistics:
  Mean morae per syllable: 1.547 ± 0.551 mora/syllable
  Mean morae per word: 4.847 ± 1.676 mora/word
  Total morae: 23826 mora
```

---

# Technical Design

- Update textual formatter in `src/akkapros/lib/metrics.py` to change the
  printed ordering and formatting.
- Add JSON structure keys and ensure migration compatibility (emit old
  top-level keys for one release if present).
- Update CSV writer and document chosen schema.

---

# Files Likely Affected

`src/akkapros/lib/metrics.py`, `src/akkapros/cli/metricalc.py`, `tests/test_metrics_stats.py`,
integration fixtures under `tests/integration_refs/`.

---

# Acceptance Criteria

- `Word statistics` appears before `Mora statistics` in both ORIGINAL and
  ACCENTUATED sections.
- `Mean morae per word` appears under `Mora statistics` with unchanged value.
- `Mean morae per syllable` shows mean ± stddev inline in one line.
- Label is `Total morae` (not `Total morae number`) in both sections.
- JSON and CSV outputs expose the reorganized metrics and pass tests.

---

# Risks / Edge Cases

- Existing scripts that scrape text output by section order may break until
  updated.
- CSV header/row changes must be documented so downstream imports stay
  deterministic.
- JSON compatibility may require a short migration period if old keys are still
  consumed externally.

---

# Testing Strategy

- Add quick checks to `src/akkapros/lib/metrics.py::run_tests()` for textual
  layout.
- Add pytest tests in `tests/test_metrics_stats.py` for JSON/CSV shape and
  numeric consistency.
- Update integration fixtures and run the stage-pipeline/fullprosmaker
  integration tests.

---

# Rollback Plan

Restore the previous section order and field names in the emitters, then
regenerate reference fixtures. Rollback does not require recomputation changes,
only formatter reversal.

---

# Related Issues

- This CR is the companion to `CR-016`; both are legalized by `REQ-012`.
- The underlying metrics calculations remain governed by `REQ-004`.

---

# Tasks

## Implementation

- [ ] Update textual formatter.
- [ ] Update JSON emitter.
- [ ] Update CSV emitter.

## Tests

- [ ] Add `run_tests()` checks.
- [ ] Add pytest tests.
- [ ] Update integration references.

## Documentation

- [ ] Update docs `docs/akkapros/metrics-computation.md`.

## Review

- [ ] Verify ordering and labels in both ORIGINAL and ACCENTUATED sections,
      including `Total morae` naming and inline ± format.
- [ ] Verify migration notes for JSON/CSV consumers.

---

# Notes for CR-017

This is a presentation-level change that groups related statistics; reviewers
should check integration fixtures and downstream consumers for compatibility.
