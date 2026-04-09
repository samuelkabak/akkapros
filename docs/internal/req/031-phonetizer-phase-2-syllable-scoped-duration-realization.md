---
req_id: REQ-031
status: Draft
priority: High
impact: Mutative
created: 2026-04-08
updated: 2026-04-09
related_adrs: 'ADR-041, ADR-040, ADR-039'
implemented_by: 'CR-040 and follow-up CRs'
---

# Requirement: Phonetizer Phase 2 Syllable-Scoped Duration Realization

# Summary

The system shall realize phonetizer Phase 2 durations by traversing prebuilt
phone rows as a sequence of syllables and pauses only.

Within this Phase 2 model, the active syllable inventory is reduced to four
non-accentuated categories and four accentuated categories because hiatus and
vowel-transition rows are treated as consonantal structure for timing. The
solver is syllable-scoped: it enters one syllable at a time, realizes the
non-accentuated form first, assigns onset and optional coda anchors first,
then assigns the nucleus, performs same-consonant coda/onset look-ahead where
needed, computes the realized syllable duration, and resolves mismatch by the
ordered policy drift -> vowel -> drift-policy branch.

The only valid accentuated syllable models in this requirement are `C:V`,
`CVC:`, `CVV:`, and `CVV:C`. `CVVC:C` is not a valid model.

When a syllable is accentuated, the solver adds exactly
`0.5 * phonetize.timing_model.durations.cvc_reference` to the total syllable
duration and distributes that increment first to the accentuated segment and
then, if needed, to the adjacent segment according to the configured
accentuation-distribution policy and segment-class legality limits.

If the baseline syllable closes with a consonant and the following syllable
opens with the same consonant, the baseline pass must detect that geminate
boundary before the next syllable is solved and pre-assign the next onset's
baseline duration from the geminate logic rather than treating the pair as two
independent singleton anchors. If later accentuation creates an additional
coda extension on that same consonant chain, the solver must treat the result
as a double-gemination case and reduce the second onset first if the combined
same-consonant duration would exceed
`phonetize.timing_model.durations.segmental_ceiling`.

Phase 2 shall also maintain an internal ordered list of drift values observed
during traversal so the finalized phone artifacts can expose drift summary
statistics in frontmatter for downstream reporting.

This requirement narrows the Phase 2 runtime described by
[REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md) and
[REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
without changing the existing two-phase architecture or row contract.

---

# Motivation

The current phonetizer records already establish that Phase 2 must traverse
prebuilt rows, keep consonants as hard timing pillars by default, use running
drift before vowel recovery, and branch by drift policy when recovery fails.
What is still missing is one explicit requirement for the syllable-scoped
solver itself.

That missing contract matters because the timing algorithm is now specific
enough to require a stable interpretation of syllable categories, target foot
values, drift behavior, accentuation distribution, same-consonant geminate
handling, and pause discharge.
Without that detail, later CRs could all claim to satisfy the same broad
stability-first model while implementing materially different local solvers.

The drift history itself is also now part of the contract because metricalc
needs a stable way to report how much cumulative timing correction the
phonetizer used, without recomputing that history independently.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given Phase 2 duration realization is active, when the row stream is
      traversed, then the traversal partitions the stream into syllables and
      pauses only.
- [ ] Given the solver classifies a non-pause unit, when the unit is not
      accentuated, then its syllable class is one of exactly `CV`, `CVV`,
      `CVC`, or `CVVC`.
- [ ] Given the solver classifies a non-pause unit, when the unit is
      accentuated, then its syllable class is one of exactly `C:V`, `CVV:`,
      `CVC:`, or `CVV:C`.
- [ ] Given internal hiatus rows `˙` and vowel-transition rows `¨` are present
      in the Phase 1 row stream, when Phase 2 identifies syllable structure,
      then those rows are treated as consonantal structure and the solver does
      not expose separate active timing categories `V`, `VV`, `VC`, or `VVC`.
- [ ] Given the solver enters a syllable scope, when row roles are assigned,
      then the first consonantal row in the syllable is the onset, the vowel
      row or rows form the nucleus, and an optional following consonantal row
      inside the same syllable is the coda.
- [ ] Given a non-accentuated syllable is realized, when its nominal target is
      computed from `phonetize.timing_model.durations.cvc_reference`, then the
      nominal foot values are exactly:
      `CV = 0.5 * cvc_reference`,
      `CVV = 1.0 * cvc_reference`,
      `CVC = 1.0 * cvc_reference`, and
      `CVVC = 1.5 * cvc_reference`.
- [ ] Given a syllable is accentuated, when its total target is computed, then
  the target gains exactly
  `0.5 * phonetize.timing_model.durations.cvc_reference` beyond the
  corresponding non-accentuated syllable class.
- [ ] Given Phase 2 starts a stream, when runtime state is initialized, then a
      signed `drift_cursor` starts at `0`.
- [ ] Given Phase 2 starts a stream, when runtime state is initialized, then an
  internal ordered drift-history list is initialized for that stream.
- [ ] Given a syllable is realized, when nominal segment anchors are assigned,
      then the solver assigns duration to the onset first, assigns duration to
      the coda second if a coda exists, and assigns duration to the nucleus
      after the consonantal anchors are fixed.
- [ ] Given the solver enters a syllable, when duration realization starts,
      then it completes the syllable's non-accentuated baseline form before
      applying any accentuation increment to that syllable.
- [ ] Given a syllable has a class-specific nominal foot value `shape_ref`,
      when its target equation is evaluated, then the solver attempts to satisfy
      `realized_syllable_duration = shape_ref - drift_cursor`.
- [ ] Given the first-pass sum of assigned segment durations does not satisfy
      the syllable target equation, when correction order is applied, then the
      solver attempts correction in the exact order `drift`, then `vowel`, then
      `drift_policy` branch.
- [ ] Given the local syllable mismatch is evaluated, when running drift is
      updated, then the mismatch contributes to `drift_cursor` only up to the
      configured drift limit represented by
      `phonetize.process.drift_tolerance`.
- [ ] Given the solver updates or discharges `drift_cursor` during syllable or
  pause realization, when that step completes, then the current drift value
  is appended to the stream's internal drift-history list.
- [ ] Given a syllable is accentuated, when its extra half-foot is distributed,
  then the solver applies the configured
  `phonetize.process.accentuation_distribution_policy` to the accentuated
  segment first and uses the adjacent segment only for any legal remainder.
- [ ] Given `phonetize.process.accentuation_distribution_policy` is `100_0`,
  when the accentuated segment can absorb the entire accent increment
  without violating its maximum, then the whole added half-foot remains on
  the accentuated segment.
- [ ] Given `phonetize.process.accentuation_distribution_policy` is `100_0`,
  when the accentuated segment reaches its legal maximum before absorbing
  the whole accent increment, then the remaining duration is assigned to the
  adjacent segment chosen by syllable type as follows: `C:V -> V`,
  `CVV: -> C`, `CVC: -> V`, and `CVV:C -> C`.
- [ ] Given `phonetize.process.accentuation_distribution_policy` is `85_15`,
  when accentuation is realized, then the solver begins from an intended
  eighty-five/fifteen split between the accentuated segment and the
  adjacent segment, and then clamps or redistributes only as required by
  the legal maxima of those segment classes.
- [ ] Given `phonetize.process.accentuation_distribution_policy` is `70_30`,
  when accentuation is realized, then the solver begins from an intended
  seventy/thirty split between the accentuated segment and the adjacent
  segment, and then clamps or redistributes only as required by the legal
  maxima of those segment classes.
- [ ] Given accentuation is realized on a long vowel or consonant, when the
  increment is applied, then the accentuated segment is not extended beyond
  the configured legal maximum for its segment class, including long-vowel
  maxima and geminate maxima.
- [ ] Given accentuation distribution and ordinary legality checks are applied,
  when a non-zero `drift_cursor` enters the accentuated syllable, then the
  solver uses the accentuation increment as additional recovery space and
  attempts to bring the signed `drift_cursor` to `0`, or otherwise as close
  to `0` as the legal segment limits allow.
- [ ] Given the syllable is still mismatched after ordinary drift correction,
      when vowel recovery is attempted, then only the nucleus duration may be
      adjusted and only within the legal min/max range of the vowel's current
      category.
- [ ] Given `phonetize.process.drift_tolerance = 0` and
  `phonetize.process.drift_policy = extensible`, when correction order is
  applied, then the practical behavior becomes vowel-first followed by
  unlimited drift extension because ordinary bounded drift is unavailable.
- [ ] Given running drift and legal vowel recovery are exhausted, when
      `phonetize.process.drift_policy` is `strict`, then Phase 2 fails for that
      stream rather than silently violating the syllable target equation.
- [ ] Given running drift and legal vowel recovery are exhausted, when
      `phonetize.process.drift_policy` is `extensible`, then the unresolved
      mismatch is carried by extended drift and the runtime continues with that
      updated signed `drift_cursor`.
- [ ] Given a syllable-final coda and the next syllable onset are realized,
      when both consonants are the same consonant across the syllable boundary,
      then the pair is treated as a geminate-structured pair and its combined
      coda-plus-onset duration is governed by
      `phonetize.process.geminate_policy` and the configured geminate anchor.
- [ ] Given a syllable-final coda and the next syllable onset are realized,
  when both consonants are the same consonant across the syllable boundary,
  then the solver performs that same-consonant check during baseline
  realization of the current syllable and may pre-assign the next onset's
  baseline duration before the next syllable itself is solved.
- [ ] Given a syllable-final coda and the next syllable onset are realized,
      when the two consonants are not the same consonant, then the next onset
  uses its ordinary configured onset anchor rather than geminate timing,
  and the current syllable does not pre-assign a geminate-derived onset
  duration to it.
- [ ] Given a geminate-structured same-consonant pair was realized across a
      syllable boundary, when the next syllable is solved, then the next
      syllable re-enters the same target equation and correction order using
      the current signed `drift_cursor`.
- [ ] Given an accentuated syllable is solved after its non-accentuated
  baseline form, when accentuation targets a coda in a `CVC:` shape and
  the following syllable begins with the same consonant, then the solver
  treats the coda-plus-next-onset chain as a double-gemination case.
- [ ] Given a double-gemination case was created across a syllable boundary,
  when the combined duration of the current coda and the pre-assigned next
  onset would exceed
  `phonetize.timing_model.durations.segmental_ceiling`, then the solver
  reduces the second onset first until the total same-consonant duration is
  less than or equal to that ceiling.
- [ ] Given a pause is realized, when pause duration is assigned, then the
      solver uses the configured pause band plus the current signed
      `drift_cursor` as the discharge space.
- [ ] Given a short pause is realized, when pause-band constraints prevent full
      discharge of the current drift reserve, then the solver reduces the drift
      as much as legally possible inside the short-pause band and carries the
      remainder into the following phrase.
- [ ] Given a long pause is realized, when the current drift reserve is
      discharged, then the solver drives `drift_cursor` back to `0`.
- [ ] Given the stream approaches a pause through one or more accentuated
  syllables, when the local solver has legal room to absorb drift through
  those accentuated syllables, then the absolute value of `drift_cursor`
  should usually decrease before the pause rather than accumulate.
- [ ] Given Phase 2 finishes writing a finalized `_phone.txt` or `_ophone.txt`
  artifact, when frontmatter is serialized, then it includes
  `data.drift.max`, `data.drift.mean`, and `data.drift.stddev` computed
  from that stream's internal drift-history list.
- [ ] Given `data.drift` frontmatter is emitted, when the summary values are
  computed, then `max` is the maximum absolute drift observed in the stored
  drift-history list, `mean` is the arithmetic mean of the stored drift
  values, and `stddev` is the population standard deviation of the stored
  drift values.
- [ ] Given public diagnostics expose current drift state, when the state is
  rendered for users, then it is reported with performer-style labels:
  `Ahead (rushing)` for before the beat, `On the beat` for zero drift, and
  `Behind (dragging)` for after the beat.
- [ ] Given Phase 2 tests are written for this solver, when representative
      coverage is reviewed, then tests cover all eight active syllable
      categories, drift-positive and drift-negative cases, same-consonant
  geminate versus non-geminate boundaries, strict versus extensible drift
  policy, short-versus-long pause discharge, and frontmatter drift-summary
  emission from the stored drift-history list.

---

# User Story (optional)
> As the maintainer of the Phase 2 phonetizer runtime, I want the duration
> solver defined as a syllable-scoped drift-first algorithm so that later
> implementation work does not drift between incompatible local timing models.

---

# Interface Notes
- Traversal unit:
  - syllable or pause
- Active non-accentuated syllable classes:
  - `CV`
  - `CVV`
  - `CVC`
  - `CVVC`
- Active accentuated syllable classes:
  - `C:V`
  - `CVC:`
  - `CVV:`
  - `CVV:C`
- Suppressed standalone timing classes in Phase 2 classification:
  - `V`
  - `VV`
  - `VC`
  - `VVC`
- Segment-role order inside a syllable:
  - onset
  - nucleus
  - optional coda
- Assignment order inside a syllable:
  - onset duration
  - coda duration when present
  - nucleus duration
- Boundary look-ahead rule:
  - after baseline coda assignment, inspect the next onset before closing the
    current syllable
  - if the next onset is the same consonant, pre-assign that onset through the
    geminate rule
  - if the next onset is not the same consonant, leave it for its own ordinary
    onset assignment when the next syllable is solved
- Nominal foot mapping from `cvc_reference`:
  - `CV -> 0.5 * cvc_reference`
  - `CVV -> 1.0 * cvc_reference`
  - `CVC -> 1.0 * cvc_reference`
  - `CVVC -> 1.5 * cvc_reference`
- Accentuation increment:
  - every accentuated syllable gains `0.5 * cvc_reference`
- Accentuation-distribution goal:
  - use the accent increment to drive `drift_cursor` toward `0` whenever legal
    segment limits allow
- Accentuation-distribution adjacency:
  - `C:V -> V`
  - `CVV: -> C`
  - `CVC: -> V`
  - `CVV:C -> C`
- Accentuation-distribution limits:
  - long-vowel extension stops at the configured long-vowel maximum
  - consonant extension stops at the configured geminate maximum for the
    relevant consonant class
- Runtime state:
  - signed `drift_cursor`, initialized to `0`
  - ordered drift-history list for the current stream
- Correction order:
  - `drift -> vowel -> drift_policy`
- Special correction order:
  - if `drift_tolerance = 0` and `drift_policy = extensible`, the practical
    order becomes `vowel -> extensible drift`
- Geminate rule:
  - only same-consonant coda/onset pairs count as geminate-structured pairs
  - that same-consonant check happens during baseline realization of the first
    syllable in the pair
  - the next onset may therefore be pre-assigned before its own syllable is
    traversed
  - if later accentuation yields a `CVC:`-style extra coda extension on the
    same chain, the result is treated as double gemination
  - double-gemination correction reduces the second onset first if the total
    same-consonant duration would exceed `segmental_ceiling`
- Pause rule:
  - short pauses minimize residual drift inside their legal band
  - long pauses reset the drift reserve to `0`
- Frontmatter drift summary:
  - `data.drift.max`
  - `data.drift.mean`
  - `data.drift.stddev`
  - each finalized `_phone.txt` and `_ophone.txt` artifact carries the summary
    computed from that stream's internal drift-history list
- Public drift wording:
  - `Ahead (rushing)` means the performer is before the beat
  - `On the beat` means zero drift
  - `Behind (dragging)` means the performer is after the beat
- Affected components:
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/cli/phonetizer.py`
  - phonetize timing config under `phonetize.process` and
    `phonetize.timing_model.durations`

Illustrative solver sketch:

```text
for unit in stream:
    if unit is pause:
        realize pause within pause band using drift_cursor
    append drift_cursor to drift_history
        continue

    classify unit as one of CV, CVV, CVC, CVVC, C:V, CVV:, CVC:, CVV:C
  realize the non-accentuated baseline form first
    assign onset anchor
    assign coda anchor if present
    assign nucleus anchor
  if coda exists and next onset is the same consonant:
    pre-assign next onset through geminate handling
    if unit is accentuated:
      add 0.5 * cvc_reference
      distribute toward the accentuated segment first
      send legal remainder to the adjacent segment for that syllable class
      use that extra space to reduce drift_cursor toward 0
    if accentuation created a same-consonant double-gemination chain:
      reduce the second onset first until chain_duration <= segmental_ceiling
    target = shape_ref(unit) - drift_cursor
    if realized_duration != target:
        apply drift correction first
    if realized_duration != target:
        adjust nucleus within legal vowel range
    if realized_duration != target:
        branch by drift_policy
    append drift_cursor to drift_history

frontmatter.data.drift = {
    'max': max_abs(drift_history),
    'mean': mean(drift_history),
    'stddev': population_stddev(drift_history),
}
```

---

# Open Questions
- [ ] None for now.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium to large
- Migration:
  - keep [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md)
    as the umbrella architecture record
  - keep [REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md)
    as the higher-level timing-control boundary
  - use this requirement as the detailed local-solver contract for CR-040 and
    follow-up implementation records

# Related
- Related ADRs: [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md), [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md), [ADR-039](../adr/039-replacement-of-timing-model.md)
- Parent REQs: [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md), [REQ-026](026-stability-first-phonetizer-timing-control-and-baseline-validation.md), [REQ-027](027-phonetize-config-semantic-invariants-for-shared-verification.md)
- Implementation CRs: [CR-040](../cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)

# Non-Goals
- This requirement does not redefine the Phase 1 phone-row schema.
- This requirement does not reopen `_tilde` parsing during Phase 2.
- This requirement does not replace the existing config-policy surface defined
  by the current phonetize records.
- This requirement does not define metrics formulas or metrics-side interval
  aggregation.

# Security / Safety Considerations
- Restricting Phase 2 to syllables and pauses reduces the risk of silent local
  reparsing with inconsistent structural assumptions.
- Requiring drift-first recovery before vowel adjustment reduces the risk of
  arbitrary vowel manipulation that changes category semantics.
- Making long-pause discharge reset drift to `0` reduces the risk of hidden
  cross-phrase timing debt accumulating without trace.