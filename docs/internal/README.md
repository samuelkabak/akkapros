# Internal Documentation — Development Cycle

Purpose

- Central place for machine-oriented project records: Architecture Decision Records (ADRs), Change Requests (CRs), short requirements, and reviews.

Principles / Workflow

- ADR-first: Propose design changes as an ADR before changing behavior or files. Each ADR should explain motivation, alternatives considered, the decision, and consequences.
- CRs implement or coordinate changes that follow from ADRs (use CRs for breaking changes, broad refactors, or cross-cutting work). CR status workflow is `Draft -> Approved -> Done` for accepted work, or `Draft -> Rejected` for declined work. Use `Blocked` as a temporary status when a CR cannot be implemented or verified safely as written.
- Governance lookup budget rule: start from the relevant `docs/internal/*/index.md` page, the target record, and any records directly referenced by that target. Do not scan governance history from `001` upward by default.
- Summary-first lookup rule: when older context is needed, prefer index entries, front matter, headings, and summaries first. The default full-text reading budget is the target record, its directly referenced records, and at most 3 to 5 additional recent directly relevant CRs, plus only the directly relevant ADRs and REQs needed to resolve a concrete ambiguity or dependency. Expand beyond that budget only when a specific unresolved conflict or ambiguity remains.
- Minimal disclosure rule for LLM-assisted work: when sending repository governance or implementation context to a model, send the smallest sufficient slice first. If the current slice is insufficient, the next step is to request one smaller additional slice tied to a named ambiguity or dependency rather than bulk-loading broad surrounding history.
- CR self-containment rule: author CRs so that the CR is the primary implementation prompt. A contributor or implementing agent should normally be able to act on an instruction such as `implement CR-076` by reading the CR itself plus only the narrowly scoped additional material that the CR explicitly references as required context.
- Dependency-based CR sequencing rule: a later CR is blocked only when an earlier CR in a non-terminal state is a direct prerequisite, is explicitly referenced as governing or prerequisite, or shares the same active implementation surface in a way that leaves the contract ambiguous or conflicting. Unrelated earlier CRs do not block later work merely because their identifiers are lower. For example, `CR-020` not being `Done` does not by itself block `CR-075` unless the target CR directly depends on `CR-020` or the same unresolved contract surface.
- Controlled-test rule: unit tests, integration tests, and regression tests must not rely implicitly on mutable built-in default parameters for the behavior they are asserting. They must set the parameters needed for the targeted path explicitly through fixtures, test-local config, function arguments, or CLI overrides so the execution path is 100% controlled and not ambiguous. Tests whose explicit purpose is to verify defaults themselves are allowed, but they must be narrow and clearly identified as default-contract tests.
- Req: short, testable requirement documents describing what to implement. It is acceptable for `req/` to be empty until requirements are added.
- Internal software-management artifacts in `docs/internal/` are developer-facing only. User-facing package documentation such as `docs/akkapros/` pages and onboarding docs must not cite ADRs, CRs, REQs, review files, or `docs/internal/` paths. Public docs should describe package behavior directly rather than exposing internal governance records.
- Change-management rule: do not rewrite older accepted ADRs, REQs, or CRs as though a later decision had always been true. This applies to any future change that alters, narrows, removes, replaces, or reinterprets an earlier documented decision or contract. Preserve historical records and record the newer decision additively in new documents or explicit supersession notes, using short forward references when readers need help understanding the relationship between past and current state.
- Incremental precedence rule: ADRs, REQs, and CRs are additive and incremental. A newer higher-numbered record may narrow, replace, rehome, or otherwise override behavior previously approved by an older accepted record. That alone is not a blocker. For active implementation and verification, follow the newest directly relevant higher-numbered record while keeping the older record intact as historical context.
- Supersession hygiene: when a newer higher-numbered record changes behavior approved by an older record, make that relationship explicit with forward references, supersession notes, or linked rationale where needed. Do not silently ignore the older record, but do not treat its older behavior as still controlling once the newer record clearly replaces it.
- Lookback rule for spec writing: when drafting or updating an ADR, REQ, or CR, check the directly relevant earlier records to see whether the new document replaces or narrows an older decision or contract. Use index pages and summaries first, then read full text only for the smaller set of earlier records that materially constrain the new document. If the new document replaces or narrows older behavior, say so explicitly in the new document and name the superseded record or records.
- Prompt-decoupling rule: treat specification authoring and implementation execution as separate steps. The specification author assembles the contract into the CR. The implementing agent should not need to reconstruct that contract from scattered governance history unless the CR explicitly leaves a named dependency or ambiguity to inspect.

Blocked CR methodology

- `Blocked` means the CR is not executable as written: the contract is too weak, contradictory, mismatched to the codebase, governance-constrained, or otherwise not safely implementable/verifiable.
- A CR is also not executable yet if one or more earlier CRs in a non-terminal state are directly relevant prerequisites or leave the same implementation surface in an unresolved ambiguous state. Earlier CRs already marked `Done` or `Rejected` do not block later implementation, and unrelated earlier CRs do not block later work solely because they have lower identifiers.
- The source of truth for blocking information is the `# Implementation Blockers` section in the CR document.
- Implementers record concrete blocker entries there and set CR status to `Blocked` when they encounter blockers that prevent safe progress.
- A CR is not blocked merely because it conflicts with an older accepted ADR, REQ, or CR if the target CR or its directly linked newer higher-numbered governing records explicitly update or supersede that older behavior.
- Spec writers resolving a blocked CR must read the `# Implementation Blockers` section first, then repair the affected CR sections so the contract becomes implementable and testable.
- When a blocker is resolved by a spec rewrite, keep the blocker entry for history and append `Resolved on: YYYY-MM-DD` and `Resolution: <short description of the spec change that resolved it>`.
- If all blocker entries are resolved, change status from `Blocked` back to `Draft` unless a different status is explicitly requested.
- If any blocker remains unresolved, keep status as `Blocked`.

Directory layout

- `adr/` — ADR documents and `index.md`. Use the ADR template `000-adr-template.md` and the numeric prefix to order decisions (e.g., `023-rename-repair-to-accentuation.md`).
- `cr/` — Change Requests. Keep one file per CR using `NNN-short-kebab-title.md`, plus `index.md` and `000-cr-template.md`.
- `req/` — Short requirements and acceptance criteria. Use `000-req-template.md` when creating new requirement documents. Requirement docs are optional and may be added later.

- `review/` — Project and code reviews. Use `000-review-template.md` as a starting point. Review files should use a numeric prefix for ordering (e.g., `001-review.md` or `review-001.md`). Files beginning with `000-` are reserved for templates and ignored by indexers.

Naming & numbering

- ADRs, CRs, REQs, and reviews use short kebab-case filenames prefixed with a stable ordered identifier such as `NNN-short-kebab-title.md`.
- Identifier progression is base-36 by leading character group for stable ordering: `000` through `999`, then `A00`, `A01` ... `A99`, then `B00` ... `B99`, then `C00` ... `C99`, then `D00`, and so on. In other words, the first character advances through `0..9` and then `A..Z`; examples: after `999` comes `A00`, and after `C99` comes `D00`.
- ADR, CR, and REQ record filenames therefore use canonical forms such as `071-title.md`, `999-title.md`, and `A00-title.md`.
- Numbering within each document type (`adr/`, `cr/`, `req/`, `review/`) must be contiguous once identifiers are assigned. Do not leave permanent gaps such as `040` followed by `042` with no `041` record, or `A03` followed by `A05` with no `A04` record.
- If a number has already been referenced or effectively reserved, close the gap by adding a narrow placeholder or follow-up record rather than silently skipping it. Renumbering later documents is allowed only before references have spread and only when the renumber is low-risk.
- Refer to ADRs/CRs by their canonical identifier (e.g., `ADR-023`, `CR-004`, `CR-A00`) in code, tests, and commit messages.
- When committing an implementation for a CR, the commit subject must use this pattern: `Implement CR-{canonical CR identifier}: {CR title copy/paste}`.
- Review files also participate in the same identifier ordering contract. The generated review index accepts `review-001.md`, `001-review.md`, titled forms such as `002-frontmatter-data-review.md`, and higher-order variants such as `review-A00.md` or `A00-governance-review.md`.

Index generation

- Index pages (`docs/internal/*/index.md`) are generated/updated by the repository script: `python scripts/update-indexes.py`.
- Run the indexer after adding, renaming, or removing ADR/CR/Req files to keep indexes consistent. Review generated `index.md` pages before committing.
- The indexer treats malformed governance record filenames as an explicit tooling problem. It emits warnings to stderr and exits non-zero instead of silently omitting unsupported files.

Reviews: After adding or renaming review files, run `python scripts/update-indexes.py` to regenerate `docs/internal/review/index.md`. The indexer accepts `review-001.md`, `001-review.md`, and slugged forms such as `002-frontmatter-data-review.md`, and will skip template files prefixed with `000-`.

Housekeeping flow:

1. Add, rename, or remove the governance record using the canonical identifier format for its document type.
2. Run `python scripts/update-indexes.py`.
3. Resolve any warnings about malformed or unsupported governance filenames before proceeding.
4. Run `pytest tests/test_update_indexes_script.py tests/test_git_commit_cr_script.py -q` when changing governance tooling or its contract.
5. Review the generated `docs/internal/*/index.md` files before committing.

Templates

- Use the templates in this folder (`000-adr-template.md`, `000-cr-template.md`, `000-req-template.md`) as starting points. Keep templates minimal and focused on decision rationale and consequences.

Status, review & metadata

- All ADR/CR/REQ/review documents use YAML front matter at the top of the file.
- Front matter keys use lowercase snake_case names such as `adr_id`, `cr_id`, `req_id`, `review_id`, `created`, and `updated`.
- Add a clear `status` value in every ADR/CR/REQ/review record using the document-type-specific workflow already in use.
- When accepting a decision, add reviewer metadata and dates to the ADR/CR.
- ADRs should carry `adr_id`, `status`, `created`, and `updated` in front matter at minimum.
- CRs should carry `cr_id`, `status`, `priority`, `impact`, `created`, `updated`, and `implements` in front matter. Current CR statuses are `Draft`, `Blocked`, `Approved`, `Rejected`, and `Done`.
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
- Use index pages and direct references first; do not read large stretches of governance history unless a concrete ambiguity requires it.
- Write CRs so the requested change, acceptance criteria, boundaries, likely files, and verification path are understandable from the CR itself.
- When writing or updating tests, declare the parameters needed for the path under test explicitly; do not let regression or behavioral coverage inherit mutable runtime defaults unless the test is specifically about those defaults.
- Run `python scripts/update-indexes.py` and verify the generated indexes.
- Run the test suite for behavioral changes.

Agent guidance

- Custom repository agents and governance-aware prompts should encode the same bounded-context policy described above.
- Default behavior for governance-aware agents should be summary-first, relevance-first, and dependency-based rather than full-history scans or blanket checks that every earlier CR is `Done`.
- Default behavior for governance-aware agents should also be incremental-disclosure: send a minimal slice first, then ask for one additional targeted slice only if the current slice is insufficient.
- If an agent expands beyond the default lookup budget, it should do so only to resolve a specific ambiguity, dependency, or contract conflict it can name concretely.

Related governance changes

- [ADR-050](adr/050-bounded-governance-context-and-dependency-based-cr-sequencing.md)
- [CR-076](cr/076-optimize-governance-context-loading-and-agent-cr-responsibilities.md)

Contacts

- Maintainers and reviewer contacts are listed in `CONTRIBUTING.md`. Use the issue tracker to request reviews for ADR/CR proposals.
