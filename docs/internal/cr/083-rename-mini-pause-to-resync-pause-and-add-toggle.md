---
cr_id: CR-083
status: Done
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-20
implements: 'REQ-043'
---

# Change Request: Rename Mini Pause to Resync Pause and Add Toggle

# Summary

Rename the phonetizer's algorithmic non-punctuation recovery pause from
`mini pause` to `resync pause` across approved config, diagnostics,
documentation, and metrics reporting, and add a new process control
`phonetize.process.timing_model.enable_resync_pause` with default `false`.

Repository inspection on 2026-04-19 shows that the active runtime still uses
`MINI_PAUSE_*` constants, `pauses.mini`, `_maybe_insert_mini_pause()`,
`mini_pause_*` diagnostic keys, and public documentation that presents the same
term everywhere. This CR makes the terminology precise without changing the
current row identity contract `MEN|...|M|...|MP|...|<space>`.

This CR narrows the historical terminology from
[CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md),
[CR-066](066-promote-mini-pauses-to-a-distinct-phone-row-contract.md),
[CR-075](075-humanize-phonetizer-diagnostic-names-and-replace-ordinary-vowel-correction-rate-with-drift-tolerance-effect.md),
and [CR-080](080-add-mora-mode-aware-beat-alignment-and-relax-original-ophone-timing.md).
Those records remain history, but `resync pause` and `enable_resync_pause`
become the active contract terms.

---

# Motivation

The current pause type is not merely a small pause band. Its function is to
bring the stream back to an equivalent synchronization branch. The existing name
therefore describes size more than function. That is now misleading because the
current solver uses explicit beat-equivalence logic and exposes enough
diagnostics that the pause's resynchronization role is central.

The runtime also currently inserts such rows whenever conditions permit. The
requested flag makes that behavior explicit and default-off so users can choose
whether algorithmic resynchronization is active.

---

# Scope

## Included

- Add `phonetize.process.timing_model.enable_resync_pause: false`.
- Rename `pauses.mini` to `pauses.resync` in the approved config surface.
- Rename the runtime helper/constant terminology from `mini` to `resync` where
  those names are part of active contract, docs, or tests.
- Rename canonical frontmatter and metrics-facing diagnostic keys from the
  `mini_pause_*` family to the `resync_pause_*` family.
- Update human-readable metrics text and public docs to say `resync pause`.
- Keep the emitted row contract `MEN`, subtype `M`, realization `MP`, and one
  literal ASCII space in `text` unchanged.
- Gate row insertion on `enable_resync_pause`.

## Not Included

- Changing the row codes `MEN`, `M`, or `MP`.
- Changing the resync duration math beyond the new flag and renamed band path.
- Introducing compatibility aliases unless another approved record requires
  them.
- Changing punctuation-owned short/long pause behavior.

---

# Current Behavior

Observed current behavior on 2026-04-19:

- `src/akkapros/lib/phonetize.py` exposes `MINI_PAUSE_LABEL`,
  `MINI_PAUSE_TYPE`, `MINI_PAUSE_REALIZATION`, and `MINI_PAUSE_TEXT`
- `_mini_pause_structurally_eligible()` and `_maybe_insert_mini_pause()` govern
  runtime insertion
- config defaults use `phonetize.process.timing_model.durations.pauses.mini`
- no process flag exists to disable insertion globally
- `src/akkapros/lib/metrics.py` extracts and prints `mini_pause_count`,
  `inserted_mini_pause_count`, `eligible_mini_pause_count`, and
  `mini_pause_insertion_rate`
- public docs and tests describe the same concept as `mini pause`

The current contract is therefore internally consistent but uses the older term
everywhere and provides no explicit top-level enable/disable control.

---

# Proposed Change

## 1. Adopt `resync pause` as the active term

All canonical config, diagnostic, metrics, and documentation surfaces shall use
`resync pause` terminology instead of `mini pause`.

## 2. Add an explicit toggle

`phonetize.process.timing_model.enable_resync_pause` is a new boolean process
control with default `false`. If false, the solver must skip algorithmic
recovery-pause insertion even when the structural and duration conditions are
otherwise satisfied.

## 3. Rename the pause-band path

The non-punctuation recovery pause band currently exposed as
`phonetize.process.timing_model.durations.pauses.mini` becomes
`phonetize.process.timing_model.durations.pauses.resync`.

## 4. Keep the row contract stable in this change

The emitted phone-row identity remains:

- label `MEN`
- pause subtype `M`
- realization `MP`
- `text` as one literal space

This CR changes terminology and control surface, not row encoding.

## 5. Rename diagnostics and metrics-facing labels

Canonical phonetizer diagnostics become:

- `resync_pause_count`
- `inserted_resync_pause_count`
- `eligible_resync_pause_count`
- `resync_pause_insertion_rate`

Human-readable metrics text must use the same terminology.

---

# Technical Design

Concrete execution surfaces:

- update the phonetizer default schema and `src/akkapros/config/default.yaml`
  to add `enable_resync_pause` and rename `pauses.mini` to `pauses.resync`
- rename the canonical helper/constants/diagnostic names in
  `src/akkapros/lib/phonetize.py`, `src/akkapros/lib/metrics.py`,
  `src/akkapros/lib/print.py`, and `src/akkapros/lib/docflow.py`
- gate the insertion branch so `_maybe_insert_*()` is bypassed when the new
  flag is false
- update config help, confwriter/path inventory, phonetizer docs, metrics docs,
  and repository demo YAML files
- update tests that currently import `MINI_PAUSE_*` or assert `mini_pause_*`
  frontmatter keys and printed labels

Recommended naming contract:

- runtime code may keep a stable internal row-code meaning of `M` and `MP`
- public/current config and diagnostic names must use `resync`
- historical `mini` wording may remain only inside older historical governance
  records

---

# Files Likely Affected

src/akkapros/lib/phonetize.py  
src/akkapros/lib/metrics.py  
src/akkapros/lib/print.py  
src/akkapros/lib/docflow.py  
src/akkapros/config/default.yaml  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/confwriter.py  
tests/test_phonetize_lib.py  
tests/test_integration.py  
tests/test_metrics_stats.py  
tests/test_print_merger.py  
tests/test_config_support.py  
docs/akkapros/phonetizer.md  
docs/akkapros/phonetizer-algorithm.md  
docs/akkapros/phonetizer-phone-file-guide.md  
docs/akkapros/phonetizer-data-model.md  
docs/akkapros/metrics-computation.md  
demo/akkapros/lexlinks/construct-demo.yaml  
demo/akkapros/prosmaker/corpus-demo.yaml  

---

# Acceptance Criteria

- [x] `enable_resync_pause: false` exists in the approved process timing-model
      surface.
- [x] `pauses.resync` replaces `pauses.mini` as the canonical config path.
- [x] When `enable_resync_pause = false`, no algorithmic resync pause rows are
      inserted.
- [x] When `enable_resync_pause = true`, legal inserted rows still emit
      `MEN`, `M`, `MP`, and one literal space in `text`.
- [x] Canonical diagnostics and metrics-facing labels use `resync_pause_*`
      terminology.
- [x] Public docs and help surfaces say `resync pause` instead of `mini pause`
      except in historical records.
- [x] Focused tests cover the new toggle, renamed config path, and renamed
      diagnostics.

---

# Risks / Edge Cases

- Renaming diagnostics without updating metrics extraction aliases and tests will
  leave frontmatter and reporting out of sync.
- Renaming the pause-band path without updating config help/demo YAML surfaces
  will make the contract look mixed and unstable.
- The default `false` toggle changes behavior; tests and examples that relied on
  automatic insertion must opt in explicitly.

---

# Testing Strategy

Unit tests:

- default config exposes `enable_resync_pause` and `pauses.resync`
- disabled flag suppresses insertion
- enabled flag preserves row identity and insertion behavior
- diagnostics/frontmatter use `resync_pause_*` names

Integration tests:

- CLI path overrides can enable resync pause insertion and set the resync band
- metrics output text uses `resync pause` terminology

Manual checks:

- inspect one emitted phone file to confirm row codes remain `MEN|...|MP|...`
- inspect one metrics table and phonetizer doc page to confirm terminology

---

# Rollback Plan

Restore `mini` naming and remove `enable_resync_pause`, accepting the older
always-available insertion behavior.

---

# Related Issues

- [REQ-043](../req/043-resync-pause-terminology-toggle-and-reporting.md)
- [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
- [CR-066](066-promote-mini-pauses-to-a-distinct-phone-row-contract.md)
- [CR-075](075-humanize-phonetizer-diagnostic-names-and-replace-ordinary-vowel-correction-rate-with-drift-tolerance-effect.md)

---

# Tasks

## Implementation

- [x] Add `enable_resync_pause`
- [x] Rename the canonical band path to `pauses.resync`
- [x] Rename canonical diagnostics/reporting labels to `resync_pause_*`
- [x] Gate insertion on the new flag

## Tests

- [x] Update config/help surface tests
- [x] Update runtime and metrics tests for renamed diagnostics
- [x] Add explicit disabled/enabled insertion coverage

## Documentation

- [x] Update phonetizer, phone-row, metrics, and config docs
- [x] Update demo YAML examples

## Review

- [x] Verify terminology changed without changing row encoding

---

# Implementation Blockers
