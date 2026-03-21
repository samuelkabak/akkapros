# Syllabifier CLI (`syllabifier.py`)

This document explains what `syllabifier.py` does, how to run it, and what files it produces.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/syllabifier.py`
- Core syllabification library: `src/akkapros/lib/syllabify.py`

---

## 📋 Purpose

`syllabifier.py` converts cleaned Akkadian text into syllabified form used by the prosody realization stage.

It inserts syllable boundaries and marks word endings in the toolkit internal format.

---

## 📂 Input and Output

### Input
- Typically `<prefix>_proc.txt` from `atfparser.py`

### Output
- `<prefix>_syl.txt` in `--outdir`

By default, if no `--prefix` is provided, the output prefix is derived from the input filename stem.

---

## 🚀 Command Syntax

    python src/akkapros/cli/syllabifier.py <input_proc.txt> [options]

---

## ⚙️ Options

| Option | Description |
|--------|-------------|
| `--version` | Print CLI version |
| `-p, --prefix <name>` | Output prefix |
| `--outdir <dir>` | Output directory (default: current directory) |
| `--extra-vowels <chars>` | Additional vowel characters to recognize |
| `--extra-consonants <chars>` | Additional consonant characters to recognize |
| `--merge-hyphen` | Merge hyphens into syllable separators |
| `--merge-lines` | Normalize line breaks (`1 newline → space`, `2+ newlines → paragraph break`) |
| `--test` | Run internal syllabifier tests |

### Line Break Behavior

| Mode | Default | `--merge-lines` |
|------|---------|-----------------|
| Single newline | Preserved as line break | Converted to space |
| Multiple newlines | Preserved as paragraph breaks | Converted to single newline |

Default behavior preserves original line structure, which may encode verse boundaries.

---

## 🔤 Output Format Markers

The `*_syl.txt` file uses these markers:

| Marker | Meaning |
|--------|---------|
| `·` | Syllable separator |
| `¦` | Word-ending marker |
| `-` | Hyphen boundary (unless merged with `--merge-hyphen`) |
| `+` | Linker boundary (prosodic attachment) |
| `⟦...⟧` | Escaped punctuation or non-word segments |

Escaped non-Akkadian chunks use CR-005 syntax inside `⟦...⟧`:

- `{{text}}` (plain escaped chunk)
- `{tag{text}}` (tagged escape, `tag` matches `[0-9a-z_]{1,16}`)
- Internal tags start with `_` (for pipeline-internal commands), e.g. `{_mdf{---}}`

---

## 💡 Typical Usage Examples

### Basic Syllabification

    python src/akkapros/cli/syllabifier.py outputs/erra_proc.txt \
      -p erra \
      --outdir outputs

### Merge Hyphens and Normalize Line Breaks

    python src/akkapros/cli/syllabifier.py outputs/erra_proc.txt \
      --merge-hyphen \
      --merge-lines \
      -p erra \
      --outdir outputs

### Provide Additional Phonetic Symbols

    python src/akkapros/cli/syllabifier.py outputs/text_proc.txt \
      --extra-vowels "ø" \
      --extra-consonants "ɣ" \
      -p text \
      --outdir outputs

### Run Tests

    python src/akkapros/cli/syllabifier.py --test

---

## 📝 Important Processing Notes

- **Diphthong handling**: The library may insert glottal stops between adjacent vowels for diphthong expansion (e.g., `ua` → `u·ʾa`). These are later restored by `prosmaker.py`.
- **Hyphen and linker behavior** is context-sensitive and follows Akkadian morphological boundaries.
- **Punctuation** is preserved as escaped material (`⟦...⟧`) and is not syllabified as Akkadian words.
- **Escapes in source text**: `{{text}}` and `{tag{text}}` are preserved verbatim, wrapped as `⟦...⟧`, and excluded from Akkadian syllabification.
- **Nested escapes** are intentionally unsupported; only `{{...}}` and one-level `{tag{...}}` are recognized.
- **Word endings** are explicitly marked with `¦` for downstream processing.
- By default, input format is validated at startup and reports precise source + line for obvious corruption or wrong stage input (for example raw ATF lines in a `*_proc.txt` input).

### Validation Rules (Middle Strictness)

Validation here is pragmatic: `syllabifier.py` verifies that input looks like cleaned `*_proc.txt` text and rejects obvious wrong-stage files (for example raw `%n`/`#tr.en:` ATF content), empty/binary files, and clearly corrupted structure. It does not enforce a strict grammar for every possible line. The purpose is to catch inputs that would likely cause hard downstream exceptions, not to block valid textual variation.
The validator is gatekeeper-only: it never rewrites or auto-corrects input; it only allows processing to continue or fails with a precise error.

---

## 🔗 Pipeline Position

The syllabifier is the **second step** in the akkapros pipeline:

1. `atfparser.py` → `*_proc.txt`
2. **`syllabifier.py`** → `*_syl.txt`
3. `prosmaker.py` → `*_tilde.txt`
4. `metricalc.py` and `printer.py` → metrics and formatted outputs

For a one-command run of all stages, use **`fullprosmaker.py`**.

---

## ✅ Summary

`syllabifier.py` transforms plain Akkadian text into the syllabified format required for prosodic analysis. It handles syllable boundaries, word endings, and special markers while preserving structural information for downstream stages.