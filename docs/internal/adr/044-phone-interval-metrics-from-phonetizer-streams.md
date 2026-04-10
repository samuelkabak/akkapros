---
adr_id: ADR-044
status: Accepted
created: 2026-04-08
updated: 2026-04-10
superseded_by: null
---

# 44. Phone-Interval Metrics from Phonetizer Streams

## Plain Summary

Move metricalc away from `_tilde` parsing and make `_phone.txt` plus
`_ophone.txt` the sole active inputs for rhythm metrics. The new metrics model
derives vocalic, consonantal, and pause intervals directly from duration-bearing
phonetizer rows, then computes Ramus-Dellwo and Grabe-Low style statistics from
those intervals.

This also retires the previous active understanding of `ΔC`, `VarcoC`, and
related metrics as `_tilde`-derived consonant-spacing measures. Active metrics
documentation must describe only the new phone-interval definitions, and the
active metrics output must remain complete under the new design.

## Context and Problem Statement

The existing metrics contract still assumes that metricalc reads
prosody-realized `_tilde.txt` and reconstructs rhythmic measures from symbolic
text plus timing assumptions. That design is no longer the best fit for the
pipeline.

The phonetizer now owns the duration-bearing structural representation needed by
metrics:

- `_ophone.txt` encodes the original stream
- `_phone.txt` encodes the accentuated stream
- row structure already carries the information needed for syllables,
  accentuation, explicit linking, and interval timing

At the same time, the prior active explanation of `ΔC`, `VarcoC`, and related
metrics is fundamentally wrong for the intended rhythm literature alignment. The
project needs one explicit decision that metrics are computed from contiguous
phone-derived intervals, not from `_tilde`-derived consonant spacing.

## Decision Drivers

- Align active metrics with Ramus-Dellwo and Grabe-Low interval definitions
- Use the phonetizer as the single source of truth for segment durations
- Eliminate duplicate reconstruction of information already encoded in phone rows
- Keep original and accentuated metrics directly comparable from paired streams
- Remove obsolete `_tilde` frontmatter dependencies where the data is now
  encoded downstream

## Considered Options

- Keep metricalc on `_tilde` and only patch individual formulas.
- Use a hybrid design where metrics reads `_tilde` plus `_phone`/`_ophone`.
- Make `_phone` and `_ophone` the sole active metrics inputs and compute all
  interval metrics from those files.

## Decision Outcome

Chosen option: make `_phone` and `_ophone` the sole active metrics inputs and
compute all active rhythm metrics from phone-derived intervals.

Under this decision:

- metricalc reads paired phonetizer artifacts, not `_tilde`
- the primary metrics input artifact is `<prefix>_phone.txt`
- metricalc accepts an optional `--ophone` path for the original stream; if the
  option is absent, the stage derives the sibling `<prefix>_ophone.txt` path
  from the supplied `_phone.txt` name and fails clearly if that file does not
  exist
- the metrics core normalizes phonetizer rows into a class stream of `V`, `C`,
  and `P`
- phonetizer rows with consonant category, including hiatus and
  vowel-transition rows, remain consonantal for metrics interval formation
- contiguous rows of the same class are merged into one interval with summed
  duration
- pause intervals are excluded from `mean`, `Δ`, `Varco`, and PVI families, but
  remain included in the total duration denominator for `%V` and `%C`
- original metrics are computed from `_ophone.txt`
- accentuated metrics are computed from `_phone.txt`
- the public metrics output remains complete under the new design except where
  separate accepted records already removed a surface, such as metrics CSV
  output
- syllable counts, accentuation counts, ratio denominators, and explicit-link
  counts are derived from phone/ophone content and their retained frontmatter,
  not from `_tilde`
- `metadata.data.prosody.explicit_word_link_count` is no longer part of the
  active `_tilde` frontmatter contract
- the `--explicit-link-count` metrics CLI override is obsolete and removed from
  the active contract
- `_phone.txt` and `_ophone.txt` retain frontmatter; `_mbrola.pho` and
  `_ombrola.pho` do not carry frontmatter and are not metrics inputs

The active rhythm family becomes:

- `%C`, `meanC`, `ΔC`, `VarcoC`, `rPVI-C`
- `%V`, `meanV`, `ΔV`, `VarcoV`, `nPVI-V`

## Pros and Cons of the Options

### Chosen Option

- Pros: aligns the active implementation target with standard interval-based
  rhythm metrics.
- Pros: removes the need to reconstruct durations from `_tilde` after the
  phonetizer has already resolved them.
- Pros: makes the original/accentuated comparison a direct comparison of paired
  phonetizer outputs.
- Pros: lets metrics derive explicit word-link counts from encoded downstream
  structure instead of requiring `_tilde` to carry that counter forever.
- Cons: changes the metrics input contract substantially.
- Cons: invalidates older active documentation that explained the previous
  `_tilde`-based interpretation.
- Cons: requires coordinated updates across phonetizer, metrics, frontmatter,
  and documentation records.

### Other Options

- Keep `_tilde` and patch formulas:
  - Pro: smaller migration surface.
  - Con: preserves the wrong data source for interval metrics.
- Hybrid `_tilde` plus phone inputs:
  - Pro: smaller short-term migration burden.
  - Con: duplicates authority and leaves ambiguity about the source of truth.

## Implications and Consequences

- The active metricalc contract must be rewritten around paired `_phone` and
  `_ophone` inputs.
- Active metrics documentation must describe only the new interval definitions,
  formulas, and pause treatment; obsolete `_tilde`-based `ΔC` explanations must
  not remain in active user-facing metrics docs.
- Frontmatter requirements must change so `_tilde` no longer serializes
  `prosody.explicit_word_link_count` as a downstream metrics dependency.
- The active metrics-input and metrics-option portions of the historical
  full-pipeline contract must be superseded additively so fullprosmaker aligns
  with phone/ophone-driven metrics.
- Demo scripts and demo walkthrough material that currently assume tilde-driven
  metrics must be updated to the phone/ophone-driven contract.
- The historical metrics explicit-link override contract must be superseded
  additively so metrics no longer accepts a user-supplied explicit-link count.
- Release 3.0 removes the previous `_tilde` metrics input contract from the
  active design.
- Records that still describe metrics as `_tilde`-driven remain historical and
  must be treated as superseded for active implementation.
- This decision supersedes the active metrics-input aspect of
  [ADR-010](010-metrics-from-text-and-dual-percent-v.md) and the
  metrics-from-`_tilde` downstream portion of
  [ADR-004](004-stage-pipeline-and-pivot-format.md) without removing those
  records from project history.

## Links

- Related ADR: [ADR-040](040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Historical ADR: [ADR-010](010-metrics-from-text-and-dual-percent-v.md)
- Historical pipeline ADR: [ADR-004](004-stage-pipeline-and-pivot-format.md)
- Historical REQ: [REQ-007](../req/007-full-pipeline-orchestration.md)
- Historical REQ: [REQ-017](../req/017-frontmatter-minimization-and-source-flexible-pipeline-inputs.md)
- Related REQ: [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- Related CR: [CR-045](../cr/045-move-mbrola-pho-output-to-phonetizer.md)
- Related runtime/demo surface: `demo/` and wrapper scripts such as
  `scripts/run_fullprosmaker.py`

## Implementation Notes (optional)

- The implementing requirement and CR should define the exact row-to-class
  normalization, interval coalescing rules, CLI pairing behavior, and formulas.
- Active documentation updates should replace old metrics explanations rather
  than presenting both definitions as if they were simultaneously current.

## Reviewed By

- Accepted through CR-046 implementation and verification on 2026-04-10