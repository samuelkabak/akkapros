---
Status: Accepted
Date: 2026-03-06
---

# 13. Canonical Docs Location and Build Sync

## Plain Summary

Keep the main docs in `docs/` and make sure generated docs match the code by syncing during builds.
This makes documentation reliable and easy to update.

## Context and Problem Statement

The project needs both repository-facing docs and packaged docs. Manually maintaining two editable copies causes drift.

## Decision Drivers

- Single canonical documentation source
- Keep packaged docs available when needed
- Avoid manual duplication

## Considered Options

- Maintain two editable docs trees
- Keep top-level docs canonical and sync into package docs before build

## Decision Outcome

Chosen option: Canonical docs live under `docs/`, and packaging sync copies `docs/akkapros` into `src/akkapros/docs` via build scripts.

## Pros and Cons of the Options

### Canonical top-level docs + sync

- Good, because authoring has one source of truth
- Good, because package data can still include docs
- Bad, because build process must run sync step

### Two editable trees

- Good, because no sync step required
- Bad, because drift is likely and expensive to clean up

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `scripts/sync_docs.py`
- Related: `scripts/build_package.py`
- Related: `src/akkapros/docs/README.md`

## Reviewed By

- Akkapros maintainers

