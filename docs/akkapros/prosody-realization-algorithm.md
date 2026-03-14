# Akkadian Prosody Realization Algorithm (LOB/SOB)

## Purpose
This document describes the `akkapros` moraic prosody realization algorithm for scholars of Akkadian and Assyriology. It explains how the system moves from syllabified text to prosody-realized prosodic output, with explicit attention to:

- accent models (`LOB`, `SOB`)
- prosody realization decision hierarchy
- forward and backward merging
- explicit `+` linking (construct/prosodic linking)
- function-word behavior
- diphthong processing and restoration

The goal is reproducible, linguistically constrained rhythm reconstruction, not arbitrary stress assignment.

## Input and Output

### Input format (`*_syl.txt`)
The prosody realization stage reads syllabified text where:

- `.` marks syllable boundaries
- `-` marks internal/prosodic boundaries preserved from input
- `¦` marks word end
- `+` can explicitly link words into a forced prosodic unit
- `[...]` style escaped punctuation/chunks are passed through as non-lexical material

### Output format (`*_tilde.txt`)
The prosody realization stage writes prosody-realized text where:

- `~` marks the prosody-realized (accented) moraic target
- `+` marks merged/prosodically linked words (no pause)
- spaces mark ordinary word boundaries

### Rendering prosody-realized text (`printer.py`)
After prosody realization (`*_tilde.txt`), the text is typically rendered in one of three reading outputs:

1. `--acute`
- output file: `*_accent_acute.txt`
- rendering: `~` is converted to acute accent (`´`) on the prosody-realized syllable
- use case: compact philological reading with explicit prosody-realized prominence

2. `--bold` (often cited as markdown output, `--md`)
- output file: `*_accent_bold.md`
- rendering: prosody-realized syllable is bolded (`**...**`), `~` removed
- use case: publication-ready visual emphasis in markdown documents

3. `--ipa`
- output file: `*_accent_ipa.txt`
- rendering: IPA transliteration with stress/length marking and pause tags
- use case: phonetic interpretation, prosodic timing inspection, and TTS-oriented workflows

## Core Principle: Bimoraic Well-Formedness
Each prosodic unit should resolve to an even mora count. If a standalone word is odd and cannot be resolved internally, the algorithm merges prosodically with neighboring material and retries prosody realization.

## Syllable Typology and Mora Values
The engine classifies syllables into the standard types used in the project:

- light: `CV`, `V` (1 mora)
- heavy: `CVC`, `VC`, `CVV`, `VV` (2 morae)
- superheavy: `CVVC`, `VVC` (3 morae)

This classification drives prosody realization eligibility and model priorities.

## Legal prosody realization Operations
The engine adds exactly one mora per prosody realization event.

1. `lengthen_vowel`
- allowed on: `CVV`, `VV`, `CVVC`, `VVC`
- effect: add `~` after the long vowel symbol

2. `geminate_coda`
- allowed on: `CVC`, `VC` when syllable is not word-final in the active unit
- effect: add `~` at syllable end

3. last-resort onset prosody realization
- if no legal candidate exists: geminate onset (`C~V`) or glottal onset for vowel-initial (`~V`)

## Accent Models and Decision Hierarchy
`LOB` and `SOB` share operations but differ in candidate priority.

### LOB (Literary Old Babylonian)
Priority order:

1. final superheavy (including circumflex finals treated as superheavy-like)
2. rightmost non-final heavy
3. final heavy

### SOB (Standard Old Babylonian)
Priority order:

1. rightmost non-final heavy
2. final heavy

In both models, the algorithm chooses the first candidate in the ordered priority list.

## Word-Level Decision Flow
For each lexical word (unless function-word logic applies):

1. compute prosody-realized mora parity
2. if already even: keep unchanged
3. if odd: try internal prosody realization by model hierarchy
4. if internal prosody realization fails: attempt prosodic merge (forward first)
5. if unresolved: apply last-resort onset/glottal prosody realization

## Merge Forward and Merge Backward

### Merge forward (default prosody realization expansion)
If a word cannot be prosody-realized internally and remains odd:

1. merge with following word
2. recompute unit parity/candidates
3. continue extending rightward until:
- unit becomes even without prosody realization, or
- a legal prosody realization candidate appears

If successful, the unit is emitted with `+` between merged words.

### Merge backward (function-word edge case)
Backward merge is primarily used when trailing function words occur before punctuation/end and need a content host. In that case, the algorithm may roll back prior local prosody realization and rebuild a larger prosodic unit including the preceding content word plus trailing function words.

## Explicit `+` Linking (Construct/Forced Prosodic Unit)
The input `+` is treated as an explicit user instruction that the linked sequence forms one mandatory prosody realization domain.

### Strict mode (default, `only_last=True`)
prosody realization candidates before the linked tail are locked. Operationally, only the last linked word domain is eligible for prosody realization targeting.

### Relaxed mode (`--prosody-relax-last`, `only_last=False`)
prosody realization may propagate right-to-left across the linked chain; the rightmost legal site in the full explicit group is chosen.

### If explicit group is still unresolved
If no candidate is legal inside the explicit group, the engine merges further rightward until punctuation/end or successful prosody realization. If still unresolved, it applies last resort on the first syllable of the last word in the merged explicit group.

## Function Words
Function words are not prosody-realized as independent stress-bearing units.

- consecutive function words are grouped
- when followed by content, they attach forward to that content word with `+`
- if stranded at line end/punctuation, they are attached backward to previous content material

This enforces clitic-like prosodic dependence.

## Diphthong Processing and Restoration
Diphthongs are handled in two phases across pipeline stages.

### Phase 1 (syllabification stage)
Adjacent vowels are split with glottal insertion (for unambiguous syllable parsing), for example `ua` -> `u.ʾa`.

### Phase 2 (prosody realization postprocess)
After prosody realization, optional restoration collapses the split patterns back to diphthongal forms via ordered regex rules. The restoration preserves prosody realization marks where applicable (for example `u.ʾā~` -> `uā~`).

This keeps prosody realization computation explicit while allowing diphthongal surface output.

## Punctuation and Escaped Segments
Non-lexical escaped chunks are preserved and passed through. They do not participate in moraic prosody realization, but they delimit where forward merge can continue.

## Why This Matters for Philology
The implementation encodes a testable bridge between lexical stress eligibility and connected-speech timing:

- model-specific stress targeting (`LOB` vs `SOB`)
- constrained, language-internal prosody realization operations
- explicit representation of prosodic grouping (`+`)
- reproducible outputs suitable for corpus-scale comparison

## Minimal Worked Example
Input (`*_syl.txt`):

```text
gi.mir¦dad.mē¦
```

Possible output (`*_tilde.txt`, model-dependent target):

```text
gi.mir+dad~.mē
```

Interpretation:

- first word cannot resolve independently
- unit merges forward
- prosody realization target selected by hierarchy
- one mora added at the selected syllable (`~`)

## Worked Example: *Erra and Išum* (lines 21-22)

### Source lines (transliteration)

```text
engidudu bēlu muttallik mūši muttarrû rubê
ša eṭla u ardata ina šulmi ittanarrû unammaru kīma ūmi
```

### Translation

```text
O Engidudu, lord who wanders in the night, who guides the princes,
Who leads safely lad and girl, illuminating them like the light of day!
```

### Command used

```bash
python src/akkapros/cli/fullprosmaker.py outputs/demo_proc.txt -p demo --outdir outputs --print-acute --print-bold --print-ipa
```

### prosody-realized pivot (`*_tilde.txt`)

> en~·gi·du·du bē~·lu mut·tal·lik mū~·ši mut·tar·rû ru·bê~
> ša+eṭ·la u+ar·da·ta ina+šul·mi it·ta·nar~·rû u·nam~·ma·ru kī~·ma ū~·mi

### `--print-acute` output (`*_accent_acute.txt`)

> en´gidudu bē´lu muttallik mū´ši muttarrû rubê´
> ša‿eṭla u‿ardata ina‿šulmi ittanar´rû unam´maru kī´ma ū´mi

### `--print-bold` output (`*_accent_bold.md`)

> **en**gidudu **bē**lu muttallik **mū**ši muttarrû ru**bê**
> ša‿eṭla u‿ardata ina‿šulmi itta**nar**rû u**nam**maru **kī**ma **ū**mi

### `--print-ipa` output (`*_accent_ipa.txt`)

> ˈʔenː.gi.du.du.ˈbeːː.lu.mut.tal.lik.ˈmuːː.ʃi.mut.tar.ruː.ru.ˈbeːː ⟨linebreak⟩ ‖
> ʃa.ʔetˤ.la.ʔu.ʔar.da.ta.ʔina.ʃul.mi.ʔit.ta.ˈnarː.ruː.ʔu.ˈnamː.ma.ru.ˈkiːː.ma.ˈʔuːː.mi ⟨linebreak⟩ ‖

IPA mode selection is controlled with `--print-ipa-proto-semitic {preserve,replace}`:
- `preserve` (`ipa-strict`): Old Akkadian distinctions (`ḥ -> ħ`, `ḫ -> χ`, `ʿ -> ʕ`, `ʾ -> ʔ`)
- `remove` (`ipa-ob`): Old Babylonian merger (`ḥ -> χ`, `ḫ -> χ`, `ʿ -> ʔ`, `ʾ -> ʔ`)

In IPA output, spaces and linkers (`+`/`‿`) do not add pauses. Punctuation emits tags plus a prosodic marker: weak punctuation uses `|`, strong punctuation (including line break) uses `‖`. If a line already ends in strong punctuation, line-break deduplication prevents duplicate strong markers.

### Note on vowel coloring in IPA
The IPA renderer applies context-sensitive vowel coloring **post-emphatic only** (notably after `q`, `ṣ`, `ṭ`). As a result, default vowels (`a i u e`) may surface as backed/centralized/opened qualities (`ɑ ɨ ʊ ɛ`) only when the preceding consonant is emphatic. Vowels before emphatics remain plain.

## Implementation Note
Current behavior corresponds to `src/akkapros/lib/prosody.py` and CLI orchestration in `fullprosmaker.py`.




