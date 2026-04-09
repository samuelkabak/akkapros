# Phonetizer Algorithm

This document describes the currently implemented two-phase phonetize algorithm as exposed by the live `phonetizer` stage.

## Current Scope

The live implementation is intentionally transitional.

It provides:
- one canonical `phonetize` config section
- one executable `phonetizer` CLI
- two materialized artifacts, `<prefix>_ophone.txt` and `<prefix>_phone.txt`
- one shared library module, `src/akkapros/lib/phonetize.py`

It now implements the later duration-realization pass over the prebuilt row streams.

Phase 1 now derives the original stream deterministically from accentuated `_tilde` by removing `~` and replacing internal merges `&` with spaces while preserving explicit lexical merges `+`.

## Canonical Inventory

The live implementation keeps the CR-036 inventories in code-owned canonical tables.

Consonant-class sets:

```python
CONSONANT_HIATUS = set('˙')
CONSONANT_VOWEL_TRANSITION = set('¨')
CONSONANT_CLOSURE = set('bdgkptṭqʾ')
CONSONANT_FRICATIVE = set('szšṣḥḫʿ')
CONSONANT_SONORANT = set('lrmnwy')
EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}
```

The input-character inventory is kept distinct from realization codes. The input side preserves exact source glyph identity, including separate labels for short, long, and circumflex vowels, plus the normalized pause representatives `:inner-punct:` and `:phrasal-punct:`.

The realization-code inventory is authoritative for realization-side `Category`, `Type`, and `Emphaticity`. Representative pause rows use `SP` with IPA `|` and `ZP` with IPA `‖`.

## Row Model

The current `_ophone.txt` and `_phone.txt` bodies use the canonical flat-line row contract:

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
- `duration` is the finalized millisecond duration emitted by Phase 2
- `text` preserves the source glyph, punctuation mark, or `<EOL>`

Supported serializations:

```text
('SUD','C','F','S','O','N','F','SU','0137','ṣ')
SUD-C-F-S-O-N-F-SU-0137:ṣ
```

The flat-line form is the canonical file serialization.

## Duration Source

The live builder remains structure-first. Phase 1 still materializes the full row contract with placeholder durations, then Phase 2 traverses those rows in place to assign non-zero durations from the active timing model, pause bands, geminate policy, accentuation-distribution policy, and drift policy.

## Dual Stream Behavior

The phonetizer now builds two row streams from one `_tilde` input:
- accentuated rows preserve `~`, `&`, `+`, `·`, and `-` through the row boundary and accent fields
- original rows are built from the derived deaccented view where `~` is removed and `&` becomes ordinary space while `+` remains preserved

Round-trip reconstruction uses the emitted row fields rather than hidden builder state. Accentuated rows reconstruct the accentuated `_tilde` structure; original rows reconstruct the derived original view.

## Boundary Behavior

The current stage:
- carries the closing structure on the last segment of each syllable or prosodic unit
- uses `I` for ordinary internal syllable breaks and `E` for enclitic dashes
- uses `L` for internal merges (`&`) and `X` for explicit merges (`+`)
- uses `F` for prosodic-unit endings, including space-separated words before the next unit
- emits `SES` / `SP` rows for short pauses and `ZEN` / `ZP` rows for long pauses and line breaks
- serializes line breaks as `<EOL>` in the `text` field

Boundary reconstruction examples:
- `I` reconstructs `·` inside a word.
- `E` reconstructs `-` for enclitic attachment.
- `L` reconstructs `&` for internal merges inside a prosodic unit.
- `X` reconstructs `+` for explicit inherited merges.
- `F` closes the current prosodic unit rather than reconstructing another separator.

Examples:
- `šit·ku·nat-ma` yields `I`, `I`, `E`, `F` on the boundary-bearing rows.
- `u+ana&šar~·ri` yields `X`, `L`, `I`, `F` and reconstructs to the same `_tilde` structure.

Neighborhood traversal across emitted rows may cross word boundaries. Silence rows are the only mandatory stopping points for local look-behind or look-ahead logic.

Finalized front matter also carries drift summaries for each emitted stream:
- `metadata.data.phonetize.drift.max`
- `metadata.data.phonetize.drift.mean`
- `metadata.data.phonetize.drift.stddev`
- `metadata.data.phonetize.drift_extension_count`
- `metadata.data.phonetize.max_drift_extension`

Special-realization note:
- hiatus rows use the closure special-realization anchor only as an unstressed baseline
- vowel-transition rows use the sonorant special-realization anchor only as an unstressed baseline
- when those rows are accentuated in later duration realization, timing escalates to the corresponding class geminate target without changing row identity

The `_tilde` input contract consumed here may also carry armored punctuation spans as `⟦...⟧`; those are preserved as structured pause rows rather than de-armored back to plain punctuation upstream. Unsupported non-punctuation armored content fails explicitly instead of being dropped silently.

## Transition Note

`metricalc` still computes from `_tilde.txt` rather than consuming `_ophone.txt` and `_phone.txt` directly.
The transition plan is that metrics eventually consumes the structured `_phone` handoff alongside the prosody-bearing `_tilde` pivot while the contract settles.
During the current transition it uses the phonetize defaults internally:
- `wpm = 193`
- `pause_ratio = 35`

That is an implementation bridge, not the final phonetize-to-metrics contract.
