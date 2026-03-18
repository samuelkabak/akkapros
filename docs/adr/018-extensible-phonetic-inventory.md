---
Status: Accepted
Date: 2026-03-17
---

# 18. Extensible Phonetic Inventory

## Plain Summary

Keep the list of vowels and consonants in one place and allow extra characters via CLI options.
This makes it easy to support foreign characters or experiments.

## Context and Problem Statement

Multiple stages depend on consistent vowel/consonant classification. Hardcoding character sets per module causes drift and makes extension to mixed-language data difficult.

## Decision Drivers

- Single source of truth for phonetic sets
- Consistent behavior across syllabification, prosody, metrics, and printing
- Support controlled extension with foreign characters
- Minimize duplicated logic

## Considered Options

- Keep per-module hardcoded inventories
- Centralize inventories in shared constants and expose extension knobs
- Load inventories dynamically from external config files only

## Decision Outcome

Chosen option: Centralize core Akkadian inventories in shared constants and allow controlled per-run extension through CLI options (`--extra-vowels`, `--extra-consonants`).

## Pros and Cons of the Options

### Centralized + extensible inventory (chosen)

- Good, because all modules use the same base phonetic assumptions
- Good, because extension does not require code edits
- Good, because behavior is traceable and testable
- Bad, because extensions can mask input errors if overused

### Per-module inventories

- Good, because local independence
- Bad, because drift and inconsistent classification bugs

### External config only

- Good, because maximum flexibility
- Bad, because operational complexity and weaker defaults

## Implications and Consequences

- Adding/removing base phonemes must be coordinated across docs, tests, and release notes.
- CLI docs must continue to explain extension flags as advanced, opt-in behavior.

## Links

- Code: `src/akkapros/lib/constants.py`
- Code: `src/akkapros/lib/syllabify.py`
- Code: `src/akkapros/lib/metrics.py`
- CLI: `src/akkapros/cli/syllabifier.py`
- CLI: `src/akkapros/cli/fullprosmaker.py`
- Doc: `docs/akkapros/fullprosmaker.md`

## Reviewed By

- Akkapros maintainers

