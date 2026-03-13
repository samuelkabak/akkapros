# Akkadian Prosody Toolkit (akkapros)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A computational toolkit for reconstructing Babylonian accentuation. Processes phonological texts, applies a novel accentuation prosody realization algorithm, computes acoustic metrics (VarcoC, Î”C, %V), and generates publication-ready output in multiple formats.

Developed for Assyriologists, historical linguists, and digital humanities researchers working with Akkadian literary texts.

---

## ðŸ“‹ Overview

The Akkadian Prosody Toolkit addresses a fundamental problem in Assyriology: the standard moraic stress model describes *where* accent *could* fall, but not *how* it was realized in connected speech. This toolkit implements a computational solution:

1. **Parse** ATF files from the electronic Babylonian Library (eBL)
2. **Syllabify** according to standard Akkadian rules
3. **prosody realization** accentuation patterns using a phrase-level algorithm
4. **Compute** acoustic metrics (%V, Î”C, VarcoC)
5. **Generate** outputs for publication and speech synthesis

For release planning/versioning, see `docs/akkapros/release-strategy.md`.
For metrics methodology and formulas, see `docs/akkapros/metrics-computation.md`.

Documentation
- Full developer and CLI documentation is under `docs/akkapros/` and packaged CLI docs are copied into the installed package. A brief Getting Started guide is at `docs/GETTING_STARTED.md`.

---

## ðŸ”§ Tools Included

| Program | Version | Description |
|---------|---------|-------------|
| `atfparser.py` | 1.0.0 | Converts eBL ATF files to clean phonological text |
| `syllabify.py` | 1.0.0 | Syllabifies Akkadian text following Huehnergard (2011) |
| `prosmaker.py` | 1.0.0 | Applies accentuation prosody realization algorithm |
| `metricalc.py` | 1.0.0 | Computes acoustic metrics from prosody-realized text |
| `fullprosmaker.py` | 1.0.0 | Runs syllabify + prosody realization + metrics + print in one command |
| `printer.py` | 1.0.0 | Converts `*_tilde.txt` to accent text, bold markdown, IPA, and XAR outputs |

---

## ðŸš€ Quick Start â€” use the demo scripts

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

The demo scripts run the full pipeline (parse â†’ syllabify â†’ prosody realization â†’ metrics
â†’ outputs). Use `demo/akkapros/prosmaker/results/` to inspect generated `_syl`, `_tilde`,
metrics and accent outputs.

To prepare phone-level datasets (MBROLA, manifests) use the `akkapros` phoneprep demo:

```powershell
.\demo\akkapros\prosmaker\corpus-demo.ps1   # runs akkapros pipeline
.\demo\akkapros\phoneprep\phoneprep-demo.ps1 # runs akkapros phoneprep and dataset prep
```

Source files for demos are under `data/samples/` and demo outputs are in
`demo/akkapros/prosmaker/results/` and `demo/akkapros/phoneprep/results/`.

---

## ðŸ–¨ï¸ Accent Printer CLI (`printer.py`)

`printer.py` reads `*_tilde.txt` and produces reading outputs:

- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`
- `<prefix>_xar.txt`

### Marker behavior

- `+` (`WORD_LINKER`) â†’ `â€¿`
- `Â·` (`SYL_SEPARATOR`) removed in final output
- `-` (`HYPHEN`) preserved
- `~` marks the preceding syllable:
	- in `accent_acute`: replaced by `Â´`
	- in `accent_bold`: removed and the host syllable is bolded
	- in `accent_ipa`: converted to IPA length (`Ë`) and stress (`Ëˆ`) markers
	- in `accent_xar`: replaced by `Â´` on the prosody-realized segment in XAR orthography
- in `xar` (plain), prosody-realized `Â´` marks are removed; this file keeps the same XAR transliteration otherwise
- in XAR outputs, glottal letters `Ê¿` and `Ê¾` are currently represented as apostrophe (`'`) and are not stripped by cleanup
- in IPA mode, spaces and `+` are connected speech boundaries and are rendered as syllable separators (`.`)
- in IPA mode, punctuation emits symbolic tags and prosody markers:
	- weak/inner punctuation -> `|`
	- strong/final punctuation -> `â€–`
- in IPA mode, bracket chunks are emitted as `âŸ¨escape:[...]âŸ©`
- content inside square brackets `[ ... ]` remains untouched in non-IPA outputs (for markdown URI safety)

### IPA modes (`--ipa-ob` vs `--ipa-strict`)

- `--ipa-ob`: Old Babylonian profile. Letter glottals (`Ê¾`, `Ê¿`) are removed in IPA output.
- `--ipa-strict`: keeps full IPA symbols (including letter glottals).
- `--ipa` is an alias of `--ipa-strict`.
- Implied glottal stops inserted by the prosody realization/stress process are treated separately from letter glottals; prosody-realized onset glottals are preserved.

Historical rationale: these weak consonants were already largely lost in Old Babylonian connected speech, while they are older in Old Akkadian. Their later written presence can be conservative scribal traditionalism rather than direct phonetic realization.

### XAR orthography profile

- XAR output is available both in `printer.py --xar` and in the full pipeline `fullprosmaker.py --print-xar`.
- Selecting XAR writes two files: `<prefix>_accent_xar.txt` and `<prefix>_xar.txt`.
- Consonant remap includes distinct emphatic/base channels (e.g., `q -> ê—`, `á¹­ -> êž“`, `á¹£ -> É‰`, `Å¡ -> xÌŒ`).
- Vowel strategy uses doubled notation for long vowels while preserving macron/circumflex classes:
	- default: `Ä -> aa`, `Ä« -> ii`, `Å« -> uu`, `Ä“ -> ee`, `Ã¢ -> eÃ¢`, `Ã® -> eÃ®`, `Ã» -> iÃ»`, `Ãª -> aÃª`
	- emphatic: `Ä -> Ã a`, `Ä« -> Ã¬i`, `Å« -> Ã¹u`, `Ä“ -> Ã¨e`, `Ã¢ -> Ã¨Ã¢`, `Ã® -> Ã¨Ã®`, `Ã» -> Ã¬Ã»`, `Ãª -> Ã Ãª`
- Design rationale: macron vowels are written as pure doubled vowels (`aa/ii/uu/ee`), while circumflex vowels are encoded as mixed pairs where the second slot carries the circumflex (`eÃ¢/eÃ®/iÃ»/aÃª`). This gives a visual cue that the second vowel is dominant while preserving a clear keyboard-friendly contrast between macron and circumflex series.
- Processing order for XAR is: consonant substitution -> vowel substitution -> accent-mark handling.
- Current policy keeps apostrophe realizations for `Ê¿` and `Ê¾` in both XAR outputs.

### Emphatic vowel coloring

In this system, the four plain vowel phonemes `/a, i, u, e/` undergo systematic allophonic variation only in **post-emphatic position** (after emphatic consonants, including `/q/`). Vowels before emphatics remain plain. The emphatic allophones are: `/a/ â†’ [É‘]`, `/i/ â†’ [É¨]`, `/u/ â†’ [ÊŠ]`, and `/e/ â†’ [É›]`.

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
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --ipa --ipa-pharyngeal preserve

# write IPA with Old Babylonian pharyngeal merger
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --ipa --ipa-pharyngeal remove

# write XAR outputs (accented and plain)
python3 src/akkapros/cli/printer.py outputs/erra_tilde.txt -p erra --outdir outputs --xar

# run self-tests
python3 src/akkapros/cli/printer.py --test
```

`--test` runs both:
- printer CLI option-resolution checks (including `--ipa-pharyngeal preserve|remove`)
- `akkapros.lib.print.run_tests()` conversion checks

---

## âš¡ Full Pipeline CLI (`fullprosmaker.py`)

Use `fullprosmaker.py` when you want to run the full pipeline (`syllabifier` â†’ `prosmaker` â†’ `metricalc` â†’ `printer`) in one command.

### Input and outputs

- **Input**: Akkadian processed text (typically `*_proc.txt`)
- **Always written**:
	- `<prefix>_syl.txt`
	- `<prefix>_tilde.txt`
- **Metrics outputs**: selected by flags (`--metrics-table`, `--metrics-json`, `--metrics-csv`)
	- If no metrics format is selected, `--metrics-table` is used by default.
- **Accent outputs**: selected by flags (`--print-acute`, `--print-bold`, `--print-ipa`, `--print-xar`)
	- If no accent format is selected, `--print-acute` and `--print-bold` are used by default.

### Shared options (deduplicated)

- `-p, --prefix`: shared prefix for all outputs
- `--outdir`: shared output directory
- `--extra-vowels`, `--extra-consonants`: applied to syllabify and metrics

### Stage-specific options

- **Syllabification**: `--syl-merge-hyphens`, `--syl-merge-lines`
- **prosody realization**: `--prosody-style {lob,sob}` (default: `sob`), `--prosody-relax-last`
	- Diphthong restoration is always applied after prosody realization; split markers never appear in `_tilde.txt` output.
- **Metrics**: `--metrics-wpm`, `--metrics-pause-ratio`, `--metrics-weak-punct-weight`, `--metrics-strong-punct-weight`, `--metrics-table`, `--metrics-json`, `--metrics-csv`
- **Printer**: `--print-acute`, `--print-bold`, `--print-ipa`, `--print-ipa-pharyngeal {preserve,remove}`, `--print-xar`
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

- Project tests for the printer/IPA mode logic are implemented in built-in `run_tests()` functions.
- No pytest module is required for validating `--ipa-ob` / `--ipa-strict` behavior.

---

## ðŸ§  Moraic prosody realization algorithm (Current Behavior)

### 1) Syllable classification

Each syllable is classified by structure and mora count:

| Type | Structure | Morae | Example |
|---|---|---:|---|
| `CV` | consonant + short vowel | 1 | `Å¡a` |
| `V` | short vowel (initial) | 1 | `a` |
| `CVC` | closed short | 2 | `Å¡ar` |
| `VC` | closed short (initial) | 2 | `ap` |
| `CVV` | open long | 2 | `bÄ` |
| `VV` | open long (initial) | 2 | `Ä«` |
| `CVVC` | closed long | 3 | `nÄÅ¡` |
| `VVC` | closed long (initial) | 3 | `Än` |

### 2) prosody realization operations

When a target syllable is selected, exactly one mora is added:

| Operation | Applies to | Effect | Example |
|---|---|---|---|
| Vowel lengthening | `CVV`, `VV`, `CVVC`, `VVC` | long vowel becomes extra-long | `rÄ â†’ rÄ~` |
| Coda gemination | `CVC`, `VC` (non-final in unit) | coda consonant geminated | `dad â†’ dad~` |
| Onset gemination (last resort) | `CV`, `V` | onset geminated; for vowel-initial, glottal gemination | `ka â†’ k~a`, `a â†’ ~a` |

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

- `u + ana + Å¡arri â†’ u+ana+Å¡arÂ·ri`

## ðŸ”§ Prosmaker CLI (`prosmaker.py`)

`prosmaker.py` applies moraic prosody realization to `*_syl.txt` and writes `<prefix>_tilde.txt`.

### Explicit `+` linker behavior

`+` in `*_syl.txt` is treated as an explicit user-defined prosodic link:

- Linked sequences are parsed as a mandatory merged unit.
- **Default behavior**: strict tail-only prosody realization (only the last linked word is prosody realization-eligible).
- **Relaxed behavior** (`-r/--relax-last`): prosody realization may propagate leftward to previous linked words when needed.

Examples:

- Default: `bÄÂ·nÃ»+aÂ·pilÂ¦ â†’ bÄÂ·nÃ»+~aÂ·pil`
- Relaxed (`--relax-last`): `bÄÂ·nÃ»+aÂ·pilÂ¦ â†’ bÄÂ·nÃ»~+aÂ·pil`

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
- `Â·` and `-` preserved as syllable/prosodic boundaries
- spaces for non-merged word boundaries




