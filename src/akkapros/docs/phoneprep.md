# Phoneprep CLI (`phoneprep.py`)

This page documents the current implementation in `src/akkapros/cli/phoneprep.py`.

## Purpose

`phoneprep.py` generates a recording script that is optimized for diphone coverage,
plus machine-readable sidecars for downstream segmentation and MBROLA dataset prep.

Core goals:

1. Cover legal Akkadian diphone transitions with minimal recording burden.
2. Keep pronunciation prompts human-readable (IPA-like display script).
3. Emit deterministic sidecars for automatic alignment/segmentation tooling.
4. Optionally generate an interactive HTML recording assistant.

## Quick Start

PowerShell:

```powershell
python src/akkapros/cli/phoneprep.py \
  --coverage 3 \
  --with-html-recording-helper \
  --seed 100 \
  --output demo/akkapros/phoneprep/results/phoneprep.txt
```

POSIX shell:

```bash
python src/akkapros/cli/phoneprep.py \
  --coverage 3 \
  --with-html-recording-helper \
  --seed 100 \
  --output demo/akkapros/phoneprep/results/phoneprep.txt
```

Also see demo launchers:

- `demo/akkapros/phoneprep/phoneprep-demo.ps1`
- `demo/akkapros/phoneprep/phoneprep-demo.sh`

## Generated Files

If output is `.../phoneprep.txt`, the CLI writes:

1. `phoneprep.txt`
  - Human recording script.
  - Each utterance line is wrapped with `_..._`.
  - Dots mark syllable boundaries.
  - Sections are grouped by pattern class.

2. `phoneprep_manifest.tsv` (unless `--no-sidecars`)
  - One row per utterance.
  - MBROLA-side symbols, diphone list per utterance, pattern id, batch tag.
  - Intended as the main machine manifest for later segmentation/alignment.

3. `phoneprep_diphones.tsv` (unless `--no-sidecars`)
  - One row per diphone cursor position.
  - Useful when aligning segment timelines to diphone sequence index.

4. `phoneprep_words.txt` (unless `--no-sidecars`)
  - One MBROLA-symbol utterance per line.
  - Compact line-oriented input for downstream tools.

5. `phoneprep_recording_helper.html` (when `--with-html-recording-helper`)
  - Interactive page to guide chunk recording and produce timestamped logs.

## CLI Options

Coverage and optimization:

- `--coverage`, `-c` : target per-diphone coverage (`1..4`, default `3`).
- `--max-non-vv` : non-VV target count (`1..3`).
- `--non-vv-target-ratio` : soft completion ratio for non-VV targets (default `0.8`).
- `--strict-max-non-vv` : hard cap mode for non-VV counts.
- `--max-iterations` : stochastic optimizer sample budget.
- `--candidate-pool-size` : random candidates scored per selection round.
- `--seed` : reproducible random seed.

Batching and outputs:

- `--two-batch-emphatic` : build two recording batches (plain-first, then mixed).
- `--output`, `-o` : output script path (default `outputs/akkadian_script.txt`).
- `--no-sidecars` : skip manifest/diphone/word sidecars.

Recording helper:

- `--with-html-recording-helper` : create helper HTML next to script file.
- `--recording-max-words` : max accepted words per recording chunk (default `1000`).

Inventory override/debug:

- `--debug-reduced-set`
- `--plain-consonants`
- `--emphatic-consonants`
- `--plain-vowels-short`
- `--plain-vowels-long`
- `--colored-vowels-short`
- `--colored-vowels-long`

Testing:

- `--test` : run self-tests and exit.

## How Word Lists Are Created

### 1. Inventory model

The script defines:

- Plain consonants and emphatic consonants.
- Plain vowels and colored vowels.
- Boundary symbol `#` for word edges.

Long vowels are folded to doubled short-vowel behavior for generation logic.

### 2. Phonotactic legality

Important constraints enforced during generation:

1. Post-emphatic coloring rule:
  - Colored vowels are legal only after emphatic consonants (`q ṣ ṭ`).
  - Word-initial vowels must be plain.
2. In V-V sequences, both vowels must be from the same class (plain/plain or colored/colored).

### 3. Word shape patterns

Generator samples legal words across three templates:

1. Pattern 1: `_ V C C V C C V _` (displayed as `VC.CVC.CV`)
2. Pattern 2: `_ C V C V C C V C _` (displayed as `CV.CVC.CVC`)
3. Pattern 3: `_ C V V C V V C _` (displayed as `CVV.CVVC`)

Rationale: these templates expose diverse boundary and internal diphone contexts,
including C-C, C-V, V-C, V-V and boundary transitions.

### 4. Coverage optimizer

`phoneprep.py` uses a stochastic greedy selector:

1. Compute reachable diphone inventory under legality constraints.
2. Repeatedly sample candidate words.
3. Score candidates by how much they improve under-covered diphones.
4. Stop when target criteria are met (or sample budget is exhausted).

Rationale: maximize coverage while keeping the final list compact.

### 5. Symbol mapping for sidecars

Output script is human-oriented (IPA-like), while sidecars are machine-oriented:

- Human script uses IPA-mapped symbols.
- Sidecars use MBROLA/X-SAMPA-like symbols for segmenter/MBROLATOR pipeline steps.

## Pronunciation Expectations For Recording

The generated script includes recorder guidance:

1. Speak each line naturally.
2. Pause ~1 second before and after each word.
3. Record at 16 kHz, 16-bit, mono.

Line format notes:

- `_..._` wraps one utterance.
- `.` marks syllable boundaries to help consistent articulation.
- Read the whole displayed line as one item.

## Recording Helper HTML: Behavior And Logic

When `--with-html-recording-helper` is enabled, an HTML page is generated.

### On page load

1. Word list is loaded from utterance lines in `phoneprep.txt`.
2. UI starts with `Press space to start`.
3. Log area is empty.
4. Recording index starts at `1`.

### Keyboard controls

1. `Space`
  - If not recording: starts a recording chunk and shows current word.
  - If recording and no word currently displayed: displays current word.
  - If recording and a word is displayed: accepts that word, stops current chunk, and prepares next chunk.

2. `Right Arrow`
  - Accept current word and move to next word without stopping current chunk.
  - Use this when pronunciation is correct and you want to continue within same WAV file.

3. `Left Arrow`
  - Mark pronunciation error and repeat same word.
  - Word index does not advance.

### Practical operator workflow

Recommended flow:

1. Press `Space` to start chunk and show first word.
2. Pronounce the displayed word.
3. If good, press `Right Arrow` to advance.
4. If mistake, press `Left Arrow`, re-pronounce same word, then `Right Arrow` when correct.
5. When you want to stop/save this chunk, press `Space` while a word is displayed.
6. Save audio as prompted filename, then press `Space` to start next chunk.

### End of word list

When all words are completed:

1. Display changes to `All words completed`.
2. Hint tells you final WAV filename and log filename to save.
3. A `COMPLETE` event is appended to log.

### WAV naming convention

WAV chunk names are:

`<prefix>_NNN.wav`

Where:

- `<prefix>` is the output script stem (for `phoneprep.txt`, prefix is `phoneprep`).
- `NNN` is zero-padded recording index (`001`, `002`, ...).

### Log format and export

The helper writes tab-separated event rows in the textarea. Fields include:

- ISO timestamp
- elapsed clock time
- recording index
- WAV filename
- current word index
- accepted count in current chunk
- error count on current word
- event name
- displayed word
- optional metadata

Events include: `DISPLAY`, `RECORDING_START`, `ACCEPT`, `ERROR_REPEAT`, `RECORDING_STOP`, `COMPLETE`.

Use `Copy Log` to copy all rows, then save to:

`<prefix>_segmanifest.txt`

This log is intended for downstream automatic segmentation.

## Two-Batch Mode

`--two-batch-emphatic` creates:

1. Batch 1: plain consonants + plain vowels only.
2. Batch 2: mixed consonants and mixed vowels under post-emphatic legality.

Manifest rows include batch labels so downstream tools can preserve batch provenance.

## Where This Fits In The MBROLA Workflow

Use this doc together with:

- `docs/akkapros/mbrola-voice-prep.md`

Pipeline summary:

1. Generate script + sidecars + HTML with `phoneprep.py`.
2. Record WAV chunks with helper page and save exported event log.
3. Feed WAV + log + sidecars to segmenter (when released) to build MBROLATOR dataset.
4. Run MBROLATOR to build the MBROLA voice.
