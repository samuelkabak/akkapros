---
req_id: REQ-045
status: Implemented
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
related_adrs: 'ADR-039, ADR-043'
implemented_by: 'CR-085'
---

# Requirement: Global Phonetizer Duration Scale

# Summary

The phonetizer timing table shall gain a new global scalar
`phonetize.process.timing_model.durations.scale` as the first key inside the
`durations` block, with default value `1.0`.

When `scale == 1.0`, the runtime shall use the configured duration values as-is
without multiplying them by `1.0`. When `scale != 1.0`, the runtime shall apply
the scale to all duration values in the `durations` table except `scale`
itself, then use that scaled effective table for realization, reporting, and
metrics-facing propagation.

The applied scale shall be surfaced in phonetizer frontmatter, logs, and
metrics outputs so downstream readers can tell whether the emitted durations are
unscaled or globally scaled.

---

# Motivation

The current phonetizer exposes a detailed duration table but no single knob for
scaling the whole runtime timing model coherently. Tuning the entire table up or
down currently requires editing many independent duration values.

The requested `scale` is therefore a global runtime convenience control, not a
replacement for the existing duration table. The special case for `1.0` avoids
injecting unnecessary floating-point approximation into the default path.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the approved grouped config surface is materialized, when the
      `durations` block is inspected, then `scale: 1.0` is the first key.
- [ ] Given `scale == 1.0`, when the phonetizer computes effective durations,
      then the original configured duration values are used directly rather than
      being multiplied by `1.0`.
- [ ] Given `scale != 1.0`, when effective durations are computed, then every
      duration value under `durations` except `scale` itself is multiplied by
      the configured scale before runtime use.
- [ ] Given scaled effective durations are used, when frontmatter is emitted,
      then the applied scale is recorded in phonetizer metadata.
- [ ] Given scaled effective durations are used, when phonetizer logging or
      metrics artifacts summarize the timing model, then the applied scale is
      visible there as current runtime context.
- [ ] Given semantic verification is executed, when `scale` is provided, then it
      is validated as a positive numeric value and the effective scaled table is
      not allowed to silently violate the active timing invariants.
- [ ] Given demo configs, config help, and public docs are refreshed, when the
      timing table is shown, then `durations.scale` is documented as the global
      multiplier and described as no-op at `1.0`.

---

# User Story (optional)
> As a phonetizer user, I want one global duration multiplier so I can retune
> the whole timing model coherently while still keeping the detailed table.

---

# Interface Notes
- New config path:
  - `phonetize.process.timing_model.durations.scale`
- Default value:
  - `1.0`
- Runtime rule:
  - if `scale == 1.0`, use configured values directly
  - otherwise multiply every duration leaf under `durations` except `scale`
- Reporting requirement:
  - expose the applied scale in phonetizer frontmatter
  - expose the applied scale in phonetizer logging
  - expose the applied scale in metrics outputs derived from phone rows
- Affected components:
  - phonetizer defaults, runtime effective-config handling, and verification
  - phonetizer frontmatter stage data and logging
  - metrics extraction/reporting of phonetizer timing context
  - config docs, phonetizer docs, demo YAML files, and tests

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - add `durations.scale: 1.0`
  - centralize effective-duration scaling in one helper so runtime and
    verification read the same scaled table
  - treat `1.0` as a true no-op path
  - record the applied scale in frontmatter, logs, and metrics-facing outputs

# Related
- Related ADRs: [ADR-039](../adr/039-replacement-of-timing-model.md), [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)
- Implementation CRs: [CR-085](../cr/085-add-global-duration-scale-to-phonetizer-timing-model.md)

# Non-Goals
- This requirement does not remove the existing detailed duration parameters.
- This requirement does not redefine row-derived speech metrics formulas.
- This requirement does not imply automatic rescaling of unrelated non-duration
  config outside the `durations` block.

# Security / Safety Considerations
- The scaled effective table must still satisfy the active timing invariants;
  otherwise a single convenient multiplier could push the runtime into invalid
  or contradictory duration relations.