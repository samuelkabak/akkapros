# Reading `_phone.txt` and `_ophone.txt`

This guide explains the compact fixed-width row format used by the phonetizer.

It is meant to help a reader inspect the files directly without needing to read
the library code first. The phone-row files are the main downstream analysis
artifacts of the phonetizer.

## Purpose

`_phone.txt` is the accentuated downstream stream.
`_ophone.txt` is the original/deaccented downstream stream.

Both files are now the active downstream inputs for:

- `metricalc.py`
- `printer.py`
- the corresponding stages inside `fullprosmaker.py`

Both files keep YAML frontmatter. The body is a flat row stream.

## One Row Per Line

Each body line uses the canonical field order:

```text
label-category-type-length-position-boundary-accent-realization-duration-intonation:text
```

Example:

```text
SUD-C-F-S-O-N-F-SU-0137-M0C:ṣ
AYA-V-L-S-N-F-F-AA-0085-M0C:a
ZEN-S-S-L-S-S-F-ZP-1525-L2C:<EOL>
```

Read this as:

- left of `:`: fixed-width structural fields
- right of `:`: source-facing text tail

## Field Meanings

`label`
- Canonical source-side symbol label such as `SUD`, `AYA`, `ARU`, `SES`, `ZEN`.

`category`
- `C` consonant row
- `V` vowel row
- `S` silence or pause row

`type`
- Consonant and vowel subclass code used by runtime logic.
- Typical values include closure/fricative/sonorant classes and the special hiatus/transition rows.

`length`
- `S` short
- `L` long

For pause rows this is the pause class:
- `S` short pause
- `L` long pause

`position`
- `O` onset
- `N` nucleus
- `C` coda
- `S` silence row

`boundary`
- `N` no boundary closes here
- `I` internal syllable break
- `E` enclitic dash boundary
- `L` internal merge (`&` in `_tilde`)
- `X` explicit merge (`+` in `_tilde`)
- `F` prosodic-unit end

`accent`
- `A` accentuated row
- `F` non-accentuated phoneme row
- `P` pause row accent placeholder

`realization`
- Two-letter realization code such as `SU`, `AA`, `AO`, `SP`, `ZP`.
- `SP` is the short-pause IPA-like marker `|`.
- `ZP` is the long-pause IPA-like marker `‖`.

`duration`
- Four-digit millisecond duration.
- During Phase 1 this is `0000`.
- Finalized phonetizer outputs carry non-zero values.

`intonation`
- Canonical three-character row token such as `M0C`, `H2C`, `L2C`, `R1L`, `F1L`, `P2E`, or `V2E`.
- Pass 3 writes finalized intonation tokens after duration realization.
- Neutral rows use `M0C`.

`text`
- The source-facing glyph or pause text.
- For line breaks the phonetizer writes `<EOL>`.

## Pause Type Letters

Pause rows now carry a meaningful subtype rather than one generic silence type.

| Type | Meaning |
|------|---------|
| `Q` | question-final pause |
| `E` | exclamatory pause |
| `S` | statement-final or ordinary line-final pause |
| `C` | continuation pause |
| `I` | internal or sanitizing pause with no clause-final override |

When a punctuation suite contains mixed cues, the phonetizer resolves it by the
active precedence `Q > E > S > C > I`.

## How Boundaries Travel

Lexical structure does not need a separate word table downstream.
It travels in the boundary field of the phoneme rows.

Examples:

- `X` means an explicit merge connector `+`
- `L` means an internal merge connector `&`
- `E` means a hyphen/enclitic boundary
- `F` closes a prosodic unit

This is how metrics derives explicit-link counts from phone rows and how the
printer reconstructs lexical rendering without using `_tilde.txt` as its active
input.

## How Pauses Travel

Pause ownership now belongs to the phonetizer row stream.

Short pause row:

```text
SES-S-C-S-S-S-F-SP-0600-H1C::
```

Long pause row:

```text
ZEN-S-Q-L-S-S-F-ZP-1525-H3C:?!
```

Line break row:

```text
ZEN-S-S-L-S-S-F-ZP-1525-L2C:<EOL>
```

Important rules:

- If the consumed upstream text has no final line break, the phonetizer inserts one final `<EOL>` row before writing `_phone.txt` and `_ophone.txt`.
- Pause rows use subtype `Q`, `S`, `E`, `C`, or `I` rather than one generic silence type.
- Grouped punctuation suites use precedence `Q > E > S > C > I`.
- Metrics and printer read pause strength from these rows instead of recomputing it from punctuation later.

For interpretation, this means pause meaning is already decided here. Later
stages do not need to guess again whether a symbol acted as continuation,
statement, or question punctuation.

## `_phone.txt` versus `_ophone.txt`

`_phone.txt`
- accentuated stream
- keeps accent-bearing rows marked with `accent = A`

`_ophone.txt`
- original/deaccented stream
- derived from `_tilde` by removing `~` and converting internal merge `&` to ordinary space before row construction

Both files still preserve the same structural boundary inventory and pause rows.

## Frontmatter

Both phone files keep YAML frontmatter. Important downstream metadata includes:

- `file.format: "phone"`
- `metadata.data.phonetize.source_variant`
- `metadata.data.phonetize.phone_row_count`
- `metadata.data.phonetize.silence_row_count`
- `metadata.data.phonetize.drift.max`
- `metadata.data.phonetize.drift.mean`
- `metadata.data.phonetize.drift.stddev`

`metricalc.py` reads drift summary from this frontmatter instead of recomputing it.

## How `.pho` Export Relates to Phone Rows

The phone-row files and the `.pho` files intentionally do not use the same
surface symbols.

`_phone.txt` and `_ophone.txt`
- keep the internal realization codes such as `ET`, `HE`, `AI`, `AL`, `AO`, `SP`, and `ZP`
- remain the canonical downstream row contract for metrics and printer

`_mbrola.pho` and `_ombrola.pho`
- derive MBROLA/X-SAMPA-like export symbols from that same realization inventory
- emit symbols such as `X`, `x`, `H`, `?`, `a.`, and `_`
- derive one or more pitch targets from the row's `intonation` token plus `f0`
- keep vowel length in duration, not by duplicating the symbol string

This means `.pho` is a backend rendering of the realization inventory, not a
replacement for the realization codes stored in phone rows.

## Practical Reading Strategy

When inspecting a phone file manually:

1. Read `category` first to separate phoneme rows from pause rows.
2. Read `boundary` to understand word, syllable, and merge structure.
3. Read `accent` to locate the accentuated segment in `_phone.txt`.
4. Read `duration` to see the realized timing.
5. Read the `text` tail last to map the row back to source material.

If you are comparing `_phone.txt` and `_ophone.txt`, keep the following rule in
mind: both files preserve the same structural skeleton, but only `_phone.txt`
shows the accentuated stream. That makes the pair useful for both metrics and
manual before/after comparison.

For user-facing rendering, `printer.py` reconstructs lexical text from the row
stream and uses the pause rows to decide whether a pause is short, long, or a
line break.