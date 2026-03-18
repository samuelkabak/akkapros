---
Status: Accepted
Date: 2026-03-13
---

# 12. Phoneprep Coverage and Sidecars

## Plain Summary

Keep sidecar files (extra data) for phoneprep and TTS so the main pipeline stays focused.
Sidecars store mapping and extra annotations used only by synthesis tools.

## Context and Problem Statement

Building MBROLA-compatible resources requires broad diphone coverage and reliable segmentation metadata, not only a readable recording script.

## Decision Drivers

- Coverage-oriented recording material generation
- Deterministic sidecar artifacts for segmentation
- Human-friendly recording workflow support

## Considered Options

- Emit only a plain recording text
- Emit script plus manifest/diphone/word sidecars and optional HTML helper

## Decision Outcome

Chosen option: Keep `phoneprep` as coverage optimizer with sidecar outputs and optional recording helper HTML for operational consistency.

## Pros and Cons of the Options

### Script + sidecars + helper

- Good, because segmentation and downstream tooling become automatable
- Good, because recording workflow is less error-prone
- Bad, because output set is larger and more complex

### Script only

- Good, because minimal output surface
- Bad, because downstream alignment must be recreated manually

## Implications and Consequences

- Keep implementation, tests, and docs aligned with this decision when related changes are introduced.
- Treat changes that alter this decision's user-facing behavior as release-note-worthy updates.

## Links

- Related: `docs/akkapros/phoneprep.md`
- Related: `docs/akkapros/mbrola-voice-prep.md`

## Reviewed By

- Akkapros maintainers
