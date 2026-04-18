---
req_id: REQ-040
status: Implemented
priority: High
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
related_adrs: 'ADR-049, ADR-046, ADR-041, ADR-040'
implemented_by: 'CR-074'
---

# Requirement: Accentuation-First Long-Vowel Recovery and Accent-Sensitive Bounds

# Summary

On accent-bearing syllables, the phonetizer shall apply accentuation before any
long-vowel chrono cleanup and shall use accent-sensitive long-vowel recovery
bounds.

Ordinary non-accented long-vowel cleanup remains a narrower, tolerance-gated
operation. Accent-bearing long-vowel cleanup uses the broader elongated range
because accentuation has already moved the vowel beyond the ordinary category
barrier.

---

# Motivation

If ordinary long-vowel cleanup runs before accentuation, it can consume timing
space that should first be available to the accentuation process. The system
also needs one explicit rule for how the legal recovery range differs between
ordinary non-accented long vowels and accent-bearing long vowels.

---

# Acceptance Criteria

- [x] Given a syllable is accent-bearing, when Phase 2 realizes it, then the
      order is baseline assignment, accentuation, then any long-vowel cleanup.
- [x] Given a syllable is not accent-bearing, when long-vowel cleanup is
      considered, then the long-vowel recovery range is from
      `vowels.perception_limits.long_min` up to
      `vowels.perception_limits.very_long_min - 1`.
- [x] Given a syllable is accent-bearing with a long vowel model `CVV:` or
      `CVV:C`, when post-accent long-vowel cleanup is considered, then the legal
      recovery range extends up to `vowels.perception_limits.elongation_max`.
- [x] Given a syllable is accent-bearing with model `C:V` or `CVC:`, when
      long-vowel cleanup rules are evaluated, then the long-vowel cleanup path
      is not applicable because those models have no long vowel.
- [x] Given a non-accent-bearing long vowel, when absolute drift does not exceed
      `drift_tolerance`, then ordinary long-vowel cleanup does not modify the
      vowel.
- [x] Given a non-accent-bearing long vowel and absolute drift exceeds
      `drift_tolerance`, when ordinary long-vowel cleanup runs, then it attempts
      to reduce drift toward zero within the legal ordinary long-vowel range
      rather than merely trimming mismatch down to the tolerance limit.
- [x] Given an accent-bearing long vowel in `CVV:` or `CVV:C`, when post-accent
      cleanup runs, then activation is not gated by the ordinary
      `drift_tolerance` threshold and the solver may use the broader elongated
      range to reduce drift.
- [x] Given pause rows are realized, when pause discharge runs, then pauses
      continue to target zero-drift discharge according to their existing pause
      logic; this requirement does not weaken pause recovery.

---

# User Story (optional)
> As a user studying accent-bearing long vowels, I want accentuation to take
> precedence over ordinary chrono cleanup so the accent process is not weakened
> by earlier long-vowel adjustment.

---

# Interface Notes
- Input: Phase 2 syllable realization state, accent-bearing syllable model, and
  long-vowel perception limits
- Output: reordered solver behavior with accent-sensitive long-vowel cleanup
  bounds
- Affected components: phonetizer Phase 2 solver, phonetizer algorithm docs,
  unit/integration/regression tests

---

# Open Questions
- [x] None at draft time.

---

# Implementation Notes (optional)
- Migration: expect gold phone/ophone and downstream metrics outputs to refresh
  because timing values may change for accent-bearing long-vowel cases.
- Implemented by CR-074 with updated unit, integration, metrics-reference, and
      flowchart-sync coverage.

# Related
- Related ADRs: [ADR-049](../adr/049-accentuation-first-long-vowel-recovery-and-accent-sensitive-bounds.md), [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md), [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md), [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Implementation CRs: [CR-074](../cr/074-apply-accentuation-before-ordinary-long-vowel-drift-recovery.md)

# Non-Goals
- Changing the fixed half-foot accent target itself
- Renaming phonetizer reporting fields

# Security / Safety Considerations
- Solver-order changes must be documented and tested explicitly so downstream
  timing changes are understood rather than treated as accidental drift.
