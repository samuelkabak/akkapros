# Internal Documentation — Development Cycle

Purpose
- Central place for machine-oriented project records: Architecture Decision Records (ADRs), Change Requests (CRs), short requirements, and reviews.

Principles / Workflow
- ADR-first: Propose design changes as an ADR before changing behavior or files. Each ADR should explain motivation, alternatives considered, the decision, and consequences.
- CRs implement or coordinate changes that follow from ADRs (use CRs for breaking changes, broad refactors, or cross-cutting work). Mark CR status clearly (Draft / Proposed / Accepted / Done).
- Req: short, testable requirement documents describing what to implement. It is acceptable for `req/` to be empty until requirements are added.
- Change-management rule: do not rewrite older accepted ADRs, REQs, or CRs as though a later decision had always been true. This applies to any future change that alters, narrows, removes, replaces, or reinterprets an earlier documented decision or contract. Preserve historical records and record the newer decision additively in new documents or explicit supersession notes, using short forward references when readers need help understanding the relationship between past and current state.

Directory layout
- `adr/` — ADR documents and `index.md`. Use the ADR template `000-adr-template.md` and the numeric prefix to order decisions (e.g., `023-rename-repair-to-accentuation.md`).
- `cr/` — Change Requests. Keep one file per CR using `NNN-short-kebab-title.md`, plus `index.md` and `000-cr-template.md`.
- `req/` — Short requirements and acceptance criteria. Use `000-req-template.md` when creating new requirement documents. Requirement docs are optional and may be added later.

- `review/` — Project and code reviews. Use `000-review-template.md` as a starting point. Review files should use a numeric prefix for ordering (e.g., `001-review.md` or `review-001.md`). Files beginning with `000-` are reserved for templates and ignored by indexers.

Naming & numbering
- ADRs and CRs use short kebab-case filenames prefixed with a 3-digit number for stable ordering: `NNN-short-kebab-title.md`.
- Refer to ADRs/CRs by their canonical number (e.g., `ADR-023`, `CR-004`) in code, tests, and commit messages.
- When committing an implementation for a CR, the commit subject must use this pattern: `Implement CR-{CR number NNN}: {CR title copy/paste}`.

Index generation
- Index pages (`docs/internal/*/index.md`) are generated/updated by the repository script: `python scripts/update-indexes.py`.
- Run the indexer after adding, renaming, or removing ADR/CR/Req files to keep indexes consistent. Review generated `index.md` pages before committing.

Reviews: After adding or renaming review files, run `python scripts/update-indexes.py` to regenerate `docs/internal/review/index.md`. The indexer accepts both `review-001.md` and `001-review.md` naming patterns and will skip template files prefixed with `000-`.

Templates
- Use the templates in this folder (`000-adr-template.md`, `000-cr-template.md`, `000-req-template.md`) as starting points. Keep templates minimal and focused on decision rationale and consequences.

Status, review & metadata
- All ADR/CR/REQ/review documents use YAML front matter at the top of the file.
- Front matter keys use lowercase snake_case names such as `adr_id`, `cr_id`, `req_id`, `review_id`, `created`, and `updated`.
- Add a clear `status` value in every ADR/CR/REQ/review record (`Draft`, `Proposed`, `Accepted`, `Done`, or the document-type-specific equivalent already in use).
- When accepting a decision, add reviewer metadata and dates to the ADR/CR.
- ADRs should carry `adr_id`, `status`, `created`, and `updated` in front matter at minimum.
- CRs should carry `cr_id`, `status`, `priority`, `impact`, `created`, `updated`, and `implements` in front matter.
- REQs should carry `req_id`, `status`, `priority`, `impact`, `created`, and `updated` in front matter.
- Reviews should carry `review_id`, `status`, `created`, `updated`, `reviewer`, and `scope` in front matter.
- If an older accepted document is no longer current, prefer adding an explicit supersession note or a short historical-reference paragraph instead of changing the original decision text to match the newer state.

Unicode & file-encoding policy
- This project is sensitive to Unicode. All files must be UTF-8 encoded and editors/processes must preserve Unicode characters.
- Scripts and automation must read and write files using UTF-8 encoding explicitly. Avoid tools that normalize or strip Unicode glyphs.
- If you encounter replacement characters (�) or missing glyphs, restore the affected file from the last known-good commit and report the incident in an issue.

Quick contributor checklist
- Propose an ADR for large or breaking changes before implementation.
- Create or update a CR when implementing an ADR or coordinating a breaking change.
- Add requirement documents when formalizing requirements (optional for now).
- For any later change that impacts the meaning or scope of older internal records, add a new decision record and cross-link the older documents rather than editing the past out of them.
- Run `python scripts/update-indexes.py` and verify the generated indexes.
- Run the test suite for behavioral changes.

Contacts
- Maintainers and reviewer contacts are listed in `CONTRIBUTING.md`. Use the issue tracker to request reviews for ADR/CR proposals.
