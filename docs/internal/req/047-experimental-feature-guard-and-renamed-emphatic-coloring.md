---
req_id: REQ-047
status: Draft
priority: Medium
impact: Mutative
created: 2026-04-22
updated: 2026-04-22
related_adrs: 'ADR-040, ADR-012, ADR-011'
implemented_by: 'CR-089'
---

# Requirement: Experimental Feature Guard and Renamed Emphatic Coloring

## Summary

The system shall require explicit user consent before enabling any experimental phonetizer feature. A new top‑level config key `allow_experimental` shall be added with default `false`; when `false`, any attempt to enable an experimental feature must cause config verification to fail.

Two features are initially considered experimental:
- Extended emphatic vowel coloring (currently `extended_emphatic_coloring: true`, after rename `limit_emphatic_coloring: false`).
- Resynchronization‑pause insertion (`enable_resync_pause: true`).

The extended‑coloring key shall be renamed to `limit_emphatic_coloring` with inverted semantics and a default that keeps the feature enabled (i.e., `false`). Because this is experimental, the default configuration will fail verification unless `allow_experimental` is set to `true` (or `limit_emphatic_coloring` is set to `true`).

## Motivation

Experimental features need a clear guard to prevent users from inadvertently enabling them without acknowledging their unstable status. The guard also provides a single point of control for future experimental additions.

Renaming `extended_emphatic_coloring` to `limit_emphatic_coloring` aligns the key with the verb‑based naming pattern used elsewhere (`enable`, `merge`, etc.). The default `false` corresponds to extended coloring enabled (experimental). The guard ensures that if `limit_emphatic_coloring` is `false` (extended coloring enabled) or `enable_resync_pause` is `true`, `allow_experimental` must be `true`.

## Acceptance Criteria

- [ ] Given the phonetizer configuration is loaded, when `allow_experimental` is `false`, then config verification passes only if both `limit_emphatic_coloring` is `true` and `enable_resync_pause` is `false`.
- [ ] Given the phonetizer configuration is loaded, when `limit_emphatic_coloring` is `false` and `allow_experimental` is `false`, then config verification fails with a clear error indicating that `allow_experimental` must be `true` to enable experimental extended coloring.
- [ ] Given the phonetizer configuration is loaded, when `enable_resync_pause` is `true` and `allow_experimental` is `false`, then config verification fails with a clear error indicating that `allow_experimental` must be `true` to enable experimental resync‑pause insertion.
- [ ] Given the phonetizer configuration is loaded, when `allow_experimental` is `true`, then config verification passes even if `limit_emphatic_coloring` is `false` and/or `enable_resync_pause` is `true`.
- [ ] Given the default configuration (no user overrides), when config verification runs, then it fails because `allow_experimental` defaults to `false` and `limit_emphatic_coloring` defaults to `false` (extended coloring enabled, experimental).
- [ ] Given the phonetizer runtime reads the config, when `limit_emphatic_coloring` is `false`, then the extended emphatic‑coloring behavior (same‑syllable coda coloring and immediate next‑syllable carry) is active.
- [ ] Given the phonetizer runtime reads the config, when `limit_emphatic_coloring` is `true`, then only the legacy onset‑only emphatic coloring is applied.
- [ ] Given `confwriter` lists, gets, sets, or verifies phonetize configuration, when the new keys are present, then `allow_experimental` and `limit_emphatic_coloring` appear in the appropriate surfaces with correct descriptions.
- [ ] Given any repository YAML file that serializes active phonetize defaults or examples, when this requirement is implemented, then the file includes `allow_experimental` and the renamed `limit_emphatic_coloring` key with values that keep the configuration verification‑passing (i.e., either `allow_experimental: true` or `limit_emphatic_coloring: true`).
- [ ] Given existing tests reference `extended_emphatic_coloring`, when the test suite runs, then those tests are updated to use `limit_emphatic_coloring` with inverted values where needed, and all tests pass.

## User Story

> As a user of the phonetizer, I want to be explicitly warned when I try to enable an experimental feature, so that I do not rely on unstable behavior unintentionally.

## Interface Notes

- New config key: `phonetize.process.allow_experimental` (bool, default `false`).
- Renamed config key: `phonetize.process.realization.limit_emphatic_coloring` (bool, default `false`, experimental when `false`).
- Experimental features:
  1. `limit_emphatic_coloring: false` (extended coloring enabled)
  2. `enable_resync_pause: true`
- Verification failure message must clearly state which experimental feature is enabled and that `allow_experimental` must be set to `true`.
- Affected components:
  - `src/akkapros/lib/_phonetize_config.py` – schema, defaults, verification.
  - `src/akkapros/lib/phonetize.py` – runtime reading of renamed key.
  - `src/akkapros/cli/confwriter.py` – help and command surfaces.
  - `src/akkapros/config/default.yaml`
  - `tests/integration_refs/regression_defaults.yaml`
  - `demo/akkapros/prosmaker/corpus-demo.yaml`
  - `demo/akkapros/lexlinks/construct-demo.yaml`
  - `tests/test_phonetize_lib.py`
  - `tests/test_config_support.py`
  - `tests/test_integration.py`

## Open Questions

None at draft time.

## Implementation Notes

- Owner: TBD
- Estimated effort: medium
- The rename is a breaking change; existing user configs that set `extended_emphatic_coloring` will cause a validation error. This is intentional to force users to update their configs and explicitly opt into experimental features.
- The default of `limit_emphatic_coloring` is `false` (limit disabled, extended coloring enabled). This preserves the default behavior from CR‑088. Because this is experimental, the default `allow_experimental` is `false` to block experimental features by default. To keep verification passing, existing configs must set `allow_experimental: true` or `limit_emphatic_coloring: true`.
- The guard logic should be placed in `verify_phonetize_config` after config merging but before other semantic validation.
- The guard can be extended later by adding new experimental features to the same condition.

## Related

- Related ADRs: [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md), [ADR-012](../adr/012-phoneprep-coverage-and-sidecars.md), [ADR-011](../adr/011-multi-format-printer-outputs.md)
- Implementation CRs: [CR-089](../cr/089-rename-extended-emphatic-coloring-and-add-experimental-guard.md)
- Related umbrella requirements: [REQ-046](046-extended-emphatic-vowel-coloring-and-phoneprep-coverage.md), [REQ-025](025-two-phase-phonetizer-structure-and-duration-pipeline.md)

## Non-Goals

- Adding backward‑compatibility auto‑migration for the old key name.
- Changing the underlying algorithm of extended coloring or resync‑pause insertion beyond the config guard.
- Adding other experimental features beyond the two listed.

## Security / Safety Considerations

- The guard prevents users from accidentally relying on experimental features in production‑like scenarios.
- Verification errors must be clear and actionable, guiding users to either disable the experimental feature or set `allow_experimental: true`.
- Because the default behavior remains extended coloring enabled, downstream scripts that rely on extended coloring will continue to work, but they must also have `allow_experimental: true` (since default is `false`) to pass verification.