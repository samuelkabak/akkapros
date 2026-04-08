---
req_id: REQ-025
status: Draft
priority: High
impact: Mutative
created: 2026-04-05
updated: 2026-04-08
related_adrs: 'ADR-040, ADR-039, ADR-004'
implemented_by: 'CR-039 and follow-up CRs'
---

# Requirement: Two-Phase Phonetizer Structure and Duration Pipeline

# Summary

The system shall provide a phonetizer program and associated phonetize library
that consume `<prefix>_tilde.txt` and operate in two strictly separated phases.

Phase 1 builds phone-row structure with all non-duration fields populated and
`duration=0000` for every row. It produces two row streams:

- original / deaccented phone rows
- accentuated phone rows

Phase 2 traverses those already-built row streams and updates `duration`
according to later timing algorithms specified by child requirements rather
than by this umbrella record alone.

The canonical output files for the two streams are:

- `<prefix>_ophone.txt` for the original stream
- `<prefix>_phone.txt` for the accentuated stream

This requirement reserves the full two-phase contract, while the first child CR
implements only Phase 1.

---

# Motivation

The new phonetize stage is intended to replace direct timing assumptions in
metrics and related downstream logic. To do that safely, the project needs a
stable structural intermediate that is complete before any timing realization is
applied.

That separation is critical because the duration algorithm must read already-
computed phone-row structure, including segment class, boundary codes,
accentuation state, and original-versus-accentuated stream identity. If the
project mixes structure building with duration assignment in one pass, later
timing experiments will be harder to validate and harder to compare.

The project also needs a deterministic way to derive the original stream from
the accentuated `_tilde` input without requiring a second upstream artifact.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given phonetizer input is `<prefix>_tilde.txt`, when the phonetizer is
      run, then it reads `_tilde` rather than requiring a separate original-text
      stage artifact.
- [ ] Given the phonetizer contract is implemented, when processing occurs,
      then it is defined as two phases: structure-first row generation and a
      later duration-realization pass.
- [ ] Given Phase 1 builds phone rows, when rows are emitted before duration
      realization, then every row has `duration=0000` and all other required
      fields are already populated.
- [ ] Given the phonetizer works from one accentuated `_tilde` input, when the
      original stream is derived, then it is obtained by removing `~` and
      replacing internal merge `&` with ordinary space while preserving lexical
      merge `+` and other retained input structure.
- [ ] Given the phonetizer emits its canonical artifacts, when output files are
      written, then the original stream is written to `<prefix>_ophone.txt` and
      the accentuated stream is written to `<prefix>_phone.txt`.
- [ ] Given Phase 2 is added later, when duration algorithms are applied, then
      they traverse prebuilt row streams instead of rebuilding the structure on
      the fly.
- [ ] Given detailed Phase 2 solver behavior is needed, when child timing
      requirements are added, then they narrow this umbrella record without
      changing the Phase 1 / Phase 2 architecture split.
- [ ] Given the phonetizer stage is testable, when automated tests are run,
      then extensive unit tests cover structural row generation and at least one
      automatic round-trip test reconstructs the relevant `_tilde` input from
      emitted phone rows.

---

# User Story (optional)
> As the maintainer of the phonetize redesign, I want structure generation and
> duration realization to be separate phases so that timing algorithms can be
> changed later without redefining the phone-row contract each time.

---

# Interface Notes
- Inputs:
  - `<prefix>_tilde.txt`
- Phase 1 outputs:
  - `<prefix>_ophone.txt`
  - `<prefix>_phone.txt`
- Phase 1 rule for deriving the original stream from accentuated `_tilde`:
  - remove `~`
  - replace `&` with space
  - preserve explicit lexical merge `+`
  - preserve syllable separator distinctions such as `·` and `-`
- Phase 2 scope is reserved but not yet specified here.
- The row schema itself is governed by child records such as CR-036.

Examples:

- accentuated `_tilde`: `u+ana&šar~.ri`
- derived original structure input: `u+ana šar.ri`

- accentuated `_tilde`: `šit·ku·nat-ma`
- derived original structure input: `šit·ku·nat-ma`

- accentuated `_tilde`: `gi.mir&dad~.mē`
- derived original structure input: `gi.mir dad.mē`

---

# Open Questions
- [x] Detailed Phase 2 local-solver behavior is narrowed by
      [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md).
- [ ] Will Phase 2 update the Phase 1 files in place or regenerate them from
      the same row lists before final writeout?
- [x] Phase 1 can be implemented independently before Phase 2 is finalized.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium to large
- Child CR strategy:
  - first child CR implements Phase 1 only
      - later child CRs add duration realization over the same row structure
      - [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
            is the current detailed Phase 2 local-solver requirement

# Related
- Related ADRs: [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md), [ADR-039](../adr/039-replacement-of-timing-model.md), [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md)
- Implementation CRs: [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- Child timing REQs: [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md)

# Non-Goals
- This requirement does not define the detailed local Phase 2 duration formulas
      itself; those belong in child requirements such as
      [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md).
- This requirement does not change the already-approved `_phone` row schema.
- This requirement does not replace `_tilde` as the phonetizer input artifact.

# Security / Safety Considerations
- The original stream must be derived deterministically from the accentuated
  stream so tests can verify behavior without hidden side inputs.
- The two-phase split should prevent partially timed rows whose structure is not
  yet stable or reproducible.