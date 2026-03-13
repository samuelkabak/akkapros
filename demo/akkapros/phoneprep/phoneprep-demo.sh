#!/bin/bash
cd "$(dirname "$0")/../../.."
export PYTHONPATH="$PWD/src"
set -e
resultsDir="demo/akkapros/phoneprep/results"
if [ -d "$resultsDir" ]; then
  echo "Clearing existing results in $resultsDir"
  rm -rf "$resultsDir"/* "$resultsDir"/.[!.]* "$resultsDir"/?* 2>/dev/null || true
else
  mkdir -p "$resultsDir"
fi
echo "Running phoneprep.py..."
python src/akkapros/cli/phoneprep.py --coverage 3 --with-html-recording-helper --seed 100 --output "$resultsDir/phoneprep.txt"
echo "Demo complete."
