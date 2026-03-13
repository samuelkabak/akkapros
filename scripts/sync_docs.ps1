# Copy CLI docs from repo docs/akkapros into package docs
$src = "docs/akkapros"
$dst = "src/akkapros/docs"
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }
Get-ChildItem -Path $src -Filter *.md -File | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $dst -Force
}
Write-Host "Synced docs from $src to $dst"