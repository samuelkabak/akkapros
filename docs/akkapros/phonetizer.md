# Phonetizer CLI (`phonetizer.py`)

`phonetizer.py` is the transitional stage that turns a prosody-realized `*_tilde.txt` file into a canonical phone-row artifact, `<prefix>_phone.txt`.

## Purpose

The phonetize stage now sits between prosody and metrics in the documented pipeline:

1. `*_proc.txt` -> `*_syl.txt`
2. `*_syl.txt` -> `*_tilde.txt`
3. `*_tilde.txt` -> `*_phone.txt`
4. `*_tilde.txt` -> metrics outputs
5. `*_tilde.txt` -> print outputs

At this stage of the rollout, `_phone.txt` is a real artifact with front matter and structured body rows, but metrics still computes from `_tilde.txt` using the phonetize transition defaults internally.

The current implementation now follows the CR-036 row contract for `<prefix>_phone.txt`:
- flat-line serialization, one row per line
- exact field order: `label-category-type-length-position-boundary-accent-realization-duration:text`
- canonical segment and pause inventories
- placeholder `duration=0000` until later duration-realization work lands

## Input and Output

Input:
- One `*_tilde.txt` file

Output:
- `<prefix>_phone.txt`

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

`confwriter --list phonetize` is the supported way to inspect the live schema.

See also:
- `docs/akkapros/phonetizer-algorithm.md` for the row and boundary model
- `docs/akkapros/fullprosmaker.md` for the pipeline surface that writes `_phone.txt`
