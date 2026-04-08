---
req_id: REQ-018
status: Implemented
priority: High
impact: Mutative
created: 2026-03-29
updated: 2026-04-05
related_adrs: 'ADR-033, ADR-028, ADR-029, ADR-031'
implemented_by: 'CR-026'
---

# Requirement: Minimize Path Disclosure in Metrics Artifacts

# Summary

The system shall prevent metrics artifacts from exposing full filesystem paths.
updated: 2026-04-05
the same shortened safe-display strategy already required for runtime logging:
show only the leaf and at most one parent segment where possible.

This requirement applies to shareable metrics artifacts, not only console logs.
The goal is to avoid leaking usernames, local directory structure, storage
provider names, or other environment-specific information through generated
files that users may distribute.

---

# Motivation

Metrics output is often copied into reports, sent to collaborators, or used as
reference artifacts in documentation and tests. Absolute paths in those files
reveal user and machine details that are unrelated to the research output and
therefore create an avoidable privacy and security problem.

The repository already adopted a path-minimization strategy for logging in
[REQ-016](016-standardized-cli-logging-and-console-options.md). Metrics
artifacts must follow the same rule so the security strategy is consistent
across both runtime output and persisted generated files.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given metrics text output, when the `METRICS SUMMARY:` line is emitted,
      then it uses the safe path form rather than an absolute filesystem path.
- [ ] Given metrics text output, when the `input:` field under
      `--- RUN CONFIGURATION ---` is emitted, then it uses the safe path form
      rather than an absolute filesystem path.
- [ ] Given metrics JSON output, when the top-level `file` field is emitted,
      then it uses the safe path form rather than an absolute filesystem path.
- [ ] Given a path-bearing value emitted by metrics artifacts, when it has more
      than one parent segment, then the display form is `...\parent\file.ext`.
- [ ] Given a drive-root path such as `C:\corpus-lob_tilde.txt`, when it is
      emitted by metrics artifacts, then it is preserved in that drive-root
      form.
- [ ] Given a metrics artifact path value, when a shorter one-parent form is
      available, then no username, home directory, deep workspace path, or
      other unnecessary prefix is exposed.
- [ ] Given the implementation is complete, when metrics artifacts are audited,
      then no remaining absolute-path disclosure exists in metrics text or JSON
      output.
- [ ] Given tests are updated, when regression coverage runs, then it verifies
      safe-path rendering for metrics text and JSON outputs and rejects
      representative absolute-path leakage.
- [ ] Given documentation is updated, when metrics examples or path-bearing
      output fields are shown, then they use the shortened safe-path form and
      explain that full path disclosure is intentionally avoided.

---

# User Story (optional)
> As a user who shares generated metrics files, I want paths in those artifacts
> to avoid exposing my local filesystem details so that reports and fixtures can
> be shared safely.

---

# Interface Notes
- Input: `_tilde.txt` and related metrics inputs processed by `metricalc`.
- Outputs affected:
  - `_metrics.txt`
  - `_metrics.json`
- Safe-path examples:
  - `...\results\corpus-lob_tilde.txt`
  - `C:\corpus-lob_tilde.txt`
- Unsafe example:
  - `C:\Users\samue\YandexDisk\GED\...\results\corpus-lob_tilde.txt`
- Affected components: `src/akkapros/lib/metrics.py`,
  `src/akkapros/cli/metricalc.py`, metrics docs, and metrics test fixtures.

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: small
- Migration: update metrics reference artifacts and example snippets that still
  embed absolute local paths.

# Related
- Related ADRs: [ADR-033](../adr/033-minimize-path-disclosure-in-metrics-artifacts.md),
  [ADR-028](../adr/028-centralized-cli-logging-with-logging-actions.md),
  [ADR-029](../adr/029-cli-runtime-output-via-logger-only.md),
  [ADR-031](../adr/031-factual-runtime-records-and-structured-self-test-output.md)
- Related REQs: [REQ-016](016-standardized-cli-logging-and-console-options.md),
  [REQ-012](012-metrics-output-structure-and-layout.md),
  [REQ-004](004-metrics-computation.md)
- Implementation CRs: [CR-026](../cr/026-minimize-path-disclosure-in-metrics-artifacts.md)

# Non-Goals
- This requirement does not change the underlying metrics computations.
- This requirement does not redesign the metrics JSON schema beyond replacing
  unsafe absolute-path display with the safe-path form.
- This requirement does not reopen already-compliant logger call sites outside
  metrics artifacts.

# Security / Safety Considerations
- Full path disclosure in shareable artifacts is treated as a security and
  privacy issue, not merely a formatting concern.
- Shortened paths must still remain readable enough for users to identify the
  analyzed file without revealing unnecessary local environment detail.