# Phonetizer Algorithm

This document describes the currently implemented CR-036 phonetize row contract as exposed by the live `phonetizer` stage.

## Current Scope

The live implementation is intentionally transitional.

It provides:
- one canonical `phonetize` config section
- one executable `phonetizer` CLI
- one materialized `<prefix>_phone.txt` artifact
- one shared library module, `src/akkapros/lib/phonetize.py`

It does not yet implement the later dual-output `_ophone` stage or the later duration-realization pass from downstream phonetizer records.

## Row Model

The current `_phone.txt` body uses the canonical flat-line row contract:

```text
label-category-type-length-position-boundary-accent-realization-duration:text
```

Implemented semantics:
- `label` is the canonical source-facing row label such as `SUD`, `AYA`, `ARU`, or `ZEN`
- `category` is `C`, `V`, or `S`
- `type` is split from `length` and preserves hiatus (`H`), vowel-transition (`T`), closure (`C`), fricative (`F`), sonorant (`S`), and vowel-height classes
- `position` is `O`, `C`, `N`, or `S`
- `boundary` is `N`, `I`, `E`, `L`, `X`, or `F`
- `realization` is the two-character code inventory token such as `SU`, `AA`, `AO`, `SP`, or `ZP`
- `duration` is currently the Phase 1 placeholder `0000`
- `text` preserves the source glyph, punctuation mark, or `<EOL>`

## Duration Source

The live builder is now structure-first. It emits `duration=0000` on every row so the artifact matches the Phase 1 placeholder contract while later duration work remains separate.

## Boundary Behavior

The current stage:
- carries the closing structure on the last segment of each syllable or prosodic unit
- uses `I` for ordinary internal syllable breaks and `E` for enclitic dashes
- uses `L` for internal merges (`&`) and `X` for explicit merges (`+`)
- uses `F` for prosodic-unit endings, including space-separated words before the next unit
- emits `SES` / `SP` rows for short pauses and `ZEN` / `ZP` rows for long pauses and line breaks
- serializes line breaks as `<EOL>` in the `text` field

## Transition Note

`metricalc` still computes from `_tilde.txt` rather than consuming `_phone.txt` directly.
During this transition it uses the phonetize defaults internally:
- `wpm = 193`
- `pause_ratio = 35`

That is an implementation bridge, not the final phonetize-to-metrics contract.
