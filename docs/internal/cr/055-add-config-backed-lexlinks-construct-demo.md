---
cr_id: CR-055
status: Done
priority: Medium
impact: Additive
created: 2026-04-12
updated: 2026-04-12
implements: 'ADR-043, REQ-009'
---

# Change Request: Add config-backed lexlinks construct demo

## Summary

Add runnable demo launchers under `demo/akkapros/lexlinks/` that execute the
current one-command `fullprosmaker.py` pipeline against the checked-in
construct-prepared lexical-links sample
`data/lexlinks/construct_prep/erra_construct_proc.txt`.

The goal is to make the construct-prepared Erra sample reproducible through the
same config-backed demo pattern already used for the corpus demo: one shared
grouped YAML file, one PowerShell launcher, one POSIX launcher, and a stable
results location with a fixed prefix.

---

## Motivation

The repository already contains a checked-in lexlinks demo config file, but it
is not currently paired with runnable launchers or documented as an executable
demo workflow.

That leaves a gap between the stored lexlinks input artifacts and the
repository's demo surface. Users can inspect the construct-prepared input and
the grouped config, but they do not yet have a thin wrapper that reproduces the
full pipeline run directly from those checked-in assets.

This CR legalizes that workflow by defining the launcher contract and the
expected demo inputs and outputs.

---

## Scope

## Included

- Adapt `demo/akkapros/lexlinks/construct-demo.yaml` so it is runnable for the
  fixed construct-prepared Erra sample with prefix `erra_construct`.
- Add `construct-demo.ps1` and `construct-demo.sh` under
  `demo/akkapros/lexlinks/`.
- Make both launchers run `fullprosmaker.py` on
  `data/lexlinks/construct_prep/erra_construct_proc.txt` using the shared YAML
  config.
- Keep the launchers thin and config-backed rather than hardcoding the stable
  option surface in two separate scripts.
- Document the lexlinks demo in `demo/README.md`.

## Not Included

- Changing the lexical-links preparation workflow or the contents of
  `data/lexlinks/construct_prep/erra_construct_proc.txt`.
- Redesigning `fullprosmaker.py`.
- Adding a second lexlinks demo variant beyond the fixed Erra construct sample.

---

## Current Behavior

Before this CR, repository inspection on 2026-04-12 showed that
`demo/akkapros/lexlinks/construct-demo.yaml` existed, but there were no
checked-in launcher scripts in `demo/akkapros/lexlinks/` to execute it.

The config also still carried the generic prefix `corpus`, which did not match
the fixed sample name requested for the construct-prepared Erra run.

As a result, the lexlinks demo directory was not yet a discoverable, runnable
demo surface comparable to the existing `demo/akkapros/prosmaker/` workflow.

---

## Proposed Change

- Set the lexlinks demo config prefix to `erra_construct` while keeping the
  checked-in results directory under `demo/akkapros/lexlinks/results/`.
- Add one PowerShell and one POSIX launcher that:
  - resolve the repository root from the script location
  - clear the demo results directory
  - invoke `src/akkapros/cli/fullprosmaker.py`
  - pass the fixed input file
    `data/lexlinks/construct_prep/erra_construct_proc.txt`
  - load `demo/akkapros/lexlinks/construct-demo.yaml` with `--conf`
- Update `demo/README.md` so users can discover and run the new demo.

---

## Technical Design

Architecture notes:

Components:

- `demo/akkapros/lexlinks/construct-demo.yaml`
- `demo/akkapros/lexlinks/construct-demo.ps1`
- `demo/akkapros/lexlinks/construct-demo.sh`
- `demo/README.md`

Launcher design:

- follow the repository's existing demo-wrapper style by resolving the repo
  root from the launcher location
- prefer the checked-in virtual environment interpreter when present, then fall
  back to the system Python entry points
- keep the launchers thin by delegating stable defaults to the grouped YAML
  config instead of duplicating them in both scripts

Pipeline contract:

- the demo runs `fullprosmaker.py` directly from a checked-in `*_proc.txt`
  input, consistent with the live full-pipeline CLI contract
- the run produces the standard `fullprosmaker` artifacts for prefix
  `erra_construct` in `demo/akkapros/lexlinks/results/`

---

## Files Likely Affected

demo/akkapros/lexlinks/construct-demo.yaml
demo/akkapros/lexlinks/construct-demo.ps1
demo/akkapros/lexlinks/construct-demo.sh
demo/README.md
docs/internal/cr/055-add-config-backed-lexlinks-construct-demo.md

---

## Acceptance Criteria

- [x] `demo/akkapros/lexlinks/construct-demo.yaml` is runnable for the fixed
      construct-prepared sample and sets the effective prefix to
      `erra_construct`.
- [x] The repository contains checked-in PowerShell and POSIX launchers under
      `demo/akkapros/lexlinks/`.
- [x] Both launchers invoke `fullprosmaker.py` on
      `data/lexlinks/construct_prep/erra_construct_proc.txt` using
      `demo/akkapros/lexlinks/construct-demo.yaml`.
- [x] The launchers remain thin and config-backed rather than re-encoding the
      stable option surface in both scripts.
- [x] `demo/README.md` documents the new lexlinks construct demo and how to run
      it.
- [x] A verification run of the config-backed command completes and emits the
      expected `erra_construct` output family under
      `demo/akkapros/lexlinks/results/`.

---

## Risks / Edge Cases

Possible issues:

- the POSIX launcher prefers `.venv/Scripts/python.exe` when present because
  this repository is often run on Windows-backed worktrees; non-Windows users
  may instead rely on `python` or `python3`
- if package defaults change later, the checked-in demo config may need refresh
  to remain self-describing, consistent with the existing config-backed demo
  policy
- the demo is intentionally fixed to one checked-in input file and does not try
  to generalize lexlinks batch processing

---

## Testing Strategy

Verification run:

- execute `python src/akkapros/cli/fullprosmaker.py
  data/lexlinks/construct_prep/erra_construct_proc.txt --conf
  demo/akkapros/lexlinks/construct-demo.yaml`
- confirm that the run writes the expected `erra_construct_*` artifacts into
  `demo/akkapros/lexlinks/results/`

Documentation verification:

- confirm that `demo/README.md` lists the lexlinks demo scripts, config, input,
  and output family

---

## Rollback Plan

If the lexlinks demo wrappers prove misleading or unstable, remove the two
launchers, revert the config prefix change, and remove the README entry while
keeping the checked-in lexical-links inputs intact.

---

## Related Issues

- [CR-052](052-make-prosmaker-demo-config-driven-and-restore-printer-outputs.md)
- [CR-053](053-expand-prosmaker-demo-config-to-full-explicit-defaults.md)
- [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)
- [REQ-009](../req/009-phonological-research-model-and-corpus-scope.md)

---

## Tasks

## Implementation

- [x] Adapt the lexlinks demo config for the fixed `erra_construct` run
- [x] Add PowerShell and POSIX launchers
- [x] Keep the launchers config-backed and thin

## Tests

- [x] Run the config-backed fullprosmaker command on the checked-in input

## Documentation

- [x] Document the lexlinks demo in `demo/README.md`
- [x] Add this legalizing CR record

## Review

- [x] Verify the acceptance criteria against the repository state and demo run

---

## Implementation Blockers

Use this section when implementation or verification cannot proceed safely.

Leave the section empty if no blockers are known.

---

## Notes

Verification completed on 2026-04-12:

- updated the lexlinks demo config prefix from `corpus` to `erra_construct`
- added `construct-demo.ps1` and `construct-demo.sh` as thin wrappers over the
  checked-in grouped config
- updated `demo/README.md` so the lexlinks demo is discoverable alongside the
  existing prosmaker and phoneprep demos
- verified the config-backed fullprosmaker run against the checked-in
  `erra_construct_proc.txt` input and confirmed generation of the expected
  `erra_construct_*` artifact family under `demo/akkapros/lexlinks/results/`
