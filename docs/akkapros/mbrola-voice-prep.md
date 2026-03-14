# How to Create an MBROLA Voice for Akkadian

This guide explains the practical pipeline currently implemented in `akkapros`, plus the handoff points for tools outside this repository.

---

## 🎯 Goal

Build an Akkadian MBROLA voice using:

1. **`phoneprep.py`** to generate recording prompts and machine sidecars
2. **HTML recording assistant** to record and log utterance timing and events
3. **`akkapros` segmenter** (planned, not yet released) to segment WAV chunks
4. **MBROLATOR** to compile the resulting diphone dataset into an MBROLA voice

---

## 📋 Pipeline Overview

    phoneprep.py → Recording materials → HTML helper → WAVs + event log
         ↓
    Sidecars (manifest, diphones, words)
         ↓
    [Segmenter - planned] → Aligned segments
         ↓
    MBROLATOR → MBROLA voice

---

## Step 1: Generate Recording Materials with phoneprep

### Command

    python src/akkapros/cli/phoneprep.py \
      --coverage 3 \
      --with-html-recording-helper \
      --seed 100 \
      --output demo/akkapros/phoneprep/results/phoneprep.txt

### Demo Launchers

Ready-to-run scripts are provided:

- Windows: `demo/akkapros/phoneprep/phoneprep-demo.ps1`
- Unix: `demo/akkapros/phoneprep/phoneprep-demo.sh`

### Expected Outputs

| File | Description |
|------|-------------|
| `phoneprep.txt` | Human recording script (`_..._` utterances, syllable dots) |
| `phoneprep_manifest.tsv` | One row per utterance with MBROLA symbols and full diphone list |
| `phoneprep_diphones.tsv` | One row per diphone cursor position |
| `phoneprep_words.txt` | One MBROLA-symbol utterance per line |
| `phoneprep_recording_helper.html` | Interactive recording controller with event logging |

**Note:** If you do not want sidecars, pass `--no-sidecars`.

---

## 🧠 Why This Word List Works

`phoneprep.py` does not output arbitrary words. It uses a **legality-aware, coverage-driven generator**.

### Key Features

1. **Enforces Akkadian-oriented phonotactic constraints**
2. **Covers boundary and internal diphone transitions**
3. **Tries to reach configured diphone coverage** with minimal utterance count

### Main Pattern Templates

| Pattern | Structure | Display Form |
|---------|-----------|--------------|
| Pattern 1 | `_ V C C V C C V _` | `VC.CVC.CV` |
| Pattern 2 | `_ C V C V C C V C _` | `CV.CVC.CVC` |
| Pattern 3 | `_ C V V C V V C _` | `CVV.CVVC` |

### Key Legality Rule

**Colored vowels are post-emphatic only** – they are licensed only after emphatic consonants (`q`, `ṣ`, `ṭ`). This reflects Akkadian phonology.

---

## Step 2: Record with the HTML Helper and Export Logs

Open `phoneprep_recording_helper.html` in a browser.

### What Happens When It Starts

1. Loads utterance lines from `phoneprep.txt`
2. Displays "Press space to start"
3. Initializes recording index `1` and empty log

### Keyboard Controls

| Key | Action |
|-----|--------|
| **Space** | **Toggle recording state** – starts chunk and displays current word; or accepts current word and stops chunk |
| **Right Arrow** | **Accept current word** and advance to next (continue within same chunk) |
| **Left Arrow** | **Mark error** and keep same word for re-pronunciation |

### Recommended Workflow

1. Press `Space` to start a new chunk
2. Pronounce the displayed word naturally
3. If pronunciation is good, press `Right Arrow` to continue
4. If pronunciation is wrong, press `Left Arrow`, repeat, then press `Right Arrow`
5. To close and save the current chunk, press `Space` on a displayed word
6. Save the chunk WAV file with the prompted name, then continue

### End of List Behavior

When the final item is accepted:

1. Screen shows "All words completed"
2. Helper displays the final WAV name and target log filename
3. Log receives a `COMPLETE` event

### WAV Naming Convention

The helper enforces:

    <prefix>_NNN.wav

For output stem `phoneprep`, expected names are:

- `phoneprep_001.wav`
- `phoneprep_002.wav`
- etc.

### Log Export

Use the **`Copy Log`** button, then save as:

    <prefix>_segmanifest.txt

This event log is required for the next segmentation step.

---

## Step 3: Segment WAV Files with akkapros Segmenter (Planned)

**Current status:** The `akkapros` segmenter is not yet released.

### Intended Inputs for Segmenter

| Input | Source |
|-------|--------|
| WAV chunk files | `<prefix>_NNN.wav` from recording |
| Event log | `<prefix>_segmanifest.txt` from HTML helper |
| Sidecars | `*_manifest.tsv`, `*_diphones.tsv`, `*_words.txt` from `phoneprep.py` |

### Intended Outputs from Segmenter

- Time-aligned diphone or phoneme segments
- MBROLATOR-ready dataset tables
- Manifest linking each segment to utterance and diphone index

---

## Step 4: Build the MBROLA Voice with MBROLATOR

After the segmentation dataset is ready:

1. **Feed dataset** into MBROLATOR
2. **Run MBROLATOR build** procedure
3. **Validate** output voice on held-out test words
4. **Iterate** recording or segmentation fixes if needed

---

## 📁 Suggested Project Folder Convention

    session/
      phoneprep.txt
      phoneprep_manifest.tsv
      phoneprep_diphones.tsv
      phoneprep_words.txt
      phoneprep_recording_helper.html
      phoneprep_segmanifest.txt
      phoneprep_001.wav
      phoneprep_002.wav
      ...
      segmenter_output/
      mbrolator_dataset/

---

## 📝 Important Notes

1. **Keep logs and WAV files together** for reproducible segmentation
2. **Do not rename sidecars after recording** – downstream matching expects consistency
3. **Multiple recording sessions** – preserve continuous file numbering or keep per-session folders
4. For deeper generator internals, see `docs/akkapros/phoneprep.md`

---

## ✅ Summary

This pipeline transforms linguistic knowledge into a working speech synthesis voice:

| Stage | Tool | Output |
|-------|------|--------|
| 1. Generate | `phoneprep.py` | Recording script + sidecars + HTML helper |
| 2. Record | HTML helper | WAV chunks + event log |
| 3. Segment | (planned) | Aligned segments |
| 4. Compile | MBROLATOR | MBROLA voice |

The current implementation covers stages 1–2 completely, with clear handoff points for future tooling.