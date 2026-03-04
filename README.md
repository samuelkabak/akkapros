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
| `fullreparer.py` | 1.0.0 | Runs syllabify + repair + metrics + print in one command |
| `printer.py` | 1.0.0 | Converts `*_tilde.txt` to accent text, bold markdown, IPA, and XAR outputs |

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

# Full pipeline in one command (writes _syl, _tilde, metrics, and accent outputs)
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra --outdir outputs --table

# Accent rendering from *_tilde.txt (writes both outputs by default)
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs

```

---

## 🖨️ Accent Printer CLI (`printer.py`)

`printer.py` reads `*_tilde.txt` and produces reading outputs:

- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`

### Marker behavior

- `+` (`WORD_LINKER`) → `‿`
- `·` (`SYL_SEPARATOR`) removed in final output
- `-` (`HYPHEN`) preserved
- `~` marks the preceding syllable:
	- in `accent_acute`: replaced by `´`
	- in `accent_bold`: removed and the host syllable is bolded
	- in `accent_ipa`: converted to IPA length (`ː`) and stress (`ˈ`) markers
	- in `accent_xar`: replaced by `´` on the repaired segment in XAR orthography
- in `accent_xar`, glottal letters `ʿ` and `ʾ` are removed in final output (Old Babylonian profile); glottal-cleanup rules are kept as a protective normalization when input includes forms from other Akkadian periods/regions (e.g., Old Akkadian, Standard Babylonian, Assyrian Akkadian)
- in IPA mode, spaces emit `⟨pause⟩ (.)`
- in IPA mode, punctuation emits symbolic tags and a clustered punctuation pause `(..)`
- in IPA mode, bracket chunks are emitted as `⟨escape:[...]⟩`
- content inside square brackets `[ ... ]` remains untouched in non-IPA outputs (for markdown URI safety)

### XAR orthography profile

- XAR output is available both in `printer.py --xar` and in the full pipeline `fullreparer.py --xar`.
- Consonant remap includes distinct emphatic/base channels (e.g., `q -> ꝗ`, `ṭ -> ꞓ`, `ṣ -> ɉ`, `š -> x̌`).
- Vowel strategy uses doubled notation for long vowels while preserving macron/circumflex classes:
	- default: `ā -> aa`, `ī -> ii`, `ū -> uu`, `ē -> ee`, `â -> aạ`, `î -> iị`, `û -> uụ`, `ê -> eẹ`
	- emphatic: `ā -> àa`, `ī -> ìi`, `ū -> ùu`, `ē -> èe`, `â -> àạ`, `î -> ìị`, `û -> ùụ`, `ê -> èẹ`
- Processing order for XAR is: consonant substitution -> glottal cleanup rules -> vowel substitution.
- Old Babylonian profile: `ʿ` and `ʾ` are removed in final XAR output. Cleanup rules are kept as protection for inputs from other Akkadian periods/regions.

### Emphatic vowel coloring

In this system, the four plain vowel phonemes `/a, i, u, e/` undergo systematic allophonic variation when adjacent to emphatic consonants (including the uvular plosive `/q/`), based on the physical constraint of tongue root retraction (pharyngealization). Drawing on MRI evidence of articulatory constraints and validated by native Levantine Arabic speaker intuition, the resulting emphatic allophones are: `/a/ → [ɑ]` (backed, unrounded), `/i/ → [ɨ]` (centralized/backed), `/u/ → [ʊ]` (slightly lowered), and `/e/ → [ɛ]` (lowered and backed). This mapping prioritizes physiological plausibility over dialectal variation, ensuring consistent and natural emphatic coloring across the inventory.

### Usage

```bash
# write both outputs (default)
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs

# write only accent text
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --acute

# write only bold markdown
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --bold

# write only IPA output
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --ipa

# write only XAR output
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --xar

# run self-tests
python3 src/akkapros/cli/printer.py --test
```

---

## ⚡ Full Pipeline CLI (`fullreparer.py`)

Use `fullreparer.py` when you want to run the full pipeline (`syllabifier` → `repairer` → `metricser` → `printer`) in one command.

### Input and outputs

- **Input**: Akkadian processed text (typically `*_proc.txt`)
- **Always written**:
	- `<prefix>_syl.txt`
	- `<prefix>_tilde.txt`
- **Metrics outputs**: selected by flags (`--table`, `--json`, `--csv`)
	- If no metrics format is selected, `--table` is used by default.
- **Accent outputs**: selected by flags (`--acute`, `--bold`, `--ipa`, `--xar`)
	- If no accent format is selected, `--acute` and `--bold` are used by default.

### Shared options (deduplicated)

- `-p, --prefix`: shared prefix for all outputs
- `--outdir`: shared output directory
- `--extra-vowels`, `--extra-consonants`: applied to syllabify and metrics

### Stage-specific options

- **Syllabification**: `--merge-hyphen`
- **Repair**: `--style {lob,sob}` (default: `sob`), `-r/--relax-last`, `--restore-diphthongs`, `--only-restore-diphthongs`
- **Metrics**: `--wpm`, `--pause-ratio`, `--punct-weight`, `--table`, `--json`, `--csv`
- **Printer**: `--acute`, `--bold`, `--ipa`, `--xar`

### Examples

```bash
# SOB style (default), metrics table output
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra --outdir outputs --table

# SOB style with JSON and CSV metrics
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra_sob --outdir outputs --style sob --json --csv

# Restore diphthongs in repair stage
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra_diph --outdir outputs --restore-diphthongs --table

# Write only IPA accent output (skip acute/bold)
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra_ipa --outdir outputs --ipa --table

# Write only XAR accent output (skip acute/bold/ipa)
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra_xar --outdir outputs --xar --table

# Allow explicit + repair propagation before the last linked word
python3 src/akkapros/cli/fullreparer.py outputs/erra_proc.txt -p erra_relax --outdir outputs --style sob --relax-last --table

# Run integrated tests for all stages
python3 src/akkapros/cli/fullreparer.py --test-all

```

---

## 🧠 Moraic Repair Algorithm (Current Behavior)

### 1) Syllable classification

Each syllable is classified by structure and mora count:

| Type | Structure | Morae | Example |
|---|---|---:|---|
| `CV` | consonant + short vowel | 1 | `ša` |
| `V` | short vowel (initial) | 1 | `a` |
| `CVC` | closed short | 2 | `šar` |
| `VC` | closed short (initial) | 2 | `ap` |
| `CVV` | open long | 2 | `bā` |
| `VV` | open long (initial) | 2 | `ī` |
| `CVVC` | closed long | 3 | `nāš` |
| `VVC` | closed long (initial) | 3 | `ān` |

### 2) Repair operations

When a target syllable is selected, exactly one mora is added:

| Operation | Applies to | Effect | Example |
|---|---|---|---|
| Vowel lengthening | `CVV`, `VV`, `CVVC`, `VVC` | long vowel becomes extra-long | `rā → rā~` |
| Coda gemination | `CVC`, `VC` (non-final in unit) | coda consonant geminated | `dad → dad~` |
| Onset gemination (last resort) | `CV`, `V` | onset geminated; for vowel-initial, glottal gemination | `ka → k~a`, `a → ~a` |

### 3) Accent styles

Two styles are implemented and differ only in candidate priority:

- **LOB**: final superheavy (incl. circumflex finals) > rightmost non-final heavy > final heavy
- **SOB**: rightmost non-final heavy > final heavy

### 4) Merge logic

If an odd-mora content word cannot be repaired internally:

1. **Forward merge** with following content words until the merged unit is even or repairable.
2. **Backward merge for trailing function-word groups** at punctuation/end (with rollback of earlier repairs when needed).
3. **Last resort** onset gemination when no merge path succeeds.

### 5) Function words

Function words are never stressed independently; they attach to neighboring content words:

- `u + ana + šarri → u+ana+šar·ri`

## 🔧 Repairer CLI (`repairer.py`)

`repairer.py` applies moraic repair to `*_syl.txt` and writes `<prefix>_tilde.txt`.

### Explicit `+` linker behavior

`+` in `*_syl.txt` is treated as an explicit user-defined prosodic link:

- Linked sequences are parsed as a mandatory merged unit.
- **Default behavior**: strict tail-only repair (only the last linked word is repair-eligible).
- **Relaxed behavior** (`-r/--relax-last`): repair may propagate leftward to previous linked words when needed.

Examples:

- Default: `bā·nû+a·pil¦ → bā·nû+~a·pil`
- Relaxed (`--relax-last`): `bā·nû+a·pil¦ → bā·nû~+a·pil`

Usage:

```bash
# strict tail-only linked repair (default)
python3 src/akkapros/cli/repairer.py outputs/erra_syl.txt -p erra --outdir outputs

# explicit LOB style (non-default)
python3 src/akkapros/cli/repairer.py outputs/erra_syl.txt -p erra --outdir outputs --style lob

# relaxed linked repair propagation
python3 src/akkapros/cli/repairer.py outputs/erra_syl.txt -p erra --outdir outputs --relax-last
```

### 7) Hyphen behavior

`-` is preserved as an intra-word prosodic marker (construct chains, enclitics, compounds) and behaves like a syllable boundary for repair parsing.

### 8) Output markers

Current repair output conventions:

- `~` after repaired syllable
- `+` between merged/linked words in prosodic units
- `·` and `-` preserved as syllable/prosodic boundaries
- spaces for non-merged word boundaries
