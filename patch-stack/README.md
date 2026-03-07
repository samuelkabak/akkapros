# Patch Stack

This directory stores local, upstream-independent patch files used by this project.

Goal:
- Keep third-party sources close to upstream.
- Avoid maintaining full forks when only small compatibility fixes are needed.
- Apply patches conditionally by platform/toolchain.

## Layout

- `mbrolator/`: patches targeting MBROLATOR sources.

Naming convention:
- `NNNN-<scope>-<short-purpose>.patch`
- Example: `0001-resynthesis-src-resynth-windows-drand48.patch`

## Current patches

1. `mbrolator/0001-resynthesis-src-resynth-windows-drand48.patch`

Purpose:
- Patch to circumvent `drand48` not available in Windows toolchains.

Apply when:
- Building MBROLATOR on Windows/MinGW/UCRT where `drand48` family is missing.

Do not apply when:
- Building on platforms/toolchains that already provide `drand48` APIs.

## How to apply

From the MBROLATOR repository root (`externtools/MBROLATOR`):

```bash
git apply ../../patch-stack/mbrolator/0001-resynthesis-src-resynth-windows-drand48.patch
```

Or from MBROLATOR root using helper scripts:

```powershell
../../patch-stack/apply-mbrolator-patches.ps1
../../patch-stack/apply-mbrolator-patches.ps1 -CheckOnly
../../patch-stack/apply-mbrolator-patches.ps1 -Revert
```

```bash
../../patch-stack/apply-mbrolator-patches.sh
../../patch-stack/apply-mbrolator-patches.sh --check
../../patch-stack/apply-mbrolator-patches.sh --revert
```

If not running from MBROLATOR root, pass an explicit target path:

```powershell
./patch-stack/apply-mbrolator-patches.ps1 -MbrolatorRoot "externtools/MBROLATOR"
```

```bash
./patch-stack/apply-mbrolator-patches.sh --mbrolator-root externtools/MBROLATOR
```

## How to revert

```bash
git apply -R ../../patch-stack/mbrolator/0001-resynthesis-src-resynth-windows-drand48.patch
```

## Notes

- Patch files are documentation artifacts too; include context and rationale in comments.
- Prefer small, focused patches over large refactors.
- Keep compatibility fixes platform-scoped where possible.

## Strategy For Future Upstreams

Use this same patch-stack approach for research/open-source codebases that are not heavily industrialized:

- Keep upstream source trees minimally changed.
- Store local fixes in numbered patch files under `patch-stack/<project>/`.
- Add one-line rationale in each patch header (problem and platform scope).
- Add apply/revert helpers only when needed for repeated workflows.
- Avoid redistributing modified upstream binaries unless required.
