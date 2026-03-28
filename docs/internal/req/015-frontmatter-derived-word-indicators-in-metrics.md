---
req_id: REQ-015
status: Implemented
priority: High
impact: Mutative
created: 2026-03-27
updated: 2026-03-28
---

# Requirement: Frontmatter-Derived Word Indicators in Metrics

# Summary

The system shall add three frontmatter-derived word indicators to metrics
outputs in both supported formats, table/text and JSON, under a dedicated
`Prominence statistics` section for the `ORIGINAL` section only:

- `Function words: <number> words`
- `Explicitly linked words: <number> words`
- `Prominence candidates: <number> words`

In JSON, the canonical field names shall be:

- `function_word_count`
- `explicit_word_link_count`
- `prominence_candidate_word_count`

The required counts shall be sourced from input front matter rather than
reconstructed from `_tilde.txt`.

---

# Motivation

Metrics outputs need compact lexical-eligibility indicators that help interpret
word statistics in both original and accentuated views. The metrics stage
cannot faithfully reconstruct explicit user word links from `_tilde.txt`, and
function-word counts can also be propagated more reliably through front matter.

Legalizing these fields through the front matter contract keeps the pipeline
consistent with `REQ-013` and avoids reviving the rejected lex-input design.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given metrics table/text output, when `Prominence statistics` is
      rendered, then it contains `Function words`, `Explicitly linked words`,
      and `Prominence candidates` in the `ORIGINAL` section.
- [ ] Given metrics JSON output, when `prominence_statistics` is rendered for
      the `original` section, then it contains the fields
      `function_word_count`, `explicit_word_link_count`, and
      `prominence_candidate_word_count`.
- [ ] Given metrics JSON output, when the new fields are emitted, then they
      appear only under `original.prominence_statistics` and are not mirrored
      elsewhere for compatibility.
- [ ] Given metrics computation, when `Function words` is populated, then it is
      read from input front matter.
- [ ] Given metrics computation, when `Explicitly linked words` is populated,
      then it is read from input front matter using the canonical
      `explicit_word_link_count` field.
- [ ] Given metrics computation, when `Prominence candidates` is populated in
      the `ORIGINAL` section, then it equals
      `Total words - Function words - Explicitly linked words`.
- [ ] Given required front matter values are missing, when metrics runs, then
      the stage fails clearly rather than inventing values from `_tilde.txt`.
- [ ] Given built-in self-tests, when `run_tests()` is executed, then the new
      numeric outputs are covered.
- [ ] Given pytest regression coverage, when the new feature is implemented,
      then exact table/text and JSON values are asserted.
- [ ] Given metrics documentation, when word-statistic outputs are documented,
      then the new fields and their front matter dependency are described.
- [ ] Given this requirement is implemented, when documentation is updated,
      then user-facing docs describe the new metrics fields and developer-facing
      docs describe the front matter dependency and output placement rules.
- [ ] Given this requirement is implemented, when tests are updated, then
      built-in `run_tests()` coverage and pytest coverage both exercise the new
      fields, missing-front-matter failures, and representative integration
      flows.

---

# User Story (optional)
> As a researcher reading metrics outputs, I want frontmatter-derived lexical
> indicators in a dedicated `Prominence statistics` section so that I can
> interpret prominence-relevant word classes without mixing them into general
> word statistics or relying on reconstruction from transformed pivot text.

---

# Interface Notes
- Input: `<prefix>_tilde.txt` with required front matter values available to
  the metrics stage.
- Output: `<prefix>_metrics.txt`, `<prefix>_metrics.json`, with the new fields
      placed in `Prominence statistics` / `prominence_statistics` for `ORIGINAL`.
- Affected components: `src/akkapros/lib/metrics.py`,
  `src/akkapros/cli/metricalc.py`, `docs/akkapros/metrics-computation.md`,
  `docs/akkapros/metricalc.md`.

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration: downstream JSON consumers should be informed that new
      `prominence_statistics` keys will appear only in that location because
      these changes target release v3.

# Related
- Related ADRs: [ADR-010](../adr/010-metrics-from-text-and-dual-percent-v.md),
  [ADR-027](../adr/027-yaml-front-matter-for-cli-pipeline-files.md)
- Related REQs: [REQ-012](012-metrics-output-structure-and-layout.md),
  [REQ-013](013-cli-file-front-matter-and-metadata-propagation.md),
  [REQ-014](014-remove-metrics-csv-output.md)
- Implementation CRs: [CR-022](../cr/022-add-frontmatter-derived-word-indicators-to-metrics.md)

# Non-Goals
- This requirement does not add CSV output support for these indicators.
- This requirement does not authorize reconstruction of explicitly linked-word
  counts from `_tilde.txt`.
- This requirement does not change the underlying metrics algorithms beyond the
  addition of these output fields.
- This requirement does not add compatibility mirrors outside
      `original.prominence_statistics`.

# Security / Safety Considerations
- Metrics must treat front matter as untrusted input and fail predictably when
  required keys are missing or malformed.
