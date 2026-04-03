---
adr_id: ADR-037
status: Proposed
created: 2026-04-03
updated: 2026-04-03
superseded_by: null
---

# 37. Centralized Help Message Registry for CLI and Config Docs

## Plain Summary

Maintain one canonical registry of user-facing help strings in
`src/akkapros/lib/helpmsg.py` and reuse it for both CLI parser help and
documented config-file emission.

## Context and Problem Statement

The package now emits documented YAML config files and also exposes many CLI
flags across related tools. Repeating help text independently in multiple CLI
modules and again in config generation creates predictable drift.

The new config-file workflow makes that drift more visible because users compare
CLI `--help` with `default.yaml` and `confwriter` output directly.

## Decision Drivers

- Keep user-facing wording consistent across surfaces.
- Make config comments richer without duplicating maintenance effort.
- Reduce drift risk when option wording changes.
- Preserve thin CLI wrappers by moving descriptive text to shared library code.

## Decision Outcome

Chosen option: centralize shared help strings in `src/akkapros/lib/helpmsg.py`.

Concretely:

- Canonical help text lives in one shared library module.
- CLI modules reuse that text for config-eligible options.
- Config emission reuses the same text for YAML comments.
- Related wording families should use consistent terminology.

## Consequences

- Help-text edits become simpler and less error-prone.
- Generated config files can include richer inline documentation without adding
  a second documentation source.
- The package now has an explicit dependency from CLI argument declarations and
  config emission to a shared help registry.

## Links

- Related ADR: [ADR-001](001-cli-lib-separation.md)
- Related ADR: [ADR-036](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- Related CR: [CR-030](../cr/030-add-package-wide-yaml-config-and-confwriter.md)
- Related CR: [CR-031](../cr/031-centralize-cli-help-text-for-cli-and-config-doc-emission.md)
