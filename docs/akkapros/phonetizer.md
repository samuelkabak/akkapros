# Phonetizer CLI (`phonetizer.py`)

`phonetizer.py` is the transitional stage that turns a prosody-realized `*_tilde.txt` file into two Phase 1 phone-row artifacts: `<prefix>_ophone.txt` for the original stream and `<prefix>_phone.txt` for the accentuated stream.

## Purpose

The phonetize stage now sits between prosody and metrics in the documented pipeline:

1. `*_proc.txt` -> `*_syl.txt`
2. `*_syl.txt` -> `*_tilde.txt`
3. `*_tilde.txt` -> `*_ophone.txt`, `*_phone.txt`
4. `*_tilde.txt` -> metrics outputs
5. `*_tilde.txt` -> print outputs

At this stage of the rollout, `_ophone.txt` and `_phone.txt` are real artifacts with front matter and structured body rows, but metrics still computes from `_tilde.txt` using the phonetize transition defaults internally.

The current implementation now follows the CR-039 Phase 1 contract for both `<prefix>_ophone.txt` and `<prefix>_phone.txt`:
- flat-line serialization, one row per line
- exact field order: `label-category-type-length-position-boundary-accent-realization-duration:text`
- canonical segment and pause inventories
- placeholder `duration=0000` until later duration-realization work lands
- deterministic original-stream derivation from `_tilde` by removing `~` and replacing `&` with space while preserving `+`

The contract is intentionally structured for downstream traversal. Neighborhood logic may cross word boundaries inside one prosodic unit; silence rows are the only mandatory stopping points for that local traversal.

## Input and Output

Input:
- One `*_tilde.txt` file

Output:
- `<prefix>_ophone.txt`
- `<prefix>_phone.txt`

The original stream is derived from the accentuated `_tilde` input by removing `~` and replacing internal merges `&` with spaces, while preserving explicit lexical merges `+` and the other structural separators needed for reconstruction.

The consumed `_tilde` contract may contain armored punctuation spans as `⟦...⟧`, explicit inherited merges as `+`, and internal prosody merges as `&`.

The body is a flat line-oriented format. Each row uses the canonical ten-field order:

```text
label-category-type-length-position-boundary-accent-realization-duration:text
```

Examples:

```text
SUD-C-F-S-O-N-F-SU-0000:ṣ
AYA-V-L-S-N-F-F-AA-0000:a
ZEN-S-S-L-S-N-P-ZP-0000:<EOL>
```

The `boundary` field preserves whether the row closes an ordinary internal syllable (`I`), an enclitic dash (`E`), an internal merge (`L`), an explicit merge (`X`), or a prosodic unit (`F`).

During the current transition, metricalc still computes from `_tilde.txt`. The broader stage plan is that `_ophone.txt` and `_phone.txt` become the structured phonetic handoff artifacts while `_tilde.txt` remains the live prosody-bearing pivot until the phonetize-to-metrics contract is completed.

## Command Syntax

```bash
python -m akkapros.cli.phonetizer <input_tilde.txt> -p <prefix> [options]
```

## Options

| Option | Description |
|--------|-------------|
| `-p, --prefix <name>` | Output prefix |
| `--outdir <dir>` | Output directory |
| `--geminate-policy {corrective,cumulative}` | Override `phonetize.process.geminate_policy` |
| `--accentuation-distribution-policy {100_0,85_15,70_30}` | Override `phonetize.process.accentuation_distribution_policy` |
| `--short-pause-policy {strict,best_effort}` | Override `phonetize.process.short_pause_policy` |
| `--drift-policy {strict,extensible}` | Override `phonetize.process.drift_policy` |
| `--drift-tolerance <int>` | Override `phonetize.process.drift_tolerance` |
| `-t, --option phonetize.timing_model...=...` | Override values under `phonetize.timing_model` |
| `--conf <file>` | Load shared grouped config |
| `--test` | Run CLI self-tests |

## Examples

```bash
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --outdir outputs
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --geminate-policy cumulative
python -m akkapros.cli.phonetizer outputs/erra_tilde.txt -p erra --option phonetize.timing_model.speech.wpm=201
```

## Config Ownership

The phonetizer is the canonical owner of the top-level `phonetize` config section.

Representative keys:
- `phonetize.process.geminate_policy`
- `phonetize.process.accentuation_distribution_policy`
- `phonetize.process.short_pause_policy`
- `phonetize.process.drift_policy`
- `phonetize.process.drift_tolerance`
- `phonetize.timing_model.speech.wpm`
- `phonetize.timing_model.durations.cvc_reference`

`phonetize.process` keys are policy controls and tolerances for later duration realization. `perception_limits` under `phonetize.timing_model` are classification boundaries, not alternate emitted duration rows.

`confwriter --list phonetize` is the supported way to inspect the live schema.

See also:
- `docs/akkapros/phonetizer-algorithm.md` for the row and boundary model
- `docs/akkapros/fullprosmaker.md` for the pipeline surface that writes `_ophone.txt` and `_phone.txt`
