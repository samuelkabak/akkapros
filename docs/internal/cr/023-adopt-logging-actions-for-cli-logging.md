---
cr_id: CR-023
status: Done
priority: High
impact: Mutative
created: 2026-03-27
updated: 2026-03-28
implements: REQ-016
---

# Change Request: Adopt `logging-actions` for CLI logging

# Summary

Adopt the `logging-actions` library for command-line logging and console
control, and centralize the integration in `src/akkapros/lib/utils.py` so all
relevant CLIs share one argument-registration path and one logging-setup path.

All runtime output shall go through the shared logger, with direct `print()`
reserved only for the built-in `--help` response.

Console output and file logging must present one coherent record shape, and
runtime path display must avoid leaking full filesystem paths when a shorter
one-parent form is sufficient. Layout-only lines, conversational stage
narration, and built-in self-test transcript chatter must be removed in favor
of structured logger records. Repository-provided wrapper scripts that invoke
multiple CLIs must not reintroduce conversational stage narration around those
tool calls.

The standardized options are:

- `--quiet`
- `--no-console`
- `--log`
- `--log-append`

---

# Motivation

The codebase already centralizes reusable CLI helpers in `lib/utils.py`, but
logging and console behavior remain fragmented across startup banners and direct
`print()` calls. Adopting `logging-actions` through a shared wrapper makes the
logging flow easier to maintain and easier to debug.

This CR also makes the logging options discoverable and consistent across tools.

---

# Scope

## Included

- Add shared logging argument helpers in `src/akkapros/lib/utils.py`.
- Add shared logger setup helpers in `src/akkapros/lib/utils.py`.
- Standardize parser support for `--quiet`, `--no-console`, `--log`, and
  `--log-append`.
- Centralize the help text for these options.
- Migrate all CLI entrypoints to the shared logging helper path across two
      independent paths: the main pipeline CLIs and the Python phoneprep path.
- Replace runtime `print()` output with logger output everywhere except
      parser-generated `--help`.
- Update docs and tests for the shared logging behavior.

## Not Included

- A bespoke custom logging subsystem independent of `logging-actions`.
- Keeping long-term duplicated per-CLI logging setup code.
- Full redesign of every library module's internal logging model.
- JavaScript code under phoneprep.

---

# Current Behavior

CLI tools currently mix shared startup helpers with direct `print()` usage and
locally defined arguments. Logging and console behavior are therefore not yet a
single consistent contract.

---

# Proposed Change

1. Introduce centralized helpers in `src/akkapros/lib/utils.py` for:
   - shared logging-option argument registration,
   - shared help text fragments, and
   - shared logger initialization using `logging-actions`.

2. Standardize these CLI options across relevant tools:
   - `--quiet`: suppress INFO logs on console
   - `--no-console`: disable console output entirely
   - `--log FILE`: write logs to file
   - `--log-append`: append instead of overwrite

3. Use one homogeneous record format across console and file handlers so log
      files remain operationally consistent with the live console stream.

4. Migrate all CLI entrypoints to call the shared helper functions instead of
      defining local logging behavior. The rollout covers the main pipeline CLIs
      and the Python phoneprep path, which may proceed independently and in
      parallel.

5. Route all runtime output through the logger and reserve direct `print()`
      only for the built-in `--help` response.

6. Minimize logged path disclosure to the final path segment plus one parent
      segment where possible, while preserving drive-root forms such as
      `C:\file.txt`.

7. Remove repeated high-frequency progress counters that do not add useful
      operator value under the new shared logging system.

8. Remove banner/separator/layout records and conversation-style stage logs in
      favor of factual runtime records that remain useful in batch log review.

9. Standardize built-in self-test logging to single-line structured records of
      the form `PASS | Category | 01: Label` and `FAIL | Category | 01: Label`,
      with inline failure details instead of transcript-style commentary.

10. Keep repository-provided demo and orchestration wrappers silent unless they
      are emitting factual records that add non-duplicative operator value over
      the underlying tool logs.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/utils.py` as the canonical helper location
- CLI entrypoints under `src/akkapros/cli/`
- the Python phoneprep path
- shared docs describing utility helpers

Shared behavior:
- one helper for parser option registration
- one helper for logging initialization
- one shared help-text source for the four standard options

Debuggability:
- logging setup should remain easy to trace from each CLI `main()`
- helper names and call sites should make the control flow obvious

Argument behavior:
- `--quiet` affects console verbosity only
- file logging should capture the same coherent record format used on console
- `--log-append` controls append vs overwrite when file logging is active
- invalid or incomplete combinations should be handled consistently by the
  shared helper layer
- path-bearing log messages should pass through a shared display-minimization rule
- high-frequency progress counters should be opt-in work if ever reintroduced,
      not default runtime output
- self-test helpers should be centralized enough that modules do not invent
      separate PASS/FAIL syntaxes, emoji markers, or banner blocks
- wrapper scripts should not add `Running ...` or equivalent narration when the
      invoked CLIs already provide the factual output stream

---

# Files Likely Affected

`src/akkapros/lib/utils.py`
CLI entrypoints under `src/akkapros/cli/`
`docs/akkapros/utils.md`
CLI documentation pages that list shared options
tests covering CLI startup and helper behavior

---

# Acceptance Criteria

- [ ] `src/akkapros/lib/utils.py` contains the canonical shared helpers for
      logging option registration and logging setup.
- [ ] All CLI parsers in scope expose `--quiet`, `--no-console`, `--log`, and
      `--log-append` through the shared helper path.
- [ ] Shared help text is reused instead of redefining the option descriptions
      in each CLI.
- [ ] Logger initialization uses `logging-actions`.
- [ ] Console and file logging use one homogeneous record format.
- [ ] Logging setup is easy to locate and debug from each CLI entrypoint.
- [ ] Runtime output other than parser-generated `--help` is emitted through
      the shared logger rather than direct `print()` calls.
- [ ] Source modules in scope no longer contain direct `print()` calls for
      runtime, self-test, or generator output.
- [ ] Logged filesystem paths are minimized to one parent plus the leaf where
      possible, while preserving drive-root cases.
- [ ] Repeated low-value progress counters are removed from normal runtime logs.
- [ ] Banner lines, separator-only lines, and conversational stage narration
      are removed from normal runtime logs.
- [ ] Repository-provided wrapper scripts do not emit duplicate conversational
      stage narration around CLI invocations.
- [ ] Built-in self-tests emit structured single-line PASS/FAIL records with
      normalized numbering and category labels.
- [ ] The migration covers both the main pipeline CLIs and the Python
      phoneprep path.
- [ ] No JavaScript phoneprep code is modified under this CR.
- [ ] Tests cover argument registration, shared setup behavior, and expected
      console/file logging semantics.
- [ ] Documentation is updated to describe the shared logging options and the
      helper location.
- [ ] User-facing documentation is updated for shared logging behavior and the
      visible effects of `--quiet`, `--no-console`, `--log`, and
      `--log-append`.
- [ ] Developer-facing documentation is updated for helper ownership,
      logger-only runtime rules, and migration guidance for both rollout paths.
- [ ] Built-in `run_tests()` coverage is updated where applicable.
- [ ] Pytest coverage includes unit tests and integration tests for shared
      parser options, logger setup, and runtime-output control.

---

# Risks / Edge Cases

Possible issues:

- Introducing `logging-actions` changes the runtime dependency profile.
- Existing CLI output snapshots or tests may depend on direct `print()` text.
- The Python phoneprep path may require extra migration care because it
      currently contains more monolithic CLI logic than the other tools.

---

# Testing Strategy

Unit tests:

- shared parser helper adds the four expected options
- shared setup helper applies quiet/no-console/log/log-append behavior
- invalid option combinations are handled consistently

Pytest / regression tests:

- CLI entrypoints use the shared helper path
- expected console and file logging behavior is stable
- documentation references match the shared option contract

---

# Rollback Plan

Remove the `logging-actions` integration and restore the prior CLI-specific
console and logging setup if the change must be reversed.

---

# Related Issues

- Legalized by [REQ-016](../req/016-standardized-cli-logging-and-console-options.md).
- Based on [ADR-028](../adr/028-centralized-cli-logging-with-logging-actions.md).
- Constrained by [ADR-029](../adr/029-cli-runtime-output-via-logger-only.md).
- Content policy refined by [ADR-031](../adr/031-factual-runtime-records-and-structured-self-test-output.md).
- Builds on the shared-helper architecture established by
  [CR-009](009-reorganize-cli-gencode.md).

---

# Tasks

## Implementation

- [ ] Add shared logging option helper(s) to `src/akkapros/lib/utils.py`.
- [ ] Add shared logging setup helper(s) using `logging-actions`.
- [ ] Migrate the main pipeline CLIs to the shared helper path.
- [ ] Migrate the Python phoneprep path to the shared helper path.
- [ ] Replace runtime `print()` calls with logger output except for
      parser-generated `--help`.

## Tests

- [ ] Update built-in `run_tests()` coverage where applicable.
- [ ] Add pytest unit coverage for argument registration and setup behavior.
- [ ] Add pytest integration coverage for CLI output-control behavior.

## Documentation

- [ ] Update `docs/akkapros/utils.md`.
- [ ] Update CLI docs that list shared options.
- [ ] Update developer-facing docs for helper ownership, logger-only policy,
      and rollout expectations.

## Review

- [ ] Confirm rollout sequencing between the main pipeline CLIs and the Python
      phoneprep path.

---

# Notes for CR-023

This CR is intentionally centralized around `src/akkapros/lib/utils.py` so the
logging path is easy to find and debug. The user's request to make it common in
`utils.lob` is interpreted here as the repository's existing shared helper home
in `src/akkapros/lib/utils.py`.
