---
adr_id: ADR-032
status: Accepted
created: 2026-03-28
updated: 2026-03-29
superseded_by: null
---

# 032. Internal Doc Frontmatter Schema

## Plain Summary

All internal ADR, CR, REQ, and review documents shall use YAML front matter
with snake_case metadata keys. The schema shall be consistent enough that
humans and tooling can read document identity, status, and lifecycle dates from
one predictable place.

TL;DR: one frontmatter style for every internal record.

## Context and Problem Statement

The current internal documentation set mixes two metadata styles. ADRs already
use YAML front matter, but CRs, REQs, and reviews still keep metadata as ad hoc
top-of-file lines below the title. Even within that older style, key naming is
inconsistent (`CR-ID`, `REQ-ID`, `Review ID`, `Date`, `Created`, `Updated`).

This inconsistency makes the internal records harder to scan, harder to parse,
and harder to evolve coherently. It also leaves ADR metadata poorer than the
other document types because ADRs currently lack explicit `adr_id` and
`created` fields.

## Decision Drivers

- Consistent machine-readable metadata across internal records
- Clear document identity at the top of every file
- Predictable key naming for future tooling
- Minimal disruption to existing document bodies and historical meaning

## Considered Options

- Option A — Keep the mixed metadata styles and only fix templates going forward. Rejected because the historical set would remain inconsistent.
- Option B — Convert ADR, CR, REQ, and review documents to YAML front matter with snake_case keys and define a minimal schema per type. Chosen because it standardizes both templates and active records.
- Option C — Create one universal frontmatter schema with many optional fields for every document type. Not chosen because it adds noise and invites empty metadata.

## Decision Outcome

Choose Option B.

All ADR, CR, REQ, and review documents under `docs/internal/` shall use YAML
front matter. Frontmatter keys shall use lowercase snake_case naming.

The minimum metadata keys are:

- ADR: `adr_id`, `status`, `created`, `updated`
- CR: `cr_id`, `status`, `priority`, `impact`, `created`, `updated`, `implements`
- REQ: `req_id`, `status`, `priority`, `impact`, `created`, `updated`
- Review: `review_id`, `status`, `created`, `updated`, `reviewer`, `scope`

For legacy ADRs that previously stored only one `Date` value, that historical
date shall be preserved as both `created` and `updated` unless a more precise
creation date is already documented elsewhere.

This decision standardizes metadata location and key naming only. It does not
change the required section headers or the substantive meaning of older records.

## Pros and Cons of the Options

### Chosen Option

- Pros: makes metadata extraction uniform across all internal docs
- Pros: removes inconsistent key styles such as `CR-ID` vs `Review ID`
- Pros: enriches ADR metadata without expanding document bodies
- Pros: keeps the schema minimal and document-type-specific
- Cons: requires touching a large number of existing internal docs
- Cons: legacy documents with incomplete history can only approximate `created`

### Other Options

- Option A:
  - Pro: smallest immediate change
  - Con: preserves long-term inconsistency in the active corpus
- Option C:
  - Pro: one schema for every type
  - Con: too many empty or irrelevant fields per document

## Implications and Consequences

- Templates for ADR, CR, REQ, and review documents must be updated.
- Existing internal documents should be normalized to the new frontmatter style.
- `docs/internal/README.md` should describe the schema and naming convention.
- Index files may need regeneration after any file additions or renames, but the metadata conversion itself does not require renaming records.

## Links

- [docs/internal/README.md](../README.md)
- [docs/internal/adr/000-adr-template.md](000-adr-template.md)
- [docs/internal/cr/000-cr-template.md](../cr/000-cr-template.md)
- [docs/internal/req/000-req-template.md](../req/000-req-template.md)
- [docs/internal/review/000-review-template.md](../review/000-review-template.md)

## Implementation Notes (optional)

- Keep section headers unchanged while migrating metadata into front matter.
- Preserve legacy status values unless a record already documents a more precise replacement.
- For historical records, prefer preserving the old date semantics over inventing new chronology.

## Reviewed By

- Pending maintainer review
