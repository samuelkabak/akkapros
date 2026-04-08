---
cr_id: CR-033
status: Draft
priority: High
impact: Mutative
created: 2026-04-03
updated: 2026-04-04
implements: 'ADR-039, REQ-024'
---

# Change Request: Remove long_pause_weight from conf and cli options

# Summary

Stop reading the current configurable long-pause-weight parameter from both the
CLI surface and the grouped config surface, and hard-code the effective value
to `2` in the active implementation.

This CR is an early transition step for the timing-model replacement program.
It intentionally narrows the current interface before the broader replacement
algorithm is specified.

---

# Motivation

The timing-model redesign will replace the current computation logic more
substantially, so the project should stop preserving configuration surface area
that is expected to disappear. The current long-pause weighting option is one
such surface: removing it now reduces migration noise and clarifies that the
current implementation should treat the value as fixed.

The requested CR title uses `long_pause_weight`, but the current user-facing
parameter/config key is `long_punct_weight`. This CR applies to the existing
`long_punct_weight` surface while preserving the requested CR title verbatim.

---

# Scope

## Included

- Remove the long-pause-weight option from the metricalc CLI.
- Remove the long-pause-weight option from grouped config and generated default
  config documentation.
- Remove help-text and docs that present the value as configurable.
- Set the effective runtime value to a hard-coded constant of `2`.
- Update tests and internal/public docs to match the new fixed-value contract.

## Not Included

- Redesigning the full timing algorithm.
- Reordering the full pipeline so metrics runs before print.
- Defining the future metrics-output artifact that printer will consume.
- Removing other metrics parameters unless covered by later CRs.

---

# Current Behavior

The current metrics implementation exposes `long_punct_weight` through CLI
arguments, grouped config, help text, default config, and related docs. Users
can override the default runtime value even though that control is expected to
disappear as part of the replacement timing-model work.

---

# Proposed Change

Adopt the following contract.

- The runtime long-pause weight is fixed at `2`.
- Metricalc does not expose a CLI option for overriding that value.
- Grouped config does not expose a `metrics.long_punct_weight` setting.
- Fullprosmaker does not expose a metrics-stage override for that value.
- If a later `phonetize` timing-parameter section is introduced, it does not
  reintroduce `long_punct_weight` as a configurable member.
- Public docs and default config stop presenting long-pause weight as user-
  configurable.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/config/default.yaml`

Implementation direction:

- Introduce or reuse a single constant with effective value `2` for the current
  long-pause weighting behavior.
- Remove CLI parsing and config parsing for `long_punct_weight`.
- Keep the fixed value outside any future `phonetize` timing-parameter config
  section so CR-033 remains coherent with later timing-model structuring work.
- Ensure table/JSON run-context reporting reflects the fixed effective value
  without implying user configurability.
- Update generated/default documentation surfaces to remove the option.

Compatibility note:

- Existing configs that still declare `metrics.long_punct_weight` should be
  be treated according to the current unpublished-config policy during
  implementation. Because the config-file feature has not been published yet,
  this CR does not require a backward-compatibility migration path for old
  config layouts.

---

# Files Likely Affected

`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/config/default.yaml`
`docs/akkapros/`
`tests/`

---

# Acceptance Criteria

- [ ] The effective long-pause weight is hard-coded to `2`.
- [ ] `metricalc` no longer accepts a CLI option for overriding long-pause
      weight.
- [ ] `fullprosmaker` no longer accepts a metrics-stage CLI option for
      overriding long-pause weight.
- [ ] Grouped config no longer defines `metrics.long_punct_weight`.
- [ ] If a later `phonetize` timing-parameter section is present, it still does
  not define `long_punct_weight`.
- [ ] Default config and config docs no longer present long-pause weight as a
      configurable setting.
- [ ] Help text and public CLI docs no longer describe long-pause weight as
      user-configurable.
- [ ] Tests cover the removed option surfaces and the fixed runtime value.
- [ ] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [ ] Documentation is updated in configuration, generated/default config,
  confwriter-facing, fullprosmaker-facing, and any affected phonetizer-
  facing docs so the removed setting is not described anywhere.

---

# Risks / Edge Cases

Possible issues:

- saved user configs may still contain `metrics.long_punct_weight`
- tests may rely on configurable weighting in run-context output
- documentation may retain stale references to the removed option
- partial removal could leave grouped config, CLI, and runtime behavior out of
  sync

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- update detailed `run_tests()` coverage in affected modules for removed
  option surfaces, fixed-value behavior, and stale help/config references

Unit tests:

- fixed long-pause-weight value is applied in metrics runtime behavior
- grouped config schema no longer includes `metrics.long_punct_weight`
- CLI help no longer exposes the removed option
- phonetize timing-parameter schema, if introduced alongside this change, does
  not reintroduce `long_punct_weight`

Integration tests:

- metricalc and fullprosmaker continue to generate metrics outputs with the
  fixed value
- config-driven and default-driven runs continue to resolve the same fixed value
- docs/default config expectations stay aligned with the new surface

Manual review:

- inspect metrics docs and generated/default config for stale option references

---

# Rollback Plan

Restore the removed CLI/config surfaces together and revert the fixed-value
contract in one change. Partial rollback is discouraged because it would leave
surface and runtime behavior mismatched.

---

# Related Issues

- [ADR-039](../adr/039-replacement-of-timing-model.md)
- [REQ-024](../req/024-replacement-of-timing-model.md)
- [ADR-010](../adr/010-metrics-from-text-and-dual-percent-v.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)

---

# Tasks

## Implementation

- [ ] Remove `long_punct_weight` from CLI parsing surfaces
- [ ] Remove `long_punct_weight` from grouped config surfaces
- [ ] Hard-code the effective value to `2`
- [ ] Update help text and output/run-context reporting as needed

## Tests

- [ ] Update or add detailed built-in `run_tests()` coverage in affected
  modules
- [ ] Update or add pytest unit tests for removed CLI/config options
- [ ] Update or add pytest integration tests for fixed-value behavior

## Documentation

- [ ] Update `docs/akkapros/configuration.md` and generated/default config
  comments for the removed setting
- [ ] Create or update `docs/akkapros/confwriter.md` if config-edit examples or
  key inventories are affected
- [ ] Update `docs/akkapros/fullprosmaker.md` and any other impacted
  program/stage docs that mention metrics timing controls
- [ ] Keep `docs/akkapros/phonetizer.md` and
  `docs/akkapros/phonetizer-algorithm.md` synchronized anywhere this
  setting would otherwise still appear in timing-model examples or stage
  narratives

## Review

- [ ] Verify acceptance criteria

---

# Notes for CR-033

This CR is intentionally narrow and transitional. It is meant to prune one
configurable parameter from the current timing-model surface without claiming
that the broader replacement architecture is already complete.