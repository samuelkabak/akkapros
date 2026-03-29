---
cr_id: CR-026
status: Draft
priority: High
impact: Mutative
created: 2026-03-29
updated: 2026-03-29
implements: 'ADR-033, REQ-018'
---

# Change Request: Minimize Path Disclosure in Metrics Artifacts

# Summary

Align `metricalc` and metrics-generated artifacts with the path-disclosure
policy formalized for metrics artifacts in
[ADR-033](../adr/033-minimize-path-disclosure-in-metrics-artifacts.md) and
[REQ-018](../req/018-minimize-path-disclosure-in-metrics-artifacts.md), while
remaining consistent with the earlier logging strategy in
[REQ-016](../req/016-standardized-cli-logging-and-console-options.md) and
[CR-023](023-adopt-logging-actions-for-cli-logging.md). Metrics text and
JSON outputs currently embed absolute filesystem paths that reveal user-specific
directory information and therefore violate the repository's path-minimization
security strategy.

This CR requires metrics artifacts to display only the safe one-parent path
form, such as `...\results\corpus-lob_tilde.txt`, while preserving drive-root
forms such as `C:\corpus-lob_tilde.txt` where no parent reduction is possible.

---

# Motivation

Absolute filesystem paths leak personal and machine-specific information,
including usernames, local directory layout, storage-provider names, and other
environment details. Those paths are especially risky in generated artifacts
that users may share externally, such as metrics reports and JSON outputs.

The repository already adopted a security-oriented path-display strategy in
`REQ-016` and `CR-023`: show only the leaf and at most one parent segment when
possible. Metrics artifacts have not fully followed that strategy, so this CR
closes that gap.

---

# Scope

## Included

- Minimize path disclosure in metrics text/table output.
- Minimize path disclosure in metrics JSON output.
- Apply the same safe-path rule to any metrics run-configuration fields that
  currently embed absolute input paths.
- Audit `metricalc` and directly related metrics artifact generation paths for
  remaining absolute-path disclosure.
- Update regression tests and reference artifacts that assert metrics output.
- Update user-facing and developer-facing documentation where metrics examples
  or path-display behavior are described.

## Not Included

- Rewriting unrelated CLI log messages that already use the shared safe-path
  helper correctly.
- Changing non-metrics output schemas unless they are found to share the same
  metrics artifact serializer or contract.
- Introducing a new path-display policy different from `REQ-016` / `CR-023`.

---

# Current Behavior

The audit for this CR found that the shared logging path minimization helper is
already used in most CLI runtime logs, but metrics artifacts still expose full
paths in at least these locations:

1. Metrics table output header:
   - `METRICS SUMMARY: C:\Users\...\results\corpus-lob_tilde.txt`

2. Metrics table run configuration:
   - `input: C:\Users\...\results\corpus-lob_tilde.txt`

3. Metrics JSON payload:
   - top-level `file` value stores the full absolute path of the analyzed input

The audit did not identify the same problem in the already-migrated logger
calls that use `format_path_for_logging(...)`; the leakage is concentrated in
metrics artifact content rather than logger transport.

---

# Proposed Change

Apply the same safe-path formatting rule used by the shared logger helper to
all path-bearing values embedded in metrics artifacts.

Approved display examples:

- `...\results\corpus-lob_tilde.txt`
- `C:\corpus-lob_tilde.txt`

Disallowed display example:

- `C:\Users\samue\YandexDisk\GED\08 CONLANG\...\results\corpus-lob_tilde.txt`

Affected output locations include at minimum:

- the `METRICS SUMMARY:` line in text/table output
- the `input:` value under `--- RUN CONFIGURATION ---` in text/table output
- the top-level `file` field in metrics JSON output

This CR also requires a focused review of related metrics-generated path values
so no other absolute-path disclosure remains in `metricalc` artifact content.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- any helper used to serialize metrics text or JSON artifacts

Formatting rule:
- use the same path-minimization contract already defined by `REQ-016`
- prefer `...\parent\file.ext` when the path has deeper structure
- preserve drive-root forms such as `C:\file.ext`
- never emit user-home or deep workspace prefixes inside shared metrics
  artifacts when the safe shortened form is available

Audit rule:
- search metrics text serializers, metrics JSON serializers, and metrics test
  fixtures for path-bearing fields
- update all affected path-bearing fields to the safe-path form
- explicitly verify that no other absolute path remains in metrics artifact
  output after the change

Security rationale:
- artifact content is shareable output, not just local runtime logging, so path
  minimization is mandatory rather than cosmetic

---

# Files Likely Affected

`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`docs/akkapros/metricalc.md`
`docs/akkapros/metrics-computation.md`
tests and integration reference artifacts for metrics text and JSON output

---

# Acceptance Criteria

- [ ] Metrics text/table output no longer exposes absolute filesystem paths.
- [ ] The `METRICS SUMMARY:` line uses the safe one-parent path form.
- [ ] The `input:` field under `--- RUN CONFIGURATION ---` uses the safe
      one-parent path form.
- [ ] Metrics JSON output no longer exposes an absolute path in its top-level
      `file` field.
- [ ] Path-bearing values in metrics artifacts follow the same shortening rule
      as `REQ-016`: one parent plus leaf where possible, with drive-root paths
      preserved.
- [ ] Regression tests and integration reference artifacts are updated to match
      the shortened path form.
- [ ] Documentation examples and descriptions for metrics output no longer show
      full user filesystem paths.
- [ ] Review confirms there is no remaining absolute-path disclosure in
      `metricalc` artifact content after the audit.

---

# Risks / Edge Cases

Possible issues:

- Existing snapshots and integration references will change even though the
  underlying metrics computation does not.
- Consumers that incorrectly relied on the previous absolute-path value in the
  JSON `file` field may need migration notice.
- Drive-root and UNC-path cases must still remain readable and deterministic.

---

# Testing Strategy

Unit tests:

- metrics table formatting shortens the summary path correctly
- metrics table formatting shortens run-configuration input paths correctly
- metrics JSON serialization shortens the top-level `file` path correctly
- drive-root and shallow-path cases preserve the approved shortened form

Integration tests:

- end-to-end metrics text fixtures use the safe path form
- end-to-end metrics JSON fixtures use the safe path form
- no metrics artifact fixture contains an absolute user path after regeneration

Manual/spec review:

- inspect representative generated metrics text and JSON files to confirm that
  no username or deep local directory prefix is present

---

# Rollback Plan

Restore the previous metrics artifact path serialization if a downstream
consumer proves dependent on the old absolute-path behavior, and document the
security tradeoff explicitly before any such rollback is accepted.

---

# Related Issues

- Legalized by
  [ADR-033](../adr/033-minimize-path-disclosure-in-metrics-artifacts.md) and
  [REQ-018](../req/018-minimize-path-disclosure-in-metrics-artifacts.md).
- Follows the earlier path-minimization policy in
  [REQ-016](../req/016-standardized-cli-logging-and-console-options.md).
- Closes a metrics-artifact gap left after
  [CR-023](023-adopt-logging-actions-for-cli-logging.md).
- Adjacent to metrics output contract work such as
  [REQ-012](../req/012-metrics-output-structure-and-layout.md),
  [CR-019](019-metrics-deltac-meanc-dual-lines-and-varcoc-unitless.md), and
  [CR-024](024-minimize-frontmatter-and-enable-source-flexible-stage-inputs.md).

---

# Tasks

## Implementation

- [ ] Apply safe-path formatting to metrics text/table serializers.
- [ ] Apply safe-path formatting to metrics JSON serializers.
- [ ] Audit remaining path-bearing metrics artifact fields for leaks.

## Tests

- [ ] Add unit coverage for shortened metrics paths.
- [ ] Update integration reference artifacts for text and JSON metrics outputs.
- [ ] Add or update a regression check that rejects absolute user-path leakage
      in metrics artifacts.

## Documentation

- [ ] Update metrics docs and examples to use shortened safe paths.
- [ ] Document that metrics artifacts follow the shared path-security strategy.

## Review

- [ ] Confirm that no remaining absolute path is emitted in metrics artifact
      content after implementation.

---

# Notes for CR-026

The audit performed while drafting this CR found the main leakage in metrics
artifact content rather than in already-migrated logger calls. This CR is
therefore intentionally scoped as a follow-up hardening pass for `metricalc`
and metrics serialization, not a restart of the broader logging migration.