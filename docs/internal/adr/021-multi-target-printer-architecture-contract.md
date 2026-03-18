---
Status: Accepted
Date: 2026-03-17
---

# 21. Multi-Target Printer Architecture Contract

## Plain Summary

Define a simple printer API that takes pivot text and options and returns several output types.
Keep the printer contract stable so other tools can rely on it.

## Context and Problem Statement

`printer.py` is the single stage that converts pivot-format prosody output into multiple user-facing representations. Scholars, phoneticians, and synthesis workflows need different renderings from the same source without divergence in meaning.

## Decision Drivers

- One canonical input (`*_tilde.txt`) for all renderers
- Deterministic rendering across formats
- Clear separation between prosody computation and display/transliteration policy
- Support for both human-readable and synthesis-oriented outputs

## Considered Options

- Keep one output format only and require external converters
- Use one centralized printer with multiple format backends
- Duplicate formatting logic in each CLI command

## Decision Outcome

Chosen option: Keep a dedicated, centralized printer architecture where one pivot input is rendered to acute, bold, IPA, XAR, and MBROLA outputs through a shared library (`src/akkapros/lib/print.py`) and a thin CLI wrapper.

## Pros and Cons of the Options

### Centralized multi-target printer (chosen)

- Good, because all outputs derive from one semantic source
- Good, because display policy stays in one code path
- Good, because new output formats can be added without changing upstream stages
- Bad, because the printer module becomes a high-impact integration point

### Single format only

- Good, because maintenance is simpler
- Bad, because users must build fragile custom converters

### Duplicated formatters across CLIs

- Good, because local changes are isolated in appearance
- Bad, because behavior drifts and bugs are duplicated

## Implications and Consequences

- Printer output policy changes are contract-sensitive and must be documented in release notes.
- New output modes should be added in the shared printer library first, then surfaced in CLI docs/tests.

## Links

- Code: `src/akkapros/lib/print.py`
- CLI: `src/akkapros/cli/printer.py`
- CLI: `src/akkapros/cli/fullprosmaker.py`
- Doc: `docs/akkapros/printer.md`
- Doc: `docs/internal/adr/011-multi-format-printer-outputs.md`

## Reviewed By

- Akkapros maintainers

