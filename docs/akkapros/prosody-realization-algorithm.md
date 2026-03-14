# Akkadian Prosody Realization Algorithm (LOB/SOB)

## Purpose
This document describes the `akkapros` moraic prosody realization algorithm for scholars of Akkadian and Assyriology. It explains how the system moves from syllabified text to prosody-realized output, with explicit attention to:

- accent models (`LOB`, `SOB`)
- prosody realization decision hierarchy
- forward and backward merging
- explicit `+` linking (construct/prosodic linking)
- function-word behavior
- diphthong processing and restoration

The goal is reproducible, linguistically constrained rhythm reconstruction, not arbitrary stress assignment.

---

## Input and Output

### Input format (`*_syl.txt`)
The prosody realization stage reads syllabified text where:

| Symbol | Meaning |
|--------|---------|
| `.` | Syllable boundaries |
| `-` | Internal/prosodic boundaries preserved from input |
| `¦` | Word end |
| `+` | Explicit link between words (forced prosodic unit) |
| `[...]` | Escaped punctuation/chunks (passed through as non-lexical material) |

### Output format (`*_tilde.txt`)
The prosody realization stage writes prosody-realized text where:

| Symbol | Meaning |
|--------|---------|
| `~` | Prosody-realized (accented) moraic target |
| `+` | Merged/prosodically linked words (no pause) |
| space | Ordinary word boundaries |

### Rendering prosody-realized text (`printer.py`)
After prosody realization, the text is typically rendered in one of three reading outputs:

#### `--acute` (Acute-accented text)

    Output file: `*_accent_acute.txt`
    Rendering: `~` converted to acute accent (`´`) on the prosody-realized syllable
    Use case: Compact philological reading with explicit prominence

#### `--bold` (Markdown bold text)

    Output file: `*_accent_bold.md`
    Rendering: Prosody-realized syllable bolded (`**...**`), `~` removed
    Use case: Publication-ready visual emphasis in markdown documents

#### `--ipa` (IPA transcription)

    Output file: `*_accent_ipa.txt`
    Rendering: IPA transliteration with stress/length marking and pause tags
    Use case: Phonetic interpretation, prosodic timing inspection, TTS workflows

---

## Core Principle: Bimoraic Well-Formedness

Each prosodic unit should resolve to an even mora count. If a standalone word has an odd mora count and cannot be resolved internally, the algorithm merges prosodically with neighboring material and retries prosody realization.

---

## Syllable Typology and Mora Values

The engine classifies syllables into the standard types:

| Type | Structure | Mora Value |
|------|-----------|------------|
| Light | `CV`, `V` | 1 mora |
| Heavy | `CVC`, `VC`, `CVV`, `VV` | 2 morae |
| Superheavy | `CVVC`, `VVC` | 3 morae |

This classification drives prosody realization eligibility and model priorities.

---

## Legal Prosody Realization Operations

The engine adds exactly one mora per prosody realization event.

### 1. `lengthen_vowel`

- **Allowed on:** `CVV`, `VV`, `CVVC`, `VVC`
- **Effect:** Add `~` after the long vowel symbol
- **Example:** `rā` → `rā~`

### 2. `geminate_coda`

- **Allowed on:** `CVC`, `VC` when syllable is **not** word-final in the active unit
- **Effect:** Add `~` at syllable end
- **Example:** `dad` → `dad~`

### 3. Last-resort onset prosody realization

- **When:** No legal candidate exists
- **Effect:** Geminate onset (`C~V`) or glottal onset for vowel-initial (`~V`)
- **Example:** `ka` → `k~a`, `a` → `~a`

---

## Accent Models and Decision Hierarchy

`LOB` and `SOB` share operations but differ in candidate priority.

### LOB (Literary Old Babylonian)

Priority order:

1. Final superheavy (including circumflex finals treated as superheavy-like)
2. Rightmost non-final heavy
3. Final heavy

### SOB (Standard Old Babylonian)

Priority order:

1. Rightmost non-final heavy
2. Final heavy

In both models, the algorithm chooses the first candidate in the ordered priority list.

---

## Word-Level Decision Flow

For each lexical word (unless function-word logic applies):

1. Compute prosody-realized mora parity
2. If already even: keep unchanged
3. If odd: try internal prosody realization by model hierarchy
4. If internal prosody realization fails: attempt prosodic merge (forward first)
5. If unresolved: apply last-resort onset/glottal prosody realization

---

## Merge Forward and Merge Backward

### Merge Forward (default prosody realization expansion)

If a word cannot be prosody-realized internally and remains odd:

1. Merge with following word
2. Recompute unit parity and candidates
3. Continue extending rightward until:
   - Unit becomes even without prosody realization, or
   - A legal prosody realization candidate appears

If successful, the unit is emitted with `+` between merged words.

### Merge Backward (function-word edge case)

Backward merge is primarily used when trailing function words occur before punctuation or end of text and need a content host. In this case, the algorithm may roll back prior local prosody realization and rebuild a larger prosodic unit including the preceding content word plus trailing function words.

---

## Explicit `+` Linking (Construct / Forced Prosodic Unit)

The input `+` is treated as an explicit user instruction that the linked sequence forms one mandatory prosody realization domain.

### Strict mode (default, `only_last=True`)

Prosody realization candidates before the linked tail are locked. Only the last linked word domain is eligible for prosody realization targeting.

### Relaxed mode (`--prosody-relax-last`, `only_last=False`)

Prosody realization may propagate right-to-left across the linked chain; the rightmost legal site in the full explicit group is chosen.

### If explicit group is still unresolved

If no candidate is legal inside the explicit group, the engine merges further rightward until punctuation, end of text, or successful prosody realization. If still unresolved, it applies last resort on the first syllable of the last word in the merged explicit group.

---

## Function Words

Function words are **not** prosody-realized as independent stress-bearing units.

- Consecutive function words are grouped
- When followed by content, they attach forward to that content word with `+`
- If stranded at line end or punctuation, they are attached backward to previous content material

This enforces clitic-like prosodic dependence.

---

## Diphthong Processing and Restoration

Diphthongs are handled in two phases across pipeline stages.

### Phase 1 (Syllabification stage)

Adjacent vowels are split with glottal insertion for unambiguous syllable parsing:

    ua → u.ʾa

### Phase 2 (Prosody realization post-process)

After prosody realization, optional restoration collapses the split patterns back to diphthongal forms via ordered regex rules. The restoration preserves prosody realization marks where applicable:

    u.ʾā~ → uā~

This keeps prosody realization computation explicit while allowing diphthongal surface output.

---

## Punctuation and Escaped Segments

Non-lexical escaped chunks are preserved and passed through. They do not participate in moraic prosody realization, but they delimit where forward merge can continue.

---

## Why This Matters for Philology

The implementation encodes a testable bridge between lexical stress eligibility and connected-speech timing:

- Model-specific stress targeting (`LOB` vs `SOB`)
- Constrained, language-internal prosody realization operations
- Explicit representation of prosodic grouping (`+`)
- Reproducible outputs suitable for corpus-scale comparison

---

## Minimal Worked Example

**Input (`*_syl.txt`):**

    gi.mir¦dad.mē¦

**Possible output (`*_tilde.txt`, model-dependent target):**

    gi.mir+dad~.mē

**Interpretation:**

- First word cannot resolve independently
- Unit merges forward
- Prosody realization target selected by hierarchy
- One mora added at the selected syllable (`~`)

---

## Worked Example: *Erra and Išum* (lines 21-22)

### Source lines (transliteration)

    engidudu bēlu muttallik mūši muttarrû rubê
    ša eṭla u ardata ina šulmi ittanarrû unammaru kīma ūmi

### Translation

    O Engidudu, lord who wanders in the night, who guides the princes,
    Who leads safely lad and girl, illuminating them like the light of day!

### Command used

    python src/akkapros/cli/fullprosmaker.py outputs/demo_proc.txt \
      -p demo \
      --outdir outputs \
      --print-acute --print-bold --print-ipa

### Prosody-realized pivot (`*_tilde.txt`)

    en~·gi·du·du bē~·lu mut·tal·lik mū~·ši mut·tar·rû ru·bê~
    ša+eṭ·la u+ar·da·ta ina+šul·mi it·ta·nar~·rû u·nam~·ma·ru kī~·ma ū~·mi

### `--print-acute` output (`*_accent_acute.txt`)

    en´gidudu bē´lu muttallik mū´ši muttarrû rubê´
    ša‿eṭla u‿ardata ina‿šulmi ittanar´rû unam´maru kī´ma ū´mi

### `--print-bold` output (`*_accent_bold.md`)

    **en**gidudu **bē**lu muttallik **mū**ši muttarrû ru**bê**
    ša‿eṭla u‿ardata ina‿šulmi itta**nar**rû u**nam**maru **kī**ma **ū**mi

### `--print-ipa` output (`*_accent_ipa.txt`)

    ˈʔenː.gi.du.du.ˈbeːː.lu.mut.tal.lik.ˈmuːː.ʃi.mut.tar.ruː.ru.ˈbeːː ⟨linebreak⟩ ‖
    ʃa.ʔetˤ.la.ʔu.ʔar.da.ta.ʔina.ʃul.mi.ʔit.ta.ˈnarː.ruː.ʔu.ˈnamː.ma.ru.ˈkiːː.ma.ˈʔuːː.mi ⟨linebreak⟩ ‖

### IPA mode selection

IPA mode is controlled with `--print-ipa-proto-semitic {preserve,replace}`:

| Mode | Description | Mapping |
|------|-------------|---------|
| `preserve` | Old Akkadian distinctions | `ḥ → ħ`, `ḫ → χ`, `ʿ → ʕ`, `ʾ → ʔ` |
| `replace` | Old Babylonian merger | `ḥ → χ`, `ḫ → χ`, `ʿ → ʔ`, `ʾ → ʔ` |

### IPA output conventions

- Spaces and linkers (`+`/`‿`) do not add pauses
- Punctuation emits tags plus a prosodic marker:
  - Weak punctuation: `|`
  - Strong punctuation (including line break): `‖`
- If a line already ends in strong punctuation, line-break deduplication prevents duplicate strong markers

### Note on vowel coloring in IPA

The IPA renderer applies context-sensitive vowel coloring **post-emphatic only** (after `q`, `ṣ`, `ṭ`). As a result:

| Default vowel | After emphatic |
|---------------|----------------|
| `a` | `ɑ` |
| `i` | `ɨ` |
| `u` | `ʊ` |
| `e` | `ɛ` |

Vowels before emphatics remain plain.

---

## Implementation Note

Current behavior corresponds to `src/akkapros/lib/prosody.py` and CLI orchestration in `fullprosmaker.py`.