---
adr_id: ADR-046
status: Accepted
created: 2026-04-14
updated: 2026-04-14
superseded_by: null
---

# 46. Phonetizer mini-band and row-derived pause reporting

## Plain Summary

Adopt a row-derived pause model for downstream metrics and introduce a
mini (`M`) pause band plus a phonetizer-inserted recovery pause type (`R`).
Downstream metrics shall report per-type pause counts and average durations in
both human-readable table output and JSON output. Drift handling remains
extensible-only and `drift_tolerance` increases to 70 ms.

TL;DR: metrics must use realized phone rows as the single source of truth for
pause durations; phonetizer may insert small recovery pauses to discharge drift
inside the mini band; metrics shall report per-type pause aggregates.

## Context and Problem Statement

Recent verification showed two overlapping mismatches in pause handling:

- `metricalc` still reconstructed pause durations from guessed `wpm` and
  `pause_ratio` and applied synthetic allocation and mora-correction logic
  (see [CR-058](../cr/058-remove-synthetic-pause-allocation-from-metricalc.md)).
- The phonetizer used only two pause bands (short/long) and had no mechanism
  to insert brief recovery pauses to discharge running drift more frequently
  (see [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)).

These gaps reduce reproducibility and create duplicate inference paths between
phonetizer and metrics.

## Decision Drivers

- Accuracy: metrics should reflect realized durations rather than reconstructed
  allocations.
- Reproducibility: downstream consumers must get the same pause durations the
  phonetizer produced.
- Robustness: the phonetizer should avoid hard failures in normal parameter
  ranges (`extensible` drift behavior preferred).
- Minimal surface change: keep existing pause `type` letters and add `R` and
  `M` length codes to preserve most row contract fields.

## Considered Options

- Option A — Keep synthetic pause allocation in `metricalc` and add mini-band
  simulation there.
- Option B — Move to a row-derived pause model; add mini-band recovery in
  phonetizer and require metrics to report per-type aggregates. (Chosen)
- Option C — Hybrid: phonetizer emits band hints and metrics reconstructs
  durations using the hints plus global pause-ratio.

Rationale: Option B places responsibility for pause durations with the stage
that realizes durations (phonetizer), eliminates duplicated logic, and gives
metrics a deterministic artifact to consume.

## Decision Outcome

We choose Option B: a row-derived pause model with a mini band and an
`R` recovery pause. Implementation is performed by CR-059 (pause restructure)
and CR-058 (metrics contract change). Key configuration and output contracts:

- `phonetize.process.timing_model.durations.pauses` must include `mini`,
  `short`, `long` bands (min/max ms).
- `phonetize.process.timing_model.drift_tolerance` default is increased to
  70 ms.
- `short_pause_policy` is removed from the active schema; only `extensible`
  drift behavior is supported as the documented runtime contract.
- `realize_phone_rows()` may insert recovery pauses (`type='R', length='M'`) at
  eligible `boundary='F'` locations when `abs(running_drift_ms) >= pauses.mini.min`.
- `metricalc` must emit per-stream `Pause metrics` (human table) and
  `pause_metrics` (JSON) with `count` and `average_duration_ms` for the types
  `Q`, `S`, `E`, `C`, `I`, `R`.

## Pros and Cons of the Options

### Chosen Option (Option B)

- Pros:
  - Single source of truth for pause durations (phonetizer rows).
  - Deterministic metrics computed from rows; increased reproducibility.
  - Mini recovery band reduces the need for destructive vowel-length changes.
- Cons:
  - Requires changes across phonetizer, fullprosmaker, and metricalc.
  - Emitted durations and demo snapshots will change; tests must be updated.

### Option A (Keep synthetic allocation)

- Pros: minimal phonetizer change; metrics continues to use existing code.
- Cons: duplication of logic; less reproducible and more brittle to upstream
  changes.

### Option C (Hybrid)

- Pros: partial compatibility with older outputs.
- Cons: retains ambiguity; requires careful specification of hint semantics.

## Implications and Consequences

- Code: modify `src/akkapros/lib/phonetize.py` to support `mini` band and
  recovery insertion; modify `src/akkapros/lib/metrics.py` to aggregate per-
  type pause metrics and include them in table/JSON outputs; update
  `src/akkapros/config/default.yaml`.
- Docs: update `docs/akkapros/phonetizer*.md`, `docs/akkapros/metrics-computation.md`,
  config docs, and CLI help.
- Tests: add unit and integration tests for recovery insertion, partial-unload
  counting, and per-type pause aggregation.
- Migration: demo result artifacts and snapshots will need regeneration.

## Links

- [CR-058](../cr/058-remove-synthetic-pause-allocation-from-metricalc.md)
- [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
- [REQ-033](../req/033-phonetizer-pause-bands-and-pause-metrics-reporting.md)

## Implementation Notes (optional)

- Next steps: implement CR-059 then CR-058 in sequence; update tests and
  regenerate demo artifacts.

## Reviewed By

- Phonetizer maintainers (TBD)
