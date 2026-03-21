# Change Request: Add format-validation guard to file-input CLIs

CR-ID: CR-011
Status: Done
Priority: Medium
Created: 2026-03-20
Updated: 2026-03-20
Implements: ADR-001
---

# Summary

Add a lightweight format-validation guard at the start of all file-input CLIs:
`atfparser.py`, `syllabifier.py`, `prosmaker.py`, `metricalc.py`, `printer.py`,
and `fullprosmaker.py`. The guard detects obviously partial/corrupted inputs and
returns clear, actionable errors with source path + line number + reason.

---

# Motivation

Partial or truncated intermediate files (for example when a previous stage was
killed mid-write) currently get silently processed by downstream stages. This
produces misleading outputs and noisy downstream errors that are hard to debug.

A simple validation step will raise an early error, save developer time, and
make pipeline runs and CI more robust.

---

# Scope

## Included

- Add a small, well-documented validation helper and call it early in all six
  file-input CLI entrypoints.
- The guard should check for common corruption classes only (see Technical
  Design) and return a helpful error message + exit code.
- Add unit tests covering valid, truncated, and obviously-broken inputs.

## Not Included

- Full schema validation of every intermediate format (out-of-scope for this
  change). Heavy-weight validation can be considered separately.
- Automatic repair of corrupted files. This CR only detects and reports.

---

# Current Behavior

Both CLIs silently accept input files and proceed. If an input file is
partially written (truncated), downstream processing may raise obscure
exceptions later or produce incorrect outputs.

Example failure mode:

- A `*_syl.txt` file truncated in the middle of a line produces incomplete
  syllable lists; `prosmaker` proceeds and generates incorrect accentuation.

---

# Proposed Change

- Introduce `validate_intermediate_format(path: Path, expected_kind: str) -> None`
  and `FormatValidationError` in `akkapros.lib.utils`, and call it at startup
  of all six file-input CLIs.
- Validation is mandatory in all validating CLIs (no CLI bypass flag).
- On validation failure, CLIs return exit code `2` and print a precise message
  including source path, line number (when available), and reason.

---

# Technical Design

Validation is intentionally lightweight and fast. It should detect the most
likely and actionable problems without trying to be a full parser.

Checks to implement (examples):

- File existence and non-empty
- File size threshold: warn/fail if file size < X bytes (configurable default,
  e.g., 8 bytes)
- Line-count heuristic: expected minimal number of lines for this stage (e.g.,
  `*_syl.txt` should have >= 1 non-empty line; `*_tilde.txt` typically has
  many lines — use a small threshold)
- Syntax spot-checks:
  - For `*_syl.txt`: at least one line must contain a syllable separator (`.`)
    or the word-boundary marker (`¦`) and consist of ASCII/Unicode letters or
    permitted punctuation.
  - For `*_tilde.txt`: at least one `~` or `_` or a dot `.` must appear if the
    file is expected to contain prosody markers; if none of these are present,
    raise a validation warning or error.
- Common corruption signatures: truncated final line (no trailing newline) is
  a warning; extremely short final token lists (single character) considered
  suspicious.

Design choices:

- Keep the checks conservative (avoid false positives) and fail-fast on
  obviously broken inputs.
- Provide clear, actionable error text suggesting the upstream stage and the
  likely reason (e.g., "previous stage may have been interrupted; re-run
  atfparser/syllabify to regenerate file X").
- Put the implementation in a small helper so other CLIs can reuse it later.

---

# Files Likely Affected

src/akkapros/lib/utils.py  (preferred place for reusable helper)
src/akkapros/cli/atfparser.py
src/akkapros/cli/syllabifier.py
src/akkapros/cli/prosmaker.py
src/akkapros/cli/metricalc.py
src/akkapros/cli/printer.py
src/akkapros/cli/fullprosmaker.py
tests/test_format_validation.py

---

# Acceptance Criteria

- [x] All six file-input CLIs call the validator at startup.
- [x] On obviously truncated/corrupted input, the CLI exits with non-zero
  status and prints a clear, actionable message with source + line + reason.
- [x] All validating CLIs enforce startup validation with no bypass flag.
- [x] Unit tests for validator: valid input passes, truncated input fails,
  suspicious-but-valid input may only warn (configurable).
- [x] Documentation: short note in `docs/akkapros/` describing the new guard
  and guidance for automated pipelines.

---

# Risks / Edge Cases

- False positives: overly-strict checks could break edge-case valid inputs.
  Mitigation: make thresholds configurable and keep checks conservative.
- Packaging/import path: validation helper should be added to `lib/utils.py`
  to avoid circular imports from CLI wrappers.

---

# Testing Strategy

Unit tests:

- `tests/test_format_validation.py` covering:
  - valid small `*_syl.txt` and `*_tilde.txt` examples
  - truncated files (short size, missing separators)
  - files with no trailing newline

Integration tests (manual/CI):

- Run `prosmaker.py --test` and `metricalc.py --test` with generated good and
  intentionally-truncated inputs to ensure the guard triggers appropriately.

---

# Rollback Plan

If the guard causes false positives in CI, revert the CLI calls to the helper
and adjust thresholds. The helper addition is additive and easy to roll back.

---

# Tasks

## Implementation
- [x] Add `validate_intermediate_format()` to `src/akkapros/lib/utils.py` or
      `src/akkapros/cli/_format_validation.py`.
- [x] Call validator early in all six file-input `main()` entrypoints.
- [x] Keep validation mandatory (no CLI skip option).

## Tests
- [x] Add `tests/test_format_validation.py`.

## Documentation
- [x] Update all affected CLI docs with validation behavior and
  mandatory startup validation guidance.

## Review
- [x] Code review and CI run
- [ ] Merge after approval

---

# Notes for CR-011

Keep the validator minimal and conservative. The goal is to reduce silent
failures caused by truncated intermediate files and obvious wrong-stage input,
not to implement a full parser of every edge case.

Verification notes (2026-03-20):

- `pytest -q tests/test_format_validation.py tests/test_selftests_cli.py -k "prosmaker or metricalc or format_validation"`
  - Result: `9 passed, 13 deselected`
- `rg "validate_intermediate_format\(" src/akkapros/cli`
  - Result: all validating CLIs call the shared startup validator.
- `python src/akkapros/cli/prosmaker.py --test`
  - Result: all prosmaker self-tests passed
- `python src/akkapros/cli/metricalc.py --test`
  - Result: `12/12` metrics self-tests passed
