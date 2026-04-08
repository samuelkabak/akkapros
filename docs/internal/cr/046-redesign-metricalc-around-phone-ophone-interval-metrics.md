---
cr_id: CR-046
status: Draft
priority: High
impact: Mutative
created: 2026-04-08
updated: 2026-04-08
implements: 'ADR-044, REQ-024, REQ-030'
---

# Change Request: Redesign metricalc Around Phone/Ophone Interval Metrics

# Summary

Redesign metricalc so the stage takes `_phone.txt` as its primary input,
resolves `_ophone.txt` from `--ophone` or by filename discovery, computes
rhythm metrics from phone-derived interval durations, and rewrites the active
metrics documentation around the new interval definitions.

This change also removes the active metrics dependency on
`metadata.data.prosody.explicit_word_link_count` in `_tilde` frontmatter,
because explicit-link information is now encoded in the phonetizer outputs, and
removes the obsolete `--explicit-link-count` metrics override.

Big-picture requirement chain for implementation context:

- [REQ-024](../req/024-replacement-of-timing-model.md): umbrella program story
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md): metricalc redesign around phone/ophone inputs
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md): upstream phonetizer timing contract consumed by metricalc

---

# Motivation

The current metrics contract is built around the wrong source and the wrong
active explanation for `ΔC`, `ΔV`, `VarcoC`, and related measures. The
phonetizer now owns the actual duration-bearing representation, so metrics
should consume that representation directly.

Keeping `_tilde` as the active metrics source would preserve obsolete logic,
duplicate already-encoded structure, and force the documentation to defend a
definition the project no longer wants to treat as correct.

---

# Scope

## Included

- Change the active metricalc input contract from `_tilde.txt` to paired
  `_ophone.txt` and `_phone.txt` artifacts.
- Define metricalc CLI input as positional `_phone.txt` plus optional
  `--ophone <path>`, with `_ophone` auto-discovered from the input filename when
  the option is absent.
- Redefine the metrics core around phone-derived interval tuples of class and
  duration.
- Require interval coalescing by merging adjacent rows of the same class and
  summing durations.
- Require hiatus and vowel-transition rows to be treated as consonants during
  metrics interval formation.
- Compute the following active rhythm metrics for both original and accentuated
  sections:
  - `%C`, `meanC`, `ΔC`, `VarcoC`, `rPVI-C`
  - `%V`, `meanV`, `ΔV`, `VarcoV`, `nPVI-V`
- Require pause treatment where pauses remain in the total-duration denominator
  for `%V` and `%C`, but are excluded from `mean`, `Δ`, `Varco`, and PVI
  calculations.
- Require syllable counts, syllable-type ratios, accentuation counts, and other
  structural ratios to be derived from phone/ophone files only.
- Require `explicit_word_link_count` to be computed from encoded phone/ophone
  structure rather than inherited from `_tilde` frontmatter.
- Remove `prosody.explicit_word_link_count` from the active `_tilde`
  frontmatter contract.
- Remove the obsolete `--explicit-link-count` CLI parameter from metricalc and
  from full pipeline orchestration.
- Preserve frontmatter on `_phone.txt` and `_ophone.txt`.
- Keep MBROLA artifacts without frontmatter and outside the metrics input
  contract.
- Keep the active metrics indicator inventory complete under the new design,
  except for surfaces already removed by separate accepted records.
- Align fullprosmaker and active pipeline docs/help with the new metrics input
  behavior.
- Maintain demo scripts and demo walkthroughs so they follow the new
  phone/ophone-driven metrics contract.
- Rewrite active metrics documentation and help text so they describe only the
  new metrics definitions and the new input contract.
- Remove the previous `_tilde`-driven metrics input contract from the v3
  release design.

## Not Included

- Redesigning the phonetizer row schema itself.
- Making MBROLA artifacts valid inputs for metrics.
- Keeping the old `_tilde`-based `ΔC` interpretation as a supported active
  alternative.
- Rewriting historical internal records as though the older definition never
  existed.

---

# Current Behavior

The current active metrics records still say that metricalc reads `_tilde.txt`
and computes rhythm metrics from reconstructed symbolic structure. They also
retain a frontmatter dependency on `explicit_word_link_count` inherited from
`metadata.data.prosody`.

That no longer matches the architecture now that phonetizer emits paired
duration-bearing streams and encodes the structural information metrics needs.

---

# Proposed Change

Adopt the following active metrics design.

## 1. Input contract

- metricalc consumes positional `<prefix>_phone.txt` as the accentuated stream
- `--ophone PATH` optionally supplies the original stream
- if `--ophone` is absent and the positional input ends with `_phone.txt`, the
  stage derives the original stream path by replacing the suffix with
  `_ophone.txt`
- if the derived `_ophone.txt` path does not exist, the command fails clearly
  and emits no metrics output
- `_ophone.txt` is the source of original metrics
- `_phone.txt` is the source of accentuated metrics
- `_tilde.txt` is no longer parsed as an active metrics input
- `_mbrola.pho` and `_ombrola.pho` are not metrics inputs

## 2. Interval-building algorithm

Metrics shall build a normalized row stream of tuples:

```python
('V' | 'C' | 'P', duration_ms)
```

Normalization rules:

- any phonetizer row with `category=V` maps to `V`
- any phonetizer row with `category=C` maps to `C`
- hiatus rows and vowel-transition rows remain in `C`
- any phonetizer row with `category=S` maps to `P`

The algorithm shall then coalesce adjacent tuples of the same class by summing
their durations.

Example after coalescing:

```python
[('V', 150), ('C', 120), ('P', 100), ('C', 45), ('V', 245)]
```

Example before coalescing:

```python
[('V', 150), ('C', 80), ('C', 40), ('P', 100), ('C', 45), ('V', 245)]
```

## 3. Metric formulas

Let `V` be the list of vocalic interval durations, `C` the list of consonantal
interval durations, and `Total = sum(V) + sum(C) + sum(P)` over all intervals.

The active formulas are:

- `%V = (sum(V) / Total) * 100`
- `%C = (sum(C) / Total) * 100`
- `meanV = arithmetic_mean(V)`
- `meanC = arithmetic_mean(C)`
- `ΔV = population_standard_deviation(V)`
- `ΔC = population_standard_deviation(C)`
- `VarcoV = (ΔV / meanV) * 100`
- `VarcoC = (ΔC / meanC) * 100`
- `rPVI-C = mean(abs(C[k] - C[k+1]))`
- `nPVI-V = 100 * mean(abs((V[k] - V[k+1]) / ((V[k] + V[k+1]) / 2)))`

Pause intervals are excluded from `meanV`, `meanC`, `ΔV`, `ΔC`, `VarcoV`,
`VarcoC`, `rPVI-C`, and `nPVI-V`, but remain included in `Total` for `%V` and
`%C`.

Fallback rules:

- if a class has no intervals, its `%`, `mean`, `Δ`, `Varco`, and PVI-family
  values are `0`
- if a class has fewer than two intervals, its `Δ` and PVI-family values are
  `0`

## 4. Structural statistics

- syllable counts and syllable ratios must be derived from the structure encoded
  in phone/ophone files
- accentuation statistics must be derived from the difference between the paired
  streams and/or encoded row structure, not by reparsing `_tilde`
- explicit word-link counts must be computed from encoded phone/ophone link
  information
- the redesign keeps the active metrics indicator inventory complete,
  including structural, moraic, prominence, merge, accentuation, and
  speech/timing indicators, except where a separate accepted record has already
  removed an output surface

## 5. Frontmatter changes

- `_tilde` frontmatter shall no longer expose
  `metadata.data.prosody.explicit_word_link_count` as an active downstream
  metrics dependency
- metricalc no longer accepts `--explicit-link-count`; explicit-link counts are
  always derived internally from phone/ophone structure
- `_phone.txt` and `_ophone.txt` retain frontmatter
- `_mbrola.pho` and `_ombrola.pho` do not carry frontmatter

## 6. Documentation rewrite requirement

Active metrics documentation must be rewritten so that it describes only the new
phone/ophone-based interval metrics.

This explicitly includes:

- `docs/akkapros/metrics-computation.md`
- `docs/akkapros/metricalc.md`
- `docs/akkapros/fullprosmaker.md`
- generated CLI help text and configuration/help registries that describe
  metrics inputs or formulas

Those docs must not continue to present the previous `_tilde`-based `ΔC` model
as current behavior.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/cli/fullprosmaker.py`
- `scripts/run_fullprosmaker.py`
- `demo/`
- phonetizer output/frontmatter serialization
- metrics help text, docs, and examples
- pipeline orchestration docs and config docs that mention metrics inputs

Design requirements:

- input resolution must ensure both `_ophone.txt` and `_phone.txt` are available
- interval construction must be deterministic and derived from row classes and
  durations only
- the same formulas must drive all output formats
- metrics must not read MBROLA files
- frontmatter dependencies must be minimized where encoded phone structure makes
  reconstruction unnecessary
- active documentation must be corrected, not merely appended with a competing
  obsolete explanation
- release 3.0 removes the previous `_tilde` metrics input contract from the
  active implementation design

---

# Files Likely Affected

`docs/internal/adr/044-phone-interval-metrics-from-phonetizer-streams.md`
`docs/internal/req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md`
`docs/internal/req/004-metrics-computation.md`
`docs/internal/req/015-frontmatter-derived-word-indicators-in-metrics.md`
`docs/internal/req/017-frontmatter-minimization-and-source-flexible-pipeline-inputs.md`
`docs/internal/req/007-full-pipeline-orchestration.md`
`docs/internal/cr/022-add-frontmatter-derived-word-indicators-to-metrics.md`
`docs/internal/cr/024-minimize-frontmatter-and-enable-source-flexible-stage-inputs.md`
`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/fullprosmaker.py`
`scripts/run_fullprosmaker.py`
`demo/`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/metricalc.md`
`docs/akkapros/fullprosmaker.md`
`docs/akkapros/configuration.md`

---

# Acceptance Criteria

- [ ] metricalc accepts positional `_phone.txt` plus optional `--ophone` and
  resolves paired `_ophone.txt` and `_phone.txt` as its active metrics
  inputs.
- [ ] metricalc does not compute active metrics from `_tilde.txt`.
- [ ] metrics input normalization produces interval tuples with class `V`, `C`,
      or `P` and integer duration.
- [ ] hiatus and vowel-transition phonetizer rows are normalized into
  consonantal intervals.
- [ ] adjacent same-class tuples are merged before metric computation.
- [ ] `%C`, `meanC`, `ΔC`, `VarcoC`, and `rPVI-C` are computed from consonantal
      intervals only.
- [ ] `%V`, `meanV`, `ΔV`, `VarcoV`, and `nPVI-V` are computed from vocalic
      intervals only.
- [ ] pauses remain in the total-duration denominator for `%V` and `%C`.
- [ ] pauses are excluded from `mean`, `Δ`, `Varco`, and PVI families.
- [ ] original metrics are derived from `_ophone.txt` and accentuated metrics
      are derived from `_phone.txt`.
- [ ] explicit word-link counts are computed from phone/ophone structure rather
      than `_tilde` frontmatter.
- [ ] `_tilde` frontmatter no longer carries `prosody.explicit_word_link_count`
      as an active metrics dependency.
- [ ] metricalc no longer exposes `--explicit-link-count` as an active CLI
  interface.
- [ ] `_phone.txt` and `_ophone.txt` retain frontmatter.
- [ ] `_mbrola.pho` and `_ombrola.pho` do not carry frontmatter.
- [ ] the redesign keeps the active metrics indicator inventory complete,
      except for surfaces already removed by separate accepted records.
- [ ] active metrics documentation is rewritten to describe only the new
      interval definitions and formulas.
- [ ] active full pipeline documentation and help text are aligned with the new
  phone/ophone metrics behavior.
- [ ] demo scripts and demo walkthroughs are aligned with the new phone/ophone
      metrics behavior.
- [ ] Built-in metrics `run_tests()` coverage asserts all computed indicators
  for both original and accentuated streams, including `%C`, `meanC`, `ΔC`,
  `VarcoC`, `rPVI-C`, `%V`, `meanV`, `ΔV`, `VarcoV`, and `nPVI-V`.
- [ ] Pytest coverage asserts all computed indicators for both original and
  accentuated streams, including `%C`, `meanC`, `ΔC`, `VarcoC`, `rPVI-C`,
  `%V`, `meanV`, `ΔV`, `VarcoV`, and `nPVI-V`.

---

# Risks / Edge Cases

Possible issues:

- paired phone/ophone files could drift structurally and produce incomparable
  original/accentuated results unless validation is explicit
- old documentation could survive in one help surface and keep the obsolete
  `ΔC` explanation alive
- explicit word-link counting must distinguish encoded explicit links from other
  downstream structural joins
- interval classification must be stable for silence-like rows and any future
  foreign-symbol extensions

---

# Testing Strategy

Specification-level verification:

- confirm the active metrics contract names `_phone.txt` and `_ophone.txt` as
  inputs
- confirm `_tilde` is no longer documented as the active metrics input
- confirm the documented formulas match the required interval-based definitions
- confirm `_tilde` frontmatter no longer carries the explicit-link counter for
  metrics

Implementation-level tests to require later:

- tuple normalization from phone rows into `V/C/P`
- hiatus and vowel-transition rows asserted as consonantal in metrics
- adjacent same-class coalescing
- `%V/%C` denominator includes pauses
- pauses excluded from `Δ`, `Varco`, and PVI families
- `rPVI-C` and `nPVI-V` exact regression tests on fixed interval lists
- zero-interval and one-interval fallback behavior
- explicit-link counts derived from phone/ophone structure
- paired-stream original/accentuated output consistency
- built-in `run_tests()` coverage for all computed indicators in both streams
- pytest coverage for all computed indicators in both streams
- manual expected-value calculations carried over from existing tests and
  reworked for the new interval design

---

# Rollback Plan

If this redesign is rejected, keep metricalc on `_tilde` and retain the
existing `_tilde` frontmatter dependency for explicit link counts until another
replacement is approved.

---

# Related Issues

- Historical metrics requirement:
  [REQ-004](../req/004-metrics-computation.md)
- Historical frontmatter dependency requirement:
  [REQ-015](../req/015-frontmatter-derived-word-indicators-in-metrics.md)
- Historical frontmatter minimization requirement:
  [REQ-017](../req/017-frontmatter-minimization-and-source-flexible-pipeline-inputs.md)
- Phonetizer architecture dependency:
  [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)

---

# Tasks

## Implementation

- [ ] Rebase metricalc input handling onto paired phone/ophone artifacts.
- [ ] Implement row classification and interval coalescing.
- [ ] Recompute rhythm metrics from interval durations.
- [ ] Remove `_tilde` explicit-link frontmatter dependency.
- [ ] Remove the obsolete `--explicit-link-count` interface and related
  fullprosmaker propagation.
- [ ] Preserve the historical indicator inventory under the new data source.
- [ ] Add or update built-in `run_tests()` assertions for every computed
  indicator in original and accentuated outputs.
- [ ] Add or update pytest coverage for every computed indicator in original
  and accentuated outputs.
- [ ] Recreate metrics tests from the existing suite by manually executing the
  new calculations for fixed inputs.

## Documentation

- [ ] Rewrite active metrics docs around the new formulas only.
- [ ] Update help text and examples to name `_phone`/`_ophone` as inputs.
- [ ] Update frontmatter docs to remove `prosody.explicit_word_link_count` from
      `_tilde` outputs.
- [ ] Update full pipeline docs and help text so metrics no longer appears as a
  `_tilde`-driven stage.
- [ ] Update demo scripts and demo walkthroughs so they use phone/ophone-driven
  metrics behavior.

## Review

- [ ] Confirm the v3 implementation removes the previous `_tilde` metrics input
  contract.

---

# Notes for CR-046

This CR intentionally treats the previous active `ΔC` interpretation as
historical rather than co-equal. The documentation work must therefore replace
the old active explanation in metrics docs, not merely append the new formulas
under an additional heading.

Test-note constraint: grouped tests are acceptable only when one broken formula
cannot be masked by another broken formula in the same assertion block.