# Change Request: Enforce POSIX EOF newline in all program outputs

CR-ID: CR-007
Status: Done
Priority: Low
Created: 2026-03-20
Updated: 2026-03-20

---

# Summary

Require that all non-empty text files produced by the project's CLIs and
library writers end with a single terminating newline (POSIX convention:
"A text file is a sequence of lines, each terminated by a <newline> character").

This CR records the decision, the scope of the change, and the implementation
notes. The work has been applied to the staged files listed below and is marked
Done.

---

# Motivation

Some POSIX tools and text-processing idioms expect text files to end with a
newline. Missing final newlines can produce spurious diffs, confuse some
tooling, and create inconsistent output across platforms and runtimes. Ensuring
that every non-empty text output ends with a newline makes outputs more
portable and easier to consume by downstream tools and automated checks.

---

# Scope

## Included

- Ensure all text-writing code paths append a single trailing newline when the
  output is non-empty.
- Update writers used by CLI entrypoints to use a canonical helper or pattern
  that enforces the newline.
- Update unit/self-tests to assert this behavior for program outputs.

## Not Included

- Binary output formats (audio, images) or external tool artifacts.
- External downstream consumers of produced files (they should be updated if
  necessary but are out of scope for this CR).

---

# Current Behavior

Some of the project's text output writers implicitly produced files that may
end without a trailing newline in edge cases. This is a low-severity problem
but affects tooling compatibility and produces diffs when files are edited by
some editors.

---

# Proposed Change

Standardize text output so that any non-empty text file written by the
project's code ends with a single `\n` character. Prefer a small helper in
`src/akkapros/lib/utils.py` or a consistent write pattern used by CLI modules
and library writers.

Concretely:

- Add or use a single canonical write helper that ensures trailing newline.
- Update existing writers in the listed files to use the helper or follow the
  pattern.
- Add unit tests that run each CLI entrypoint that produces textual outputs to
  a temp directory and assert the last byte is `0x0A` when the file size > 0.

The change is non-breaking for downstream consumers because it only adds a
single newline at EOF for non-empty files.

---

# Technical Design

Implementation notes and recommendations:

- Provide a small utility function `write_text_file_atomic(path, text)` which
  normalizes text and appends a single trailing `\n` if `text` is non-empty.
- Use `pathlib.Path.write_text(..., encoding='utf-8')` or an atomic write helper
  and call the normalization helper before writing.
- For streaming writers, ensure the writer emits a final newline when closing
  if any content was written.
- Add unit tests that run each CLI entrypoint that produces example outputs and
  assert EOF newline when file size > 0.

Example helper (implementation detail, not included here):

```py
def ensure_trailing_newline(s: str) -> str:
    if not s:
        return s
    return s.rstrip('\n') + '\n'
```

---

# Files Likely Affected

Staged files with the changes applied in this implementation:

- src/akkapros/cli/fullprosmaker.py
- src/akkapros/cli/metricalc.py
- src/akkapros/cli/syllabifier.py
- src/akkapros/lib/metrics.py
- src/akkapros/lib/print.py
- src/akkapros/lib/prosody.py

Other text-writers (reviewers should scan these as part of a follow-up):

- other CLI modules in `src/akkapros/cli/`
- library-level writers in `src/akkapros/lib/`

---

# Acceptance Criteria

- [x] A canonical text-writing pattern or helper is adopted by writers.
- [x] The staged files listed above have been updated to ensure trailing
  newlines for non-empty text outputs.
- [x] Unit/self-tests added or updated to assert trailing-newline behavior.
- [x] CR status is updated to Done and this CR document is added to the CR
  directory.

---

# Risks / Edge Cases

- Care must be taken not to add spurious extra blank lines (only a single
  trailing newline should be added).
- Writers that intentionally produce empty files must remain empty (no newline
  added in that case).

---

# Testing Strategy

- Unit tests that call writer helpers with empty and non-empty strings.
- CLI self-tests that produce example outputs and verify EOF newline when file
  size > 0.
- Add a small CI check that scans produced text files in a smoke-run and fails
  if any non-empty text file lacks trailing newline.

---

# Rollback Plan

- Revert the commit(s) adding the helper and changes to writers.
- Re-run tests and re-open the CR if unexpected side-effects are observed.

---

# Related Issues

- Follow-up: add an automated pre-commit or CI smoke test to enforce EOF newline
  for outputs.
