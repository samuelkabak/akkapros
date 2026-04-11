# Prosmaker CLI (`prosmaker.py`)

This document describes what the prosmaker does, how to run it, and what files it reads and writes.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/prosmaker.py`
- Core logic: `src/akkapros/lib/prosody.py`

---

## 📋 Purpose

`prosmaker.py` applies moraic prosody realization to syllabified Akkadian text.

It takes input produced by the syllabifier (`*_syl.txt`) and creates the prosody-realized pivot format (`*_tilde.txt`), which is used by downstream modules and full-pipeline stages.

For researchers, this is the stage where syllabified words become a prosodic
analysis. The stage decides whether a word remains independent, whether it
joins a neighboring word into one prosodic unit, and where the added mora is
realized. It does not yet assign phonetic duration or pitch.

---

## 📂 Input and Output

### Input
- A syllabified file, typically `<prefix>_syl.txt`

`prosmaker.py` consumes only inherited `file.title` from upstream front matter.
It computes line, word, syllable, function-word, prosodic-unit, and
accentuated-syllable indicators internally and logs them at runtime instead of
serializing them into output front matter.

### Output
- A prosody-realized file `<prefix>_tilde.txt`

**Naming rules:**
- If `-p/--prefix` is provided: `<outdir>/<prefix>_tilde.txt`
- If no prefix is provided: output filename is derived from input stem (with `_syl` removed when present)

---

## 🚀 Command Syntax

    python src/akkapros/cli/prosmaker.py <input_syl.txt> [options]

---

## ⚙️ Options

| Option | Description |
|--------|-------------|
| `--version` | Print CLI version |
| `-p, --prefix <name>` | Output prefix (result file: `<prefix>_tilde.txt`) |
| `--outdir <dir>` | Output directory (default: current directory) |
| `--style {lob,sob}` | Accent style used to choose prosody realization target syllables (default: `lob`) |
| `--mora-mode {bi,mono}` | Accentuation trigger mode: bimoraic parity gate (`bi`, default) or academic mono-mode (`mono`) |
| `-r, --relax-last` | For explicit `+` links, allow prosody realization propagation before the last linked word |
| `--test` | Run standard prosody realization tests |
| `--test-diphthongs` | Run diphthong-restoration tests |

### Important Note on Diphthongs

Diphthongs are **always restored automatically** after prosody realization. The `_tilde.txt` pivot output now keeps the diphthong memory marker `¨` (for example `ti¨ā~m·tu`) so downstream stages can still see the internal syllable boundary. The printer removes `¨` only in final user-facing outputs.

The `_tilde.txt` pivot also preserves armored punctuation and escaped chunks as `⟦...⟧`. Downstream stages consume that armor directly, and printer restores normal visible punctuation only when rendering user-facing outputs.

The `_tilde.txt` pivot now also preserves merge provenance directly: explicit links inherited from input remain `+`, while automatic merges introduced by prosody are serialized as `&`.

---

## 🎯 Accent Styles

| Style | Priority Order | Description |
|-------|----------------|-------------|
| **LOB** (Literary Old Babylonian) | 1. Final superheavy (incl. circumflex finals)<br>2. Rightmost non-final heavy<br>3. Final heavy | Default style, appropriate for literary texts |
| **SOB** (Standard Old Babylonian) | 1. Rightmost non-final heavy<br>2. Final heavy | Simpler rule set |

---

## 🔎 How to Read `_tilde.txt`

`_tilde.txt` is the prosody pivot. It is not a final pronunciation file. It is
the compact record of the prosodic decisions that later stages inherit.

| Symbol | Meaning |
|--------|---------|
| `~` | one extra mora is realized on this syllable |
| `+` | explicit user-supplied link inherited from the input |
| `&` | automatic merge introduced by the prosody engine |
| space | ordinary boundary between separate prosodic units |
| `·` / `-` | preserved internal syllable or bound-morpheme structure |

Example:

```text
gi·mir&dad~·mē
```

This means `gimir` and `dadmē` were merged into one prosodic unit by the
algorithm, and the added mora was realized on `dad`.

---

## μ Mora Modes

| Mode | Behavior |
|------|----------|
| **`bi`** | Default. A standalone word or eligible prosodic unit is accentuated only when its current mora count is odd. Even units emit unchanged. |
| **`mono`** | Comparative academic mode. Structural grouping still determines the unit, but eligible units may be accentuated regardless of current parity. If no internal candidate is legal, the unit falls directly to last resort instead of forward-merging. |

`mono` changes the trigger for attempting accentuation. It does **not** change the
`lob` / `sob` target-selection hierarchy or the legal accentuation operations,
but it also does not use bimoraic forward merge as a repair step.

In plain language:

- `bi` keeps the repository's default bimoraic model. Even units can pass
    through unchanged, while odd units may require accentuation or merging.
- `mono` is a comparative academic mode. It may accentuate an eligible unit
    even when that unit is already even, and it does not merge forward merely to
    satisfy bimoraic parity.

---

## 🔗 Explicit Linker (`+`) Behavior

The `+` marker in syllabified input indicates a forced prosodic unit.

In `_tilde.txt`, explicit `+` links remain `+`. If prosody extends that linked group further, the added internal merge boundary is written as `&`.

| Mode | Behavior |
|------|----------|
| **Default** (strict) | Only the last linked word is eligible for prosody realization |
| **`--relax-last`** | Prosody realization may propagate leftward to previous linked words when needed |

The mora mode does not override explicit-link locking. Words before the
eligible linked tail remain protected from accentuation in both `bi` and
`mono`.

Example with `bā·nû+a·pil`:

- Default: `bā·nû+~a·pil` (last word accentuated)
- Relaxed: `bā·nû~+a·pil` (accentuation propagates leftward)

---

## 💡 Typical Usage Examples

### Run with Defaults

    python src/akkapros/cli/prosmaker.py outputs/erra_syl.txt

### Run with Explicit Style and Output Location

    python src/akkapros/cli/prosmaker.py outputs/erra_syl.txt \
      --style lob \
      -p erra \
      --outdir outputs

### Run in Academic Comparison Mode

        python src/akkapros/cli/prosmaker.py outputs/erra_syl.txt \
            --style lob \
            --mora-mode mono \
            -p erra-mono \
            --outdir outputs

### Run with Relaxed Linker Behavior

    python src/akkapros/cli/prosmaker.py outputs/erra_syl.txt \
      --style sob \
      --relax-last \
      -p erra \
      --outdir outputs

### Run Tests

    python src/akkapros/cli/prosmaker.py --test
    python src/akkapros/cli/prosmaker.py --test-diphthongs

---

## 🔗 Pipeline Position

The prosmaker is the **third step** in the akkapros pipeline:

1. `atfparser.py` → `*_proc.txt`
2. `syllabifier.py` → `*_syl.txt`
3. **`prosmaker.py`** → `*_tilde.txt`
4. `phonetizer.py` consumes `*_tilde.txt` and produces `_ophone.txt` plus `_phone.txt`
5. `metricalc.py` and `printer.py` both consume `_ophone.txt` plus `_phone.txt`

`_tilde.txt` remains the upstream prosody pivot for phonetizer input. It is no
longer the active downstream input for metrics or printer.

In practice:

- inspect `_tilde.txt` when you want to study grouping and accentuation
    decisions
- inspect `_phone.txt` and `_ophone.txt` when you want phonetic timing,
    intonation, or metrics-ready structure
- inspect printer outputs when you want a user-facing reading form

For one-command execution of all stages, see **`fullprosmaker.py`**.

---

## 📝 Important Notes

- **Output prefix** is sanitized to a filesystem-safe filename.
- By default, startup performs lightweight format validation on input files and fails fast on obviously partial/corrupted inputs with precise source + line error reporting.
- The CLI name is `prosmaker.py` (not `repairer.py`—this has been updated).
- All temporary markers from syllabification are resolved in the output.
- Escaped non-Akkadian chunks (`{{text}}` or `{tag{text}}`) are carried through as non-lexical material.
- Tags in `{tag{text}}` follow `[0-9a-z_]{1,16}`; tags starting with `_` are internal-only conventions.
- The prosody realization algorithm is fully deterministic given the input and style choice.
- Output front matter records `metadata.options.mora_mode` so downstream stages
    can identify whether `bi` or `mono` was used.
- Output front matter from this stage no longer carries explicit-link counts for metrics; downstream metrics derives them from phone-row structure.

### Validation Rules (Middle Strictness)

`prosmaker.py` expects syllabified `*_syl.txt` input. Validation checks that input is text and that syllabified content includes explicit word-ending markers (`¦`). It rejects obvious corruption (empty/binary) but does not require a final trailing newline in the file (missing final newline is normalized in memory). It is deliberately not ultra-strict: it will not validate every linguistic detail in advance. The key goal is to prevent processing clearly wrong stage input such as `*_proc.txt`, because that would produce wrong results or large exceptions.
The validator is gatekeeper-only: it never rewrites or auto-corrects input; it only allows processing to continue or fails with a precise error.

---

## ✅ Summary

`prosmaker.py` implements the core prosody realization algorithm. It transforms syllabified text into a prosody-realized pivot format by adding prominence markers (`~`) according to the selected accent style and linking rules. The output serves as the foundation for all downstream analysis and formatting.