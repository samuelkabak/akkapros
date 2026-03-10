# Ensure Unicode (UTF-8) output in PowerShell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::UTF8
chcp 65001 | Out-Null

$repoRoot = Resolve-Path "$PSScriptRoot\..\.."
$resultsDir = Join-Path $repoRoot 'demo\akkatts\results'
if (Test-Path $resultsDir) {
	Write-Output "Clearing existing results in $resultsDir"
	Get-ChildItem -Path $resultsDir -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
} else {
	New-Item -ItemType Directory -Path $resultsDir | Out-Null
}

Write-Output "Running phoneprep.py..."
python "$repoRoot\src\akkatts\cli\phoneprep.py" --coverage 3 --with-html-recording-helper --seed 100 --output "$resultsDir\phoneprep.txt"
Write-Output "Demo complete."
