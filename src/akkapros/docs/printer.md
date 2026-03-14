# Printer CLI (`printer.py`)

This document explains what `printer.py` does, how to run it, and what output formats it writes.

Implementation:
- CLI wrapper: `src/akkapros/cli/printer.py`
- Core formatter library: `src/akkapros/lib/print.py`

## Purpose

`printer.py` converts prosody-realized pivot text (`*_tilde.txt`) into user-facing reading and phonetic outputs.

Supported outputs:
- Acute-mark text
- Bold-mark text (Markdown)
- IPA
- XAR transliteration
- MBROLA/X-SAMPA-like output

## Input And Output

Input:
- One `*_tilde.txt` file.

Outputs (by selected flags):
- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`
- `<prefix>_xar.txt`
- `<prefix>_accent_mbrola.txt`

If no output flags are selected, default output is:
- acute + bold

## Command Syntax

```bash
python src/akkapros/cli/printer.py <input_tilde.txt> [options]
```

## Options

- `--version`
  - Print CLI version.
- `-p, --prefix <name>`
  - Output prefix.
- `--outdir <dir>`
  - Output directory (default: current directory).

Output selectors:
- `--acute`
- `--bold`
- `--ipa`
- `--xar`
  - Writes both XAR files: accented (`<prefix>_accent_xar.txt`) and plain (`<prefix>_xar.txt`).
- `--mbrola`

IPA-specific options:
- `--ipa-proto-semitic {preserve,replace}`
  - `preserve`: strict mode (Old Akkadian distinctions).
  - `remove`: OB-style pharyngeal merger.
- `--circ-hiatus`
  - Speculative mode splitting circumflex vowels into hiatus in IPA.
  - Example: `qû -> qʊ.ʊ`.

Testing:
- `--test`
  - Run CLI and library printer tests.

## Typical Usage

Default outputs (acute + bold):

```bash
python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
  -p erra --outdir outputs
```

IPA output with OB pharyngeal policy:

```bash
python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
  --ipa --ipa-proto-semitic replace \
  -p erra --outdir outputs
```

IPA output with speculative circumflex hiatus:

```bash
python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
  --ipa --circ-hiatus \
  -p erra --outdir outputs
```

Generate all display outputs:

```bash
python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
  --acute --bold --ipa --xar --mbrola \
  -p erra --outdir outputs
```

Run tests:

```bash
python src/akkapros/cli/printer.py --test
```

## Pipeline Position

`printer.py` is typically run after prosody realization:
1. `atfparser.py`
2. `syllabifier.py`
3. `prosmaker.py` -> `*_tilde.txt`
4. `printer.py`

For one-command processing with optional print stage included, see `fullprosmaker.py`.



