---
req_id: REQ-039
status: Draft
priority: Medium
impact: Additive
created: 2026-04-18
updated: 2026-04-18
related_adrs: 'ADR-031, ADR-040'
implemented_by: 'CR-073'
---

# Requirement: Probability-Oriented Phonetizer Diagnostic Reporting

# Summary

The phonetizer shall emit denominator-aware diagnostic statistics so timing
recovery events can be interpreted as frequencies over a known population, not
just as isolated raw counts.

This requirement adds reporting only. It does not change the timing algorithm.

---

# Motivation

Raw counts such as drift-extension events are difficult to interpret without an
explicit denominator, especially when the obvious available count is a row count
from a different population.

---

# Acceptance Criteria

- [ ] Given the phonetizer reports an event count, when that count is intended
      to support probability-style interpretation, then the emitted metadata also
      includes the correct denominator and derived rate.
- [ ] Given post-unit drift extension reporting is emitted, when the stream is
      finalized, then count, denominator, and rate are all present.
- [ ] Given ordinary vowel chrono correction occurs, when diagnostics are
      emitted, then the output exposes how often that correction happened over a
      clearly defined population.
- [ ] Given mini-pause recovery or pause residual carry occurs, when diagnostics
      are emitted, then the output exposes those event frequencies over clearly
      named populations.
- [ ] Given a denominator is emitted, when the field is documented, then the
      affected population is stated explicitly.

---

# User Story (optional)
> As a research-facing user, I want phonetizer diagnostics to be interpretable as
> probabilities or rates so I can compare solver behavior across configurations.

---

# Interface Notes
- Input: Phase 2 realization events and existing front matter stage data
- Output: additional count/denominator/rate diagnostics in phonetizer metadata
- Affected components: phonetizer report object, front matter, metrics docs,
  test fixtures

---

# Open Questions
- [ ] Whether some rates should use all-unit denominators or narrower
      eligibility denominators should be decided explicitly per field.

---

# Implementation Notes (optional)
- Migration: preserve existing raw counts where useful for debugging.

# Related
- Related ADRs: [ADR-031](../adr/031-factual-runtime-records-and-structured-self-test-output.md), [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Implementation CRs: [CR-073](../cr/073-add-probability-oriented-phonetizer-diagnostic-statistics.md)

# Non-Goals
- Replacing the row-level drift column
- Introducing segment-by-segment drift as a new metric

# Security / Safety Considerations
- Misaligned denominators are a research-integrity risk because they invite
  false probability interpretations.
