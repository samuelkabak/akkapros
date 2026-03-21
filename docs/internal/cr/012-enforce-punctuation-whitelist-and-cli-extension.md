# Change Request: Enforce punctuation whitelist and configurable CLI extension

CR-ID: CR-012
Status: Draft
Priority: High
Created: 2026-03-21
Updated: 2026-03-21
Implements: REQ-011
---

# Summary

Introduce strict punctuation allowlisting in syllabifier and metrics so that only
predeclared punctuation is accepted/classified. Centralize punctuation definitions in
shared constants and add CLI options to extend the lists intentionally.
Undeclared punctuation becomes an explicit error instead of being silently assimilated.
`fullprosmaker.py` must accept and forward the same punctuation options.

---

# Motivation

Current behavior allows some non-Akkadian symbols/letters to pass as punctuation in
edge cases, reducing corpus quality controls. This is especially problematic for
linguistic reproducibility where punctuation classes affect pause modeling.

The change enforces explicit scientific configuration while still allowing controlled
extension by command-line options in exceptional workflows.

---

# Scope

## Included

- Add centralized punctuation classes/patterns in shared constants.
- Wire punctuation configuration into both `akkapros.lib.syllabify` and
  `akkapros.lib.metrics`.
- Add CLI options for punctuation extension in:
  - `src/akkapros/cli/syllabifier.py`
  - `src/akkapros/cli/metricalc.py`
  - `src/akkapros/cli/fullprosmaker.py` (pass-through)
- Enforce hard failure for undeclared punctuation in syllabifier.
- Enforce hard failure for unclassifiable punctuation in metrics.
- Update user docs and internal docs for new options and strict behavior.
- Add/extend tests for tokenizer validation and metrics punctuation classification.
- Replace legacy tests that currently expect non-Akkadian letters to be escaped as punctuation.

## Not Included

- No change to ATF parser `h/H` policy (`--preserve-h` remains unchanged).
- No redesign of pause model mathematics beyond punctuation admission/classification.
- No broad refactor of `tokenize_line()` beyond what is needed for this CR.

---

# Current Behavior

- Punctuation handling is not fully centralized as an explicit scientific contract.
- `tokenize_line()` may treat unexpected characters as punctuation-like segments.
- Metrics punctuation classes exist but are not yet driven by a strict shared
  declaration/extension workflow.

---

# Proposed Change

- Move baseline punctuation classes/patterns to shared constants and use them as the
  sole default source in syllabifier and metrics.
- Add runtime extension options:
  - `--long-punct-chars <chars>`
  - `--short-punct-chars <chars>`
  - `--short-punct-pattern <regex>` (repeatable)
  - `--long-punct-pattern <regex>` (repeatable)
- During syllabification, reject undeclared punctuation with clear error context
  (line number, token, and remediation hint).
- During metrics computation, reject punctuation that does not map to declared short/long
  classes or declared patterns.
- During full pipeline runs, `fullprosmaker.py` forwards all punctuation-extension
  options to the relevant sub-stages.

Baseline configuration to use:

- `SHORT_PAUSE_PUNCTUATION_CHARS`
- `SHORT_PAUSE_PUNCTUATION_PATTERNS`
- `LONG_PAUSE_PUNCTUATION_CHARS`
- `LONG_PAUSE_PUNCTUATION_PATTERNS`

(Exact literal sets/patterns per REQ-011.)

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/constants.py`: authoritative punctuation classes/patterns
- `src/akkapros/lib/syllabify.py`: token admission check against declared punctuation;
  helper validation remains here near parser algorithm
- `src/akkapros/lib/metrics.py`: punctuation classification against declared classes/patterns
- CLI wrappers for extension options and propagation to library layer

Validation and matching behavior:
- Char classes are additive unions (defaults + user-provided chars).
- Pattern classes are additive tuples/lists (defaults + repeated CLI patterns).
- Regex compilation errors are surfaced as input/configuration errors before any
  text processing starts.
- Error text explicitly distinguishes:
  unknown punctuation char,
  unclassifiable punctuation segment,
  invalid user regex.
- Syllabifier raises exceptions for undeclared punctuation tokens; tests must catch
  the exceptions explicitly.

High-risk note:
- `tokenize_line()` and related syllabifier path are high-risk in this codebase;
  apply minimal, test-first edits.
- Parsing is error-sensitive: keep helper validation close to tokenizer/parsing flow in
  `syllabify.py` and avoid broad parser rewrites.

---

# Files Likely Affected

src/akkapros/lib/constants.py
src/akkapros/lib/syllabify.py
src/akkapros/lib/metrics.py
src/akkapros/cli/syllabifier.py
src/akkapros/cli/metricalc.py
src/akkapros/cli/fullprosmaker.py
docs/akkapros/syllabifier.md
docs/akkapros/metricalc.md
docs/akkapros/fullprosmaker.md
docs/akkapros/metrics-computation.md
docs/akkapros/prosody-realization-algorithm.md
tests/test_selftests_lib.py
tests/test_selftests_cli.py
tests/test_integration.py

---

# Acceptance Criteria

- [ ] Syllabifier accepts only declared punctuation by default.
- [ ] Syllabifier fails with explicit error on undeclared punctuation.
- [ ] Metrics classifies punctuation only via declared short/long classes/patterns.
- [ ] Metrics fails with explicit error on unclassifiable punctuation.
- [ ] CLI options for char + short-pattern + long-pattern extension are implemented and documented.
- [ ] `fullprosmaker.py` accepts and forwards all punctuation-extension options.
- [ ] Repeated `--long-punct-pattern` works as intended.
- [ ] Repeated `--short-punct-pattern` works as intended.
- [ ] `--number-format <regex>` works in syllabifier (and fullprosmaker pass-through), with empty value using built-in default regex.
- [ ] Existing valid Akkadian fixtures pass unchanged.
- [ ] New regression tests cover rejection and extension scenarios.
- [ ] Legacy permissive tests are updated (including the six
  "Foreign character in word" cases that currently expect escaped `⟦o⟧`).
- [ ] Regex options are validated before processing starts and fail fast on invalid syntax.
- [ ] Documentation clearly explains regex processing semantics and anchors (`^`, `$`),
  including `[:bol:]`, `[:eol:]` and treatment of literal `¨`/`$` symbols in pipeline text.
- [ ] EOF is normalized internally to EOL behavior for punctuation regex matching.
- [ ] Preserve-lines behavior keeps newline boundaries in output for punctuation,
  preserve blocks, and numeric/currency punctuation suites.
- [ ] Line-start bullets and `#` markers are handled as punctuation suites
  and preserved in escaped output.

---

# Risks / Edge Cases

- False positives on punctuation not currently declared but present in historical sources.
- Regex overreach/performance issues with user-provided patterns.
- Backward compatibility concerns if old corpora relied on permissive behavior.
- Option name ambiguity (`punt` vs `punct`) may confuse users.

---

# Testing Strategy

Unit tests:
- tokenizer rejects undeclared punctuation chars.
- tokenizer accepts punctuation added via CLI extension.
- metrics classification rejects unknown punctuation segments.
- repeated short/long pattern options are both honored.
- invalid regex in `--long-punct-pattern` returns clear error.
- invalid regex in `--short-punct-pattern` returns clear error.
- undeclared punctuation exceptions are asserted with explicit exception-catching tests.

Integration tests:
- full stage run with default punctuation set.
- run with additional punctuation chars and repeated short/long pattern options.
- regression sample for former `koria`-style assimilation behavior now failing fast.
- fullprosmaker pass-through validation for all four option types.

Manual tests:
- verify error diagnostics include file/line/token details.
- verify docs examples produce expected behavior.

---

# Rollback Plan

If strict enforcement causes unacceptable disruption:

- Revert punctuation admission checks in syllabifier and metrics to prior behavior.
- Keep centralized constants as non-breaking internal groundwork.
- Re-open with staged rollout plan (warning mode first, strict mode later).

---

# Related Issues

- Requirement: [REQ-011](../specs/011-punctuation-whitelist-and-cli-extension.md)
- Prior validation hardening: [CR-011](011-add-format-validation-guard.md)

---

# Tasks

## Implementation

- [ ] Add shared punctuation constants and pattern lists.
- [ ] Integrate strict punctuation admission in syllabifier.
- [ ] Integrate strict punctuation classification in metrics.
- [ ] Add CLI extension options (`--long-punct-chars`, `--short-punct-chars`,
      `--long-punct-pattern`, `--short-punct-pattern`) and propagate to libraries.
- [ ] Add fullprosmaker pass-through for all punctuation extension options.

## Tests

- [ ] Add unit tests for whitelist enforcement.
- [ ] Add unit tests for extension options.
- [ ] Add integration tests for strict failure and extended success paths.
- [ ] Update/remove legacy permissive tests that expect escaped non-Akkadian letters.

## Documentation

- [ ] Update CLI docs (`syllabifier.md`, `metricalc.md`, `fullprosmaker.md`).
- [ ] Update algorithm/reference docs (`metrics-computation.md`, `prosody-realization-algorithm.md`).
- [ ] Add migration note for users relying on permissive punctuation behavior.
- [ ] Add explicit regex-processing guidance with examples for anchors and literal-symbol
  handling (`¨`, `$`) plus boundary pseudo-tokens (`[:bol:]`, `[:eol:]`).

## Review

- [ ] Code review
- [ ] Verify all acceptance criteria

---

# Notes for CR-012

Confirmed naming decisions:

- Use `--long-punct-chars` (not `--long-punt-chars`).
- Include `--short-punct-pattern` in addition to `--long-punct-pattern`.
- fullprosmaker must expose and forward all punctuation extension options.

The implementation should avoid broad refactors of `tokenize_line()` and proceed
with focused, test-backed changes only.
