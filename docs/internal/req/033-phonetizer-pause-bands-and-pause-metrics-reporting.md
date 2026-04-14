---
req_id: REQ-033
status: Draft
priority: High
impact: Mutative
created: 2026-04-14
updated: 2026-04-14
related_adrs: 'ADR-046'
implemented_by: 'CR-058, CR-059'
---

# Requirement: Phonetizer Pause Bands and Pause Metrics Reporting

# Summary

Define a three-band pause-duration model for phonetizer-emitted silence rows
(mini `M`, short `S`, long `L`), add a phonetizer-inserted recovery pause type
(`R`), and require downstream metrics to report per-type pause counts and
average durations in both human-readable table output and JSON output.

This requirement legalizes the changes requested in [CR-058](../cr/058-remove-synthetic-pause-allocation-from-metricalc.md)
and [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md).

---

# Motivation

Accurate rhythm and metrical reporting require that pause durations be row-
derived from the phonetizer's finalized phone streams instead of being
reconstructed from guessed WPM/pause-ratio models. Having a mini pause band
enables more frequent drift discharge without changing punctuation semantics,
and per-type pause reporting allows reproducible downstream analysis.

---

# Acceptance Criteria

- [ ] The grouped config schema exposes `phonetize.process.timing_model.durations.pauses` with `mini`, `short`, and `long` objects having `min` and `max` integer ms fields.
- [ ] Default values: `pauses.mini.min = 100`, `pauses.mini.max = 200`, `pauses.short.min = 280`, `pauses.short.max = 350`, `pauses.long.min = 730`, `pauses.long.max = 930` in `src/akkapros/config/default.yaml`.
- [ ] `phonetize.process.timing_model.short_pause_policy` is removed from the active schema and CLI surfaces.
- [ ] `phonetize.process.timing_model.drift_tolerance` default is set to `70` ms.
- [ ] Phonetizer frontmatter includes `recovery_pause_count`, `short_pause_partial_unload_count`, and `long_pause_partial_unload_count` for both original and accentuated streams.
- [ ] `realize_phone_rows()` (Pass 2) may insert recovery pause rows (`category='S', type='R', length='M'`) only after `boundary='F'` and only when the following row is non-silence and `abs(running_drift_ms) >= pauses.mini.min`.
- [ ] `metricalc` and `metrics` emit a per-stream `Pause metrics` section in human-readable table output labeled exactly `Pause metrics:` and a per-stream `pause_metrics` object in JSON output keyed by `Q`, `S`, `E`, `C`, `I`, `R` with `count` and `average_duration_ms` numeric fields (zero when count is zero).
- [ ] Tests cover recovery insertion eligibility, punctuation-owned pause precedence, mini-band discharge behavior, residual partial-unload counting, and per-type pause aggregation in both table and JSON outputs.

---

# Interface Notes

- Input: `_tilde.txt` → phonetizer builds `_phone.txt`/`_ophone.txt` streams where silence rows carry `category='S'`, `type ∈ {Q,E,S,C,I,R}`, and `length ∈ {M,S,L}` plus `duration` in ms.
- Phonetizer frontmatter: include drift summary and the three counters named above under `metadata.data.phonetize`.
- Metrics JSON per stream example:

```json
"pause_metrics": {
  "Q": {"count": 10, "average_duration_ms": 812.3},
  "S": {"count": 45, "average_duration_ms": 312.0},
  "E": {"count": 1, "average_duration_ms": 915.0},
  "C": {"count": 12, "average_duration_ms": 322.1},
  "I": {"count": 5, "average_duration_ms": 298.6},
  "R": {"count": 8, "average_duration_ms": 150.0}
}
```

# Open Questions

- Should the recovery pause trigger use a separate explicit config key (for example `pauses.mini.trigger_ms`) rather than `pauses.mini.min`? Current CR-059 normalizes to `pauses.mini.min`.

---

# Implementation Notes (optional)

- Affected components: `src/akkapros/lib/phonetize.py`, `src/akkapros/lib/metrics.py`, `src/akkapros/cli/phonetizer.py`, `src/akkapros/cli/fullprosmaker.py`, `src/akkapros/config/default.yaml`, documentation and tests listed in CR-059.
- Implementation is by CR-059 (pause restructure) and CR-058 (metrics shape changes).

# Related

- Related ADRs: [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- Implementation CRs: [CR-058](../cr/058-remove-synthetic-pause-allocation-from-metricalc.md), [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)

# Non-Goals

- This requirement does not mandate exact duration-selection algorithms inside the phonetizer beyond legal-band selection and recovery-trigger eligibility.

# Security / Safety Considerations

- None specific beyond avoiding failure modes: in case of malformed streams phonetizer must emit diagnostics and not crash.
