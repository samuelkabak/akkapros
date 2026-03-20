# Change Request System

This directory contains project Change Requests (CRs).

Each CR is a single Markdown file that includes:
- CR description
- tasks checklist
- optional notes

Use `index.md` to browse all CRs.

## File Layout

- Template: `docs/internal/cr/000-cr-template.md`
- CR files: `docs/internal/cr/NNN-short-kebab-title.md`
- Index: `docs/internal/cr/index.md`

Example:

- `docs/internal/cr/001-extend-metrics-output.md`
- `docs/internal/cr/002-fix-mora-stats-with-tilde.md`

## Naming Rules

- Use a 3-digit numeric prefix: `NNN-`
- Use lowercase kebab-case title
- Keep titles short and descriptive

## Status Values

Use `Status:` in each CR:
- `Draft`
- `Approved`
- `Done`

## Workflow

1. Determine the next CR number.
2. Copy `000-cr-template.md` to `NNN-short-kebab-title.md`.
3. Fill in Summary, Scope, Design, and Acceptance Criteria.
4. Add or update the Tasks section in the same file.
5. Add optional notes at the bottom if needed.
6. Run `python scripts/update-indexes.py`.
7. Reference the CR ID in PRs and commits.

## Indexing

`scripts/update-indexes.py` rebuilds `docs/internal/cr/index.md` from `docs/internal/cr/*.md` (excluding `index.md` and `000-cr-template.md`).

## Assistant Guidance

When creating a new CR:
1. Create one file: `docs/internal/cr/NNN-short-kebab-title.md`.
2. Use `docs/internal/cr/000-cr-template.md`.
3. Keep tasks and notes in the same file.
4. Update the CR index.

