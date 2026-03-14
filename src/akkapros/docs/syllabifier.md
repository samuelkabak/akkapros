# Syllabifier CLI (`syllabifier.py`)

This document explains what `syllabifier.py` does, how to run it, and what files it produces.

Implementation:
- CLI wrapper: `src/akkapros/cli/syllabifier.py`
- Core syllabification library: `src/akkapros/lib/syllabify.py`

## Purpose

`syllabifier.py` converts cleaned Akkadian text into syllabified form used by the prosody realization stage.

It inserts syllable boundaries and marks word endings in the toolkit internal format.

## Input And Output

Input:
- Typically `<prefix>_proc.txt` from `atfparser.py`.

Output:
- `<prefix>_syl.txt` in `--outdir`.

By default, if no `--prefix` is provided, output prefix is derived from input stem.

## Command Syntax

```bash
python src/akkapros/cli/syllabifier.py <input_proc.txt> [options]
```

## Options

- `--version`
  - Print CLI version.
- `-p, --prefix <name>`
  - Output prefix.
- `--outdir <dir>`
  - Output directory (default: current directory).
- `--extra-vowels <chars>`
  - Additional vowel characters.
- `--extra-consonants <chars>`
  - Additional consonant characters.
- `--merge-hyphen`
  - Merge hyphens into syllable separators.
- `--merge-lines`
  - Normalize line breaks (`1 newline -> space`, `2+ -> paragraph break`).
  - Default behavior preserves original lines.
- `--test`
  - Run internal syllabifier tests.

## Output Format Markers

Common markers used in `*_syl.txt`:
- `·`: syllable separator.
- `¦`: word-ending marker.
- `-`: hyphen boundary (unless merged).
- `+`: linker boundary.
- `‹...›`: escaped punctuation/non-word segments.

## Typical Usage

Basic run:

```bash
python src/akkapros/cli/syllabifier.py outputs/erra_proc.txt \
  -p erra \
  --outdir outputs
```

Merge hyphens and normalize line breaks:

```bash
python src/akkapros/cli/syllabifier.py outputs/erra_proc.txt \
  --merge-hyphen --merge-lines \
  -p erra --outdir outputs
```

Provide additional phonetic symbols:

```bash
python src/akkapros/cli/syllabifier.py outputs/text_proc.txt \
  --extra-vowels "ø" --extra-consonants "ɣ" \
  -p text --outdir outputs
```

Run tests:

```bash
python src/akkapros/cli/syllabifier.py --test
```

## Important Processing Notes

- The library may insert glottal stops between adjacent vowels for diphthong expansion.
- Hyphen and linker behavior is context-sensitive.
- Punctuation is preserved as escaped material, not syllabified as Akkadian words.

## Pipeline Position

Typical pipeline order:
1. `atfparser.py`
2. `syllabifier.py`
3. `prosmaker.py`
4. `metricalc.py` / `printer.py`

For a one-command run of all stages, use `fullprosmaker.py`.


