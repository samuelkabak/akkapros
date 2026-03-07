param(
    [switch]$Revert,
    [switch]$CheckOnly,
    [string]$MbrolatorRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-GitApplyProbe {
    param(
        [string]$Repo,
        [string[]]$Args
    )

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & git -C $Repo @Args 1>$null 2>$null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

$mbrolatorRootResolved = $null

if ($MbrolatorRoot) {
    if (-not (Test-Path $MbrolatorRoot)) {
        throw "MBROLATOR root path does not exist: $MbrolatorRoot"
    }
    $mbrolatorRootResolved = (Resolve-Path $MbrolatorRoot).Path
} else {
    $cwd = (Get-Location).Path
    $mbrolatorRootResolved = (& git -C $cwd rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not detect MBROLATOR root from current directory. cd into MBROLATOR root or pass -MbrolatorRoot <path>."
    }
    $mbrolatorRootResolved = $mbrolatorRootResolved.Trim()
}

if ((Split-Path -Leaf $mbrolatorRootResolved) -ne "MBROLATOR") {
    throw "Target repository is not MBROLATOR: $mbrolatorRootResolved"
}

$patches = @(
    (Join-Path $PSScriptRoot "mbrolator\0001-resynthesis-src-resynth-windows-drand48.patch")
)

$patchMarkers = @{
    "0001-resynthesis-src-resynth-windows-drand48.patch" = @{
        File = "Resynthesis/Src/resynth.c"
        Marker = "mbr_drand48"
    }
}

foreach ($patch in $patches) {
    if (-not (Test-Path $patch)) {
        throw "Patch not found: $patch"
    }

    $patchToApply = $patch
    $temporaryPatch = $null

    $lines = Get-Content -Path $patch
    $diffStart = ($lines | Select-String -Pattern '^diff --git ' | Select-Object -First 1)
    if (-not $diffStart) {
        throw "No unified diff found in patch file: $patch"
    }
    if ($diffStart.LineNumber -gt 1) {
        $temporaryPatch = [System.IO.Path]::GetTempFileName()
        $lines[($diffStart.LineNumber - 1)..($lines.Length - 1)] | Set-Content -Path $temporaryPatch -Encoding UTF8
        $patchToApply = $temporaryPatch
    }

    $modeLabel = if ($Revert) { "revert" } else { "apply" }
    Write-Host "[patch-stack] Checking $modeLabel for: $patch"

    $canApply = $false
    $alreadyInTargetState = $false
    $patchLeaf = Split-Path -Leaf $patch
    $markerInfo = $patchMarkers[$patchLeaf]

    if ($Revert) {
        if ((Invoke-GitApplyProbe -Repo $mbrolatorRootResolved -Args @("apply", "--check", "-R", $patchToApply)) -eq 0) {
            $canApply = $true
        } else {
            if ($markerInfo) {
                $markerFile = Join-Path $mbrolatorRootResolved $markerInfo.File
                $markerPattern = [regex]::Escape($markerInfo.Marker)
                $hasMarker = (Test-Path $markerFile) -and (Select-String -Path $markerFile -Pattern $markerPattern -Quiet)
                if (-not $hasMarker) {
                    $alreadyInTargetState = $true
                } else {
                    if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
                    throw "Patch check failed for: $patch"
                }
            } elseif ((Invoke-GitApplyProbe -Repo $mbrolatorRootResolved -Args @("apply", "--check", $patchToApply)) -eq 0) {
                $alreadyInTargetState = $true
            } else {
                if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
                throw "Patch check failed for: $patch"
            }
        }
    } else {
        if ((Invoke-GitApplyProbe -Repo $mbrolatorRootResolved -Args @("apply", "--check", $patchToApply)) -eq 0) {
            $canApply = $true
        } else {
            if ($markerInfo) {
                $markerFile = Join-Path $mbrolatorRootResolved $markerInfo.File
                $markerPattern = [regex]::Escape($markerInfo.Marker)
                $hasMarker = (Test-Path $markerFile) -and (Select-String -Path $markerFile -Pattern $markerPattern -Quiet)
                if ($hasMarker) {
                    $alreadyInTargetState = $true
                } else {
                    if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
                    throw "Patch check failed for: $patch"
                }
            } elseif ((Invoke-GitApplyProbe -Repo $mbrolatorRootResolved -Args @("apply", "--check", "-R", $patchToApply)) -eq 0) {
                $alreadyInTargetState = $true
            } else {
                if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
                throw "Patch check failed for: $patch"
            }
        }
    }

    if ($alreadyInTargetState) {
        $stateLabel = if ($Revert) { "already reverted" } else { "already applied" }
        Write-Host "[patch-stack] Skipping: $stateLabel for $patch"
        if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
        continue
    }

    if ($CheckOnly) {
        if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
        continue
    }

    if (-not $canApply) {
        throw "Patch cannot be processed for: $patch"
    }

    Write-Host "[patch-stack] Executing $modeLabel for: $patch"
    if ($Revert) {
        & git -C $mbrolatorRootResolved apply -R $patchToApply
    } else {
        & git -C $mbrolatorRootResolved apply $patchToApply
    }

    if ($LASTEXITCODE -ne 0) {
        if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
        throw "Patch operation failed for: $patch"
    }

    if ($temporaryPatch -and (Test-Path $temporaryPatch)) { Remove-Item $temporaryPatch -Force }
}

Write-Host "[patch-stack] Done."
