# Printer CLI (`printer.py`)

This document explains what `printer.py` does, how to run it, and what output formats it writes.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/printer.py`
- Core formatter library: `src/akkapros/lib/print.py`

---

## 📋 Purpose

`printer.py` converts phonetizer-owned phone rows (`*_phone.txt` and the
matching `*_ophone.txt`) into user-facing reading outputs.

### Supported Output Formats

| Format | Description | File Extension |
|--------|-------------|----------------|
| **Acute** | Stress marked with acute accent after vowel | `_accent_acute.txt` |
| **Bold** | Stress marked with bold in Markdown | `_accent_bold.md` |
| **IPA** | International Phonetic Alphabet transcription | `_accent_ipa.txt` |
| **XAR** | Specialized transliteration (accented and plain) | `_accent_xar.txt`, `_xar.txt` |

---

## 📂 Input and Output

### Input
- One `<prefix>_phone.txt` file
- Optional matching `<prefix>_ophone.txt` file via `--ophone`; otherwise the
    CLI derives it from the input name

`printer.py` consumes the phonetizer-owned downstream artifacts directly.
Pause strength and line-break behavior come from phone rows, not from
re-parsing `_tilde` punctuation as an active downstream source.

### Outputs (by selected flags)
- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`
- `<prefix>_xar.txt`

**Default behavior:** If no output flags are selected, acute + bold are generated.

---

## 🚀 Command Syntax

    python src/akkapros/cli/printer.py <input_phone.txt> [options]

---

## ⚙️ Options

### General Options

| Option | Description |
|--------|-------------|
| `--version` | Print CLI version |
| `--ophone <file>` | Explicit matching `<prefix>_ophone.txt` |
| `-p, --prefix <name>` | Output prefix |
| `--outdir <dir>` | Output directory (default: current directory) |
| `--test` | Run CLI and library printer tests |

### Output Selectors

| Option | Generates |
|--------|-----------|
| `--acute` | Acute-marked text |
| `--bold` | Bold-marked Markdown |
| `--ipa` | IPA transcription |
| `--xar` | Both XAR files (accented and plain) |
| `--print-merger` | Show the visible merge connector `‿` in acute, bold, and accented XAR output |

### IPA-Specific Options

| Option | Description |
|--------|-------------|
| `--ipa-proto-semitic {preserve,replace}` | Pharyngeal/glottal mapping:<br>• `preserve`: `ḥ -> ħ`, `ḫ -> χ`, `ʿ -> ʕ`, `ʾ -> ʔ`<br>• `replace`: `ḥ -> ʔ`, `ḫ -> χ`, `ʿ -> ʔ`, `ʾ -> ʔ` (default) |
| `--circ-hiatus` | Speculative mode splitting circumflex vowels into hiatus in IPA<br>Example: `qû → qʊ.ʊ` |

---

## 💡 Typical Usage Examples

### Default Outputs (Acute + Bold)

        python src/akkapros/cli/printer.py outputs/erra_phone.txt \
      -p erra \
      --outdir outputs

### IPA Output with OB Pharyngeal Policy

        python src/akkapros/cli/printer.py outputs/erra_phone.txt \
      --ipa \
      --ipa-proto-semitic replace \
      -p erra \
      --outdir outputs

### IPA Output with Speculative Circumflex Hiatus

        python src/akkapros/cli/printer.py outputs/erra_phone.txt \
      --ipa \
      --circ-hiatus \
      -p erra \
      --outdir outputs

### Generate All Display Outputs

        python src/akkapros/cli/printer.py outputs/erra_phone.txt \
  --acute --bold --ipa --xar \
      -p erra \
      --outdir outputs

### Run Tests

    python src/akkapros/cli/printer.py --test

---

## 📝 Output Format Details

### Acute Format (`_accent_acute.txt`)

Stress is marked with an acute accent (`´`) placed **immediately after** the vowel of the prominent syllable.

Merged words print with a normal space by default. Use `--print-merger` to preserve the visible connector `‿`.

Printer reconstructs lexical rendering from the phone-row stream. Explicit `+`
and internal `&` distinctions are preserved in the row boundaries and render
with the same visible merge policy as before.

Example: `tāḫā´za ik´taṣar`

### Bold Format (`_accent_bold.md`)

Prominent syllables are wrapped in `**` for visual emphasis in Markdown.
Preserved adjacent input lines are serialized with a trailing `\` so Markdown
renderers keep them as separate visible lines. Blank lines remain blank lines
and do not receive escape markers.

Merged words print with a normal space by default. Use `--print-merger` to preserve the visible connector `‿`.

Example: `ukappit-ma : ti**ām**tu pitiqša\`

Next line example: `tā**ḫā**za **ik**taṣar`

### IPA Format (`_accent_ipa.txt`)

Full phonetic transcription with:

| Feature | Marking |
|---------|---------|
| Stress | `ˈ` before prominent syllable |
| Length | `ː` for long, `ːː` for extra-long |
| Emphatic coloring | Vowel backing after `q`, `ṣ`, `ṭ` (e.g., `sˤɑr`) |
| Prosodic boundaries | `|` for short pause, `‖` for long pause |

Example: `taː.ˈχaːː.za.ˈʔikː.ta.sˤɑr`

`--ipa-proto-semitic preserve` keeps `ḥ`, `ḫ`, `ʿ`, and `ʾ` distinct. In
`replace` mode, `ḥ`, `ʿ`, and `ʾ` converge to `ʔ`, while `ḫ` remains `χ`.

**Emphatic vowel coloring**: In Semitic languages, emphatic consonants (`q`, `ṣ`, `ṭ`) retract the tongue body, lowering the second formant (F2) of following vowels. This is transcribed in IPA as vowel backing: plain `/a/` → `/ɑ/`, `/i/` → `/ɨ/`, `/u/` → `/ʉ/`, `/e/` → `/ɛ/`. Example: sˤɑr (plain sar would be /sar/).

This printer-side vowel coloring is post-emphatic only. `ḥ` does not trigger
automatic recoloring, so any `ḥ`-conditioned vowel quality must already be
encoded in the input text.

Escaped chunks from earlier stages are preserved in IPA metadata as:

- `⟨escape:{{text}}⟩`
- `⟨escape:{tag{text}}⟩`

Tags follow `[0-9a-z_]{1,16}`. Tags beginning with `_` are internal pipeline tags and are preserved verbatim unless a dedicated expansion rule is added.

### XAR Format (`_xar.txt` and `_accent_xar.txt`)

Specialized transliteration with:
- Consonant remapping for emphatics
- Apostrophe convergence for `ḥ`, `ʿ`, and `ʾ`, while `ḫ` remains `ḫ`
- Doubled notation for long vowels
- Mixed pairs for circumflex vowels (e.g., `eâ`)

Two files are generated:
- `_accent_xar.txt`: with prominence marked
- `_xar.txt`: plain version without accent markers

In `_accent_xar.txt`, merged words print with a normal space by default. Use `--print-merger` to preserve the visible connector `‿`. The plain `_xar.txt` output keeps space-separated word boundaries.

XAR does not infer `ḥ`-conditioned vowel coloring. If the intended reader text
needs `'e` rather than `'a`, that vowel quality must already be present in the
input text.

Speech-synthesis `.pho` export is no longer owned by `printer.py`. Use `phonetizer.py` or `fullprosmaker.py` to produce `<prefix>_ombrola.pho` and `<prefix>_mbrola.pho` from the phonetize stage.

---

## 🔗 Pipeline Position

`printer.py` is typically run after phonetization:

1. `atfparser.py` → `*_proc.txt`
2. `syllabifier.py` → `*_syl.txt`
3. `prosmaker.py` → `*_tilde.txt`
4. `phonetizer.py` → `*_ophone.txt`, `*_phone.txt`
5. **`printer.py`** → formatted outputs

For one-command processing that includes all stages, see **`fullprosmaker.py`**.

---

## ✅ Summary

`printer.py` transforms the phonetizer-owned downstream row stream into
multiple human-readable outputs. It supports scholarly notation (acute),
publication-ready formatting (bold), phonetic analysis (IPA), and specialized
transliteration (XAR). Speech-synthesis `.pho` export now belongs to the
phonetize stage.

By default, input format is validated at startup and reports precise source +
line details for obvious corruption in `*_phone.txt` input.

Printer output front matter preserves the standard YAML wrapper used by the
pipeline text stages, but it does not republish any inherited `metadata.data`
block. Printer outputs keep `input_file_id` and resolved options only.

### Validation Rules (Middle Strictness)

`printer.py` expects a `*_phone.txt` file from the phonetize stage. Validation
checks the canonical phone-row line format and the `file.format: "phone"`
frontmatter contract, then processes the matching `_ophone.txt` sibling or the
path supplied via `--ophone`.

The phonetizer normalizes a missing final break into one final `<EOL>` long-
pause row before these files are written. `printer.py` therefore inherits the
final line break from the phone stream instead of inventing a separate EOF
pause rule downstream.

See also: `docs/akkapros/phonetizer-phone-file-guide.md`

Any residual `_tilde` reconstruction helpers in the library are internal
compatibility code, not the active printer input contract.
The validator is gatekeeper-only: it never rewrites or auto-corrects input; it only allows processing to continue or fails with a precise error.