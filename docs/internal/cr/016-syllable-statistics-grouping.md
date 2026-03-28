---
cr_id: CR-016
status: Done
priority: Medium
impact: Mutative
created: 2026-03-26
updated: 2026-03-26
implements: REQ-012
---

# Change Request: Group syllable counts under "Syllable statistics"

# Summary

Group the existing `Syllable types` and `Total syllables` outputs into a single
sub-section called `Syllable statistics` in all human-readable metrics tables
and mirror that grouping in JSON and CSV outputs. Apply the change to both the
`ORIGINAL TEXT` and `ACCENTUATED TEXT` sections.

---

# Motivation

Improve readability and make syllable-related metrics a single, auditable
block for humans and programs. Grouping simplifies downstream parsing, makes
the table easier to scan, and aligns the table layout with a clearer JSON/CSV
schema.

---

# Scope

## Included

- Update human-readable table formatting emitted by `metricalc.py` so the
  table shows a `Syllable statistics` block containing `Syllable types` and
  `Total syllables` in both `ORIGINAL TEXT` and `ACCENTUATED TEXT` sections.
- Update JSON emitter to provide `syllable_statistics.types` and
  `syllable_statistics.count`.
- Update CSV emitter to include syllable statistics rows (see Technical
  Design) and document the schema.
- Add unit and integration tests to validate new layout and machine formats.

## Not Included

- Changing metric computations or counts. This CR only re-organizes output
  presentation and machine-readable schema.

---

# Current Behavior

`Syllable types` and `Total syllables` are printed as separate, adjacent
top-level blocks in the metrics table and emitted as separate top-level JSON
fields/CSV rows. Consumers must locate both sections when auditing syllable
counts.

---

# Proposed Change

- Human table: replace the adjacent blocks with a nested block:

```
Syllable statistics:
  Syllable types:
    CV: ...
    CVC: ...
    ...
  Total syllables: N
```

- JSON: add `syllable_statistics` object with `types` and `count` fields.
- CSV: emit syllable statistics rows grouped under `syllable_statistics` (see
  Technical Design for options).

Example target layout:

```
Syllable statistics:
  Syllable types:
    CV    : 5839 syllables (37.90%)
    CVC   : 3224 syllables (20.93%)
    CVV   : 3274 syllables (21.25%)
    CVVC  :  373 syllables ( 2.42%)
    VC    :  867 syllables ( 5.63%)
    V     : 1574 syllables (10.22%)
    VV    :  201 syllables ( 1.30%)
    VVC   :   54 syllables ( 0.35%)
  Total syllables: 15406 syllables
```

---

# Technical Design

- JSON canonical structure:

```json
"syllable_statistics": {
  "types": { "CV": {"count": 5839, "percent": 37.90}, ... },
  "count": 15406
}
```

- CSV options:
  - Preferred: `section,metric,submetric,value` rows for syllable statistics.
  - Fallback: keep flat rows and add `syllable_statistics.count` row.

---

# Files Likely Affected

`src/akkapros/lib/metrics.py` (emitters), `src/akkapros/cli/metricalc.py`, test
files under `tests/`, and integration reference fixtures under
`tests/integration_refs/`.

---

# Acceptance Criteria

- Text metrics show `Syllable statistics` block in ORIGINAL and ACCENTUATED
  sections.
- JSON contains `syllable_statistics.types` and `syllable_statistics.count`.
- CSV contains syllable statistics per chosen CSV schema.
- Unit tests and integration fixtures updated to assert the new layout.

---

# Risks / Edge Cases

- Existing downstream parsers that rely on the exact textual table layout will
  need adjustment.
- JSON/CSV consumers may need migration if they assume the old top-level field
  layout only.
- Label consistency matters: `Total syllables` must be used uniformly once this
  CR lands.

---

# Testing Strategy

- Update `src/akkapros/lib/metrics.py::run_tests()` with quick checks for the
  new textual block.
- Add pytest tests in `tests/test_metrics_stats.py` to validate JSON and CSV
  outputs.
- Add integration reference files under `tests/integration_refs/`.

---

# Rollback Plan

Revert the formatter and emitter changes and restore the previous table, JSON,
and CSV layouts. Regenerate the integration reference fixtures if rollback is
required after partial implementation.

---

# Related Issues

- This CR refines the output contract defined by `REQ-004` for rhythmic metrics
  computation.
- See also `CR-017` for the companion metrics-layout change affecting word and
  mora statistics.
- `CR-012` is superseded by this CR and should remain unchanged for historical
  traceability.

---

# Tasks

## Implementation

- [ ] Update textual formatter in `metricalc.py`.
- [ ] Update JSON emitter.
- [ ] Update CSV emitter and document option chosen.

## Tests

- [ ] Add unit checks to `run_tests()` for metrics.
- [ ] Add pytest tests for JSON/CSV.
- [ ] Add integration fixtures.

## Documentation

- [ ] Update `docs/akkapros/metrics-computation.md` and `docs/akkapros/metricalc.md`.

## Review

- [ ] Verify output examples match the approved layout in both sections.
- [ ] Confirm JSON and CSV schemas are documented for downstream consumers.

---

# Notes for CR-016

This CR is presentation-only: metric computations stay unchanged, but the
surface output contract changes, so the impact is mutative for consumers of the
formatted outputs.

Supersedence note: this CR supersedes `CR-012`.
