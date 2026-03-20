---
Status: Accepted
Date: 2026-03-18
---

# 024 — Command-annotated escape syntax (`{tag{text}}`) for pipeline metadata and internal commands

## Plain Summary

Introduce a small, explicit command-annotated escape syntax that lets input files embed commands and metadata for downstream pipeline stages: `{tag{text}}` where `tag` matches the regex `[0-9a-z_]{0,16}`. Also preserve the plain double-brace `{{text}}` form for simple escapes. Tags beginning with `_` are reserved for internal pipeline commands (e.g., `{_mdf{---}}`) and may trigger stage-specific behavior (printer expansion) or be carried pass-through by default.

## Motivation

Researchers and downstream tooling sometimes need to attach small pieces of metadata or commands to segments of input text (for printing hints, formatting switches, or synthesis controls). Embedding these as explicit, stamped tokens keeps the information tied to the text and lets pipeline stages optionally act on it while otherwise preserving the segment verbatim.

## Syntax

- `{{text}}` — plain escaped segment, preserved verbatim.
- `{tag{text}}` — command-annotated escape. `tag` must match regex `[0-9a-z_]{0,16}`.
  - Internal commands: `tag` starting with `_` (e.g., `_mdf`) are reserved for pipeline internal use and are documented as such.

Examples:

- `{{hello}}` — plain escape
- `{url{http://www.github.com}}` — embed a URL as metadata
- `{_mdf{---}}` — internal markdown-formatting command (printer may expand at output)

## Design Constraints

- No nested `{...{...}}` parsing beyond the two-level `{tag{...}}` form; nested escapes are intentionally unsupported to keep parsing simple and robust.
- Tags limited to alphanumerics and underscore, up to 16 chars, to avoid wide character or injection complexities.
- Internal tags starting with `_` should be documented and minimized; stages should ignore unknown tags unless explicitly implemented.

## Implementation Notes

- Tokeniser: update `tokenize_line()`/`syllabify.py` to match `{{...}}` or `{tag{...}}` and to trim surrounding whitespace when wrapping escaped tokens.
- Printer: support expansion hooks for a small set of internal tags; otherwise preserve verbatim in `⟨escape:...⟩` metadata.
- Tests: include unit tests for recognition, whitespace handling, prohibited nesting, and internal-tag pass-through behavior.

## Security & Safety

- Internal command tags are not executed as code; they are declarative markers that pipeline stages explicitly handle. Do not add dynamic code evaluation hooks.

## Links

- Implementation CR: `docs/internal/cr/005-change-bracket-escapes-to-double-braces.md`

## Reviewed By

- (TBD)

<!-- Usage: This ADR proposes the command-annotated escape syntax. When accepted, CR-005 will implement it and follow-up PRs will add tests and docs. -->

