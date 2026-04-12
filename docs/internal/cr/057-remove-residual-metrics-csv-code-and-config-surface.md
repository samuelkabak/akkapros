---
cr_id: CR-057
status: Done
priority: High
impact: Mutative
created: 2026-04-12
updated: 2026-04-12
implements: 'REQ-014, REQ-029, CR-021'
---

# Change Request: Remove Residual Metrics CSV Code and Config Surface

## Summary

CR-021 and REQ-014 removed metrics CSV as an active output and allowed only a
short deprecation window for explicit legacy CSV flags. Repository inspection
on 2026-04-12 shows that the deprecation window is still encoded in active
runtime code, configuration schema, help text, demo config, and tests.

This CR closes that remaining compatibility window and removes the leftover
metrics CSV surface completely from active code and configuration. Historical
documentation may continue to mention the abandoned CSV format as history, but
active runtime and config contracts shall no longer expose any metrics CSV
toggle, alias, warning path, or demo setting.

Repository inspection on 2026-04-12 found exactly three YAML config files in
the workspace, and all three still encode the metrics CSV key. This CR
therefore requires removal of the metrics `csv` option from all YAML config
files in the project, not only from the default config.

Because the next planned release is 3.0.0, this CR does not preserve backward
compatibility for residual metrics CSV flags or config keys. Removed CLI flags
shall fail through the normal unsupported-option path once they are deleted.

This CR is a completion and narrowing record for the older CSV-removal work.
For active implementation and verification, treat this CR as narrowing the
older deprecation-window behavior still described in CR-021 and REQ-014 and as
overriding the older `metrics.run.csv` config-key expectation in REQ-029.

---

## Motivation

The repository still contains active metrics CSV compatibility paths even
though the approved end state is JSON-only machine-readable metrics output.
Those leftovers increase maintenance cost, confuse users reviewing default
config and demo files, and keep tests and help text tied to a feature that is
supposed to be gone.

The problem is no longer whether metrics CSV is generated. It is that the
package still advertises and carries CSV-shaped runtime and config surface area
that should have disappeared after the approved deprecation window ended.

---

## Scope

## Included

- Remove the active metrics CSV key from runtime config schema and emitted
  default config.
- Remove hidden CLI compatibility flags for metrics CSV from `metricalc` and
  `fullprosmaker`.
- Remove metrics CSV deprecation-warning code paths, constants, and help-text
  entries.
- Remove metrics CSV toggles from demo YAML files and any other active config
  examples.
- Remove the metrics `csv` option from every YAML config file in the project.
- Remove or rewrite tests that still assert the legacy metrics CSV warning
  behavior.
- Update directly relevant internal specs that still treat `metrics.run.csv` or
  `--metrics-csv` as active config or CLI surface.

## Not Included

- Non-metrics CSV facilities elsewhere in the repository, such as phoneprep TSV
  or CSV handling.
- Historical records that mention CSV as part of earlier design history,
  provided they are explicitly historical and not active contract text.
- Any change to metrics algorithms, JSON schema, or text metrics values.

---

## Current Behavior

Repository inspection on 2026-04-12 found these active residual metrics CSV
surfaces:

- `src/akkapros/config/default.yaml` still emits `metrics.run.csv: false` with
  a live comment saying `Emit deprecated CSV output.`
- `src/akkapros/lib/config.py` still defines schema and CLI/config mapping for
  `metrics.run.csv`, `metricalc --csv`, and `fullprosmaker --metrics-csv`.
- `src/akkapros/lib/helpmsg.py` still publishes active help strings for
  `metrics.run.csv`, `metricalc.csv`, `fullprosmaker.metrics_csv`, and
  `metrics.csv`.
- `src/akkapros/cli/metricalc.py` still accepts hidden `--csv`, excludes it in
  runtime-option export, and emits a deprecation warning when used.
- `src/akkapros/cli/fullprosmaker.py` still accepts hidden `--metrics-csv`,
  threads `output_csv` through the pipeline call surface, and emits the same
  deprecation warning path.
- `src/akkapros/lib/metrics.py` still defines
  `METRICS_CSV_DEPRECATION_MESSAGE`, and built-in self-test naming still refers
  to CSV removal.
- `demo/akkapros/lexlinks/construct-demo.yaml` and
  `demo/akkapros/prosmaker/corpus-demo.yaml` still encode `metrics.run.csv:
  false`.
- A workspace-wide YAML search found only these three YAML config files:
  `src/akkapros/config/default.yaml`,
  `demo/akkapros/lexlinks/construct-demo.yaml`, and
  `demo/akkapros/prosmaker/corpus-demo.yaml`; all three currently include the
  metrics CSV key.
- `tests/test_integration.py` and `tests/test_cli_logging.py` still verify the
  deprecated warning behavior for explicit CSV flags.
- `docs/internal/req/029-stage-config-run-process-separation-and-common-outdir-removal.md`
  still says `metrics.run` contains exactly `csv`, `table`, and `json`, which
  conflicts with the approved CSV end state.

These are active code/config surfaces, not just historical notes.

---

## Proposed Change

- Remove `metrics.run.csv` from the active metrics config surface.
- Remove hidden `--csv` and `--metrics-csv` compatibility flags from runtime
  CLI parsers.
- Remove `METRICS_CSV_DEPRECATION_MESSAGE` and any runtime path that logs or
  checks deprecated metrics CSV behavior.
- Remove metrics CSV help-string registry entries and config aliases.
- Remove `metrics.run.csv: false` from default and demo config files.
- Remove `metrics.run.csv: false` from all YAML config files in the project.
- Replace legacy CSV-warning tests with tests that assert the flags are absent
  from the active CLI contract or rejected clearly, according to the chosen CLI
  failure policy.
- Update active internal config/spec records so `metrics.run` is defined only in
  terms of `table` and `json`.

Historical notes about abandoned metrics CSV may remain where needed, but they
must not appear as active runtime or config contract.

---

## Technical Design

Architecture notes:

Components:

- metrics config schema in `src/akkapros/lib/config.py`
- default runtime config in `src/akkapros/config/default.yaml`
- all YAML config files in the repository, currently the three verified files
  under `src/akkapros/config/` and `demo/akkapros/`
- config/help registry in `src/akkapros/lib/helpmsg.py`
- metrics CLI in `src/akkapros/cli/metricalc.py`
- orchestration CLI in `src/akkapros/cli/fullprosmaker.py`
- metrics library constants or helper names in `src/akkapros/lib/metrics.py`
- demo YAML files under `demo/akkapros/**`
- pytest coverage that still encodes deprecated CSV behavior

Active contract after implementation:

- `metrics.run` exposes only `table` and `json`
- `metricalc` exposes no metrics CSV flag, hidden or public
- `fullprosmaker` exposes no metrics CSV flag, hidden or public
- no default or demo config file contains a metrics CSV key
- no YAML config file in the project contains a metrics CSV key
- no runtime warning path exists for deprecated metrics CSV because the
  compatibility window is over

Spec alignment required:

- Narrow the older transition semantics in CR-021 and REQ-014 by treating the
  deprecation window as finished.
- Override the older exact-key wording in REQ-029 so active grouped metrics
  config no longer includes `csv`.
- Keep older accepted records intact as history, but add forward-reference or
  supersession guidance where needed in the newer implementing work.

---

## Files Likely Affected

`src/akkapros/config/default.yaml`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/fullprosmaker.py`
`demo/akkapros/lexlinks/construct-demo.yaml`
`demo/akkapros/prosmaker/corpus-demo.yaml`
`src/akkapros/config/default.yaml`
`tests/test_integration.py`
`tests/test_cli_logging.py`
`docs/internal/req/029-stage-config-run-process-separation-and-common-outdir-removal.md`

---

## Acceptance Criteria

- [x] Given the active emitted default config, when `metrics.run` is inspected,
      then it contains only `table` and `json`.
- [x] Given active config schema and alias resolution, when metrics runtime
      keys are enumerated, then `metrics.run.csv` is absent.
- [x] Given `metricalc` runtime parsing, when CLI options are inspected and
      exercised, then no `--csv` compatibility flag remains.
- [x] Given `fullprosmaker` runtime parsing, when CLI options are inspected and
      exercised, then no `--metrics-csv` compatibility flag remains.
- [x] Given metrics runtime code paths, when repository code is searched, then
      no active metrics CSV deprecation constant or warning path remains.
- [x] Given config/help registry text, when metrics-related help entries are
      inspected, then no active metrics CSV help keys remain.
- [x] Given demo YAML files, when metrics output blocks are inspected, then no
      metrics CSV key remains.
- [x] Given all YAML config files in the project, when repository search is
  run for the metrics `csv` key, then no YAML config file still contains
  that option.
- [x] Given pytest coverage after the change, when integration and logging
      tests are inspected, then they no longer encode deprecated metrics CSV
      warning behavior as the approved contract.
- [x] Given directly relevant active internal specs, when grouped metrics config
      is described, then `metrics.run.csv` is no longer listed as an active
      approved key.
- [x] Given repository search after implementation, when residual metrics CSV
      code/config surfaces are checked, then only historical documentation or
      clearly non-metrics CSV facilities remain.

---

## Risks / Edge Cases

- Some external users may still rely on the hidden compatibility flags. Removing
  them is intentionally a breaking change, but 3.0.0 is the correct boundary
  for removing the residual compatibility surface.
- Older internal documents still contain historical CSV wording. Implementers
  must distinguish active code/config contract from preserved historical
  records.
- Search-based verification must not accidentally remove unrelated CSV usage,
  especially in non-metrics modules such as phoneprep.

---

## Testing Strategy

Unit tests:

- verify config schema/export no longer contains `metrics.run.csv`
- verify metrics help registry no longer exposes CSV keys
- verify parser/help behavior no longer accepts removed CSV flags and falls back
  to normal unsupported-option failure

Integration tests:

- verify `metricalc` and `fullprosmaker` still produce table/text and JSON
  outputs correctly without any CSV compatibility path
- remove legacy warning-path assertions and replace them with assertions for the
  post-window contract

Repository verification:

- run targeted repository searches for `metrics.run.csv`, `--csv`,
  `--metrics-csv`, `metrics_csv`, and
  `METRICS_CSV_DEPRECATION_MESSAGE`
- confirm remaining CSV references are either historical docs or unrelated
  non-metrics CSV usage

---

## Rollback Plan

If removal of the leftover compatibility surface breaks a required downstream
workflow, reintroduce a temporary compatibility path only through a new higher-
numbered record that explicitly reopens the deprecation window and defines its
end date.

---

## Related Issues

- [CR-021](021-remove-metrics-csv-output.md)
- [REQ-014](../req/014-remove-metrics-csv-output.md)
- [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md)
- [ADR-030](../adr/030-metrics-csv-abandonment-and-spec-history-policy.md)

---

## Tasks

## Analysis

- [x] Confirm all active code/config surfaces that still expose metrics CSV
- [x] Separate historical CSV references from active runtime/config leftovers

## Implementation

- [x] Remove metrics CSV keys from config schema, aliases, and emitted defaults
- [x] Remove hidden metrics CSV CLI flags and compatibility code paths
- [x] Remove metrics CSV help-text entries and YAML-config toggles across the
  whole project

## Tests

- [x] Replace legacy warning-path tests with post-removal contract tests
- [x] Verify no metrics CSV artifact or compatibility path remains

## Documentation

- [x] Update active internal spec text that still treats `metrics.run.csv` as
      part of the approved config surface

## Review

- [x] Re-run internal indexes after the CR is finalized
- [x] Verify repository search leaves only historical or non-metrics CSV
      references

---

## Implementation Blockers

None currently.

---

## Notes

This CR is intentionally narrow. It is not a second broad CSV-removal project.
It exists to finish the specific residual metrics CSV runtime and config surface
that remained after CR-021 was marked done.
