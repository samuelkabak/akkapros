# Ensure Unicode (UTF-8) output in PowerShell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::UTF8
chcp 65001 | Out-Null
#[Unicode/UTF-8 output setup]
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::UTF8
chcp 65001 | Out-Null
# PowerShell demo script for Akkapros corpus pipeline
echo "Running syllabifier..."
echo "Running repairer (LOB)..."
echo "Running repairer (SOB)..."
echo "Running metrics (LOB, pause ratios 30/35/40)..."
echo "Running metrics (SOB, pause ratios 30/35/40)..."
echo "Running printer (LOB)..."
echo "Running printer (SOB)..."
echo "Running fullreparer --test-all..."
echo "Demo pipeline complete."
Write-Output "Parsing ATF samples with --append..."
$repoRoot = Resolve-Path "$PSScriptRoot\..\.."
$resultsDir = Join-Path $repoRoot 'demo\akkapros\results'
if (Test-Path $resultsDir) {
  Write-Output "Clearing existing results in $resultsDir"
  Get-ChildItem -Path $resultsDir -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
} else {
  New-Item -ItemType Directory -Path $resultsDir | Out-Null
}
$sampleFiles = @(
  (Join-Path $repoRoot 'data\samples\L_I.5_Erra_and_Isum_SB_I.atf'),
  (Join-Path $repoRoot 'data\samples\L_III.3_Marduks_Address_to_the_Demons_SB.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_II.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_IV.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_VI.atf'),
  (Join-Path $repoRoot 'data\samples\L_I.2_Poem_of_Creation_SB_VII.atf')
)
foreach ($f in $sampleFiles) {
  python "$repoRoot\src\akkapros\cli\atfparser.py" "$f" --append -p corpus --outdir "$resultsDir"
}
Write-Output "Running syllabifier..."
python "$repoRoot\src\akkapros\cli\syllabifier.py" "$resultsDir\corpus_proc.txt" -p corpus --outdir "$resultsDir"

Write-Output "Running repairer (LOB)..."
python "$repoRoot\src\akkapros\cli\repairer.py" "$resultsDir\corpus_syl.txt" -p corpus-lob --outdir "$resultsDir" --style lob

Write-Output "Running repairer (SOB)..."
python "$repoRoot\src\akkapros\cli\repairer.py" "$resultsDir\corpus_syl.txt" -p corpus-sob --outdir "$resultsDir" --style sob

Write-Output "Running metrics (LOB, pause ratios 30/35/40)..."
python "$repoRoot\src\akkapros\cli\metricser.py" "$resultsDir\corpus-lob_tilde.txt" --table --json --csv --pause-ratio 30 -p corpus-lob-p30 --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\metricser.py" "$resultsDir\corpus-lob_tilde.txt" --table --json --csv --pause-ratio 35 -p corpus-lob-p35 --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\metricser.py" "$resultsDir\corpus-lob_tilde.txt" --table --json --csv --pause-ratio 40 -p corpus-lob-p40 --outdir "$resultsDir"

Write-Output "Running metrics (SOB, pause ratios 30/35/40)..."
python "$repoRoot\src\akkapros\cli\metricser.py" "$resultsDir\corpus-sob_tilde.txt" --table --json --csv --pause-ratio 30 -p corpus-sob-p30 --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\metricser.py" "$resultsDir\corpus-sob_tilde.txt" --table --json --csv --pause-ratio 35 -p corpus-sob-p35 --outdir "$resultsDir"
python "$repoRoot\src\akkapros\cli\metricser.py" "$resultsDir\corpus-sob_tilde.txt" --table --json --pause-ratio 40 -p corpus-sob-p40 --outdir "$resultsDir"

Write-Output "Running printer (LOB)..."
python "$repoRoot\src\akkapros\cli\printer.py" -p corpus-lob --outdir "$resultsDir" --acute --bold --ipa "$resultsDir\corpus-lob_tilde.txt"

Write-Output "Running printer (SOB)..."
python "$repoRoot\src\akkapros\cli\printer.py" -p corpus-sob --outdir "$resultsDir" --acute --bold --ipa "$resultsDir\corpus-sob_tilde.txt"

Write-Output "Running fullreparer --test-all..."
python "$repoRoot\src\akkapros\cli\fullreparer.py" --test-all 
Write-Output "Demo pipeline complete."
