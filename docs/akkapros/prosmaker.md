# Prosmaker CLI (`prosmaker.py`)

This document describes what the prosmaker does, how to run it, and what files it reads and writes.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/prosmaker.py`
- Core logic: `src/akkapros/lib/prosody.py`

---

## 📋 Purpose

`prosmaker.py` applies moraic prosody realization to syllabified Akkadian text.

It takes input produced by the syllabifier (`*_syl.txt`) and creates the prosody-realized pivot format (`*_tilde.txt`), which is used by downstream modules (metrics, printer, full pipeline).

---

## 📂 Input and Output

### Input
- A syllabified file, typically `<prefix>_syl.txt`

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
| `-r, --relax-last` | For explicit `+` links, allow prosody realization propagation before the last linked word |
| `--test` | Run standard prosody realization tests |
| `--test-diphthongs` | Run diphthong-restoration tests |

### Important Note on Diphthongs

Diphthongs are **always restored automatically** after prosody realization. Temporary split markers inserted during syllabification are systematically removed in the output.

---

## 🎯 Accent Styles

| Style | Priority Order | Description |
|-------|----------------|-------------|
| **LOB** (Literary Old Babylonian) | 1. Final superheavy (incl. circumflex finals)<br>2. Rightmost non-final heavy<br>3. Final heavy | Default style, appropriate for literary texts |
| **SOB** (Standard Old Babylonian) | 1. Rightmost non-final heavy<br>2. Final heavy | Simpler rule set |

---

## 🔗 Explicit Linker (`+`) Behavior

The `+` marker in syllabified input indicates a forced prosodic unit.

| Mode | Behavior |
|------|----------|
| **Default** (strict) | Only the last linked word is eligible for prosody realization |
| **`--relax-last`** | Prosody realization may propagate leftward to previous linked words when needed |

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
4. `metricalc.py` and `printer.py` consume `*_tilde.txt` for metrics and formatted output

For one-command execution of all stages, see **`fullprosmaker.py`**.

---

## 📝 Important Notes

- **Output prefix** is sanitized to a filesystem-safe filename.
- The CLI name is `prosmaker.py` (not `repairer.py`—this has been updated).
- All temporary markers from syllabification are resolved in the output.
- The prosody realization algorithm is fully deterministic given the input and style choice.

---

## ✅ Summary

`prosmaker.py` implements the core prosody realization algorithm. It transforms syllabified text into a prosody-realized pivot format by adding prominence markers (`~`) according to the selected accent style and linking rules. The output serves as the foundation for all downstream analysis and formatting.