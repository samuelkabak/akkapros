# Demo: prepare phone dataset using akktts phoneprep
# Assumes a Python venv is active with this repo installed (editable)

$in = "data/samples/sample_input.txt"   # adjust or point to data/samples/*.txt
$out = "demo/akkatts/results"

mkdir -Force $out | Out-Null

# Run phoneprep via module entry point
python -m akktts.cli.phoneprep --infile $in --outdir $out --format mbrola

Write-Host "Phoneprep demo complete — outputs in" $out
