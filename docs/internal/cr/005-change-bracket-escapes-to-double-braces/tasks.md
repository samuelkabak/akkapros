title: Tasks for CR-005 — Change bracket escapes to double-braces

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

