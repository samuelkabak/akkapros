## Unreleased

Commits since release `v1.0.1`:

- `b0d4fde` (2026-03-18) — Implement CR-003: Use rare bracket delimiters for escape markers (⟦ ⟧)
- `567eb35` (2026-03-18) — chore(scripts): add POSIX newline fixer (UTF-8-safe)
- `71d3679` (2026-03-18) — docs(internal): regenerate README; fix MD links/anchors; add CODE_OF_CONDUCT; add md link checker
- `47ce510` (2026-03-18) — docs: move ADR/CR/specs to docs/internal; add specs scaffold; update indexes script
- `fdc5961` (2026-03-18) — Add 3 CR and several ADRs, update ADR text for clarity
- `1b2d3ad` (2026-03-17) — Update old CR and README
- `132470f` (2026-03-17) — Add update indexes script to update CR and ADR indexes
- `750a5e8` (2026-03-17) — Add index to ADR README.md
- `3ff2cf8` (2026-03-17) — Complete CR docs and release notes for metrics updates
- `1879df9` (2026-03-17) — Harden DeltaC distance validation and align mora math
- `a2ff0eb` (2026-03-17) — Fix direct CLI script imports in atfparser and syllabifier
- `f17aa59` (2026-03-16) — Add CR structure and template and update ADR dates and template

- `CR-003` (2026-03-17) — Change escape delimiters from `‹ ›` to `⟦ ⟧` across the codebase and documentation; updated `OPEN_ESCAPE`/`CLOSE_ESCAPE` in constants, refactored usages in syllabification and prosody code, and updated tests and docs. See `docs/internal/cr/003-change-escape-delimiters.md` for details. Migration note: downstream scripts that hardcode the previous delimiters should replace `‹` → `⟦` and `›` → `⟧` where they were intended as escape markers.

- `CR-004` (2026-03-18) — Rename terminology from `repair/repaired/repairs` to `accentuation/accentuated/accentuations` across source code, JSON/CSV keys, table headings, logs, tests, and user-facing docs. This is a deliberate breaking change (no compatibility aliases).
	- Migration examples:
		- `result['repaired']` → `result['accentuated']`
		- `rep_total_morae` → `accentuated_total_morae`
		- `rep_sps_speech` → `accentuated_sps_speech`
		- `rep_ΔC_seconds` → `accentuated_ΔC_seconds`

- `CR-005` (2026-03-18) — Escape syntax migration from bracket escapes to CR-005 forms:
	- New preserved forms: `{{text}}` and `{tag{text}}` (tag regex `[0-9a-z_]{1,16}`)
	- Internal tags begin with `_` and are reserved for pipeline-internal handling
	- Nested escapes are intentionally unsupported
	- `syllabify.py`, `prosody.py`, and `print.py` updated to parse/preserve new forms
	- IPA printer now emits `⟨escape:{{...}}⟩` or `⟨escape:{tag{...}}⟩`
	- Added migration helper: `scripts/migrate-escapes.py`


