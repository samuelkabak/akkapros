---
req_id: REQ-012
status: Implemented
priority: Medium
impact: Mutative
created: 2026-03-26
updated: 2026-03-29
---

# Requirement: Metrics Output Structure and Layout

# Summary

Historical note: this requirement was drafted when metrics CSV was still part
of the documented metrics contract. The later removal of CSV is defined by
[ADR-030](../adr/030-metrics-csv-abandonment-and-spec-history-policy.md) and
[REQ-014](014-remove-metrics-csv-output.md). Read CSV references here as
historical contract state, not current end-state policy.

The system shall present metrics outputs using a normalized structure across
the human-readable table, JSON, and CSV formats. In particular, syllable-count
reporting shall be grouped under a `Syllable statistics` block, and word/mora
statistics shall use a consistent order and naming convention in both the
`ORIGINAL TEXT` and `ACCENTUATED TEXT` sections.

The metrics display contract shall also normalize unit presentation for
consonant-interval statistics by exposing time (`s`) and mora values on
separate lines for both `ΔC` and `MeanC`, and by rendering `VarcoC` as a
unitless value without a trailing percent sign.

---

# Motivation

The current metrics reports are numerically correct but structurally harder to
audit than necessary. Related fields are split across adjacent sections and the
human-readable ordering does not align closely with the logical grouping needed
for machine-readable outputs.

Formalizing the reporting structure ensures the textual table, JSON, and CSV
stay aligned and gives downstream consumers a documented contract for layout,
labels, and grouped statistics.

---

# Acceptance Criteria

- [ ] Given a metrics report in table format, when syllable counts are shown,
      then `Syllable types` and `Syllable count` appear inside a parent block
      named `Syllable statistics` in both `ORIGINAL TEXT` and `ACCENTUATED TEXT`.
- [ ] Given a metrics report in table format, when word and mora statistics are
      shown, then `Word statistics` appears before `Mora statistics` in both
      report sections.
- [ ] Given a metrics report in table format, when mora-per-syllable statistics
      are shown, then the mean and standard deviation are rendered inline using
      `mean ± stddev` notation.
- [ ] Given a metrics report in table format, when mora-per-word statistics are
      shown, then the field is named `Mean morae per word` and appears in the
      `Mora statistics` block immediately after `Mean morae per syllable`.
- [ ] Given JSON output, when syllable statistics are emitted, then they are
      available under `syllable_statistics.types` and
      `syllable_statistics.count`.
- [ ] Given JSON output, when word and mora statistics are emitted, then they
      are available under `word_statistics` and `mora_statistics` with explicit
      `mean` and `stddev` subfields where applicable.
- [ ] Given CSV output, when grouped metrics are emitted, then syllable, word,
      and mora statistics are represented in a documented schema that preserves
      section/metric identity and numeric values.
- [ ] Given a metrics report in table format, when `ΔC` and `MeanC` are shown,
      then each is rendered as two separate lines in this order for both
      `ORIGINAL TEXT` and `ACCENTUATED TEXT`: seconds first, then mora.
- [ ] Given a metrics report in table format, when consonant-interval values
      are shown, then the labels follow this pattern: `ΔC: <seconds> s`,
      `ΔC_mora: <mora> mora`, `MeanC: <seconds> s`, `MeanC_mora: <mora> mora`.
- [ ] Given a metrics report in table format, when `VarcoC` is shown, then it
      is rendered as a unitless numeric value with no trailing `%`.
- [ ] Given JSON output, when `ΔC` and `MeanC` are emitted, then each section
      (`original`, `accentuated`) contains explicit and separate second-based
      and mora-based fields for these metrics.
- [ ] Given CSV output, when `ΔC` and `MeanC` are emitted, then rows preserve
      separate second-based and mora-based values with clear metric labels for
      both sections.
- [ ] Documentation is updated to reflect the dual-line table format,
      unitless `VarcoC`, and JSON/CSV schema updates.
- [ ] The same grouped structure is covered by built-in `run_tests()`, pytest
      tests, and integration fixtures.

---

# User Story (optional)
> As a researcher comparing original and accentuated Akkadian metrics, I want
> the output formats to group related counts and averages consistently so that I
> can audit them quickly and consume them reliably in downstream tools.

---

# Interface Notes
- Input: `<prefix>_tilde.txt`.
- Output: `<prefix>_metrics.txt`, `<prefix>_metrics.json`, `<prefix>_metrics.csv`.
- Affected components: `src/akkapros/lib/metrics.py`,
      `src/akkapros/cli/metricalc.py`, `docs/akkapros/metrics-computation.md`,
      `docs/akkapros/metricalc.md`.

---

# Open Questions
- [ ] Should the JSON emitter preserve legacy top-level fields for one release
      cycle after the grouped keys are introduced?
- [ ] Should CSV schema versioning be made explicit if grouped rows replace the
      current flat layout?

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration: downstream parsers of text/JSON/CSV metrics may require updates
  once the grouped layout is implemented.

# Related
- Related ADRs: [ADR-010](../adr/010-metrics-from-text-and-dual-percent-v.md)
- Implementation CRs: [CR-016](../cr/016-syllable-statistics-grouping.md),
      [CR-017](../cr/017-word-mora-statistics-reorg.md),
      [CR-019](../cr/019-metrics-deltac-meanc-dual-lines-and-varcoc-unitless.md)

# Non-Goals
- This requirement does not change the underlying metrics algorithms or numeric
  values.
- This requirement does not add new acoustic metrics beyond those already
  defined by `REQ-004`.

# Security / Safety Considerations
- Output-schema changes must be documented clearly because downstream automated
  consumers may fail silently if they rely on previous field names or layout.