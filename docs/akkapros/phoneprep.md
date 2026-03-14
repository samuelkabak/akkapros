# Phoneprep CLI (`phoneprep.py`)

This document explains what `phoneprep.py` does, how to run it, and what files it produces.

**Implementation:**
- CLI wrapper: `src/akkapros/cli/phoneprep.py`
- Core logic: `src/akkapros/lib/phoneprep.py`

---

## 📋 Purpose

`phoneprep.py` generates a recording script optimized for diphone coverage, plus machine-readable sidecars for downstream segmentation and MBROLA dataset preparation.

### Core Goals

1. **Cover legal Akkadian diphone transitions** with minimal recording burden
2. **Keep pronunciation prompts human-readable** (IPA-like display script)
3. **Emit deterministic sidecars** for automatic alignment and segmentation tooling
4. **Optionally generate an interactive HTML recording assistant**

---

## 🚀 Quick Start

### Windows (PowerShell)

    python src/akkapros/cli/phoneprep.py ^
      --coverage 3 ^
      --with-html-recording-helper ^
      --seed 100 ^
      --output demo/akkapros/phoneprep/results/phoneprep.txt

### Unix/Linux/macOS

    python src/akkapros/cli/phoneprep.py \
      --coverage 3 \
      --with-html-recording-helper \
      --seed 100 \
      --output demo/akkapros/phoneprep/results/phoneprep.txt

### Demo Scripts

Ready-to-run demo launchers are provided:

- Windows: `demo/akkapros/phoneprep/phoneprep-demo.ps1`
- Unix: `demo/akkapros/phoneprep/phoneprep-demo.sh`

---

## 📂 Generated Files

If output is `.../phoneprep.txt`, the CLI writes these files in the same directory:

| File | Description |
|------|-------------|
| `phoneprep.txt` | **Human recording script** – Each utterance wrapped in `_..._`, dots mark syllable boundaries, sections grouped by pattern class |
| `phoneprep_manifest.tsv` | **Machine manifest** – One row per utterance with MBROLA symbols, diphone list, pattern ID, batch tag (unless `--no-sidecars`) |
| `phoneprep_diphones.tsv` | **Diphone index** – One row per diphone cursor position (unless `--no-sidecars`) |
| `phoneprep_words.txt` | **Compact word list** – One MBROLA-symbol utterance per line (unless `--no-sidecars`) |
| `phoneprep_recording_helper.html` | **Interactive recording assistant** – Guides chunk recording and produces timestamped logs (when `--with-html-recording-helper`) |

---

## ⚙️ CLI Options

### Coverage and Optimization

| Option | Description |
|--------|-------------|
| `--coverage, -c <1-4>` | Target per-diphone coverage (default: `3`) |
| `--max-non-vv <1-3>` | Maximum non-VV target count |
| `--non-vv-target-ratio <float>` | Soft completion ratio for non-VV targets (default: `0.8`) |
| `--strict-max-non-vv` | Hard cap mode for non-VV counts |
| `--max-iterations <int>` | Stochastic optimizer sample budget |
| `--candidate-pool-size <int>` | Random candidates scored per selection round |
| `--seed <int>` | Reproducible random seed |

### Batching and Outputs

| Option | Description |
|--------|-------------|
| `--two-batch-emphatic` | Build two recording batches (plain-first, then mixed) |
| `--output, -o <path>` | Output script path (default: `outputs/akkadian_script.txt`) |
| `--no-sidecars` | Skip manifest, diphone, and word sidecars |

### Recording Helper

| Option | Description |
|--------|-------------|
| `--with-html-recording-helper` | Create interactive HTML recording assistant alongside script file |
| `--recording-max-words <int>` | Max accepted words per recording chunk (default: `1000`) |

### Inventory Override and Debug

| Option | Description |
|--------|-------------|
| `--debug-reduced-set` | Use reduced inventory for testing |
| `--plain-consonants <chars>` | Override plain consonants |
| `--emphatic-consonants <chars>` | Override emphatic consonants |
| `--plain-vowels-short <chars>` | Override short plain vowels |
| `--plain-vowels-long <chars>` | Override long plain vowels |
| `--colored-vowels-short <chars>` | Override short colored vowels |
| `--colored-vowels-long <chars>` | Override long colored vowels |

### Testing

| Option | Description |
|--------|-------------|
| `--test` | Run self-tests and exit |

---

## 🔤 How Word Lists Are Created

### 1. Inventory Model

The script defines:

- **Plain consonants** and **emphatic consonants** (`q`, `ṣ`, `ṭ`)
- **Plain vowels** and **colored vowels** (post-emphatic allophones)
- **Boundary symbol** `#` for word edges

Long vowels are folded to doubled short-vowel behavior for generation logic.

### 2. Phonotactic Legality Constraints

Two critical rules are enforced during generation:

| Rule | Description |
|------|-------------|
| **Post-emphatic coloring** | Colored vowels are legal only after emphatic consonants (`q`, `ṣ`, `ṭ`). Word-initial vowels must be plain. |
| **V-V sequence class matching** | In vowel-vowel sequences, both vowels must belong to the same class (both plain or both colored). |

### 3. Word Shape Patterns

The generator samples legal words across three templates:

| Pattern | Structure | Display Form | Purpose |
|---------|-----------|--------------|---------|
| **Pattern 1** | `_ V C C V C C V _` | `VC.CVC.CV` | Exposes diverse C-C, C-V, V-C boundaries |
| **Pattern 2** | `_ C V C V C C V C _` | `CV.CVC.CVC` | Tests internal clusters and boundaries |
| **Pattern 3** | `_ C V V C V V C _` | `CVV.CVVC` | Tests long vowels and V-V transitions |

These templates cover boundary contexts including C-C, C-V, V-C, V-V, and word edges.

### 4. Coverage Optimizer

`phoneprep.py` uses a **stochastic greedy selector**:

1. Compute reachable diphone inventory under legality constraints
2. Repeatedly sample candidate words
3. Score candidates by how much they improve under-covered diphones
4. Stop when target criteria are met or sample budget is exhausted

This approach maximizes coverage while keeping the final list compact.

### 5. Symbol Mapping for Sidecars

| Output | Symbol System | Purpose |
|--------|---------------|---------|
| **Human script** (`phoneprep.txt`) | IPA-like display | Reciter-friendly prompts |
| **Sidecars** (`*_manifest.tsv`, etc.) | MBROLA/X-SAMPA-like | Machine segmentation and MBROLATOR pipeline |

---

## 🎙️ Pronunciation Expectations for Recording

The generated script includes guidance for recorders:

1. **Speak each line naturally** – as if reading connected speech
2. **Pause ~1 second** before and after each word
3. **Record at 16 kHz, 16-bit, mono** – standard for speech processing

### Line Format Notes

- `_..._` wraps one utterance
- `.` marks syllable boundaries to encourage consistent articulation
- Read the entire displayed line as one item

---

## 🖥️ Recording Helper HTML: Behavior and Logic

When `--with-html-recording-helper` is enabled, an interactive HTML page is generated.

### On Page Load

1. Word list is loaded from utterance lines in `phoneprep.txt`
2. UI starts with "Press space to start"
3. Log area is empty
4. Recording index starts at `1`

### Keyboard Controls

| Key | Action |
|-----|--------|
| **Space** | Toggle recording state – starts chunk, displays current word, or accepts word and stops chunk |
| **Right Arrow** | Accept current word and move to next (continue within same chunk) |
| **Left Arrow** | Mark pronunciation error and repeat same word (index does not advance) |

### Recommended Operator Workflow

1. Press `Space` to start chunk and show first word
2. Pronounce the displayed word
3. If correct, press `Right Arrow` to advance
4. If mistake, press `Left Arrow`, re-pronounce, then `Right Arrow` when correct
5. To stop and save current chunk, press `Space` while a word is displayed
6. Save audio with prompted filename, then press `Space` to start next chunk

### End of Word List

When all words are completed:
- Display changes to "All words completed"
- Hint shows final WAV filename and log filename to save
- A `COMPLETE` event is appended to log

### WAV Naming Convention

    <prefix>_NNN.wav

Where:
- `<prefix>` is the output script stem (e.g., for `phoneprep.txt`, prefix is `phoneprep`)
- `NNN` is zero-padded recording index (`001`, `002`, etc.)

### Log Format and Export

The helper writes tab-separated event rows in the textarea with fields:

| Field | Description |
|-------|-------------|
| Timestamp | ISO timestamp |
| Elapsed | Clock time since start |
| Recording index | Current chunk number |
| WAV filename | Current output file |
| Word index | Current word position |
| Accepted count | Words accepted in current chunk |
| Error count | Errors on current word |
| Event | `DISPLAY`, `RECORDING_START`, `ACCEPT`, `ERROR_REPEAT`, `RECORDING_STOP`, `COMPLETE` |
| Displayed word | Current utterance |
| Metadata | Optional additional info |

Use **`Copy Log`** to copy all rows, then save to:

    <prefix>_segmanifest.txt

This log is designed for downstream automatic segmentation.

---

## 🔁 Two-Batch Mode

When `--two-batch-emphatic` is enabled, the script creates:

| Batch | Content | Purpose |
|-------|---------|---------|
| **Batch 1** | Plain consonants + plain vowels only | Establishes baseline voice |
| **Batch 2** | Mixed consonants and mixed vowels under post-emphatic legality | Captures emphatic coloring effects |

Manifest rows include batch labels so downstream tools can preserve batch provenance.

---

## 🔗 Where This Fits in the MBROLA Workflow

Use this document together with `docs/akkapros/mbrola-voice-prep.md`.

### Pipeline Summary

1. **Generate** script, sidecars, and HTML with `phoneprep.py`
2. **Record** WAV chunks using the helper page and save exported event log
3. **Feed** WAV + log + sidecars to segmenter (when released) to build MBROLATOR dataset
4. **Run** MBROLATOR to build the MBROLA voice

---

## 🧪 Testing

Run the self-test suite:

    python src/akkapros/cli/phoneprep.py --test

---

## ✅ Summary

`phoneprep.py` bridges the gap between computational phonology and speech synthesis. It generates optimized recording scripts that maximize diphone coverage with minimal recording effort, produces machine-readable sidecars for automated processing, and provides an interactive assistant for high-quality recording sessions. This toolkit is essential for building MBROLA voices for Akkadian synthesis.