Phoneprep — akktts/phoneprep.py
================================

Overview
--------
`phoneprep.py` prepares orthographic input for phone-level processing and dataset
preparation used by `akkatts`. It normalizes input text, maps orthography to a
phoneme-friendly representation, and can emit MBROLA- or TTS-ready token lists.

Typical usage (demo): see `demo/akkatts/phoneprep-demo.ps1` or
`demo/akkapros/phoneprep-demo.sh`.

Inputs and outputs
- Input: raw text files (one utterance per line) from `data/samples/`.
- Output: prepared phone lists and manifests written under `demo/akkatts/results/`.

Options
- `--infile` : input text file
- `--outdir` : output directory
- `--format` : output format (mbrola, csv, manifest)

Notes
- `phoneprep.py` is intended to be run from the demo scripts for reproducible
  dataset preparation. For details on MBROLA dataset preparation see
  `docs/akkatts/mbrola-dataset-prep.md`.
