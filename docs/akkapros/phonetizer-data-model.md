# Phonetizer Data Model

This page is the centralized reference for the live phonetizer data model.
It collects the canonical row schema, input-facing and realization-facing
tables, output serialization, and the structural constraints that downstream
readers must preserve when consuming `_phone.txt` and `_ophone.txt`.

Use this page when you need the contract. Use
`docs/akkapros/phonetizer.md` for the stage overview,
`docs/akkapros/phonetizer-phone-file-guide.md` for guided reading, and
`docs/akkapros/phonetizer-algorithm.md` for the runtime solver.

## Output Artifacts

The phonetizer emits four artifacts:

- `_phone.txt` for the accentuated phone-row stream
- `_ophone.txt` for the original or deaccented phone-row stream
- `_mbrola.pho` for MBROLA-style export of the accentuated stream
- `_ombrola.pho` for MBROLA-style export of the original stream

This document is normative for `_phone.txt` and `_ophone.txt`.
The `.pho` files are derived exports, not the canonical analysis contract.

## Canonical Row Format

Each phone-row body line uses the same twelve-field order:

```text
label|category|type|length|position|boundary|accent|realization|duration|drift|intonation|text
```

Example rows:

```text
SUD|C|F|S|O|N|F|SU|0137|+000|M0C|ṣ
AYA|V|L|S|N|F|F|AA|0085|+023|M0C|a
MEN|S|M|S|S|N|P|MP|0054|+000|M0C| 
ZEN|S|S|L|S|N|P|ZP|1525|+000|L2C|<EOL>
```

## Field Schema

| Field | Width | Allowed values | Meaning |
| --- | --- | --- | --- |
| `label` | 3 chars | Canonical source-side label | Source-facing symbol or pause label |
| `category` | 1 char | `C`, `V`, `S` | Consonant, vowel, or silence |
| `type` | 1 char | `H`, `T`, `C`, `F`, `S`, `L`, `M`, `Q`, `E`, `I` | Subclass code interpreted by `category` |
| `length` | 1 char | `S`, `L` | Short or long |
| `position` | 1 char | `O`, `C`, `N`, `S` | Onset, coda, nucleus, or silence |
| `boundary` | 1 char | `N`, `I`, `E`, `L`, `X`, `F` | Structural closure carried by the row |
| `accent` | 1 char | `A`, `F`, `P` | Accentuated, flat, or pause |
| `realization` | 2 chars | Canonical realization code | Stable realization lookup token |
| `duration` | 4 chars | Zero-padded milliseconds | Realized row duration |
| `drift` | 4 chars | Signed beat-offset token such as `+000`, `-023` | Post-unit drift after the most recently completed syllable or pause |
| `intonation` | 3 chars | Canonical token such as `M0C`, `H2C`, `L2C`, `R1L` | Row-level pitch-shape token |
| `text` | variable | Exact source glyph, normalized pause text, `<EOL>`, or one literal space | Source-facing tail field |

## Structural Code Semantics

### `category`

| Code | Meaning |
| --- | --- |
| `C` | consonant row |
| `V` | vowel row |
| `S` | silence or pause row |

### `type`

For consonant rows:

| Code | Meaning |
| --- | --- |
| `H` | hiatus marker row |
| `T` | vowel-transition row |
| `C` | closure consonant |
| `F` | fricative consonant |
| `S` | sonorant consonant |

For vowel rows:

| Code | Meaning |
| --- | --- |
| `L` | low vowel |
| `M` | mid vowel |
| `H` | high vowel |

For pause rows:

| Code | Meaning |
| --- | --- |
| `Q` | question pause |
| `E` | exclamation pause |
| `S` | statement or line-final pause |
| `C` | continuation pause |
| `I` | internal or sanitizing punctuation-owned pause |
| `M` | inserted mini pause |

### `length`

| Code | Meaning |
| --- | --- |
| `S` | short segment or short pause |
| `L` | long vowel or long pause |

### `position`

| Code | Meaning |
| --- | --- |
| `O` | onset consonant |
| `C` | coda consonant |
| `N` | vowel nucleus |
| `S` | silence row |

### `boundary`

| Code | Meaning | Reconstructs to |
| --- | --- | --- |
| `N` | no structural closure on this row | none |
| `I` | ordinary internal syllable closure | `·` |
| `E` | enclitic or hyphen-attached closure | `-` |
| `L` | non-final internal merge boundary | `&` |
| `X` | non-final explicit merge boundary | `+` |
| `F` | prosodic-unit end | unit end |

### `accent`

| Code | Meaning |
| --- | --- |
| `A` | accentuated segment row |
| `F` | non-accentuated segment row |
| `P` | pause row placeholder |

## Canonical Consonant and Vowel Sets

The phonetizer uses these exact class sets:

```python
CONSONANT_HIATUS = set('˙')
CONSONANT_VOWEL_TRANSITION = set('¨')
CONSONANT_CLOSURE = set('bdgkptṭqʾ')
CONSONANT_FRICATIVE = set('szšṣḥḫʿ')
CONSONANT_SONORANT = set('lrmnwy')
EMPHATIC_CONSONANTS = {'q', 'ṣ', 'ṭ'}

SHORT_VOWELS = set('aeiu')
LONG_VOWELS = set('āēīūâêîû')
LOW_VOWELS = set('aāâ')
MID_VOWELS = set('eēê')
HIGH_VOWELS = set('iuīūîû')
```

These sets control phonetizer typing, realization lookup, and row construction.

## Input Character Inventory

This table is source-facing. It maps the exact consumed input glyph or
normalized pause token to its canonical label and source length.

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

Input-side constraints:

- labels are source-facing and remain distinct from realization codes
- long and circumflex vowels keep their distinct source glyph identity
- punctuation-owned pauses enter the contract through normalized source tokens,
  not through literal punctuation glyphs in the inventory table

## Realization Code Inventory

This table is realization-facing. It is the authoritative inventory for
realization code, IPA, MBROLA/X-SAMPA export, category, type, and emphaticity.

| Code | IPA | MBROLA/X-SAMPA | Category | Type | Emphaticity |
| --- | --- | --- | --- | --- | --- |
| `BE` | `b` | `b` | `C` | `C` | `P` |
| `DA` | `d` | `d` | `C` | `C` | `P` |
| `GI` | `ɡ` | `g` | `C` | `C` | `P` |
| `KA` | `k` | `k` | `C` | `C` | `P` |
| `PA` | `p` | `p` | `C` | `C` | `P` |
| `TU` | `tˤ` | `t.` | `C` | `C` | `E` |
| `QU` | `q` | `q` | `C` | `C` | `E` |
| `SU` | `sˤ` | `s.` | `C` | `F` | `E` |
| `SA` | `s` | `s` | `C` | `F` | `P` |
| `ZI` | `z` | `z` | `C` | `F` | `P` |
| `SI` | `ʃ` | `S` | `C` | `F` | `P` |
| `LA` | `l` | `l` | `C` | `S` | `P` |
| `MI` | `m` | `m` | `C` | `S` | `P` |
| `NA` | `n` | `n` | `C` | `S` | `P` |
| `RE` | `r` | `r` | `C` | `S` | `P` |
| `ET` | `ħ` | `X` | `C` | `F` | `P` |
| `HE` | `x` | `x` | `C` | `F` | `P` |
| `AI` | `ʕ` | `H` | `C` | `F` | `P` |
| `AL` | `ʔ` | `?` | `C` | `C` | `P` |
| `WA` | `w` | `w` | `C` | `S` | `P` |
| `YI` | `j` | `j` | `C` | `S` | `P` |
| `TA` | `t` | `t` | `C` | `C` | `P` |
| `AA` | `a` | `a` | `V` | `L` | `P` |
| `EE` | `e` | `e` | `V` | `M` | `P` |
| `II` | `i` | `i` | `V` | `H` | `P` |
| `UU` | `u` | `u` | `V` | `H` | `P` |
| `AO` | `ɑ` | `a.` | `V` | `L` | `P` |
| `EO` | `ɛ` | `e.` | `V` | `M` | `P` |
| `IO` | `ɨ` | `i.` | `V` | `H` | `P` |
| `UO` | `ʊ` | `u.` | `V` | `H` | `P` |
| `MP` | `.` | `_` | `S` | `S` | `P` |
| `SP` | `|` | `_` | `S` | `S` | `P` |
| `ZP` | `‖` | `_` | `S` | `S` | `P` |

Realization-side constraints:

- `MP` is the dedicated mini-pause realization code
- `SP` and `ZP` remain the punctuation-owned short and long pause realizations
- downstream `.pho` export derives its symbol directly from this table

## Input-to-Realization Associations

The phonetizer resolves input labels through the following canonical mapping.
Repeated input labels are intentional and indicate one-to-many realization
options.

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
| `MEN` | `MP` |
| `SES` | `SP` |
| `ZEN` | `ZP` |

Association constraints:

- realization metadata is looked up through the realization inventory, not
  repeated here
- `MEN` exists only for algorithmically inserted mini pauses
- `SES` and `ZEN` remain the canonical punctuation-owned pause labels

## Pause and Text Conventions

The phonetizer distinguishes three pause identities at the row-contract level:

| Kind | Label | Type | Length | Realization | Text |
| --- | --- | --- | --- | --- | --- |
| short punctuation-owned pause | `SES` | `Q`, `E`, `S`, `C`, or `I` | `S` | `SP` | punctuation suite text |
| long punctuation-owned pause | `ZEN` | `Q`, `E`, `S`, `C`, or `I` | `L` | `ZP` | punctuation suite text or `<EOL>` |
| inserted mini pause | `MEN` | `M` | `S` | `MP` | one literal space |

Text-field constraints:

- `<EOL>` is the serialized representation of a line break in a pause row
- an inserted mini pause uses exactly one literal ASCII space in `text`
- downstream parsers must preserve the final field exactly as written

## Serialization and Parsing Constraints

- each phone row is serialized as one line in pipe-delimited flat form
- parsers must split with a bounded operation such as `split('|', 11)`
- parsers must not trim the whole line before splitting, because the last
  field may legitimately be one literal space
- empty body lines are not valid phone rows
- `duration` is zero-padded to four digits
- `drift` is a signed token such as `+000`, `+023`, or `-114`
- `intonation` is a finalized row-level token after Pass 3

## Structural and Reconstruction Constraints

- onset consonants and silence rows carry `boundary = N`
- the row stream preserves enough structure to reconstruct ordinary syllable
  boundaries, enclitic boundaries, internal merges, explicit merges, and
  prosodic-unit ends
- `_ophone.txt` is derived from `_tilde` by removing `~` and replacing `&`
  with ordinary spaces while preserving `+`
- mini pauses are phone-row artifacts only and are ignored when reconstructing
  upstream lexical `_tilde` text
- metrics and printer consume the phone-row stream directly; they do not need
  to recompute pause strength or infer consonant class from raw glyphs

## Related Reading

- `docs/akkapros/phonetizer.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `docs/akkapros/phonetizer-algorithm.md`