---
req_id: REQ-030
status: Draft
priority: High
impact: Mutative
created: 2026-04-08
updated: 2026-04-08
related_adrs: 'ADR-044, ADR-040'
implemented_by: 'CR-046'
---

# Requirement: Phone/Ophone-Only Metrics and Interval Rhythm Computation

# Summary

The metrics stage shall take `<prefix>_phone.txt` as its primary input,
resolve the matching original stream from `--ophone` or from the corresponding
`<prefix>_ophone.txt` filename, and compute all active rhythm statistics from
those paired phonetizer files only. The stage shall no longer parse
`_tilde.txt` as an active metrics input.

The active metrics model shall derive vocalic, consonantal, and pause intervals
from duration-bearing phone rows, then compute the interval statistics `%C`,
`meanC`, `ΔC`, `VarcoC`, `rPVI-C`, `%V`, `meanV`, `ΔV`, `VarcoV`, and
`nPVI-V` for both original and accentuated streams, while keeping the active
metrics output inventory complete unless a separate accepted record has already
removed a surface.

Metricalc shall also read the phonetizer-provided drift summary carried in
phone/ophone frontmatter and report those drift statistics in its public table
and JSON outputs instead of recomputing drift independently.

---

# Motivation

The phonetizer now encodes the timing and structural information that metrics
needs. Recomputing rhythmic structure from `_tilde` is both redundant and wrong
for the intended literature-based interval measures.

This requirement is needed to make metricalc depend on the actual duration
representation, to remove obsolete `_tilde` frontmatter dependencies, and to
replace the previous incorrect understanding of `ΔC`, `ΔV`, `VarcoC`, and
related interval metrics.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given metricalc runs under the active contract, when it reads rhythmic
      input, then it consumes `_phone.txt` and `_ophone.txt` only and does not
      compute active metrics from `_tilde.txt`.
- [ ] Given metricalc CLI input is resolved, when the user supplies the
      positional metrics input, then that positional input is the accentuated
      `_phone.txt` artifact.
- [ ] Given metricalc is invoked with `--ophone PATH`, when the original stream
      input is resolved, then the stage reads that exact `_ophone.txt` path.
- [ ] Given metricalc is invoked without `--ophone`, when the positional input
      path ends with `_phone.txt`, then the stage derives the original path by
      replacing that suffix with `_ophone.txt`.
- [ ] Given metricalc is invoked without `--ophone`, when the derived
      `_ophone.txt` path does not exist, then the command fails clearly and
      emits no metrics output.
- [ ] Given `_mbrola.pho` or `_ombrola.pho` files are present, when metrics
      input is resolved, then those files are not treated as valid metrics
      inputs.
- [ ] Given `_phone.txt` and `_ophone.txt` are inspected, when metadata is
      required, then frontmatter is read from those files and not from MBROLA
      artifacts.
- [ ] Given `_phone.txt` and `_ophone.txt` frontmatter includes
      `data.drift.max`, `data.drift.mean`, and `data.drift.stddev`, when
      metricalc loads the paired phonetizer artifacts, then it reads those
      three fields from frontmatter rather than recomputing drift statistics
      from the row stream.
- [ ] Given phone rows are traversed, when rows are normalized for rhythm
      computation, then each row is mapped to one of exactly three interval
      classes: `V`, `C`, or `P`.
- [ ] Given a phonetizer row has consonant category, when it is normalized for
      interval computation, then it maps to class `C`, including hiatus rows
      and vowel-transition rows.
- [ ] Given a row originates from `˙` / `ARU -> AL` or from `¨` / `ENA -> WA`
      or `ENA -> YI`, when it is normalized for interval computation, then it
      is treated as consonantal.
- [ ] Given the normalized class stream contains adjacent rows of the same
      class, when interval lists are formed, then the adjacent rows are merged
      into one interval and their durations are summed.
- [ ] Given a silence row or silence-like phone-row encoding is encountered,
      when it enters the normalized interval list, then it is treated as class
      `P` for pause.
- [ ] Given a normalized interval list exists, when `%V` is computed, then the
      numerator is the sum of `V` interval durations and the denominator is the
      total duration of `V + C + P` intervals.
- [ ] Given a normalized interval list exists, when `%C` is computed, then the
      numerator is the sum of `C` interval durations and the denominator is the
      total duration of `V + C + P` intervals.
- [ ] Given pause intervals exist, when `meanV`, `ΔV`, `VarcoV`, and `nPVI-V`
      are computed, then pause intervals are excluded from those calculations.
- [ ] Given pause intervals exist, when `meanC`, `ΔC`, `VarcoC`, and `rPVI-C`
      are computed, then pause intervals are excluded from those calculations.
- [ ] Given at least one vocalic interval exists, when `meanV` is computed,
      then it equals the arithmetic mean of vocalic interval durations.
- [ ] Given at least one consonantal interval exists, when `meanC` is
      computed, then it equals the arithmetic mean of consonantal interval
      durations.
- [ ] Given a duration list for one class, when `ΔV` or `ΔC` is computed, then
      the metric is the population standard deviation of interval durations in
      milliseconds.
- [ ] Given `ΔV` and `meanV` are available, when `VarcoV` is computed, then it
      equals `(ΔV / meanV) * 100`.
- [ ] Given `ΔC` and `meanC` are available, when `VarcoC` is computed, then it
      equals `(ΔC / meanC) * 100`.
- [ ] Given no vocalic intervals exist, when `%V`, `meanV`, `ΔV`, `VarcoV`, or
      `nPVI-V` are computed, then the reported value is `0`.
- [ ] Given no consonantal intervals exist, when `%C`, `meanC`, `ΔC`,
      `VarcoC`, or `rPVI-C` are computed, then the reported value is `0`.
- [ ] Given fewer than two vocalic intervals exist, when `ΔV` or `nPVI-V` is
      computed, then the reported value is `0`.
- [ ] Given fewer than two consonantal intervals exist, when `ΔC` or `rPVI-C`
      is computed, then the reported value is `0`.
- [ ] Given at least two consonantal intervals exist, when `rPVI-C` is
      computed, then it equals the arithmetic mean of the absolute differences
      between adjacent consonantal interval durations.
- [ ] Given at least two vocalic intervals exist, when `nPVI-V` is computed,
      then it equals `100 * mean(abs((d_k - d_{k+1}) / ((d_k + d_{k+1}) / 2)))`
      over adjacent vocalic intervals.
- [ ] Given the paired `_ophone.txt` and `_phone.txt` streams are available,
      when metrics are reported, then the original section is computed from
      `_ophone.txt` and the accentuated section is computed from `_phone.txt`.
- [ ] Given phonetizer drift summary is present in both paired streams, when
      metricalc renders its human-readable table output, then it reports drift
      statistics for each stream including `max`, `mean`, and `stddev`.
- [ ] Given phonetizer drift summary is present in both paired streams, when
      metricalc renders JSON output, then it includes the consumed frontmatter
      drift summary for each stream with subfields `max`, `mean`, and
      `stddev`.
- [ ] Given syllable counts, syllable ratios, accentuation counts, or related
      structural ratios are reported, when their source is traced, then they are
      derived from phone/ophone file content and retained frontmatter only, not
      from reparsing `_tilde.txt`.
- [ ] Given `explicit_word_link_count` is needed by metrics, when the count is
      computed, then it is derived from the link information encoded in
      phone/ophone files rather than inherited from `_tilde` frontmatter.
- [ ] Given metricalc CLI help or option parsing is inspected, when explicit
      link handling is reviewed, then `--explicit-link-count` is absent from the
      active CLI contract.
- [ ] Given `_tilde.txt` frontmatter is serialized under the active contract,
      when `metadata.data.prosody` is emitted, then it does not include
      `explicit_word_link_count` for metrics consumption.
- [ ] Given the redesign is implemented, when the metrics output inventory is
      reviewed against the active metrics surface, then the full indicator set
      remains computed under the new design except surfaces already removed by
      separate accepted records such as metrics CSV output.
- [ ] Given the redesign is implemented, when public outputs are inspected,
      then they continue to include the previously computed structural,
      prominence, syllable, moraic, accentuation, merge, and speech/timing
      indicators in addition to the redefined interval metrics.
- [ ] Given full pipeline orchestration or fullprosmaker documentation is
      updated under the active contract, when the metrics stage is described,
      then it is described as operating on phone/ophone inputs rather than on
      `_tilde`, and obsolete metrics input flags are not presented as current
      behavior.
- [ ] Given demo scripts or demo walkthrough material invoke metricalc or the
      full pipeline, when they are updated under the active contract, then they
      use phone/ophone-driven metrics behavior and do not present `_tilde` as
      the active metrics input.
- [ ] Given active metrics documentation is updated, when the input contract and
      formulas are described, then the documentation describes only the new
      phone/ophone-based interval definitions and does not present the previous
      active `ΔC` interpretation as current behavior.
- [ ] Given tests are updated for this redesign, when expected values are
      defined, then the expected metrics values are computed manually from fixed
      inputs rather than being regenerated by the same implementation logic
      under test.

---

# User Story (optional)
> As a researcher using metricalc, I want rhythm metrics to be computed from
> the actual phonetizer duration streams so that the reported interval measures
> reflect the encoded phonetic timing rather than a reconstructed `_tilde`
> approximation.

---

# Interface Notes
- Inputs:
      - positional `<prefix>_phone.txt`
      - optional `--ophone <prefix>_ophone.txt`
- Non-inputs:
  - `<prefix>_tilde.txt` for active metrics computation
  - `<prefix>_mbrola.pho` and `<prefix>_ombrola.pho`
- Outputs:
  - the active metrics artifacts already owned by metricalc
- Frontmatter-derived drift input:
      - `data.drift.max`
      - `data.drift.mean`
      - `data.drift.stddev`
- Normalized interval representation:

```python
[('V', 150), ('C', 120), ('P', 100), ('C', 45), ('V', 245)]
```

- Example before coalescing adjacent same-class rows:

```python
[('V', 150), ('C', 80), ('C', 40), ('P', 100), ('C', 45), ('V', 245)]
```

- Affected components:
  - `src/akkapros/cli/metricalc.py`
  - `src/akkapros/lib/metrics.py`
      - `src/akkapros/cli/fullprosmaker.py`
      - `scripts/run_fullprosmaker.py`
      - `demo/`
  - phonetizer output/frontmatter contracts
  - metrics documentation and help text
- Historical indicator inventory retained from:
 - Active indicator inventory carried forward from:
      - [REQ-004](004-metrics-computation.md)
      - [REQ-015](015-frontmatter-derived-word-indicators-in-metrics.md)
      except where a separate accepted record has already removed an output surface.
- Drift reporting source:
      - phonetizer frontmatter in `_phone.txt` and `_ophone.txt`
      - not a metricalc recomputation from interval or row data

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: large
- Migration:
  - rebase metricalc input resolution onto paired phonetizer files
      - remove `_tilde` frontmatter dependence for `explicit_word_link_count`
      - remove the obsolete `--explicit-link-count` CLI override
      - align full pipeline orchestration and docs with phone/ophone-driven metrics
                  - remove the previous `_tilde` metrics input contract from the v3 design
                  - update demo scripts and demo walkthroughs that currently assume
                        `_tilde`-driven metrics
  - rewrite active metrics documentation around the new interval formulas only

# Related
- Related ADRs: [ADR-044](../adr/044-phone-interval-metrics-from-phonetizer-streams.md),
  [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Historical REQs: [REQ-004](004-metrics-computation.md),
  [REQ-015](015-frontmatter-derived-word-indicators-in-metrics.md),
      [REQ-017](017-frontmatter-minimization-and-source-flexible-pipeline-inputs.md),
      [REQ-007](007-full-pipeline-orchestration.md)
- Implementation CRs: [CR-046](../cr/046-redesign-metricalc-around-phone-ophone-interval-metrics.md)

# Non-Goals
- This requirement does not redefine the phonetizer row schema itself.
- This requirement does not make MBROLA files valid metrics inputs.
- This requirement does not preserve the old `_tilde`-based interval formulas as
  an alternative active mode.
- This requirement does not preserve the obsolete `--explicit-link-count`
      override as a supported active interface.
- This requirement does not retain the previous `_tilde` metrics input contract
      in the v3 release.

# Security / Safety Considerations
- Metrics must fail clearly if the paired phone/ophone inputs are inconsistent,
  missing, or malformed rather than silently mixing data sources.