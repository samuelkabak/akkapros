# Akkadian Prosody Toolkit (akkapros)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A computational toolkit for reconstructing Babylonian accentuation. Processes phonological texts, applies a novel accentuation repair algorithm, computes acoustic metrics (VarcoC, ΔC, %V), and generates publication-ready output in multiple formats.

Developed for Assyriologists, historical linguists, and digital humanities researchers working with Akkadian literary texts.

---

## 📋 Overview

The Akkadian Prosody Toolkit addresses a fundamental problem in Assyriology: the standard moraic stress model describes *where* accent *could* fall, but not *how* it was realized in connected speech. This toolkit implements a computational solution:

1. **Parse** ATF files from the electronic Babylonian Library (eBL)
2. **Syllabify** according to standard Akkadian rules
3. **Repair** accentuation patterns using a phrase-level algorithm
4. **Compute** acoustic metrics (%V, ΔC, VarcoC)
5. **Generate** outputs for publication and speech synthesis

---

## 🔧 Tools Included

| Program | Version | Description |
|---------|---------|-------------|
| `atfparser.py` | 1.0.0 | Converts eBL ATF files to clean phonological text |
| `syllabify.py` | 1.0.0 | Syllabifies Akkadian text following Huehnergard (2011) |
| `repairer.py` | 1.0.0 | Applies accentuation repair algorithm |
| `metricser.py` | 1.0.0 | Computes acoustic metrics from repaired text |
| `fullreparer.py` | 1.0.0 | Runs syllabify + repair + metrics in one command |
| `printer.py` | 1.0.0 | Converts `*_tilde.txt` to accent text and accent markdown outputs |
| `format.py` | 1.0.0 | Generates Markdown, LaTeX, and IPA output |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/samuelkabak/akkapros.git
cd akkapros

# Process an ATF file
python3 src/atfparser.py texts/erra.atf -p erra --outdir outputs

# Syllabify and repair
python3 src/repairer.py erra_proc.txt -p erra --outdir outputs

# Compute metrics
python3 src/akkapros/cli/metricser.py erra.tilde > erra_metrics.txt

# Full pipeline in one command (writes _syl, _tilde and metrics outputs)
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra --outdir outputs --table

# Accent rendering from *_tilde.txt (writes both outputs by default)
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs

# Generate publication outputs
python3 src/format.py erra.tilde --md --tex --ipa

```

---

## 🖨️ Accent Printer CLI (`printer.py`)

`printer.py` reads `*_tilde.txt` and produces reading outputs:

- `<prefix>_accent_accute.txt`
- `<prefix>_accent_bold.md`

### Marker behavior

- `+` (`TIL_WORD_LINKER`) → `‿`
- `·` (`SYL_SEPARATOR`) removed in final output
- `-` (`HYPHEN`) preserved
- `~` marks the preceding syllable:
	- in `accent_accute`: replaced by `´`
	- in `accent_bold`: removed and the host syllable is bolded
- content inside square brackets `[ ... ]` is left untouched (for markdown URI safety)

### Usage

```bash
# write both outputs (default)
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs

# write only accent text
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --accute

# write only bold markdown
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --bold

# run self-tests
python3 src/akkapros/cli/printer.py --test
```

---

## ⚡ Full Pipeline CLI (`fullreparer.py`)

Use `fullreparer.py` when you want to avoid running `syllabify`, `repairer`, and `metricser` separately.

### Input and outputs

- **Input**: Akkadian processed text (typically `*_proc.txt`)
- **Always written**:
	- `<prefix>_syl.txt`
	- `<prefix>_tilde.txt`
- **Metrics outputs**: selected by flags (`--table`, `--json`, `--csv`)
	- If no metrics format is selected, `--table` is used by default.

### Shared options (deduplicated)

- `-p, --prefix`: shared prefix for all outputs
- `--outdir`: shared output directory
- `--extra-vowels`, `--extra-consonants`: applied to syllabify and metrics

### Stage-specific options

- **Syllabification**: `--merge-hyphen`
- **Repair**: `--style {lob,sob}`, `--restore-diphthongs`, `--only-restore-diphthongs`
- **Metrics**: `--wpm`, `--pause-ratio`, `--punct-weight`, `--table`, `--json`, `--csv`

### Examples

```bash
# LOB style, metrics table output
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra --outdir outputs --style lob --table

# SOB style with JSON and CSV metrics
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra_sob --outdir outputs --style sob --json --csv

# Restore diphthongs in repair stage
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra_diph --outdir outputs --restore-diphthongs --table

# Run integrated tests for all three stages
python3 src/akkapros/cli/fullreparer.py --test-all

```
