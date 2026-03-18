---
Status: Accepted
Date: 2026-03-03
---

# 11. Multi-Format Printer Outputs

## Plain Summary

The printer stage creates several output formats (IPA, markup, TTS-ready) from the same pivot file.
This keeps output rules in one place and serves different users without changing the pipeline.

## Context and Problem Statement

Different users need different surface representations (philological reading, computational export, synthesis-oriented transcription).

## Decision Drivers

- One canonical transformed input for rendering
- Support scholarly and engineering workflows
- Keep output generation deterministic

## Considered Options

- Provide one output format only
- Provide multiple output formats from one printer stage

## Decision Outcome

Chosen option: Keep a dedicated printer stage producing acute, bold, IPA, XAR, and MBROLA-oriented outputs from the same pivot input.

## Pros and Cons of the Options

### Multi-format printer

- Good, because one pipeline serves multiple audiences
- Good, because format policy remains centralized
- Bad, because output policy requires sustained documentation

### Single output format

- Good, because reduced maintenance
- Bad, because users must build custom converters

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/printer.md`
- Related: `docs/akkapros/xar-script.md`

## Reviewed By

- Akkapros maintainers

