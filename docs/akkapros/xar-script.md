# XAR Script: A Practical Reading Orthography for Akkadian

## Purpose

The XAR script is a reader-oriented orthography for Akkadian designed for two audiences at once:

- scholars who need systematic, reversible correspondences with standard academic transliteration
- conlangers and learners who need a more pronounceable and visually guided writing system

It is not meant to replace philological transliteration in critical editions. It is a pronunciation-facing layer that makes reading aloud more consistent.

---

## Core Design Principles

1. No ambiguity when glyph modifiers are unavailable
2. Visual cues for non-Latin sounds
3. Unified marking of emphatics
4. Explicit vowel length
5. Explicit vowel coloring near emphatics
6. Historical memory for circumflex vowels
7. Compatibility with modern punctuation habits
8. Stable practical output policy for glottal letters

---

## Why XAR Is Different from Standard Academic Transliteration

Standard academic transliteration is optimized for philological precision and historical layering. XAR is optimized for oral readability and robust practical use.

**Key differences:**

| Feature | Academic Transliteration | XAR Script |
|---------|-------------------------|------------|
| Emphatics | Usually diacritic on Latin base (`ṭ`, `ṣ`) + separate `q` | Dedicated marked family (`ꞓ`, `ɉ`, `ꝗ`) |
| Long vowels | Macron (`ā ī ū ē`) | Doubling (`aa ii uu ee`) |
| Circumflex vowels | Single circumflex letter (`â î û ê`) | Two-vowel memory forms (`eâ eî iû aê`) |
| Emphatic coloring | Usually implicit/analytical | Explicit via grave accent (`à ì ù è`) |
| Pharyngeals/glottals in final reader text | Preserved in transliteration | Mapped to apostrophe (`'`) |
| Punctuation behavior | Philological/editorial conventions | English-like practical punctuation |

---

## Letter System

### Consonants

Base correspondences are mostly transparent (`b d g k p s z l m n r w j t`).

#### Emphatic Set

The emphatic set uses a shared visual strategy (bar-marked family):

| Phoneme | XAR Glyph | Design Rationale |
|---------|-----------|------------------|
| `q` | `ꝗ` | All emphatics share a marked visual identity |
| `ṭ` | `ꞓ` | Intentionally similar to `t` as visual reminder of historical relation |
| `ṣ` | `ɉ` | Marked member of the family |

A letter with non-common Latin sound should be visibly marked (`ꝗ`, not plain `q`).

#### Additional Consonant Handling

| Phoneme | XAR Glyph |
|---------|-----------|
| `š` | `x̌` |
| `y` | `j` |
| `ḥ` | `ḫ` |
| `ḫ` | `ḫ` |
| `ʿ` | `'` |
| `ʾ` | `'` |

---

### Vowels

#### Short Vowels

| Phoneme | XAR Glyph |
|---------|-----------|
| `a` | `a` |
| `i` | `i` |
| `u` | `u` |
| `e` | `e` |

#### Macron Vowels (same quality, longer duration)

Macron vowels are **doubled** to prevent intuitive shortening by readers from languages where accent marks do not imply length:

| Phoneme | XAR Glyph |
|---------|-----------|
| `ā` | `aa` |
| `ī` | `ii` |
| `ū` | `uu` |
| `ē` | `ee` |

#### Circumflex Vowels

Circumflex vowels preserve diphthong memory while showing unified realization by dominance on the **second element**:

| Phoneme | XAR Glyph | Historical Memory |
|---------|-----------|-------------------|
| `â` | `eâ` | e + a |
| `î` | `eî` | e + i |
| `û` | `iû` | i + u |
| `ê` | `aê` | a + e |

This keeps a visual trace of the historical diphthong source while signaling a single rendered vowel target.

---

## Emphatic Vowel Coloring (Visible Pronunciation Aid)

XAR explicitly marks emphatic coloring with **grave accents**.

### Short Colored Vowels

| Plain | Colored (after emphatic) |
|-------|--------------------------|
| `a` | `à` |
| `i` | `ì` |
| `u` | `ù` |
| `e` | `è` |

### Long Colored Vowels

| Plain | Colored (after emphatic) |
|-------|--------------------------|
| `aa` | `àa` |
| `ii` | `ìi` |
| `uu` | `ùu` |
| `ee` | `èe` |

### Colored Circumflex Series

Circumflex series under emphatic coloring remains structurally parallel:

| Plain Circumflex | Colored Circumflex |
|------------------|--------------------|
| `eâ` | `èâ` |
| `eî` | `èî` |
| `iû` | `ìû` |
| `aê` | `àê` |

**Why this matters:**

- readers who cannot fully articulate emphatic consonants can still shift vowel quality
- this gets pronunciation perceptibly closer to historically plausible output

---

### Vowel Coloring Rule (Formal)

Operational rule:

- vowel coloring is **post-emphatic only**: a vowel is colored only when the preceding consonant is emphatic (`q`, `ṣ`, `ṭ`)
- vowels before emphatics remain plain
- if no preceding emphatic is present, the vowel must remain plain

#### Word-Initial Contexts (`# + V + C`)

| Left | Vowel | Right | Status |
|------|-------|-------|--------|
| `#` | Plain | Plain | LEGAL |
| `#` | Plain | Emphatic | LEGAL |
| `#` | Colored | Plain | ILLEGAL |
| `#` | Colored | Emphatic | ILLEGAL |

#### Word-Medial Contexts (`C + V + C`)

| Left | Vowel | Right | Status |
|------|-------|-------|--------|
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
|------|-------|-------|--------|
| Plain | Plain | `#` | LEGAL |
| Emphatic | Plain | `#` | ILLEGAL |
| Plain | Colored | `#` | ILLEGAL |
| Emphatic | Colored | `#` | LEGAL |

---

## Fallback Robustness: No Conflict Without Glyph Modifiers

In XAR, **glyph modifiers** is the umbrella term for both:

- diacritics (acute, grave, macron, circumflex)
- stroke/bar-based or otherwise modified letterforms

A key XAR requirement is robust fallback behavior in low-tech contexts (keyboards, plain text, copy/paste losses), where users may lack access to either diacritics or stroked letters.

**Principle:** Fallback must reduce all symbols to ASCII letters while preserving readability and minimizing functional conflict in practical use.

### ASCII Fallback Policy

| Original | Fallback |
|----------|----------|
| `ꝗ` | `q` |
| `ꞓ` | `c` |
| `ɉ` | `j` |
| `à` | `a` |
| `ì` | `i` |
| `ù` | `u` |
| `è` | `e` |
| `àa` | `aa` |
| `ìi` | `ii` |
| `ùu` | `uu` |
| `èe` | `ee` |
| `eâ` | `ea` |
| `eî` | `ei` |
| `iû` | `iu` |
| `aê` | `ae` |
| `èâ` | `ea` |
| `èî` | `ei` |
| `ìû` | `iu` |
| `àê` | `ae` |

This keeps XAR operable on plain keyboards while maintaining a coherent one-to-one practical fallback path for consonants and both short and long vowel forms.

---

## OB Alignment and Glottal/Pharyngeal Policy

XAR is aligned with an **Old Babylonian reading profile**:

- pharyngeal and glottal letters are represented by apostrophe (`'`) in final practical text
- apostrophe is retained to keep output reversible and avoid hidden deletions
- both accented and plain XAR outputs follow the same consonant mapping

This makes the script easier for continuous reading while preserving enough structure for conversion pipelines.

---

## Punctuation Model

XAR is intended to work with punctuation conventions similar to English:

- commas, periods, question marks, exclamation marks, quotes, dashes, etc.
- no special punctuation burden beyond standard modern typing habits

This improves accessibility for both academic readers and conlang communities.

---

## Practical Outcome

XAR gives Akkadian a practical reading script that is:

- **structurally systematic** – consistent rules govern all mappings
- **visually explicit** – non-Latin sounds are visibly marked
- **speech-oriented** – designed for reading aloud
- **robust** – works under real-world typing and fallback conditions
- **useful** – for both trained Assyriologists and advanced conlang practitioners

In short: XAR keeps linguistic discipline while making Akkadian easier to read aloud consistently.

---

## Example: Academic, XAR, and English Translation

The following short passage is shown in three parallel forms: standard academic Akkadian, the XAR reading orthography, and an English translation.

### Academic Akkadian

    ukappit-ma : tiāmtu pitiqša
    tāḫāza iktaṣar : ana ilī niprīša
    aḫrâtaš eli apsî : ulammin tiāmtu
    ananta kī iṣmidu : ana ea iptašrū
    išmē-ma ea : amāta šuāti
    kummiš ušḫarrir-ma : šaqummiš ušba
    ištu imtalkū-ma : uzzašu inūḫu
    muttiš anšar abīšu : šū uštardi
    īrum-ma maḫru abi : ālidīšu anšar
    mimmû tiāmtu ikpudu : ušannâ ana šâšu

### XAR Script

    ukappit-ma : tiaamtu pitiꝗx̌a
    taaḫaaza iktaɉàr : ana ilii nipriix̌a
    aḫreâtax̌ eli apseî : ulammin tiaamtu
    ananta kii iɉmidu : ana ea iptax̌ruu
    ix̌mee-ma ea : amaata x̌uaati
    kummix̌ ux̌ḫarrir-ma : x̌aꝗùmmix̌ ux̌ba
    ix̌tu imtalkuu-ma : uzzax̌u inuuḫu
    muttix̌ anx̌ar abiix̌u : x̌uu ux̌tardi
    iirum-ma maḫru abi : aalidiix̌u anx̌ar
    mimmiû tiaamtu ikpudu : ux̌anneâ ana x̌eâx̌u

### English Translation

    Tiamat assembled her creatures,
    Drew up for battle against the gods her brood.
    Thereafter Tiamat, more than Apsu, was become an evildoer.
    She informed Ea that she was ready for battle.
    When Ea heard this,
    He fell silent in his chamber and sat stock still.
    After he had taken thought and his anger had calmed,
    He made straight his way to Anshar his grandfather.
    He came in before his grandfather, Anshar,
    All that Tiamat plotted he recounted to him.

---

## Summary

| Feature | XAR Approach |
|---------|--------------|
| Emphatics | Marked family: `ꝗ`, `ꞓ`, `ɉ` |
| Long vowels | Doubled: `aa`, `ii`, `uu`, `ee` |
| Circumflex | Two-vowel memory: `eâ`, `eî`, `iû`, `aê` |
| Emphatic coloring | Grave accents: `à`, `ì`, `ù`, `è` |
| Pharyngeals/glottals | Apostrophe: `'` |
| Fallback | Clean ASCII mapping |
| Punctuation | English-like conventions |

This example demonstrates how XAR maps academic transliteration into a readable, speech-oriented orthography while preserving phonetic structure.