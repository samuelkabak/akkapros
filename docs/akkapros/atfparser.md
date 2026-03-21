# ATF Parser CLI (`atfparser.py`)

This document explains what `atfparser.py` does, how to run it, and what files it produces.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/atfparser.py`
- Core parser library: `src/akkapros/lib/atfparse.py`

---

## 📋 Purpose

`atfparser.py` converts eBL ATF files into clean Akkadian text for the prosody pipeline.

It is designed for **phonetic and prosodic processing**, not for preserving full scholarly ATF structure. Think of it as a filter that extracts the linguistic content and discards most markup.

### Main Behavior
- Extract Akkadian text from `%n` lines
- Extract English translation from `#tr.en:` lines
- Ignore unrelated metadata lines
- Normalize editorial markup to readable, pipeline-ready text

---

## 📂 Input and Output

### Input
- An eBL ATF file containing `%n` lines (Akkadian text lines)

### Outputs (in `--outdir`)

| File | Description |
|------|-------------|
| `<prefix>_orig.txt` | Original Akkadian `%n` text with markup preserved |
| `<prefix>_proc.txt` | Cleaned Akkadian text ready for syllabification and prosody realization |
| `<prefix>_trans.txt` | English translations (when present in the ATF file) |

---

## 🚀 Command Syntax

    python src/akkapros/cli/atfparser.py <input.atf> [options]

---

## ⚙️ Options

| Option | Description |
|--------|-------------|
| `--version` | Print CLI version |
| `-p, --prefix <name>` | Output prefix (default: input filename stem) |
| `--outdir <dir>` | Output directory (default: current directory) |
| `--remove-hyphens` | Remove hyphens from cleaned output |
| `--preserve-case` | Keep original case (default behavior lowercases text) |
| `--preserve-h` | Keep `h/H` unchanged (default maps `h` → `ḫ`, `H` → `Ḫ`) |
| `--strict` | Enable strict warning mode (warns about unexpected markup) |
| `--test` | Run parser self-tests |
| `--append` | Append to output files instead of overwriting |

### About `--append`

If output files already exist, new content is appended after a newline. Each appended block always starts at the beginning of a new line, never in the middle of an existing line. This ensures that every line in the output is properly separated, matching the line structure of the input ATF files.

---

## 🔧 ATF Normalization Rules (Core)

Within Akkadian `%n` lines, the parser applies these transformations:

| Original Markup | Normalized Form |
|-----------------|-----------------|
| `( )`, `[ ]`, `< >` | Delimiters removed, content kept |
| `{ }` | Removed entirely |
| `\|` (pipe) | Converted to space |
| `\|\|`, `‡`, `—`, `–` | Normalized to `:` (phrase separator) |
| `x` (broken signs) | Collapsed to one `…` marker |
| `? ! * °` | Removed |
| Ellipsis | Preserved as `…` |
| Numerals | Preserved as-is |

---

## 💡 Typical Usage Examples

### Basic Conversion

    python src/akkapros/cli/atfparser.py "data/samples/L I.5 Erra and Išum SB I.atf" \
      -p erra \
      --outdir outputs

This produces:
- `outputs/erra_orig.txt`
- `outputs/erra_proc.txt`
- `outputs/erra_trans.txt` (if translations exist)

### Preserve Case and Original `h`

    python src/akkapros/cli/atfparser.py data/samples/file.atf \
      --preserve-case \
      --preserve-h \
      -p sample \
      --outdir outputs

### Remove Hyphens and Append to Existing Files

    python src/akkapros/cli/atfparser.py data/samples/file.atf \
      --remove-hyphens \
      --append \
      -p sample \
      --outdir outputs

### Run Self-Tests

    python src/akkapros/cli/atfparser.py --test

---

## 🔗 Pipeline Position

The ATF parser is the **first step** in the akkapros pipeline:

1. `atfparser.py` → `*_proc.txt`
2. `syllabifier.py` → `*_syl.txt`
3. `prosmaker.py` → `*_tilde.txt`
4. `metricalc.py` → metrics output  
   `printer.py` → formatted outputs (acute, bold, IPA, XAR)

For end-to-end one-command processing, see **`fullprosmaker.py`**.

---

## 📝 Important Notes

- This parser intentionally removes most structural metadata. It is optimized for prosodic analysis, not for scholarly edition preservation.
- **Line breaks are preserved** as meaningful structural information for downstream processing. Do not remove them manually.
- By default, input format is validated at startup and reports precise source + line for obvious corruption (for example missing `%n` lines or unbalanced markers).
- If you need to process multiple ATF files, consider using the demo scripts (`corpus-demo.sh` or `corpus-demo.ps1`) which handle batch processing.

### Validation Rules (Middle Strictness)

Validation is intentionally moderate: `atfparser.py` checks that the file is readable text and contains expected ATF content (`%n` lines), plus obvious corruption signatures (empty/binary content, unbalanced structural markers). It does not attempt full philological validation of every ATF edge case. The goal is to stop inputs that are clearly wrong enough to trigger major failures later, while keeping normal corpus workflows usable.
The validator is gatekeeper-only: it never rewrites or auto-corrects input; it only allows processing to continue or fails with a precise error.

---

## 🐛 Troubleshooting

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Missing translations | ATF file has no `#tr.en:` lines | Check the original file; some texts lack translations |
| Unexpected characters in output | Markup not covered by normalization rules | Run with `--strict` to see warnings |
| Wrong output directory | `--outdir` not specified | Files are written to current directory by default |

---

## ✅ Summary

`atfparser.py` transforms cluttered ATF files into clean, pipeline-ready Akkadian text. It removes editorial markup while preserving the linguistic content and line structure needed for prosodic analysis.