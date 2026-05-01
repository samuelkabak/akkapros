---
cr_id: CR-097
status: Done
verified: 2026-05-01
priority: Low
impact: Additive
created: 2026-05-01
updated: 2026-05-01
implements: ''
---

# Change Request: Add Mono Mode Branch to Lexlinks Construct Demo

# Summary

The lexlinks construct demo currently runs only a single bimoraic (bi mode, style lob) pipeline. Add a second mono mode branch (style lob) so the demo exercises both mora modes, matching the corpus demo's coverage.

The change is purely additive — the existing bi mode branch is untouched, and the new mono branch produces its own artifact set under a distinct prefix.

---

# Motivation

- The corpus demo (`demo/akkapros/prosmaker/`) already runs three branches: sob, lob (bi), and mono-lob. The construct demo should offer comparable coverage so users can compare bi vs. mono mode outputs on the same input.
- Mono mode is a supported first-class feature (CR-027, CR-093). The construct demo should exercise it to keep the demo surface representative.

---

# Scope

## Included

- Add a second `fullprosmaker.py` invocation to both launcher scripts (`.sh` and `.ps1`) with `--mora-mode mono --prosody-style lob` and prefix `erra_construct-mono`
- Update `demo/README.md` to document the new mono branch outputs
- Create CR-097 governance record

## Not Included

- No changes to the existing bi mode config file or its invocation
- No changes to any source code, tests, or package defaults
- No new config file — the mono branch reuses the same `construct-demo.yaml` config (only `--mora-mode` and `--prefix` differ via CLI flags, matching the corpus demo pattern)

---

# Current Behavior

The construct demo runs a single `fullprosmaker.py` invocation:

```bash
python src/akkapros/cli/fullprosmaker.py data/lexlinks/construct_prep/erra_construct_proc.txt \
  --conf demo/akkapros/lexlinks/construct-demo.yaml
```

This produces artifacts under the `erra_construct` prefix (bi mode, style lob).

---

# Proposed Change

After the existing bi mode run, add a second invocation:

```bash
python src/akkapros/cli/fullprosmaker.py data/lexlinks/construct_prep/erra_construct_proc.txt \
  --conf demo/akkapros/lexlinks/construct-demo.yaml \
  --prefix erra_construct-mono \
  --mora-mode mono \
  --prosody-style lob
```

This produces a parallel artifact set under the `erra_construct-mono` prefix in the same `results/` directory.

---

# Technical Design

**Launcher scripts** — two files to update:

1. `demo/akkapros/lexlinks/construct-demo.sh` — add the mono invocation after the existing bi invocation
2. `demo/akkapros/lexlinks/construct-demo.ps1` — same change for PowerShell

Both scripts already clear the `results/` directory at the start, so the mono artifacts will be fresh on each run.

**Config reuse:** The existing `construct-demo.yaml` already sets `prosody.process.style: lob` and `prosody.process.mora_mode: bi`. The mono invocation overrides both via CLI flags (`--mora-mode mono --prosody-style lob`), matching the pattern used by the corpus demo's mono branch.

---

# Files Likely Affected

demo/akkapros/lexlinks/construct-demo.sh
demo/akkapros/lexlinks/construct-demo.ps1
demo/README.md

---

# Acceptance Criteria

- [x] `construct-demo.sh` runs two `fullprosmaker.py` invocations (bi + mono)
- [x] `construct-demo.ps1` runs two `fullprosmaker.py` invocations (bi + mono)
- [x] Mono branch produces artifacts under prefix `erra_construct-mono` in `results/`
- [x] Existing bi mode artifacts under prefix `erra_construct` are unchanged
- [x] `demo/README.md` documents the new mono branch outputs
- [x] Running either launcher script completes without error

---

# Risks / Edge Cases

- The `results/` directory is cleared at the start of each run, so there is no risk of stale mono artifacts from a previous run.
- The mono branch uses the same input file (`erra_construct_proc.txt`) and the same config, so no additional input validation is needed.

---

# Testing Strategy

Manual verification:

1. Run `sh demo/akkapros/lexlinks/construct-demo.sh` (or the `.ps1` variant on Windows)
2. Verify that `results/` contains both `erra_construct_*.txt` and `erra_construct-mono_*.txt` files
3. Spot-check that the mono artifacts differ from the bi artifacts (e.g., different syllable counts in metrics)

---

# Rollback Plan

Revert the two launcher scripts and `demo/README.md` to remove the mono invocation.

---

# Related Issues

- CR-027: Add prosody mora mode selection (introduced mono mode)
- CR-093: Skip accent elongation in mono mode (mono mode refinements)
- CR-055: Add config-backed lexlinks construct demo (original construct demo)

---

# Tasks

## Implementation

- [x] Add mono `fullprosmaker.py` invocation to `construct-demo.sh`
- [x] Add mono `fullprosmaker.py` invocation to `construct-demo.ps1`
- [x] Update `demo/README.md` to document mono branch outputs

## Tests

- [x] Manual verification: run both launcher scripts and confirm artifact sets

## Documentation

- [x] Update `demo/README.md`

## Review

- [x] Verify acceptance criteria

---

# Implementation Blockers

None.

---

# Notes

The corpus demo passes `--mora-mode mono` as a CLI flag to `prosmaker.py` while keeping the shared config file at `mora_mode: bi`. The construct demo follows the same pattern with `fullprosmaker.py`.
