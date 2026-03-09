# Metricser CLI (`metricser.py`)

This document explains what the metrics CLI does, how to run it, and how to interpret its generated files.

Implementation:
- CLI wrapper: `src/akkapros/cli/metricser.py`
- Core logic: `src/akkapros/lib/metrics.py`
- Metric definitions: `docs/akkapros/metrics-computation.md`

## Purpose

`metricser.py` computes rhythmic and structural metrics from repaired text (`*_tilde.txt`).

It can output:
- Human-readable text table
- JSON
- CSV

It supports single-file and batch (`--input-list`) processing.

## Input And Output

Input:
- One `*_tilde.txt` file, or
- A list file containing one input path per line (`--input-list`).

Output formats:
- Table: `<base>_metrics.txt`
- JSON: `<base>.json`
- CSV: `<base>.csv`

Base naming:
- If `--prefix` is given: `<outdir>/<prefix>`
- If single input and no prefix: `<outdir>/<input_stem>`
- If multiple inputs and no prefix: `<outdir>/metrics`

## Command Syntax

```bash
python src/akkapros/cli/metricser.py <input_tilde.txt> [options]
```

Batch syntax:

```bash
python src/akkapros/cli/metricser.py --input-list <list.txt> [options]
```

## Options

- `--version`
  - Print CLI version.
- `--input-list <file>`
  - File with one input path per line.
- `-p, --prefix <name>`
  - Output prefix.
- `--outdir <dir>`
  - Output directory. Default: current directory.
- `--table`
  - Write human-readable table output.
- `--json`
  - Write JSON output.
- `--csv`
  - Write CSV output.
- `--wpm <float>`
  - Words per minute used in speech-rate estimation. Default: `165`.
- `--pause-ratio <float>`
  - Pause ratio in percent of total time. Default: `35`.
- `--long-punct-weight <float>`
  - Relative weight of long punctuation pauses vs short pauses. Default: `2.0`.
- `--extra-consonants <chars>`
  - Additional consonant symbols to include in parsing.
- `--extra-vowels <chars>`
  - Additional vowel symbols to include in parsing.
- `--test`
  - Run metrics test suite.

Default format behavior:
- If none of `--table`, `--json`, `--csv` is specified, `--table` is enabled automatically.

## Typical Usage

Single file, default table output:

```bash
python src/akkapros/cli/metricser.py outputs/erra_tilde.txt
```

Write table + JSON + CSV:

```bash
python src/akkapros/cli/metricser.py outputs/erra_tilde.txt \
  --table --json --csv \
  -p erra \
  --outdir outputs
```

Custom timing parameters:

```bash
python src/akkapros/cli/metricser.py outputs/erra_tilde.txt \
  --wpm 170 \
  --pause-ratio 35 \
  --long-punct-weight 2.5 \
  --table
```

Batch mode:

```bash
python src/akkapros/cli/metricser.py \
  --input-list outputs/tilde_files.txt \
  --csv --json \
  --outdir outputs/compare
```

Run tests:

```bash
python src/akkapros/cli/metricser.py --test
```

## What It Computes (Summary)

Main families of metrics:
- Syllable-type distributions and counts
- Mora statistics per syllable and per word
- Merge statistics
- Repair statistics
- Acoustic/rhythmic metrics (`%V`, `DeltaC`, `MeanC`, `VarcoC`)
- Speech and pause allocation metrics

For formal definitions and equations, see:
- `docs/akkapros/metrics-computation.md`

## %V Note

Current outputs expose both:
- `%V (articulate)`
- `%V (normal speech, incl. pauses)`

This makes text-derived moraic `%V` directly comparable with pause-inclusive speech measurements.

## Pipeline Position

`metricser.py` is typically run after `repairer.py`:
1. `atfparser.py`
2. `syllabifier.py`
3. `repairer.py` -> `*_tilde.txt`
4. `metricser.py`

For all-in-one execution, see `fullreparer.py`.
