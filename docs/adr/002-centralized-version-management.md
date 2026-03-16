#---
Status: Accepted
Date: 2026-03-14
---

# 2. Centralized Version Management

## Context and Problem Statement

Version constants and display strings became fragmented across CLIs and modules, creating inconsistency risk and release overhead.

## Decision Drivers

- Single source of truth for version metadata
- Consistent `--version` output across all tools
- Lower release maintenance cost

## Considered Options

- Keep per-CLI/per-module version strings
- Centralize package metadata in `src/akkapros/__init__.py`
- Resolve version dynamically from packaging metadata only

## Decision Outcome

Chosen option: Centralize package metadata in `src/akkapros/__init__.py` and expose a shared display helper consumed by all CLIs.

## Pros and Cons of the Options

### Centralized package metadata

- Good, because one update changes all CLI version outputs
- Good, because display quality is standardized
- Bad, because CLIs depend on shared helper functions

### Per-file versions

- Good, because local independence
- Bad, because drift and inconsistent releases are likely
- Bad, because manual edits scale poorly

## Links

- Related: `src/akkapros/__init__.py`
- Related: `src/akkapros/cli/_cli_common.py`
