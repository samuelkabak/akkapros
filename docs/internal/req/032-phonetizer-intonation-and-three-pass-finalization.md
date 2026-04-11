---
req_id: REQ-032
status: Implemented
priority: High
impact: Mutative
created: 2026-04-11
updated: 2026-04-11
related_adrs: 'ADR-045, ADR-043, ADR-040'
implemented_by: 'CR-050'
---

# Requirement: Phonetizer Intonation and Three-Pass Finalization

# Summary

The phonetizer shall finalize its active phone-row artifacts in three ordered
passes: structure, duration, and intonation.

Pass 1 builds the row streams and fills every required row field except
`duration` and final `intonation`. Pass 2 traverses those prebuilt rows and
fills `duration` only. Pass 3 traverses the duration-bearing rows and fills
`intonation` only, using pause type as the cause-side signal for phrase-level
intonation. In the current implementation scope, that cause is realized on the
last syllable before the pause, while leaving room for later phrase-spread
models.

The pause-type inventory includes `Q`, `S`, `E`, `C`, and `I`, where `I`
means an internal or sanitizing pause that carries no clause-final intonation
override.

The finalized `_phone.txt` and `_ophone.txt` artifacts shall therefore carry
both duration and intonation, and MBROLA `.pho` output shall be derived entirely
from those finalized phone rows plus `f0`.

---

# Motivation

The repository already established structure-first phonetizer rows and later
row-traversal duration realization. Intonation introduces a broader contextual
operation: it depends on syllables and silences, and its trigger is pause type.
That is wider than one phoneme and should not be collapsed into either source-
side row construction or duration realization.

This requirement is needed to formalize intonation as a whole phonetizer
contract rather than as a small set of pitch scalars. It is also needed to keep
MBROLA export derived from the finalized phone table rather than allowing a
separate pitch system to drift away from the row contract.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the active phonetizer architecture is inspected, when pass ordering
      is described, then it is defined as exactly three ordered passes:
      structure, duration, and intonation.
- [ ] Given Pass 1 runs, when row streams are materialized, then it fills all
      required row fields except `duration` and final `intonation`.
- [ ] Given Pass 2 runs, when row streams are traversed, then it fills
      `duration` only and does not assign final row-level intonation.
- [ ] Given Pass 3 runs, when row streams are traversed, then it fills
      `intonation` only and does not recompute structure or duration.
- [ ] Given Pass 2 or Pass 3 runs, when they inspect upstream data, then they
      do not consult `_tilde`, raw source text, or punctuation reparsing after
      Pass 1 has materialized the rows.
- [ ] Given a pause row is present, when its role is interpreted, then its
      silence subtype is treated as the cause-side signal for preceding-phrase
      intonation.
- [ ] Given the current implementation scope is applied, when a clause-final
      contour is realized, then the consequence is assigned to the last
      syllable before the pause rather than to the whole phrase.
- [ ] Given future models later widen intonation spread, when they are added,
      then they may change the consequence mapping while preserving pause type
      as the cause-side contract.
- [ ] Given the current scope realizes clause-final intonation on the last
      syllable, when that syllable is not stressed, then the clause-final
      contour applies directly without stress conflict.
- [ ] Given the current scope realizes clause-final intonation on the last
      syllable, when that syllable is stressed in an edge case, then the
      clause-final intonation supersedes the ordinary stress color.
- [ ] Given the intonation config surface is inspected, when approved keys are
      listed, then they are exactly `f0`, `stress`, `question`, `statement`,
      `exclamation`, and `continuation` under
      `phonetize.process.intonation`.
- [ ] Given compact config values such as `H2`, `L2`, `M0`, `R1`, `F1`, `P2`,
      or `V2` are supplied, when they are normalized for finalized rows, then
      they become canonical row tokens with the only legal shape suffix.
- [ ] Given finalized phone rows are serialized, when the row schema is
      inspected, then the schema contains the added `intonation` field and
      still keeps `duration` as a four-digit field.
- [ ] Given spaces separate words in phonetizer input, when rows are built,
      then spaces alone do not emit silence rows.
- [ ] Given punctuation or explicit line breaks create pauses, when rows are
      built, then they emit typed silence rows that survive into Pass 3.
- [ ] Given pause rows are typed, when clause-final mapping is applied, then
      `Q`, `S`, `E`, and `C` select their corresponding intonation presets and
      `I` applies no clause-final override.
- [ ] Given a pause row has type `I`, when Pass 3 assigns intonation, then that
      pause contributes no clause-final contour and the preceding phrase keeps
      only whatever non-pause-driven intonation would otherwise apply.
- [ ] Given MBROLA `.pho` output is generated, when its source is traced, then
      it is derived entirely from finalized phone rows plus
      `phonetize.process.intonation.f0`.
- [ ] Given MBROLA `.pho` output is generated, when pitch targets are emitted,
      then the contract allows a variable-length pitch-target tail consistent
      with the row's intonation token family.
- [ ] Given MBROLA pitch targets are emitted on one phoneme line, when their
      timing is interpreted, then they are assumed to be evenly spaced over the
      phoneme duration and linearly interpolated between adjacent targets.
- [ ] Given the test contract for this redesign is reviewed, when coverage is
      planned, then it includes both a substantial unit-test layer and a
      substantial integration-test layer.
- [ ] Given unit tests are added for this requirement, when the suite is
      reviewed, then it includes at least the following groups:
      token normalization, token validation, pause typing, punctuation
      precedence, pass-order discipline, row serialization/parsing, last-
      syllable consequence assignment, and MBROLA pitch-target derivation.
- [ ] Given integration tests are added for this requirement, when the suite is
      reviewed, then it includes at least the following groups: finalized
      `_phone`/`_ophone` row-shape verification, representative question /
      statement / exclamation / continuation / internal pause cases, and `.pho`
      derivation from finalized rows.

---

# User Story (optional)
> As the maintainer of the phonetizer, I want intonation to be realized in a
> third independent pass so that phrase-sensitive pitch behavior can evolve
> without corrupting row construction or duration logic.

---

# Interface Notes
- Input artifact: `<prefix>_tilde.txt` for Pass 1 only.
- Finalized row artifacts:
  - `<prefix>_ophone.txt`
  - `<prefix>_phone.txt`
- Finalized row schema includes `intonation` in addition to the existing row
  fields.
- Pause-type interface inventory: `Q`, `S`, `E`, `C`, `I`.
- `.pho` output is derived from finalized rows, not from upstream text.
- Affected components:
  - phonetizer library and CLI
  - phone-row serializer/parser
  - config verification and default config docs
  - `.pho` exporter
  - phonetizer unit and integration tests

---

# Open Questions
- [x] Pause rows with `Q`, `S`, `E`, and `C` carry the same contour token as
      the governed final syllable in the accentuated stream. Resolved on
      2026-04-11 by CR-050 implementation.
- [x] The original stream remains entirely neutral in Phase 3 for the current
      implementation scope. Resolved on 2026-04-11 by CR-050 implementation.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: large
- Migration: downstream row readers, docs, and tests must be updated together
  because the finalized row schema gains one field and the phonetizer pass
  architecture changes from two to three.

# Related
- Related ADRs: [ADR-045](../adr/045-three-pass-phonetizer-intonation-and-row-derived-mbrola.md), [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md), [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Implementation CRs: [CR-050](../cr/050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)

# Non-Goals
- This requirement does not implement production code.
- This requirement does not force the current implementation to spread
  intonation across the whole phrase; it only preserves that possibility.
- This requirement does not redesign duration formulas or pause-band values.
- This requirement does not specify automatic lexical expansion for unsupported
  punctuation symbols.

# Security / Safety Considerations
- Separating intonation into Pass 3 reduces the risk of duration bugs caused by
  pitch logic and reduces the risk of pitch logic depending on unstable
  structure.
- Requiring `.pho` derivation from finalized rows avoids divergence between the
  phone-table contract and emitted speech-synthesis artifacts.
