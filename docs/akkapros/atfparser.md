# ATF Parser CLI (`atfparser.py`)

This document explains what `atfparser.py` does, how to run it, and what files it produces.

Implementation:
- CLI wrapper: `src/akkapros/cli/atfparser.py`
- Core parser library: `src/akkapros/lib/atfparse.py`

## Purpose

`atfparser.py` converts eBL ATF files into clean Akkadian text for the prosody pipeline.

It is designed for phonetic/prosodic processing, not full scholarly ATF structure preservation.

Main behavior:
- Extract Akkadian from `%n` lines.
- Extract English translation from `#tr.en:` lines.
- Ignore unrelated metadata lines.
- Normalize editorial markup to readable, pipeline-ready text.

## Input And Output

Input:
- An eBL ATF file containing `%n` lines.

Outputs (in `--outdir`):
- `<prefix>_orig.txt`: original Akkadian `%n` text with markup preserved.
- `<prefix>_proc.txt`: cleaned Akkadian text for syllabification/prosody realization.
- `<prefix>_trans.txt`: English translations, when present.

## Command Syntax

```bash
python src/akkapros/cli/atfparser.py <input.atf> [options]
```

## Options

- `--version`
  - Print CLI version.
- `-p, --prefix <name>`
  - Output prefix (default: input filename stem).
- `--outdir <dir>`
  - Output directory (default: current directory).
- `--remove-hyphens`
  - Remove hyphens from cleaned output.
- `--preserve-case`
  - Keep original case (default behavior lowercases text).
- `--preserve-h`
  - Keep `h/H` unchanged (default maps to `á¸«/á¸ª`).
- `--strict`
  - Enable strict warning mode.
- `--test`
  - Run parser self-tests.
- `--append`
  - **Append to output files instead of overwriting.** If the output files already exist, new content is appended after a newline. Each appended block always starts at the beginning of a new line, never after the last character of the previous line. This ensures that every line in the output is properly separated, matching the line structure of the input ATF files.

## ATF Normalization Rules (Core)

Within Akkadian `%n` lines:
- `( )`, `[ ]`, `< >`: delimiters removed, content kept.
- `{ }`: removed.
- `|`: converted to space.
- `||`, `â€¡`, `â€”`, `â€“`: normalized to `:` phrase separator.
- `x` broken signs: collapsed to one `â€¦` marker.
- `? ! * Â°`: removed.
- Ellipsis preserved as `â€¦`.
- Numerals preserved.

## Typical Usage

Basic run:

```bash
python src/akkapros/cli/atfparser.py data/samples/"L I.5 Erra and IÅ¡um SB I.atf" \
  -p erra \
  --outdir outputs
```

Preserve case and h/H:

```bash
python src/akkapros/cli/atfparser.py data/samples/file.atf \
  --preserve-case --preserve-h \
  -p sample --outdir outputs
```

Run self-tests:

```bash
python src/akkapros/cli/atfparser.py --test
```

## Pipeline Position

Typical pipeline order:
1. `atfparser.py` -> `*_proc.txt`
2. `syllabifier.py` -> `*_syl.txt`
3. `prosmaker.py` -> `*_tilde.txt`
4. `metricser.py` and `printer.py`

## Notes

- This parser intentionally removes most structural metadata.
- Line breaks are preserved as meaningful textual structure for downstream processing.
- For end-to-end one-command processing, see `fullprosmaker.py`.


