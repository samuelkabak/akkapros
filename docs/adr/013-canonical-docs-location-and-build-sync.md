# 13. Canonical Docs Location and Build Sync

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

## Links

- Related: `scripts/sync_docs.py`
- Related: `scripts/build_package.py`
- Related: `src/akkapros/docs/README.md`
