---
req_id: REQ-043
status: Draft
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
related_adrs: 'ADR-046'
implemented_by: 'CR-083'
---

# Requirement: Resync Pause Terminology, Toggle, and Reporting

# Summary

The phonetizer shall rename the current non-punctuation recovery concept from
`mini pause` to `resync pause` across approved configuration, diagnostics,
documentation, and metrics-facing reporting, while keeping the existing phone
row identity codes `MEN`, `M`, and `MP` unchanged for now.

The phonetizer shall also add a new process-level control
`phonetize.process.timing_model.enable_resync_pause` with default `false`.
When this flag is false, the phonetizer shall not insert algorithmic recovery
pause rows even if the structural and duration conditions would otherwise make
them legal.

Historical note:

- This requirement renames the terminology introduced through
  [REQ-033](033-phonetizer-pause-bands-and-pause-metrics-reporting.md),
  [CR-059](../cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md),
  [CR-066](../cr/066-promote-mini-pauses-to-a-distinct-phone-row-contract.md),
  and [CR-075](../cr/075-humanize-phonetizer-diagnostic-names-and-replace-ordinary-vowel-correction-rate-with-drift-tolerance-effect.md).
- Those older records remain historical, but `resync pause` becomes the active
  public contract term.

---

# Motivation

Repository inspection on 2026-04-19 shows that the current code, docs, tests,
and metrics-facing diagnostics consistently use `mini pause` language for a
pause row whose actual function is beat resynchronization. The current term is
historical, but the active algorithm now uses beat-equivalence logic tightly
enough that `resync pause` is the clearer name.

The requested change also adds an explicit on/off control. Today the solver may
insert one such recovery row whenever the local conditions are satisfied. The
new flag makes that behavior a deliberate runtime choice rather than an always-
available hidden default.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the approved grouped config surface is materialized, when the
      phonetize timing-model process controls are inspected, then
      `enable_resync_pause: false` appears immediately after
      `drift_tolerance`.
- [ ] Given the approved grouped config surface is materialized, when pause-band
      keys are inspected, then `phonetize.process.timing_model.durations.pauses`
      uses `resync` instead of `mini` as the non-punctuation recovery pause
      band name.
- [ ] Given the phonetizer is executed with `enable_resync_pause = false`, when
      a boundary would otherwise qualify for algorithmic recovery pause
      insertion, then no inserted `MEN|...|MP|...` row is emitted.
- [ ] Given the phonetizer is executed with `enable_resync_pause = true`, when
      a boundary qualifies for algorithmic recovery pause insertion, then the
      existing row contract `MEN`, `M`, `MP`, and one literal space in `text`
      remains unchanged.
- [ ] Given frontmatter diagnostics, metrics extraction, and human-readable
      metrics output are inspected, when pause-insertion statistics are named,
      then the canonical keys and labels use `resync_pause_*` terminology rather
      than `mini_pause_*` terminology.
- [ ] Given public phonetizer documentation is updated, when the recovery pause
      mechanism is described, then it is called a `resync pause` and the row
      identity codes are documented as unchanged.
- [ ] Given config and CLI help surfaces are updated, when old paths or labels
      are checked, then the approved path is `pauses.resync` and the process
      toggle is `enable_resync_pause`.

---

# User Story (optional)
> As a phonetizer user, I want the non-punctuation recovery pause to be named
> for its actual function and controlled by an explicit flag so the config and
> diagnostics describe what the solver is really doing.

---

# Interface Notes
- New process key:
  - `phonetize.process.timing_model.enable_resync_pause`
- Renamed pause-band key:
  - `phonetize.process.timing_model.durations.pauses.mini` becomes
    `phonetize.process.timing_model.durations.pauses.resync`
- Renamed diagnostics family:
  - `mini_pause_count` -> `resync_pause_count`
  - `inserted_mini_pause_count` -> `inserted_resync_pause_count`
  - `eligible_mini_pause_count` -> `eligible_resync_pause_count`
  - `mini_pause_insertion_rate` -> `resync_pause_insertion_rate`
- Stable row contract for now:
  - label `MEN`
  - pause subtype `M`
  - realization `MP`
  - text field one literal space
- Affected components:
  - phonetizer runtime and diagnostics
  - metrics extraction and human-readable metrics text
  - print/docflow helpers that currently mention `mini pause`
  - config help, confwriter, demo YAML, and phonetizer docs

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - rename the canonical config path from `pauses.mini` to `pauses.resync`
  - add `enable_resync_pause: false`
  - rename canonical diagnostics and metrics-facing labels to `resync_pause_*`
  - keep row identity codes stable in this change
  - update docs/tests/examples together so no mixed `mini`/`resync` contract
    remains

# Related
- Related ADRs: [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- Implementation CRs: [CR-083](../cr/083-rename-mini-pause-to-resync-pause-and-add-toggle.md)

# Non-Goals
- This requirement does not change the `MEN` / `M` / `MP` row identity codes.
- This requirement does not redesign the duration math for the recovery pause
  itself.
- This requirement does not add a second recovery-pause row type.

# Security / Safety Considerations
- The new toggle must be explicit and default-safe because it changes whether
  hidden algorithmic recovery rows may appear in emitted phone streams.