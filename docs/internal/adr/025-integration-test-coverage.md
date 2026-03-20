---
Status: Accepted
Date: 2026-03-20
---

# ADR 025: Integration Test Coverage for CLI and Outputs

## Context

The project exposes a set of command-line entrypoints (CLIs) that implement
the end-to-end processing pipeline for Akkadian prosody. Regressions that span
multiple stages (parsing → syllabification → prosody realization → metrics →
printer) are hard to catch with per-module unit tests alone. Several outputs
are produced by default CLI runs (processed ATF, syllabified text, `_tilde`/
accentuated pivot format, metrics in text/JSON/CSV, phoneprep sidecars, and
printer outputs) and must be verified together to ensure pipeline correctness.

## Decision

The project will maintain a single, small, reproducible integration test
(`tests/test_integration.py`) that runs the full pipeline using the default
CLI behavior and verifies all output types produced by those default runs.
The integration test will be considered a required continuous-integration
check and must be maintained alongside any change that affects CLI output
formats or pipeline semantics.

Specifically, the integration test MUST:

- Invoke the public CLI entrypoints (or their equivalent library functions)
  for the following modules using their default behavior: `atfparser`,
  `syllabifier`, `prosmaker`/`fullprosmaker`, `metricalc`/`metrics calculator`,
  `phoneprep`, and `printer`.
- Verify that every output file normally produced by a default run is
  present and non-empty.
- Compare produced outputs against committed golden references in
  `tests/integration_refs/` (or an agreed equivalent). Comparisons must
  sanitize or canonicalize path- or environment-dependent fields (e.g.
  absolute paths in metrics tables) to avoid brittle failures.
- Assert a small set of pinned, well-documented metrics (e.g., VarcoC and
  accentuation rate) using tolerances recorded in the test.
- Include at least one canonical `_tilde.txt` line (sample) whose format is
  expected to remain stable; the sample line must be stored in the
  reference fixtures.

## Consequences

- The project repository will include committed golden reference outputs
  sufficient to exercise the integration test deterministically in CI. These
  files live under `tests/integration_refs/` and must be updated when output
  formats intentionally change.
- Developers making changes that affect CLI output formats or pipeline
  semantics must update the integration references and update the ADR/CR as
  appropriate.
- The test must be written to tolerate small numeric variations (via
  explicit tolerances) and to canonicalize path-dependent fields so that CI
  remains deterministic across environments.

## Implementation Notes

- Prefer importing library entrypoints when available (faster, cross-platform)
  but tests may also call CLI wrappers when necessary to exercise the exact
  default-run behavior.
- Keep the sample small (≈3–10 lines) to limit runtime in CI.
- Document regeneration steps in `tests/integration_refs/README.md` so that
  maintainers can update golden outputs reproducibly.

## Related Change Requests

- CR-008: Add end-to-end integration test with gold-standard metrics
  ([docs/internal/cr/008-add-integration-test.md](docs/internal/cr/008-add-integration-test.md))

## Review

This ADR was authored 2026-03-20 and accepted by the repository maintainer.
