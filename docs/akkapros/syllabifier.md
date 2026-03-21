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
| `--short-punct-chars <chars>` | Additional characters to classify as short-pause punctuation |
| `--long-punct-chars <chars>` | Additional characters to classify as long-pause punctuation |
| `--short-punct-pattern <regex>` | Repeatable regex for short-pause punctuation segments |
| `--long-punct-pattern <regex>` | Repeatable regex for long-pause punctuation segments |
| `--number-format <regex>` | Number regex override; empty uses built-in English-grouping-compatible pattern |
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

### Extend Punctuation Allowlist

        python src/akkapros/cli/syllabifier.py outputs/text_proc.txt \
            --short-punct-chars "·" \
            --long-punct-chars "※" \
            --short-punct-pattern "^\\s*[·]+\\s*$" \
            --long-punct-pattern "^\\s*[※]+\\s*$" \
            -p text \
            --outdir outputs

### Select Number Locale

        python src/akkapros/cli/syllabifier.py outputs/text_proc.txt \
            --number-format "-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?" \
            -p text \
            --outdir outputs

### Run Tests

    python src/akkapros/cli/syllabifier.py --test

---

## 📝 Important Processing Notes

- **Diphthong handling**: The library may insert glottal stops between adjacent vowels for diphthong expansion (e.g., `ua` → `u·ʾa`). These are later restored by `prosmaker.py`.
- **Hyphen and linker behavior** is context-sensitive and follows Akkadian morphological boundaries.
- **Punctuation** is preserved as escaped material (`⟦...⟧`) and is not syllabified as Akkadian words.
- **Strict punctuation allowlist** is enforced. Unclassified punctuation/non-word symbols now fail fast with a line-aware error instead of being silently accepted.
- **Line-start bullets and `#`** are handled as punctuation suites and preserved in escaped output (`⟦...⟧`) rather than treated as Markdown structure.
- **Line breaks in preserve mode** are never removed from output; punctuation/escape/number suites are emitted per line and separated by `\n`.
- **Escapes in source text**: `{{text}}` and `{tag{text}}` are preserved verbatim, wrapped as `⟦...⟧`, and excluded from Akkadian syllabification.
- **Nested escapes** are intentionally unsupported; only `{{...}}` and one-level `{tag{...}}` are recognized.
- **Word endings** are explicitly marked with `¦` for downstream processing.
- By default, input format is validated at startup and reports precise source + line for obvious corruption or wrong stage input (for example raw ATF lines in a `*_proc.txt` input).

### Regex Semantics for Punctuation Patterns

- Patterns are Python regex expressions compiled at startup, before file processing begins.
- `--short-punct-pattern` and `--long-punct-pattern` are repeatable; each use appends one full regex.
- Anchors `^` and `$` refer to the full punctuation chunk (including surrounding spaces and line boundaries).
- For line/file boundaries, use pseudo-tokens:
    - `[:bol:]` = beginning of line
    - `[:eol:]` = end of line
- `[:bof:]` is intentionally unsupported.
- EOF is normalized internally to end-of-line semantics; user patterns do not need a dedicated EOF token.
- Escape `$` as `\$` when you need a literal dollar character.
- The diphthong separator `¨` is a normal literal character in regex; it is not treated specially by punctuation matching.
- Practical rule: use anchored patterns like `^...$` for exact suite matching to avoid accidental partial matches.

Example (em dash with required surrounding spacing or line-end):

    ^(?:[:bol:]|[ \t]+)—(?:[ \t]+|[:eol:])$

Example (custom long punctuation: two dashes with leading space and trailing space or line-end):

    --long-punct-pattern "^[ \t]+--([ \t]+|[:eol:])$"

Matches:
- ` -- ` in `aba -- ana`
- ` --` in `aba --\nana`

### Number Regex Notes

`--number-format` accepts a regex (core number shape). If empty, built-in English-grouping-compatible behavior is used.

Examples:
- strict no-grouping: `-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?`
- English-grouping-compatible: `(?:-?(?:0|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\\.[0-9]+)?|-?(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?)`

Why `[` is invalid for `--number-format`:
- `[` starts a character class in regex and must be closed (`]`), so it raises an "unterminated character set" compile error.

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