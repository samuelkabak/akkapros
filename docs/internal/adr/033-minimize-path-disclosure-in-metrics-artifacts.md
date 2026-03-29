---
adr_id: ADR-033
status: Accepted
created: 2026-03-29
updated: 2026-03-29
superseded_by: null
---

# 033. Minimize Path Disclosure in Metrics Artifacts

## Plain Summary

Metrics text and JSON artifacts shall not expose full filesystem paths. Instead,
they shall use the same safe shortened path form already required for runtime
logging: one parent plus the filename where possible, while preserving shallow
drive-root paths when no further reduction is available.

TL;DR: shareable metrics files must not leak user directory paths.

## Context and Problem Statement

The repository already has a path-minimization policy for runtime logging in
`REQ-016` and `CR-023`. Most logger calls now follow that policy through the
shared path-formatting helper. However, metrics artifacts themselves still
embed absolute paths in user-visible content such as:

- the `METRICS SUMMARY:` line in text output,
- the `input:` value in metrics run configuration, and
- the top-level `file` field in metrics JSON output.

Those outputs are often shared outside the local machine. Absolute paths in
such artifacts reveal usernames, cloud-storage providers, workspace names, and
other local environment details that are not necessary for interpreting the
metrics.

The project therefore needs an explicit decision that the path-security rule
applies not only to logs, but also to persisted metrics artifacts.

## Decision Drivers

- Avoid leaking user-specific filesystem information in shareable artifacts
- Keep metrics outputs aligned with the existing path-minimization strategy
- Preserve enough path information for humans to identify the analyzed file
- Minimize surprise between runtime logs and generated metrics files
- Keep the solution small and deterministic

## Considered Options

- Option A — Keep absolute paths in metrics artifacts for maximum traceability. Rejected because it leaks unnecessary local information and conflicts with the established security direction.
- Option B — Apply the existing one-parent safe-path strategy to metrics artifacts. Chosen because it aligns with the current logging policy and preserves enough context for users.
- Option C — Remove path-bearing fields from metrics artifacts entirely. Not chosen because users still benefit from a readable file identifier in metrics text and JSON.

## Decision Outcome

Choose Option B.

Metrics artifacts shall use the existing safe-path display strategy already
approved for runtime logging:

- prefer `...\parent\file.ext` when deeper path structure exists,
- preserve drive-root forms such as `C:\file.ext`, and
- do not expose longer absolute prefixes when the safe shortened form is
  available.

This decision applies at minimum to:

- the `METRICS SUMMARY:` line in metrics text output,
- path-bearing values under `--- RUN CONFIGURATION ---`, and
- the top-level `file` field in metrics JSON output.

The metrics artifact content is treated as security-sensitive shareable output,
not merely as an internal debugging transcript.

## Pros and Cons of the Options

### Chosen Option

- Pros: aligns metrics artifacts with the existing logging security policy
- Pros: avoids leaking usernames and deep local directory structure
- Pros: preserves readable provenance for the analyzed file
- Pros: requires only a narrow serializer change rather than a format redesign
- Cons: changes snapshot and reference fixtures
- Cons: some downstream tooling may need to stop depending on absolute path values

### Other Options

- Option A:
  - Pro: preserves maximal local traceability
  - Con: exposes unnecessary personal and machine-specific information
  - Con: conflicts with the repository's safe-path policy
- Option C:
  - Pro: strongest possible privacy posture for path-bearing fields
  - Con: removes useful provenance context from metrics outputs
  - Con: is a larger contract change than necessary

## Implications and Consequences

- Metrics text and JSON serializers must be updated to shorten path-bearing
  fields.
- Integration fixtures and expected output snapshots must be regenerated or
  edited to the safe-path form.
- Documentation examples showing metrics output must stop using absolute local
  paths.
- Future metrics fields that carry filesystem paths must follow the same rule
  by default.

## Links

- [docs/internal/req/018-minimize-path-disclosure-in-metrics-artifacts.md](../req/018-minimize-path-disclosure-in-metrics-artifacts.md)
- [docs/internal/cr/026-minimize-path-disclosure-in-metrics-artifacts.md](../cr/026-minimize-path-disclosure-in-metrics-artifacts.md)
- [docs/internal/req/016-standardized-cli-logging-and-console-options.md](../req/016-standardized-cli-logging-and-console-options.md)
- [docs/internal/cr/023-adopt-logging-actions-for-cli-logging.md](../cr/023-adopt-logging-actions-for-cli-logging.md)

## Implementation Notes (optional)

- Prefer reusing the existing safe-path helper rather than inventing a second
  metrics-specific path-shortening rule.
- Audit both metrics text and metrics JSON outputs, because both are shareable
  artifacts and both currently expose paths.

## Reviewed By

- Pending maintainer review