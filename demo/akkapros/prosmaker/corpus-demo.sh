#!/bin/bash
cd "$(dirname "$0")/../.."
export PYTHONPATH="$PWD/src"
set -e
resultsDir="demo/akkapros/prosmaker/results"
corpusBase="$resultsDir/corpus"
if [ -d "$resultsDir" ]; then
  rm -rf "$resultsDir"/* "$resultsDir"/.[!.]* "$resultsDir"/?* 2>/dev/null || true
else
  mkdir -p "$resultsDir"
fi
sampleFiles=(
  "data/samples/L_I.2_Poem_of_Creation_SB_II.atf"
  "data/samples/L_I.2_Poem_of_Creation_SB_IV.atf"
  "data/samples/L_I.2_Poem_of_Creation_SB_VI.atf"
  "data/samples/L_I.2_Poem_of_Creation_SB_VII.atf"
  "data/samples/L_I.5_Erra_and_Isum_SB_I.atf"
  "data/samples/L_III.3_Marduks_Address_to_the_Demons_SB.atf"
)
for f in "${sampleFiles[@]}"; do
  python src/akkapros/cli/atfparser.py "$f" --append -p corpus --outdir "$resultsDir"
done
python src/akkapros/cli/syllabifier.py "$corpusBase"_proc.txt -p corpus --outdir "$resultsDir"
python src/akkapros/cli/prosmaker.py "$corpusBase"_syl.txt -p corpus-lob --outdir "$resultsDir" --style lob
python src/akkapros/cli/prosmaker.py "$corpusBase"_syl.txt -p corpus-sob --outdir "$resultsDir" --style sob
python src/akkapros/cli/metricalc.py "$resultsDir/corpus-lob_tilde.txt" --table --json --pause-ratio 30 -p corpus-lob-p30 --outdir "$resultsDir"
python src/akkapros/cli/metricalc.py "$resultsDir/corpus-lob_tilde.txt" --table --json --pause-ratio 35 -p corpus-lob-p35 --outdir "$resultsDir"
python src/akkapros/cli/metricalc.py "$resultsDir/corpus-lob_tilde.txt" --table --json --pause-ratio 40 -p corpus-lob-p40 --outdir "$resultsDir"
python src/akkapros/cli/metricalc.py "$resultsDir/corpus-sob_tilde.txt" --table --json --pause-ratio 30 -p corpus-sob-p30 --outdir "$resultsDir"
python src/akkapros/cli/metricalc.py "$resultsDir/corpus-sob_tilde.txt" --table --json --pause-ratio 35 -p corpus-sob-p35 --outdir "$resultsDir"
python src/akkapros/cli/metricalc.py "$resultsDir/corpus-sob_tilde.txt" --table --json --pause-ratio 40 -p corpus-sob-p40 --outdir "$resultsDir"
python src/akkapros/cli/printer.py -p corpus-lob --outdir "$resultsDir" --acute --bold --ipa "$resultsDir/corpus-lob_tilde.txt"
python src/akkapros/cli/printer.py -p corpus-sob --outdir "$resultsDir" --acute --bold --ipa "$resultsDir/corpus-sob_tilde.txt"
python src/akkapros/cli/fullprosmaker.py --test-all
