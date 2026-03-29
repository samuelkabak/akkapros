---
req_id: REQ-017
status: Draft
priority: High
impact: Mutative
created: 2026-03-29
updated: 2026-03-29
related_adrs: 'ADR-027, ADR-028, ADR-029, ADR-031'
implemented_by: 'CR-024'
---

# Requirement: Frontmatter Minimization and Source-Flexible Pipeline Inputs

# Summary

The pipeline shall reduce stage-specific frontmatter coupling so downstream
stages no longer depend on inherited line, word, syllable, or prosody counts
that they can compute internally. The only inherited file-level metadata that
must remain broadly consumable for these stages is `file.title`, plus
`metadata.data.prosody.explicit_word_link_count` for metrics input unless the
user overrides it on the command line.

The syllabifier shall also support non-ATF-parser inputs by accepting content
files that have no frontmatter at all, defaulting `file.title` to `null` unless
the user supplies `--title`. All newly required computed indicators shall be
logged through the standardized CLI logging path rather than serialized into
frontmatter unless they remain explicitly required by this requirement.

The supported minimal pipeline path for this change is
`syllabify -> prosmaker -> (metricalc or printer)`. Frontmatter-free input
compatibility is limited to the `syllabify` entry point; downstream stages in
this requirement continue to consume the reduced frontmatter contract rather
than arbitrary content-only inputs.

This requirement intentionally narrows parts of the earlier frontmatter
propagation contract in [REQ-013](013-cli-file-front-matter-and-metadata-propagation.md)
and the metrics dependency introduced by
[REQ-015](015-frontmatter-derived-word-indicators-in-metrics.md), without
rewriting those historical records.

---

# Motivation

The current contract makes several stages verify and re-emit counters that are
already derivable from their actual input body. That creates unnecessary schema
coupling between stages, prevents the syllabifier from cleanly processing files
originating outside `atfparser`, and makes frontmatter larger and more brittle
than necessary.

Reducing frontmatter to the minimum metadata that must cross stage boundaries
improves interoperability, removes low-value duplication, and keeps derived
statistics authoritative at the stage that computes them. The remaining values
that cannot always be reconstructed faithfully, especially explicit user word
links, continue to travel via frontmatter or an explicit CLI override.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given `atfparser` output, when frontmatter is written, then
      `metadata.data.atfparse.line_count` is not emitted.
- [ ] Given `atfparser` runs, when line counts are computed, then the computed
      `line_count` is emitted through the shared logger rather than frontmatter.
- [ ] Given `syllabify` reads an input file with frontmatter, when it consumes
      inherited metadata, then it reads only `file.title` and does not require
      or verify `metadata.data.atfparse.line_count`.
- [ ] Given `syllabify` reads an input file with no frontmatter, when parsing
      begins, then the command still succeeds and treats inherited `file.title`
      as `null` unless overridden by `--title`.
- [ ] Given `syllabify` is invoked with `--title SOME STRING`, when output
      frontmatter is written, then `file.title` equals that exact string even
      if the input frontmatter already contained another title or `null`.
- [ ] Given `syllabify` writes output frontmatter, when `metadata.data` is
      serialized, then `metadata.data.syllabify.word_count` and
      `metadata.data.syllabify.syllable_count` are not emitted.
- [ ] Given `syllabify` processes content, when internal indicators are
      computed, then the internally computed `line_count`, `word_count`, and
      `syllable_count` are emitted through the shared logger.
- [ ] Given `prosmaker` reads an input file with frontmatter, when it consumes
      inherited metadata, then it reads only `file.title` and does not require
      or verify `metadata.data.atfparse.line_count`,
      `metadata.data.syllabify.word_count`, or
      `metadata.data.syllabify.syllable_count`.
- [ ] Given `prosmaker` writes output frontmatter, when `metadata.data.prosody`
      is serialized, then it emits only `explicit_word_link_count` and does not
      emit `function_word_count`, `prosodic_unit_count`, or
      `accentuated_syllable_count`.
- [ ] Given `prosmaker` processes content, when internal indicators are
      computed, then the internally computed `line_count`, `word_count`,
      `syllable_count`, `function_word_count`, `prosodic_unit_count`, and
      `accentuated_syllable_count` are emitted through the shared logger.
- [ ] Given `metricalc` reads an input file with frontmatter, when it consumes
      inherited metadata, then it reads only `file.title` and
      `metadata.data.prosody.explicit_word_link_count` and does not require or
      verify `metadata.data.atfparse.line_count`,
      `metadata.data.syllabify.word_count`,
      `metadata.data.syllabify.syllable_count`,
      `metadata.data.prosody.function_word_count`,
      `metadata.data.prosody.prosodic_unit_count`, or
      `metadata.data.prosody.accentuated_syllable_count`.
- [ ] Given `metricalc` is invoked with `--explicit-link-count N`, when the
      metrics stage resolves explicit user word-link input, then that CLI value
      overrides any inherited `metadata.data.prosody.explicit_word_link_count`.
- [ ] Given `metricalc` is invoked with `--explicit-link-count N`, when the
      value is validated, then it must be an integer with
      `0 <= N <= word_count - function_word_count`, using the metrics stage's
      internally computed `word_count` and `function_word_count`.
- [ ] Given `metricalc` is invoked with `--explicit-link-count N`, when `N` is
      not a number or is negative, then the command fails clearly with the
      message `--explicit-link-count must be a positive integer` and does not
      emit metrics output.
- [ ] Given `metricalc` is invoked with `--explicit-link-count N`, when `N`
      exceeds the admissible maximum `word_count - function_word_count`, then
      the command fails clearly with the message
      `--explicit-link-count must be an integer between 0 and <max>, where <max> = word_count - function_word_count`
      and does not emit metrics output.
- [ ] Given `metricalc` resolves function-word statistics, when it computes the
      count, then `function_word_count` is derived internally from the actual
      input text rather than inherited frontmatter, and the implementation must
      account for the fact that function-word constants are not syllabified.
- [ ] Given `metricalc` computes internal indicators, when logging occurs, then
      the logger includes internally computed indicators relevant to metrics,
      including line, word, syllable, function-word, prosodic-unit, and
      accentuated-syllable counts where available from the consumed pivot text.
- [ ] Given `metricalc` writes output frontmatter, when metrics table or JSON
      frontmatter is serialized, then no `metadata.data` section is emitted.
- [ ] Given `printer` reads an input file with frontmatter, when it consumes
      inherited metadata, then it reads only `file.title` and does not require
      or verify any `metadata.data.*` counters.
- [ ] Given `printer` computes internal indicators from its consumed text, when
      logging occurs, then the logger includes internally computed indicators
      relevant to printing, including available line, word, or syllable counts.
- [ ] Given `printer` writes output frontmatter, when an output text file is
      serialized, then no `metadata.data` section is emitted.
- [ ] Given `fullprosmaker` exposes orchestration options, when the new stage
      options are added, then it propagates `--title` to `syllabify` and
      `--explicit-link-count` to `metricalc` without inventing divergent option
      names.
- [ ] Given user-facing documentation and manuals are updated, when frontmatter
      contracts and CLI options are described, then they reflect the reduced
      metadata surface, non-ATF syllabifier input support, `--title`, and
      `--explicit-link-count`, including override precedence and validation
      bounds.
- [ ] Given tests are updated for this requirement, when regression coverage is
      added, then it includes content-only syllabifier input, title override,
      explicit-link-count override, explicit-link-count rejection for invalid
      type or range, reduced frontmatter serialization, and the absence of
      legacy verification dependencies.

---

# User Story (optional)
> As a researcher running individual pipeline stages on prepared text from more
> than one source, I want the stages to depend on minimal inherited metadata so
> that I can reuse the tools outside the exact `atfparser` pipeline while still
> preserving optional titles and explicit-link information where needed along
> the minimal path `syllabify -> prosmaker -> (metricalc or printer)`.

---

# Interface Notes
- Input: text files with YAML frontmatter or plain text files without
      frontmatter for `syllabify`; reduced-frontmatter upstream files for
      `prosmaker`, `metricalc`, and `printer` within the supported minimal path
      `syllabify -> prosmaker -> (metricalc or printer)`.
- New CLI options:
  - `syllabify --title STRING`
  - `metricalc --explicit-link-count INTEGER`
- Validation rule for `metricalc --explicit-link-count`:
      - integer only
      - minimum `0`
      - maximum `word_count - function_word_count`, computed internally by metrics
      - if not numeric or negative, fail clearly with the message
            `--explicit-link-count must be a positive integer`
      - if greater than the computed maximum, fail clearly with the message
            `--explicit-link-count must be an integer between 0 and <max>, where <max> = word_count - function_word_count`
      - if invalid, emit no metrics output
- Output frontmatter rules:
  - `atfparse`: no `metadata.data.atfparse` block
  - `syllabify`: no serialized `metadata.data.syllabify` counts
  - `prosody`: serialize only `metadata.data.prosody.explicit_word_link_count`
      - `metrics` input: consume only `file.title` and `metadata.data.prosody.explicit_word_link_count`
      - `metrics` output: no serialized `metadata.data` block
      - `printer` input: consume only `file.title`
      - `printer` output: no serialized `metadata.data` block
- Logging rules: internally computed indicators must be emitted through the
  shared logger and not through ad hoc `print()` output, consistent with
  [REQ-016](016-standardized-cli-logging-and-console-options.md).
- Affected components: `src/akkapros/cli/atfparser.py`,
  `src/akkapros/cli/syllabify.py`, `src/akkapros/cli/prosmaker.py`,
      `src/akkapros/cli/metricalc.py`, `src/akkapros/cli/printer.py`,
      `scripts/run_fullprosmaker.py`, and the related user/developer docs.

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration: this is a mutative contraction of the serialized frontmatter
  schema. Documentation and tests must be updated so consumers stop expecting
  the removed counters in frontmatter and rely on logs or recomputation
  instead.

# Related
- Related ADRs: [ADR-027](../adr/027-yaml-front-matter-for-cli-pipeline-files.md),
  [ADR-028](../adr/028-centralized-cli-logging-with-logging-actions.md),
  [ADR-029](../adr/029-cli-runtime-output-via-logger-only.md),
  [ADR-031](../adr/031-factual-runtime-records-and-structured-self-test-output.md)
- Related REQs: [REQ-013](013-cli-file-front-matter-and-metadata-propagation.md),
  [REQ-015](015-frontmatter-derived-word-indicators-in-metrics.md),
  [REQ-016](016-standardized-cli-logging-and-console-options.md),
      [REQ-007](007-full-pipeline-orchestration.md),
      [REQ-005](005-multi-format-printer-output.md)
- Implementation CRs: [CR-024](../cr/024-minimize-frontmatter-and-enable-source-flexible-stage-inputs.md)

# Non-Goals
- This requirement does not redesign the underlying syllabification,
  prosody-realization, or metrics algorithms.
- This requirement does not remove `file.title` from frontmatter.
- This requirement does not replace the explicit-link counter with a new
  reconstruction heuristic in upstream stages.
- This requirement does not authorize edits to historical accepted REQs or CRs
  except for additive cross-references if maintainers later choose to add them.

# Security / Safety Considerations
- Reduced frontmatter should continue to avoid leaking filesystem-bearing input
  or output paths.
- Stages must treat optional or overridden frontmatter values as untrusted
  input and validate them predictably.
- Logged indicators should remain factual and concise, following the shared
  logger-only runtime policy.