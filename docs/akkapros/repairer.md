# Repairer CLI (`repairer.py`)

This document describes what the repairer does, how to run it, and what files it reads/writes.

Implementation:
- CLI wrapper: `src/akkapros/cli/repairer.py`
- Core logic: `src/akkapros/lib/repair.py`

## Purpose

`repairer.py` applies moraic repair to syllabified Akkadian text.

It takes input produced by the syllabifier (`*_syl.txt`) and creates the repaired pivot format (`*_tilde.txt`), which is used by downstream modules (metrics, printer, full pipeline).

## Input And Output

Input:
- A syllabified file, typically `<prefix>_syl.txt`.

Output:
- A repaired file `<prefix>_tilde.txt`.
- If `-p/--prefix` is provided, output is `<outdir>/<prefix>_tilde.txt`.
- If no prefix is provided, output is derived from input stem (with `_syl` removed when present).

## Command Syntax

```bash
python src/akkapros/cli/repairer.py <input_syl.txt> [options]
```

## Options

- `--version`
  - Print CLI version.
- `-p, --prefix <name>`
  - Output prefix. Result file is `<prefix>_tilde.txt`.
- `--outdir <dir>`
  - Output directory. Default: current directory.
- `--style {lob,sob}`
  - Accent style used to choose repair target syllables.
  - Default: `lob`.
- `-r, --relax-last`
  - For explicit `+` links, allow repair propagation before the last linked word.
- `--restore-diphthongs`
  - Restore diphthongs by removing inserted glottal stops after repair.
- `--only-restore-diphthongs`
  - Only restore diphthongs, skip the repair algorithm.
- `--test`
  - Run standard repair tests.
- `--test-diphthongs`
  - Run diphthong-restoration tests.

## Typical Usage

Run with defaults:

```bash
python src/akkapros/cli/repairer.py outputs/erra_syl.txt
```

Run with explicit style and output location:

```bash
python src/akkapros/cli/repairer.py outputs/erra_syl.txt \
  --style lob \
  -p erra \
  --outdir outputs
```

Run with diphthong restoration:

```bash
python src/akkapros/cli/repairer.py outputs/erra_syl.txt \
  --restore-diphthongs \
  -p erra \
  --outdir outputs
```

Only restore diphthongs (no new repairs):

```bash
python src/akkapros/cli/repairer.py outputs/erra_syl.txt \
  --only-restore-diphthongs \
  -p erra_restored \
  --outdir outputs
```

Run tests:

```bash
python src/akkapros/cli/repairer.py --test
python src/akkapros/cli/repairer.py --test-diphthongs
```

## Pipeline Position

Standard pipeline stage order:
1. `atfparser.py` -> `*_proc.txt`
2. `syllabifier.py` -> `*_syl.txt`
3. `repairer.py` -> `*_tilde.txt`
4. `metricser.py` and `printer.py` consume `*_tilde.txt`

## Notes

- `repairer.py` is the current CLI name (not `reparer.py`).
- Output prefix is sanitized to a filesystem-safe filename.
- For one-command execution of all stages, see `fullreparer.py`.
