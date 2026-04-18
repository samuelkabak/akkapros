---
req_id: REQ-038
status: Implemented
priority: Medium
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
related_adrs: 'ADR-031'
implemented_by: 'CR-072'
---

# Requirement: Post-Unit Drift Reporting Label Clarity

## Summary

Phonetizer drift-reporting labels shall identify the reported quantity as
post-unit drift rather than leaving the unit semantics ambiguous.

This requirement is label-only. It does not change the meaning, sampling, or
numeric values of the existing drift-reporting quantities.

---

## Motivation

The current phonetizer report already represents completed-unit drift history,
but the shortest labels such as `drift_extension_count` do not say whether the
reported quantity is segmental, syllable-final, or broader post-unit drift.

---

## Acceptance Criteria

- [x] Given phonetizer front matter is emitted, when drift-reporting fields are
      named, then the names identify the quantity as post-unit drift.
- [x] Given user-facing report headings or table labels expose the same values,
      when they are rendered, then the labels use `Post-unit drift` wording.
- [x] Given the rename is applied, when the same input is processed, then the
      numeric values remain unchanged.
- [x] Given the row-level flat file column remains named `drift`, when public
      docs describe it, then they state explicitly that it is the post-unit
      drift token.

---

## User Story (optional)
> As a reader of phonetizer outputs, I want drift-reporting labels to say they
> are post-unit values so I do not mistake them for segment-level timing traces.

---

## Interface Notes
- Input: phonetizer report object and emitted front matter
- Output: renamed metadata keys and user-facing labels
- Affected components: phonetizer/front matter docs, report rendering, metrics
  consumption of phonetizer drift summary

---

## Open Questions
- [x] None at draft time.

---

## Implementation Notes (optional)
- Migration: document any temporary backward-compat aliases explicitly if they
  are needed during rollout. `metricalc` keeps a legacy read fallback for older
  phone artifacts that still carry `metadata.data.phonetize.drift`, while newly
  emitted metadata uses only the `post_unit_drift` names.

## Related
- Related ADRs: [ADR-031](../adr/031-factual-runtime-records-and-structured-self-test-output.md)
- Implementation CRs: [CR-072](../cr/072-rename-drift-reporting-to-post-unit-drift.md)

## Non-Goals
- Introducing a new segment-level drift metric
- Changing drift math or solver behavior

## Security / Safety Considerations
- Metadata renames must not create ambiguous dual long-term contracts.
