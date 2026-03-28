# Requirement: Standardized CLI Logging and Console Options

REQ-ID: REQ-016
Status: Implemented
Priority: High
Impact: Mutative
Created: 2026-03-27
Updated: 2026-03-28
---

# Summary

The system shall provide one standardized logging and console-control interface
for command-line tools, implemented through the `logging-actions` library and
centralized in `src/akkapros/lib/utils.py`.

Every CLI shall expose the same logging options and use the same shared helper
functions for argument registration and logger setup. All runtime output shall
go through the shared logger, with direct `print()` reserved only for the
built-in `--help` response. This same logger-only rule also applies to built-in
`run_tests()` and related self-test output in source modules.

Console output and file logging shall use one coherent message shape so the log
file does not present a materially different runtime narration from the console.
Runtime path display shall be minimized to the leaf and one parent segment when
possible, to avoid leaking unnecessary filesystem detail in logs. Layout-only
records (banner lines, separator lines, empty spacer records) and
conversation-style stage narration shall not be emitted.
Shipped orchestration wrappers and demo runners that invoke the CLIs shall not
add a second layer of conversational stage messages on top of the underlying
CLI log stream.

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

- [x] Given any CLI entrypoint in the package, when its parser is built, then
      it exposes these standardized options:
      `--quiet`, `--no-console`, `--log`, and `--log-append`.
- [x] Given `--quiet`, when console output is enabled, then INFO-level logs are
      suppressed and WARNING-and-above logs remain visible.
- [x] Given `--no-console`, when the CLI runs, then console log output is
      disabled entirely.
- [x] Given `--log FILE`, when the CLI runs, then logs are written to `FILE`.
- [x] Given console logging and file logging are both enabled, when the CLI
      runs, then both outputs use one homogeneous record format rather than
      diverging message shapes.
- [x] Given `--log-append`, when `--log FILE` is also used, then the log file
      is opened in append mode rather than overwrite mode.
- [x] Given `--log-append` without `--log FILE`, when arguments are validated,
      then the behavior is handled consistently by the shared logging layer.
- [x] Given shared CLI help output, when logging options are shown, then the
      help text is provided by a common helper rather than per-CLI duplication.
- [x] Given CLI startup, when logging is initialized, then the setup is routed
      through shared functions in `src/akkapros/lib/utils.py`.
- [x] Given code navigation or debugging, when a maintainer looks for logging
      behavior, then the canonical logic is easy to find in `src/akkapros/lib/utils.py`.
- [x] Given runtime output other than the built-in `--help` response, when any
      CLI runs, then status, progress, warning, and error messages are emitted
      through the shared logger rather than direct `print()` calls.
- [x] Given source modules under `src/`, when output is emitted from runtime,
      self-test, or code-generation paths, then direct `print()` calls are not
      used and logger output is used instead.
- [x] Given runtime logging includes filesystem paths, when those paths are
      emitted, then they are minimized to the leaf and at most one parent
      segment where possible, while preserving drive-root paths such as
      `C:\file.txt`.
- [x] Given runtime logging uses the shared logger, when progress messages are
      emitted, then redundant high-frequency counters that add little operator
      value are omitted from normal runs.
- [x] Given runtime logging is intended for later log review, when records are
      emitted, then banner lines, separator-only lines, and conversational
      stage narration such as `Processing`, `Running ...`, or `[1/4]` markers
      are omitted.
- [x] Given repository-provided wrapper scripts or demo runners invoke multiple
      CLIs in sequence, when they are executed, then they do not emit their own
      conversational stage narration that duplicates or obscures the factual
      records emitted by the called tools.
- [x] Given built-in self-tests emit progress or results, when they log test
      cases, then they use a structured single-line shape of the form
      `PASS | Category | 01: Label` or `FAIL | Category | 01: Label`, without
      emoji markers or separate heading/layout lines.
- [x] Given this requirement is implemented, when documentation is updated,
      then user-facing docs describe the shared logging options and user-visible
      behavior and developer-facing docs describe helper ownership, rollout
      scope, and logger-only runtime rules.
- [x] Given this requirement is implemented, when tests are updated, then
      built-in `run_tests()` coverage is adjusted where applicable and pytest
      coverage includes unit and integration validation of shared argument
      registration, logger setup, and output-control behavior.
- [x] Given logging migration rollout, when implementation scope is applied,
      then all CLI entrypoints are migrated across two independent paths: the
      main pipeline CLIs and the Python phoneprep path.
- [x] Given phoneprep migration, when scope is interpreted, then only the
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
- Shared record format: console and file handlers should emit the same core
      `level:name:message` structure.
- Shared path-display rule: prefer `...\parent\file.ext`; preserve root-level
      drive paths such as `C:\file.ext`.
- Shared self-test record body: prefer `PASS | Category | NN: Label` and
      `FAIL | Category | NN: Label`, with optional single-line key/value
      failure details appended after the label.
- Affected components: CLI entrypoints under `src/akkapros/cli/`, the Python
      phoneprep path, utility docs, and any tests covering CLI startup and logging
      behavior.

---

# Open Questions
- [x] None.

---

# Implementation Notes (optional)
- Owner: GitHub Copilot
- Estimated effort: medium
- Migration: replace repeated parser-option definitions and all runtime
      `print()` calls, except parser-generated `--help`, with shared logging
      helpers. Keep console/file message shapes coherent, minimize logged path
      disclosure, remove low-value repeated progress counters, remove
      banner/layout records, standardize built-in self-test result records, and
      avoid adding duplicate stage narration in repository-provided wrapper
      scripts. The main pipeline CLIs and the Python phoneprep path may be
      migrated independently and in parallel.

# Related
- Related ADRs: [ADR-028](../adr/028-centralized-cli-logging-with-logging-actions.md),
      [ADR-029](../adr/029-cli-runtime-output-via-logger-only.md),
      [ADR-031](../adr/031-factual-runtime-records-and-structured-self-test-output.md),
      [ADR-001](../adr/001-cli-lib-separation.md)
- Related REQs: [REQ-007](007-full-pipeline-orchestration.md)
- Implementation CRs: [CR-023](../cr/023-adopt-logging-actions-for-cli-logging.md)

# Non-Goals
- This requirement does not require every library module to expose a public
  logger API.
- This requirement does not preserve scattered per-CLI logging option
  definitions.
- This requirement does not cover JavaScript code under phoneprep.

# Security / Safety Considerations
- File logging should be centralized so path handling and mode selection are not
  reimplemented inconsistently across CLIs.
