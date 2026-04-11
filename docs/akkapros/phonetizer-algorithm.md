# Phonetizer Algorithm

This document describes the currently implemented three-pass phonetize
algorithm as exposed by the live `phonetizer` stage.

The practical question answered here is: once prosody has already been decided
in `_tilde.txt`, how does the toolkit turn that structure into a paired
phonetic representation that can drive both metrics and MBROLA export?

## Current Scope

It provides:
- one canonical `phonetize` config section
- one executable `phonetizer` CLI
- two materialized artifacts, `<prefix>_ophone.txt` and `<prefix>_phone.txt`
- one shared library module, `src/akkapros/lib/phonetize.py`

It implements separate duration-realization and intonation-realization passes
over the prebuilt row streams.

It also now has one baseline semantic-validation boundary shared with
`confwriter --verify`. Schema-valid grouped config is a prerequisite; semantic
verification then enforces the current narrow invariant inventory and warning
layer before standalone phonetizer runtime proceeds into Phase 2.

Phase 1 now derives the original stream deterministically from accentuated `_tilde` by removing `~` and replacing internal merges `&` with spaces while preserving explicit lexical merges `+`.

## Canonical Inventory

The live implementation keeps the segment inventories in code-owned canonical
tables, but the user-facing point is simpler: the phonetizer distinguishes
ordinary consonants, vowels, pauses, hiatus markers, and vowel-transition
markers in a stable way before any duration or pitch is assigned.

The input-character inventory is kept distinct from realization codes. The input side preserves exact source glyph identity, including separate labels for short, long, and circumflex vowels, plus the normalized pause representatives `:inner-punct:` and `:phrasal-punct:`.

The realization-code inventory is authoritative for realization-side `Category`, `Type`, and `Emphaticity`. Representative pause rows use `SP` with IPA `|` and `ZP` with IPA `‖`.

## Row Model

The current `_ophone.txt` and `_phone.txt` bodies use the canonical flat-line row contract:

```text
label-category-type-length-position-boundary-accent-realization-duration-intonation:text
```

Implemented semantics:
- `label` is the canonical source-facing row label such as `SUD`, `AYA`, `ARU`, or `ZEN`
- `category` is `C`, `V`, or `S`
- `type` is split from `length` and preserves hiatus (`H`), vowel-transition (`T`), closure (`C`), fricative (`F`), sonorant (`S`), and vowel-height classes
- `position` is `O`, `C`, `N`, or `S`
- `boundary` is `N`, `I`, `E`, `L`, `X`, or `F`
- `realization` is the two-character code inventory token such as `SU`, `AA`, `AO`, `SP`, or `ZP`
- `duration` is the finalized millisecond duration emitted by Phase 2
- `intonation` is the finalized three-character row token emitted by Phase 3
- `text` preserves the source glyph, punctuation mark, or `<EOL>`

Supported serializations:

```text
('SUD','C','F','S','O','N','F','SU','0137','M0C','ṣ')
SUD-C-F-S-O-N-F-SU-0137-M0C:ṣ
```

The flat-line form is the canonical file serialization.

## Duration Source

The live builder remains structure-first. Phase 1 materializes the full row
contract with placeholder duration and neutral intonation, Phase 2 traverses
those rows in place to assign non-zero durations from the active timing model,
and Phase 3 traverses the duration-bearing rows to assign row-carried
intonation from stress and pause type.

That separation matters for interpretation. A row exists before it receives a
duration, and it receives a duration before it receives a final contour. This
is why the same phone-row artifacts can support both phonetic analysis and
speech-synthesis export without keeping separate hidden state.

## Shared Validation Boundary

The current shared verification layer is intentionally baseline-only.

It verifies explicit, path-addressable relations such as:

- enum-like process policy inventories
- positive-integer timing representation for the validated phonetize surface
- `0 < phonetize.process.timing_model.speech.pause_ratio < 100`
- consonant and vowel ordering relations required by the active timing model
- pause-band ordering and integer-multiple compatibility with
	`phonetize.process.timing_model.durations.cvc_reference`

It also emits warning-only signals for the current accepted warning layer,
including high pause ratios, strong onset/coda divergence inside a consonant
class, short-pause compatibility warnings, and selected default-deviation
warnings for the narrow parameter set named by the internal requirement record.

This layer is not the final exhaustive solver-validation regime. It is the
current shared baseline used by config authoring verification and standalone
phonetizer preflight.

## Dual Stream Behavior

The phonetizer now builds two row streams from one `_tilde` input:
- accentuated rows preserve `~`, `&`, `+`, `·`, and `-` through the row boundary and accent fields
- original rows are built from the derived deaccented view where `~` is removed and `&` becomes ordinary space while `+` remains preserved

Round-trip reconstruction uses the emitted row fields rather than hidden builder state. Accentuated rows reconstruct the accentuated `_tilde` structure plus the normalized final line break; original rows reconstruct the derived original view plus that same normalized final line break.

## Boundary Behavior

The current stage:
- carries the closing structure on the last segment of each syllable or prosodic unit
- uses `I` for ordinary internal syllable breaks and `E` for enclitic dashes
- uses `L` for internal merges (`&`) and `X` for explicit merges (`+`)
- uses `F` for prosodic-unit endings, including space-separated words before the next unit
- emits `SES` / `SP` rows for short pauses and `ZEN` / `ZP` rows for long pauses and line breaks
- serializes line breaks as `<EOL>` in the `text` field
- inserts one final `<EOL>` long-pause row if the consumed `_tilde` text had no terminal line break
- classifies one punctuation suite by typed pause precedence: `Q > E > S > C > I`

Pause-type meaning:

- `Q` question-final pause
- `E` exclamatory pause
- `S` statement-final pause, including ordinary line-final closure
- `C` continuation pause such as comma- or semicolon-like carry-on phrasing
- `I` internal or sanitizing pause that carries no clause-final override

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

## Intonation Outcome

The current implementation uses pause type as the cause-side signal for
clause-level contour. In the present scope, the visible consequence is applied
to the last syllable before the pause.

That means:

- an ordinary stressed syllable receives the configured stress color when no
	clause-final pause overrides it
- a final question receives the configured question contour on the last
	syllable before the question pause
- a final statement receives the configured statement contour on the last
	syllable before the statement pause
- internal pauses of type `I` do not impose a clause-final contour

The original stream remains neutral in the present implementation scope.

## Worked Phase 2 Examples

### Baseline syllable realization

With the default timing model, the baseline `qat` stream is realized as one
closed syllable:

```text
QUP-C-C-S-O-N-F-QU-0108:q
AYA-V-L-S-N-N-F-AA-0085:a
TAW-C-C-S-C-F-F-TA-0103:t
```

The consonantal anchors contribute `108 + 103 = 211 ms`, the short vowel is
realized at `85 ms`, and the total realized syllable duration is therefore
`296 ms`. The default `CVC` target is one `cvc_reference`, or `305 ms`, so the
stream leaves this syllable with `-9 ms` of running drift. That is why the
reported drift label stays on the rushing side until a later syllable or pause
discharges it.

### Pause discharge versus pause reset

The solver treats short and long pauses differently.

For an ordinary short pause, the row must stay inside the configured short band
and may therefore carry residual drift forward if the band blocks complete
discharge. A representative diagnostic setup is:

- `cvc_reference = 200`
- `drift_policy = extensible`
- `drift_tolerance = 0`
- `pauses.short.min = pauses.short.max = 600`

Under that configuration, `qat,` reaches the short pause with positive drift.
The short-pause row itself is still forced to `600 ms`, so that row cannot
fully discharge the drift. If the source text had no final line break, the
normalized terminal `<EOL>` long pause written after the comma then resets the
stream to zero before the file ends.

The same setup with `qat\n` behaves differently. The long pause is allowed to
choose any legal value inside the long-pause band and must unload the full drift
reserve, so the post-pause drift returns to `0` and the report ends `On the
beat`.

### Same-consonant boundary handling

Same-consonant coda/onset chains are decided during realization of the first
syllable, not delayed until the following syllable becomes current.

In `at·ta`, the first `t` is the coda of the first syllable and the second `t`
is the onset of the next one. Under `geminate_policy = corrective`, the solver
normalizes that pair toward the configured geminate target, so the coda keeps
its ordinary `103 ms` closure while the next onset is pre-assigned the reduced
companion duration used by the geminate pair. Under
`geminate_policy = cumulative`, the second onset keeps its ordinary onset anchor
instead of being corrected downward. The emitted rows stay identical; only the
durations differ.

Special-realization note:
- hiatus rows use the closure special-realization anchor only as an unstressed baseline
- vowel-transition rows use the sonorant special-realization anchor only as an unstressed baseline
- when those rows are accentuated in later duration realization, timing escalates to the corresponding class geminate target without changing row identity

The `_tilde` input contract consumed here may also carry armored punctuation spans as `⟦...⟧`; those are preserved as structured pause rows rather than de-armored back to plain punctuation upstream. Unsupported non-punctuation armored content fails explicitly instead of being dropped silently.

## Metrics Handoff Note

`metricalc` now consumes `_ophone.txt` and `_phone.txt` directly as its active
inputs. The phonetizer owns the duration-bearing representation used for
interval metrics, drift reporting, and explicit-link reconstruction.

`_tilde.txt` remains the upstream prosody pivot for phonetizer input and
upstream reconstruction, but it is no longer the active downstream source for
metrics or printer.

See also: `docs/akkapros/phonetizer-phone-file-guide.md`
