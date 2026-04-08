---
cr_id: CR-036
status: Draft
priority: High
impact: Mutative
created: 2026-04-05
updated: 2026-04-06
implements: 'ADR-018, ADR-039, REQ-024'
---

# Change Request: Define phonetizer phoneme framework

# Summary

Refine the phonetizer artifact contract introduced by [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md) by defining a concrete phoneme framework for `<prefix>_phone.txt`.

This CR specifies:

- the consonant-class sets used by the phonetizer
- the canonical input-character labels, distinct from realization labels
- the canonical realization-code inventory, which is authoritative for
  category/type/emphaticity metadata, and input-to-realization mapping
- the exact ten-field phone-row schema
- the realization-code field carried on each emitted phone row
- the syllable-boundary marker needed to preserve syllable-final structure
- the enclitic-boundary marker needed to preserve internal dash attachment
- the boundary coding needed to preserve explicit versus internal merge
  provenance inside prosodic units
- the normalization rules for long vowels and pauses
- the serialization forms that downstream tools may consume

The goal is to make `_phone` a stable intermediate artifact that is sufficient
for metrics computation and sufficiently structured to support reconstruction of
the accentuated `_tilde` representation, while also carrying timing-model
durations in one canonical row format.

---

# Motivation

CR-035 introduced the idea of a line-oriented `_phone` artifact, but it left
the row-level contract intentionally broad. That is no longer enough for the
next phonetizer step.

The project now needs one explicit internal contract for segment categories,
segment labels, duration-bearing row fields, and the distinction between
hiatus, vowel-transition, closure, fricative, sonorant, vowels, and pauses. Without that
contract, downstream computations risk drifting into stage-local assumptions.

This change is also needed to keep the phonetizer aligned with the inventory
governance already established by [ADR-018](../adr/018-extensible-phonetic-inventory.md)
and with the separated hiatus-marker semantics documented by
[CR-029](029-introduce-separate-hiatus-marker-for-word-initial-vowel-hiatus.md).

---

# Scope

## Included

- Define the canonical phonetizer consonant-class sets exactly as listed in
  this CR.
- Define the canonical input-character labels for each base consonant, vowel
  glyph, and representative pause symbol.
- Define the canonical realization-code inventory, including `Category`,
  `Type`, and `Emphaticity`, and the input-to-realization associations
  documented in this CR.
- Define the canonical ten-field phone-row schema for `_phone` output.
- Define the allowed value inventory for each row field.
- Define the syllable-boundary field that marks internal, last-word, and
  prosodic-final syllable endings.
- Define how the boundary field distinguishes an ordinary internal syllable
  separator from an enclitic dash attached to the preceding syllable.
- Define how the boundary field distinguishes internal `&` merges from explicit
  `+` merges for non-final words inside a prosodic unit.
- Define how long vowels are represented without introducing separate long-
  vowel labels.
- Define how short and long pauses are represented.
- Define the tuple-style and flat-line serializations for a phone row.
- Define the minimum invariants required for metrics computation and reverse
  reconstruction of `_tilde`.
- Cross-link this CR to the broader phonetize-stage contract in CR-035.

## Not Included

- Implementing the phonetizer.
- Defining the phase-1 realization-selection rules used when one input label
  maps to more than one realization code.
- Finalizing the full phonetize-to-metrics algorithm.
- Changing the current timing defaults introduced under CR-035.
- Redesigning syllabification, prosody-selection rules, or merge policy.
- Finalizing printer-side formatting of `_phone` rows beyond the artifact
  contract itself.

---

# Current Behavior

Current internal documentation says that `<prefix>_phone.txt` will contain one
line per phoneme or silence with duration and related metadata, but it does not
yet define:

- the canonical phoneme-class inventory
- the canonical realization-code and IPA inventory
- the input-character label inventory and how it differs from realization
  labels
- the realization-code inventory itself
- how one input symbol may map to more than one realization code
- a stable field order
- the exact per-field code values
- how syllable-final structure is preserved in the row contract
- how vowel quality and segment length are represented separately at the input
  layer and in emitted phone rows
- which source-side fields are authoritative versus looked up through the
  realization-code inventory
- how realization-side row labels relate to those input labels

As a result, `_phone` is currently specified at too high a level to support
consistent downstream consumers.

---

# Proposed Change

Adopt the following phonetizer framework as the normative contract for
`<prefix>_phone.txt`.

## 1. Canonical consonant-class sets

The phonetizer shall classify the non-vocalic inventory using these exact sets:

```python
CONSONANT_HIATUS = set('˙')
CONSONANT_VOWEL_TRANSITION = set('¨')
CONSONANT_CLOSURE = set('bdgkptṭqʾ')
CONSONANT_FRICATIVE = set('szšṣḥḫʿ')
CONSONANT_SONORANT = set('lrmnwy')
EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}
```

Interpretation constraints:

- `˙` remains the dedicated hiatus marker defined separately from `¨`.
- `¨` remains consonant-like for phonetizer output purposes, but it is typed as
  a dedicated vowel-transition marker rather than as a sonorant.
- `ʾ` is classified with closures.
- The input-character emphatic set is `{'q', 'ṣ', 'ṭ'}`.
- These sets define phonetizer typing only; they do not by themselves redefine
  the broader repository inventory governance of ADR-018.

## 2. Canonical input-character labels

This section defines labels keyed directly to the characters that appear in the
input text. These input-character labels are distinct from realization labels
used by emitted phone rows. The purpose of this table is to make the source
glyph mapping explicit before realization-side lookup is applied.

### Input character inventory

| Text | Label | Length |
| --- | --- | --- |
| `b` | `BET` | `S` |
| `d` | `DAL` | `S` |
| `g` | `GIM` | `S` |
| `k` | `KAP` | `S` |
| `p` | `PAY` | `S` |
| `ṭ` | `TUT` | `S` |
| `q` | `QUP` | `S` |
| `ṣ` | `SUD` | `S` |
| `s` | `SAM` | `S` |
| `z` | `ZIN` | `S` |
| `š` | `SIN` | `S` |
| `l` | `LAM` | `S` |
| `m` | `MIM` | `S` |
| `n` | `NAN` | `S` |
| `r` | `RES` | `S` |
| `ḥ` | `ETE` | `S` |
| `ḫ` | `HET` | `S` |
| `ʿ` | `AIN` | `S` |
| `ʾ` | `ALE` | `S` |
| `w` | `WAW` | `S` |
| `y` | `YID` | `S` |
| `t` | `TAW` | `S` |
| `˙` | `ARU` | `S` |
| `¨` | `ENA` | `S` |
| `a` | `AYA` | `S` |
| `e` | `EYA` | `S` |
| `i` | `IYA` | `S` |
| `u` | `UYA` | `S` |
| `ā` | `AWA` | `L` |
| `ē` | `EWA` | `L` |
| `ī` | `IWA` | `L` |
| `ū` | `UWA` | `L` |
| `â` | `AWI` | `L` |
| `ê` | `EWI` | `L` |
| `î` | `IWI` | `L` |
| `û` | `UWI` | `L` |
| `:inner-punct:` | `SES` | `S` |
| `:phrasal-punct:` | `ZEN` | `L` |

Input-table constraints:

- The input-character table is source-facing and defines only source `Text`,
  canonical input `Label`, and source `Length`.
- `Length` is source-scoped: consonant-like symbols always use `S`; vowels use
  `S` or `L`; pause representatives use `S` or `L`.
- `Category`, `Type`, and `Emphaticity` are looked up through the Canonical
  realization code inventory rather than repeated in the input-character table.
- The pause rows above use `:inner-punct:` and `:phrasal-punct:` as normalized
  representative source tokens for short and long punctuation-induced pauses.
  They do not, by themselves, finalize the realization-layer pause-label
  contract.

### Canonical realization code inventory

This table defines the realization-side IPA inventory and its compact codes.
The code column is listed first by design because the code is the stable lookup
token and the IPA value is the phonetic interpretation attached to that token.
This table is the authoritative inventory for realization-side `Category`,
`Type`, and `Emphaticity`. Source-side tables refer into it by realization
code. For pause representatives, source-side tables use symbolic normalized
tokens rather than literal punctuation glyphs.

| Code | IPA | Category | Type | Emphaticity |
| --- | --- | --- | --- | --- |
| `BE` | `b` | `C` | `C` | `P` |
| `DA` | `d` | `C` | `C` | `P` |
| `GI` | `ɡ` | `C` | `C` | `P` |
| `KA` | `k` | `C` | `C` | `P` |
| `PA` | `p` | `C` | `C` | `P` |
| `TU` | `tˤ` | `C` | `C` | `E` |
| `QU` | `q` | `C` | `C` | `E` |
| `SU` | `sˤ` | `C` | `F` | `E` |
| `SA` | `s` | `C` | `F` | `P` |
| `ZI` | `z` | `C` | `F` | `P` |
| `SI` | `ʃ` | `C` | `F` | `P` |
| `LA` | `l` | `C` | `S` | `P` |
| `MI` | `m` | `C` | `S` | `P` |
| `NA` | `n` | `C` | `S` | `P` |
| `RE` | `r` | `C` | `S` | `P` |
| `ET` | `ħ` | `C` | `F` | `P` |
| `HE` | `x` | `C` | `F` | `P` |
| `AI` | `ʕ` | `C` | `F` | `P` |
| `AL` | `ʔ` | `C` | `C` | `P` |
| `WA` | `w` | `C` | `S` | `P` |
| `YI` | `j` | `C` | `S` | `P` |
| `TA` | `t` | `C` | `C` | `P` |
| `AA` | `a` | `V` | `L` | `P` |
| `EE` | `e` | `V` | `M` | `P` |
| `II` | `i` | `V` | `H` | `P` |
| `UU` | `u` | `V` | `H` | `P` |
| `AO` | `ɑ` | `V` | `L` | `P` |
| `EO` | `ɛ` | `V` | `M` | `P` |
| `IO` | `ɨ` | `V` | `H` | `P` |
| `UO` | `ʊ` | `V` | `H` | `P` |
| `SP` | `|` | `S` | `S` | `P` |
| `ZP` | `‖` | `S` | `S` | `P` |

### Input-to-realization associations

This table associates canonical input labels with realization codes only. IPA,
`Category`, `Type`, and `Emphaticity` are looked up through the Canonical
realization code inventory. Some input labels intentionally appear more than
once because realization is not always one-to-one. The special conditions
governing those alternations are not finalized in this CR and will be
specified later in CR-039.

| Label | Realization Code |
| --- | --- |
| `BET` | `BE` |
| `DAL` | `DA` |
| `GIM` | `GI` |
| `KAP` | `KA` |
| `PAY` | `PA` |
| `TUT` | `TU` |
| `QUP` | `QU` |
| `SUD` | `SU` |
| `SAM` | `SA` |
| `ZIN` | `ZI` |
| `SIN` | `SI` |
| `LAM` | `LA` |
| `MIM` | `MI` |
| `NAN` | `NA` |
| `RES` | `RE` |
| `ETE` | `ET` |
| `HET` | `HE` |
| `AIN` | `AI` |
| `ALE` | `AL` |
| `WAW` | `WA` |
| `YID` | `YI` |
| `TAW` | `TA` |
| `ARU` | `AL` |
| `ENA` | `WA` |
| `ENA` | `YI` |
| `AYA` | `AA` |
| `EYA` | `EE` |
| `IYA` | `II` |
| `UYA` | `UU` |
| `AWA` | `AA` |
| `EWA` | `EE` |
| `IWA` | `II` |
| `UWA` | `UU` |
| `AWI` | `AA` |
| `EWI` | `EE` |
| `IWI` | `II` |
| `UWI` | `UU` |
| `AYA` | `AO` |
| `EYA` | `EO` |
| `IYA` | `IO` |
| `UYA` | `UO` |
| `AWA` | `AO` |
| `EWA` | `EO` |
| `IWA` | `IO` |
| `UWA` | `UO` |
| `AWI` | `AO` |
| `EWI` | `EO` |
| `IWI` | `IO` |
| `UWI` | `UO` |
| `SES` | `SP` |
| `ZEN` | `ZP` |

Realization-mapping constraints:

- Input-character labels and realization codes are distinct inventories and
  must not be conflated.
- Repeated `Label` values in the association table are normative and indicate
  that one input label may have more than one realization.
- The Canonical realization code inventory is the authoritative source for
  realization-side `Category`, `Type`, and `Emphaticity`.
- In the input-character inventory, `:inner-punct:` corresponds to the
  short-pause input label `SES`, and `:phrasal-punct:` corresponds to the
  long-pause input label `ZEN`.
- The choice among multiple realization codes is governed by special rules that
  are intentionally deferred to CR-039, where phase-1 row construction chooses
  realization codes while reading `_tilde`.

## 3. Canonical phone-row schema

Unless stated otherwise, the row schema and normalization rules below concern
realization rows emitted by the phonetizer, not the input-character label table
in Section 2.

Each output line represents one phoneme or one silence event and shall expose
ten fields in this exact order:

1. `label`
2. `category`
3. `type`
4. `length`
5. `position`
6. `boundary`
7. `accent`
8. `realization`
9. `duration`
10. `text`

The earlier shorthand spelling `lable` is not canonical for this contract.

### Field definitions

| Field | Width | Allowed values | Meaning |
| --- | --- | --- | --- |
| `label` | 3 chars | Realization-layer row label inventory defined for emitted `_phone` rows, including later bindings to the realization-code inventory above | Canonical emitted segment name |
| `category` | 1 char | `C`, `V`, `S` | Consonant, vowel, silence |
| `type` | 1 char | For `C`: `H`, `T`, `C`, `F`, `S`; for `V`: `H`, `M`, `L`; for `S`: `S` | Structural class within category |
| `length` | 1 char | For `C`: `S`; for `V`: `S`, `L`; for `S`: `S`, `L` | Segment or pause length class |
| `position` | 1 char | For `C`: `O`, `C`; for `V`: `N`; for `S`: `S` | Onset, coda, nucleus, or silence position |
| `boundary` | 1 char | For onset consonants and silence: `N`; for vowels or codas: `N`, `I`, `E`, `L`, `X`, `F` | Syllable-boundary and merge-provenance status carried by this row |
| `accent` | 1 char | For `C` or `V`: `A`, `F`; for `S`: `P` | Accentuated, flat, or pause |
| `realization` | 2 chars | Canonical realization code inventory defined in Section 2, including segment and pause codes | Compact emitted realization code |
| `duration` | 4 chars | Zero-padded decimal value in milliseconds | Segment or pause duration token |
| `text` | variable | Exact source glyph or punctuation text with line breaks rendered as `<EOL>` | Source-facing symbol text |

### Type-code semantics

- `category=C`, `type=H`: hiatus marker consonant (`˙`)
- `category=C`, `type=T`: vowel-transition marker consonant (`¨`)
- `category=C`, `type=C`: closure consonant
- `category=C`, `type=F`: fricative consonant
- `category=C`, `type=S`: sonorant consonant
- `category=V`, `type=H`: high vowel (`i`, `u`, `ī`, `ū`, `î`, `û`)
- `category=V`, `type=M`: mid vowel (`e`, `ē`, `ê`)
- `category=V`, `type=L`: low vowel (`a`, `ā`, `â`)
- `category=S`, `type=S`: silence

### Length-code semantics

- `category=C`, `length=S`: consonant rows are always short for length coding
- `category=V`, `length=S`: short vowel
- `category=V`, `length=L`: long or circumflex vowel
- `category=S`, `length=S`: short pause
- `category=S`, `length=L`: long pause

### Position-code semantics

- `category=C`, `position=O`: consonant onset
- `category=C`, `position=C`: consonant coda
- `category=V`, `position=N`: vowel nucleus
- `category=S`, `position=S`: silence

### Boundary-code semantics

- `boundary=N`: no syllable boundary is carried on this row. This is required
  for all onset consonants and all silence rows. It is also used for vowel
  nuclei that are not syllable-final.
- `boundary=I`: the row is the last phoneme of an internal syllable inside a
  word, and the following syllable is introduced in `_tilde` with the ordinary
  internal syllable separator `·`. This applies only to vowel nuclei or coda
  consonants.
- `boundary=E`: the row is the last phoneme of an internal syllable inside a
  prosodic word, and the following syllable is introduced in `_tilde` with a
  dash `-` signaling enclitic attachment to the preceding syllable. This
  applies only to vowel nuclei or coda consonants.
- `boundary=L`: the row is the last phoneme of the last syllable of a word
  inside a prosodic unit, but not the final segment of that unit. This applies
  only to vowel nuclei or coda consonants when the following link inside the
  unit was created internally and is serialized in `_tilde` as `&`.
- `boundary=X`: the row is the last phoneme of the last syllable of a word
  inside a prosodic unit, but not the final segment of that unit. This applies
  only to vowel nuclei or coda consonants when the following link inside the
  unit was explicitly requested upstream and is serialized in `_tilde` as `+`.
- `boundary=F`: the row is the last phoneme of the last syllable of a word and
  also the final segment of a prosodic unit. This applies only to vowel nuclei
  or coda consonants.

Boundary constraints:

- onset consonants must always use `boundary=N`
- silence rows must always use `boundary=N`
- vowel nuclei may use `N`, `I`, `E`, `L`, `X`, or `F`
- coda consonants may use `I`, `E`, `L`, `X`, or `F`, and must not use `N`
- `boundary=I` must reconstruct to `·` between the current syllable and the
  next syllable in the same word
- `boundary=E` must reconstruct to `-` between the current syllable and the
  next syllable in the same prosodic word, preserving enclitic attachment as
  entered upstream
- `boundary=L` must reconstruct to `&` between the current word and the next
  word in the same prosodic unit
- `boundary=X` must reconstruct to `+` between the current word and the next
  word in the same prosodic unit
- `boundary=F` must reconstruct to the end of the current prosodic unit rather
  than to `·`, `-`, `&`, or `+`
- the boundary field is the canonical carrier of syllable-final and
  prosodic-final structure needed to reconstruct `_tilde`-level boundaries and
  non-final merge provenance after timing data has been added

### Boundary reconstruction examples

The following examples are normative. They are intentionally redundant so that
the implementation does not have to guess whether a syllable break should
serialize as `·`, `-`, `&`, `+`, or prosodic termination.

#### Ordinary internal syllable boundaries: `I`

`boundary=I` means the row closes a syllable and the next syllable in `_tilde`
must be introduced with `·`.

| `_tilde` fragment | Boundary-bearing row | Required code | Why |
| --- | --- | --- | --- |
| `ši`t`·ku` | `t` in `šit` | `I` | Internal syllable end followed by `·` |
| `ši`t·k`u` | `u` in `ku` when followed by another ordinary syllable | `I` | Nucleus closes syllable before `·` |
| `ki`b`·ra` | `b` in `kib` | `I` | Coda closes ordinary internal syllable |
| `ra`·`bi` | `a` in `ra` | `I` | Open syllable closes before `·` |
| `ba`·`na`·`tum` | `a` in first `ba` and `a` in `na` | `I`, `I` | Each ordinary internal break stays `·` |

#### Enclitic dash boundaries: `E`

`boundary=E` means the row closes a syllable and the next syllable in `_tilde`
must be introduced with `-`, not with `·`.

| `_tilde` fragment | Boundary-bearing row | Required code | Why |
| --- | --- | --- | --- |
| `nat`-`ma` | `t` in `nat` | `E` | Enclitic dash attaches `ma` to the preceding syllable |
| `liš`-`šu` | `š` in `liš` | `E` | Dash-preserved enclitic connection |
| `iq`-`bi` | `q` in `iq` | `E` | Final segment before dash must not be confused with `·` |
| `ša`-`ma` | `a` in `ša` | `E` | Open syllable before enclitic dash |
| `ī`-`ma` | `ī` in `ī` | `E` | Long nucleus before enclitic dash still uses `E` |

#### Worked example: `šit·ku·nat-ma`

The input `_tilde` fragment `šit·ku·nat-ma` must be reconstructible from the
boundary stream alone together with the segment text stream.

| Segment text | Position | Boundary | Interpretation |
| --- | --- | --- | --- |
| `š` | onset | `N` | Onset never carries a boundary |
| `i` | nucleus | `N` | Not syllable-final because `t` is the coda |
| `t` | coda | `I` | Ends `šit`, followed by ordinary `·` |
| `k` | onset | `N` | Onset never carries a boundary |
| `u` | nucleus | `I` | Ends `ku`, followed by ordinary `·` |
| `n` | onset | `N` | Onset never carries a boundary |
| `a` | nucleus | `N` | Not syllable-final because `t` is the coda |
| `t` | coda | `E` | Ends `nat`, followed by enclitic dash `-` |
| `m` | onset | `N` | Onset never carries a boundary |
| `a` | nucleus | `F` | Ends `ma`, which also ends the prosodic unit |

#### Word-final non-final boundaries: `L` and `X`

| `_tilde` fragment | Boundary-bearing row | Required code | Why |
| --- | --- | --- | --- |
| `gi.mir&dad.mē` | final row of `gi.mir` | `L` | Non-final internal merge |
| `ana+šar.ri` | final row of `ana` | `X` | Non-final explicit merge |
| `u+ana+šar.ri` | final row of `u`, final row of `ana` | `X`, `X` | Both links are explicit |
| `dam.qá.tum&maḫ.rat` | final row of `tum` | `L` | Internal merge persists through word edge |

#### Prosodic-final boundaries: `F`

| `_tilde` fragment | Boundary-bearing row | Required code | Why |
| --- | --- | --- | --- |
| `bā.nû` | final row of `nû` | `F` | Final segment of prosodic unit |
| `nat-ma` | final row of `ma` | `F` | Dash does not remove finality of the enclitic syllable |
| `ana+šar.ri` | final row of `šar.ri` | `F` | Unit ends after explicit merge chain |

Implementation note:

- The implementation must not normalize `E` back to `I`.
- The implementation must not infer `-` from syllable shape alone.
- The implementation must preserve the user-entered distinction between `·`
  and `-` so that `_phone` remains sufficient to reproduce the input `_tilde`
  string exactly modulo timing augmentation and allowed pause normalization.

## 4. Normalization rules

### Long vowels

- At the input-character layer, long and circumflex vowels have distinct labels
  and preserve their exact glyph identity as listed in Section 2.
- Any realization-layer collapsing, relabeling, or duration mapping for long
  vowels is separate from the input-character mapping and must not erase the
  Section 2 distinction between short, long, and circumflex input glyphs.
- Section 2 explicitly permits both plain-vowel and colored-vowel realization
  codes for the same input vowel glyphs; the governing selection rules are
  deferred.

### Pauses

- At the input-character layer, representative pause symbols are the
  normalized tokens `:inner-punct:` for short pause and `:phrasal-punct:` for
  long pause, labeled `SES` and `ZEN`, respectively.
- Realization-layer pause labels, normalization, and emitted-row behavior are
  distinct from those input representatives and must be specified as
  realization-side rules.
- If punctuation-derived pause text encodes a line break, it must serialize the
  line break as `<EOL>`, not as a literal newline embedded in the row.
- Downstream tools that need a literal newline may convert `<EOL>` to `\\n` or
  to an actual newline after parsing the row stream.

## 5. Supported serializations

The contract shall document both of the following equivalent row renderings.

Tuple/object style:

```text
('SUD','C','F','S','O','N','F','SU','0137','ṣ')
```

Flat-line style:

```text
SUD-C-F-S-O-N-F-SU-0137:ṣ
```

The flat-line style is the canonical file serialization for `_phone` unless a
future CR explicitly replaces it.

## 6. Reconstruction and downstream invariants

The `_phone` artifact defined by this CR must preserve enough information for
the following downstream guarantees:

- metrics can derive category-aware timing and segment statistics from `_phone`
  without needing to re-infer consonant class from raw text
- metrics can derive vowel-height and segment-length information from `_phone`
  without collapsing those into one overloaded field
- long-vowel identity from the input layer remains distinguishable from any
  realization-side duration treatment
- input-to-realization mappings remain available even when one input glyph has
  multiple possible realization codes
- syllable-final, word-final, and prosodic-final boundaries remain recoverable
  from the `boundary` field
- ordinary internal syllable boundaries versus enclitic dash boundaries remain
  recoverable from the `boundary` field via `I` versus `E`
- non-final internal-merge versus explicit-merge word endings remain
  recoverable from the `boundary` field via `L` versus `X`
- accentuated versus flat segments remain recoverable from the `accent` field
- onset, coda, and nucleus structure remain recoverable from the `position`
  field
- hiatus (`˙`) and diphthong-transition (`¨`) behavior remain distinct in the
  artifact
- silence rows preserve at least short-versus-long pause distinction
- reverse reconstruction to `_tilde` is supported in principle from `_phone`
  plus existing stage knowledge, without requiring a second ad hoc segment
  inventory
- `_phone` is intended to be the single structured handoff artifact that can
  feed metricalc and print while preserving the information needed to restore
  the prosody-bearing structure of prosmaker output

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/lib/constants.py`
- `src/akkapros/lib/diphthongs.py`
- `src/akkapros/lib/print.py`
- `src/akkapros/cli/fullprosmaker.py`
- phonetizer-facing documentation under `docs/akkapros/`

Design requirements:

- One canonical mapping from text glyph to input-character label must exist,
  and it must remain distinct from any realization-label inventory used by
  emitted phone rows.
- One canonical realization-code inventory and one canonical input-to-
  realization association table must exist, even where one source glyph maps
  to multiple phonetic outputs.
- This CR defines the inventories and associations only; the runtime
  realization-selection rules that choose among multiple codes belong in
  CR-039 rather than in this contract record.
- The realization-code inventory must include `Category`, `Type`, and
  `Emphaticity` as authoritative realization-side metadata.
- The consonant-class sets above must be treated as the authoritative source
  for phonetizer consonant typing.
- `_phone` rows must use the exact ten-field order specified by this CR.
- `_phone` rows must split segment class and segment length into separate
  `type` and `length` fields.
- `_phone` rows must carry a dedicated two-character realization code in the
  `realization` field.
- `_phone` rows must carry boundary codes sufficient to distinguish syllable-
  internal, word-final, and prosodic-final endings, including non-final
  explicit-versus-internal merge provenance inside a prosodic unit and
  enclitic dash attachment inside a prosodic word.
- The Section 2 input-character mapping must preserve the distinction between
  short, long, and circumflex vowel glyphs through source labels and source
  length.
- Silence handling must remain compatible with the broader stage contract of
  CR-035.
- The phonetizer contract must preserve the semantic distinction between
  lexical consonants, hiatus marker `˙`, and vowel-transition marker `¨`.
- The `_phone` contract must be documented as structured enough for metrics and
  `_tilde` reconstruction, not just for display.

This CR narrows the broad `_phone` artifact contract from CR-035. If a future
change needs a different row shape or a different label inventory, it must be
specified additively in a later CR rather than silently changing this one.

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/lib/constants.py`
`src/akkapros/lib/diphthongs.py`
`src/akkapros/lib/print.py`
`src/akkapros/cli/fullprosmaker.py`
`tests/`
`docs/akkapros/`

---

# Acceptance Criteria

- [ ] Internal documentation defines the phonetizer consonant-class sets
      exactly as:
  `set('˙')`, `set('¨')`, `set('bdgkptṭqʾ')`, `set('szšṣḥḫʿ')`, and
  `set('lrmnwy')`.
- [ ] Internal documentation defines `EMPHATIC_CONSONANTS` as
  `{'q', 'ṣ', 'ṭ'}` for the input-character layer.
- [ ] Internal documentation defines the exact input-character labels listed in
  this CR for all base consonants, hiatus and vowel-transition markers,
  the four short vowels, the eight long or circumflex vowels, and the two
  representative pause symbols.
- [ ] Internal documentation defines the realization-code inventory with `Code`,
  `IPA`, `Category`, `Type`, and `Emphaticity` columns in the order documented
  by this CR.
- [ ] Internal documentation defines the input-to-realization association table
  with `Label` and `Realization Code` columns.
- [ ] The input-to-realization association table explicitly allows repeated
  input labels where one source label has multiple realizations.
- [ ] The input-to-realization association table omits the `IPA` column and
  relies on realization-code lookup through the canonical realization-code
  inventory.
- [ ] The input-character table uses `:inner-punct:` for the short-pause
  representative and `:phrasal-punct:` for the long-pause representative.
- [ ] The realization-code inventory includes short-pause code `SP` with IPA
  `|` and long-pause code `ZP` with IPA `‖`.
- [ ] The realization-code inventory is documented as the authoritative source
  for `Category`, `Type`, and `Emphaticity`.
- [ ] The input-character table includes `Text`, `Label`, and `Length`
  columns.
- [ ] The input-character table defines consonant `length=S` for all
  consonant-like symbols.
- [ ] The input-character table defines vowel and pause representatives with
  `length=S` or `L`.
- [ ] The `_phone` artifact contract defines ten fields in this exact order:
  `label`, `category`, `type`, `length`, `position`, `boundary`, `accent`,
  `realization`, `duration`, `text`.
- [ ] The input-character pause representatives are documented as
  `:inner-punct:` with label `SES` for short pause and `:phrasal-punct:` with
  label `ZEN` for long pause.
- [ ] The contract defines `category` values `C`, `V`, and `S`.
- [ ] The contract defines consonant `type` values `H`, `T`, `C`, `F`, and `S`.
- [ ] The contract defines vowel `type` values `H`, `M`, and `L`.
- [ ] The contract defines silence `type` value `S`.
- [ ] The contract defines consonant `length` value `S`.
- [ ] The contract defines vowel `length` values `S` and `L`.
- [ ] The contract defines silence `length` values `S` and `L`.
- [ ] The contract defines `position` values `O` and `C` for consonants,
  `N` for vowels, and `S` for silence.
- [ ] The contract defines `boundary=N` for onset consonants and silence rows.
- [ ] The contract defines `boundary=E` for internal syllable ends followed by
  an enclitic dash `-` in `_tilde`.
- [ ] The contract defines `boundary=L` for non-final internal-merge word ends
  inside a prosodic unit.
- [ ] The contract defines `boundary=X` for non-final explicit-merge word ends
  inside a prosodic unit.
- [ ] The contract defines `boundary` values `N`, `I`, `E`, `L`, `X`, and `F`
  for vowel nuclei according to syllable-final, enclitic, merge-provenance,
  and prosodic-final status.
- [ ] The contract defines `boundary` values `I`, `E`, `L`, `X`, and `F` for
  consonant codas.
- [ ] The contract defines `accent` values `A` and `F` for segments and `P`
      for silence.
- [ ] The contract defines the `realization` field as a two-character code
  drawn from the canonical realization-code inventory.
- [ ] The input-character mapping distinguishes short, long, and circumflex
  vowels with separate labels while keeping their exact source identity
  explicit.
- [ ] Both supported serializations are documented, including the example
  `SUD-C-F-S-O-N-F-SU-0137:ṣ`.
- [ ] The contract is documented as sufficient for metrics computation and as
  structured enough to support reconstruction of `_tilde`.
- [ ] The contract includes explicit worked examples showing how `I`, `E`,
  `L`, `X`, and `F` reconstruct to `·`, `-`, `&`, `+`, and prosodic-final end.
- [ ] The contract states that punctuation-derived line breaks must be
  rendered as `<EOL>` in the `text` field.
- [ ] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [ ] Documentation is updated in separate phonetizer and algorithm files,
  with cross-links to configuration/confwriter docs and impacted downstream
  program docs where the row contract is consumed.

---

# Risks / Edge Cases

Possible issues:

- The original request text mixed input-character labels and realization
  labels; this revision separates the source-facing mapping in Section 2 from
  realization-side row labeling so later label work can proceed without losing
  the exact input-glyph contract.
- The realization-code inventory includes one-to-many mappings for some input
  glyphs; later CRs must define those selection rules without silently
  rewriting the canonical tables here.
- Reconstructing `_tilde` exactly may still require surrounding stage context
  for word boundaries or merge semantics not represented in one isolated phone
  row, although the new boundary field is intended to minimize how much must be
  inferred outside the row stream.
- Enclitic boundaries are easy to lose if the implementation treats all
  syllable-internal separators as equivalent; this CR therefore treats `I`
  versus `E` as a semantic distinction, not a formatting preference.

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for
  inventory typing, realization mapping, row serialization, parsing, and
  boundary reconstruction

Unit tests:

- verify the input glyph-to-label mapping matches the canonical Section 2
  inventory
- verify the input glyph-to-length mapping matches the canonical Section 2
  inventory
- verify the realization-code inventory matches the canonical code-first table,
  including authoritative `Category`, `Type`, and `Emphaticity` metadata
- verify the input-to-realization association table preserves documented
  one-to-one and one-to-many mappings
- verify the input-to-realization association table omits IPA and resolves IPA
  through realization-code lookup
- verify representative pause symbols map to `SP` and `ZP` realization codes
- verify input labels `SES` and `ZEN` map to `SP` and `ZP`
- verify consonant-class typing for `˙`, closures, fricatives, sonorants,
  vowel-transition `¨`, and sonorants
- verify row serialization and parsing for the ten-field contract
- verify vowel `type` assignment as low for `a`-series, mid for `e`-series,
  and high for `i`- and `u`-series
- verify consonant `length=S` and pause/vowel length coding matches the split
  contract
- verify boundary assignment for onset, nucleus, coda, and silence rows,
  including `I` versus `E` inside words and `L` versus `X` for non-final words
  inside a prosodic unit
- verify representative enclitic forms such as `šit·ku·nat-ma`, `liš-šu`, and
  `ša-ma` round-trip back to the same `_tilde` separator choices
- verify short, long, and circumflex vowels map to their distinct
  input-character labels while preserving exact `text`
- verify representative pause symbols normalize to `:inner-punct:` and
  `:phrasal-punct:` in the input-character inventory without collapsing the
  short-versus-long distinction documented in Section 2
- verify punctuation-derived pause rows encode line breaks as `<EOL>` in
  `text`

Integration tests:

- verify representative phonetizer output emits the documented flat-line row
  format
- verify metrics-facing consumers can read the row format without re-inferring
  consonant class from raw glyphs
- verify a representative accentuated sample can be mapped from `_tilde` to
  `_phone` and back to an equivalent structured accent representation,
  including recovery of `·`, `-`, `&`, `+`, and prosodic-final boundaries

Manual review:

- inspect phonetizer docs for exact inventory, label, and field-order coverage
- inspect CR-035 cross-references so the broad and narrow `_phone` contracts do
  not diverge

---

# Rollback Plan

Revert to the broader CR-035 wording that describes `_phone` only as a generic
line-oriented phoneme/silence artifact, and defer the row schema and phoneme
inventory to a later CR. Partial rollback is discouraged because it would leave
the phonetizer contract ambiguously specified.

---

# Related Issues

- [ADR-018](../adr/018-extensible-phonetic-inventory.md)
- [ADR-039](../adr/039-replacement-of-timing-model.md)
- [REQ-024](../req/024-replacement-of-timing-model.md)
- [CR-029](029-introduce-separate-hiatus-marker-for-word-initial-vowel-hiatus.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- [CR-038](038-distinguish-explicit-and-internal-merge-connectors-in-tilde-pivot.md)

---

# Tasks

## Implementation

- [ ] Add the canonical phonetizer class sets to the phonetizer-facing library
      contract
- [ ] Add the canonical glyph-to-input-label mapping for the input-character
  inventory
- [ ] Add the canonical realization-code inventory and input-to-realization
      association mapping to the phonetizer-facing contract
- [ ] Implement the ten-field `_phone` row serializer and parser
- [ ] Implement the `type` and `length` split for input-character inventory
  and emitted `_phone` rows
- [ ] Implement the dedicated two-character `realization` field on emitted
  `_phone` rows
- [ ] Implement dedicated `type=T` handling for `¨` distinct from sonorants
- [ ] Implement boundary assignment for nucleus/coda syllable endings and
  onset/silence non-boundaries, including `I` versus `E` separator coding and
  `L` versus `X` provenance coding
- [ ] Preserve the Section 2 distinction between short, long, and circumflex
  vowel input labels
- [ ] Preserve the Section 2 representative distinction between short and long
  punctuation-induced pause inputs
- [ ] Keep `_phone` compatible with metrics consumption and `_tilde`
      reconstruction goals

## Tests

- [ ] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [ ] Add pytest unit coverage for inventory typing, label mapping, row
  parsing, and boundary assignment
- [ ] Add pytest integration coverage for representative `_phone` artifacts
  and metrics-facing consumption

## Documentation

- [ ] Create or update `docs/akkapros/phonetizer.md` for the input/output row
  contract, inventories, and CLI-visible semantics
- [ ] Create or update `docs/akkapros/phonetizer-algorithm.md` for row
  interpretation, reconstruction semantics, and the algorithm-facing use of
  the contract
- [ ] Update `docs/akkapros/configuration.md` and `docs/akkapros/confwriter.md`
  anywhere the row-contract-related config surface is described
- [ ] Update impacted downstream program docs, including
  `docs/akkapros/fullprosmaker.md`, wherever `_phone` consumption or row
  semantics are described
- [ ] Cross-link the narrow row contract with CR-035's broader stage contract

## Review

- [ ] Verify acceptance criteria

---

# Notes for CR-036

This CR is intentionally narrow. It does not authorize implementation by
itself, and it does not settle the final timing algorithm. It specifies the
phoneme framework and row contract needed so the phonetizer stage described in
CR-035 can be implemented against one stable internal artifact definition.