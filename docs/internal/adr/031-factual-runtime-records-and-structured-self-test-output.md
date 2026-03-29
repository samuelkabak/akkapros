---
adr_id: ADR-031
status: Accepted
created: 2026-03-28
updated: 2026-03-29
superseded_by: null
---

# 031. Factual Runtime Records and Structured Self-Test Output

## Plain Summary

Runtime output shall favor factual records that are equally usable on a live
console and in later batch-log review. Decorative layout lines, conversational
stage narration, and transcript-style self-test chatter are not part of that
contract and shall be removed.

TL;DR: log facts, not narration.

## Context and Problem Statement

ADR-028 centralized CLI logging setup and ADR-029 required runtime output to
flow through the logger rather than direct `print()` calls. That still left one
operational question open: what kind of messages are acceptable once everything
is logged.

Recent cleanup work exposed the difference between logger-only transport and a
good logging contract. A tool can technically use the logger and still emit
records that add little operator value, such as banner separators, `Running
printer (SOB)...`, `[1/4]` stage markers, or self-test transcripts with mixed
emoji, headings, and commentary. Those records are noisy in batch runs and make
log files harder to scan or parse.

The project therefore needs an explicit decision that defines the acceptable
content of runtime records, not just the output mechanism.

## Decision Drivers

- Batch-log readability
- Operational consistency between console and file logging
- Easy parsing and grepability of self-test results
- Avoidance of duplicate narration from wrapper scripts and called CLIs
- Alignment with ADR-028 and ADR-029 without rewriting those earlier decisions

## Considered Options

- Option A — Allow any logger message shape once output goes through the shared logger. Rejected because transport consistency alone still permits noisy and low-value runtime records.
- Option B — Require factual runtime records, forbid decorative and conversational narration, and standardize self-test lines. Chosen because it creates a reviewable content contract for both tools and wrappers.
- Option C — Remove nearly all runtime records except final file outputs and fatal errors. Not chosen because some factual informational records remain useful for operators and debugging.

## Decision Outcome

Choose Option B.

Across runtime-capable CLIs, CLI-facing library flows, and repository-provided
wrapper scripts, emitted records shall be factual and operationally useful.
This means:

- keep records that report concrete outcomes, parameters, warnings, errors, or written artifacts,
- remove banner lines, separator-only lines, empty spacer records, and conversational stage narration such as `Running ...`, `Processing ...`, or `[1/4] ...`, and
- avoid duplicate wrapper narration when invoked tools already emit the necessary factual stream.

Built-in self-tests shall use a normalized single-line result format:

- `PASS | Category | NN: Label`
- `FAIL | Category | NN: Label`

Categories should remain short, human-readable, and operationally stable.
Failure details may be appended inline when needed, but headings, emoji, and
transcript-style commentary shall not be used.

This ADR extends the logging policy from transport-level consistency to
content-level consistency. It does not supersede ADR-028 or ADR-029; it refines
how those decisions are realized in emitted records.

## Pros and Cons of the Options

### Chosen Option

- Pros: improves scanability of logs in long batch runs
- Pros: makes self-test output easy to grep and compare
- Pros: prevents wrapper scripts from reintroducing noise after CLI cleanup
- Pros: creates a concrete review standard for future logging changes
- Cons: removes some human-oriented narration that may feel friendly in ad hoc manual runs
- Cons: requires auditing wrappers and self-tests in addition to core CLIs

### Other Options

- Option A:
  - Pro: minimal migration effort once logger transport exists
  - Con: noisy records remain fully allowed
- Option C:
  - Pro: extremely quiet logs
  - Con: may hide useful factual progress/context records from operators

## Implications and Consequences

- Future logging reviews must evaluate message content, not only whether the logger API was used.
- Wrapper scripts shipped in the repository should usually remain silent and rely on the underlying tools' factual logs.
- Self-test helpers should stay centralized so the result format does not drift.
- REQ-016 and CR-023 should reference this policy as the content contract that complements ADR-028 and ADR-029.
- Tests may enforce selected examples of banned narration and required PASS/FAIL formatting.

## Links

- [docs/internal/adr/028-centralized-cli-logging-with-logging-actions.md](028-centralized-cli-logging-with-logging-actions.md)
- [docs/internal/adr/029-cli-runtime-output-via-logger-only.md](029-cli-runtime-output-via-logger-only.md)
- [docs/internal/req/016-standardized-cli-logging-and-console-options.md](../req/016-standardized-cli-logging-and-console-options.md)
- [docs/internal/cr/023-adopt-logging-actions-for-cli-logging.md](../cr/023-adopt-logging-actions-for-cli-logging.md)

## Implementation Notes (optional)

- Prefer deleting wrapper-script narration rather than renaming it unless the wrapper adds unique factual value.
- Treat self-test output helpers in `src/akkapros/lib/utils.py` as the canonical formatter for PASS/FAIL lines.
- When in doubt, ask whether a record would still be useful if read alone in a long log file days later.

## Reviewed By

- Pending maintainer review