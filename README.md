# Akkadian Prosody Toolkit (akkapros)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![DOI](https://zenodo.org/badge/1158133867.svg)](https://doi.org/10.5281/zenodo.19010721)

A computational toolkit for reconstructing Babylonian accentuation. Processes phonological texts, applies a novel accentuation prosody realization algorithm, computes acoustic metrics (VarcoC, ΔC, %V), and generates publication-ready output in multiple formats.

Developed for Assyriologists, historical linguists, and digital humanities researchers working with Akkadian literary texts.

---

## 📋 Overview

The Akkadian Prosody Toolkit addresses a fundamental problem in Assyriology: the standard moraic stress model describes *where* accent *could* fall, but not *how* it was realized in connected speech. This toolkit implements a computational solution:

1. **Parse** ATF files from the electronic Babylonian Library (eBL)
2. **Syllabify** according to standard Akkadian rules
3. **prosody realization** accentuation patterns using a phrase-level algorithm
4. **Compute** acoustic metrics (%V, ΔC, VarcoC)
5. **Generate** outputs for publication and speech synthesis

For release planning/versioning, see `docs/akkapros/release-strategy.md`.
For metrics methodology and formulas, see `docs/akkapros/metrics-computation.md`.

Documentation
- Full developer and CLI documentation is under `docs/akkapros/` and packaged CLI docs are copied into the installed package. A brief Getting Started guide is at `docs/GETTING_STARTED.md`.

---

## 🔧 Tools Included

| Program | Version | Description |
|---------|---------|-------------|
| `atfparser.py` | 1.0.0 | Converts eBL ATF files to clean phonological text |
| `syllabify.py` | 1.0.0 | Syllabifies Akkadian text following Huehnergard (2011) |
| `prosmaker.py` | 1.0.0 | Applies accentuation prosody realization algorithm |
| `metricalc.py` | 1.0.0 | Computes acoustic metrics from prosody-realized text |
| `fullprosmaker.py` | 1.0.0 | Runs syllabify + prosody realization + metrics + print in one command |
| `printer.py` | 1.0.0 | Converts `*_tilde.txt` to accent text, bold markdown, IPA, and XAR outputs |

---

## 🚀 Quick Start — use the demo scripts

The repository ships ready-to-run demo scripts that exercise the full
pipeline on sample inputs. The demos read sources from `data/samples/` and
write outputs to `demo/akkapros/prosmaker/results/`.

Windows (PowerShell) demo:

```powershell
.\demo\akkapros\prosmaker\corpus-demo.ps1
```

Unix demo:

```bash
./demo/akkapros/prosmaker/corpus-demo.sh
```

The demo scripts run the full pipeline (parse → syllabify → prosody realization → metrics
→ outputs). Use `demo/akkapros/prosmaker/results/` to inspect generated `_syl`, `_tilde`,
metrics and accent outputs.

To prepare phone-level datasets (MBROLA, manifests) use the `akkapros` phoneprep demo:

```powershell
.\demo\akkapros\prosmaker\corpus-demo.ps1   # runs akkapros pipeline
.\demo\akkapros\phoneprep\phoneprep-demo.ps1 # runs akkapros phoneprep and dataset prep
```

Source files for demos are under `data/samples/` and demo outputs are in
`demo/akkapros/prosmaker/results/` and `demo/akkapros/phoneprep/results/`.

---

## 🖨️ Accent Printer CLI (`printer.py`)

`printer.py` reads `*_tilde.txt` and produces reading outputs:

- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`
- `<prefix>_xar.txt`

### Marker behavior

- `+` (`WORD_LINKER`): emitted as `‿` (no prosodic pause) in final outputs.
- `·` (`SYL_SEPARATOR`): removed from final text outputs (used only in intermediate/syllabified formats).
- `-` (`HYPHEN`): preserved as an orthographic boundary; when the syllabifier is run with `--merge-hyphen` the hyphen may be treated as a syllable separator.
- Prosody-realization marker `~` is rendered as `´` in XAR and as stress/length markers in IPA output.
- In IPA mode, punctuation is emitted as tagged clusters followed by a prosody marker:
  - weak/inner punctuation -> `|`
	- strong/final punctuation -> `‖`
- Bracketed chunks are emitted in IPA mode as `⟨escape:...⟩` so their contents are preserved verbatim.
- Content inside square brackets (`[ ... ]`) is preserved verbatim in non-IPA outputs (useful for foreign-language glosses or editorial notes).

### IPA mode selection

IPA output is enabled with `--ipa`. Use `--ipa-proto-semitic {preserve,replace}` to select the phonological profile that controls pharyngeal/glottal symbol mapping:

- `preserve`: preserve Proto-Semitic/pharyngeal distinctions (keeps letter glottals and pharyngeal contrasts in IPA output).
- `replace`: apply the Old Babylonian-style merger (map conservative pharyngeal symbols to merged IPA symbols).

`--ipa` only enables IPA output; `--ipa-proto-semitic` chooses how symbols are mapped.

Historical rationale: these weak consonants were already largely lost in Old Babylonian connected speech, while they are older in Old Akkadian. Their later written presence can be conservative scribal traditionalism rather than direct phonetic realization.

### XAR orthography profile

- XAR output is available both in `printer.py --xar` and in the full pipeline `fullprosmaker.py --print-xar`.
- Selecting XAR writes two files: `<prefix>_accent_xar.txt` and `<prefix>_xar.txt`.
- Consonant remap includes distinct emphatic/base channels (e.g., `q -> ꝗ`, `ṭ -> ꞓ`, `ṣ -> ɉ`, `š -> x̌`).
- Vowel strategy uses doubled notation for long vowels while preserving macron/circumflex classes:
	- default: `ā -> aa`, `ī -> ii`, `ū -> uu`, `ē -> ee`, `â -> eâ`, `î -> eî`, `û -> iû`, `ê -> aê`
	- emphatic: `ā -> àa`, `ī -> ìi`, `ū -> ùu`, `ē -> èe`, `â -> èâ`, `î -> èî`, `û -> ìû`, `ê -> àê`
- Design rationale: macron vowels are written as pure doubled vowels (`aa/ii/uu/ee`), while circumflex vowels are encoded as mixed pairs where the second slot carries the circumflex (`eâ/eî/iû/aê`). This gives a visual cue that the second vowel is dominant while preserving a clear keyboard-friendly contrast between macron and circumflex series.
- Processing order for XAR is: consonant substitution -> vowel substitution -> accent-mark handling.
- Current policy keeps apostrophe realizations for `ʿ` and `ʾ` in both XAR outputs.

### Emphatic vowel coloring

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

# write IPA with Old Akkadian pharyngeals preserved (default)
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --ipa --ipa-proto-semitic preserve

# write IPA with Old Babylonian pharyngeal merger
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --ipa --ipa-proto-semitic replace

# write XAR outputs (accented and plain)
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --xar

# run self-tests
python3 src/akkapros/cli/printer.py --test
```

`--test` runs both:
- printer CLI option-resolution checks (including `--ipa-proto-semitic preserve|replace`)
- `akkapros.lib.print.run_tests()` conversion checks

---

Use `fullprosmaker.py` when you want to run the full pipeline (`syllabifier` → `prosmaker` → `metricalc` → `printer`) in one command.

### Input and outputs

- **Input**: Akkadian processed text (typically `*_proc.txt`)
- **Always written**:
	- `<prefix>_syl.txt`
	- `<prefix>_tilde.txt`
- **Metrics outputs**: selected by flags (`--metrics-table`, `--metrics-json`, `--metrics-csv`)
	- If no metrics format is selected, `--metrics-table` is used by default.
- **Accent outputs**: selected by flags (`--print-acute`, `--print-bold`, `--print-ipa`, `--print-xar`)
	- If no accent format is selected, `--print-acute` and `--print-bold` are used by default.


- `-p, --prefix`: shared prefix for all outputs
- `--outdir`: shared output directory
- `--extra-vowels`, `--extra-consonants`: applied to syllabify and metrics

### Stage-specific options

- **Syllabification**: `--syl-merge-hyphens`, `--syl-merge-lines`
- **prosody realization**: `--prosody-style {lob,sob}` (default: `sob`), `--prosody-relax-last`
	- Diphthong restoration is always applied after prosody realization; split markers never appear in `_tilde.txt` output.
- **Metrics**: `--metrics-wpm`, `--metrics-pause-ratio`, `--metrics-weak-punct-weight`, `--metrics-strong-punct-weight`, `--metrics-table`, `--metrics-json`, `--metrics-csv`
- **Printer**: `--print-acute`, `--print-bold`, `--print-ipa`, `--print-ipa-proto-semitic {preserve,replace}`, `--print-xar`
	- Test flags: `--test` (all printer-side tests live in internal `run_tests()` flows)

### Line handling (default vs merge)

- Default mode (no flag):
	- original input lines are preserved as-is
	- no newline normalization is applied
	- useful when line boundaries encode phrasing/verse structure
- `--syl-merge-lines` mode:
	- single newline is treated as line-wrap continuation and normalized to one space
	- two or more consecutive newlines are treated as paragraph boundaries and normalized to one newline
- Markdown-aware exception in merge mode:
	- structural Markdown lines are not merged across a single newline (headings, list items, blockquotes, horizontal rules, table rows/separators, fenced code blocks)
- Hyphen/plus split rejoin still runs before line normalization in both modes.

### Examples

```bash
# SOB style (default), metrics table output
python3 src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra --outdir outputs --metrics-table

# SOB style with JSON and CSV metrics
python3 src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra_sob --outdir outputs --prosody-style sob --metrics-json --metrics-csv

# Diphthongs are restored automatically in prosody realization stage
python3 src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra_diph --outdir outputs --metrics-table

# Write only IPA accent output (skip acute/bold)
python3 src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra_ipa --outdir outputs --print-ipa --metrics-table

# Write only XAR outputs (accented and plain; skip acute/bold/ipa)
python3 src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra_xar --outdir outputs --print-xar --metrics-table

# Allow explicit + prosody realization propagation before the last linked word
python3 src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra_relax --outdir outputs --prosody-style sob --prosody-relax-last --metrics-table

# Merge lines in the syllabification stage (default is preserve)
python3 src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt -p erra_lines --outdir outputs --syl-merge-lines --metrics-table

# Run integrated tests for all stages
python3 src/akkapros/cli/fullprosmaker.py --test-all

# Run fullprosmaker CLI option-resolution tests only
python3 src/akkapros/cli/fullprosmaker.py --test-cli

```

### Internal testing policy

-- Project tests for the printer/IPA profile logic are implemented in built-in `run_tests()` functions.
-- No external pytest module is required for validating `--ipa-proto-semitic` profile mapping (see `printer.py` and `fullprosmaker.py` built-in tests).

---

## 🧠 Moraic prosody realization algorithm (Current Behavior)

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

### 2) prosody realization operations

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

If an odd-mora content word cannot be prosody-realized internally:

1. **Forward merge** with following content words until the merged unit is even or prosody-realizable.
2. **Backward merge for trailing function-word groups** at punctuation/end (with rollback of earlier repairs when needed).
3. **Last resort** onset gemination when no merge path succeeds.

### 5) Function words

Function words are never stressed independently; they attach to neighboring content words:

- `u + ana + šarri → u+ana+šar·ri`

## 🔧 Prosmaker CLI (`prosmaker.py`)

`prosmaker.py` applies moraic prosody realization to `*_syl.txt` and writes `<prefix>_tilde.txt`.

### Explicit `+` linker behavior

`+` in `*_syl.txt` is treated as an explicit user-defined prosodic link:

- Linked sequences are parsed as a mandatory merged unit.
- **Default behavior**: strict tail-only prosody realization (only the last linked word is prosody realization-eligible).
- **Relaxed behavior** (`-r/--relax-last`): prosody realization may propagate leftward to previous linked words when needed.

Examples:

- Default: `bā·nû+a·pil¦ → bā·nû+~a·pil`
- Relaxed (`--relax-last`): `bā·nû+a·pil¦ → bā·nû~+a·pil`

Usage:

```bash
# strict tail-only linked prosody realization (default)
python3 src/akkapros/cli/prosmaker.py outputs/erra_syl.txt -p erra --outdir outputs

# explicit LOB style (non-default)
python3 src/akkapros/cli/prosmaker.py outputs/erra_syl.txt -p erra --outdir outputs --style lob

# relaxed linked prosody realization propagation
python3 src/akkapros/cli/prosmaker.py outputs/erra_syl.txt -p erra --outdir outputs --relax-last
```

### 7) Hyphen behavior

`-` is preserved as an intra-word prosodic marker (construct chains, enclitics, compounds) and behaves like a syllable boundary for prosody realization parsing.

### 8) Output markers

Current prosody realization output conventions:

- `~` after prosody-realized syllable
- `+` between merged/linked words in prosodic units
- `·` and `-` preserved as syllable/prosodic boundaries
- spaces for non-merged word boundaries




