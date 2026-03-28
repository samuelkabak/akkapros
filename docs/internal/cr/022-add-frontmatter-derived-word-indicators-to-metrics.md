# Change Request: Add frontmatter-derived word indicators to metrics outputs

CR-ID: CR-022
Status: Done
Priority: High
Impact: Mutative
Created: 2026-03-27
Updated: 2026-03-28
Implements: REQ-015
---

# Summary

Add three new word-level indicators to metrics outputs in both supported output
formats, table/text and JSON, under a separate `Prominence statistics`
section in the `ORIGINAL` section only:

- `Function words: <number> words`
- `Explicitly linked words: <number> words`
- `Prominence candidates: <Total words - Function words - Explicitly linked words> words`

The counts for `Function words` and `Explicitly linked words` shall be obtained
from input front matter rather than reconstructed from `_tilde.txt`.

In JSON, use these exact field names:

- `function_word_count`
- `explicit_word_link_count`
- `prominence_candidate_word_count`

---

# Motivation

Current metrics outputs do not expose lexical eligibility indicators that are
useful for interpreting prominence and grouping behavior. Researchers need these
counts in the same place they inspect other word statistics.

The explicitly linked-word count is not computable faithfully from `_tilde.txt`,
and function-word counts can also be sourced more reliably from front matter.
Using front matter keeps the metrics stage aligned with the approved metadata
propagation design instead of reviving the rejected lex-input approach.

---

# Scope

## Included

- Add the three new fields to a dedicated `Prominence statistics` section in
  metrics table/text output.
- Add the same three fields to a dedicated `prominence_statistics` object in
  metrics JSON output.
- Populate the three fields in the `ORIGINAL` section only.
- Keep the new JSON fields only in `original.prominence_statistics` with no
  compatibility mirroring elsewhere.
- Read `function_word_count` and `explicit_word_link_count` from input front
  matter.
- Compute `Prominence candidates` as:
  `Total words - Function words - Explicitly linked words`.
- Add unit tests via built-in `run_tests()` coverage.
- Add pytest regression tests for exact numeric outputs.
- Update metrics documentation to describe the new fields and their front
  matter dependency.

## Not Included

- CSV output changes. CSV is excluded because it is being removed by `REQ-014`
  and `CR-021`.
- Any attempt to reconstruct explicitly linked-word counts from `_tilde.txt`.
- Any compatibility mirror of the new JSON fields outside
  `original.prominence_statistics`.
- Any change to the underlying metrics algorithms beyond the added counters.

---

# Current Behavior

Metrics outputs currently lack a dedicated prominence-focused subsection for
function words, explicit user word links, and prominence candidates in the
`ORIGINAL` section. The metrics stage does not yet consume these values from
input front matter.

---

# Proposed Change

1. Add a `Prominence statistics` section in the `ORIGINAL` section containing:
   - `Function words`
   - `Explicitly linked words`
   - `Prominence candidates`

2. Data source rules:
   - `Function words` is read from input front matter.
   - `Explicitly linked words` is read from input front matter using the
     canonical `explicit_word_link_count` field.
   - `Prominence candidates = Total words - Function words - Explicitly linked words`.

3. Output scope:
   - table/text metrics output: add the three lines in a separate
     `Prominence statistics` section for the `ORIGINAL` section;
   - JSON metrics output: add `function_word_count`,
     `explicit_word_link_count`, and `prominence_candidate_word_count` in a
     separate `prominence_statistics` object in the `original` section;
   - CSV: no change, because CSV is being removed.

4. Validation requirement:
   - if required front matter values are missing, metrics must fail clearly
     rather than inventing values from `_tilde.txt`.

---

# Technical Design

Architecture notes:

Components:
- metrics CLI surface in `src/akkapros/cli/metricalc.py`
- metrics computation / serialization logic in `src/akkapros/lib/metrics.py`
- front matter parsing support introduced by `REQ-013` / `CR-018`

Data contract:
- read `function_word_count` and `explicit_word_link_count` from the input
  front matter for the metrics stage
- compute `prominence_candidates` deterministically from those values and total
  word count already present in metrics

Output mapping:
- table/text: append three lines under a separate `Prominence statistics`
  section in the `ORIGINAL` section
- JSON: add `function_word_count`, `explicit_word_link_count`, and
  `prominence_candidate_word_count` in the `original` section under
  `prominence_statistics`

Failure behavior:
- metrics must not infer `explicitly linked words` from `_tilde.txt`
- if front matter is absent or missing required keys, the behavior must follow
  the approved front matter validation policy and fail clearly

---

# Files Likely Affected

`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/metricalc.md`
tests covering metrics `run_tests()` and pytest regression outputs

---

# Acceptance Criteria

- [ ] Table/text metrics output contains `Function words`, `Explicitly linked
  words`, and `Prominence candidates` under a separate `Prominence
  statistics` section in the `ORIGINAL` section.
- [ ] JSON metrics output contains `function_word_count`,
  `explicit_word_link_count`, and `prominence_candidate_word_count` in
  the `original.prominence_statistics` object.
- [ ] The new JSON fields appear only in `original.prominence_statistics` and
  are not duplicated elsewhere for compatibility.
- [ ] `Explicitly linked words` is sourced from input front matter and not
      reconstructed from `_tilde.txt`.
- [ ] `Function words` is sourced from input front matter.
- [ ] `Prominence candidates` equals `Total words - Function words - Explicitly
  linked words` in the `ORIGINAL` section.
- [ ] Built-in `run_tests()` coverage includes the new numeric outputs.
- [ ] Pytest regression tests verify exact values for the new fields.
- [ ] Metrics documentation is updated to describe the new fields and their
  dependency on input front matter and their placement in `Prominence
  statistics`.
- [ ] User-facing documentation explains the new metrics fields and their
  interpretation.
- [ ] Developer-facing documentation explains the front matter dependency,
  JSON placement rule, and failure behavior when required metadata is
  missing.

---

# Risks / Edge Cases

Possible issues:

- Metrics now depends on front matter values being present and correct.
- Historical inputs without front matter cannot support these counters unless a
  migration policy is defined elsewhere.
- Downstream JSON consumers will see a new `prominence_statistics` object and
  may need schema updates.

---

# Testing Strategy

Unit tests:

- add `run_tests()` coverage for frontmatter-derived `Function words`
- add `run_tests()` coverage for frontmatter-derived `Explicitly linked words`
- add `run_tests()` coverage for `Prominence candidates` formula correctness
- add `run_tests()` coverage for missing-front-matter failure behavior

Pytest regression tests:

- assert exact table/text lines for the `Prominence statistics` section in
  `ORIGINAL`
- assert exact JSON numeric fields for the `original.prominence_statistics`
  object
- assert failure behavior when required front matter keys are absent
- assert representative integration behavior in pipeline flows where metrics
  consumes front matter produced upstream

---

# Rollback Plan

Remove the new word-statistic fields from metrics outputs and restore the prior
metrics schema if this addition must be withdrawn.

---

# Related Issues

- Depends on [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md)
  and [CR-018](018-add-cli-file-front-matter-and-metadata-propagation.md) for
  front matter availability.
- Legalized by [REQ-015](../req/015-frontmatter-derived-word-indicators-in-metrics.md).
- Adjacent to [REQ-012](../req/012-metrics-output-structure-and-layout.md) and
  [CR-019](019-metrics-deltac-meanc-dual-lines-and-varcoc-unitless.md) for
  metrics output contract work.
- Intentionally replaces the rejected `_lex.txt` path recorded in
  [CR-020](020-metrics-word-stats-lex-input.md).
- Compatible with CSV removal specified by
  [REQ-014](../req/014-remove-metrics-csv-output.md) and
  [CR-021](021-remove-metrics-csv-output.md).

---

# Tasks

## Implementation

- [ ] Read the required counts from metrics input front matter.
- [ ] Add the three fields to table/text metrics output.
- [ ] Add the three fields to JSON metrics output.
- [ ] Fail clearly if required front matter values are missing.

## Tests

- [ ] Add built-in `run_tests()` coverage.
- [ ] Add pytest regression tests for exact numbers and failure behavior.

## Documentation

- [ ] Update metrics docs for the new word indicators.
- [ ] Update developer-facing docs for the front matter dependency and JSON
  placement contract.
- [ ] Document that these counters come from front matter, not `_tilde.txt`.
- [ ] Document that they appear in `Prominence statistics`, separate from
  `Word statistics`.

## Review

- [ ] Confirm that the indicators remain restricted to the `ORIGINAL` section
  only.
- [ ] Confirm that no compatibility mirror is introduced outside
      `original.prominence_statistics`.

---

# Notes for CR-022

This CR adds new output fields but does not authorize reconstruction of missing
lexical metadata from `_tilde.txt`. The design intentionally prefers explicit
front matter provenance over inference.
