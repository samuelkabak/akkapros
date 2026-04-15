---
req_id: REQ-034
status: Implemented
priority: High
impact: Mutative
created: 2026-04-15
updated: 2026-04-15
related_adrs: ''
implemented_by: 'CR-062'
---

# Requirement: Pipe-Delimited Phone/Ophone Rows and Signed Drift Token

# Summary

The system shall standardize the row contract used by phone and ophone files.

Both files shall use one unified field separator, the pipe character (`|`), and
shall serialize row drift using an arithmetic sign plus three zero-padded
digits (for example `-012`, `+000`, `+054`).

This requirement applies to row production and row consumption across the
pipeline components that read or write phone/ophone files.

---

# Motivation

Current phone/ophone rows use mixed delimiters (`-` inside the structural head
and `:` before the text tail). The mixed shape increases parser complexity and
makes manual inspection less consistent.

A single separator (`|`) makes the schema easier to parse and validate. Signed
numeric drift tokens make drift direction explicit with normal arithmetic
conventions and avoid letter-coded interpretation.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given a phonetizer row is emitted to phone/ophone output, when the row is
      serialized, then fields are emitted in this order with pipe separators:
      `label|category|type|length|position|boundary|accent|realization|duration|drift|intonation|text`.
- [ ] Given a row is emitted, when `drift` is serialized, then its token format
      is exactly `[+-][0-9]{3}`.
- [ ] Given the drift is exactly zero, when serialized, then the token is
      `+000`.
- [ ] Given the stream is ahead of beat by `n` ms, when serialized, then drift
      is `-nnn` (zero-padded to three digits).
- [ ] Given the stream is behind beat by `n` ms, when serialized, then drift is
      `+nnn` (zero-padded to three digits).
- [ ] Given metricalc and printer consume phone/ophone rows, when parsing rows,
      then they accept the pipe-delimited schema without relying on legacy
      `-`/`:` splitting.
- [ ] Given repository tests are run after implementation, when phone-row
      parsing/emission tests execute, then all relevant tests pass using the
      new format.
- [ ] Given user-facing docs and demos are updated, when row examples are
      displayed, then examples use pipe-separated rows and signed drift tokens.
- [ ] Given a computed drift magnitude exceeds 999 ms, when row serialization is
      attempted, then processing fails fast (no clamping).

---

# User Story (optional)
> As a maintainer and researcher reading phone/ophone rows, I want one stable
> delimiter and arithmetic drift tokens so that parsing and validation are
> simpler and less error-prone.

---

# Interface Notes
- Input: phone/ophone row lines in unified form
  `label|category|type|length|position|boundary|accent|realization|duration|drift|intonation|text`
- Output: canonical parsed row objects consumed by metrics/printer pipeline
- Affected components:
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/lib/metrics.py`
  - `src/akkapros/lib/print.py`
  - `src/akkapros/cli/metricalc.py`
  - `src/akkapros/cli/printer.py`

---

# Open Questions
- [ ] Should separator and drift-token validation errors include line numbers in
      all consumers?

---

# Implementation Notes (optional)
- Owner: maintainer
- Estimated effort: medium
- Migration: no backward-compatibility obligation for legacy row separators.
- Drift magnitude policy: absolute drift values above 999 ms are invalid and
      must fail fast.

# Related
- Related ADRs: none yet
- Implementation CRs: [CR-062](../cr/062-unify-phone-ophone-row-separator.md)

# Non-Goals
- This requirement does not change non-phone artifacts such as `.pho`.
- This requirement does not redesign timing-model mathematics.
- This requirement does not add a conversion utility for legacy files.

# Security / Safety Considerations
- Enforce strict schema validation to avoid silent parsing drift when malformed
  rows are encountered.
