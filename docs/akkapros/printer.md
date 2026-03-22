# Printer CLI (`printer.py`)

This document explains what `printer.py` does, how to run it, and what output formats it writes.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/printer.py`
- Core formatter library: `src/akkapros/lib/print.py`

---

## 📋 Purpose

`printer.py` converts prosody-realized pivot text (`*_tilde.txt`) into user-facing reading and phonetic outputs.

### Supported Output Formats

| Format | Description | File Extension |
|--------|-------------|----------------|
| **Acute** | Stress marked with acute accent after vowel | `_accent_acute.txt` |
| **Bold** | Stress marked with bold in Markdown | `_accent_bold.md` |
| **IPA** | International Phonetic Alphabet transcription | `_accent_ipa.txt` |
| **XAR** | Specialized transliteration (accented and plain) | `_accent_xar.txt`, `_xar.txt` |
| **MBROLA** | X-SAMPA-like format for speech synthesis | `_accent_mbrola.txt` |

---

## 📂 Input and Output

### Input
- One `*_tilde.txt` file (prosody-realized pivot format)

### Outputs (by selected flags)
- `<prefix>_accent_acute.txt`
- `<prefix>_accent_bold.md`
- `<prefix>_accent_ipa.txt`
- `<prefix>_accent_xar.txt`
- `<prefix>_xar.txt`
- `<prefix>_accent_mbrola.txt`

**Default behavior:** If no output flags are selected, acute + bold are generated.

---

## 🚀 Command Syntax

    python src/akkapros/cli/printer.py <input_tilde.txt> [options]

---

## ⚙️ Options

### General Options

| Option | Description |
|--------|-------------|
| `--version` | Print CLI version |
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
| `--mbrola` | MBROLA/X-SAMPA-like output |

### IPA-Specific Options

| Option | Description |
|--------|-------------|
| `--ipa-proto-semitic {preserve,replace}` | Pharyngeal/glottal mapping:<br>• `preserve`: strict mode (Old Akkadian distinctions)<br>• `replace`: OB-style pharyngeal merger (default) |
| `--circ-hiatus` | Speculative mode splitting circumflex vowels into hiatus in IPA<br>Example: `qû → qʊ.ʊ` |

---

## 💡 Typical Usage Examples

### Default Outputs (Acute + Bold)

    python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
      -p erra \
      --outdir outputs

### IPA Output with OB Pharyngeal Policy

    python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
      --ipa \
      --ipa-proto-semitic replace \
      -p erra \
      --outdir outputs

### IPA Output with Speculative Circumflex Hiatus

    python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
      --ipa \
      --circ-hiatus \
      -p erra \
      --outdir outputs

### Generate All Display Outputs

    python src/akkapros/cli/printer.py outputs/erra_tilde.txt \
      --acute --bold --ipa --xar --mbrola \
      -p erra \
      --outdir outputs

### Run Tests

    python src/akkapros/cli/printer.py --test

---

## 📝 Output Format Details

### Acute Format (`_accent_acute.txt`)

Stress is marked with an acute accent (`´`) placed **immediately after** the vowel of the prominent syllable.

Example: `tāḫā´za ik´taṣar`

### Bold Format (`_accent_bold.md`)

Prominent syllables are wrapped in `**` for visual emphasis in Markdown.

Example: `tā**ḫā**za **ik**taṣar`

### IPA Format (`_accent_ipa.txt`)

Full phonetic transcription with:

| Feature | Marking |
|---------|---------|
| Stress | `ˈ` before prominent syllable |
| Length | `ː` for long, `ːː` for extra-long |
| Emphatic coloring | Vowel backing after `q`, `ṣ`, `ṭ` (e.g., `sˤɑr`) |
| Prosodic boundaries | `|` for short pause, `‖` for long pause |

Example: `taː.ˈχaːː.za.ˈʔikː.ta.sˤɑr`

**Emphatic vowel coloring**: In Semitic languages, emphatic consonants (`q`, `ṣ`, `ṭ`) retract the tongue body, lowering the second formant (F2) of following vowels. This is transcribed in IPA as vowel backing: plain `/a/` → `/ɑ/`, `/i/` → `/ɨ/`, `/u/` → `/ʉ/`, `/e/` → `/ɛ/`. Example: sˤɑr (plain sar would be /sar/).

Escaped chunks from earlier stages are preserved in IPA metadata as:

- `⟨escape:{{text}}⟩`
- `⟨escape:{tag{text}}⟩`

Tags follow `[0-9a-z_]{1,16}`. Tags beginning with `_` are internal pipeline tags and are preserved verbatim unless a dedicated expansion rule is added.

### XAR Format (`_xar.txt` and `_accent_xar.txt`)

Specialized transliteration with:
- Consonant remapping for emphatics
- Doubled notation for long vowels
- Mixed pairs for circumflex vowels (e.g., `eâ`)

Two files are generated:
- `_accent_xar.txt`: with prominence marked
- `_xar.txt`: plain version without accent markers

### MBROLA Format (`_accent_mbrola.txt`)

X-SAMPA-like format designed for speech synthesis, compatible with the MBROLA diphone synthesizer. Used with the 878-word recording script included in the toolkit.

---

## 🔗 Pipeline Position

`printer.py` is typically run after prosody realization:

1. `atfparser.py` → `*_proc.txt`
2. `syllabifier.py` → `*_syl.txt`
3. `prosmaker.py` → `*_tilde.txt`
4. **`printer.py`** → formatted outputs

For one-command processing that includes all stages, see **`fullprosmaker.py`**.

---

## ✅ Summary

`printer.py` transforms the internal prosody-realized pivot format into multiple human-readable and machine-readable outputs. It supports scholarly notation (acute), publication-ready formatting (bold), phonetic analysis (IPA), specialized transliteration (XAR), and speech synthesis preparation (MBROLA). The flexible flag system allows researchers to generate exactly the formats they need.

By default, input format is validated at startup and reports precise source + line details for obvious corruption in `*_tilde.txt` input.

### Validation Rules (Middle Strictness)

`printer.py` expects a `*_tilde.txt` file from the prosody stage. Validation is intentionally moderate: readable short plain tilde lines are accepted, while obvious wrong-stage input (`*_syl.txt` markers like `¦`) and corruption risks (empty/binary) are rejected. A final trailing newline is not mandatory (missing newline is normalized in memory). It does not try to validate every phonological detail before formatting. The purpose is to avoid processing inputs that are clearly from the wrong stage or likely to trigger major runtime exceptions.
The validator is gatekeeper-only: it never rewrites or auto-corrects input; it only allows processing to continue or fails with a precise error.