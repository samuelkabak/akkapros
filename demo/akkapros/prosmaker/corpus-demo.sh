#!/bin/bash
cd "$(dirname "$0")/../../.."
export PYTHONPATH="$PWD/src"
set -e

if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v py >/dev/null 2>&1; then
  PYTHON_BIN="py -3"
elif [ -f ".venv/Scripts/python.exe" ]; then
  PYTHON_BIN=".venv/Scripts/python.exe"
else
  echo "No usable Python interpreter found. Expected python, python3, py, or .venv/Scripts/python.exe." >&2
  exit 1
fi

configFile="demo/akkapros/prosmaker/corpus-demo.yaml"
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
  eval "$PYTHON_BIN" src/akkapros/cli/atfparser.py "$f" --conf "$configFile"
done
eval "$PYTHON_BIN" src/akkapros/cli/syllabifier.py "$corpusBase"_proc.txt --conf "$configFile"
eval "$PYTHON_BIN" src/akkapros/cli/prosmaker.py "$corpusBase"_syl.txt --conf "$configFile" -p corpus-lob --style lob
eval "$PYTHON_BIN" src/akkapros/cli/prosmaker.py "$corpusBase"_syl.txt --conf "$configFile" -p corpus-mono-lob --style lob --mora-mode mono
eval "$PYTHON_BIN" src/akkapros/cli/prosmaker.py "$corpusBase"_syl.txt --conf "$configFile" -p corpus-sob --style sob
eval "$PYTHON_BIN" src/akkapros/cli/phonetizer.py "$resultsDir/corpus-lob_tilde.txt" --conf "$configFile" -p corpus-lob
eval "$PYTHON_BIN" src/akkapros/cli/phonetizer.py "$resultsDir/corpus-mono-lob_tilde.txt" --conf "$configFile" -p corpus-mono-lob
eval "$PYTHON_BIN" src/akkapros/cli/phonetizer.py "$resultsDir/corpus-sob_tilde.txt" --conf "$configFile" -p corpus-sob
eval "$PYTHON_BIN" src/akkapros/cli/metricalc.py "$resultsDir/corpus-lob_phone.txt" --conf "$configFile" -p corpus-lob
eval "$PYTHON_BIN" src/akkapros/cli/metricalc.py "$resultsDir/corpus-mono-lob_phone.txt" --conf "$configFile" -p corpus-mono-lob
eval "$PYTHON_BIN" src/akkapros/cli/metricalc.py "$resultsDir/corpus-sob_phone.txt" --conf "$configFile" -p corpus-sob
eval "$PYTHON_BIN" src/akkapros/cli/printer.py "$resultsDir/corpus-lob_phone.txt" --conf "$configFile" -p corpus-lob
eval "$PYTHON_BIN" src/akkapros/cli/printer.py "$resultsDir/corpus-mono-lob_phone.txt" --conf "$configFile" -p corpus-mono-lob
eval "$PYTHON_BIN" src/akkapros/cli/printer.py "$resultsDir/corpus-sob_phone.txt" --conf "$configFile" -p corpus-sob
eval "$PYTHON_BIN" src/akkapros/cli/fullprosmaker.py --test-all
