---
cr_id: CR-089
status: Done
priority: Medium
impact: Mutative
created: 2026-04-23
updated: 2026-04-23
implements:
---

# Change Request: Rename extended_emphatic_coloring to limit_emphatic_coloring with inverted default

# Summary

Rename the phonetizer config key `extended_emphatic_coloring` to `limit_emphatic_coloring` with inverted semantics and default. The old key `extended_emphatic_coloring` (default `true`) is removed. The new key `limit_emphatic_coloring` defaults to `false`. The meaning of the new parameter is the inverse of the old parameter: `limit_emphatic_coloring: false` corresponds to `extended_emphatic_coloring: true` (extended coloring enabled), and `limit_emphatic_coloring: true` corresponds to `extended_emphatic_coloring: false` (limit coloring to onset‑only).

This rename aligns the key with the verb‑based naming pattern used elsewhere (`enable_resync_pause`, `merge_connector`, etc.) and makes the default `false` correspond to the more permissive (extended coloring enabled) behavior.

# Motivation

The extended emphatic‑coloring behavior introduced in CR‑088 is considered experimental. The rename prepares for a separate experimental‑feature guard (CR‑090) by establishing a verb‑based key name (`limit`) and a default that keeps the feature enabled (`false`). The inversion ensures that the default behavior (extended coloring enabled) remains the same after the rename.

# Scope

## Included

- Remove `phonetize.process.realization.extended_emphatic_coloring`.
- Add `phonetize.process.realization.limit_emphatic_coloring` with default `false`.
- Update the configuration schema (`_phonetize_config.py`) with the new key and inverted default.
- Update the phonetizer runtime (`phonetize.py`) to read `limit_emphatic_coloring` and invert the logic where needed (i.e., `extended = not config['process']['realization']['limit_emphatic_coloring']`).
- Update all repository YAML files that contain phonetize defaults or examples to rename the key and invert the value.
- Update `confwriter` help, list, get, set, default, and verify surfaces accordingly.
- Update any existing tests that reference `extended_emphatic_coloring` to use the new name and inverted values.

## Not Included

- Adding an experimental‑feature guard (that is CR‑090).
- Changing the underlying emphatic‑coloring algorithm beyond the config key rename and inversion.
- Modifying `phoneprep` or printer logic except where they depend on the renamed config key.

# Current Behavior

- `phonetize.process.realization.extended_emphatic_coloring` exists as a boolean with default `true`. When `true`, the phonetizer applies same‑syllable coda coloring and immediate next‑syllable carry in addition to onset‑triggered coloring.
- No guard prevents users from enabling this feature.
- Config verification does not check for experimental‑feature consent.

# Proposed Change

1. **Schema update** (`_phonetize_config.py`):
   - Remove `'extended_emphatic_coloring'` from `PHONETIZE_SCHEMA`.
   - Add `'limit_emphatic_coloring': _field(False, 'bool', 'When true, limit emphatic vowel coloring to the legacy onset‑only rule (non‑experimental). When false, enable same‑syllable emphatic‑coda coloring and immediate next‑syllable carry (experimental).')` under `'realization'`.

2. **Runtime update** (`phonetize.py`):
   - Replace every reference to `config['process']['realization']['extended_emphatic_coloring']` with `config['process']['realization']['limit_emphatic_coloring']`.
   - Invert the boolean where needed: `extended = not bool(config['process']['realization']['limit_emphatic_coloring'])`.

3. **YAML config updates**:
   - `src/akkapros/config/default.yaml`
   - `tests/integration_refs/regression_defaults.yaml`
   - `demo/akkapros/prosmaker/corpus-demo.yaml`
   - `demo/akkapros/lexlinks/construct-demo.yaml`
   In each file, rename `extended_emphatic_coloring` to `limit_emphatic_coloring` and invert the value (i.e., `true` → `false`, `false` → `true`).

4. **`confwriter` updates**:
   - Ensure `confwriter` can list, get, set, and verify the renamed key.
   - Update help text accordingly.

5. **Test updates**:
   - Update any test that directly references `extended_emphatic_coloring` in config or in assertions.
   - Invert boolean values as needed.

# Technical Design

## Configuration schema changes

In `_phonetize_config.py`, modify `PHONETIZE_SCHEMA`:

- Under `'realization'`, replace `'extended_emphatic_coloring'` with `'limit_emphatic_coloring'`, change default to `False`, and update description.

## Runtime changes

In `phonetize.py`, update `_apply_emphatic_vowel_coloring` and any other function that reads `extended_emphatic_coloring`. Use the inverted boolean as described.

## Backward compatibility

Because the key name changes and the default inverts, existing user configs that set `extended_emphatic_coloring` will be ignored (the key will be treated as unknown and cause a validation error). This is intentional: the rename is a breaking change that forces users to update their configs. The validation error will guide them to rename the key.

# Files Likely Affected

- `src/akkapros/lib/_phonetize_config.py` – schema, defaults.
- `src/akkapros/lib/phonetize.py` – runtime references.
- `src/akkapros/cli/confwriter.py` – help and command surfaces.
- `src/akkapros/config/default.yaml`
- `tests/integration_refs/regression_defaults.yaml`
- `demo/akkapros/prosmaker/corpus-demo.yaml`
- `demo/akkapros/lexlinks/construct-demo.yaml`
- `tests/test_phonetize_lib.py` – tests referencing the old key.
- `tests/test_config_support.py` – config loading/verification tests.
- `tests/test_integration.py` – integration configs.
- `docs/akkapros/configuration.md` – documentation of phonetize config keys.
- `docs/akkapros/phonetizer.md` – description of the extended coloring feature.

# Acceptance Criteria

- [x] Config key `phonetize.process.realization.extended_emphatic_coloring` is removed.
- [x] Config key `phonetize.process.realization.limit_emphatic_coloring` exists with default `false`.
- [x] Description of `limit_emphatic_coloring` clearly states that `false` enables extended coloring (experimental) and `true` limits coloring to onset‑only (non‑experimental).
- [x] Phonetizer runtime correctly interprets `limit_emphatic_coloring: false` as extended coloring enabled (i.e., `extended = True`).
- [x] All repository YAML files that serialize phonetize config are updated to include the renamed `limit_emphatic_coloring` key with inverted values.
- [x] `confwriter` surfaces (help, list, get, set, default, verify) include the renamed key.
- [x] Existing tests are updated to use the new key name and inverted values where needed.

# Risks / Edge Cases

- **Breaking change**: Existing user configs that set `extended_emphatic_coloring` will cause a validation error. This is acceptable because the feature is experimental and we want users to update their configs.
- **Default behavior unchanged**: The default remains extended coloring enabled (`limit_emphatic_coloring: false`), preserving the same behavior as before the rename.

# Testing Strategy

- Update existing unit tests for phonetizer config and runtime.
- Ensure that the integration test suite passes with the updated defaults.

# Rollback Plan

Revert the changes in the configuration schema, runtime, and YAML files. Because the rename is breaking, a rollback would also need to revert the key name back to `extended_emphatic_coloring` and restore its default `true`.

# Related Issues

- Implements the rename requested by the user.
- Updates [CR-088](088-extend-emphatic-vowel-coloring-to-coda-contexts-and-phoneprep.md) by renaming its config key.
- Separate from the experimental‑feature guard (CR‑090).

# Tasks

## Implementation

- [ ] Update `_phonetize_config.py` schema with renamed `limit_emphatic_coloring`.
- [ ] Update `phonetize.py` runtime to use the renamed key and invert logic.
- [ ] Update all repository YAML config files.
- [ ] Update `confwriter` surfaces.

## Tests

- [ ] Update existing unit tests for phonetizer config and verification.
- [ ] Ensure all tests pass with the new defaults.

## Documentation

- [ ] Update configuration documentation.
- [ ] Update phonetizer documentation regarding the renamed key.

## Review

- [ ] Verify that the rename works as specified.
- [ ] Verify that default behavior is unchanged (extended coloring enabled).