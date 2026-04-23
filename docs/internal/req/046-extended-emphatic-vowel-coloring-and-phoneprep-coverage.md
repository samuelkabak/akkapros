---
req_id: REQ-046
status: Implemented
priority: High
impact: Mutative
created: 2026-04-22
updated: 2026-04-22
related_adrs: 'ADR-040, ADR-012, ADR-011'
implemented_by: 'CR-088'
---

# Requirement: Extended Emphatic Vowel Coloring and Phoneprep Coverage

## Summary

The system shall extend emphatic vowel coloring beyond the current emphatic-
onset-only rule. In addition to preserving onset-based coloring, the phonetizer
shall optionally color a syllable nucleus from an emphatic coda in the same
syllable, and shall optionally carry that coloring to the immediately following
syllable when no punctuation-owned pause intervenes.

The same functional change shall be reflected in `phoneprep` so the recording-
inventory legality model and reachable diphone inventory cover the newly legal
colored-vowel contexts. The feature shall be enabled by default through a new
phonetizer realization parameter.

## Motivation

The current phonetizer undergenerates emphatic-colored vowels because it only
colors nuclei after emphatic onsets. That misses coda-driven contexts required
by the requested phonological model and creates divergence between runtime
phonetizer behavior, printer outputs, and `phoneprep` coverage generation.

Because this is a user-visible behavioral change, it needs a dedicated
requirement record so downstream implementation, tests, and documentation can be
evaluated against one explicit contract.

## Acceptance Criteria

- [x] Given the phonetizer processes a syllable whose onset contains `q`, `ṣ`,
      or `ṭ`, when the nucleus is realized, then the vowel is colored using the
      existing emphatic realization family (`AO`, `EO`, `IO`, `UO`).
- [x] Given the phonetizer processes a syllable whose coda contains `q`, `ṣ`,
      or `ṭ`, when the same syllable onset does not contain `t`, `s`, or `k`,
      then the nucleus of that syllable is colored.
- [x] Given the phonetizer processes a syllable whose coda contains `q`, `ṣ`,
      or `ṭ`, when the same syllable onset contains `t`, `s`, or `k`, then the
      same-syllable coda-driven coloring is blocked and the nucleus remains
      plain unless another independent coloring rule applies.
- [x] Given an emphatic coda is followed by another syllable in the same
      continuity span, when no punctuation-owned short or long pause intervenes
      and the following onset does not contain `t`, `s`, or `k`, then the
      immediately following syllable nucleus is also colored.
- [x] Given an emphatic coda is followed by another syllable in the same
      continuity span, when the following onset contains `t`, `s`, or `k`, then
      the carry to that following nucleus is blocked.
- [x] Given the new feature is configured off, when phonetizer runtime runs,
      then the legacy onset-only coloring behavior is preserved.
- [x] Given phonetizer configuration is rendered or loaded, when defaults are
  applied, then `phonetize.process.realization.limit_emphatic_coloring`
  exists as a boolean key with default `false`.
- [x] Given `confwriter` renders, lists, or verifies phonetize configuration,
  when the new feature is present, then the new realization key is included
  in the same help, default, and verification surfaces as the other live
  phonetizer config keys.
- [x] Given printer IPA and XAR outputs are produced from phonetizer results,
      when coda-driven coloring applies, then those outputs reflect the colored
      vowel realizations without requiring a separate printer-side coloring
      algorithm.
- [x] Given integration coverage is run, when the feature is enabled and
  disabled in controlled test-owned configs, then IPA and XAR outputs are
  both verified against immutable expected outputs stored under `tests/`.
- [x] Given `phoneprep` computes legal inventories and reachable diphone
      coverage, when extended emphatic coloring is part of the active model,
      then plain-to-colored and colored-to-emphatic contexts introduced by the
      new rule become reachable where legal.
- [x] Given `phoneprep` generates its recording inventory, when testing plain
      predecessors of emphatic-colored vowels, then plain `t`, `d`, and `k` are
      excluded from that predecessor set.
- [x] Given automated tests are added for this feature, when fixtures or
  configuration files are needed, then they are created under `tests/` and
  do not depend on `demo/`, `outputs/`, `tmp/`, or any other mutable
  repository data.
- [x] Given the repository contains YAML files that serialize active phonetize
  configuration defaults or examples, when this requirement is implemented,
  then every such YAML config surface carries the new realization key.

## User Story

> As the maintainer of the phonetizer and phoneprep model, I want emphatic
> vowel coloring to include coda-driven and immediate post-coda contexts so the
> generated phone rows, printer outputs, and diphone coverage inventory match
> the intended phonological behavior.

## Interface Notes

- Input:
  - phonetizer row streams derived from `_tilde.txt`
  - `phoneprep` internal legality and reachable-inventory generation surfaces
- Output:
  - updated `realization` codes on vowel rows in `_phone` and `_ophone`
  - updated printer IPA/XAR surfaces that consume those rows
  - expanded `phoneprep` reachable diphone inventory and legality model
- New config key:
  - `phonetize.process.realization.limit_emphatic_coloring: false`
- Affected components:
  - `src/akkapros/lib/phonetize.py`
  - `src/akkapros/lib/_phonetize_config.py`
  - `src/akkapros/cli/confwriter.py`
  - `src/akkapros/config/default.yaml`
  - `src/akkapros/lib/phoneprep.py`
  - `src/akkapros/lib/print.py`
  - `tests/integration_refs/regression_defaults.yaml`
  - `demo/akkapros/prosmaker/corpus-demo.yaml`
  - `demo/akkapros/lexlinks/construct-demo.yaml`

Normative examples:

- `ma.qâm` -> second syllable nucleus is colored from emphatic onset `q`
- `maq.rab` -> first nucleus is colored from emphatic coda `q`; second nucleus
  is colored by immediate carry
- `saq.rab` -> first nucleus remains plain because onset `s` blocks same-
  syllable coda coloring; second nucleus is colored by carry
- `maq.sab` -> first nucleus is colored from emphatic coda `q`; second nucleus
  remains plain because following onset `s` blocks carry

## Open Questions

None at draft time.

## Implementation Notes

- Owner: TBD
- Estimated effort: medium
- The preferred implementation shape is one dedicated coloring pass after Phase
  1 row building and before duration assignment so all coloring rules live in a
  single owning path.
- The parameter belongs under `phonetize.process.realization`, not under
  `timing_model`, because it changes segmental realization choice rather than
  duration behavior.
- `phoneprep` may use a legality helper model that is not literally identical
  to runtime phonetizer branching, but it must produce coverage results that
  satisfy the acceptance criteria above, including the special `t`, `d`, `k`
  recording-inventory exclusion.
- Integration fixtures and expected outputs for IPA and XAR must be immutable
  test-owned assets under `tests/`.

## Related

- Related ADRs: [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md), [ADR-012](../adr/012-phoneprep-coverage-and-sidecars.md), [ADR-011](../adr/011-multi-format-printer-outputs.md)
- Implementation CRs: [CR-088](../cr/088-extend-emphatic-vowel-coloring-to-coda-contexts-and-phoneprep.md)
- Related umbrella requirements: [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md), [REQ-006](006-diphone-recording-script-generator.md), [REQ-005](005-multi-format-printer-output.md)

## Non-Goals

- This requirement does not add new vowel realization codes.
- This requirement does not redesign syllabification or prosody boundaries.
- This requirement does not change pause timing, pause classification, or the
  duration solver beyond requiring that the new coloring pass happen before
  duration assignment.
- This requirement does not unify the phonetizer blocker set (`t`, `s`, `k`)
  and the `phoneprep` recording-inventory exclusion set (`t`, `d`, `k`).

## Security / Safety Considerations

- The new behavior is user-visible in emitted reading formats, so tests must
  pin examples explicitly rather than inheriting mutable defaults silently.
- Because phoneprep inventory expansion affects generated recording materials,
  legality changes must remain deterministic and reproducible under a fixed
  seed.
- Test fixtures for this feature must be immutable repository-owned data under
  `tests/` only.
