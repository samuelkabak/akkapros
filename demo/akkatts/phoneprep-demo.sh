#!/usr/bin/env bash
# Demo: prepare phone dataset using akktts phoneprep
# Assumes a Python venv is active with this repo installed (editable)

IN=data/samples/sample_input.txt
OUT=demo/akkatts/results
mkdir -p "$OUT"
python -m akktts.cli.phoneprep --infile "$IN" --outdir "$OUT" --format mbrola

echo "Phoneprep demo complete — outputs in $OUT"
