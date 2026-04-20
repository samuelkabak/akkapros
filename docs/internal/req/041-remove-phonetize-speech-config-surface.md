---
req_id: REQ-041
status: Draft
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
related_adrs: 'ADR-039, ADR-043'
implemented_by: 'CR-081'
---

# Requirement: Remove Phonetize Speech Config Surface

# Summary

The grouped configuration shall no longer expose
`phonetize.process.timing_model.speech`, and the legacy keys
`phonetize.process.timing_model.speech.wpm` and
`phonetize.process.timing_model.speech.pause_ratio` shall be removed from the
 approved config surface, emitted default YAML, shared semantic verification,
CLI/config-path tooling, tests, and user-facing documentation.

This requirement records the current repository reality that phonetizer timing
no longer uses those speech scalars as active timing controls, while metrics
already derives reported `WPM` and `Pause ratio` from realized phone-row
durations. The removal therefore narrows older phonetize config contracts that
still advertise a `speech` subtree even though the active timing solver no
longer depends on it.

Historical note:

- This requirement narrows the phonetize config surface described in
  [REQ-027](027-phonetize-config-semantic-invariants-for-shared-verification.md)
  and the grouped-config shape recorded in
  [REQ-029](029-stage-config-run-process-separation-and-common-outdir-removal.md).
- It does not change the row-derived speech metrics introduced downstream by
  [CR-058](../cr/058-remove-synthetic-pause-allocation-from-metricalc.md).

---

# Motivation

Repository inspection on 2026-04-19 shows that `wpm` and `pause_ratio` remain
in the phonetize schema, verification layer, config tooling, tests, demos, and
docs, but are no longer consumed by the phonetizer duration solver. Keeping
dead config surface in an approved contract is misleading for users and costly
for maintenance because every schema, help, and test surface must continue to
pretend those keys are meaningful.

The required change is therefore not only a schema deletion. The approved
contract must remove the entire `speech` block consistently across config
emission, path validation, preflight verification, test expectations, example
YAML files, and user-facing documentation.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the approved grouped config surface is materialized, when the
      phonetize timing-model subtree is inspected, then
      `phonetize.process.timing_model.speech` is absent.
- [ ] Given the approved grouped config surface is materialized, when removed
      keys are checked, then
      `phonetize.process.timing_model.speech.wpm` and
      `phonetize.process.timing_model.speech.pause_ratio` are absent from the
      emitted default YAML, config schema, confwriter inventory, and path
      override help surfaces.
- [ ] Given phonetize semantic verification is executed, when config relations
      are checked, then verification no longer reads, validates, warns on, or
      blocks on `phonetize.process.timing_model.speech.wpm` or
      `phonetize.process.timing_model.speech.pause_ratio`.
- [ ] Given an old config file still contains
      `phonetize.process.timing_model.speech`, when that config is loaded
      through the approved config path, then the removed keys are rejected
      clearly as unsupported current contract rather than being silently
      accepted.
- [ ] Given the phonetizer implementation is inspected, when active timing
      control inputs are listed, then no runtime path depends on
      `wpm`, `pause_ratio`, or a surviving `speech` block under
      `phonetize.process.timing_model`.
- [ ] Given user-facing configuration and phonetizer documentation is updated,
      when approved config paths are shown, then they do not document a
      phonetize `speech` block or examples using
      `phonetize.process.timing_model.speech.wpm` or
      `phonetize.process.timing_model.speech.pause_ratio`.
- [ ] Given repository-owned demos and sample configs are updated, when
      phonetize timing examples are inspected, then they do not include a
      `speech:` section under `phonetize.process.timing_model`.
- [ ] Given tests cover the removed contract, when config-surface and CLI-path
      expectations are verified, then tests assert absence or rejection of the
      removed `speech` keys instead of asserting warning/blocking semantics for
      `pause_ratio` or path acceptance for `wpm`.
- [ ] Given metrics outputs are inspected after this removal, when `WPM` and
      `Pause ratio` appear in metrics artifacts, then they remain row-derived
      runtime outputs rather than phonetize-config inputs.

---

# User Story (optional)
> As a maintainer or config user, I want the phonetize config surface to expose
> only active timing controls so that the YAML contract, help text, and tests
> do not advertise dead parameters.

---

# Interface Notes
- Removed config paths:
  - `phonetize.process.timing_model.speech`
  - `phonetize.process.timing_model.speech.wpm`
  - `phonetize.process.timing_model.speech.pause_ratio`
- Config-survival rule:
  - `phonetize.process.timing_model` remains, but without a `speech` child
  - row-derived metrics outputs named `WPM` and `Pause ratio` remain active in
    metrics artifacts and are not removed by this requirement
- Affected components:
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/cli/phonetizer.py`
  - `src/akkapros/cli/confwriter.py`
  - `src/akkapros/cli/fullprosmaker.py`
  - config/default emission and config-path schema helpers under `src/akkapros/`
  - phonetizer/config docs and repository-owned demo YAML files
  - tests that still assert the old speech-block contract

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - remove the `speech` subtree from the canonical default config and schema
  - remove verification-only logic for the deleted keys
  - rewrite tests from “warn/block on pause_ratio” to “removed keys are absent
    or rejected”
  - update all package docs and demo configs that still show the removed block

# Related
- Related ADRs: [ADR-039](../adr/039-replacement-of-timing-model.md),
  [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)
- Implementation CRs: [CR-081](../cr/081-remove-phonetize-speech-config-and-dead-speech-controls.md)

# Non-Goals
- This requirement does not remove `WPM` or `Pause ratio` from metrics outputs.
- This requirement does not redesign phonetizer timing behavior beyond removal
  of dead config surface.
- This requirement does not change row-derived speech metrics formulas in
  metricalc.

# Security / Safety Considerations
- The config loader, schema, and docs must not continue to advertise removed
  keys as approved current contract because that creates silent mismatch
  between documented and executable behavior.