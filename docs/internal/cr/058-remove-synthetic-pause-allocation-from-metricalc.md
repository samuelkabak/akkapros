---
cr_id: CR-058
status: Done
priority: High
impact: Mutative
created: 2026-04-13
updated: 2026-04-15
implements: 'ADR-044, ADR-045, REQ-030'
---

# Change Request: Remove Synthetic Pause Allocation from Metricalc

# Summary

Remove the remaining synthetic pause-allocation model from metricalc now that
the stage reads realized `_phone.txt` and `_ophone.txt` files whose pause rows
already carry explicit durations.

Under the active code path, metricalc still derives `speech` outputs from
hard-coded transition defaults (`wpm = 193`, `pause_ratio = 35`) and still
allocates pause time across short and long punctuation classes using a fixed
long-weight model plus a later mora-based correction step. That behavior no
longer matches the active source of truth because pause durations now come from
the phonetizer rows themselves.

This CR narrows the temporary transition behavior left in [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md) and the live metrics contract implemented by [CR-046](046-redesign-metricalc-around-phone-ophone-interval-metrics.md). It also relies on the phonetizer-owned silence-row contract established by [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md).

Repository inspection on 2026-04-14 also shows that the current interval-metrics
implementation already coalesces adjacent same-class intervals, including
successive silence rows, before computing `%C`, `%V`, `meanC`, `meanV`, `ΔC`,
`ΔV`, `VarcoC`, `VarcoV`, `rPVI-C`, and `nPVI-V`. This CR makes that behavior
an explicit contract requirement for `_phone.txt` / `_ophone.txt` inputs that
contain multiple consecutive silence rows.

---

# Motivation

Metrics now consumes duration-bearing phone rows directly. Once pause durations
are present in those rows, any later attempt inside metricalc to reconstruct
pause timing from a guessed pause ratio, guessed WPM, punctuation weights, or
mora-based correction is redundant and misleading.

Repository inspection on 2026-04-13 shows that the current implementation still
contains all of the obsolete transition machinery:

- `src/akkapros/lib/metrics.py` still defines `compute_speech_rate()` from
  explicit `wpm` and `pause_ratio` inputs.
- `src/akkapros/lib/metrics.py` still defines `compute_pause_durations()` that
  distributes pause time using `SHORT_PAUSE_PUNCT_WEIGHT`,
  `DEFAULT_LONG_PAUSE_PUNCT_WEIGHT`, and a later short-pause mora correction.
- `src/akkapros/lib/metrics.py` still renders `Speech rate (...)` sections with
  `SPS`, articulation rate, syllable duration, mora duration, and word duration
  derived from those guessed inputs.
- `src/akkapros/lib/metrics.py` still renders a `Pause duration allocation`
  block, including the corrected-long-pause-weight reporting.
- `src/akkapros/cli/metricalc.py` and `src/akkapros/cli/fullprosmaker.py` still
  inject `wpm_words_per_min`, `pause_ratio_percent`,
  `short_pause_punct_weight_unitless`, and
  `fixed_long_pause_punct_weight_unitless` into metrics table run-context.
- `tests/test_metrics_stats.py`, `tests/test_integration.py`, and the metrics
  self-tests in `src/akkapros/lib/metrics.py` still encode the obsolete
  synthetic pause-allocation behavior.
- active package docs still describe the hard-coded transition defaults as part
  of the current metricalc story.

The required change is therefore broader than a table-label rewrite. The stage
contract, result shape, test expectations, and documentation all need to move
to a row-derived pause model.

---

# Scope

## Included

- Remove metricalc's synthetic speech-rate and pause-allocation model.
- Remove the internal use of hard-coded `wpm = 193` and `pause_ratio = 35` in
  metricalc.
- Remove the internal short/long punctuation weight model from metricalc.
- Remove the internal mora-based short-pause correction and corrected-long-pause
  backfill logic from metricalc.
- Compute pause ratio directly from realized phone-row durations for both the
  original and accentuated streams.
- Compute WPM directly from realized phone-row durations for both the original
  and accentuated streams.
- Replace the current `Speech rate (...)` table sections with `Speech metrics`
  sections containing the row-derived duration and rate values requested here.
- Remove the `Pause duration allocation` section completely from the human-
  readable metrics output.
- Remove the current standalone pause-metrics inventory from the human-readable
  output.
- Remove obsolete run-context fields from metricalc and fullprosmaker metrics
  table output.
- Remove or rewrite tests, self-tests, help text, docs, and examples that still
  assert the synthetic pause-allocation contract.
- Keep the interval-acoustic metrics (`%C`, `%V`, `meanC`, `meanV`, `ΔC`, `ΔV`,
  `VarcoC`, `VarcoV`, `rPVI-C`, `nPVI-V`) based on realized row durations.
- Preserve support for `_phone.txt` / `_ophone.txt` streams that contain
  multiple successive silence rows.
- Treat adjacent silence rows as one coalesced pause interval only for the
  preparation of the interval list used by acoustic metrics.
- Preserve row-level pause events separately for pause reporting, drift-facing
  summaries, and any later per-type pause inventory required by newer records
  such as [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md).

## Not Included

- Changing how phonetizer itself realizes durations upstream.
- Removing `phonetize.process.timing_model.speech.wpm` or
  `phonetize.process.timing_model.speech.pause_ratio` from phonetizer-owned
  config. Those remain upstream phonetizer concerns unless a later record
  removes them.
- Redesigning pause typing in phonetizer beyond the temporary metrics mapping
  specified below.
- Introducing a separate original-stream `Pause metrics` table block. This CR
  preserves the current single pause-metrics section placement under the
  accentuated report unless a later record changes that layout.
- Changing the existing interval formulas from [CR-046](046-redesign-metricalc-around-phone-ophone-interval-metrics.md).

---

# Current Behavior

Current repository behavior does not yet treat pause durations carried in
`_phone.txt` / `_ophone.txt` as the sole source of truth for metrics-owned
pause reporting.

Observed current behavior:

- Metricalc still calls `compute_speech_rate(..., wpm, pause_ratio)` for both
  streams even though both streams already contain realized durations.
- Metricalc still computes `pause_metrics` from silence-row counts but then
  separately computes `pause_durations` from guessed pause share rather than
  reading actual silence durations.
- The current table still prints `Speech rate (original):` and `Speech rate
  (accentuated):` instead of the requested `Speech metrics:` label.
- The current table still prints derived metrics that are no longer meaningful
  under explicit pause durations: `SPS (speech)`, `SPS (articulation)`,
  `Average syllable duration`, `Mora duration`, and `Word duration`.
- The current table still prints pause-allocation internals that no longer have
  semantic value: short-pause weight, fixed long-pause weight, initial short and
  long pause durations, corrected short and long pause durations, and corrected
  long-weight ratio.
- The current human-readable output still separates pause reporting into its
  own block instead of folding row-derived duration totals into `Speech
  metrics:`.
- The current JSON/result object still exposes `speech` and `pause_durations`
  substructures built from the obsolete model.
- `docs/akkapros/configuration.md` and `docs/akkapros/metricalc.md` still say
  metricalc uses the hard-coded transition defaults internally.
- Current code already coalesces adjacent same-class rows when preparing the
  interval sequence for acoustic metrics; because silence rows normalize to
  interval class `P`, successive silence rows currently become one pause
  interval with summed duration in the acoustic list.

That last behavior is correct and shall be preserved. What is missing from the
current written contract is an explicit statement that this coalescing applies
to successive silence rows only for interval preparation and does not collapse
the underlying pause rows for reporting.

---

# Proposed Change

Adopt the following active contract.

## 1. Pause durations become the only source of truth inside metricalc

- Metricalc shall treat silence-row durations in `_ophone.txt` and `_phone.txt`
  as authoritative.
- In the active contract, metricalc only reports realized pause classes and
  realized pause durations that already exist in the phone streams.
- Once phone rows are loaded, metricalc shall not extrapolate pause duration,
  pause share, or speech rate from user-provided or internally hard-coded WPM,
  pause-ratio, punctuation-weight, or mora-based correction parameters.
- Metricalc shall not generate pauses, place pauses, resize pauses, or own
  drift-recovery pause policy.
- The synthetic helper path represented today by `compute_pause_durations()`
  shall be removed from the active metricalc contract.
- Any remaining direct-text or punctuation-gap pause helpers may remain only if
  they serve other still-active structural counting tasks and no longer
  participate in synthetic pause-duration derivation.

## 2. Speech metrics are derived from realized row durations

For each stream separately (`original` from `_ophone.txt`, `accentuated` from
`_phone.txt`), metricalc shall compute speech metrics from the row durations in
that same stream.

Definitions per stream:

- `total_duration_ms = sum(duration_ms for all rows)`
- `pause_duration_ms = sum(duration_ms for rows where category == 'S')`
- `articulation_duration_ms = total_duration_ms - pause_duration_ms`
- `pause_ratio = (pause_duration_ms / total_duration_ms) * 100`, or `0` if
  `total_duration_ms == 0`
- `wpm = total_words / (total_duration_ms / 60000)`, or `0` if
  `total_duration_ms == 0`

Word-count source per stream:

- original `wpm` uses `result['original']['stats']['word_stats']['total_words']`
- accentuated `wpm` uses
  `result['accentuated']['stats']['word_stats']['total_words']`

This CR intentionally defines WPM against each stream's own reported word total
and its own elapsed duration, even though merged-unit behavior means original
and accentuated word counts differ.

## 2A. Successive silence rows in interval preparation

Metricalc shall accept `_phone.txt` / `_ophone.txt` streams containing multiple
successive silence rows with no intervening vowel or consonant rows.

For preparation of the interval list used by interval-acoustic metrics only:

- silence rows normalize to one pause interval class `P`
- adjacent `P` intervals shall be coalesced exactly like adjacent `C` or `V`
  intervals
- the coalesced pause interval duration shall equal the sum of the consecutive
  silence-row durations

Examples:

- `C, C, V, C` becomes `C, V, C` with the first `C` interval duration equal to
  the summed duration of the adjacent consonant rows
- `C, V, C, P, P, C, V` becomes `C, V, C, P, C, V` with the `P` interval
  duration equal to the summed duration of the adjacent silence rows
- if two successive silence rows have durations `600` and `600`, the interval
  list used for `%C`, `%V`, `meanC`, `meanV`, `ΔC`, `ΔV`, `VarcoC`, `VarcoV`,
  `rPVI-C`, and `nPVI-V` shall contain one pause interval of `1200`

For pause reporting and row-derived inventories:

- the underlying silence rows remain distinct events
- successive silence rows shall not be merged before pause-type counting,
  per-type averages, intonation-sensitive inspection, or any other row-level
  pause reporting
- this rule preserves support for cases where one realized pause row is
  followed by another realized pause row for a different structural reason
- paragraph-adjacent extra pauses are only an example of that pattern; this CR
  does not freeze which pause `type` or `length` such an extra row must carry

## 3. Table output contract changes

The human-readable table shall replace both existing speech-rate blocks with a
new section label:

```text
Speech metrics:
  Total duration: ... ms
  Total pause duration: ... ms
  Total articulate duration: ... ms
  Pause ratio: ... %
  WPM: ... word/minute
```

Requirements:

- The section shall appear in both the original and accentuated blocks where
  the current speech-rate sections appear.
- The label shall be exactly `Speech metrics:`.
- `Total duration` shall display `total_duration_ms` derived from realized row
  durations.
- `Total pause duration` shall display `pause_duration_ms` derived from
  realized silence-row durations.
- `Total articulate duration` shall display `articulation_duration_ms` derived
  from realized row durations.
- `Pause ratio` shall display a percentage computed from realized row durations.
- `WPM` shall display words per minute computed from realized row durations.
- The table shall no longer print `SPS (speech)`, `SPS (articulation)`,
  `Average syllable duration`, `Mora duration`, or `Word duration`.
- The table shall no longer print `Speech rate (original):` or
  `Speech rate (accentuated):`.
- The table shall not include a standalone `Pause metrics:` section.

## 4. Remove obsolete pause-duration allocation reporting

- The entire `Pause duration allocation` section shall be removed.
- All processing associated only with that removed output shall also be removed.
- The following values shall disappear from active metrics outputs and active
  metrics logic:
  - initial short-pause punctuation duration
  - initial long-pause punctuation duration
  - corrected short-pause punctuation duration
  - corrected long-pause punctuation duration
  - short-pause weight
  - fixed long-pause weight
  - corrected long-pause weight
  - short-pause mora ratio
  - corrected short-pause mora multiple
  - any percentage-of-pause-time allocations derived from that model

## 5. Remove obsolete metrics run-context fields

The metrics table `--- RUN CONFIGURATION ---` block shall no longer include:

- `wpm_words_per_min`
- `pause_ratio_percent`
- `short_pause_punct_weight_unitless`
- `fixed_long_pause_punct_weight_unitless`

This applies to metrics table emission whether it is invoked through
`metricalc.py` or `fullprosmaker.py`.

## 6. Result-shape requirements for JSON and internal consumers

The JSON/result object shall be aligned with the new contract.

- The per-stream `speech` object may remain named `speech`, but it shall no
  longer expose fields derived only from the obsolete guessed model.
- At minimum, the per-stream `speech` object shall expose `total_duration_ms`,
  `pause_duration_ms`, `articulation_duration_ms`, `pause_ratio`, and `wpm`
  computed directly from realized row durations.
- The accentuated result shall no longer expose a `pause_durations` object.
- The active result contract shall not require a standalone `pause_metrics`
  object when all reported pause-related values are already carried in the
  per-stream `speech` object.

## 7. Documentation, help, and test alignment

Active docs, tests, and self-tests shall be narrowed to the new contract.

This explicitly includes:

- `docs/akkapros/metricalc.md`
- `docs/akkapros/metrics-computation.md`
- `docs/akkapros/fullprosmaker.md`
- `docs/akkapros/configuration.md`
- any help-text registry entries or generated config/help references that still
  describe metricalc as using hard-coded metrics timing defaults
- pytest cases in `tests/test_metrics_stats.py`, `tests/test_integration.py`,
  and any other tests that still assert `compute_speech_rate()` or
  `compute_pause_durations()` behavior
- the built-in metrics self-tests in `src/akkapros/lib/metrics.py`

The active documentation must stop presenting metricalc as estimating pause
reporting from `wpm = 193` and `pause_ratio = 35` once this CR is implemented.

Documentation content requirements:

- The affected public docs shall explain that the human-readable metrics output
  now uses `Speech metrics:` rather than `Speech rate (...)`.
- The affected public docs shall explain that `Total duration`, `Total pause
  duration`, `Total articulate duration`, `Pause ratio`, and `WPM` are now
  computed from realized phone-row durations rather than extrapolated from
  metrics-owned defaults or punctuation-weight models.
- The affected public docs shall explain that `Pause duration allocation` was
  removed because pause durations are already materialized upstream in the phone
  streams.
- The affected public docs shall explain that the standalone `Pause metrics:`
  section was removed and that pause reporting now appears only through the
  row-derived speech-duration fields.
- Where JSON output is documented, the docs shall explain that the active
  result shape no longer includes `pause_durations` and does not require a
  standalone `pause_metrics` object as active output.

---

# Technical Design

Architecture notes:

Components:

- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/cli/fullprosmaker.py`
- metrics JSON/table formatting paths
- metrics self-tests and pytest coverage
- active package docs and help/config registries that describe metrics

Design requirements:

- Keep interval-acoustic metrics driven by coalesced `V`, `C`, and `P`
  intervals from realized phone rows.
- Treat successive silence rows as coalescible `P` intervals only inside the
  acoustic-interval preparation step. Do not delete, rewrite, or pre-merge the
  underlying pause rows in the loaded phone streams.
- Compute speech metrics from elapsed row durations, not from guessed tempo.
- Treat pause handling in metrics as reporting only, not pause generation or
  pause-control logic.
- Remove internal constants, helper functions, and display surfaces that exist
  only to support synthetic pause allocation.
- Preserve the distinction between upstream phonetizer timing controls and
  downstream metricalc reporting. Upstream phonetizer config may still use its
  own timing model; downstream metricalc must not mirror that model once rows
  are realized.
- Keep the change minimal to the metrics formulas that remain valid.

Recommended implementation direction:

- replace `compute_speech_rate()` with a row-derived helper such as
  `compute_speech_metrics_from_rows()` or equivalent
- remove `compute_pause_durations()` from the active library API
- rewrite `format_table()` so it emits the expanded `Speech metrics:` section
  and no standalone `Pause metrics:` or `Pause duration allocation` blocks
- remove now-obsolete run-context injection from CLI wrappers

---

# Files Likely Affected

`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/helpmsg.py`
`tests/test_metrics_stats.py`
`tests/test_integration.py`
`tests/test_selftests_lib.py`
`tests/test_selftests_cli.py`
`docs/akkapros/metricalc.md`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/fullprosmaker.md`
`docs/akkapros/configuration.md`

---

# Acceptance Criteria

- [ ] Given metricalc loads `_ophone.txt` and `_phone.txt`, when speech metrics
      are computed for each stream, then `pause_ratio` is derived from actual
      silence-row durations in that stream and not from an input or hard-coded
      pause-ratio parameter.
- [ ] Given metricalc loads `_ophone.txt` and `_phone.txt`, when speech metrics
      are computed for each stream, then `wpm` is derived from the stream's own
      reported word count and actual total elapsed duration and not from an
      input or hard-coded WPM parameter.
- [ ] Given the human-readable metrics table is rendered, when the original
  block is inspected, then it contains a `Speech metrics:` section with
  `Total duration`, `Total pause duration`, `Total articulate duration`,
  `Pause ratio`, and `WPM`.
- [ ] Given the human-readable metrics table is rendered, when the accentuated
  block is inspected, then it contains a `Speech metrics:` section with
  `Total duration`, `Total pause duration`, `Total articulate duration`,
  `Pause ratio`, and `WPM`.
- [ ] Given the human-readable metrics table is rendered, when speech sections
      are searched, then `Speech rate (original):` and `Speech rate
      (accentuated):` do not appear.
- [ ] Given the human-readable metrics table is rendered, when speech sections
      are searched, then `SPS (speech)`, `SPS (articulation)`, `Average
      syllable duration`, `Mora duration`, and `Word duration` do not appear.
- [ ] Given the human-readable metrics table is rendered, when pause reporting
      is inspected, then no `Pause duration allocation` section appears.
- [ ] Given the human-readable metrics table is rendered, when output sections
  are searched, then no standalone `Pause metrics:` section appears.
- [ ] Given the metrics table run-context is rendered, when the configuration
      block is inspected, then `wpm_words_per_min`, `pause_ratio_percent`,
      `short_pause_punct_weight_unitless`, and
      `fixed_long_pause_punct_weight_unitless` are absent.
- [ ] Given the metrics JSON/result object is emitted, when per-stream `speech`
      objects are inspected, then they do not contain fields that exist only for
      the obsolete guessed speech-rate model.
- [ ] Given the metrics JSON/result object is emitted, when per-stream `speech`
  objects are inspected, then they include `total_duration_ms`,
  `pause_duration_ms`, `articulation_duration_ms`, `pause_ratio`, and
  `wpm` as directly row-derived values.
- [ ] Given the metrics JSON/result object is emitted, when the accentuated
      block is inspected, then no `pause_durations` object is present.
- [ ] Given the metrics JSON/result object is emitted, when the accentuated
  block is inspected, then no standalone `pause_metrics` object is required
  by the active contract.
- [ ] Given `_phone.txt` or `_ophone.txt` contains two or more successive
  silence rows, when the acoustic interval list is prepared for `%C`, `%V`,
  `meanC`, `meanV`, `ΔC`, `ΔV`, `VarcoC`, `VarcoV`, `rPVI-C`, and
  `nPVI-V`, then those adjacent silence rows contribute one coalesced `P`
  interval whose duration is the sum of their durations.
- [ ] Given `_phone.txt` or `_ophone.txt` contains two or more successive
  silence rows, when pause rows are counted or grouped for reporting, then
  those rows remain separate pause events rather than being collapsed away
  before row-level reporting.
- [ ] Given the metrics library API and self-tests are inspected, when obsolete
      pause-allocation helpers are reviewed, then the synthetic pause-duration
      derivation path is absent from the active contract.
- [ ] Given active package docs and help text are inspected, when metricalc's
      pause handling is described, then they do not present `wpm = 193`,
      `pause_ratio = 35`, or punctuation-weight-based pause allocation as the
      active metrics behavior.
- [ ] Given the affected public docs are inspected, when the new metrics output
  is explained, then they describe the expanded `Speech metrics:` section and
  the removal of both `Pause duration allocation` and standalone `Pause
  metrics:` reporting.
- [ ] Given the affected public docs are inspected, when JSON/result output is
  described, then they do not present `pause_durations` as part of the
  active metrics result contract.

---

# Risks / Edge Cases

Possible issues:

- Original and accentuated `WPM` will differ because merged-unit behavior means
  the two sections report different word totals. This CR treats that as correct
  under the current word-statistics contract.
- Very short samples may produce unstable or unintuitive `WPM` because the
  denominator is actual elapsed duration.
- If a malformed phone stream has zero total duration, this CR requires `0`
  instead of division failure.
- If upstream phonetizer pause typing changes, metricalc reporting and its
  documentation will need to stay aligned with the emitted row semantics.

---

# Testing Strategy

Unit tests:

- verify row-derived pause-ratio computation for both streams
- verify row-derived WPM computation for both streams
- verify row-derived `total_duration_ms`, `pause_duration_ms`, and
  `articulation_duration_ms` for both streams
- verify interval preparation collapses adjacent silence rows into one `P`
  interval with summed duration
- verify pause reporting still counts successive silence rows as separate row
  events
- verify `pause_durations` no longer appears in result data
- verify no standalone `pause_metrics` block is required by the active result
  contract

Integration tests:

- verify emitted table no longer contains `Pause duration allocation`
- verify emitted table uses `Speech metrics:` instead of `Speech rate (...)`
- verify obsolete run-context keys are absent

Manual verification:

- inspect a representative `_metrics.txt` output such as `outputs/erra_metrics.txt`
  and confirm that the pause and speech sections now reflect row-derived values
  only

---

# Rollback Plan

Revert the implementation that removes synthetic pause allocation and restore
the previous metricalc output contract.

Because this CR intentionally removes obsolete output fields and changes result
shape, rollback should be treated as a full contract reversal rather than a
partial toggle.

---

# Related Issues

- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- [CR-046](046-redesign-metricalc-around-phone-ophone-interval-metrics.md)
- [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md)

---

# Tasks

## Implementation

- [x] Remove synthetic speech-rate and pause-allocation helpers from metricalc
- [x] Compute row-derived speech metrics for both streams
- [x] Rewrite metrics table output so speech totals and rates appear only under
  `Speech metrics:`
- [x] Remove obsolete metrics run-context fields from CLI wrappers

## Tests

- [x] Rewrite unit tests that currently assert `compute_speech_rate()` or
      `compute_pause_durations()`
- [x] Rewrite metrics self-tests for the new table/result shape
- [x] Update integration expectations for removed output fields and renamed
      sections

## Documentation

- [x] Rewrite active metrics docs that still describe the hard-coded transition
      timing model
- [x] Add explicit explanation of the new metrics output sections, removed
  sections, and the expanded `Speech metrics:` fields in the affected public
  docs
- [x] Update package docs/help so metricalc is described as row-derived for
      pause and speech reporting

## Review

- [x] Verify acceptance criteria against emitted metrics artifacts
- [x] Confirm no active doc/help surface still presents synthetic pause
      allocation as current behavior

---

# Implementation Blockers

None currently identified.

---

# Notes

- This CR does not remove upstream phonetizer timing controls. It removes only
  downstream metricalc's reuse of a synthetic timing model after realized phone
  rows already exist.