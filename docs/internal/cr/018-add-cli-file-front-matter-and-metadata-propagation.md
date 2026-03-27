# Change Request: Add CLI file front matter and metadata propagation

CR-ID: CR-018
Status: Done
Priority: High
Impact: Mutative
Created: 2026-03-27
Updated: 2026-03-27
Implements: ADR-027, REQ-013
---

Bug note: During verification, diphthong restoration in `_tilde` was found to
drop the real syllable separator before the internal hiatus marker
(`ti·¨ā~m·tu` became `ti¨ā~m·tu`). The generator and restoration tests were
corrected so pivot output now preserves the explicit `·¨` structure.

# Summary

Introduce a front matter contract for CLI-generated files across the Akkadian
prosody pipeline. The change adds YAML front matter to text outputs, an
equivalent `frontmatter` object to metrics JSON, and centralized schema/version
management so stages can read, validate, and propagate metadata between steps.

The compact validation-oriented stage data shall use `explicit_word_link_count`
as the canonical field name for explicit user word-link markers.

This CR replaces the earlier lex-output proposal for metadata propagation.

---

# Motivation

The current content-only file contract does not preserve file identity, format
version, source title, or stage-specific metadata in a reusable way. The now-
discarded lexical output approach solved one narrow propagation problem but did
not provide a general mechanism for validation or metadata transport.

This CR introduces one pipeline-wide contract instead of adding more special-
purpose outputs.

---

# Scope

## Included

- Add YAML front matter to CLI-generated text outputs.
- Add a top-level `frontmatter` object to metrics JSON outputs.
- Leave metrics CSV outside this change and without a front matter contract.
- Require all pipeline stages to read front matter before consuming content.
- Validate input `file.format` and `file.version` using front matter.
- Generate and propagate `file.id`, `file.title`, and `metadata.input_file_id`.
- Emit `metadata.input_file_id: null` for `atfparser` outputs because ATF
  inputs are not prior pipeline files.
- Record effective non-filesystem CLI options under `metadata.options`.
- Propagate stage-specific metadata under `metadata.data` in pipeline order.
- Aggregate append-mode front matter across appended documents, including
  joined titles and summed numeric stage counters.
- Use canonical snake_case field names for compact stage-data counters,
  including `explicit_word_link_count` for explicit user word-link markers.
- Define front matter templates and per-format version values centrally in
  `src/akkapros/lib/frontmatter.py`.
- Update user-facing documentation and internal fixtures/spec references for
  the new file contract.
- Keep cross-line attached `-` / `+` handling out of generic shared validation.
  The syllabifier stage alone owns this lexical-continuation behavior, using
  the strict pattern `AKKADIAN_LETTER + EOL + AKKADIAN_LETTER`.

## Not Included

- Reintroducing `_lex.txt` as a metadata-propagation mechanism.
- Embedding front matter in metrics CSV outputs.
- Defining a retained front matter contract for metrics CSV.

---

# Current Behavior

Pipeline files are emitted as raw content without a metadata header. Downstream
commands therefore cannot rely on an embedded contract for provenance, format
validation, or option propagation. Metadata needs are addressed either by
recomputation or by proposing special-purpose outputs.

---

# Proposed Change

1. Emit front matter with this logical structure in text outputs:

```yaml
---
package:
  name: akkapros
  version: <package version>
pipeline: pipeline
step: <atfparse | syllabify | prosody | metrics | print>
file:
  id: <uuid>
  title: <ATF-derived title>
  format: <filename suffix before extension>
  version: <format version>
  date: <YYYY-MM-DD>
metadata:
  input_file_id: <input id>
  options:
    <effective options in snake_case>
  data:
    <stage-keyed propagated data>
---

<content>
```

2. Apply equivalent structure to metrics JSON under a top-level `frontmatter`
   object.

3. Leave metrics CSV as plain CSV while ensuring the same metadata remains
   available in the paired text and JSON metrics outputs.

4. Replace the previous lex-output dependency path for metadata propagation.

5. Use the filename suffix before the extension as the approved `file.format`
  value. Examples: `_proc.txt` -> `proc`, `_syl.txt` -> `syl`, `_tilde.txt`
  -> `tilde`, `_metrics.txt` and `_metrics.json` -> `metrics`, `_ipa.txt`
  -> `ipa`, `_xar.txt` -> `xar`.

---

# Technical Design

Architecture notes:

Components:
- shared front matter schema and helpers in `src/akkapros/lib/frontmatter.py`
- all CLI emitters and readers participating in the pipeline

Schema rules:
- keys use lowercase snake_case
- `package.version` comes from `src/akkapros/__init__.py`
- `file.id` is created with Python `uuid` at file creation time
- `file.title` originates from the ATF source title and is propagated
- `pipeline` is `pipeline` for all files covered by this CR
- `metadata.options` excludes filename and output-directory arguments
- `explicit_word_link_count` is the canonical stage-data field name for
  explicit user word-link markers; in current scope this means literal `+`
  links inherited from upstream input
- default option values are emitted only when effective values are not empty
  strings and not `false`
- `metadata.data` contains only populated stage blocks up to the current step
- stage-data emission is reduced to the approved non-duplicated set:
  - `atfparse.line_count`
  - `syllabify.word_count`, `syllabify.syllable_count`
  - `prosody.function_word_count`, `prosody.explicit_word_link_count`,
    `prosody.prosodic_unit_count`, `prosody.accentuated_syllable_count`
  - no serialized `metrics` stage block
- if a later stage recomputes `line_count`, `word_count`, or `syllable_count`,
  it must verify the inherited value matches and omit the duplicate field from
  output

Validation:
- read front matter before content parsing
- verify supported `file.format` and `file.version`
- do not reject input files generically for trailing `-` / `+` across physical
  lines; that interpretation belongs to the syllabifier only
- for append-mode aggregate files, strip every embedded front matter block
  before validating or processing the concatenated content bodies
- when append mode targets an existing atfparser output, rewrite the file using
  one effective merged front matter block so the current aggregate contract is
  directly represented on disk
- preserve current validation behavior and extend it with front matter checks

Format-specific exception:
- metrics text output: YAML front matter
- metrics JSON output: `frontmatter` object
- metrics CSV output: outside this change and no embedded front matter

---

# Files Likely Affected

`src/akkapros/lib/frontmatter.py`
`src/akkapros/cli/atfparser.py`
`src/akkapros/cli/syllabify.py`
`src/akkapros/cli/prosmaker.py`
`src/akkapros/cli/metricalc.py`
printer/format CLI modules under `src/akkapros/cli/`
pipeline documentation under `docs/akkapros/`
tests and integration fixtures that assert file-output contracts

---

# Acceptance Criteria

- [x] CLI-generated text outputs begin with YAML front matter, then one blank
      line, then the content body.
- [x] Metrics JSON outputs contain a top-level `frontmatter` object equivalent
      to the YAML front matter structure.
- [x] Metrics CSV outputs contain no embedded front matter.
- [x] All emitted front matter keys use lowercase snake_case.
- [x] `pipeline` is emitted as `pipeline` for all files covered by this CR.
- [x] Each stage can read front matter and validate `file.format` and
      `file.version` before consuming content.
- [x] `file.format` equals the output filename suffix before the extension,
  including `metrics` for both `_metrics.txt` and `_metrics.json`.
- [x] `file.id`, `file.title`, and `metadata.input_file_id` are populated and
      propagated according to the approved contract.
- [x] `atfparser` outputs emit `metadata.input_file_id: null`.
- [x] `metadata.options` excludes filesystem-bearing arguments and records
      effective non-empty, non-false option values in snake_case.
- [x] `explicit_word_link_count` is used as the canonical field name for
  explicit user word-link counters in stage data.
- [x] `metadata.data` carries populated stage data from the start of the
      pipeline through the current step without printing empty future blocks.
- [x] The serialized stage-data field set is reduced to the approved non-
  duplicated counters and omits `data.metrics`.
- [x] Duplicate indicator fields (`line_count`, `word_count`,
  `syllable_count`) are checked for consistency and omitted from later
  stage blocks when they match inherited values.
- [x] Generic shared validation does not reject input files solely because a
  line ends with `-` or `+`.
- [x] The syllabifier stage alone handles cross-line attached `-` / `+` as
  lexical continuation only for the strict pattern `AKKADIAN_LETTER + EOL +
  AKKADIAN_LETTER`.
- [x] Append-mode aggregate files with repeated embedded front matter blocks
  are validated and processed against their concatenated content bodies rather
  than against YAML metadata text.
- [x] Append-mode atfparser outputs merge titles with ` | `, null out
  ambiguous source `input_file_id` values, and sum numeric stage counters
  across appended source documents.
- [x] Front matter templates and format-version values are maintained in
      `src/akkapros/lib/frontmatter.py`.
- [x] User-facing documentation is updated for the mutative output contract,
  including file examples, migration guidance, and metrics text versus JSON
  behavior.
- [x] Developer-facing documentation is updated for the shared schema,
  format/version handling, validation rules, and helper ownership in
  `src/akkapros/lib/frontmatter.py`.
- [x] Built-in `run_tests()` coverage is added or extended in affected modules
  where self-tests exist for serialization and validation behavior.
- [x] Pytest coverage includes focused unit tests and end-to-end integration
  tests for the new front matter contract.

---

# Risks / Edge Cases

Possible issues:

- File-contract breakage for downstream consumers that currently expect raw
  content with no header.
- Migration handling for legacy files not yet carrying front matter.
- Rejection of malformed cross-line continuation may require users to repair a
  small number of rare legacy inputs before processing.
- Divergence risk if YAML and JSON front matter schemas are maintained in more
  than one place.

---

# Testing Strategy

Unit tests:

- front matter serialization for text outputs
- JSON `frontmatter` mapping
- option filtering and snake_case normalization
- canonical stage-data field naming, including `explicit_word_link_count`
- append-mode merged-front-matter aggregation and title joining
- file-format and file-version validation
- validation failure for attached terminal `-` / `+` cross-line continuation
- stage-data propagation rules

Integration tests:

- end-to-end pipeline file generation with front matter
- append-mode end-to-end pipeline generation with aggregated front matter and
  reduced stage-data blocks
- metrics text/JSON special-case behavior and CSV exclusion from this change
- pytest integration coverage for representative multi-step pipeline flows
- legacy-input migration behavior once approved

Manual/spec review:

- verify template alignment with ADR-027 and REQ-013
- verify that no filesystem-sensitive arguments are emitted
- verify that line counts remain trustworthy because malformed cross-line
  continuation is rejected rather than repaired implicitly

---

# Rollback Plan

Revert to the prior content-only file contract and remove front matter parsing,
serialization, and validation changes from the pipeline. Any such rollback must
also revert documentation and fixtures that assume front matter.

---

# Related Issues

- Legalized by [ADR-027](../adr/027-yaml-front-matter-for-cli-pipeline-files.md)
  and [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md).
- Replaces the discarded lex-output path previously attached to `REQ-013` and
  `CR-018`.
- Provides the metadata propagation path that future metrics enhancements must
  use instead of `_lex.txt` pairing.

---

# Tasks

## Implementation

- [ ] Add shared front matter schema/version support.
- [ ] Update all relevant CLI writers to emit front matter.
- [ ] Update all relevant CLI readers to parse and validate front matter.
- [ ] Handle metrics text/JSON/CSV output exceptions according to the contract.
- [ ] Implement explicit validation for attached terminal `-` / `+` cross-line
  continuation and emit a clear error instead of merging lines.

## Tests

- [ ] Add or extend built-in `run_tests()` coverage in affected modules where
  self-tests already exist.
- [ ] Add pytest unit coverage for serialization, validation, and propagation
  rules.
- [ ] Add or refresh pytest integration fixtures for affected outputs.

## Documentation

- [ ] Update user docs for pipeline file contracts and metrics-output behavior.
- [ ] Update developer-facing docs for the schema contract, helper ownership,
  and validation rules.
- [ ] Document migration expectations for downstream consumers.

## Review

- [ ] Confirm migration handling for legacy content-only inputs.

---

# Notes for CR-018

This CR is intentionally mutative because it changes file-output contracts
across the pipeline. Final implementation sequencing depends on approval of the
remaining identifier questions captured in `REQ-013`.
