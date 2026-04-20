---
cr_id: CR-082
status: Done
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-20
implements: 'REQ-042'
---

# Change Request: Add Corrective Geminate Coda Share Ratio

# Summary

Add a new class-local phonetizer timing key
`phonetize.process.timing_model.durations.consonants.<class>.geminate_coda_ratio`
with default `0.60` for `closure`, `fricative`, and `sonorant`, and use it to
rebalance same-consonant coda/onset pairs when
`geminate_policy = corrective`.

Repository inspection on 2026-04-19 shows that
`src/akkapros/lib/phonetize.py::_same_consonant_next_onset()` currently keeps
the already assigned coda duration and gives the onset the remainder of the
corrective pair total. This CR replaces that fixed-coda-anchor remainder split
with an explicit configurable coda share while preserving the existing total
pair target, policy names, and class-local geminate ceilings.

This CR narrows the same-consonant corrective behavior described historically in
[CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md) and
the class-local default row surface most recently retuned by
[CR-068](068-ratio-based-parameters.md). Older records remain historical, but
this CR becomes the active contract for how corrective geminate totals are
divided internally.

---

# Motivation

The repository already exposes class-local onset, coda, geminate, and
gemination ceiling values, but the corrective same-consonant split still hides
one hardcoded assumption: the coda side stays at its ordinary anchor and the
onset absorbs the difference to the corrective target. That means maintainers
can tune the total geminate target but cannot tune how that total is shared.

The requested change is small and localized. It does not redesign the phase-2
solver or introduce a new policy mode. It simply makes the corrective split
configurable in the same timing table where the rest of the class-local
consonant behavior already lives.

---

# Scope

## Included

- Add `geminate_coda_ratio` to each consonant class under
  `phonetize.process.timing_model.durations.consonants.*`.
- Set the default value to `0.60` for `closure`, `fricative`, and `sonorant`.
- Validate the new value as numeric and strictly inside `0 < value < 1`.
- Update corrective same-consonant pair handling so the coda side and onset
  side are both recomputed from the chosen corrective pair total.
- Preserve the existing corrective pair total selection rule:
  `min(configured_geminate_target, class_gemination_max)`.
- Preserve existing `cumulative` policy behavior.
- Preserve existing non-identical coda/onset behavior.
- Update default YAML, config help, confwriter surfaces, demo configs,
  phonetizer documentation, and tests.

## Not Included

- Adding a new geminate policy name.
- Retuning the geminate targets or ceilings themselves.
- Changing pause logic, vowel logic, or drift behavior.
- Changing same-consonant detection rules.

---

# Current Behavior

Observed current behavior on 2026-04-19:

- `_same_consonant_next_onset()` exits early unless both syllables expose a
  coda/onset consonant and the two symbols are identical.
- the current syllable has already assigned the coda side through
  `_consonant_anchor(..., 'C')`
- the next syllable exposes an onset anchor through
  `_consonant_anchor(..., 'O')`
- under `geminate_policy = corrective`, the pair total becomes
  `min(_consonant_geminate_target(...), _consonant_maximum(...))`
- the onset is then assigned `pair_total - coda_duration`
- under `geminate_policy = cumulative`, the pair total becomes
  `min(coda_duration + onset_anchor, ceiling)` and only the onset side changes

This means the current runtime has a configurable total geminate target but no
configurable internal coda/onset proportion in corrective mode.

---

# Proposed Change

Adopt the following active contract.

## 1. Add a class-local ratio key

Each consonant class row gains a new key immediately after `geminate`:

- `consonants.closure.geminate_coda_ratio: 0.60`
- `consonants.fricative.geminate_coda_ratio: 0.60`
- `consonants.sonorant.geminate_coda_ratio: 0.60`

## 2. Rebalance corrective same-consonant pairs from the selected total

When all of the following are true:

- the current syllable has a coda consonant
- the next syllable has an onset consonant
- the two consonants are the same symbol
- `geminate_policy = corrective`

then the solver shall:

- compute the corrective pair total exactly as it does now
- read the class-local `geminate_coda_ratio`
- assign the coda side to `pair_total * geminate_coda_ratio`
- assign the onset side to `pair_total - coda_side`

The corrective pair total remains the active target. The change is only in how
that total is divided internally.

## 3. Preserve existing behavior outside that narrow case

- `cumulative` policy continues to preserve cumulative same-consonant timing
  rather than using the new ratio.
- non-identical coda/onset pairs continue to bypass the same-consonant geminate
  path entirely.
- class-local ceilings still cap the total corrective pair duration.

## 4. Surface the key everywhere the timing table is surfaced

The new key must appear consistently in:

- `src/akkapros/config/default.yaml`
- schema/default emission in `src/akkapros/lib/phonetize.py`
- config-path help and confwriter surfaces
- repository demo YAML files
- phonetizer configuration docs
- tests that pin default and override behavior

---

# Technical Design

Concrete implementation shape:

- extend the class-local consonant schema blocks in
  `src/akkapros/lib/phonetize.py` to include `geminate_coda_ratio`
- update shared verification in `verify_phonetize_config()` so each class-local
  ratio is checked for `0 < value < 1`
- in `_same_consonant_next_onset()`, keep the existing total-selection logic,
  but under `corrective` recompute both sides from the configured ratio instead
  of preserving the previously assigned coda anchor
- leave the `cumulative` branch unchanged
- refresh docs, config support tests, unit tests, and integration tests that
  pin same-consonant corrective output

Recommended verification focus:

- one default-surface test that proves the new keys exist in emitted config
- one verification test that rejects `0`, `1`, and non-numeric values
- one corrective same-consonant test that proves the coda/onset split follows
  the configured ratio
- one cumulative same-consonant test that proves the ratio is ignored there

---

# Files Likely Affected

src/akkapros/lib/phonetize.py  
src/akkapros/config/default.yaml  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/confwriter.py  
tests/test_phonetize_lib.py  
tests/test_config_support.py  
tests/test_integration.py  
docs/akkapros/configuration.md  
docs/akkapros/phonetizer.md  
demo/akkapros/lexlinks/construct-demo.yaml  
demo/akkapros/prosmaker/corpus-demo.yaml  

---

# Acceptance Criteria

- [x] Each consonant class row exposes `geminate_coda_ratio` with default
      `0.60`.
- [x] Shared verification rejects values outside `0 < value < 1`.
- [x] Corrective same-consonant pairs rebalance both coda and onset from the
      selected corrective pair total according to the configured ratio.
- [x] Cumulative same-consonant pairs continue to follow cumulative policy and
      do not use the new ratio.
- [x] Default/help/demo/doc surfaces show the new key consistently.
- [x] Focused unit and config-surface tests pin the new contract.

---

# Risks / Edge Cases

- A ratio too near `0` or `1` could collapse one side of the pair; explicit
  exclusive-bound validation is required.
- Tests that previously assumed the coda stays at its ordinary anchor in
  corrective mode will become stale and must be updated intentionally.
- Because the key is class-local, emitted YAML and help text must show it for
  all three classes or the contract will look inconsistent.

---

# Testing Strategy

Unit tests:

- default config includes `geminate_coda_ratio` in each consonant class
- verification rejects invalid ratio values
- corrective same-consonant pair uses configured coda share
- cumulative same-consonant pair ignores the ratio

Integration tests:

- config-path override can set a class-local ratio and affect emitted phone rows

Manual checks:

- inspect emitted default YAML and help subtree for the new key under all three
  consonant classes

---

# Rollback Plan

Revert the new key and restore the previous corrective fixed-coda-anchor split.

---

# Related Issues

- [REQ-042](../req/042-corrective-geminate-coda-share-ratio.md)
- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [CR-068](068-ratio-based-parameters.md)

---

# Tasks

## Implementation

- [x] Add `geminate_coda_ratio` to the class-local timing rows
- [x] Validate `0 < value < 1`
- [x] Rebalance corrective same-consonant pairs from the selected total

## Tests

- [x] Update default/config/help surface tests
- [x] Add corrective and cumulative same-consonant coverage
- [x] Keep verification fixtures self-sufficient under `tests/`

## Documentation

- [x] Update phonetizer/config docs and demo YAML examples

## Review

- [x] Verify the new ratio only affects corrective same-consonant pairs

## Implementation Notes

- 2026-04-20: Added class-local `geminate_coda_ratio` defaults for `closure`,
  `fricative`, and `sonorant` across schema, emitted defaults, and demo YAML.
- 2026-04-20: Shared phonetize verification now rejects non-numeric values and
  endpoint values outside the exclusive interval `0 < value < 1`.
- 2026-04-20: Corrective same-consonant timing now recomputes both coda and
  onset from the selected pair total, while cumulative behavior remains
  unchanged.
