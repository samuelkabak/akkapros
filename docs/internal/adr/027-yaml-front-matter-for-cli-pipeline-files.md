---
adr_id: ADR-027
status: Proposed
created: 2026-03-27
updated: 2026-03-27
superseded_by: null
---

# 027. YAML Front Matter for CLI Pipeline Files

## Plain Summary

All CLI-generated pipeline files shall carry structured front matter so metadata can move through the pipeline explicitly instead of being reconstructed from content-specific side outputs. The front matter uses YAML for text files and a structurally equivalent `frontmatter` object for metrics JSON. Metrics CSV is outside this change and carries no front matter contract here.

Historical note: this ADR records the front matter decision at a time when
metrics CSV still existed as a separate artifact. The later removal of metrics
CSV is legalized by [ADR-030](030-metrics-csv-abandonment-and-spec-history-policy.md)
and specified in [REQ-014](../req/014-remove-metrics-csv-output.md).

TL;DR: replace ad hoc metadata propagation with a versioned, snake_case front matter contract that every stage can read and validate.

## Context and Problem Statement

The pipeline currently exchanges plain content files with no metadata header. A recent attempt to solve downstream provenance needs introduced a dedicated lexical output only to carry facts such as construct-noun counts. That approach is too narrow, creates a new file contract for one use case, and does not provide a general mechanism for validating file origin, format, or version.

The project needs a common, stage-spanning mechanism to:

- propagate metadata from one CLI step to the next,
- validate input format and file-version compatibility,
- preserve a stable file identity and source title across derived outputs,
- record effective CLI options without leaking filesystem paths, and
- carry stage-specific data forward without inventing additional output-only formats.

## Decision Drivers

- Explicit provenance across the full CLI pipeline
- Validation of file format and format version at read time
- Conservative change discipline for research-grade outputs
- Reuse of one mechanism across all stages instead of special-purpose outputs
- Security: no propagation of filesystem-sensitive arguments
- Centralized maintenance of format versions and templates

## Considered Options

- Option A — Keep raw content files and continue solving metadata needs with dedicated side outputs such as `_lex.txt`. Rejected because it does not generalize and ties provenance to one feature.
- Option B — Add a YAML front matter block to every CLI-generated file, with a JSON-native `frontmatter` object for metrics JSON and no front matter contract for metrics CSV in this change. Chosen because it provides a uniform, explicit, and extensible metadata contract.
- Option C — Use separate sidecar metadata files for all stages. Not chosen because it complicates file pairing, weakens portability, and creates more opportunities for drift.

## Decision Outcome

Choose Option B.

Every CLI-generated file in the pipeline shall carry a structured metadata contract at creation time. Text outputs shall begin with a YAML front matter block. Metrics JSON shall expose the same information under a top-level `frontmatter` object. Metrics CSV remains outside this change, stays content-only while it still exists, and is addressed later by separate abandonment work.

The front matter schema uses lowercase snake_case keys. The common top-level structure is:

```yaml
---
package:
  name: akkapros
  version: <from src/akkapros/__init__.py>
pipeline: pipeline
step: <atfparse | syllabify | prosody | metrics | print>
file:
  id: <uuid>
  title: <propagated from ATF & line>
  format: <filename suffix before extension>
  version: <format version managed centrally>
  date: <YYYY-MM-DD>
metadata:
  input_file_id: <source file id>
  options:
    <effective snake_case option values>
  data:
    atfparse:
    syllabify:
    prosody:
    metrics:
    print:
---

<content>
```

The `metadata` block is the extensible area for file-specific and stage-specific information. `metadata.options` records effective non-filesystem CLI options in snake_case. `metadata.data` carries stage data from the beginning of the pipeline through the current step.

For this ADR, the approved `pipeline` value is `pipeline`. The approved `file.format` value is the filename suffix before the extension. Examples: `_proc.txt` maps to `proc`, `_syl.txt` maps to `syl`, `_tilde.txt` maps to `tilde`, `_metrics.txt` and `_metrics.json` map to `metrics`, `_ipa.txt` maps to `ipa`, and `_xar.txt` maps to `xar`.

## Pros and Cons of the Options

### Chosen Option

- Pros: makes provenance explicit in every generated file
- Pros: supports input validation by format and file-version before parsing content
- Pros: replaces special-purpose propagation outputs with one general contract
- Pros: allows downstream stages to consume upstream metadata without reconstructing it from text
- Cons: mutates file contracts across the pipeline
- Cons: requires central schema/version management and coordinated rollout

### Other Options

- Option A:
  - Pro: minimal short-term change
  - Con: metadata remains fragmented and feature-specific
  - Con: does not solve general validation needs
- Option C:
  - Pro: keeps content bodies unchanged
  - Con: requires managing file pairs everywhere
  - Con: sidecars are easier to lose or mismatch than embedded metadata

## Implications and Consequences

- Each CLI stage must be able to read front matter before processing content.
- Validation must check front matter structure plus declared `file.format` and `file.version` in addition to existing validation logic.
- Cross-line attached `-` / `+` handling is owned only by the syllabifier stage,
  where it is interpreted as lexical continuation only for the strict pattern
  `AKKADIAN_LETTER + EOL + AKKADIAN_LETTER`; generic file validation must not
  reject unrelated ATF or intermediate files on that basis.
- A new central specification point is required for front matter templates and per-format version values in `src/akkapros/lib/frontmatter.py`.
- File identifiers become explicit and traceable through `file.id` and `metadata.input_file_id`.
- The ATF-derived title becomes a propagated data field rather than something inferred ad hoc downstream.
- Metrics outputs require a format-specific exception:
  - text table output uses YAML front matter,
  - JSON exposes an equivalent `frontmatter` object,
  - CSV is outside this change and contains no front matter block.
- The earlier lex-output approach for metadata propagation is discarded.

## Links

- [docs/internal/adr/004-stage-pipeline-and-pivot-format.md](004-stage-pipeline-and-pivot-format.md)
- [docs/internal/adr/002-centralized-version-management.md](002-centralized-version-management.md)
- [docs/internal/adr/022-output-format-public-contract-boundaries.md](022-output-format-public-contract-boundaries.md)
- [docs/internal/adr/026-conservative-change-discipline-for-research-grade-computation.md](026-conservative-change-discipline-for-research-grade-computation.md)
- [docs/internal/req/013-cli-file-front-matter-and-metadata-propagation.md](../req/013-cli-file-front-matter-and-metadata-propagation.md)
- [docs/internal/cr/018-add-cli-file-front-matter-and-metadata-propagation.md](../cr/018-add-cli-file-front-matter-and-metadata-propagation.md)
- [docs/internal/cr/020-metrics-word-stats-lex-input.md](../cr/020-metrics-word-stats-lex-input.md)

## Implementation Notes (optional)

- Define front matter templates and format-version constants centrally rather than scattering them through CLI modules.
- Exclude filename and output-directory arguments from stored options.
- In `metadata.options`, include defaults only when the effective value is neither an empty string nor `false`.
- In `metadata.data`, omit future or empty stage blocks instead of printing placeholder empty sections.
- Preserve snake_case key names uniformly in YAML and JSON.

## Reviewed By

- Pending maintainer review
