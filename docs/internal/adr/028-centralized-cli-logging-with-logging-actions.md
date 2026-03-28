---
adr_id: ADR-028
status: Proposed
created: 2026-03-27
updated: 2026-03-27
superseded_by: null
---

# 028. Centralized CLI Logging with `logging-actions`

## Plain Summary

All command-line tools shall use one shared logging setup built on the
`logging-actions` library instead of ad hoc `print()`-based status output. The
integration shall be centralized in `src/akkapros/lib/utils.py` so every CLI
gets the same logging options, help text, and initialization flow.

TL;DR: one package-wide logging contract, one shared implementation point, four
standard CLI flags.

## Context and Problem Statement

The current CLIs use a mix of startup banners, direct `print()` calls, and
module-specific output patterns. This makes console behavior inconsistent,
harder to debug, and difficult to evolve across all tools together. The codebase
already centralizes reusable CLI helpers in `src/akkapros/lib/utils.py`, and the
user wants logging and console behavior to become equally centralized with
predefined command-line options.

The requested option set is:

- `--quiet`: suppress INFO logs on console, allowing WARNING and above
- `--no-console`: disable console output entirely
- `--log`: log to file
- `--log-append`: append to log file instead of overwriting

The project also needs the resulting design to be easy to find and debug in the
code, which argues for one visible shared integration point rather than repeated
per-CLI setup logic.

## Decision Drivers

- Consistent console and file logging behavior across all CLIs
- Centralized CLI helper architecture already established in `lib/utils.py`
- Easier debugging and discoverability of logging setup
- Explicit, shared argument parsing and help text
- Reduced duplication of startup and progress output logic

## Considered Options

- Option A — Keep direct `print()`-based console output and let each CLI evolve independently. Rejected because behavior remains inconsistent and hard to maintain.
- Option B — Adopt `logging-actions` and wrap it through shared helpers in `src/akkapros/lib/utils.py`. Chosen because it centralizes option parsing and logging setup while keeping call sites easy to inspect.
- Option C — Build a custom logging layer directly on the standard `logging` module with no external library. Not chosen because the request explicitly prefers `logging-actions` and the goal is a ready-made standardized CLI behavior.

## Decision Outcome

Choose Option B.

The package shall adopt `logging-actions` for CLI logging and console output.
The integration shall be centralized in `src/akkapros/lib/utils.py`, which will
be the canonical home for:

- shared logging option registration,
- shared help text fragments,
- shared argument validation for logging flags, and
- shared logger initialization.

Each CLI shall add the same standardized options through the shared helper layer
rather than defining them independently.

The standardized options are:

- `--quiet`: suppress INFO logs on console, leaving WARNING and above
- `--no-console`: disable console output entirely
- `--log FILE`: write logs to file
- `--log-append`: append to the log file instead of overwriting

The design shall prefer logger-based status and progress messages over direct
console printing for normal operation. Centralizing the setup in `lib/utils.py`
is also the approved interpretation of the user's request to make it common in
`utils.lob`, which is treated here as `src/akkapros/lib/utils.py` to align with
the repository's established CLI-helper architecture.

## Pros and Cons of the Options

### Chosen Option

- Pros: one visible and debuggable setup path for all CLIs
- Pros: consistent flag names and help text across commands
- Pros: enables console suppression and file logging without repeated boilerplate
- Pros: aligns with the repository pattern of centralizing CLI helpers in `lib/utils.py`
- Cons: introduces or formalizes a runtime dependency around CLI behavior
- Cons: requires replacing existing `print()`-based status output in multiple tools

### Other Options

- Option A:
  - Pro: no migration work
  - Con: continued inconsistency and duplication
- Option C:
  - Pro: no external dependency
  - Con: duplicates functionality the user explicitly asked to source from `logging-actions`
  - Con: higher design burden for the package maintainers

## Implications and Consequences

- `src/akkapros/lib/utils.py` becomes the canonical logging-helper location for all CLIs.
- Existing CLI startup and progress output should migrate from `print()` to logger calls where practical.
- Help text for logging options should be added through shared helpers rather than repeated strings.
- CLIs must initialize logging early enough that startup and validation messages respect the selected logging options.
- The package documentation for utilities and CLI usage must be updated to describe the shared logging behavior.

## Links

- [docs/internal/adr/001-cli-lib-separation.md](001-cli-lib-separation.md)
- [docs/internal/adr/002-centralized-version-management.md](002-centralized-version-management.md)
- [docs/internal/cr/009-reorganize-cli-gencode.md](../cr/009-reorganize-cli-gencode.md)
- [docs/internal/req/016-standardized-cli-logging-and-console-options.md](../req/016-standardized-cli-logging-and-console-options.md)
- [docs/internal/cr/023-adopt-logging-actions-for-cli-logging.md](../cr/023-adopt-logging-actions-for-cli-logging.md)

## Implementation Notes (optional)

- Prefer one shared helper such as `add_standard_logging_arguments()` plus one setup function such as `setup_cli_logging()` in `src/akkapros/lib/utils.py`.
- Keep the logging setup easy to trace from each CLI `main()`.
- Preserve testability by making logger setup deterministic and explicit.

## Reviewed By

- Pending maintainer review
