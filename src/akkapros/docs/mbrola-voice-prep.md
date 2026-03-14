# How to create an MBROLA voice for Akkadian

This guide explains the practical pipeline currently implemented in `akkapros`,
plus the handoff points for tools outside this repository.

## Goal

Build an Akkadian MBROLA voice using:

1. `phoneprep.py` to generate recording prompts and machine sidecars.
2. The generated HTML assistant to record and log utterance timing/events.
3. The `akkapros` segmenter (planned, not yet released) to segment WAV chunks.
4. MBROLATOR to compile the resulting diphone dataset into an MBROLA voice.

## Step 1: Generate recording materials with phoneprep

Run:

```bash
python src/akkapros/cli/phoneprep.py \
  --coverage 3 \
  --with-html-recording-helper \
  --seed 100 \
  --output demo/akkapros/phoneprep/results/phoneprep.txt
```

Or use demo launcher:

- `demo/akkapros/phoneprep/phoneprep-demo.ps1`
- `demo/akkapros/phoneprep/phoneprep-demo.sh`

Expected outputs:

1. `phoneprep.txt`
	- Human recording script (`_..._` utterances, syllable dots).
2. `phoneprep_manifest.tsv`
	- One row per utterance, MBROLA symbols, full diphone list.
3. `phoneprep_diphones.tsv`
	- One row per diphone cursor position.
4. `phoneprep_words.txt`
	- One MBROLA-symbol utterance per line.
5. `phoneprep_recording_helper.html`
	- Interactive recording controller with event logging.

If you do not want sidecars, pass `--no-sidecars`.

## Why this word list works

`phoneprep.py` does not output arbitrary words. It uses a legality-aware,
coverage-driven generator:

1. Enforces Akkadian-oriented phonotactic constraints.
2. Covers boundary and internal diphone transitions.
3. Tries to reach configured diphone coverage with minimal utterance count.

Main pattern templates:

1. `_ V C C V C C V _` -> `VC.CVC.CV`
2. `_ C V C V C C V C _` -> `CV.CVC.CVC`
3. `_ C V V C V V C _` -> `CVV.CVVC`

Key legality rule in current implementation:

- Colored vowels are post-emphatic only (licensed after `q`, `ṣ`, `ṭ`).

## Step 2: Record with the HTML helper and export logs

Open `phoneprep_recording_helper.html` in a browser.

### What happens when it starts

1. It loads utterance lines from `phoneprep.txt`.
2. It shows `Press space to start`.
3. It initializes recording index `1` and empty log.

### Keyboard behavior

1. `Space`
	- Not recording: starts a chunk and displays current word.
	- Recording + no word visible: displays current word.
	- Recording + word visible: accept current word and stop current chunk.

2. `Right Arrow`
	- Accept current word and advance to next word without stopping chunk.

3. `Left Arrow`
	- Mark error and keep same word for re-pronunciation.

### Recommended user behavior during recording

1. Press `Space` to start chunk.
2. Pronounce the displayed word naturally.
3. If pronunciation is good, press `Right Arrow` to continue.
4. If pronunciation is wrong, press `Left Arrow`, repeat, then press `Right Arrow`.
5. When you want to close/save the current chunk, press `Space` on a displayed word.
6. Save the chunk WAV file with prompted name, then continue.

### End of list behavior

When final item is accepted:

1. Screen shows `All words completed`.
2. Helper tells you final WAV name and target log filename.
3. Log receives a `COMPLETE` event.

### WAV naming convention

Helper enforces:

`<prefix>_NNN.wav`

For output stem `phoneprep`, expected names are:

- `phoneprep_001.wav`
- `phoneprep_002.wav`
- ...

### Log export

Use `Copy Log`, then save as:

`<prefix>_segmanifest.txt`

This event log is required for the next segmentation step.

## Step 3: Segment WAV files with akkapros segmenter (planned)

Current status: the `akkapros` segmenter is not yet released.

Intended input set for segmenter:

1. WAV chunk files (`<prefix>_NNN.wav`).
2. Event log (`<prefix>_segmanifest.txt`).
3. Sidecars from `phoneprep.py` (`*_manifest.tsv`, `*_diphones.tsv`, `*_words.txt`).

Intended segmenter output:

1. Time-aligned diphone or phoneme segments.
2. MBROLATOR-ready dataset tables.
3. Manifest linking each segment to utterance and diphone index.

## Step 4: Build the MBROLA voice with MBROLATOR

After segmentation dataset is ready:

1. Feed dataset into MBROLATOR.
2. Run MBROLATOR build procedure.
3. Validate output voice on held-out test words.
4. Iterate recording or segmentation fixes if needed.

## Suggested project folder convention

Example layout:

```text
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
```

## Notes

1. Keep logs and WAV files together for reproducible segmentation.
2. Do not rename sidecars after recording; downstream matching expects consistency.
3. If using multiple recording days, preserve continuous file numbering or keep per-session folders.
4. For deeper generator internals, see `docs/akkapros/phoneprep.md`.
