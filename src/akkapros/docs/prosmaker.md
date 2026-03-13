# Prosmaker CLI (`prosmaker.py`)

This document describes what the prosmaker does, how to run it, and what files it reads/writes.

Implementation:
- CLI wrapper: `src/akkapros/cli/prosmaker.py`
- Core logic: `src/akkapros/lib/prosody.py`

## Purpose

`prosmaker.py` applies moraic prosody realization to syllabified Akkadian text.

It takes input produced by the syllabifier (`*_syl.txt`) and creates the prosody-realized pivot format (`*_tilde.txt`), which is used by downstream modules (metrics, printer, full pipeline).

## Input And Output

Input:
- A syllabified file, typically `<prefix>_syl.txt`.

Output:
- A prosody-realized file `<prefix>_tilde.txt`.
- If `-p/--prefix` is provided, output is `<outdir>/<prefix>_tilde.txt`.
- If no prefix is provided, output is derived from input stem (with `_syl` removed when present).

## Command Syntax

```bash
python src/akkapros/cli/prosmaker.py <input_syl.txt> [options]
```

## Options

- `--version`
  - Print CLI version.
- `-p, --prefix <name>`
  - Output prefix. Result file is `<prefix>_tilde.txt`.
- `--outdir <dir>`
  - Output directory. Default: current directory.
- `--style {lob,sob}`
  - Accent style used to choose prosody realization target syllables.
  - Default: `lob`.
- `-r, --relax-last`
  - For explicit `+` links, allow prosody realization propagation before the last linked word.
- Diphthongs are always restored after prosody realization.
  - Temporary split markers are removed systematically in output.
- `--test`
  - Run standard prosody realization tests.
- `--test-diphthongs`
  - Run diphthong-restoration tests.

## Typical Usage

Run with defaults:

```bash
python src/akkapros/cli/prosmaker.py outputs/erra_syl.txt
```

Run with explicit style and output location:

```bash
python src/akkapros/cli/prosmaker.py outputs/erra_syl.txt \
  --style lob \
  -p erra \
  --outdir outputs
```

Run prosody realization with automatic diphthong restoration:

```bash
python src/akkapros/cli/prosmaker.py outputs/erra_syl.txt \
  -p erra \
  --outdir outputs
```

Run tests:

```bash
python src/akkapros/cli/prosmaker.py --test
python src/akkapros/cli/prosmaker.py --test-diphthongs
```

## Pipeline Position

Standard pipeline stage order:
1. `atfparser.py` -> `*_proc.txt`
2. `syllabifier.py` -> `*_syl.txt`
3. `prosmaker.py` -> `*_tilde.txt`
4. `metricalc.py` and `printer.py` consume `*_tilde.txt`

## Notes

- `prosmaker.py` is the current CLI name (not `reparer.py`).
- Output prefix is sanitized to a filesystem-safe filename.
- For one-command execution of all stages, see `fullprosmaker.py`.



