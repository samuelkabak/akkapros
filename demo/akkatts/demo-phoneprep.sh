#!/bin/bash
cd "$(dirname "$0")/../.."
export PYTHONPATH="$PWD/src"
set -e
resultsDir="demo/akkatts/results"
if [ ! -d "$resultsDir" ]; then
  mkdir -p "$resultsDir"
fi
echo "Running phoneprep.py..."
python src/akkatts/cli/phoneprep.py --coverage 3 --with-html-recording-helper --seed 100 --output "$resultsDir/phoneprep.txt"
echo "Demo complete."
