---
cr_id: CR-090
status: Implemented
priority: Medium
impact: Mutative
created: 2026-04-23
updated: 2026-04-23
implements: 'REQ-046'
---

# Change Request: Add experimental feature guard to phonetizer

# Summary

Add a new top‑level config key `allow_experimental` (default `false`) that must be `true` before any experimental phonetizer feature can be enabled. Two features are considered experimental:

- `limit_emphatic_coloring: true` (i.e., limit coloring to onset‑only, experimental)
- `enable_resync_pause: true` (experimental)

If either experimental feature is present in the effective configuration while `allow_experimental` is `false`, config verification must fail and the program must exit with a verification error.

This change ensures that users explicitly acknowledge the experimental status of these features before they can be used. Because the default configuration does not enable any experimental feature (`limit_emphatic_coloring: false` is the default, non‑experimental behavior), verification will pass. Users must set `allow_experimental: true` to enable the experimental feature `limit_emphatic_coloring: true` (limit coloring to onset‑only).

# Motivation

Experimental features need a clear guard to prevent users from inadvertently enabling them without acknowledging their unstable status. The guard also provides a single point of control for future experimental additions.

The extended emphatic‑coloring behavior (now `limit_emphatic_coloring: false`) and the resynchronization‑pause insertion (`enable_resync_pause: true`) are both experimental. Users should be required to explicitly opt in before these features can be used.

# Scope

## Included

- Add a new config key `phonetize.process.allow_experimental` of type `bool` with default `false`.
- Update the config verification logic (`verify_phonetize_config`) to check that whenever `limit_emphatic_coloring` is `true` or `enable_resync_pause` is `true`, `allow_experimental` must also be `true`. If not, verification must fail with a clear error.
- Update all repository YAML files that serialize active phonetize defaults or examples to include `allow_experimental: false` (the default) because the default `limit_emphatic_coloring: false` is non‑experimental and verification will pass.
- Update `confwriter` help, list, get, set, default, and verify surfaces accordingly.
- Add verification tests that confirm the guard works.

## Not Included

- Changing the underlying emphatic‑coloring algorithm.
- Changing the behavior of `enable_resync_pause` beyond the guard.
- Modifying `phoneprep` or printer logic except where they depend on the guard.

# Current Behavior

- `limit_emphatic_coloring` defaults to `false` (extended coloring enabled, non‑experimental).
- `enable_resync_pause` defaults to `false` (experimental when `true`).
- No guard prevents users from enabling these features.
- Config verification does not check for experimental‑feature consent.

# Proposed Change

1. **Add `allow_experimental` key** (`_phonetize_config.py`):
   - Add `'allow_experimental': _field(False, 'bool', 'Must be true to enable experimental phonetizer features. Currently guarded features: limit_emphatic_coloring: true (limit coloring to onset‑only) and enable_resync_pause: true. Set to false to block experimental features and cause verification failure if any are enabled.')` under `'process'`.

2. **Update config verification** (`_phonetize_config.py`):
   - Extend `verify_phonetize_config` to enforce the following rule:
     If the effective configuration contains either `limit_emphatic_coloring: true` or `enable_resync_pause: true`, then `allow_experimental` must be `true`.
   - If `allow_experimental` is `false` and an experimental feature is enabled, produce a failure with a clear message indicating which experimental feature is enabled and that `allow_experimental` must be set to `true`.

3. **Update YAML config files**:
   - `src/akkapros/config/default.yaml`
   - `tests/integration_refs/regression_defaults.yaml`
   - `demo/akkapros/prosmaker/corpus-demo.yaml`
   - `demo/akkapros/lexlinks/construct-demo.yaml`
   In each file, add `allow_experimental: false` (the default) because the default `limit_emphatic_coloring: false` is non‑experimental and verification will pass.

4. **Update `confwriter` surfaces**:
   - Ensure `confwriter` can list, get, set, and verify the new `allow_experimental` key.
   - Update help text accordingly.

5. **Add tests**:
   - Provide a config with `limit_emphatic_coloring: true`, `allow_experimental: false`, expect verification failure.
   - Provide a config with `enable_resync_pause: true`, `allow_experimental: false`, expect verification failure.
   - Provide a config with both experimental features and `allow_experimental: true`, expect verification success.
   - Default config (no overrides) must pass verification because `allow_experimental` defaults to `false` and `limit_emphatic_coloring` defaults to `false` (non‑experimental).

# Technical Design

## Configuration schema changes

In `_phonetize_config.py`, modify `PHONETIZE_SCHEMA`:

- Add `'allow_experimental': _field(False, 'bool', 'Must be true to enable experimental phonetizer features. Currently guarded features: limit_emphatic_coloring: true (limit coloring to onset‑only) and enable_resync_pause: true.')` under `'process'`.

## Verification changes

Add a new check in `verify_phonetize_config` after the config is normalized and the runtime view is built. The check should:

- Read `allow_experimental` from the raw merged config.
- Read `limit_emphatic_coloring` from the raw config under `process.realization`.
- Read `enable_resync_pause` from the raw config under `process.timing_model`.
- If (`limit_emphatic_coloring` is `True`) or (`enable_resync_pause` is `True`) and `allow_experimental` is `False`:
  - Produce a failure with path `'phonetize.process.allow_experimental'` (or a combined path) and a reason explaining which experimental feature is enabled.

## Backward compatibility

Because `allow_experimental` defaults to `false` and `limit_emphatic_coloring` defaults to `false` (non‑experimental), the default configuration will pass verification. Users must set `allow_experimental: true` to enable experimental features like `limit_emphatic_coloring: true`.

# Files Likely Affected

- `src/akkapros/lib/_phonetize_config.py` – schema, verification, defaults.
- `src/akkapros/cli/confwriter.py` – help and command surfaces.
- `src/akkapros/config/default.yaml`
- `tests/integration_refs/regression_defaults.yaml`
- `demo/akkapros/prosmaker/corpus-demo.yaml`
- `demo/akkapros/lexlinks/construct-demo.yaml`
- `tests/test_phonetize_lib.py` – verification tests.
- `tests/test_config_support.py` – config loading/verification tests.
- `tests/test_integration.py` – integration configs.
- `docs/akkapros/configuration.md` – documentation of phonetize config keys.

# Acceptance Criteria

- [x] New config key `phonetize.process.allow_experimental` exists with default `false`.
- [x] Config verification fails with a clear error when `limit_emphatic_coloring` is `true` or `enable_resync_pause` is `true` while `allow_experimental` is `false`.
- [x] Config verification passes when `allow_experimental` is `true` and either experimental feature is enabled.
- [x] Default configuration (with `limit_emphatic_coloring: false` and `enable_resync_pause: false`) passes verification because `allow_experimental` defaults to `false` and no experimental feature is enabled.
- [x] All repository YAML files that serialize phonetize config are updated to include `allow_experimental: false` (the default) because the default configuration passes verification.
- [x] `confwriter` surfaces (help, list, get, set, default, verify) include the new key.
- [x] New verification tests are added for the experimental‑feature guard.

# Risks / Edge Cases

- **Default behavior unchanged**: The default remains extended coloring enabled (`limit_emphatic_coloring: false`), which is non‑experimental and passes verification with `allow_experimental: false`. Regression outputs remain unchanged.
- **Multiple experimental features**: The guard only checks the two listed features. Future experimental features must be added to the same guard logic.
- **Verification order**: The guard must run after config merging but before any other semantic validation, so that the error is surfaced early.

# Testing Strategy

## Unit tests

- Add focused tests in `test_phonetize_lib.py` that verify the guard:
  - Provide a config with `limit_emphatic_coloring: true`, `allow_experimental: false`, expect verification failure.
  - Provide a config with `enable_resync_pause: true`, `allow_experimental: false`, expect verification failure.
  - Provide a config with both experimental features and `allow_experimental: true`, expect verification success.
  - Default config (no overrides) must pass verification because `allow_experimental` defaults to `false` and `limit_emphatic_coloring` defaults to `false` (non‑experimental).

## Integration tests

- Update any integration test configs that rely on extended coloring being enabled by default; they must now also set `allow_experimental: true` (since default is `false`).
- Ensure that the integration test suite passes with the updated defaults.

## Manual verification

- Run `confwriter list phonetize` and confirm the new key appears.
- Run `confwriter verify` on a config with an experimental feature enabled but `allow_experimental: false` and observe the expected error.

# Rollback Plan

Revert the changes in the configuration schema, verification, and YAML files. The guard `allow_experimental` would be removed.

# Related Issues

- Implements the experimental‑feature guard requested by the user.
- Depends on [CR-089](089-rename-extended-emphatic-coloring-to-limit-emphatic-coloring.md) (rename of `extended_emphatic_coloring`).
- Updates [REQ-046](../req/046-extended-emphatic-vowel-coloring-and-phoneprep-coverage.md) by adding the guard.

# Tasks

## Implementation

- [x] Update `_phonetize_config.py` schema with `allow_experimental`.
- [x] Update config verification to enforce the guard.
- [x] Update all repository YAML config files.
- [x] Update `confwriter` surfaces.

## Tests

- [x] Add new unit tests for the experimental‑feature guard.
- [x] Update integration test configs and expected outputs.
- [x] Ensure all tests pass with the new defaults.

## Documentation

- [x] Update configuration documentation.
- [x] Update phonetizer documentation regarding the experimental feature guard.

## Review

- [x] Verify that the guard works as specified.
- [x] Verify that default behavior is extended coloring blocked because `allow_experimental` defaults to `false`.
- [x] Verify that `confwriter` surfaces are updated.