# Demo: prepare phone dataset using akkapros phoneprep
# Assumes a Python venv is active with this repo installed (editable)

$in = "data/samples/sample_input.txt"   # adjust or point to data/samples/*.txt
$out = "demo/akkapros/phoneprep/results"

mkdir -Force $out | Out-Null

# Run phoneprep via module entry point
python -m akkapros.cli.phoneprep --coverage 3 --seed 100 --output "$out/phoneprep.txt"

Write-Host "Phoneprep demo complete — outputs in" $out
