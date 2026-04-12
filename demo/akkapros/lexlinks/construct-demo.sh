#!/bin/bash
cd "$(dirname "$0")/../../.."
export PYTHONPATH="$PWD/src"
set -e

if [ -f ".venv/Scripts/python.exe" ]; then
  PYTHON_BIN=".venv/Scripts/python.exe"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v py >/dev/null 2>&1; then
  PYTHON_BIN="py -3"
else
  echo "No usable Python interpreter found. Expected .venv/Scripts/python.exe, python, python3, or py." >&2
  exit 1
fi

configFile="demo/akkapros/lexlinks/construct-demo.yaml"
inputFile="data/lexlinks/construct_prep/erra_construct_proc.txt"
resultsDir="demo/akkapros/lexlinks/results"

if [ -d "$resultsDir" ]; then
  rm -rf "$resultsDir"/* "$resultsDir"/.[!.]* "$resultsDir"/?* 2>/dev/null || true
else
  mkdir -p "$resultsDir"
fi

eval "$PYTHON_BIN" src/akkapros/cli/fullprosmaker.py "$inputFile" --conf "$configFile"