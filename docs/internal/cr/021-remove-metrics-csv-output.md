---
cr_id: CR-021
status: Done
priority: Medium
impact: Mutative
created: 2026-03-27
updated: 2026-04-12
implements: REQ-014
---

# Change Request: Remove metrics CSV output

# Summary

Remove metrics CSV output from the public CLI contract and keep JSON as the
only machine-readable metrics export format. Table/text metrics output remains
supported for human inspection.

This change removes a low-value serializer and simplifies future metrics-output
maintenance.

Legacy `--csv` invocations shall pass through only a short deprecation phase,
with the notice printed to standard output rather than standard error. No
remark shall be displayed unless `--csv` is explicitly used.

Historical note:

- [CR-057](057-remove-residual-metrics-csv-code-and-config-surface.md) later
  closes the deprecation window described here and removes the remaining hidden
  compatibility flag, config key, and help-surface residue from the active
  package contract.

---

# Motivation

CSV duplicates information already available in JSON while being less expressive
for grouped metrics structures. Maintaining CSV increases implementation and
test burden for little benefit because JSON is already sufficient for automated
processing.

Removing CSV narrows the public contract and makes future metrics changes less
costly to specify, implement, and validate.

---

# Scope

## Included

- Remove metrics CSV output from the supported public contract.
- Remove CLI support for requesting metrics CSV output after a short
  deprecation phase.
- Remove metrics CSV serializer paths and related fixture/documentation
  expectations.
- Update user and internal documentation to identify JSON as the replacement
  machine-readable format.
- Update tests to stop asserting metrics CSV behavior.
- Reduce CSV references in package docs to a minimal abandonment or migration
  note only.

## Not Included

- Any change to metrics algorithms or numeric values.
- Any change to JSON metrics schema beyond removing CSV references.
- Any change to table/text output beyond documentation updates where needed.

---

# Current Behavior

Metrics currently support three output formats: table/text, JSON, and CSV.
This means every metrics-output contract change must be reflected in three
serializers and corresponding tests and fixtures.

---

# Proposed Change

- Remove `<prefix>_metrics.csv` from the supported metrics outputs.
- Keep `<prefix>_metrics.txt` and `<prefix>_metrics.json`.
- During a short deprecation phase, allow legacy `--csv` usage to emit this
  exact message on standard output only when `--csv` is explicitly used:
  `--csv option is not anymore supported, the csv file will not be generated.`
- After that phase, remove CSV-specific CLI flags, code paths, tests,
  documentation, and fixtures from the package.
- Update migration guidance so downstream automation uses JSON.

---

# Technical Design

Architecture notes:

Components:
- metrics CLI surface in `src/akkapros/cli/metricalc.py`
- metrics serialization logic in `src/akkapros/lib/metrics.py`
- any orchestration flags that expose metrics CSV output

Contract changes:
- public metrics output set becomes text plus JSON only
- CSV is removed from package code, tests, and normal docs after the short
  deprecation phase
- the deprecation notice for legacy `--csv` usage is printed to stdout, not
  stderr
- no CSV deprecation or abandonment remark is shown unless `--csv` is
  explicitly present
- package docs keep at most a slight abandonment or migration note rather than
  ongoing feature documentation

---

# Files Likely Affected

`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/fullprosmaker.py`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/metricalc.md`
tests and integration fixtures covering metrics outputs

---

# Acceptance Criteria

- [x] Metrics no longer emit `<prefix>_metrics.csv`.
- [x] JSON remains the only supported machine-readable metrics output.
- [x] Table/text metrics output remains available.
- [x] During the approved short transition period, legacy `--csv` usage emits a
  brief deprecation notice on stdout and does not emit that notice on
  stderr.
- [x] The deprecation notice is shown only when `--csv` is explicitly used.
- [x] The exact deprecation notice text is:
  `--csv option is not anymore supported, the csv file will not be generated.`
- [x] After the transition period, CSV-related CLI behavior is removed from the
  package surface as an active documented feature; the parser retains only a
  hidden compatibility switch during the deprecation window.
- [x] Documentation no longer describes CSV as a supported metrics output.
- [x] Package docs retain at most a slight abandonment or migration note for
  CSV and otherwise remove CSV feature references.
- [x] Tests and fixtures no longer depend on metrics CSV output.
- [x] Migration guidance points downstream CSV consumers to JSON.
- [x] User-facing documentation is updated to remove CSV as an active feature
  and to describe JSON as the replacement machine-readable format.
- [x] Developer-facing documentation is updated to remove CSV from serializer,
  fixture, and maintenance expectations.
- [x] Built-in `run_tests()` coverage is updated where applicable so no
  self-test expects CSV output.
- [x] Pytest coverage includes unit tests for deprecation behavior and
  integration tests for text and JSON metrics outputs after CSV removal.

---

# Risks / Edge Cases

Possible issues:

- Existing downstream scripts may still depend on CSV and will require
  migration.
- Even a short transition path may surprise users if they miss the stdout
  deprecation notice.
- Full-pipeline wrappers may expose CSV-related flags that need coordinated
  cleanup.

---

# Testing Strategy

Unit tests:

- verify CSV serializer path is removed or unreachable according to the approved
  CLI behavior
- verify the temporary deprecation notice appears on stdout, not stderr, and
  only when `--csv` is explicitly used
- verify the exact notice text matches the approved wording
- verify JSON and table outputs still work as expected

Integration tests:

- refresh metrics fixtures to cover text and JSON only
- verify any temporary legacy `--csv` path follows the approved stdout-only
  deprecation behavior
- verify full-pipeline behavior if it previously exposed metrics CSV flags
- verify pytest integration coverage no longer expects CSV artifacts anywhere

Manual/spec review:

- verify user docs and internal specs consistently remove CSV from the metrics
  output contract
- verify CSV references in package docs are reduced to a slight abandonment or
  migration note only

---

# Rollback Plan

Restore metrics CSV serializer support, CLI flags, documentation, and tests if
CSV output must be reintroduced.

---

# Related Issues

- Legalized by [REQ-014](../req/014-remove-metrics-csv-output.md).
- Architecturally legalized by
  [ADR-030](../adr/030-metrics-csv-abandonment-and-spec-history-policy.md).
- Adjacent to [REQ-012](../req/012-metrics-output-structure-and-layout.md) and
  [CR-019](019-metrics-deltac-meanc-dual-lines-and-varcoc-unitless.md), both of
  which currently discuss CSV as part of the metrics-output contract.
- Related to the broader metrics computation contract in
  [REQ-004](../req/004-metrics-computation.md).

---

# Tasks

## Implementation

- [x] Remove or disable metrics CSV CLI support.
- [x] Implement the short stdout-only deprecation notice for legacy `--csv`
  usage.
- [x] Remove metrics CSV CLI support after the transition period.
- [x] Remove metrics CSV serializer/output paths.
- [x] Update any orchestration flags that expose metrics CSV.

## Tests

- [x] Update built-in `run_tests()` coverage where applicable.
- [x] Remove or update pytest unit tests and fixtures that treat CSV as active.
- [x] Add or refresh pytest integration coverage so JSON and text outputs
  remain correct after CSV removal.

## Documentation

- [x] Update metrics docs to remove CSV output references.
- [x] Update developer-facing docs and maintenance notes to remove CSV from the
  active serializer contract.
- [x] Add migration note directing automation to JSON.
- [x] Keep only a slight abandonment note where CSV is still mentioned.

## Review

- [x] Confirm the exact length of the short deprecation phase.
- [x] Confirm whether any release-note entry is required in addition to the
  minimal abandonment note.

---

# Notes for CR-021

This CR removes a public output format and therefore changes the external
contract for metrics consumers. Migration messaging should be explicit even if
the implementation itself is small. The intended end state is that CSV almost
disappears from the package surface.
