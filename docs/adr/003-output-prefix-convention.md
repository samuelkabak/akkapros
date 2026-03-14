# 3. Output Prefix Convention

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

## Links

- Related: `docs/akkapros/fullprosmaker.md`
- Related: `docs/akkapros/phoneprep.md`
