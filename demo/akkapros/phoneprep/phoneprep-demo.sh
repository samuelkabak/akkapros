#!/usr/bin/env bash
# Demo: prepare phone dataset using akkapros phoneprep
# Assumes a Python venv is active with this repo installed (editable)

IN=data/samples/sample_input.txt
OUT=demo/akkapros/phoneprep/results
mkdir -p "$OUT"
python -m akkapros.cli.phoneprep --coverage 3 --seed 100 --output "$OUT/phoneprep.txt"

echo "Phoneprep demo complete — outputs in $OUT"
