# Change Request: Normalize ΔC/MeanC dual-line units and unitless VarcoC in metrics outputs

CR-ID: CR-019
Status: Done
Priority: Medium
Impact: Mutative
Created: 2026-03-26
Updated: 2026-03-27
Implements: REQ-012
---

# Summary

Modify metrics output formatting for both `ORIGINAL TEXT` and `ACCENTUATED TEXT`
so `ΔC` and `MeanC` are rendered on separate unit lines with seconds first and
mora second. Also remove the trailing percent sign from `VarcoC` so it is shown
as a unitless numeric value. Apply the same contract to table, JSON, and CSV
emitters and update related documentation.

---

# Motivation

Current textual formatting combines mora and second values into one line, which
is harder to parse and less consistent with machine-readable outputs. The
trailing `%` on `VarcoC` implies a unitized display contract that is not desired
for current reporting.

This CR aligns human-readable and machine-readable outputs and defines an
explicit, auditable format across all metrics sinks.

---

# Scope

## Included

- Update table/text rendering in both `ORIGINAL TEXT` and `ACCENTUATED TEXT`:
  - `ΔC: <seconds> s`
  - `ΔC_mora: <mora> mora`
  - `MeanC: <seconds> s`
  - `MeanC_mora: <mora> mora`
- Remove trailing `%` from `VarcoC` display (`VarcoC: <value>`).
- Update JSON output to include separate second-based and mora-based fields for
  `ΔC` and `MeanC` in both sections.
- Update CSV output so second-based and mora-based values are separate and
  clearly labeled for both sections.
- Update metrics documentation to reflect the revised table, JSON, and CSV
  contracts.
- Add or update tests so all affected output contracts are validated.

## Not Included

- Any change to underlying metrics algorithms or numeric computation formulas.
- Any change to unrelated metrics fields outside this formatting/schema update.

---

# Current Behavior

Text output currently prints `ΔC` and `MeanC` as single lines combining mora and
seconds, for example:

`ΔC: 0.6919 mora (0.0337 s) (consonant-interval SD)`

`MeanC: 1.0012 mora (0.0488 s) (mean consonant interval)`

`VarcoC` is currently printed with a trailing percent sign.

---

# Proposed Change

For both `ORIGINAL TEXT` and `ACCENTUATED TEXT`, replace the current style with:

`ΔC: 0.0337 s`

`ΔC_mora: 0.6919 mora`

`MeanC: 0.0488 s`

`MeanC_mora: 1.0012 mora`

And render:

`VarcoC: 69.10`

instead of:

`VarcoC: 69.10 %`

JSON/CSV emitters must represent `ΔC` and `MeanC` as separate second and mora
values for each section, with stable labels suitable for downstream parsing.

---

# Technical Design

- Update metrics formatter contract in the metrics table printer path.
- Update JSON emitter schema to carry distinct fields for
  second-based and mora-based `ΔC`/`MeanC` in each section.
- Update CSV writer schema/rows to preserve the same separation and labeling.
- Ensure all changes remain presentation/schema-level only; computation code
  must keep existing formulas and numeric values.

---

# Files Likely Affected

`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/metricalc.md`
`tests/test_metrics_stats.py`
`tests/test_selftests_lib.py`
`tests/integration_refs/**`

---

# Acceptance Criteria

- [x] In `ORIGINAL TEXT`, `ΔC` and `MeanC` are each rendered as two lines with
      seconds first and mora second.
- [x] In `ACCENTUATED TEXT`, `ΔC` and `MeanC` are each rendered as two lines
      with seconds first and mora second.
- [x] `VarcoC` is rendered without `%` in both sections.
- [x] JSON output contains separate second-based and mora-based values for
      `ΔC` and `MeanC` in both sections.
- [x] CSV output contains separate second-based and mora-based entries for
      `ΔC` and `MeanC` in both sections.
- [x] Documentation is updated for text, JSON, and CSV output contracts.
- [x] Tests pass for updated output contracts (self-tests, pytest, and any
      affected integration references).

---

# Risks / Edge Cases

- Downstream tools scraping exact text lines may break due to renamed labels
  (`ΔC_mora`, `MeanC_mora`) and line splitting.
- JSON and CSV consumers may require migration updates for changed keys/rows.
- Unicode handling for `Δ` labels must remain stable across platforms.

---

# Testing Strategy

- Add/update metrics self-tests for the dual-line table representation and
  unitless `VarcoC`.
- Add/update pytest assertions for JSON and CSV schema/value contracts.
- Update integration fixtures where output snapshots are expected.

---

# Rollback Plan

Revert formatter/schema changes for `ΔC`, `MeanC`, and `VarcoC` presentation,
then restore prior test fixtures and documentation text.

---

# Related Issues

- Legalized by `REQ-012`.
- Follows prior metrics-structure CRs (`CR-016`, `CR-017`).

---

# Tasks

## Implementation

- [x] Update text formatter lines for `ΔC` and `MeanC`.
- [x] Remove `%` suffix from `VarcoC` display.
- [x] Update JSON schema fields for second/mora separation.
- [x] Update CSV schema rows/labels for second/mora separation.

## Tests

- [x] Update self-tests for metrics formatting.
- [x] Update pytest coverage for JSON/CSV contracts.
- [x] Refresh integration references where expected outputs changed.

## Documentation

- [x] Update `docs/akkapros/metrics-computation.md`.
- [x] Update `docs/akkapros/metricalc.md`.

## Review

- [x] Verify both sections (`ORIGINAL`, `ACCENTUATED`) follow the same format.
- [x] Verify no metric computations changed, only representation/schema.

---

# Notes for CR-019

This CR is intentionally mutative because it changes output contracts consumed
by readers and tooling. Coordinate release notes and downstream migration notes
with implementation.
