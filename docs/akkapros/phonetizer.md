# Phonetizer CLI (`phonetizer.py`)

`phonetizer.py` turns a prosody-realized `*_tilde.txt` file into two finalized phone-row artifacts, `<prefix>_ophone.txt` and `<prefix>_phone.txt`, plus two phonetizer-owned MBROLA `.pho` artifacts, `<prefix>_ombrola.pho` and `<prefix>_mbrola.pho`.

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

The current implementation now follows the CR-039 structural contract and the CR-040 Phase 2 duration contract for both `<prefix>_ophone.txt` and `<prefix>_phone.txt`:
- flat-line serialization, one row per line
- exact field order: `label-category-type-length-position-boundary-accent-realization-duration:text`
- canonical segment and pause inventories
- non-zero duration realization over the prebuilt row streams
- deterministic original-stream derivation from `_tilde` by removing `~` and replacing `&` with space while preserving `+`
- drift reporting in front matter under `metadata.data.phonetize.drift`

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

The body is a flat line-oriented format. Each row uses the canonical ten-field order:

```text
label-category-type-length-position-boundary-accent-realization-duration:text
```

Examples:

```text
SUD-C-F-S-O-N-F-SU-0137:ṣ
AYA-V-L-S-N-F-F-AA-0085:a
ZEN-S-S-L-S-N-P-ZP-1525:<EOL>
```

The `boundary` field preserves whether the row closes an ordinary internal syllable (`I`), an enclitic dash (`E`), an internal merge (`L`), an explicit merge (`X`), or a prosodic unit (`F`).

Phase 2 diagnostics to look for:
- row durations are finalized non-zero millisecond values rather than `0000`
- front matter reports `metadata.data.phonetize.drift.max`, `mean`, `stddev`, `current`, and the current drift label
- short pauses discharge as much drift as their band allows, while long pauses must reset the running drift reserve to zero

Worked baseline, pause, and same-consonant examples are documented in `docs/akkapros/phonetizer-algorithm.md` so the emitted files can be checked against the accepted Phase 2 contract.

Metricalc and printer now consume `_ophone.txt` and `_phone.txt` as their
active downstream inputs. `_tilde.txt` remains the live upstream prosody pivot
for phonetizer input and for structure-preserving reconstruction only.

Before phone output is written, the phonetizer normalizes a missing terminal
line break into one final `<EOL>` long-pause row. That means downstream stages
inherit one ordinary long-pause line break instead of inventing a separate EOF
rule.

When one punctuation suite reaches the phonetizer as one consumed chunk, pause
classification uses explicit precedence: long if any long cue is present,
otherwise short if any short cue is present. Mixed suites such as `?!!!` are
therefore serialized as one long-pause row.

See also: `docs/akkapros/phonetizer-phone-file-guide.md`

The `.pho` outputs are raw three-column files without YAML front matter. Each line is emitted as `symbol duration frequency`, where silence is `_`, duration is milliseconds, and frequency is Hertz. `phonetize.process.intonation.*` governs pitch behavior for these files, while `phonetize.process.timing_model.*` remains the timing and duration subtree.

## Command Syntax

```bash
python -m akkapros.cli.phonetizer <input_tilde.txt> -p <prefix> [options]
```

## Options

| Option | Description |
|--------|-------------|
| `-p, --prefix <name>` | Output prefix |
| `--outdir <dir>` | Output directory |
| `--geminate-policy {corrective,cumulative}` | Override `phonetize.process.timing_model.geminate_policy` |
| `--accentuation-distribution-policy {100_0,85_15,70_30}` | Override `phonetize.process.timing_model.accentuation_distribution_policy` |
| `--short-pause-policy {strict,best_effort}` | Override `phonetize.process.timing_model.short_pause_policy` |
| `--drift-policy {strict,extensible}` | Override `phonetize.process.timing_model.drift_policy` |
| `--drift-tolerance <int>` | Override `phonetize.process.timing_model.drift_tolerance` |
| `-t, --option KEY=VALUE` | Override one config-backed runtime path; phonetize-owned runtime paths use `phonetize.process.intonation.*` and `phonetize.process.timing_model.*` |
| `--conf <file>` | Load shared grouped config |
| `--test` | Run CLI self-tests |

Dedicated config-backed flags such as `--geminate-policy` remain supported for compatibility, but they are now deprecated in favor of `--option KEY=VALUE` or `--conf FILE`.

## Examples

```bash
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --outdir outputs
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --geminate-policy cumulative
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --option phonetize.process.timing_model.speech.wpm=201
python -m akkapros.cli.phonetizer --help
python -m akkapros.cli.phonetizer --help phonetize.process.timing_model.durations
```

## Config Ownership

The phonetizer is the canonical owner of the top-level `phonetize` config section.

Representative grouped-config keys:
- `phonetize.process.intonation.f0`
- `phonetize.process.intonation.stress_rise`
- `phonetize.process.timing_model.geminate_policy`
- `phonetize.process.timing_model.accentuation_distribution_policy`
- `phonetize.process.timing_model.short_pause_policy`
- `phonetize.process.timing_model.drift_policy`
- `phonetize.process.timing_model.drift_tolerance`
- `phonetize.process.timing_model.speech.wpm`
- `phonetize.process.timing_model.durations.cvc_reference`

At runtime, path-scoped help and `-t/--option` overrides expose the same canonical phonetize subtree: `phonetize.process.intonation.*` and `phonetize.process.timing_model.*`.

`phonetize.process.intonation` and `phonetize.process.timing_model` are siblings under `phonetize.process`. The former governs emitted pitch for `.pho` export, and the latter contains both the process-policy controls and the timing-model subtree used during realization. `perception_limits` inside the timing-model subtree are classification boundaries, not alternate emitted duration rows.

## Preflight Verification

The standalone phonetizer now uses the same shared semantic verification layer
as `confwriter --verify`.

That preflight:

- assumes schema-valid key paths and value types first
- checks the current baseline semantic invariants and warning rules
- reports full dotted paths, relations, and reasons for blocking failures
- reports warning paths, thresholds or formulas, and configuration-wide hint
	summaries for warning-only conditions

Representative warning-only output:

```text
WARN phonetize.process.timing_model.speech.pause_ratio | relation: pause_ratio > 70 | reason: pause_ratio above 70 reserves an unusually large share of time for pauses.
```

Representative blocking output:

```text
FAIL phonetize.process.timing_model.speech.pause_ratio | relation: 0 < pause_ratio < 100 | reason: pause_ratio must be a percentage strictly between 0 and 100.
```

`confwriter --list phonetize` is the supported way to inspect the live schema.

See also:
- `docs/akkapros/phonetizer-algorithm.md` for the row and boundary model
- `docs/akkapros/fullprosmaker.md` for the pipeline surface that writes `_ophone.txt`, `_phone.txt`, `_ombrola.pho`, and `_mbrola.pho`
