---
req_id: REQ-042
status: Draft
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
related_adrs: 'ADR-046'
implemented_by: 'CR-082'
---

# Requirement: Corrective Geminate Coda Share Ratio

# Summary

The phonetizer shall add a class-local timing parameter
`phonetize.process.timing_model.durations.consonants.<class>.geminate_coda_ratio`
for `closure`, `fricative`, and `sonorant`, with default value `0.60`.

This parameter applies only when a same-consonant coda/onset pair is realized
under `geminate_policy = corrective`. In that case the corrective geminate pair
shall preserve the configured total geminate target while dividing that total
between coda and onset by the configured coda share instead of leaving the
entire preassigned coda anchor in place and giving the onset the remainder.

Historical note:

- This requirement narrows the same-consonant corrective behavior described in
  [REQ-031](031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
  without changing the meaning of `geminate_policy` itself.
- It extends the class-local timing row surface currently maintained under
  [REQ-027](027-phonetize-config-semantic-invariants-for-shared-verification.md)
  and the ratio-based default table approved by
  [CR-068](../cr/068-ratio-based-parameters.md).

---

# Motivation

Repository inspection on 2026-04-19 shows that `_same_consonant_next_onset()`
currently preassigns the coda side to the ordinary coda anchor, selects a
corrective pair total from the configured geminate target, and then assigns the
onset side to `pair_total - coda_duration`. That preserves the pair total, but
it does not preserve any configurable coda/onset proportion inside the
corrective geminate.

The requested change is not a new geminate policy. `cumulative` and
`corrective` remain the only policy modes. The new behavior is a refinement of
the existing corrective mode so the pair-internal split becomes explicit,
configurable, and consistent across consonant classes.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the approved grouped config surface is materialized, when the
      consonant timing rows are inspected, then each of
      `closure`, `fricative`, and `sonorant` includes
      `geminate_coda_ratio: 0.60` between `geminate` and the class-specific
      nested blocks.
- [ ] Given phonetize semantic verification is executed, when a
      `geminate_coda_ratio` value is provided, then the value is accepted only
      when it is numeric and strictly inside `0 < geminate_coda_ratio < 1`.
- [ ] Given a same-consonant coda/onset pair is realized with
      `geminate_policy = corrective`, when the pair total is set from the
      configured corrective geminate target and class ceiling, then the coda
      side receives `pair_total * geminate_coda_ratio` and the onset side
      receives the exact remainder before final row serialization.
- [ ] Given a same-consonant coda/onset pair is realized with
      `geminate_policy = cumulative`, when the pair is solved, then
      `geminate_coda_ratio` does not alter the cumulative-policy behavior.
- [ ] Given the adjacent consonants are not the same consonant, when the
      syllable pair is solved, then `geminate_coda_ratio` has no effect.
- [ ] Given class-local defaults are emitted through config tooling, when the
      default YAML, help inventory, and demo configs are inspected, then the
      new ratio key is present with default `0.60` for each consonant class.
- [ ] Given unit and integration coverage is refreshed, when same-consonant
      corrective pairs are tested, then the tests assert the new ratio-driven
      coda/onset split rather than the old fixed-coda-anchor remainder split.

---

# User Story (optional)
> As a maintainer tuning the phonetizer, I want corrective geminate pairs to
> expose an explicit coda/onset share so the internal split can be adjusted
> without inventing a new policy mode.

---

# Interface Notes
- New config paths:
  - `phonetize.process.timing_model.durations.consonants.closure.geminate_coda_ratio`
  - `phonetize.process.timing_model.durations.consonants.fricative.geminate_coda_ratio`
  - `phonetize.process.timing_model.durations.consonants.sonorant.geminate_coda_ratio`
- Default value:
  - `0.60`
- Active behavior scope:
  - same-consonant coda/onset pairs only
  - corrective policy only
  - class-local ratio, class-local geminate target, and class-local ceiling
- Affected components:
  - phonetizer timing-model defaults and verification
  - same-consonant pair realization in `src/akkapros/lib/phonetize.py`
  - config help, confwriter/default YAML emission, demo YAMLs, and phonetizer
    documentation
  - unit and integration tests that pin corrective geminate behavior

---

# Open Questions
- [ ] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - add the new key to each consonant class row with default `0.60`
  - validate `0 < value < 1`
  - in corrective same-consonant handling, rebalance both sides of the pair
    from the configured total instead of leaving the coda anchor untouched
  - update default/help/demo/docs/test surfaces together so the new ratio is a
    first-class config path rather than an implicit runtime constant

# Related
- Related ADRs: [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- Implementation CRs: [CR-082](../cr/082-add-corrective-geminate-coda-share-ratio.md)

# Non-Goals
- This requirement does not add a third geminate policy beyond `corrective` and
  `cumulative`.
- This requirement does not change non-identical coda/onset pairs.
- This requirement does not retune the geminate target or gemination ceiling
  defaults themselves.

# Security / Safety Considerations
- The new ratio must be validated explicitly because values at or outside the
  closed interval endpoints would collapse the pair into a single-sided timing
  allocation and produce misleading corrective behavior.