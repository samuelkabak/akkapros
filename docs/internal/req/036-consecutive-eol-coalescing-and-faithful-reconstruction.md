---
req_id: REQ-036
status: Implemented
priority: Medium
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
related_adrs: 'ADR-040'
implemented_by: 'CR-070'
---

# Requirement: Consecutive EOL Coalescing and Faithful Reconstruction

## Summary

The system shall coalesce consecutive explicit newline events into one emitted
newline-owned pause row while preserving exact newline multiplicity in the
source-facing text field.

This requirement makes repeated end-of-line markers structurally lighter for the
phonetizer without losing reconstruction fidelity.

---

## Motivation

Multiple literal newlines currently overproduce separate newline-owned pause rows
even when the desired pause structure treats them as one event. The repository
needs a direct contract that keeps newline ownership separate from punctuation
ownership but preserves exact newline multiplicity for faithful reconstruction.

---

## Acceptance Criteria

- [ ] Given a maximal run of one or more adjacent newline characters, when Phase
      1 phone rows are built, then exactly one newline-owned long pause row is
      emitted for that run.
- [ ] Given a run of adjacent newlines, when the newline-owned row is emitted,
      then the row text contains one `<EOL>` token per consumed newline in order.
- [ ] Given `ba\nma` and `ba\n\n\nma`, when phone rows are emitted, then both
      streams contain the same count and placement of newline-owned pause rows.
- [ ] Given a newline-owned row whose text contains repeated `<EOL>` tokens,
      when reconstruction runs, then the reconstructed `_tilde` contains the
      same number of literal newlines.
- [ ] Given punctuation followed by one or more newlines, when phone rows are
      emitted, then punctuation ownership and newline ownership remain separate.

---

## User Story (optional)

> As a phonetizer user, I want repeated newlines to behave like one structural
> newline pause while preserving exact source multiplicity so that reconstruction
> remains faithful.

---

## Interface Notes

- Input: `_tilde` text with literal newline runs
- Output: phone rows with one newline-owned row per consecutive run and repeated
  `<EOL>` text tokens
- Affected components: `build_phone_rows()`, reconstruction helpers, phone docs

---

## Open Questions

- [ ] None at draft time.

---

## Implementation Notes (optional)

- Migration: update phone-row reconstruction and any docs/examples that assume
  one `<EOL>` token per newline-owned row.

## Related

- Related ADRs: [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Implementation CRs: [CR-070](../cr/070-coalesce-consecutive-eol-pause-rows-while-preserving-repeated-eol-text.md)

## Non-Goals

- Paragraph-specific pause semantics beyond newline-run coalescing
- Merging punctuation-owned and newline-owned pause rows into one event

## Security / Safety Considerations

- The reconstruction contract must remain lossless for newline multiplicity.
