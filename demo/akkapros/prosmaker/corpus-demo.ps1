# Ensure Unicode (UTF-8) output in PowerShell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::UTF8
chcp 65001 | Out-Null

# PowerShell demo script for Akkapros corpus pipeline (moved into prosmaker/)
$repoRoot = Resolve-Path "$PSScriptRoot\..\..\.."
$configFile = 'demo/akkapros/prosmaker/corpus-demo.yaml'
$resultsDir = Join-Path $repoRoot 'demo\akkapros\prosmaker\results'

Push-Location $repoRoot
try {
  if (Test-Path $resultsDir) {
    Get-ChildItem -Path $resultsDir -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  } else {
    New-Item -ItemType Directory -Path $resultsDir | Out-Null
  }
  $sampleFiles = @(
    'data/samples/L_I.2_Poem_of_Creation_SB_II.atf',
    'data/samples/L_I.2_Poem_of_Creation_SB_IV.atf',
    'data/samples/L_I.2_Poem_of_Creation_SB_VI.atf',
    'data/samples/L_I.2_Poem_of_Creation_SB_VII.atf',
    'data/samples/L_I.5_Erra_and_Isum_SB_I.atf',
    'data/samples/L_III.3_Marduks_Address_to_the_Demons_SB.atf'
  )
  foreach ($f in $sampleFiles) {
    python 'src/akkapros/cli/atfparser.py' $f --conf $configFile
  }
  python 'src/akkapros/cli/syllabifier.py' 'demo/akkapros/prosmaker/results/corpus_proc.txt' --conf $configFile

  python 'src/akkapros/cli/prosmaker.py' 'demo/akkapros/prosmaker/results/corpus_syl.txt' --conf $configFile -p corpus-lob --style lob
  python 'src/akkapros/cli/prosmaker.py' 'demo/akkapros/prosmaker/results/corpus_syl.txt' --conf $configFile -p corpus-mono-lob --style lob --mora-mode mono
  python 'src/akkapros/cli/prosmaker.py' 'demo/akkapros/prosmaker/results/corpus_syl.txt' --conf $configFile -p corpus-sob --style sob

  python 'src/akkapros/cli/phonetizer.py' 'demo/akkapros/prosmaker/results/corpus-lob_tilde.txt' --conf $configFile -p corpus-lob
  python 'src/akkapros/cli/phonetizer.py' 'demo/akkapros/prosmaker/results/corpus-mono-lob_tilde.txt' --conf $configFile -p corpus-mono-lob
  python 'src/akkapros/cli/phonetizer.py' 'demo/akkapros/prosmaker/results/corpus-sob_tilde.txt' --conf $configFile -p corpus-sob

  python 'src/akkapros/cli/metricalc.py' 'demo/akkapros/prosmaker/results/corpus-lob_phone.txt' --conf $configFile -p corpus-lob
  python 'src/akkapros/cli/metricalc.py' 'demo/akkapros/prosmaker/results/corpus-mono-lob_phone.txt' --conf $configFile -p corpus-mono-lob
  python 'src/akkapros/cli/metricalc.py' 'demo/akkapros/prosmaker/results/corpus-sob_phone.txt' --conf $configFile -p corpus-sob

  python 'src/akkapros/cli/printer.py' 'demo/akkapros/prosmaker/results/corpus-lob_phone.txt' --conf $configFile -p corpus-lob
  python 'src/akkapros/cli/printer.py' 'demo/akkapros/prosmaker/results/corpus-mono-lob_phone.txt' --conf $configFile -p corpus-mono-lob
  python 'src/akkapros/cli/printer.py' 'demo/akkapros/prosmaker/results/corpus-sob_phone.txt' --conf $configFile -p corpus-sob

  python 'src/akkapros/cli/fullprosmaker.py' --test-all
}
finally {
  Pop-Location
}
