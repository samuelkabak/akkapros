# Change Request: Change escaped-foreign-text delimiters from [ ] to {{ }}

CR-ID: CR-005
Status: Approved
Priority: Medium
Created: 2026-03-18
Updated: 2026-03-18
Implements: ADR-024
---

# Summary

Change the pipeline's escaped-foreign-text delimiters from square brackets (`[` `]`) to double-braces (`{{` `}}`) to avoid conflicts with Markdown links and improve clarity in converted outputs. Include a small whitespace-normalization fix so escaped segments never introduce duplicate spaces in final repaired output.

# Motivation

- Square brackets frequently appear in Markdown and other contexts, causing accidental link parsing or ambiguous tokenisation.
- Using `{{`/`}}` reduces collisions and reads clearly as an escape marker.
- While making this mechanical change, fix the observed extra-space bug when bracketed segments appear adjacent to words.

# Proposal

1. Replace IGNORE naming with PRESERVE naming in shared constants and parser variables (e.g., `OPEN_PRESERVE`, `CLOSE_PRESERVE`, `OPEN_PRESERVE_CHAR`, `CLOSE_PRESERVE_CHAR`).
2. Extend the escape grammar to allow optional command tags using the syntax `{command{text}}` in addition to plain `{{text}}` escapes. The allowed forms are:

- `{{text}}` — plain escaped segment (no command tag), preserves previous double-brace behaviour.
- `{tag{text}}` — command-annotated escape where `tag` matches the regex `[0-9a-z_]{0,16}`. Examples: `{{hello}}`, `{url{http://www.github.com}}`, `{meta1{some data}}`.

	- Tags that begin with an underscore are internal commands meant for the pipeline's internal processing (not intended for external consumers). Example: `{_mdf{---}}` — an internal markdown-formatting command that the `printer` may expand at output time.

3. Update tokenisation in `syllabify.py` to recognise the new forms. Nested bracket-level parsing (the previous `split_by_brackets_level3()` behaviour which supported up to 3 nested square-bracket levels, e.g. `[a[b[c]d]e]`) is deprecated: the new escape syntax is intentionally simple and rare, and nested escape blocks will not be supported. Parser logic should therefore accept only the two-level `{tag{...}}` pattern or `{{...}}` and treat any deeper nesting as literal text or an error.
4. Ensure `tokenize_line()` and `syllabify_text()` wrap escape tokens without capturing surrounding whitespace; trim leading/trailing whitespace inside tokens before wrapping with `OPEN_ESCAPE`/`CLOSE_ESCAPE`.
4. Update `prosody.py` assembly logic to avoid inserting an extra space when an escaped token already supplies spacing (normalize at join-time, not at capture-time).
6. Add regression tests showing the previous extra-space case and examples with Markdown links to ensure no regressions. Add tests for the new `{tag{text}}` forms, including internal-tag cases beginning with `_`.
7. Update documentation and release notes describing the migration and how to convert existing datasets (simple `sed` or small script included in CR tasks). Create a preparatory ADR describing the new command-escape functionality and rationale; reference that ADR in this CR.

# Scope & Impact

- Files impacted: `src/akkapros/lib/constants.py`, `src/akkapros/lib/syllabify.py`, `src/akkapros/lib/prosody.py`, tests in `tests/` and any CLI wrappers that parse/print escaped segments.
- New parser/formatting logic: `src/akkapros/lib/constants.py`, `src/akkapros/lib/syllabify.py` (tokeniser), `src/akkapros/lib/prosody.py`, `src/akkapros/lib/printer.py` (escape-serialization), tests in `tests/`, and any CLI wrappers that parse/print escaped segments.
- Backwards compatibility: This is a visible output change; users consuming existing `*_syl.txt` / `*_tilde.txt` files must be informed and provided a migration note.

# Acceptance criteria

- New tests pass that assert `{{ ... }}` is preserved verbatim and no duplicated spaces appear in repaired output.
- No remaining code references to `[`/`]` as ignore-delimiters (except migration docs).
- Documentation and changelog updated with migration steps and rationale.
 - New tests pass that assert `{{ ... }}` and `{tag{...}}` forms are preserved verbatim (or processed per tag rules) and no duplicated spaces appear in accentuated output.
 - Tests cover internal tags starting with `_` and verify pipeline-internal handling (pass-through or expansion as specified).
 - No remaining code references to `[`/`]` as ignore-delimiters (except migration docs).
 - Nested three-level bracket parsing (`split_by_brackets_level3`) is removed or disabled; tests demonstrate that nested escapes are not supported.
 - Documentation and changelog updated with migration steps and rationale; the new preparatory ADR is referenced.

# Documentation

Update all user-facing documentation (CLI help, GETTING_STARTED, README, and module docs) to explain the new escape syntax and its behavior. Specifically, document both `{{text}}` and `{tag{text}}` forms, describe tag rules and internal-tag conventions (leading `_`), and explain that escaped content will not be syllabified as Akkadian; it will be preserved verbatim through syllabification and prosody stages unless an internal tag triggers a defined expansion at print time. Provide examples:

Example
~~~~~~~
Input: šar gimir {{English word, email@example.com}} bānû

Output: šar¦gi·mir¦⟦ {{English word, email@example.com}} ⟧bā·nû¦

Note: because this changes output format, document migration steps for users who programmatically parse existing pipeline outputs.

Quick list of docs to update in `docs/akkapros/` (scan done):

- `docs/akkapros/syllabifier.md` (escape handling and tokenisation)
- `docs/akkapros/prosody-realization-algorithm.md` (escaped chunks and prosody interaction)
- `docs/akkapros/printer.md` (serialization, internal tag expansion rules)
- `docs/akkapros/prosmaker.md` and `docs/akkapros/fullprosmaker.md` (pipeline notes and CLI options)

Add a short implementation note in each file describing `{tag{text}}` syntax, allowed tag regex `[0-9a-z_]{0,16}`, and that tags beginning with `_` are internal-only commands.

Printer / IPA output
--------------------
The project's IPA/printing module (`printer.py`) is also affected: it emits IPA-formatted output where escaped segments currently appear wrapped in angle-marked metadata (for example: `ʃar.gi.mir.ˈdadː.meː.baː.nuː ⟨escape:[jugtvvv^èè]⟩ kib.ˈraːː.ti ⟨ellipsis⟩ | ⟨linebreak⟩ ‖`). As part of this CR we must ensure the IPA printer preserves the new `{{...}}` escapes and expresses them in its metadata in the same verbatim form (e.g., `⟨escape:{{jugtvvv^èè}}⟩`).

Example (IPA printer)
~~~~~~~~~~~~~~~~~~~~~
Before:

	ʃar.gi.mir.ˈdadː.meː.baː.nuː ⟨escape:[jugtvvv^èè]⟩ kib.ˈraːː.ti ⟨ellipsis⟩ | ⟨linebreak⟩ ‖

After (expected):

	ʃar.gi.mir.ˈdadː.meː.baː.nuː ⟨escape:{{jugtvvv^èè}}⟩ kib.ˈraːː.ti ⟨ellipsis⟩ | ⟨linebreak⟩ ‖

Notes:
- Update the printer's escape-serialization code to look for the new PRESERVE constants and to avoid inserting extra spaces when serialising surrounding tokens.
- Add a regression test for printer output that verifies `escape:{{...}}` appears exactly and that no duplicate spaces are introduced in adjacent IPA tokens.

Rollout plan
------------
1. Implement constants + tokenizer changes and whitespace fix in a single PR.
2. Add regression tests and run full test suite.
3. Update docs and add a small migration helper script.
4. Merge and announce breaking change in release notes.

---

# Tasks

## Implementation

- [x] [x] Draft CR (done) — create `CR.md` describing change and acceptance criteria.
- [x] Add `tasks.md` (this file) listing actionable steps and tests.
- [x] Repo scan: search for `OPEN_IGNORE`, `CLOSE_IGNORE`, `[` and `]` usages to enumerate affected modules.
- [x] Implement constants change: update `src/akkapros/lib/constants.py` to set `OPEN_IGNORE='{{'` and `CLOSE_IGNORE='}}'`.
- [x] Update tokenizer: update `src/akkapros/lib/syllabify.py` tokenisation to recognise `{{ ... }}` and the new `{tag{...}}` form, trimming surrounding whitespace when wrapping escape tokens. Do not implement multi-level nested bracket parsing — `split_by_brackets_level3()` may be removed/disabled.
- [x] Fix whitespace bug: ensure `tokenize_line()`/`syllabify_text()` and `prosody.py` assemble output without duplicating spaces around escaped segments.
- [x] Add migration helper: `scripts/migrate-escapes.py` showing how to update existing `*_syl.txt`/`*_tilde.txt` files.
- [x] Open PR with implementation, link this CR, and request review.

## Tests

- [x] Add regression tests: include the reported extra-space example and Markdown-link adjacent cases in `tests/`.
- [x] Add regression tests for `printer.py` to assert exact `⟨escape:...⟩` output and no duplicated spaces in IPA lines.
- [x] Run full test suite and adjust until green.

## Documentation

- [x] Update docs: `GETTING_STARTED.md`, CLI help, and changelog/release notes.
- [x] Update `docs/akkapros/`: `syllabifier.md`, `prosody-realization-algorithm.md`, `printer.md`, `prosmaker.md`, `fullprosmaker.md` to describe the `{tag{...}}` syntax, tag regex `[0-9a-z_]{0,16}`, and internal-tag convention (leading `_`).
- [x] Document escape behaviour across all user-facing documentation and CLI help: explain that `{{text}}` and `{tag{...}}` forms are preserved verbatim (unless a known internal tag triggers an expansion) and will not be syllabified as Akkadian; add examples and migration guidance.
- [x] Update `printer.py` (IPA output) to emit `⟨escape:{{...}}⟩` or `⟨escape:{tag{...}}⟩` metadata and avoid inserting duplicate spaces around escaped segments.

## Review

- [x] Code review
- [x] Verify acceptance criteria

## Notes

- [x] This is a visible output format change; tag as a breaking change in release notes.
- [x] Prefer to implement constants and whitespace fix together in a single PR to avoid mixed-format outputs in intermediate commits.
