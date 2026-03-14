# Full Prosmaker CLI (`fullprosmaker.py`)

This document explains what `fullprosmaker.py` does, how to run it, and what files it produces.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/fullprosmaker.py`
- Uses these libraries internally:
  - `src/akkapros/lib/syllabify.py`
  - `src/akkapros/lib/prosody.py`
  - `src/akkapros/lib/metrics.py`
  - `src/akkapros/lib/print.py`

---

## 📋 Purpose

`fullprosmaker.py` runs the complete Akkadian processing pipeline in one command.

### Pipeline Stages

| Stage | Input → Output | Description |
|-------|----------------|-------------|
| **1. Syllabify** | `*_proc.txt` → `*_syl.txt` | Adds syllable boundaries |
| **2. Prosody realization** | `*_syl.txt` → `*_tilde.txt` | Applies accentuation algorithm |
| **3. Metrics** | `*_tilde.txt` → table/json/csv | Computes rhythmic and structural metrics |
| **4. Print** | `*_tilde.txt` → accent outputs | Generates user-facing formats |

The command centralizes shared options (`--prefix`, `--outdir`, extra phonetic symbols) and writes all selected outputs in one run.

---

## 📂 Input and Core Outputs

### Input
- One processed text file, typically `<prefix>_proc.txt` from `atfparser.py`

### Core Outputs (always written)

| File | Description |
|------|-------------|
| `<prefix>_syl.txt` | Syllabified text |
| `<prefix>_tilde.txt` | Prosody-realized pivot format |

### Optional Metrics Outputs

| Flag | File | Description |
|------|------|-------------|
| `--metrics-table` | `<prefix>_metrics.txt` | Human-readable table |
| `--metrics-json` | `<prefix>.json` | JSON format |
| `--metrics-csv` | `<prefix>.csv` | CSV format |

### Optional Print Outputs

| Flag | File | Description |
|------|------|-------------|
| `--print-acute` | `<prefix>_accent_acute.txt` | Acute-marked text |
| `--print-bold` | `<prefix>_accent_bold.md` | Bold-marked Markdown |
| `--print-ipa` | `<prefix>_accent_ipa.txt` | IPA transcription |
| `--print-xar` | `<prefix>_accent_xar.txt`<br>`<prefix>_xar.txt` | XAR transliteration (accented and plain) |

---

## 🚀 Command Syntax

    python src/akkapros/cli/fullprosmaker.py <input_proc.txt> [options]

---

## ⚙️ Option Groups

### Shared I/O

| Option | Description |
|--------|-------------|
| `--version` | Print CLI version |
| `-p, --prefix <name>` | Output prefix for all generated files |
| `--outdir <dir>` | Output directory (default: current directory) |

### Syllabifier Options

| Option | Description |
|--------|-------------|
| `--extra-vowels <chars>` | Additional vowel characters to recognize |
| `--extra-consonants <chars>` | Additional consonant characters to recognize |
| `--syl-merge-hyphens` | Merge hyphens into syllable separators |
| `--syl-merge-lines` | Normalize line breaks (default preserves original lines) |

### Prosmaker Options

| Option | Description |
|--------|-------------|
| `--prosody-style {lob,sob}` | Accent style (default: `lob`) |
| `--prosody-relax-last` | Allow prosody realization propagation before last linked word |

**Note:** Diphthong restoration is always applied automatically in the prosody realization stage. Temporary split markers are removed from the final `_tilde.txt` output.

### Metricalc Options

| Option | Description |
|--------|-------------|
| `--metrics-table` | Generate human-readable table output |
| `--metrics-json` | Generate JSON output |
| `--metrics-csv` | Generate CSV output |
| `--metrics-wpm <float>` | Words per minute for speech-rate estimation (default: `165`) |
| `--metrics-pause-ratio <float>` | Pause ratio in percent of total time (default: `35`) |
| `--metrics-long-punct-weight <float>` | Relative weight of long punctuation pauses (default: `2.0`) |

**Default behavior:** If no metrics format flag is provided, table output is enabled automatically.

### Printer Options

| Option | Description |
|--------|-------------|
| `--print-acute` | Generate acute-marked text |
| `--print-bold` | Generate bold-marked Markdown |
| `--print-ipa` | Generate IPA transcription |
| `--print-ipa-proto-semitic {preserve,replace}` | Pharyngeal/glottal mapping policy |
| `--print-circ-hiatus` | Speculative mode: split circumflex vowels into hiatus (e.g., `qû → qʊ.ʊ`) |
| `--print-xar` | Generate XAR transliteration (both accented and plain) |

**Default behavior:** If no print output flag is selected, `--print-acute` and `--print-bold` are enabled automatically.

---

## 🧪 Test Modes

`fullprosmaker.py` can run stage-specific tests without processing an input file.

| Option | Tests |
|--------|-------|
| `--test-syllabify` | Syllabifier tests |
| `--test-prosody` | Prosody realization tests |
| `--test-diphthongs` | Diphthong restoration tests |
| `--test-metrics` | Metrics computation tests |
| `--test-print` | Printer output tests |
| `--test-cli` | CLI option-resolution tests |
| `--test-all` | All of the above |

---

## 💡 Typical Usage Examples

### Minimal Full Run (Default Outputs)

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs

This generates:
- `erra_syl.txt`
- `erra_tilde.txt`
- `erra_metrics.txt` (default table)
- `erra_accent_acute.txt` (default acute)
- `erra_accent_bold.md` (default bold)

### Run with Explicit Style and Metrics Table

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs \
      --prosody-style lob \
      --metrics-table

### Run with Machine-Readable Metrics (JSON + CSV)

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs \
      --metrics-json --metrics-csv

### Run with IPA and Speculative Circumflex Hiatus

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs \
      --print-ipa \
      --print-ipa-proto-semitic replace \
      --print-circ-hiatus

### Run with XAR Output (Skip Acute/Bold/IPA)

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs \
      --print-xar

### Run Full Test Suite

    python src/akkapros/cli/fullprosmaker.py --test-all

---

## 🔄 Stage Order and Internal Behavior

Execution order is **fixed** and cannot be changed:

1. **Syllabification** always runs first and saves `*_syl.txt`
2. **Prosody realization** always runs second and saves `*_tilde.txt`
3. **Metrics** computed from prosody-realized output (if requested)
4. **Print outputs** generated from prosody-realized output (if requested)

The command exits with non-zero status if any stage fails, making it suitable for scripting and batch processing.

---

## 🔗 Related Commands

For isolated stage debugging, use the single-stage CLIs:

| Stage | Command |
|-------|---------|
| ATF extraction | `atfparser.py` |
| Syllabification | `syllabifier.py` |
| Prosody realization | `prosmaker.py` |
| Metrics | `metricalc.py` |
| Formatting | `printer.py` |

For **production runs**, use `fullprosmaker.py` to ensure all stages run with consistent options and outputs.

---

## ✅ Summary

`fullprosmaker.py` is the primary entry point for end-to-end Akkadian prosodic analysis. It coordinates all pipeline stages, manages shared options, and produces a complete set of outputs—from syllabified text through metrics and publication-ready formatting—in a single, reproducible command.