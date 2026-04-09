# Full Prosmaker CLI (`fullprosmaker.py`)

This document explains what `fullprosmaker.py` does, how to run it, and what files it produces.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/fullprosmaker.py`
- Uses these libraries internally:
  - `src/akkapros/lib/syllabify.py`
  - `src/akkapros/lib/prosody.py`
  - `src/akkapros/lib/phonetize.py`
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
| **3. Phonetize** | `*_tilde.txt` → `*_phone.txt` | Builds the canonical flat-line phone-row artifact |
| **4. Metrics** | `*_tilde.txt` → table/json | Computes rhythmic and structural metrics |
| **5. Print** | `*_tilde.txt` → accent outputs | Generates user-facing formats |

The command centralizes shared options (`--prefix`, `--outdir`, extra phonetic symbols) and writes all selected outputs in one run.

---

## 📂 Input and Core Outputs

### Input
- One processed text file, typically `<prefix>_proc.txt` from `atfparser.py`.

### Core Outputs (always written)

| File | Description |
|------|-------------|
| `<prefix>_syl.txt` | Syllabified text |
| `<prefix>_tilde.txt` | Prosody-realized pivot format |
| `<prefix>_phone.txt` | Canonical flat-line phone-row artifact with CR-036 fields |

The written `_tilde` pivot preserves three kinds of downstream-critical structure: armored punctuation / escaped chunks as `⟦...⟧`, diphthong memory as `¨`, and merge provenance as `+` for explicit inherited links versus `&` for internal prosody merges.

### Optional Metrics Outputs

| Flag | File | Description |
|------|------|-------------|
| `--metrics-table` | `<prefix>_metrics.txt` | Human-readable table |
| `--metrics-json` | `<prefix>.json` | JSON format |

The metrics outputs include the same `Prominence statistics` contract as
`metricalc.py`: the table exposes those counters in the `ORIGINAL TEXT`
section only, and JSON exposes them only under
`original.prominence_statistics`.

Like standalone `metricalc.py`, full-pipeline metrics outputs do not republish
`metadata.data` in their output front matter.

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
| `--extra-vowels <chars>` | Additional vowel characters to recognize in the syllabify stage; downstream metrics inherits them from front matter |
| `--extra-consonants <chars>` | Additional consonant characters to recognize in the syllabify stage; downstream metrics inherits them from front matter |
| `--extra-short-punct-chars <chars>` | Additional short-pause punctuation characters for the syllabify stage; downstream metrics inherits them from front matter |
| `--extra-long-punct-chars <chars>` | Additional long-pause punctuation characters for the syllabify stage; downstream metrics inherits them from front matter |
| `--extra-short-punct-pattern <regex>` | Repeatable regex for short-pause punctuation segments in the syllabify stage; downstream metrics inherits them from front matter |
| `--extra-long-punct-pattern <regex>` | Repeatable regex for long-pause punctuation segments in the syllabify stage; downstream metrics inherits them from front matter |
| `--number-format <regex>` | Number regex passed to syllabifier stage (empty uses built-in English-grouping-compatible pattern) |
| `--syl-merge-hyphens` | Merge hyphens into syllable separators |
| `--syl-merge-lines` | Normalize line breaks (default preserves original lines) |
| `--title <string>` | Override inherited or missing `file.title` for the syllabifier output |

### Prosmaker Options

| Option | Description |
|--------|-------------|
| `--prosody-style {lob,sob}` | Accent style (default: `lob`) |
| `--mora-mode {bi,mono}` | Accentuation trigger mode passed to the prosody stage (default: `bi`) |
| `--prosody-relax-last` | Allow prosody realization propagation before last linked word |

**Note:** Diphthong restoration is always applied automatically in the prosody realization stage. The final `_tilde.txt` pivot keeps the diphthong memory marker `¨`, while printer outputs remove it only at display time.

`--mora-mode mono` is the academic comparison mode: it removes the bimoraic
odd-parity prerequisite for accentuation attempts while keeping the same
accent-site hierarchy and explicit-link locking. In this mode, unresolved
units do not forward-merge; they fall directly to last resort.

### Phonetizer Options

| Option | Description |
|--------|-------------|
| `--phonetize-geminate-policy {corrective,cumulative}` | Pass through `phonetize.process.geminate_policy` |
| `--phonetize-accentuation-distribution-policy {100_0,85_15,70_30}` | Pass through `phonetize.process.accentuation_distribution_policy` |
| `--phonetize-short-pause-policy {strict,best_effort}` | Pass through `phonetize.process.short_pause_policy` |
| `--phonetize-drift-policy {strict,extensible}` | Pass through `phonetize.process.drift_policy` |
| `--phonetize-drift-tolerance <int>` | Pass through `phonetize.process.drift_tolerance` |
| `-t, --option phonetize.timing_model...=...` | Override values under `phonetize.timing_model` |

### Metricalc Options

| Option | Description |
|--------|-------------|
| `--metrics-table` | Generate human-readable table output |
| `--metrics-json` | Generate JSON output |
| `--explicit-link-count <int>` | Override inherited `metadata.data.prosody.explicit_word_link_count` for metrics |

**Default behavior:** If no metrics format flag is provided, table output is enabled automatically.

Long-pause punctuation weight is fixed internally at `2.0` and is no longer a
metrics-stage CLI option. The current transition also removes metrics-owned
timing flags; `fullprosmaker` uses the phonetize transition defaults internally
for metrics (`wpm = 193`, `pause_ratio = 35`).

The longer-term transition target is a structured phonetize handoff where `_phone.txt` carries the canonical row stream and `_tilde.txt` remains the live prosody-bearing pivot until metricalc fully adopts that handoff.

### Printer Options

| Option | Description |
|--------|-------------|
| `--print-acute` | Generate acute-marked text |
| `--print-bold` | Generate bold-marked Markdown |
| `--print-ipa` | Generate IPA transcription |
| `--print-ipa-proto-semitic {preserve,replace}` | Pharyngeal/glottal mapping policy |
| `--print-circ-hiatus` | Speculative mode: split circumflex vowels into hiatus (e.g., `qû → qʊ.ʊ`) |
| `--print-xar` | Generate XAR transliteration (both accented and plain) |
| `--print-merger` | Preserve the visible merge connector `‿` in acute, bold, and accented XAR outputs |

**Default behavior:** If no print output flag is selected, `--print-acute` and `--print-bold` are enabled automatically.

Without `--print-merger`, acute, bold, and accented XAR outputs render merged words with ordinary spaces. IPA is unchanged, and plain `_xar.txt` remains space-separated.

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
- `erra_phone.txt`
- `erra_metrics.txt` (default table)
- `erra_accent_acute.txt` (default acute)
- `erra_accent_bold.md` (default bold)

### Run with Explicit Style and Metrics Table

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs \
      --prosody-style lob \
      --phonetize-geminate-policy corrective \
      --metrics-table

### Run with Mono Mora Mode

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra-mono \
      --outdir outputs \
      --mora-mode mono \
      --metrics-table

### Run with Machine-Readable Metrics (JSON)

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs \
  --metrics-json

### Start from Content-Only Prepared Text

    python src/akkapros/cli/fullprosmaker.py prepared_text.txt \
      --title "Prepared Corpus" \
      --explicit-link-count 0 \
      -p prepared \
      --outdir outputs

### Full Pipeline with Punctuation Extensions

    python src/akkapros/cli/fullprosmaker.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs \
      --extra-short-punct-chars "·" \
      --extra-long-punct-chars "※" \
      --extra-short-punct-pattern "^\\s*[·]+\\s*$" \
      --extra-long-punct-pattern "^\\s*[※]+\\s*$"

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

Punctuation regex options are pre-validated before any stage starts. Invalid regex aborts immediately.

By default, the initial input is validated at startup and reports precise source + line details for obvious corruption or wrong stage input (`*_proc.txt` expected).

### Validation Rules (Middle Strictness)

`fullprosmaker.py` validates only the entry input (`*_proc.txt`) at startup with moderate strictness: enough to detect wrong-stage/corrupted files that would break the pipeline, but not so strict that normal textual variation becomes unusable. It does not auto-correct wrong input types (for example raw `.atf`); it fails fast with a precise error instead.
The validator is gatekeeper-only: it never rewrites input files and never performs hidden precleaning; it only allows processing to continue or fails with a precise error.

This command inherits the same reduced metadata contract as the individual
stages: `--title` feeds the syllabifier title override, and
`--explicit-link-count` feeds the metrics override.

Front matter for prosody and downstream outputs preserves
`metadata.options.mora_mode` so artifact consumers can distinguish `bi` from
`mono` runs.

Escaped chunks are preserved through the full pipeline using CR-005 syntax:

- `{{text}}`
- `{tag{text}}` where `tag` matches `[0-9a-z_]{1,16}`

Internal tags begin with `_` and are reserved for pipeline-internal handling conventions.

Regex semantics for punctuation patterns are standard Python regex: `^` anchors start, `$` anchors end, and a literal dollar requires `\\$`. The diphthong separator `¨` is treated as a plain character.

Boundary pseudo-tokens are also available in punctuation patterns: `[:bol:]` (beginning of line), `[:eol:]` (end of line). EOF is normalized internally to end-of-line semantics.

When lines are preserved (default, without `--syl-merge-lines`), newline boundaries are preserved in syllabifier output for punctuation, preserve blocks, and number/currency suites.

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