# Metricalc CLI (`metricalc.py`)

`metricalc.py` computes rhythmic and structural metrics from paired phonetizer
artifacts.

Implementation:
- CLI wrapper: `src/akkapros/cli/metricalc.py`
- Core logic: `src/akkapros/lib/metrics.py`
- Metric definitions: `docs/akkapros/metrics-computation.md`

## Purpose

The active metrics contract is phone-driven. Metricalc reads the accentuated
`<prefix>_phone.txt` stream, resolves the matching original
`<prefix>_ophone.txt` stream, and computes interval metrics from the realized
durations in those files.

The stage also reports the broader structural inventory, including syllable,
word, mora, merge, prominence, accentuation, pause, speech-rate, and drift
summaries.

## Inputs

Required positional input:
- `<prefix>_phone.txt`

Original-stream resolution:
- `--ophone <file>` uses the exact `_ophone.txt` path supplied
- without `--ophone`, metricalc derives the sibling path by replacing
  `_phone.txt` with `_ophone.txt`
- if the derived file does not exist, the command fails and emits no metrics
  outputs

Batch mode:
- `--input-list` accepts one `<prefix>_phone.txt` path per line
- `--ophone` is single-file only and cannot be combined with `--input-list`

Non-inputs:
- `*_tilde.txt`
- `*_mbrola.pho` and `*_ombrola.pho`

## Outputs

| Format | File |
|--------|------|
| Table | `<prefix>_metrics.txt` |
| JSON | `<prefix>_metrics.json` |

Path-bearing display fields are shortened to the shared safe display form.

## Syntax

Single file with sibling discovery:

```bash
python src/akkapros/cli/metricalc.py outputs/erra_phone.txt -p erra --table
```

Single file with explicit original stream:

```bash
python src/akkapros/cli/metricalc.py outputs/erra_phone.txt \
  --ophone outputs/erra_ophone.txt \
  -p erra \
  --json
```

Batch mode:

```bash
python src/akkapros/cli/metricalc.py --input-list outputs/phone_files.txt --json
```

## Options

| Option | Description |
|--------|-------------|
| `--input-list <file>` | One `<prefix>_phone.txt` path per line |
| `--ophone <file>` | Explicit matching `<prefix>_ophone.txt` |
| `-p, --prefix <name>` | Output prefix |
| `--outdir <dir>` | Output directory |
| `--table` | Write table output |
| `--json` | Write JSON output |
| `--test` | Run metrics self-tests |

If no output flag is given, table output is enabled automatically.

## Active Metrics

For both original and accentuated streams, metricalc reports:

- `%C`, `%V`
- `meanC`, `meanV`
- `ΔC`, `ΔV`
- `VarcoC`, `VarcoV`
- `rPVI-C`, `nPVI-V`

Pause intervals remain in the denominator for `%C` and `%V`, but are excluded
from `mean`, `Δ`, `Varco`, and PVI calculations.

The stage also reports the phonetizer drift summary consumed from
`metadata.data.phonetize.drift` in both streams.

## Structural Reporting

The metrics outputs keep the active structural inventory under the new input
contract. That includes:

- syllable counts and syllable-type distributions
- word, mora, merge, and accentuation statistics
- prominence statistics derived from phone-row structure
- pause metrics and pause-duration reporting
- speech-rate summaries for original and accentuated streams

Prominence statistics are computed internally from the phone-row representation.
There is no active explicit-link override flag.

## Notes

- Hiatus rows and vowel-transition rows are treated as consonantal intervals.
- Prominence statistics are derived from phone-row structure, not from `_tilde`
  front matter.
- `--explicit-link-count` is not part of the active CLI contract.
