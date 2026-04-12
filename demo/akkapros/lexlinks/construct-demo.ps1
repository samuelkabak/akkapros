# Ensure Unicode (UTF-8) output in PowerShell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::UTF8
chcp 65001 | Out-Null

$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path "$PSScriptRoot\..\..\.."
$configFile = 'demo/akkapros/lexlinks/construct-demo.yaml'
$inputFile = 'data/lexlinks/construct_prep/erra_construct_proc.txt'
$resultsDir = Join-Path $repoRoot 'demo\akkapros\lexlinks\results'
$venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'

Push-Location $repoRoot
try {
  if (Test-Path $resultsDir) {
    Get-ChildItem -Path $resultsDir -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  } else {
    New-Item -ItemType Directory -Path $resultsDir | Out-Null
  }

  if (Test-Path $venvPython) {
    & $venvPython 'src/akkapros/cli/fullprosmaker.py' $inputFile --conf $configFile
  } elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python 'src/akkapros/cli/fullprosmaker.py' $inputFile --conf $configFile
  } elseif (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 'src/akkapros/cli/fullprosmaker.py' $inputFile --conf $configFile
  } else {
    throw 'No usable Python interpreter found. Expected .venv\Scripts\python.exe, python, or py.'
  }
}
finally {
  Pop-Location
}