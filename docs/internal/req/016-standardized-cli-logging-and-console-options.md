# Requirement: Standardized CLI Logging and Console Options

REQ-ID: REQ-016
Status: Draft
Priority: High
Impact: Mutative
Created: 2026-03-27
Updated: 2026-03-27
---

# Summary

The system shall provide one standardized logging and console-control interface
for command-line tools, implemented through the `logging-actions` library and
centralized in `src/akkapros/lib/utils.py`.

Every CLI shall expose the same logging options and use the same shared helper
functions for argument registration and logger setup. All runtime output shall
go through the shared logger, with direct `print()` reserved only for the
built-in `--help` response.

---

# Motivation

Current CLIs use inconsistent combinations of startup banners, status prints,
and warning prints. This makes runtime behavior harder to predict and harder to
debug. A centralized logging layer with fixed options and shared help text will
make CLI behavior consistent and easier to maintain.

The repository already centralizes common CLI helpers in `src/akkapros/lib/utils.py`,
so logging should follow the same pattern.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given any CLI entrypoint in the package, when its parser is built, then
      it exposes these standardized options:
      `--quiet`, `--no-console`, `--log`, and `--log-append`.
- [ ] Given `--quiet`, when console output is enabled, then INFO-level logs are
      suppressed and WARNING-and-above logs remain visible.
- [ ] Given `--no-console`, when the CLI runs, then console log output is
      disabled entirely.
- [ ] Given `--log FILE`, when the CLI runs, then logs are written to `FILE`.
- [ ] Given `--log-append`, when `--log FILE` is also used, then the log file
      is opened in append mode rather than overwrite mode.
- [ ] Given `--log-append` without `--log FILE`, when arguments are validated,
      then the behavior is handled consistently by the shared logging layer.
- [ ] Given shared CLI help output, when logging options are shown, then the
      help text is provided by a common helper rather than per-CLI duplication.
- [ ] Given CLI startup, when logging is initialized, then the setup is routed
      through shared functions in `src/akkapros/lib/utils.py`.
- [ ] Given code navigation or debugging, when a maintainer looks for logging
      behavior, then the canonical logic is easy to find in `src/akkapros/lib/utils.py`.
- [ ] Given runtime output other than the built-in `--help` response, when any
      CLI runs, then status, progress, warning, and error messages are emitted
      through the shared logger rather than direct `print()` calls.
- [ ] Given this requirement is implemented, when documentation is updated,
      then user-facing docs describe the shared logging options and user-visible
      behavior and developer-facing docs describe helper ownership, rollout
      scope, and logger-only runtime rules.
- [ ] Given this requirement is implemented, when tests are updated, then
      built-in `run_tests()` coverage is adjusted where applicable and pytest
      coverage includes unit and integration validation of shared argument
      registration, logger setup, and output-control behavior.
- [ ] Given logging migration rollout, when implementation scope is applied,
      then all CLI entrypoints are migrated across two independent paths: the
      main pipeline CLIs and the Python phoneprep path.
- [ ] Given phoneprep migration, when scope is interpreted, then only the
      Python code is in scope and JavaScript code is excluded.

---

# User Story (optional)
> As a maintainer or user of the CLI tools, I want one consistent logging
> interface across commands so that output control, file logging, and debugging
> work the same way everywhere.

---

# Interface Notes
- Standard CLI options:
  - `--quiet`: Suppress INFO logs (only WARNING and above)
  - `--no-console`: Disable console output entirely
  - `--log FILE`: Log to file
  - `--log-append`: Append to log file instead of overwriting
- Canonical helper location: `src/akkapros/lib/utils.py`
- Affected components: CLI entrypoints under `src/akkapros/cli/`, the Python
      phoneprep path, utility docs, and any tests covering CLI startup and logging
      behavior.

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration: replace repeated parser-option definitions and all runtime
      `print()` calls, except parser-generated `--help`, with shared logging
      helpers. The main pipeline CLIs and the Python phoneprep path may be
      migrated independently and in parallel.

# Related
- Related ADRs: [ADR-028](../adr/028-centralized-cli-logging-with-logging-actions.md),
  [ADR-029](../adr/029-cli-runtime-output-via-logger-only.md),
  [ADR-001](../adr/001-cli-lib-separation.md)
- Related REQs: [REQ-007](007-full-pipeline-orchestration.md)
- Implementation CRs: [CR-023](../cr/023-adopt-logging-actions-for-cli-logging.md)

# Non-Goals
- This requirement does not specify the exact runtime log format string beyond
  requiring shared configuration.
- This requirement does not require every library module to expose a public
  logger API.
- This requirement does not preserve scattered per-CLI logging option
  definitions.
- This requirement does not cover JavaScript code under phoneprep.

# Security / Safety Considerations
- File logging should be centralized so path handling and mode selection are not
  reimplemented inconsistently across CLIs.
