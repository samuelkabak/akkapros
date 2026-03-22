## Unreleased

Commits since release `v1.0.1`:

- `5649ee1` (2026-03-22) — Update the changelog and release notes
- `4adc337` (2026-03-22) — Fix punctuation regex errors (CR-012), update related docs
- `e6d171a` (2026-03-21) — Remove useless warnings and set tab replacement to 2 spaces
- `ca8fc03` (2026-03-21) — Implement CR-012: Enforce punctuation whitelist and configurable CLI extension
- `a4be85a` (2026-03-21) — Implement CR-011: Add format-validation guard to file-input CLIs
- `c3f993c` (2026-03-20) — Complete phoneprep and printer docs related to vowel coloring
- `510ed2c` (2026-03-20) — Implement CR-010: Refactor simple_safe_filename and phoneprep core
- `ab722d2` (2026-03-20) — Implement CR-009: Reorganize CLI common code and add `_gencode` generators
- `7b15eb1` (2026-03-20) — Restructure the CR folder to have one file per CR instead of a directory
- `6ecf357` (2026-03-20) — Add CR-009 and align the CR tasks with the template
- `76b4ddb` (2026-03-20) — Implement CR-008: Add end-to-end integration test with gold-standard metrics
- `50dc7cf` (2026-03-20) — Implement CR-007: Enforce POSIX EOF newline in all program outputs
- `5c17981` (2026-03-20) — Implement CR-006: Fix xfail in syllabifier tests, clean CR-004 untracked files
- `81e33ad` (2026-03-19) — Create specs files and review the package codebase
- `d72d991` (2026-03-18) — Implement CR-005: Change escaped-foreign-text delimiters from [ ] to {{ }}
- `b06c179` (2026-03-18) — Implement CR 004: Rename "repair" terminology to "accentuation"
- `ff44946` (2026-03-18) — Add scripts/update_unreleased.py: auto-generate release-notes/unreleased.md from git log
- `b0d4fde` (2026-03-18) — Implement CR-003: Use rare bracket delimiters for escape markers (âŸ¦ âŸ§)
- `567eb35` (2026-03-18) — chore(scripts): add POSIX newline fixer (UTF-8-safe)
- `71d3679` (2026-03-18) — docs(internal): regenerate README; fix MD links/anchors; add CODE_OF_CONDUCT; add md link checker
- `47ce510` (2026-03-18) — docs: move ADR/CR/specs to docs/internal; add specs scaffold; update indexes script
- `fdc5961` (2026-03-18) — Add 3 CR and several ADRs, update adr text for clarity.
- `1b2d3ad` (2026-03-17) — Update old CR and README
- `132470f` (2026-03-17) — Add update indexes script to update cr and adr indexes
- `750a5e8` (2026-03-17) — Add index to ADR README.md
- `3ff2cf8` (2026-03-17) — Complete CR docs and release notes for metrics updates
- `1879df9` (2026-03-17) — Harden DeltaC distance validation and align mora math
- `a2ff0eb` (2026-03-17) — Fix direct CLI script imports in atfparser and syllabifier
- `f17aa59` (2026-03-16) — Add CR structure and template and update ADR dates and template

## Summary (since v1.0.1)

- **Breaking:** JSON/CSV output keys renamed from `repair*` to `accentuated*` (CR-004). Migration: update downstream parsers to the new keys; examples and migration notes are in `release-notes/unreleased.md` and `docs/internal/cr/004-rename-repair-to-accentuation.md`.
- **Escape syntax changes:** escape delimiters moved to `⟦ ⟧` and new preserved forms `{{...}}` / `{tag{...}}` were introduced (CR-003, CR-005). Migration: run `scripts/migrate-escapes.py` on legacy files and update any tooling that matched the old delimiters.
- **Validation & punctuation control:** added a lightweight format-validation guard for all file-input CLIs and a punctuation allowlist with CLI extension options (CR-011, CR-012). Migration: test your pipelines with the default allowlist and adapt workflows that previously relied on permissive punctuation handling (see `docs/internal/cr/012-enforce-punctuation-whitelist-and-cli-extension.md`).
- **Tests & robustness:** added an end-to-end integration test with pinned gold-standard metrics and fixed syllabifier regressions; POSIX EOF newline normalization enforced across outputs (CR-008, CR-006, CR-007). Migration: no required action, but CI/test expectations may be stricter — re-run the test-suite locally after updating.
- **Refactors & tooling:** reorganized CLI common code and generators, extracted `phoneprep` core into `src/akkapros/lib/phoneprep.py`, and added scripts to update CR/ADR indexes and release notes (CR-009, CR-010). Migration: developers should re-run generator/build hooks as documented (see `pyproject.toml` `[tool.build]` generate hooks).

Other housekeeping and tooling:

- Added `scripts/update-indexes.py` and `scripts/update_unreleased.py` to regenerate `docs/internal` indexes and `release-notes/unreleased.md` from git history.
- Documentation reorganization: moved ADR/CR/specs to `docs/internal/` and regenerated internal README/indexes.


