---
cr_id: CR-077
status: Done
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
implements: 'ADR-046, REQ-027, REQ-031, REQ-033'
---

# Change Request: Retune Default Phonetizer Drift Tolerance and Segmental Floor

## Summary

Retune the repository's default phonetizer timing defaults so the active default values become `segmental_floor = 20` and `drift_tolerance = 19`, while the committed regression config remains pinned at `drift_tolerance = 35`.

This CR must update the internal default builders, the committed default config file, the committed demo YAML files, and the user-facing documentation that currently states the older defaults. The committed regression YAML stays intentionally pinned at `drift_tolerance = 35`. The CR must also treat regression changes as behavioral verification work, not as a gold-refresh exercise: the active package default changes, but regression behavior remains anchored to the pinned regression config unless a test explicitly exercises live defaults.

This CR narrows the currently active default-value contract inherited from [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md), [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md), and [CR-067](067-cap-adjacent-short-vowel-accent-spill-below-long-min.md). The earlier records remain historical, but their default values are no longer the active implementation target once this CR lands.

---

## Motivation

Why is this change needed?

- Default retune
- Config-contract update
- Documentation correction
- Regression-contract clarification

Current repository state shows these live defaults:

- `drift_tolerance = 0` in the default config and phonetizer verification defaults
- `segmental_floor = 10` in the default config and phonetizer verification defaults
- committed project YAML files still pin those older defaults except for the lexlinks demo, which already diverges to `drift_tolerance = 20`

That leaves the project with a split default surface: the canonical default config and demo configs must reflect the live package standard, while the regression config must remain deliberately stricter. The contract needs to state that split explicitly instead of treating all config surfaces as interchangeable.

The `drift_tolerance = 19` retune is behaviorally important. It widens the ordinary tolerance-gated branch for non-accented long-vowel cleanup relative to the old default `0`, but it is narrower than the regression-pinned `35`. The project therefore needs a CR that keeps live defaults and regression defaults distinct instead of silently collapsing them into one setting.

---

## Scope

## Included

- Change the active default `phonetize.process.timing_model.drift_tolerance` to `19`.
- Change the active default `phonetize.process.timing_model.durations.segmental_floor` to `20`.
- Update the canonical default config builder and the phonetizer verification default builder so both expose the same new defaults.
- Update the committed default config file `src/akkapros/config/default.yaml`.
- Update the committed default and demo YAML config files that currently carry these defaults:
  - `src/akkapros/config/default.yaml`
  - `demo/akkapros/lexlinks/construct-demo.yaml`
  - `demo/akkapros/prosmaker/corpus-demo.yaml`
- Keep `tests/integration_refs/regression_defaults.yaml` pinned at `drift_tolerance = 35` while still carrying `segmental_floor = 20`.
- Update user-facing documentation that currently states the old defaults or worked-example values where those values are meant to reflect package defaults.
- Update focused tests that pin the old defaults in config, verification, or runtime behavior.
- Avoid regression rebaselining unless a changed test is actually driven by the live-default path instead of the regression config.
- Require at least one focused verification path that demonstrates the `drift_tolerance = 19` solver branch, matching the live default, rather than relying on implicit defaults inside behavioral tests.
- Make the supersession relationship to the older default-setting records explicit.

## Not Included

- Changing the meaning of `drift_tolerance` itself.
- Changing the meaning of `segmental_floor` from validation-facing bound to runtime timing knob.
- Retuning other phonetizer timing defaults unless they must move to keep semantic verification valid.
- Removing `drift_tolerance` from the config surface.
- Broad redesign of the phonetizer solver.
- Updating disposable `tmp/` files.

---

## Current Behavior

Repository inspection on 2026-04-19 shows the following committed default surfaces:

- `src/akkapros/config/default.yaml` sets `drift_tolerance: 0` and `segmental_floor: 10`.
- `tests/integration_refs/regression_defaults.yaml` sets `drift_tolerance: 35` and `segmental_floor: 20`.
- `demo/akkapros/prosmaker/corpus-demo.yaml` sets `drift_tolerance: 0` and `segmental_floor: 10`.
- `demo/akkapros/lexlinks/construct-demo.yaml` sets `drift_tolerance: 20` and `segmental_floor: 10`.
- `tests/test_config_support.py` and `tests/test_phonetize_lib.py` assert the old defaults directly.
- `docs/akkapros/phonetizer-algorithm.md` states the live default as `drift_tolerance = 0`.
- `docs/akkapros/varco-verification.md` still records a worked configuration with `drift_tolerance = 12` and `segmental_floor = 10`.

The older governance history behind those defaults is also explicit:

- [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md) and [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md) moved the active default `drift_tolerance` to `0`.
- [CR-067](067-cap-adjacent-short-vowel-accent-spill-below-long-min.md) introduced `segmental_floor = 10` as the shared validation floor.

Under the current implementation contract, ordinary non-accented long-vowel cleanup is tolerance-gated. Raising the active default tolerance from `0` to `19` changes the default branch conditions in Phase 2 realization for default-backed runs, while the regression config continues to exercise the separately pinned `35` path.

---

## Proposed Change

Adopt these defaults as the new active package-internal values:

- `phonetize.process.timing_model.drift_tolerance = 19`
- `phonetize.process.timing_model.durations.segmental_floor = 20`

The implementation must update the committed default and demo config surfaces so they reflect those live defaults, while preserving the deliberate regression-config override at `35`.

The implementation must also treat the regression impact as a contract-verification task:

- if a default-backed path changes after the new defaults are applied, the change must be explained by the solver contract under the new tolerance and floor values
- regression references should remain stable unless a test or artifact truly follows live defaults instead of the pinned regression config
- “tests pass after rebaselining” is not sufficient verification for this CR

For `drift_tolerance`, the expected contract consequence is that some ordinary non-accented long vowels that previously crossed the recovery threshold under the default `0` may now remain unchanged when absolute drift is within `19 ms`. The implementation must verify that this broader default branch is active where intended and does not break the meaning of the existing diagnostics such as `drift_tolerance_effect`.

For `segmental_floor`, the expected contract consequence is limited to config, verification, and documented baseline behavior. The parameter remains validation-facing and must not become a direct runtime timing knob merely because its default increases from `10` to `20`.

---

## Technical Design

Explain how it should be implemented.

Implementation surfaces:

Config/default builders:

- `src/akkapros/lib/config.py`
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/config/default.yaml`

Committed YAML configs:

- `demo/akkapros/lexlinks/construct-demo.yaml`
- `demo/akkapros/prosmaker/corpus-demo.yaml`
- `tests/integration_refs/regression_defaults.yaml`

User-facing docs:

- `docs/akkapros/phonetizer.md`
- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/varco-verification.md`
- any other committed user-facing page that states these defaults as current package defaults

Verification and regression surfaces likely affected:

- `tests/test_config_support.py`
- `tests/test_phonetize_lib.py`
- `tests/test_integration.py`
- `tests/test_metrics_stats.py`
- demo artifacts under `demo/akkapros/lexlinks/results/` if they are regenerated from the updated defaults

Required implementation discipline:

- keep the change focused on default-value retuning and the resulting documentation and regression validation work
- preserve the existing semantics of `drift_tolerance` and `segmental_floor`
- verify the new default branch behavior directly instead of inferring correctness from broad pytest success alone
- if demo artifacts or regression references are refreshed, use the canonical generation path and compare the changed outputs against the stated solver contract

Required semantic verification for the new default tolerance:

- prove that the default path now differs from the previous `drift_tolerance = 0` behavior on at least one representative case where ordinary long-vowel cleanup is tolerance-gated
- prove that the changed behavior is still consistent with the active long-vowel cleanup contract from [CR-074](074-apply-accentuation-before-ordinary-long-vowel-drift-recovery.md) and [CR-075](075-humanize-phonetizer-diagnostic-names-and-replace-ordinary-vowel-correction-rate-with-drift-tolerance-effect.md)
- if a regression artifact changes, identify whether the change came from tolerated drift, validation-floor changes, or both

Required semantic verification for the new default floor:

- prove that shared config verification still accepts the default config with `segmental_floor = 20`
- prove that the raised floor still respects the relevant vowel and consonant minimum invariants instead of silently weakening or bypassing validation

---

## Files Likely Affected

src/akkapros/lib/config.py  
src/akkapros/lib/phonetize.py  
src/akkapros/config/default.yaml  
demo/akkapros/lexlinks/construct-demo.yaml  
demo/akkapros/prosmaker/corpus-demo.yaml  
tests/integration_refs/regression_defaults.yaml  
docs/akkapros/phonetizer.md  
docs/akkapros/phonetizer-algorithm.md  
docs/akkapros/varco-verification.md  
tests/test_config_support.py  
tests/test_phonetize_lib.py  
tests/test_integration.py  
tests/test_metrics_stats.py  
demo/akkapros/lexlinks/results/erra_construct.json  
demo/akkapros/lexlinks/results/erra_construct_phone.txt  

List the likely implementation and verification surfaces so the CR remains self-contained as an execution prompt.

---

## Acceptance Criteria

- [x] The active default config produced by code and by `src/akkapros/config/default.yaml` sets `drift_tolerance = 19`.
- [x] The active default config produced by code and by `src/akkapros/config/default.yaml` sets `segmental_floor = 20`.
- [x] The committed demo YAML config files `demo/akkapros/lexlinks/construct-demo.yaml` and `demo/akkapros/prosmaker/corpus-demo.yaml` use `drift_tolerance = 19` and `segmental_floor = 20`, while `tests/integration_refs/regression_defaults.yaml` intentionally remains pinned at `drift_tolerance = 35` with `segmental_floor = 20`.
- [x] Focused config tests are updated to assert the new defaults instead of the old ones.
- [x] Focused phonetizer verification tests are updated to assert the new defaults instead of the old ones.
- [x] At least one focused runtime or integration test demonstrates that the `drift_tolerance = 19` branch, matching the live default, changes the tolerance-gated behavior relative to `0` on a representative non-accented long-vowel case.
- [x] The implementation verifies that default-backed changes are consistent with the active phonetizer timing contract and does not rebalance regression references that still run through the pinned regression config.
- [x] User-facing docs that describe current phonetizer defaults or worked default configurations are updated so they do not state the superseded default values as current.
- [x] `segmental_floor` remains validation-facing only; no new runtime timing behavior is introduced for it.
- [x] The implementation review or completion note explicitly names the older records whose default-value contract was superseded.

Acceptance criteria should be specific enough that verification does not require reconstructing hidden assumptions from other records.

---

## Risks / Edge Cases

Possible issues:

- raising `drift_tolerance` may change regression artifacts in ways that look like a bug even when they are contract-correct
- raising `segmental_floor` may expose hidden validation assumptions in demo or regression configs
- some docs may describe sample settings rather than package defaults, so the implementation must distinguish “worked example” from “current default” carefully
- the lexlinks demo already diverges on `drift_tolerance`, so aligning it to the new standard may change checked-in demo outputs substantially
- broad gold-refreshing without targeted explanation would weaken the regression contract

---

## Testing Strategy

Unit tests:

- update config-default assertions in `tests/test_config_support.py`
- update phonetizer verification-default assertions in `tests/test_phonetize_lib.py`
- add or update a focused phonetizer-lib test that compares behavior under explicit `drift_tolerance = 0` and explicit `drift_tolerance = 19` on a representative non-accented long-vowel case
- keep or add validation tests showing `segmental_floor = 20` still satisfies the shared minimum-bound invariants

Integration tests:

- keep config-backed integration tests that load `tests/integration_refs/regression_defaults.yaml` stable under the pinned regression value `35`
- if a live-default-backed integration path changes, verify the changed rows or diagnostics against the tolerance-gated branch contract before updating references
- keep a comparison test that shows higher `drift_tolerance` changes the relevant rates or emitted behavior without changing the denominator population incorrectly

Manual or scripted verification:

- regenerate any affected demo or regression artifacts through the canonical wrapper or CLI path already used by the repository
- compare old and new outputs for at least one changed sample and state why the change is expected under `drift_tolerance = 19`
- run the narrowest relevant pytest slices for config support, phonetizer library behavior, and affected integration coverage before broader suite runs

Describe the verification path directly in the CR so the implementer does not need to search broadly for how to prove completion.

---

## Rollback Plan

Revert the default values to `drift_tolerance = 0` and `segmental_floor = 10`, restore the previous committed YAML files and docs, and roll back any regression references or demo artifacts that were updated solely because of this retune.

If the new defaults reveal an unintended solver defect, fix the defect separately or revert this CR rather than normalizing the defect through regression rebaselining.

---

## Related Issues

- [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
- [CR-067](067-cap-adjacent-short-vowel-accent-spill-below-long-min.md)
- [CR-074](074-apply-accentuation-before-ordinary-long-vowel-drift-recovery.md)
- [CR-075](075-humanize-phonetizer-diagnostic-names-and-replace-ordinary-vowel-correction-rate-with-drift-tolerance-effect.md)
- [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- [REQ-033](../req/033-phonetizer-pause-bands-and-pause-metrics-reporting.md)

---

## Tasks

## Implementation

- [x] Update the default config builders to emit `drift_tolerance = 19` and `segmental_floor = 20`.
- [x] Update `src/akkapros/config/default.yaml` to match the code defaults.
- [x] Update the committed demo YAML config files to match the new defaults and keep the regression YAML pinned at `35`.
- [x] Update any committed demo-artifact regeneration paths or comments if they state the old defaults explicitly.

## Tests

- [x] Update focused default-value assertions in config and phonetizer tests.
- [x] Add or update a focused test that proves the `drift_tolerance = 19` branch matching the live default activates the intended tolerance-gated behavior without relying on implicit defaults.
- [x] Re-run affected default and regression slices and confirm that the regression-backed references remain stable under the pinned regression config.

## Documentation

- [x] Update user-facing docs that state the old defaults as current package defaults.
- [x] Update worked-example docs where the example is meant to reflect the active default baseline.
- [x] Keep historical internal records intact and explain supersession in the implementation review rather than rewriting the old records as if they always used the new values.

## Review

- [x] Confirm that any regression or demo-artifact updates are explained by the new default contract.
- [x] Confirm that `segmental_floor` remains validation-only.
- [x] Confirm that the new defaults are consistent across code, default YAML, committed config YAMLs, and docs.

---

## Implementation Blockers

Leave empty.

---

## Notes

This CR is intentionally self-contained so an implementation request such as `implement CR-077` can proceed from the CR itself plus only the narrowly scoped references listed above.

The committed project YAML count is currently four. If additional committed YAML config files are added before implementation, they should be reviewed against this same default-alignment requirement if they expose these keys.

Implementation completed on 2026-04-19.

Superseded default-value contract notes:

- `drift_tolerance = 0` from [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md) and [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md) is no longer the active live default.
- `segmental_floor = 10` from [CR-067](067-cap-adjacent-short-vowel-accent-spill-below-long-min.md) is no longer the active default.
- The earlier CR-077 implementation state that temporarily aligned the regression config with the live default is superseded; the regression config now intentionally remains pinned at `35`.

Verification notes:

- Focused default and phonetizer-library coverage passed after the retune.
- A focused runtime test now proves, using explicit `drift_tolerance` values, that the `19` branch matching the live default keeps the fricative-onset non-accented long-vowel case `šā` unchanged where explicit `0` forced ordinary long-vowel adjustment.
- The regression config in `tests/integration_refs/regression_defaults.yaml` remains pinned at `35`, so the regression-backed golds continue to validate the stronger tolerance path rather than the live default path.
- [docs/akkapros/varco-verification.md](../../akkapros/varco-verification.md) was intentionally left unchanged because it explicitly documents a fixed worked sample configuration rather than the live package defaults.
