---
req_id: REQ-014
status: Implemented
priority: Medium
impact: Mutative
created: 2026-03-27
updated: 2026-03-27
---

# Requirement: Remove Metrics CSV Output

# Summary

The system shall stop generating metrics CSV output and shall treat JSON as the
single machine-readable metrics export format. Human-readable metrics table
output remains supported.

This requirement removes an output format that is no longer considered useful,
reduces serializer maintenance, and narrows the metrics-output contract to text
plus JSON.

Legacy `--csv` usage shall pass through a short deprecation phase with a brief
message emitted on standard output, not standard error, before the flag is
removed from the package. No message shall be displayed unless `--csv` is
explicitly used.

---

# Motivation

Metrics CSV output duplicates information already available in JSON while
providing less structure and requiring extra serializer, schema, fixture, and
documentation maintenance. JSON is sufficient for automated processing and is a
better fit for nested metrics sections and future front matter integration.

Removing CSV reduces contract surface area and avoids carrying a low-value
export format forward through future metrics changes.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [x] Given metrics generation, when the tool writes machine-readable output,
      then JSON is the only supported machine-readable metrics format.
- [x] Given metrics generation, when no explicit format flag is provided, then
      the human-readable table output behavior remains unchanged.
- [x] Given prior CSV-related CLI options or code paths, when this requirement
      is implemented, then CSV emission is removed from the public metrics
      contract.
- [x] Given legacy `--csv` usage during the approved transition period, when
      the CLI is invoked, then the command emits a brief deprecation message on
      standard output and does not emit that deprecation notice on standard
      error.
- [x] Given `--csv` is not used, when the CLI is invoked, then no CSV
      abandonment or deprecation remark is displayed.
- [x] Given legacy `--csv` usage during the approved transition period, when
      the CLI is invoked, then the exact message is:
      `--csv option is not anymore supported, the csv file will not be generated.`
- [x] Given the deprecation phase ends, when package internals are reviewed,
      then the `--csv` flag has been removed from documentation as an active
      feature and retained only as a hidden compatibility switch.
- [x] Given metrics documentation, when output formats are described, then CSV
      is no longer documented as a supported metrics output.
- [x] Given package documentation after the removal is complete, when CSV is
      mentioned, then it appears only as a brief abandonment or migration note
      and not as an active feature description.
- [x] Given tests or fixtures that assert metrics CSV behavior, when the change
      is implemented, then they are removed or updated to reflect the new
      contract.
- [x] Given downstream consumers, when migration is documented, then JSON is
      identified as the replacement machine-readable format.
- [x] Given this requirement is implemented, when documentation is updated,
      then both user-facing docs and developer-facing docs stop treating CSV as
      an active output and describe the JSON-only end state.
- [x] Given this requirement is implemented, when tests are updated, then
      built-in `run_tests()` coverage is adjusted where applicable and pytest
      coverage includes both unit-level deprecation behavior and integration
      checks for the remaining text and JSON outputs.

---

# User Story (optional)
> As a researcher or tool author consuming metrics programmatically, I want one
> canonical machine-readable metrics output so that downstream automation can
> rely on JSON without duplicated export formats.

---

# Interface Notes
- Input: `<prefix>_tilde.txt`.
- Output after implementation: `<prefix>_metrics.txt`, `<prefix>_metrics.json`.
- Removed output: `<prefix>_metrics.csv`.
- Affected components: `src/akkapros/lib/metrics.py`,
  `src/akkapros/cli/metricalc.py`, `docs/akkapros/metrics-computation.md`,
  `docs/akkapros/metricalc.md`, tests and integration fixtures covering metrics
  outputs.

---

# Open Questions
- [x] The compatibility phase is limited to a hidden no-op flag that prints the
      approved stdout notice while normal code paths, docs, and fixtures no
      longer treat CSV as an active output.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: small
- Migration: update any downstream scripts that currently read metrics CSV to
      consume metrics JSON instead. During the short transition period, keep only a
      brief stdout deprecation notice for explicit legacy `--csv` usage.

# Related
- Related ADRs: [ADR-010](../adr/010-metrics-from-text-and-dual-percent-v.md),
  [ADR-022](../adr/022-output-format-public-contract-boundaries.md),
  [ADR-030](../adr/030-metrics-csv-abandonment-and-spec-history-policy.md)
- Related REQs: [REQ-004](004-metrics-computation.md),
  [REQ-012](012-metrics-output-structure-and-layout.md)
- Implementation CRs: [CR-021](../cr/021-remove-metrics-csv-output.md)

# Non-Goals
- This requirement does not change the underlying metrics algorithms or numeric
  values.
- This requirement does not remove JSON output or human-readable table output.
- This requirement does not define a new replacement format beyond the existing
  JSON metrics export.
- This requirement does not preserve long-lived compatibility aliases for CSV.

# Security / Safety Considerations
- Removing CSV reduces the number of public output schemas that downstream tools
  must parse and validate.
