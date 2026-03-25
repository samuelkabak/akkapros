# Requirement: Strict Punctuation Whitelist with CLI Extensions

REQ-ID: REQ-011
Status: Draft
Priority: High
Created: 2026-03-21
Updated: 2026-03-21
---

# Summary

The system shall enforce a centralized, explicit whitelist of authorized punctuation for
Akkadian text processing in both syllabification and metrics computation.
Only predeclared punctuation characters/patterns are accepted by default, and users may
extend the accepted set deliberately via command-line options.
Undeclared punctuation in syllabifier input shall raise an explicit error.

---

# Motivation

Current behavior can silently absorb non-Akkadian letters as punctuation in edge cases,
which weakens linguistic control of input quality. For example, text such as `koria` may
be processed as `k¦⟦o⟧ri·¨a¦`, where `o` is treated like punctuation instead of being
rejected as non-Akkadian input.

A scientific workflow needs explicit and reproducible punctuation handling. Centralizing
punctuation classes and forcing declaration of exceptions provides stricter corpus hygiene,
better reproducibility, and clearer diagnostics.

---

# Acceptance Criteria

## Centralized punctuation configuration

- [ ] Punctuation configuration is centralized in shared constants and consumed by
      both `akkapros.lib.syllabify` and `akkapros.lib.metrics`.
- [ ] The following baseline classes exist and are used as defaults:

      SHORT_PAUSE_PUNCTUATION_CHARS = {
          ',', ';', ':', '—', '–', '…',
          '(', ')', '«', '»', '“', '”', '‘', '’', '"', "'",
          '/', '\\', '&', '†', '‡', '|'
      }

      SHORT_PAUSE_PUNCTUATION_PATTERNS = (
          r'\s\.\.\.(?=\s|$)',
          r'\s…(?=\s|$)',
      )

      LONG_PAUSE_PUNCTUATION_CHARS = {
          '.', '?', '!', '[', ']', '{', '}', '<', '>', '-', '*', '+'
      }

      LONG_PAUSE_PUNCTUATION_PATTERNS = (
          r'^\.\.\.',
          r'^…',
      )

## CLI extension options

- [ ] Syllabifier and metrics CLIs expose options to extend punctuation allowlists at runtime.
- [ ] Character-level extension options are supported:
      `--long-punct-chars` and `--short-punct-chars`.
- [ ] Pattern-level extension options are supported as repeatable arguments:
      `--long-punct-pattern` and `--short-punct-pattern`.
- [ ] Syllabifier exposes `--number-format <regex>`.
- [ ] Empty `--number-format` uses built-in English-grouping-compatible number regex.
- [ ] Provided number regex is validated before processing starts.
- [ ] Repeating pattern options works in one invocation (example expected usage):
      `--long-punct-pattern '...' --long-punct-pattern '[ ]+:[ ]+'`.
- [ ] Repeating short-pattern options works in one invocation (example expected usage):
      `--short-punct-pattern '...' --short-punct-pattern '[ ]+,[ ]+'`.
- [ ] Added chars/patterns extend defaults; they do not replace defaults.
- [ ] `fullprosmaker.py` accepts and forwards all punctuation extension options to
      the syllabifier and metrics stages.

## Enforcement behavior

- [ ] In `syllabify.py`, any punctuation token not declared by default or via CLI extension
      causes a hard validation error with source line and offending token.
- [ ] The punctuation validation helper remains in `syllabify.py`, close to parser/tokenizer
      logic (`tokenize_line()`/`syllabify_text()`), to reduce parser-regression risk.
- [ ] In `metrics.py`, punctuation classification uses only declared short/long classes and
      declared patterns.
- [ ] If punctuation appears that cannot be classified under declared rules, metrics exits
      with a clear error rather than silently accepting or reclassifying it.
- [ ] User-provided regex options are validated (compiled) before any text processing starts;
      invalid regex aborts immediately with a clear error.
- [ ] Regex pseudo-tokens are supported and documented for line/file boundaries:
      `[:bol:]`, `[:eol:]`.
- [ ] EOF handling is normalized internally to end-of-line semantics.
- [ ] In preserve-lines mode, newlines are preserved in output for punctuation,
      preserve blocks, and number/currency punctuation suites.
- [ ] Line-start list markers and `#` markers are treated as punctuation suites
      (escaped/preserved), not as Markdown-only structural exceptions.

## Backward compatibility and existing behavior

- [ ] Existing handling of `h` in ATF remains unchanged (`atfparser --preserve-h` controls it).
- [ ] Existing valid Akkadian pipeline inputs continue to process without additional flags.
- [ ] Existing punctuation semantics (short vs long pause interpretation) remain unchanged
      unless user explicitly extends with CLI options.

## Diagnostics and tests

- [ ] Error messages name the unrecognized punctuation and input location.
- [ ] New tests must catch raised exceptions for undeclared punctuation and invalid
      regex options (unit-level and CLI-level).
- [ ] New/updated tests cover:
      recognized punctuation,
      rejected undeclared punctuation,
      successful CLI extension,
      repeated `--short-punct-pattern` behavior,
      repeated `--long-punct-pattern` behavior,
      metrics classification failures on undeclared punctuation,
      fullprosmaker pass-through for all four punctuation extension classes.
- [ ] Legacy permissive syllabifier tests are replaced/updated so they no longer expect
      non-Akkadian letters to be escaped as punctuation (for example the six
      "Foreign character in word" cases with `⟦o⟧` in expected output).
- [ ] Test coverage explicitly protects parser-sensitive paths (`tokenize_line()` and
      `syllabify_text()`) against regressions introduced by punctuation strictness.

---

# User Story (optional)
> As an Akkadian researcher, I want punctuation acceptance to be explicit and centrally
> configured so that non-Akkadian input is rejected early and corpus processing remains
> reproducible across runs.

---

# Interface Notes
- Input: `*_proc.txt` for syllabifier and `*_tilde.txt` for metrics.
- Output: unchanged output formats; new behavior is stricter validation/classification.
- New/updated CLI surface:
      - `--long-punct-chars <chars>`
  - `--short-punct-chars <chars>`
      - `--short-punct-pattern <regex>` (repeatable)
  - `--long-punct-pattern <regex>` (repeatable)
- Affected components:
  - `src/akkapros/lib/syllabify.py`
  - `src/akkapros/lib/metrics.py`
  - `src/akkapros/lib/constants.py` (or equivalent shared constants module)
  - `src/akkapros/cli/syllabifier.py`
  - `src/akkapros/cli/metricalc.py`
      - `src/akkapros/cli/fullprosmaker.py`
      - `docs/akkapros/syllabifier.md`
      - `docs/akkapros/metricalc.md`
      - `docs/akkapros/fullprosmaker.md`
      - `docs/akkapros/metrics-computation.md`
      - `docs/akkapros/prosody-realization-algorithm.md`
      - `tests/test_selftests_lib.py`
      - `tests/test_selftests_cli.py`
      - `tests/test_integration.py`

---

# Open Questions
- [ ] Should unknown punctuation in `metrics.py` raise immediately (strict) or support an
      optional warning-only mode in future releases?

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- High-risk area: `tokenize_line()` in `src/akkapros/lib/syllabify.py`; changes must be
  covered by targeted regression tests before broader refactors.

# Related
- Related ADRs: [ADR-001](../adr/001-pipeline-architecture-and-stage-contracts.md)
- Implementation CRs: [CR-012](../cr/012-enforce-punctuation-whitelist-and-cli-extension.md)

# Non-Goals
- Does NOT change prosody realization algorithms.
- Does NOT expand Akkadian phoneme inventory beyond existing character-set extension options.
- Does NOT auto-correct non-Akkadian text.

# Security / Safety Considerations
- Regex patterns are user-supplied; implementation must compile safely and report invalid
  regex syntax clearly.
- Validation failures must be explicit and non-destructive (no file rewriting).
- Documentation must clearly describe regex evaluation semantics and anchors, including
      concrete behavior for `^`, `$`, `[:bol:]`, `[:eol:]`, and literal separator symbols such as `¨` and `$` in
      pipeline text.
