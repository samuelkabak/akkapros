---
Status: Accepted
Date: 2026-03-17
---

# 19. IPA Output Variant Policy

## Plain Summary

Document the IPA variants the printer can produce and let users choose which IPA style to use.
This keeps IPA outputs predictable and configurable.

## Context and Problem Statement

Akkadian phonetic details (especially emphatics and proto-Semitic residue) are uncertain. Users need IPA outputs for different research goals, but the pipeline must remain deterministic and explicit about which mapping is used.

## Decision Drivers

- Represent uncertainty without pretending a single definitive reconstruction
- Keep IPA output reproducible and scriptable
- Support comparative and pedagogical workflows with selectable modes
- Avoid silent mapping changes

## Considered Options

- One fixed IPA mapping for all outputs
- Multiple selectable IPA mappings with explicit CLI flags
- Omit IPA output and keep only orthographic renderings

## Decision Outcome

Chosen option: Provide multiple IPA variants through explicit options (including proto-Semitic handling and circumflex-hiatus behavior) while keeping defaults stable and documented.

## Pros and Cons of the Options

### Multi-variant IPA policy (chosen)

- Good, because uncertainty is surfaced rather than hidden
- Good, because users can choose representation fit for purpose
- Good, because mappings are explicit in code and CLI
- Bad, because output compatibility must be managed carefully

### Single IPA mapping

- Good, because minimal complexity
- Bad, because overcommits to one interpretation and limits use cases

### No IPA output

- Good, because avoids phonetic controversy
- Bad, because removes a core analysis and synthesis interface

## Implications and Consequences

- IPA mapping tables are part of the public behavior and should be versioned with release notes when changed.
- Printer documentation must keep mode semantics precise and example-driven.

## Links

- Code: `src/akkapros/lib/print.py`
- CLI: `src/akkapros/cli/printer.py`
- CLI: `src/akkapros/cli/fullprosmaker.py`
- Doc: `docs/akkapros/printer.md`
- Doc: `docs/akkapros/xar-script.md`
- Research notes: `tmp/research-notes.md` (004, 005, 038, 078)

## Reviewed By

- Akkapros maintainers

