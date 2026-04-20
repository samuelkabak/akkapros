---
cr_id: CR-081
status: Draft
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
implements: 'REQ-041'
---

# Change Request: Remove Phonetize Speech Config and Dead Speech Controls

# Summary

Remove the obsolete phonetize config subtree
`phonetize.process.timing_model.speech` and all related runtime, tooling,
tests, demos, and documentation that still treat
`phonetize.process.timing_model.speech.wpm` and
`phonetize.process.timing_model.speech.pause_ratio` as current contract.

Repository inspection on 2026-04-19 shows that these keys remain in the
phonetize default schema and shared semantic verification, but they no longer
drive phonetizer duration realization, pause targeting, drift folding,
mini-pause insertion, or long-vowel recovery. Metrics already computes output
`WPM` and `Pause ratio` directly from realized phone rows, so keeping a
phonetizer-owned `speech` config block creates dead contract surface rather
than active behavior.

This CR makes the removal executable as a single coordinated change. It narrows
the older phonetize config contract established by
[CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md), the
shared verification contract extended by
[CR-042](042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md),
and the grouped config expectations shaped by
[CR-044](044-restructure-stage-config-into-run-and-process-blocks.md). It also
preserves the downstream row-derived metrics model from
[CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md).

---

# Motivation

The repository should not keep dead configuration keys alive after the runtime
dependency on them has disappeared. Doing so causes four concrete problems:

- users see a `speech` block in YAML and reasonably assume it changes phonetize
  timing behavior
- `confwriter`, path overrides, and help text must continue to expose useless
  keys
- verification and tests spend time checking warning/blocking behavior for
  parameters that no longer affect execution
- docs and demos drift toward describing historical transition behavior instead
  of current runtime reality

The removal needs to be coordinated because the old keys are still spread
across schema/default emission, shared semantic verification, CLI tooling,
package docs, demo configs, and tests. A partial deletion would leave the
contract internally contradictory.

---

# Scope

## Included

- Remove `phonetize.process.timing_model.speech` from the approved config
  surface.
- Remove `phonetize.process.timing_model.speech.wpm` and
  `phonetize.process.timing_model.speech.pause_ratio` from:
  - phonetize default config/schema emission
  - shared phonetize semantic verification
  - CLI/config-path override and help surfaces
  - repository-owned tests
  - repository-owned demo/sample YAML files
  - user-facing docs that present approved phonetize config paths
- Remove warning/blocking behavior dedicated to `pause_ratio`.
- Remove positive-integer verification dedicated to `wpm`.
- Remove test and self-test expectations that still exercise those keys as
  live contract.
- Require old configs that still provide the removed `speech` block to fail
  clearly as unsupported current contract.
- Preserve metrics outputs that report row-derived `WPM` and `Pause ratio`.
- Update docs so speech-rate outputs are described as metrics artifacts, not as
  phonetize-config inputs.

## Not Included

- Changing the phonetizer duration solver beyond deleting dead config surface.
- Removing `WPM` or `Pause ratio` from metrics JSON or metrics table outputs.
- Reintroducing a replacement phonetize speech-control block under a different
  name.
- Changing row-derived metrics formulas already approved by
  [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md).
- Changing unrelated phonetize timing-model parameters.

---

# Current Behavior

Current repository behavior is internally split.

Observed current behavior on 2026-04-19:

- `src/akkapros/lib/phonetize.py` still defines `speech.wpm` and
  `speech.pause_ratio` in the phonetize timing-model default surface.
- `src/akkapros/lib/phonetize.py` still validates `wpm > 0`, blocks invalid
  `pause_ratio`, and warns when `pause_ratio > 70`.
- `src/akkapros/cli/phonetizer.py`, `confwriter`, config help, and related
  tests still treat `phonetize.process.timing_model.speech.wpm` as a valid path
  and still exercise `pause_ratio` verification behavior.
- package docs and demo YAML files still show a `speech:` block under
  `phonetize.process.timing_model`.
- metrics no longer consumes those inputs to compute reported speech outputs;
  row-derived `WPM` and `Pause ratio` come from realized phone-row durations.
- repository inspection does not show the phonetizer duration solver using
  `wpm` or `pause_ratio` as active timing inputs for phase-2 realization.

This means the current contract still advertises configuration that no longer
has a meaningful runtime effect.

---

# Proposed Change

Adopt the following active contract.

## 1. Remove the phonetize `speech` subtree entirely

- `phonetize.process.timing_model.speech` is no longer an approved config node.
- `phonetize.process.timing_model.speech.wpm` is removed.
- `phonetize.process.timing_model.speech.pause_ratio` is removed.
- Default config emission, schema introspection, and all generated help or
  config-path inventories must reflect that absence.

## 2. Remove dead verification logic tied to the deleted keys

- Shared phonetize semantic verification shall stop reading or validating the
  deleted `speech` keys.
- The warning rule `pause_ratio > 70` is removed from the active contract.
- The blocking rule `0 < pause_ratio < 100` is removed from the active
  contract.
- The positive-integer check for `wpm` is removed from the active contract.
- Any self-tests or confwriter preflight coverage that exist only to check
  those deleted relations shall be removed or rewritten around the new absence
  contract.

## 3. Removed keys must be rejected clearly

- Config files that still contain the deleted `speech` subtree must not be
  accepted silently.
- The approved behavior is an explicit unsupported-key failure consistent with
  the repository's existing removed-path handling.
- Tests must pin this behavior through test-owned config inputs under `tests/`
  rather than through `demo/` or mutable artifacts.

## 4. Preserve row-derived metrics outputs

- Metrics table and JSON outputs may continue to expose `WPM` and `Pause ratio`
  as derived report fields.
- User-facing docs must distinguish these row-derived metrics outputs from the
  removed phonetize config inputs.
- This CR must not remove the speech-reporting outputs introduced under the
  current metrics contract.

## 5. Clean all related repository surfaces in one pass

The implementation must remove or update all directly affected surfaces rather
than leaving mixed old/new contract fragments.

That includes at minimum:

- phonetize schema/defaults and runtime verification
- path override and config-tooling surfaces
- unit tests, integration tests, and self-tests that still assert the old keys
- user-facing docs and config docs
- repository-owned demo and sample YAML files that still show the `speech`
  block

---

# Technical Design

Minimum execution contract:

- delete the `speech` branch from the canonical phonetize config skeleton and
  runtime default materialization
- delete the corresponding phonetize verification code paths for `wpm` and
  `pause_ratio`
- delete any runtime constants or helper references that exist only to support
  the removed block
- remove config-path examples and confwriter/CLI tests that still exercise the
  removed keys as valid surface
- add replacement tests that prove:
  - the removed keys are absent from emitted config/help inventory
  - configs using the removed keys are rejected clearly
  - row-derived metrics outputs remain unchanged in contract

Migration expectations:

- no compatibility alias is required
- no silent ignore behavior is allowed
- removed-path handling should match other removed config-surface cleanup in the
  repository: explicit rejection, updated docs, and updated tests

Verification expectations:

- use focused config-support, phonetize, and integration tests that explicitly
  exercise removed-key rejection and absence from approved surfaces
- keep tests self-sufficient by using hardcoded config snippets or fixtures
  stored under `tests/`
- update package docs and demo configs in the same change so config examples do
  not lag behind the active contract

---

# Files Likely Affected

src/akkapros/lib/phonetize.py  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/confwriter.py  
src/akkapros/cli/fullprosmaker.py  
src/akkapros/config/default.yaml  
tests/test_phonetize_lib.py  
tests/test_config_support.py  
tests/test_integration.py  
docs/akkapros/phonetizer.md  
docs/akkapros/configuration.md  
docs/akkapros/confwriter.md  
demo/akkapros/**/*.yaml  

The final implementation may touch a subset of these files, but the change is
not complete until the live contract is coherent across config, verification,
tests, demos, and docs.

---

# Acceptance Criteria

- [ ] `phonetize.process.timing_model.speech` is absent from the approved
      config surface and default emitted YAML.
- [ ] `phonetize.process.timing_model.speech.wpm` and
      `phonetize.process.timing_model.speech.pause_ratio` are absent from
      config-path inventory, help, and docs.
- [ ] Shared phonetize verification no longer validates or warns on the removed
      keys.
- [ ] Configs that still provide the removed `speech` block fail clearly as
      unsupported current contract.
- [ ] Tests that previously asserted `pause_ratio` warning/blocking behavior are
      removed or rewritten to assert removed-key rejection or absence.
- [ ] Demo/sample YAML files no longer include a phonetize `speech` block.
- [ ] User-facing docs no longer present phonetize `wpm` or `pause_ratio` as
      approved configuration inputs.
- [ ] Metrics outputs still report row-derived `WPM` and `Pause ratio` where
      currently approved.
- [ ] Focused verification passes for config-surface, phonetizer, and
      integration surfaces touched by the removal.

---

# Risks / Edge Cases

- Users may still have local YAML files containing the deleted `speech` block;
  silent acceptance would hide the migration and keep the contract ambiguous.
- Some docs may mention `WPM` and `Pause ratio` as outputs; those references
  must be preserved where they describe metrics artifacts rather than config.
- Confwriter or path-override help may continue exposing stale nested keys if
  the schema cleanup is incomplete.
- Repository-owned demo configs are easy to overlook and would leave visible
  contract drift if not updated.

---

# Testing Strategy

Unit tests:

- config-schema/default tests confirm the `speech` block is absent
- phonetize verification tests confirm removed keys are no longer a supported
  validation surface
- removed-key tests confirm old `speech` paths are rejected clearly

Integration tests:

- config/CLI surfaces no longer advertise or accept the removed keys
- existing phonetizer and fullprosmaker flows still run without any `speech`
  config block present
- metrics outputs still expose row-derived `WPM` and `Pause ratio` where
  already approved

Manual/doc verification:

- inspect package docs and demo YAML examples for removal of the `speech` block
- verify no user-facing config example still shows
  `phonetize.process.timing_model.speech.*`

---

# Rollback Plan

Restore the `speech` subtree in the canonical phonetize config surface and
restore the matching verification/tooling/tests if downstream consumers are
found to rely on those keys.

Rollback should be all-or-nothing. Do not restore the keys only in docs or only
in schema, because that would recreate the same contract drift this CR removes.

---

# Related Issues

- [REQ-041](../req/041-remove-phonetize-speech-config-surface.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- [CR-042](042-add-shared-phonetize-config-verify-and-require-phonetizer-preflight.md)
- [CR-044](044-restructure-stage-config-into-run-and-process-blocks.md)
- [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md)

---

# Tasks

## Implementation

- [ ] Remove the phonetize `speech` subtree from schema/default config surfaces.
- [ ] Remove dead verification logic for `wpm` and `pause_ratio`.
- [ ] Remove stale CLI/config-tooling path support for the deleted keys.
- [ ] Reject old configs containing the removed `speech` block clearly.

## Tests

- [ ] Rewrite or remove tests that still assert live `pause_ratio` warning or
      blocking semantics.
- [ ] Add or update tests for removed-key absence and removed-key rejection.
- [ ] Verify touched tests use only test-owned inputs and configs.

## Documentation

- [ ] Remove the `speech` block from package docs and config examples.
- [ ] Update demo/sample YAML files to the new approved phonetize surface.
- [ ] Keep row-derived metrics-output documentation where still active.

## Review

- [ ] Verify acceptance criteria.
- [ ] Confirm supersession of the older phonetize speech-config contract is
      explicit in the resulting docs and behavior.


---

# Implementation Blockers

No blockers known at draft time.

---

# Notes

This CR intentionally treats the `speech` subtree as dead config surface rather
than as a deprecated-but-still-live runtime control. If compatibility handling
is desired later, it should be introduced explicitly by a newer record instead
of by preserving a silent no-op config path.