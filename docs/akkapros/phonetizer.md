# Phonetizer CLI (`phonetizer.py`)

`phonetizer.py` is the transitional stage that turns a prosody-realized `*_tilde.txt` file into a phone-row artifact, `<prefix>_phone.txt`.

## Purpose

The phonetize stage now sits between prosody and metrics in the documented pipeline:

1. `*_proc.txt` -> `*_syl.txt`
2. `*_syl.txt` -> `*_tilde.txt`
3. `*_tilde.txt` -> `*_phone.txt`
4. `*_tilde.txt` -> metrics outputs
5. `*_tilde.txt` -> print outputs

At this stage of the rollout, `_phone.txt` is a real artifact with front matter and structured body rows, but metrics still computes from `_tilde.txt` using the phonetize transition defaults internally.

## Input and Output

Input:
- One `*_tilde.txt` file

Output:
- `<prefix>_phone.txt`

The body is newline-delimited JSON. Each row represents either:
- a `phoneme` row with symbol, duration, indices, and boundary metadata
- a `silence` row created from pauses or line breaks

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
