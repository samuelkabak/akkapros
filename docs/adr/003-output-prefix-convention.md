---
Status: Accepted
Date: 2026-03-14
---

# 3. Output Prefix Convention

## Plain Summary

Use consistent file name prefixes for outputs so files are easy to find and sort.
This helps scripts and users locate generated files reliably.

## Context and Problem Statement

Most commands produce multiple related files. Ad hoc naming causes collisions and unclear artifact grouping.

## Decision Drivers

- Predictable output naming
- Easy grouping per run
- Simple automation for downstream steps

## Considered Options

- Let each output path be fully user-specified
- Use `--prefix` and optional `--outdir` as naming contract

## Decision Outcome

Chosen option: Standardize on `--prefix` + `--outdir`, with deterministic suffixes per stage.

## Pros and Cons of the Options

### `--prefix` + deterministic suffixes

- Good, because all stage outputs are discoverable
- Good, because automation and docs are simpler
- Bad, because suffix conventions must stay stable

### Fully custom output paths

- Good, because maximal flexibility
- Bad, because hard to teach and script consistently
- Bad, because artifact relationships are less obvious

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/fullprosmaker.md`
- Related: `docs/akkapros/phoneprep.md`

## Reviewed By

- Akkapros maintainers
