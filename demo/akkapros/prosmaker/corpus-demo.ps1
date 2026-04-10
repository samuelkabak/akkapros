# Ensure Unicode (UTF-8) output in PowerShell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::UTF8
chcp 65001 | Out-Null

# PowerShell demo script for Akkapros corpus pipeline (moved into prosmaker/)
$repoRoot = Resolve-Path "$PSScriptRoot\..\..\.."
$resultsDir = Join-Path $repoRoot 'demo\akkapros\prosmaker\results'
if (Test-Path $resultsDir) {
  Get-ChildItem -Path $resultsDir -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
} else {
  New-Item -ItemType Directory -Path $resultsDir | Out-Null
}
$sampleFiles = @(
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_II.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_IV.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_VI.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_VII.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.5_Erra_and_Isum_SB_I.atf'),
  (Join-Path $repoRoot 'data\samples\L_III.3_Marduks_Address_to_the_Demons_SB.atf')
)
foreach ($f in $sampleFiles) {
  python "$repoRoot\src\akkapros\cli\atfparser.py" "$f" --append -p corpus --outdir "$resultsDir"
}
python "$repoRoot\src\akkapros\cli\syllabifier.py" "$resultsDir\corpus_proc.txt" -p corpus --outdir "$resultsDir"

python "$repoRoot\src\akkapros\cli\prosmaker.py" "$resultsDir\corpus_syl.txt" -p corpus-lob --outdir "$resultsDir" --style lob

python "$repoRoot\src\akkapros\cli\prosmaker.py" "$resultsDir\corpus_syl.txt" -p corpus-mono-lob --outdir "$resultsDir" --style lob --mora-mode mono

python "$repoRoot\src\akkapros\cli\prosmaker.py" "$resultsDir\corpus_syl.txt" -p corpus-sob --outdir "$resultsDir" --style sob

python "$repoRoot\src\akkapros\cli\phonetizer.py" "$resultsDir\corpus-lob_tilde.txt" -p corpus-lob --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\phonetizer.py" "$resultsDir\corpus-mono-lob_tilde.txt" -p corpus-mono-lob --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\phonetizer.py" "$resultsDir\corpus-sob_tilde.txt" -p corpus-sob --outdir "$resultsDir"

python "$repoRoot\src\akkapros\cli\metricalc.py" "$resultsDir\corpus-lob_phone.txt" --table --json -p corpus-lob --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\metricalc.py" "$resultsDir\corpus-mono-lob_phone.txt" --table --json -p corpus-mono-lob --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\metricalc.py" "$resultsDir\corpus-sob_phone.txt" --table --json -p corpus-sob --outdir "$resultsDir"

python "$repoRoot\src\akkapros\cli\printer.py" -p corpus-lob --outdir "$resultsDir" --acute --bold --ipa --xar "$resultsDir\corpus-lob_tilde.txt"

python "$repoRoot\src\akkapros\cli\printer.py" -p corpus-mono-lob --outdir "$resultsDir" --acute --bold --ipa --xar "$resultsDir\corpus-mono-lob_tilde.txt"

python "$repoRoot\src\akkapros\cli\printer.py" -p corpus-sob --outdir "$resultsDir" --acute --bold --ipa --xar "$resultsDir\corpus-sob_tilde.txt"

python "$repoRoot\src\akkapros\cli\fullprosmaker.py" --test-all 
python "$repoRoot\src\akkapros\cli\fullprosmaker.py" --test-all 
