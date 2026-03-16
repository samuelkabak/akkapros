# Metricalc CLI (`metricalc.py`)

This document explains what `metricalc.py` does, how to run it, and how to interpret its generated files.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/metricalc.py`
- Core logic: `src/akkapros/lib/metrics.py`
- Metric definitions: `docs/akkapros/metrics-computation.md`

---

## 📋 Purpose

`metricalc.py` computes rhythmic and structural metrics from prosody-realized text (`*_tilde.txt`).

It can output:
- Human-readable text table
- JSON
- CSV

It supports single-file and batch (`--input-list`) processing.

---

## 📂 Input and Output

### Input
- One `*_tilde.txt` file, or
- A list file containing one input path per line (`--input-list`)

### Output Formats

| Format | Output File |
|--------|-------------|
| Table | `<base>_metrics.txt` |
| JSON | `<base>_metrics.json` |
| CSV | `<base>_metrics.csv` |

### Base Naming Rules

- If `--prefix` is given: `<outdir>/<prefix>`
- If single input and no prefix: `<outdir>/<input_stem>`
- If multiple inputs and no prefix: `<outdir>/metrics`

---

## 🚀 Command Syntax

Single file:

    python src/akkapros/cli/metricalc.py <input_tilde.txt> [options]

Batch mode:

    python src/akkapros/cli/metricalc.py --input-list <list.txt> [options]

---

## ⚙️ Options

| Option | Description |
|--------|-------------|
| `--version` | Print CLI version |
| `--input-list <file>` | File with one input path per line |
| `-p, --prefix <name>` | Output prefix |
| `--outdir <dir>` | Output directory (default: current directory) |
| `--table` | Write human-readable table output |
| `--json` | Write JSON output |
| `--csv` | Write CSV output |
| `--wpm <float>` | Words per minute used in speech-rate estimation (default: `165`) |
| `--pause-ratio <float>` | Pause ratio in percent of total time (default: `35`) |
| `--long-punct-weight <float>` | Relative weight of long punctuation pauses vs short pauses (default: `2.0`) |
| `--extra-consonants <chars>` | Additional consonant symbols to include in parsing |
| `--extra-vowels <chars>` | Additional vowel symbols to include in parsing |
| `--test` | Run metrics test suite |

### Default Format Behavior

If none of `--table`, `--json`, or `--csv` is specified, `--table` is enabled automatically.

---

## 💡 Typical Usage Examples

### Single File, Default Table Output

    python src/akkapros/cli/metricalc.py outputs/erra_tilde.txt

### Write Table + JSON + CSV

    python src/akkapros/cli/metricalc.py outputs/erra_tilde.txt \
      --table --json --csv \
      -p erra \
      --outdir outputs

### Custom Timing Parameters

    python src/akkapros/cli/metricalc.py outputs/erra_tilde.txt \
      --wpm 170 \
      --pause-ratio 35 \
      --long-punct-weight 2.5 \
      --table

### Batch Mode

    python src/akkapros/cli/metricalc.py \
      --input-list outputs/tilde_files.txt \
      --csv --json \
      --outdir outputs/compare

### Run Tests

    python src/akkapros/cli/metricalc.py --test

---

## 📊 What It Computes (Summary)

### Main Metric Families

| Family | Description |
|--------|-------------|
| **Syllable types** | Distributions and counts of CV, CVC, CVV, etc. |
| **Mora statistics** | Per syllable and per word |
| **Merge statistics** | Words merged, units formed, average unit size |
| **Prosody realization** | Repair rate, repairs by type |
| **Acoustic/rhythmic metrics** | `%V`, `DeltaC`, `MeanC`, `VarcoC` |
| **Speech and pause allocation** | Durations, ratios, corrections |

### Output Structure Highlights

- **Mora statistics (original and repaired)** now include:
    - `Total morae number`
- **Speech rate** is reported for both sections:
    - `Speech rate (original)`
    - `Speech rate (repaired)`
- In table output, each speech-rate block appears before its corresponding acoustic block.
- **ΔC** and **MeanC** are shown in both:
    - mora units
    - seconds (`value_in_mora * mora_duration`)

### Pause Output Details

The metrics include detailed pause information:

- `short_pauseable_boundaries` and `long_pauseable_boundaries`
- Initial pause durations and weights (before correction)
- **Corrected pause durations**: short pauses constrained to even-mora values
- Corrected long/short weight derived after conservation adjustment

For formal definitions and equations, see:
- `docs/akkapros/metrics-computation.md`

---

## 📝 Important Notes

### %V Note

Current outputs expose **both** values:
- `%V (articulate)` — continuous speech, no pauses
- `%V (normal speech, incl. pauses)` — adjusted for pause ratio

This makes text-derived moraic `%V` directly comparable with pause-inclusive speech measurements from living languages.

### Pause Duration Correction

`metricalc.py` now reports two pause-duration layers:

1. **Initial**: direct weighted allocation from `--long-punct-weight`
2. **Corrected**: short-pause duration snapped to the nearest multiple of `2 * mora_dur`, with long-pause duration adjusted to preserve total punctuation pause time

This correction affects table, JSON, and CSV outputs. It ensures that short pauses align with the bimoraic rhythm of the text.

### New Fields Across Formats

For both original and repaired outputs:

- `mora_stats.total` (JSON) / `original_total_morae`, `rep_total_morae` (CSV)
- speech metrics for original and repaired sections
- `DeltaC` and `MeanC` in mora and seconds in the table

---

## 🔗 Pipeline Position

`metricalc.py` is typically run after `prosmaker.py`:

1. `atfparser.py` → `*_proc.txt`
2. `syllabifier.py` → `*_syl.txt`
3. `prosmaker.py` → `*_tilde.txt`
4. **`metricalc.py`** → metrics output

For all-in-one execution, see **`fullprosmaker.py`**.

---

## ✅ Summary

`metricalc.py` transforms prosody-realized text into quantitative metrics that validate the algorithm and enable cross-linguistic comparison. It supports multiple output formats, batch processing, and configurable speech parameters, making it suitable for both single-file analysis and large-scale corpus studies.