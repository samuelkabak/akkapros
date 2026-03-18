# Internal Documentation — Development Cycle

Purpose
- Central place for machine-oriented project records: Architecture Decision Records (ADRs), Change Requests (CRs), and short Requirements/Specs.

Principles / Workflow
- ADR-first: Propose design changes as an ADR before changing behavior or files. Each ADR should explain motivation, alternatives considered, the decision, and consequences.
- CRs implement or coordinate changes that follow from ADRs (use CRs for breaking changes, broad refactors, or cross-cutting work). Mark CR status clearly (Draft / Proposed / Accepted / Done).
- Specs: short, testable requirement documents describing what to implement. It is acceptable for `specs/` to be empty until requirements are added.

Directory layout
- `adr/` — ADR documents and `index.md`. Use the ADR template `000-adr-template.md` and the numeric prefix to order decisions (e.g., `023-rename-repair-to-accentuation.md`).
- `cr/` — Change Requests. Organize each CR in its own folder with a `CR.md` and related artifacts. Keep the `index.md` up-to-date.
- `specs/` — Short requirements and acceptance criteria. Use `000-req-template.md` when creating new specs. Specs are optional and may be added later.

Naming & numbering
- ADRs and CRs use short kebab-case filenames prefixed with a 3-digit number for stable ordering: `NNN-short-kebab-title.md` or `NNN-short-kebab-title/CR.md`.
- Refer to ADRs/CRs by their canonical number (e.g., `ADR-023`, `CR-004`) in code, tests, and commit messages.

Index generation
- Index pages (`docs/internal/*/index.md`) are generated/updated by the repository script: `python scripts/update-indexes.py`.
- Run the indexer after adding, renaming, or removing ADR/CR/Spec files to keep indexes consistent. Review generated `index.md` pages before committing.

Templates
- Use the templates in this folder (`000-adr-template.md`, `000-cr-template.md`, `000-req-template.md`) as starting points. Keep templates minimal and focused on decision rationale and consequences.

Status, review & metadata
- Add a short `Status:` line in every ADR/CR/Spec (`Draft`, `Proposed`, `Accepted`, `Done`).
- When accepting a decision, add reviewer metadata and dates to the ADR/CR.

Unicode & file-encoding policy
- This project is sensitive to Unicode. All files must be UTF-8 encoded and editors/processes must preserve Unicode characters.
- Scripts and automation must read and write files using UTF-8 encoding explicitly. Avoid tools that normalize or strip Unicode glyphs.
- If you encounter replacement characters (�) or missing glyphs, restore the affected file from the last known-good commit and report the incident in an issue.

Quick contributor checklist
- Propose an ADR for large or breaking changes before implementation.
- Create or update a CR when implementing an ADR or coordinating a breaking change.
- Add specs when formalizing requirements (optional for now).
- Run `python scripts/update-indexes.py` and verify the generated indexes.
- Run the test suite for behavioral changes.

Contacts
- Maintainers and reviewer contacts are listed in `CONTRIBUTING.md`. Use the issue tracker to request reviews for ADR/CR proposals.
