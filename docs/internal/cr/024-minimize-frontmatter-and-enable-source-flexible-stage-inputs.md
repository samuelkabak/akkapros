---
cr_id: CR-024
status: Done
priority: High
impact: Mutative
created: 2026-03-29
updated: 2026-03-29
implements: 'REQ-017, ADR-027, ADR-028, ADR-029, ADR-031'
---

# Change Request: Minimize Frontmatter and Enable Source-Flexible Stage Inputs

# Summary

Reduce serialized stage metadata in pipeline frontmatter so each stage no
longer verifies or republishes counters it can compute from the real content
body. Extend the syllabifier so it can process non-ATF-parser inputs without
frontmatter, while preserving an optional `file.title` through either inherited
frontmatter or a new `--title` override.

For metrics, keep only `explicit_word_link_count` as required inherited
prosody-stage data, add a CLI override `--explicit-link-count`, and move all
other relevant counters to internal computation plus logger output. Update the
pipeline orchestrator, printer behavior, and manuals so the new option surface
and reduced frontmatter contract are carried consistently. Metrics and printer
outputs do not republish `metadata.data` in their own front matter.

The supported minimal path for this CR is
`syllabify -> prosmaker -> (metricalc or printer)`. Only `syllabify` gains
content-only input compatibility in this change.

This CR is additive to the historical record and narrows limited parts of
[CR-018](018-add-cli-file-front-matter-and-metadata-propagation.md) and
[CR-022](022-add-frontmatter-derived-word-indicators-to-metrics.md) without
rewriting those completed documents.

---

# Motivation

The current frontmatter payload contains repeated counters that are both noisy
and fragile. Those counters create hard dependencies between stages even when a
later stage already has the authoritative body text needed to recompute them.

That coupling blocks a practical workflow: using the syllabifier on text that
did not originate in `atfparser`. It also makes metrics more dependent on
frontmatter than necessary, even though only explicit user links cannot always
be reconstructed from transformed text.

---

# Scope

## Included

- Remove `metadata.data.atfparse.line_count` from `atfparser` output
  frontmatter.
- Log the `atfparser`-computed line count through the shared logger.
- Stop `syllabify` from reading or verifying
  `metadata.data.atfparse.line_count`.
- Add `syllabify --title STRING` and define it as an override for inherited or
  missing `file.title`.
- Allow `syllabify` to accept input files that contain no frontmatter.
- Stop `syllabify` from serializing `metadata.data.syllabify.word_count` and
  `metadata.data.syllabify.syllable_count`.
- Log `syllabify`-computed `line_count`, `word_count`, and `syllable_count`.
- Stop `prosmaker` from reading or verifying inherited `atfparse` and
  `syllabify` counters.
- Reduce serialized `metadata.data.prosody` to
  `explicit_word_link_count` only.
- Log `prosmaker`-computed `line_count`, `word_count`, `syllable_count`,
  `function_word_count`, `prosodic_unit_count`, and
  `accentuated_syllable_count`.
- Stop `metricalc` from reading or verifying inherited `atfparse`,
  `syllabify`, and non-link `prosody` counters.
- Restrict `metricalc` frontmatter consumption to `file.title` and
  `metadata.data.prosody.explicit_word_link_count`.
- Remove `metadata.data` from `metricalc` output frontmatter for both
  `_metrics.txt` and embedded JSON `frontmatter`.
- Add `metricalc --explicit-link-count INTEGER` as an override for inherited
  explicit-link metadata.
- Validate `metricalc --explicit-link-count` as an integer constrained to
  `0 <= explicit_link_count <= word_count - function_word_count`, using the
  metrics stage's internally computed counts.
- Fail clearly and emit no metrics output when `--explicit-link-count` is
  invalid, using these exact messages:
  - `--explicit-link-count must be a positive integer` when the value is not
    numeric or is negative
  - `--explicit-link-count must be an integer between 0 and <max>, where <max> = word_count - function_word_count`
    when the value exceeds the computed maximum.
- Require metrics to compute function-word counts internally against the real
  input text, with syllabification-aware handling.
- Log internally computed metrics-relevant indicators.
- Stop `printer` from reading or verifying any `metadata.data.*` counters.
- Restrict `printer` frontmatter consumption to `file.title`.
- Remove `metadata.data` from printer output frontmatter.
- Log internally computed printer-relevant indicators.
- Propagate the new CLI options through `fullprosmaker`.
- Update user-facing docs, manuals, and internal developer-facing references.

## Not Included

- Replacing `explicit_word_link_count` with a new serialized or inferred
  alternative.
- Broad compatibility promises for frontmatter-free input beyond the
  supported minimal path beginning at the syllabifier.
- Production-algorithm changes to syllabification, prominence selection, or
  acoustic metrics beyond what is needed to support the new input and metadata
  contract.
- Changing historical accepted internal records in place.

---

# Current Behavior

`atfparser`, `syllabify`, and `prosmaker` serialize stage counters into
`metadata.data`, and later stages read and verify some of those inherited
values. `metricalc` also relies on inherited prosody counters for part of its
word-level reporting.

This design means a stage can fail even when the body text is otherwise valid,
simply because an upstream counter is absent, stale, or impossible to provide
for content that entered the pipeline outside `atfparser`.

---

# Proposed Change

1. `atfparser`
   - stop serializing `metadata.data.atfparse.line_count`
   - log the computed line count through the shared logger

2. `syllabify`
   - consume only inherited `file.title`
   - accept input with no frontmatter and default `file.title` to `null`
   - add `--title STRING` to override inherited or default title
   - stop serializing `metadata.data.syllabify.word_count` and
     `metadata.data.syllabify.syllable_count`
   - log internally computed `line_count`, `word_count`, and `syllable_count`

3. `prosmaker`
   - consume only inherited `file.title`
   - stop verifying inherited `atfparse` and `syllabify` counters
   - serialize only `metadata.data.prosody.explicit_word_link_count`
   - log internally computed `line_count`, `word_count`, `syllable_count`,
     `function_word_count`, `prosodic_unit_count`, and
     `accentuated_syllable_count`

4. `metricalc`
   - consume only inherited `file.title` and
     `metadata.data.prosody.explicit_word_link_count`
   - stop verifying inherited `atfparse`, `syllabify`, and non-link `prosody`
     counters
   - add `--explicit-link-count INTEGER` to override inherited explicit-link
     metadata
   - validate `--explicit-link-count` as an integer with minimum `0` and
     maximum `word_count - function_word_count`
   - fail clearly and emit no metrics output when the override is invalid,
     using the exact message `--explicit-link-count must be a positive integer`
     for non-numeric or negative values and the exact message
     `--explicit-link-count must be an integer between 0 and <max>, where <max> = word_count - function_word_count`
     for values above the computed maximum
   - compute function-word counts internally from the consumed text rather than
     inherited frontmatter, with explicit handling for syllabified input forms
   - log internally computed indicators relevant to metrics output
  - omit `metadata.data` from metrics output frontmatter

5. `printer`
   - consume only inherited `file.title`
   - stop verifying any `metadata.data.*` counters
   - log internally computed indicators relevant to printing
  - omit `metadata.data` from printer output frontmatter

6. `fullprosmaker`
   - add pass-through support for `--title` and `--explicit-link-count`

7. Documentation
   - update manuals and CLI references to describe the reduced frontmatter
     surface, new overrides, and non-ATF syllabifier workflow

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/cli/atfparser.py`
- `src/akkapros/cli/syllabify.py`
- `src/akkapros/cli/prosmaker.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/cli/printer.py`
- `scripts/run_fullprosmaker.py`
- shared logger helpers already standardized in `src/akkapros/lib/utils.py`

Metadata contract changes:
- remove the serialized `atfparse` data block entirely unless a future change
  introduces a new permitted field
- remove the serialized `syllabify.word_count` and
  `syllabify.syllable_count` fields
- reduce serialized `prosody` data to `explicit_word_link_count` only
- remove serialized `metadata.data` entirely from metrics and printer outputs
- retain `file.title` as the cross-stage descriptive file metadata

Override precedence:
- `syllabify --title` wins over inherited `file.title`
- if no frontmatter is present and no `--title` is supplied, `file.title` is
  `null`
- `metricalc --explicit-link-count` wins over inherited
  `metadata.data.prosody.explicit_word_link_count`
- `metricalc --explicit-link-count` must validate against the internally
  computed admissible range `0..(word_count - function_word_count)` before the
  metrics report is generated

Computation ownership:
- line, word, syllable, function-word, prosodic-unit, and accentuated-syllable
  indicators are owned by the stage that computes them from its current input
- those indicators are logged rather than serialized unless explicitly kept in
  the reduced contract
- metrics-side function-word counting must account for the fact that the
  canonical function-word constants are unsyllabified while the consumed input
  is syllabified or pivot-form text
- metrics/printer outputs do not republish inherited stage data even when those
  stages consumed reduced-frontmatter inputs upstream

Logging contract:
- all newly surfaced indicators must use the shared logger rather than direct
  `print()` output
- logs must remain factual and consistent with the logger-only runtime policy

Documentation contract:
- user docs must show both frontmatter-bearing and frontmatter-free
  `syllabify` entry paths
- CLI docs must document override precedence for `--title` and
  `--explicit-link-count`
- CLI and manual docs must document `--explicit-link-count` validation bounds
  and failure behavior, including the exact condition-specific validation
  messages
- docs must state clearly that frontmatter-free compatibility is limited to the
  `syllabify` entry point and that the supported minimal path is
  `syllabify -> prosmaker -> (metricalc or printer)`
- printer docs must keep Markdown output aligned with the standard YAML
  frontmatter contract already used by pipeline text outputs

---

# Files Likely Affected

`src/akkapros/cli/atfparser.py`
`src/akkapros/cli/syllabify.py`
`src/akkapros/cli/prosmaker.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/printer.py`
`scripts/run_fullprosmaker.py`
`docs/akkapros/atfparser.md`
`docs/akkapros/syllabifier.md`
`docs/akkapros/prosmaker.md`
`docs/akkapros/metricalc.md`
`docs/akkapros/printer.md`
`docs/akkapros/fullprosmaker.md`
tests and integration fixtures asserting frontmatter and CLI behavior

---

# Acceptance Criteria

- [ ] `atfparser` no longer serializes `metadata.data.atfparse.line_count`.
- [ ] `atfparser` logs the computed line count through the shared logger.
- [ ] `syllabify` no longer requires or verifies
      `metadata.data.atfparse.line_count`.
- [ ] `syllabify` can process plain text input with no frontmatter.
- [ ] `syllabify --title` overrides inherited or default `file.title`.
- [ ] `syllabify` no longer serializes `metadata.data.syllabify.word_count`
      or `metadata.data.syllabify.syllable_count`.
- [ ] `syllabify` logs computed `line_count`, `word_count`, and
      `syllable_count`.
- [ ] `prosmaker` no longer verifies inherited `atfparse` or `syllabify`
      counters.
- [ ] `prosmaker` consumes only inherited `file.title`.
- [ ] `prosmaker` serializes only
      `metadata.data.prosody.explicit_word_link_count`.
- [ ] `prosmaker` logs computed `line_count`, `word_count`, `syllable_count`,
      `function_word_count`, `prosodic_unit_count`, and
      `accentuated_syllable_count`.
- [ ] `metricalc` no longer verifies inherited `atfparse`, `syllabify`, or
      non-link `prosody` counters.
- [ ] `metricalc` consumes only inherited `file.title` and
      `metadata.data.prosody.explicit_word_link_count`.
- [ ] `metricalc --explicit-link-count` overrides inherited explicit-link
      metadata.
- [ ] `metricalc --explicit-link-count` is validated as an integer within
  `0..(word_count - function_word_count)`.
- [ ] `metricalc` fails clearly and emits no metrics output when
  `--explicit-link-count` is invalid, using the specified message for
  negative or non-numeric input and the specified message for above-maximum
  input.
- [ ] `metricalc` computes function-word counts internally with
      syllabification-aware handling.
- [ ] `metricalc` logs internally computed indicators relevant to the metrics
      report.
- [ ] `printer` consumes only inherited `file.title`.
- [ ] `printer` no longer verifies any `metadata.data.*` counters.
- [ ] `printer` logs internally computed indicators relevant to printing.
- [ ] `fullprosmaker` exposes pass-through support for `--title` and
      `--explicit-link-count`.
- [ ] User-facing and developer-facing docs are updated for the new contract.
- [ ] Tests are updated to cover reduced frontmatter serialization, missing
      frontmatter at syllabifier input, and both override options.

---

# Risks / Edge Cases

Possible issues:

- Existing consumers may still expect removed frontmatter counters.
- Metrics-side function-word counting may drift if syllabified forms are not
  normalized consistently before comparison.
- If override precedence is undocumented or inconsistently applied, outputs may
  become hard to audit.
- Frontmatter-free compatibility at the syllabifier may create user
  expectations that later stages accept the same inputs unless docs state the
  boundary clearly.
- `--explicit-link-count` validation depends on internally computed metrics-side
  counts, so error timing and messaging must stay clear when the admissible
  maximum is smaller than a user-supplied override.

---

# Testing Strategy

Unit tests:

- `atfparser` frontmatter serialization omits `data.atfparse`
- `syllabify` accepts content-only input and applies title default/override
- `syllabify` omits serialized word and syllable counters
- `prosmaker` omits serialized non-link prosody counters
- `metricalc` override precedence for `--explicit-link-count`
- `metricalc` range validation for `--explicit-link-count`
- `metricalc` failure behavior for non-integer and out-of-range
  `--explicit-link-count`
- metrics-side function-word counting from syllabified input
- `printer` ignores inherited `metadata.data.*` counters and logs internal
  indicators

Integration tests:

- end-to-end pipeline output uses the reduced frontmatter contract
- `fullprosmaker` forwards both new CLI options correctly
- metrics output remains correct when inherited non-link counters are absent
- invalid `--explicit-link-count` inputs fail before metrics output is written
- historical verification paths no longer block valid reduced-frontmatter files
- printer output remains correct when inherited `metadata.data.*` counters are
  absent

Manual/spec review:

- verify docs clearly distinguish logged indicators from serialized metadata
- verify override precedence is stated identically across CLI help and manuals

---

# Rollback Plan

Restore the previous frontmatter counter serialization and inherited-value
verification rules, remove the new override options, and return the syllabifier
to frontmatter-required input if the reduced contract must be withdrawn.

---

# Related Issues

- Narrows part of [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md)
  and [CR-018](018-add-cli-file-front-matter-and-metadata-propagation.md).
- Narrows the frontmatter dependency introduced by
  [REQ-015](../req/015-frontmatter-derived-word-indicators-in-metrics.md) and
  [CR-022](022-add-frontmatter-derived-word-indicators-to-metrics.md).
- Uses the logging constraints defined in
  [REQ-016](../req/016-standardized-cli-logging-and-console-options.md) and
  [CR-023](023-adopt-logging-actions-for-cli-logging.md).
- Requires orchestration alignment with
  [REQ-007](../req/007-full-pipeline-orchestration.md).
- Touches the print-stage contract described in
  [REQ-005](../req/005-multi-format-printer-output.md).

---

# Tasks

## Implementation

- [ ] Remove serialized inherited-counter blocks from affected stages.
- [ ] Add `syllabify --title` and `metricalc --explicit-link-count`.
- [ ] Move affected counters to stage-local computation plus logging.
- [ ] Update `printer` to consume only `file.title` and ignore `metadata.data.*`.
- [ ] Update `fullprosmaker` pass-through argument handling.

## Tests

- [ ] Add focused regression coverage for reduced frontmatter and option
      precedence.
- [ ] Add integration coverage for non-ATF syllabifier entry and metrics
  override behavior.
- [ ] Add printer coverage for reduced-frontmatter inputs.

## Documentation

- [ ] Update CLI docs and manuals for the reduced frontmatter contract.
- [ ] Document the compatibility boundary for frontmatter-free inputs.
- [ ] Document printer behavior under the reduced frontmatter contract.
- [ ] Document `--explicit-link-count` bounds, precedence, and failure cases.
- [ ] Document the exact condition-specific `--explicit-link-count`
  validation messages.

## Review

- [ ] Verify the implemented validation messages match the specified wording.

---

# Notes for CR-024

This CR deliberately treats most counters as stage-local runtime facts rather
than cross-stage serialized contract data. The only retained prosody-stage
counter in frontmatter is `explicit_word_link_count`, because it remains the
one value in this scope that the metrics stage cannot always recover faithfully
from transformed text alone.