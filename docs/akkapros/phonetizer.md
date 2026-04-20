# Phonetizer CLI (`phonetizer.py`)

`phonetizer.py` turns a prosody-realized `*_tilde.txt` file into two finalized phone-row artifacts, `<prefix>_ophone.txt` and `<prefix>_phone.txt`, plus two phonetizer-owned MBROLA `.pho` artifacts, `<prefix>_ombrola.pho` and `<prefix>_mbrola.pho`.

For most users, this is the stage where the prosodic analysis becomes a
phonetic one. It does not merely relabel symbols. It decides segmental
realization, duration, pause strength, and row-level intonation in a form that
later metrics and printing stages can reuse directly.

## Purpose

The phonetize stage now sits between prosody and metrics in the documented pipeline:

1. `*_proc.txt` -> `*_syl.txt`
2. `*_syl.txt` -> `*_tilde.txt`
3. `*_tilde.txt` -> `*_ophone.txt`, `*_phone.txt`, `*_ombrola.pho`, `*_mbrola.pho`
4. `*_ophone.txt` + `*_phone.txt` -> metrics outputs
5. `*_ophone.txt` + `*_phone.txt` -> print outputs

`_ophone.txt` and `_phone.txt` now form the active metrics handoff. They carry
finalized non-zero durations plus drift summaries in front matter, and
metricalc consumes those artifacts directly.

The current implementation now follows a three-pass contract for both
`<prefix>_ophone.txt` and `<prefix>_phone.txt`:

- flat-line serialization, one row per line
- exact field order: `label|category|type|length|position|boundary|accent|realization|duration|drift|intonation|text`
- canonical segment and pause inventories
- Pass 1 builds rows and pause types
- Pass 2 realizes non-zero durations over the prebuilt row streams
- Pass 3 assigns row-carried intonation tokens over the duration-bearing rows
- deterministic original-stream derivation from `_tilde` by removing `~` and replacing `&` with space while preserving `+`
- unit-drift reporting in front matter under `metadata.data.phonetize.unit_drift`

In researcher-facing terms:

- Pass 1 decides structure: which rows exist, where boundaries fall, and what
  kind of pause has been encountered.
- Pass 2 decides timing: how many milliseconds each row receives.
- Pass 3 decides intonation: which rows stay neutral and which rows receive
  stress or clause-final contour.

The finalized-stream split is now:

- `_phone.txt` receives both ordinary stress intonation and pause-governed contour
- `_ophone.txt` receives pause-governed contour but not ordinary stress intonation
- `_mbrola.pho` and `_ombrola.pho` inherit pitch targets from those finalized row tokens

The timing split is now stream-aware as well:

- `_phone.txt` keeps full-beat synchronization against `cvc_reference` when the input frontmatter carries `metadata.options.mora_mode: bi`
- `_phone.txt` switches to half-beat synchronization against `0.5 * cvc_reference` when the input frontmatter carries `metadata.options.mora_mode: mono`
- `_ophone.txt` always uses that same half-beat synchronization basis, even when the accentuated stream remains bimoraic

That active synchronization basis controls pause targeting, drift folding, mini-pause discharge, and the ordinary long-vowel recovery path. The heavy-syllable reference itself still stays anchored in `cvc_reference`.

Before runtime realization begins, the CLI now also runs shared semantic config
verification. Blocking failures stop the command before `_ophone.txt`,
`_phone.txt`, `_ombrola.pho`, and `_mbrola.pho` are written. Warning-only
conditions are reported distinctly and allow processing to continue.

The contract is intentionally structured for downstream traversal. Neighborhood logic may cross word boundaries inside one prosodic unit; silence rows are the only mandatory stopping points for that local traversal.

## Input and Output

Input:

- One `*_tilde.txt` file

Output:

- `<prefix>_ophone.txt`
- `<prefix>_phone.txt`
- `<prefix>_ombrola.pho`
- `<prefix>_mbrola.pho`

The original stream is derived from the accentuated `_tilde` input by removing `~` and replacing internal merges `&` with spaces, while preserving explicit lexical merges `+` and the other structural separators needed for reconstruction.

The consumed `_tilde` contract may contain armored punctuation spans as `⟦...⟧`, explicit inherited merges as `+`, and internal prosody merges as `&`.

The body is a flat line-oriented format. Each row uses the canonical twelve-field order:

```text
label|category|type|length|position|boundary|accent|realization|duration|drift|intonation|text
```

Examples:

```text
SUD|C|F|S|O|N|F|SU|0137|+000|M0C|ṣ
AYA|V|L|S|N|F|F|AA|0110|+023|M0C|a
MEN|S|M|S|S|N|P|MP|0064|+000|M0C| 
ZEN|S|S|L|S|N|P|ZP|1525|+000|L2C|<EOL>
```

When the input contains a run of adjacent newlines, Pass 1 coalesces that run
into one newline-owned long-pause row and preserves multiplicity in the final
field. For example, three adjacent line breaks are serialized as
`<EOL><EOL><EOL>` in one `ZEN|S|S|L|...` row.

The `boundary` field preserves whether the row closes an ordinary internal syllable (`I`), an enclitic dash (`E`), an internal merge (`L`), an explicit merge (`X`), or a prosodic unit (`F`).

The new `drift` field is a row-level trace token written after Phase 2 timing realization:

- `+000` means the most recently completed syllable or pause ended on the beat
- `-xyz` means the stream stands `xyz` ms ahead of the beat
- `+xyz` means the stream stands `xyz` ms behind the beat
- non-final rows repeat the latest completed-unit value until the next syllable-final row or pause row updates it

Phase 2 diagnostics to look for:

- row durations are finalized non-zero millisecond values rather than `0000`
- row-level drift changes only on syllable-final rows and pause rows
- front matter reports `metadata.data.phonetize.unit_drift.max`, `mean`, `stddev`, `current`, and the current unit-drift label
- these front matter statistics summarize completed-unit drift history, not a segment-by-segment timing trace
- front matter also reports denominator-aware recovery diagnostics so unit-drift extension, drift-tolerance effect over non-accented long vowels, mini-pause insertion, and pause residual carry can be interpreted as rates over explicit populations rather than over row counts
- short and long pauses both target the nearest legal in-band beat multiple; if exact discharge is impossible, residual drift is carried forward
- the nearest legal beat multiple is chosen from the active synchronization basis, which may be `cvc_reference` or `0.5 * cvc_reference` depending on stream type and upstream `mora_mode`
- inserted mini pauses use the dedicated row identity `MEN|S|M|S|S|N|P|MP|...|<space>`, where the final field is one literal space character
- internal merged-unit closures with `L`, `X`, `E`, or `I` may still show raw unfolded drift until the unit-closing `F` row is realized

Worked baseline, pause, and same-consonant examples are documented in `docs/akkapros/phonetizer-algorithm.md` so the emitted files can be checked against the accepted Phase 2 contract.

That algorithm page also contains a dedicated section on hiatus and
vowel-transition processing, including how the special singleton anchors,
`C:V` accentuation, and class-specific runtime ceilings interact.

For the canonical row tables, field inventory, and parsing constraints, see
`docs/akkapros/phonetizer-data-model.md`.

Metricalc and printer now consume `_ophone.txt` and `_phone.txt` as their
active downstream inputs. `_tilde.txt` remains the live upstream prosody pivot
for phonetizer input and for structure-preserving reconstruction only.

Before phone output is written, the phonetizer normalizes a missing terminal
line break into one final `<EOL>` long-pause row. That means downstream stages
inherit one ordinary long-pause line break instead of inventing a separate EOF
rule.

Repeated adjacent newlines remain distinct from punctuation suites. A sequence
such as `?!\n\n` yields one punctuation-owned pause row for `?!` and one
newline-owned row whose `text` field is `<EOL><EOL>`. Reconstruction expands
that repeated token sequence back into the original literal newline count.

When one punctuation suite reaches the phonetizer as one consumed chunk, pause
classification uses typed precedence rather than a simple short-versus-long
split. The active precedence is `Q > E > S > C > I`, meaning question outranks
exclamation, exclamation outranks statement, statement outranks continuation,
and `I` is the neutral internal type. A mixed suite such as `?!!!` therefore
becomes one question-governed pause row, not several independent rows.

See also: `docs/akkapros/phonetizer-phone-file-guide.md`

The `.pho` outputs are raw MBROLA-style lines without YAML front matter. Each
line is emitted as `symbol duration pitch_target_1 [pitch_target_2 ...]`, where
the symbol is the MBROLA/X-SAMPA-like export value derived from the internal
realization inventory, silence is `_`, duration is milliseconds, and the pitch
targets are Hertz values derived from the row-carried intonation token plus
`phonetize.process.intonation.f0`. Constant families emit one target, linear
families emit two, and peak/valley families emit a longer pitch tail.

Important distinction:

- `_phone.txt` and `_ophone.txt` keep the internal realization codes such as `ET`, `HE`, `AI`, `AL`, `AO`, `MP`, `SP`, and `ZP`
- `.pho` export derives MBROLA/X-SAMPA-like symbols such as `X`, `x`, `H`, `?`, `a.`, and `_` from that same realization inventory

This keeps the row contract backend-neutral while making the emitted `.pho` files conventional for MBROLA-style tooling.

If you are validating outputs manually:

- read `_phone.txt` when you want the accentuated phonetic stream
- read `_ophone.txt` when you want the matched original stream
- read `.pho` only when you need the speech-synthesis export surface

The phone-row files are the authoritative downstream analysis artifacts.

## Command Syntax

```bash
python -m akkapros.cli.phonetizer <input_tilde.txt> -p <prefix> [options]
```

## Options

| Option | Description |
| --- | --- |
| `-p, --prefix <name>` | Output prefix |
| `--outdir <dir>` | Output directory |
| `--geminate-policy {corrective,cumulative}` | Override `phonetize.process.timing_model.geminate_policy` |
| `--accentuation-distribution-policy {100_0,95_05,90_10,85_15,80_20,75_25,70_30}` | Override `phonetize.process.timing_model.accentuation_distribution_policy` |
| `--drift-tolerance <int>` | Override `phonetize.process.timing_model.drift_tolerance` |
| `-t, --option KEY=VALUE` | Override one config-backed runtime path; phonetize-owned runtime paths use `phonetize.process.intonation.*` and `phonetize.process.timing_model.*` |
| `--conf <file>` | Load shared grouped config |
| `--test` | Run CLI self-tests |

Dedicated config-backed flags such as `--geminate-policy` remain supported for compatibility, but they are now deprecated in favor of `--option KEY=VALUE` or `--conf FILE`.

## Examples

```bash
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --outdir outputs
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --geminate-policy cumulative
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --option phonetize.process.timing_model.drift_tolerance=21
python -m akkapros.cli.phonetizer --help
python -m akkapros.cli.phonetizer --help phonetize.process.timing_model.durations
```

## Config Ownership

The phonetizer is the canonical owner of the top-level `phonetize` config section.

Representative grouped-config keys:

- `phonetize.process.intonation.f0`
- `phonetize.process.intonation.stress`
- `phonetize.process.intonation.question`
- `phonetize.process.intonation.statement`
- `phonetize.process.intonation.exclamation`
- `phonetize.process.intonation.continuation`
- `phonetize.process.timing_model.geminate_policy`
- `phonetize.process.timing_model.accentuation_distribution_policy`
- `phonetize.process.timing_model.drift_tolerance`
- `phonetize.process.timing_model.durations.segmental_ceiling`
- `phonetize.process.timing_model.durations.segmental_floor`
- `phonetize.process.timing_model.durations.cvc_reference`
- `phonetize.process.timing_model.durations.consonants.<class>.geminate_coda_ratio`
- `phonetize.process.timing_model.durations.consonants.closure.perception_limits.gemination_max`
- `phonetize.process.timing_model.durations.consonants.fricative.perception_limits.gemination_max`
- `phonetize.process.timing_model.durations.consonants.sonorant.perception_limits.gemination_max`
- `phonetize.process.timing_model.durations.vowels.perception_limits.long_min`

No longer user-configurable:

- `phonetize.process.timing_model.short_pause_policy`
- `phonetize.process.timing_model.drift_policy`
- `phonetize.process.timing_model.speech`

These behaviors are now fixed internally or removed from the active contract.

At runtime, path-scoped help and `-t/--option` overrides expose the same canonical phonetize subtree: `phonetize.process.intonation.*` and `phonetize.process.timing_model.*`.

`phonetize.process.intonation` and `phonetize.process.timing_model` are siblings under `phonetize.process`. The former governs emitted pitch for `.pho` export, and the latter contains both the process-policy controls and the timing-model subtree used during realization. `perception_limits` inside the timing-model subtree are classification boundaries, not alternate emitted duration rows.

Current legality notes:

- adjacent accent spill into a short vowel is strictly sub-long and stops at `long_min - 1`
- corrective same-consonant pairs preserve the selected class-local geminate total but split it by `geminate_coda_ratio` on the coda side and the exact remainder on the onset side
- runtime consonant saturation uses class-local `perception_limits.gemination_max`
- ordinary non-accented long-vowel cleanup is tolerance-gated and stops at `very_long_min - 1`, while accent-bearing `CVV:` and `CVV:C` syllables apply accentuation first and may then clean up inside the broader `elongation_max` range
- `segmental_ceiling` and `segmental_floor` remain validation-facing config bounds rather than direct runtime timing knobs

## Preflight Verification

The standalone phonetizer now uses the same shared semantic verification layer
as `confwriter --verify`.

That preflight:

- assumes schema-valid key paths and value types first
- checks the current baseline semantic invariants and warning rules
- checks the validation-only `segmental_floor` lower-bound relations
- checks class-local consonant `gemination_max` values against the global `segmental_ceiling`
- reports full dotted paths, relations, and reasons for blocking failures
- reports warning paths, thresholds or formulas, and configuration-wide hint
  summaries for warning-only conditions

If an old config still provides the removed speech block, the active contract
rejects it explicitly rather than accepting it as a no-op.

Representative removed-key output:

```text
Removed config key (CR-081): phonetize.process.timing_model.speech.wpm. This option was removed and is no longer part of the active config contract.
```

`WPM` and `Pause ratio` remain available downstream in metrics artifacts as
row-derived outputs from realized phone rows; they are no longer phonetizer
inputs.

Representative blocking output:

```text
FAIL phonetize.process.timing_model.durations.segmental_floor, phonetize.process.timing_model.durations.vowels.perception_limits.short_min | relation: segmental_floor <= short_min | reason: The global segmental floor cannot exceed the configured short-vowel minimum.
```

`confwriter --list phonetize` is the supported way to inspect the live schema.

See also:

- `docs/akkapros/phonetizer-data-model.md` for the centralized row contract and canonical inventories
- `docs/akkapros/phonetizer-algorithm.md` for the row and boundary model
- `docs/akkapros/fullprosmaker.md` for the pipeline surface that writes `_ophone.txt`, `_phone.txt`, `_ombrola.pho`, and `_mbrola.pho`
