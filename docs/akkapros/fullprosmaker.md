# Full Prosmaker CLI (`fullprosmaker.py`)

This document explains what `fullprosmaker.py` does, how to run it, and what files it produces.

Implementation:
- CLI wrapper: `src/akkapros/cli/fullprosmaker.py`
- Uses these libraries internally:
  - `src/akkapros/lib/syllabify.py`
  - `src/akkapros/lib/prosody.py`
  - `src/akkapros/lib/metrics.py`
  - `src/akkapros/lib/print.py`

## Purpose

`fullprosmaker.py` runs the complete Akkadian processing pipeline in one command.

Pipeline stages:
1. Syllabify (`*_proc.txt` -> `*_syl.txt`)
2. prosody realization (`*_syl.txt` -> `*_tilde.txt`)
3. Metrics (`*_tilde.txt` -> table/json/csv)
4. Print outputs (`*_tilde.txt` -> accent outputs)

It centralizes shared options (`--prefix`, `--outdir`, extra phonetic symbols) and writes all selected outputs in one run.

## Input And Core Outputs

Input:
- One processed text file, typically `<prefix>_proc.txt` from `atfparser.py`.

Core outputs:
- `<prefix>_syl.txt`
- `<prefix>_tilde.txt`

Optional metrics outputs:
- `<prefix>_metrics.txt` (table)
- `<prefix>.json`
- `<prefix>.csv`

Optional print outputs:
- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`
- `<prefix>_xar.txt`

## Command Syntax

```bash
python src/akkapros/cli/fullprosmaker.py <input_proc.txt> [options]
```

## Option Groups

### Shared I/O

- `--version`
- `-p, --prefix <name>`
- `--outdir <dir>`

### Syllabifier Options

- `--extra-vowels <chars>`
- `--extra-consonants <chars>`
- `--syl-merge-hyphens`
- `--syl-merge-lines`

Notes:
- Default line behavior is preserve-lines (unless `--syl-merge-lines` is set).

### Prosmaker Options

- `--prosody-style {lob,sob}` (default: `lob`)
- `--prosody-relax-last`

Notes:
- Diphthong restoration is always applied in the prosody realization stage.
- The temporary split marker is removed from final `_tilde.txt` output.

### Metricser Options

- `--metrics-table`
- `--metrics-json`
- `--metrics-csv`
- `--metrics-wpm <float>` (default: `165`)
- `--metrics-pause-ratio <float>` (default: `35`)
- `--metrics-long-punct-weight <float>` (default: `2.0`)

Defaults:
- If no metrics format flag is provided, table output is enabled automatically.

### Printer Options

- `--print-acute`
- `--print-bold`
- `--print-ipa`
- `--print-ipa-pharyngeal {preserve,remove}`
- `--print-circ-hiatus`
- `--print-xar`
  - Writes both XAR files: accented (`<prefix>_accent_xar.txt`) and plain (`<prefix>_xar.txt`).

Defaults:
- If no print output is selected, `--print-acute` and `--print-bold` are enabled automatically.

`--print-circ-hiatus` note:
- Speculative IPA mode for circumflex hiatus splitting (example: `qÃ» -> qÊŠ.ÊŠ`).

## Test Modes

`fullprosmaker.py` can run stage-specific tests without processing an input file.

- `--test-syllabify`
- `--test-prosody realization`
- `--test-diphthongs`
- `--test-metrics`
- `--test-print`
- `--test-cli`
- `--test-all`

## Typical Usage

Minimal full run:

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra --outdir outputs
```

Run with explicit prosody realization style and metrics table:

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
  -p erra \
  --outdir outputs \
  --prosody-style lob \
  --metrics-table
```

Run with machine-readable metrics (diphthongs restore automatically):

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
  -p erra \
  --outdir outputs \
  --metrics-json --metrics-csv
```

Run with IPA and speculative circumflex hiatus mode:

```bash
python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
  -p erra \
  --outdir outputs \
  --print-ipa \
  --print-ipa-pharyngeal remove \
  --print-circ-hiatus
```

Run full test suite:

```bash
python src/akkapros/cli/fullprosmaker.py --test-all
```

## Stage Order And Internal Behavior

Execution order is fixed:
1. Syllabification is always run first and saved.
2. prosody realization is always run second and saved.
3. Metrics are computed from prosody-realized output.
4. Print outputs are generated from prosody-realized output.

The command exits with non-zero status if any stage fails.

## Related Commands

Single-stage CLIs:
- `atfparser.py`
- `syllabifier.py`
- `prosmaker.py`
- `metricser.py`
- `printer.py`

Use those when you need isolated stage debugging; use `fullprosmaker.py` for one-command production runs.




