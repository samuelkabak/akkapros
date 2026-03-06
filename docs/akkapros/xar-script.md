# XAR Script: A Practical Reading Orthography for Akkadian

## Purpose

The XAR script is a reader-oriented orthography for Akkadian designed for two audiences at once:

- scholars who need systematic, reversible correspondences with standard academic transliteration,
- conlangers and learners who need a more pronounceable and visually guided writing system.

It is not meant to replace philological transliteration in critical editions. It is a pronunciation-facing layer that makes reading aloud more consistent.

## Core Design Principles

1. No ambiguity when glyph modifiers are unavailable.
2. Visual cues for non-Latin sounds.
3. Unified marking of emphatics.
4. Explicit vowel length.
5. Explicit vowel coloring near emphatics.
6. Historical memory for circumflex vowels.
7. Compatibility with modern punctuation habits.
8. OB-oriented phonological output: pharyngeals and glottals are neutralized in final text.

## Why XAR Is Different from Standard Academic Transliteration

Standard academic transliteration is optimized for philological precision and historical layering. XAR is optimized for oral readability and robust practical use.

Key differences:

- XAR intentionally uses visually marked letters for sounds that differ from common Latin expectations.
- XAR encodes long vowels as doubled vowels (`aa`, `ii`, `uu`, `ee`) to prevent intuitive shortening by readers from languages where accent marks do not imply length.
- XAR uses grave accents for emphatic vowel coloring to make the coloring visible even when speakers cannot produce full emphatic consonants.
- XAR removes pharyngeal and glottal symbols in final output for OB-aligned reading fluency.

## Letter System

### Consonants

Base correspondences are mostly transparent (`b d g k p s z l m n r w j t`).

The emphatic set uses a shared visual strategy (bar-marked family):

- `q -> ꝗ`
- `ṭ -> ꞓ`
- `ṣ -> ɉ`

Design rationale:

- All emphatics share a marked visual identity.
- `ꞓ` is intentionally similar to `t` as a visual reminder of the historical relation.
- A letter with non-common Latin sound should be visibly marked (`ꝗ`, not plain `q`).

Additional consonant handling:

- `š -> x̌`
- `y -> j`
- `ḥ -> ḫ`
- `ḫ -> ḫ`
- `ʿ -> '` (intermediate stage)
- `ʾ -> '` (intermediate stage)

In final XAR output, apostrophes are removed by rule; see the OB policy below.

### Vowels

Short vowels:

- `a -> a`
- `i -> i`
- `u -> u`
- `e -> e`

Macron vowels (same quality, longer duration) are doubled:

- `ā -> aa`
- `ī -> ii`
- `ū -> uu`
- `ē -> ee`

Circumflex vowels preserve diphthong memory while showing unified realization by dominance on the second element:

- `â -> eâ`
- `î -> eî`
- `û -> iû`
- `ê -> aê`

This keeps a visual trace of the historical diphthong source while signaling a single rendered vowel target.

## Emphatic Vowel Coloring (Visible Pronunciation Aid)

XAR explicitly marks emphatic coloring with grave accents:

- `a -> à`
- `i -> ì`
- `u -> ù`
- `e -> è`

And for long vowels:

- `ā -> àa`
- `ī -> ìi`
- `ū -> ùu`
- `ē -> èe`

Circumflex series under emphatic coloring remains structurally parallel:

- `â -> èâ`
- `î -> èî`
- `û -> ìû`
- `ê -> àê`

Why this matters:

- readers who cannot fully articulate emphatic consonants can still shift vowel quality,
- this gets pronunciation perceptibly closer to historically plausible output.

### Vowel Coloring Rule (Formal)

Operational rule:

- vowel coloring is **post-emphatic only**: a vowel is colored only when the
	preceding consonant is emphatic (`q`, `ṣ`, `ṭ`),
- vowels before emphatics remain plain,
- if no preceding emphatic is present, the vowel must remain plain.

#### Word-Initial Contexts (`# + V + C`)

| Left | Vowel | Right | Status |
| --- | --- | --- | --- |
| `#` | Plain | Plain | LEGAL |
| `#` | Plain | Emphatic | LEGAL |
| `#` | Colored | Plain | ILLEGAL |
| `#` | Colored | Emphatic | ILLEGAL |

#### Word-Medial Contexts (`C + V + C`)

| Left | Vowel | Right | Status |
| --- | --- | --- | --- |
| Plain | Plain | Plain | LEGAL |
| Plain | Plain | Emphatic | LEGAL |
| Emphatic | Plain | Plain | ILLEGAL |
| Emphatic | Plain | Emphatic | ILLEGAL |
| Plain | Colored | Plain | ILLEGAL |
| Plain | Colored | Emphatic | ILLEGAL |
| Emphatic | Colored | Plain | LEGAL |
| Emphatic | Colored | Emphatic | LEGAL |

#### Word-Final Contexts (`C + V + #`)

| Left | Vowel | Right | Status |
| --- | --- | --- | --- |
| Plain | Plain | `#` | LEGAL |
| Emphatic | Plain | `#` | ILLEGAL |
| Plain | Colored | `#` | ILLEGAL |
| Emphatic | Colored | `#` | LEGAL |

## Fallback Robustness: No Conflict Without Glyph Modifiers

In XAR, **glyph modifiers** is the umbrella term for both:

- diacritics (acute, grave, macron, circumflex),
- stroke/bar-based or otherwise modified letterforms.

A key XAR requirement is robust fallback behavior in low-tech contexts (keyboards, plain text, copy/paste losses), where users may lack access to either diacritics or stroked letters.

Principle:

- fallback must reduce all symbols to ASCII letters while preserving readability and minimizing functional conflict in practical use.

ASCII fallback policy:

- emphatic consonants: `ꝗ -> q`, `ꞓ -> c`, `ɉ -> j`
- colored vowels: `à -> a`, `ì -> i`, `ù -> u`, `è -> e`
- long colored vowels: `àa -> aa`, `ìi -> ii`, `ùu -> uu`, `èe -> ee`
- circumflex memory forms: `eâ -> ea`, `eî -> ei`, `iû -> iu`, `aê -> ae`
- emphatic circumflex memory forms: `èâ -> ea`, `èî -> ei`, `ìû -> iu`, `àê -> ae`

This keeps XAR operable on plain keyboards while maintaining a coherent one-to-one practical fallback path for consonants and both short/long vowel forms.

## OB Alignment and Glottal/Pharyngeal Policy

XAR is aligned with an Old Babylonian reading profile:

- pharyngeals and glottals are neutralized in the final practical text,
- no apostrophe is required in final output,
- intermediate apostrophe handling exists only as a transformation stage.

This makes the script easier for continuous reading while preserving enough structure for conversion pipelines.

## Punctuation Model

XAR is intended to work with punctuation conventions similar to English:

- commas, periods, question marks, exclamation marks, quotes, dashes, etc.,
- no special punctuation burden beyond standard modern typing habits.

This improves accessibility for both academic readers and conlang communities.

## Quick Comparison Table

| Feature | Academic Transliteration | XAR Script |
| --- | --- | --- |
| Emphatics | Usually diacritic on Latin base (`ṭ`, `ṣ`) + separate `q` | Dedicated marked family (`ꞓ`, `ɉ`, `ꝗ`) |
| Long vowels | Macron (`ā ī ū ē`) | Doubling (`aa ii uu ee`) |
| Circumflex vowels | Single circumflex letter (`â î û ê`) | Two-vowel memory forms (`eâ eî iû aê`) |
| Emphatic coloring | Usually implicit/analytical | Explicit via grave accent (`à ì ù è`) |
| Pharyngeals/glottals in final reader text | Preserved in transliteration | Neutralized for OB-oriented practical reading |
| Punctuation behavior | Philological/editorial conventions | English-like practical punctuation |

## Practical Outcome

XAR gives Akkadian a practical reading script that is:

- structurally systematic,
- visually explicit,
- speech-oriented,
- robust under real-world typing and fallback conditions,
- useful for both trained Assyriologists and advanced conlang practitioners.

In short: XAR keeps linguistic discipline while making Akkadian easier to read aloud consistently.