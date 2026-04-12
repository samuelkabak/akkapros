---
cr_id: CR-056
status: Done
priority: High
impact: Additive
created: 2026-04-12
updated: 2026-04-12
implements: 'REQ-012, REQ-015, REQ-018, REQ-030'
---

# Change Request: Broaden Metrics Coverage to High-Confidence Indicator Verification

## Summary

Broaden CR-056 from a narrow word-count regression into a metrics-coverage CR
for the full public indicator surface. The goal is not perfect coverage by raw
percentage. The goal is high confidence that every user-visible metrics family
has at least one exact-value verification path and that the most important
indicators are protected by more than one layer of tests.

An earlier draft of CR-056 was interpreted as a word-count-only fix. That
partial response is not sufficient. A missing unit test for an obvious surface
indicator such as `Total words` is evidence that more important metrics may
also be under-verified. This CR therefore widens scope from one indicator to a
coverage program for structural, prominence, speech, pause, drift, and acoustic
metrics across unit, self-test, and integration layers.

---

## Motivation

The current metrics suite is not empty. It already contains useful coverage for
small-corpus consistency, selected punctuation behavior, path safety, CLI
failure cases, and one manually derived single-line interval verification.
However, the current suite still leaves a confidence gap between the published
metrics contract and the tests that defend it.

Current evidence gathered from the repository shows:

- `tests/test_metrics_stats.py` exercises structure, selected formulas, one
  manual interval example, and a narrow corpus-level word-count regression.
- `tests/test_selftests_lib.py` runs the built-in metrics self-tests, but those
  mostly verify internal helpers and representative consistency checks rather
  than broad public-surface exact values.
- `tests/test_integration.py` pins full-pipeline behavior, but for metrics it
  currently locks only a small subset of high-level values such as accentuated
  `VarcoC` and accentuation rate, while many other public metrics are checked
  only for presence, safe formatting, or general coherence.

That means many public indicators are either:

- checked only for existence in table/JSON output
- checked only through formulas that reuse values already produced by the same
  implementation under test
- checked only on one synthetic or single-line example rather than on a real
  corpus or full pipeline fixture

This is not the standard needed for a research-facing metrics stage.

---

## Scope

### Included

- analyze existing metrics-related tests and document the current confidence
  level by indicator family
- define a coverage matrix for the active public metrics surface
- require exact-value verification for all major public indicator families,
  using manual or independently derived references where feasible
- require both unit/regression and integration coverage where the indicator is
  user-facing and central to the research claims
- require test additions for table/text surfaces, JSON surfaces, and library
  helper behavior where those surfaces are part of the active contract
- preserve the existing narrow word-count work as one part of the broader plan,
  not as the whole response

### Not Included

- redesigning the metrics formulas themselves
- changing the phone/ophone metrics model legalized by REQ-030
- mandating literal 100% line or branch coverage as a release gate
- rewriting unrelated non-metrics test suites

---

## Current Behavior

### Existing Strengths

Current tests provide meaningful coverage for:

- word-pattern matching, tokenization, preprocessing, segment extraction, and
  interval helper behavior through metrics self-tests
- representative formula consistency for syllable, mora, and prominence counts
- one manual low-level interval verification in `test_compute_interval_metrics_uses_manual_phone_intervals()`
- one manual end-to-end single-line verification for the active interval metric
  set in `test_single_line_metrics_match_manual_varco_verification_reference()`
- selected punctuation, diphthong, prominence, and missing-input failure cases
- path-disclosure constraints for metrics artifacts
- full-pipeline smoke/reference coverage with pinned `VarcoC` and accentuation
  rate on integration fixtures

### Existing Gaps

The current suite does not yet provide high confidence across the whole public
indicator inventory.

Observed gaps:

- many public acoustic indicators are not locked to exact expected values on a
  real corpus fixture: `%C`, `%V`, `meanC`, `meanV`, `ΔC`, `ΔV`, `VarcoV`,
  `rPVI-C`, and `nPVI-V`
- drift reporting is manually pinned for one single-line sample, but not for a
  broader corpus-level regression alongside the rest of the metrics output
- speech-rate outputs (`WPM`, `Pause ratio`, `SPS`, articulation rate,
  syllable duration, mora duration, word duration) are mostly verified through
  internal formulas, not through independently derived expected values on a
  fixed reference sample
- structural output families such as total syllables, syllable-type counts,
  syllable percentages, word statistics, and mora statistics are not broadly
  locked to exact reference values for a real corpus fixture in both text and
  JSON surfaces
- prominence statistics were under-verified until the narrow word-count fix and
  still lack broader matrix-style coverage against the full metrics inventory
- integration tests do not currently compare complete sanitized metrics text or
  JSON artifacts to approved references, unlike several other pipeline outputs
- the current tests do not expose an explicit coverage matrix showing which
  public indicators are defended by unit, self-test, regression, and
  integration layers

In short: the suite is useful, but it is still narrower than the public
research-facing contract.

---

## Proposed Change

- rewrite CR-056 as the umbrella CR for broad metrics-confidence coverage
- create a coverage matrix that maps every active public metrics family to the
  test layers that defend it
- expand the test plan so every public metrics family has at least one exact-
  value assertion path and the most important research indicators have at least
  two layers of defense
- require manual or independently derived references for the highest-risk and
  highest-value public indicators rather than relying only on consistency checks
- require that integration tests pin a materially broader slice of the metrics
  artifacts than the current `VarcoC`/accentuation-rate subset

---

## Technical Design

### Coverage Model

The implementation work for this CR shall organize metrics verification into
four complementary layers.

Layer 1: helper/self-test coverage

- low-level parsing and normalization helpers
- interval grouping and punctuation classification helpers
- fallback and zero-case handling helpers

Layer 2: unit/regression coverage with fixed expectations

- small synthetic fixtures where the expected numbers can be computed exactly
- manual or independent references for representative interval computations
- exact text/JSON assertions for structural and prominence surfaces

Layer 3: manually verified reference samples

- at least one fixed single-line sample for the active interval metric family
- at least one fixed corpus-level sample for structural and prominence metrics
- reference arithmetic or independent counting method documented outside
  `src/akkapros/lib/metrics.py`

Layer 4: full integration coverage

- metricalc CLI and fullprosmaker pipeline assertions over checked-in fixtures
- sanitized metrics text/JSON comparisons or equivalent exact-field assertions
- failure-path integration checks for input-contract errors

### Required Coverage Matrix

The coverage analysis and implementation shall treat the following families as
the active public metrics inventory.

Structural metrics:

- total syllables
- syllable-type counts and percentages
- total morae
- mean morae per syllable
- mean morae per word
- total words
- syllables per word
- merge statistics
- accentuation statistics

Prominence metrics:

- function words
- explicitly linked words
- prominence candidates

Speech and timing metrics:

- WPM
- pause ratio
- SPS (speech)
- SPS (articulation)
- average syllable duration
- mora duration
- word duration

Pause metrics:

- punctuation counts
- short/long punctuation counts
- per-syllable pause ratios
- pause duration and contribution outputs where public

Drift metrics:

- drift max
- drift mean
- drift stddev

Acoustic interval metrics:

- `%C`
- `%V`
- `meanC`
- `meanV`
- `ΔC`
- `ΔV`
- `VarcoC`
- `VarcoV`
- `rPVI-C`
- `nPVI-V`

### Coverage Expectations by Family

Minimum required confidence standard:

- every public family above must have at least one exact-value test path
- every research-critical interval metric must have both:
  - a manual or independent reference-based verification path
  - a full integration verification path on a real pipeline fixture
- every table/text surface that is part of the public report must have at least
  one assertion that checks exact rendered values, not only label presence
- every JSON surface that is part of the public contract must have at least one
  assertion that checks exact field values on a fixed fixture

### Candidate Test Additions Required by This CR

Unit/regression additions likely needed:

- exact-value tests for `analyze_text()` outputs on representative fixed inputs
- exact-value tests for `compute_speech_rate()` and `compute_pause_durations()`
  on hand-checkable fixtures
- broadened manual reference tests beyond the current single-line interval case
  so that structural, prominence, and speech families are also pinned
- explicit zero-case tests for empty/minimal interval lists across all public
  acoustic metrics

Integration additions likely needed:

- broader metrics text assertions on the gold full-pipeline fixture
- broader metrics JSON exact-field assertions on the same fixture
- either sanitized full-artifact metric references or an explicit field matrix
  covering the active public surface
- mono-mode metrics assertions beyond current presence and path checks

---

## Files Likely Affected

- `tests/test_metrics_stats.py`
- `tests/test_integration.py`
- `tests/test_selftests_lib.py`
- possibly `tests/test_selftests_cli.py`
- `src/akkapros/lib/metrics.py` built-in self-tests
- `docs/akkapros/` verification notes for manually audited references

---

## Acceptance Criteria

- [x] CR-056 documents a coverage analysis of the existing metrics tests,
      including strengths and identified gaps by indicator family.
- [x] A coverage matrix is defined for the active public metrics surface under
      REQ-012, REQ-015, REQ-018, and REQ-030.
- [x] Given the active public structural metrics, when the work is complete,
      then each structural family has at least one exact-value assertion path.
- [x] Given the active public prominence metrics, when the work is complete,
      then table/text and JSON surfaces are both asserted with exact values on a
      fixed fixture.
- [x] Given the active public speech/timing metrics, when the work is complete,
      then they are not only formula-checked internally but also pinned to
      exact expected values on at least one fixed reference sample.
- [x] Given the active public pause metrics, when the work is complete, then
      both helper behavior and surfaced public values are covered by exact-value
      regression tests.
- [x] Given the active public drift metrics, when the work is complete, then
      both original and accentuated drift summaries are asserted from fixed
      frontmatter-bearing fixtures on at least one representative sample.
- [x] Given the active public acoustic interval metrics, when the work is
      complete, then `%C`, `%V`, `meanC`, `meanV`, `ΔC`, `ΔV`, `VarcoC`,
      `VarcoV`, `rPVI-C`, and `nPVI-V` are all defended by manual or
      independently derived exact-value tests.
- [x] Given full integration coverage, when the work is complete, then metrics
      text and JSON outputs are pinned more broadly than the current
      `VarcoC`/accentuation-rate-only assertions.
- [x] Given built-in self-tests, when the work is complete, then their scope is
      reviewed and expanded where needed so helper-level metrics behavior is not
      weaker than the pytest regression layer.
- [x] Given documentation of manual verification notes, when the work is
      complete, then reference values used by the highest-risk tests are
      explainable outside the production implementation.

---

## Risks / Edge Cases

- Attempting to lock every metric on every corpus fixture may create brittle
  tests. The implementation should prefer a deliberate coverage matrix rather
  than indiscriminate snapshotting.
- Some speech and pause values depend on runtime parameters and sanitized path
  handling; fixtures and assertions must separate stable numeric expectations
  from environment-dependent fields.
- Golden metrics artifacts can drift legitimately when the approved metrics
  contract changes. The coverage design must therefore prefer documented fixed
  fields and sanitized references over opaque whole-file snapshots when that
  yields better auditability.

---

## Testing Strategy

Specifically require:

- unit tests for helper and formula boundaries
- regression tests with manually or independently derived expected values
- broadened library self-tests for metrics helper chunks
- integration tests over real pipeline fixtures with materially wider metrics
  assertions than exist today
- explicit review of which public indicators are still covered only by
  existence/presence checks after the work is done

Success condition:

- not “100% coverage”
- but “no major public indicator family remains defended only by label presence
  or internal consistency checks”

---

## Rollback Plan

- If the widened metrics-coverage program proves too large for one delivery,
  split the implementation into follow-up CRs by indicator family while keeping
  this CR as the umbrella contract and coverage target.

---

## Related

- REQ-012: Metrics Output Structure and Layout
- REQ-015: Frontmatter-Derived Word Indicators in Metrics
- REQ-018: Minimize Path Disclosure in Metrics Artifacts
- REQ-030: Phone/Ophone-Only Metrics and Interval Rhythm Computation
- CR-046: Redesign metricalc Around Phone/Ophone Interval Metrics
- CR-054: Add Single-Line Manual Metrics Verification Test
- CR-055: Add config-backed lexlinks construct demo

---

## Tasks

## Analysis

- [x] Produce the metrics coverage matrix by public indicator family
- [x] Identify which current tests are exact-value, consistency-only,
      presence-only, and integration-only

## Unit / Regression

- [x] Add exact-value tests for currently under-verified structural metrics
- [x] Add exact-value tests for currently under-verified speech and pause
      metrics
- [x] Add exact-value tests for all public acoustic interval metrics on fixed
      reference samples

## Integration

- [x] Broaden metricalc integration assertions on the full-pipeline fixture
- [x] Broaden mono-mode metrics integration assertions
- [x] Add or update sanitized metrics references where needed

## Documentation

- [x] Add or update manual verification notes for the highest-risk metrics
      references used by the test suite

## Review

- [x] Re-run internal indexes after the CR text is finalized
- [x] Verify that no major public metrics family remains under-tested by the
      coverage matrix

---

## Implementation Blockers

None currently. The problem is not lack of permission to proceed; it is that
the active CR text was previously scoped too narrowly. This rewrite broadens the
contract so implementation can proceed safely against the actual user request.

---

## Notes

This CR intentionally changes the scope of CR-056 from a narrow word-count fix
to a broad metrics-confidence program. The earlier word-count regression is
still useful, but it is now treated as one completed slice of a larger testing
obligation rather than as the full resolution.
