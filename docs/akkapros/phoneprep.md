Phoneprep — akkapros/cli/phoneprep.py
================================

Overview
--------
`phoneprep.py` prepares orthographic input for phone-level processing and dataset
preparation used by `akkapros`. It normalizes input text, maps orthography to a
phoneme-friendly representation, and can emit MBROLA- or TTS-ready token lists.

Typical usage (demo): see `demo/akkapros/phoneprep/phoneprep-demo.ps1` or
`demo/akkapros/phoneprep/phoneprep-demo.sh`.

Inputs and outputs
- Input: raw text files (one utterance per line) from `data/samples/`.
- Output: prepared phone lists and manifests written under `demo/akkapros/phoneprep/results/`.

Options
- `--infile` : input text file
- `--outdir` : output directory
- `--format` : output format (mbrola, csv, manifest)

Notes
- `phoneprep.py` is intended to be run from the demo scripts for reproducible
  dataset preparation. For details on MBROLA dataset preparation see
  `docs/akkapros/mbrola-dataset-prep.md`.
