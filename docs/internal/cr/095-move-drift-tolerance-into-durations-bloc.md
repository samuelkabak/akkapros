---
cr_id: CR-095
status: Done
verified: 2026-05-01
priority: High
impact: Mutative
created: 2026-05-01
updated: 2026-05-01
implements: 'REQ-045 (extends)'
---

# Change Request: Move `drift_tolerance` into the `durations` Bloc and Make It Subject to Scale

# Summary

Move the `phonetize.process.timing_model.drift_tolerance` parameter into the
`phonetize.process.timing_model.durations` bloc, placing it immediately after
`cvc_reference`. Make `drift_tolerance` subject to the global duration `scale`
multiplier: when `scale != 1.0`, the effective drift tolerance is
`round(drift_tolerance * scale)`. All other numeric leaves in the `durations`
bloc are already subject to scale per CR-085; this change brings
`drift_tolerance` into the same contract.

The CR also requires verifying that this feature is correctly applied and, if
not, enforcing it across all config surfaces, the schema, the runtime code, the
CLI wrappers, the confwriter, and all YAML files in the project.

---

# Motivation

- **Consistency**: Every other numeric duration leaf under `durations` is
  already scaled by the global `scale` factor (CR-085). `drift_tolerance` is a
  timing threshold expressed in milliseconds, logically belongs in the
  `durations` bloc, and should scale uniformly with all other durations.
- **Correctness**: When a user sets `scale = 0.95`, they expect all timing
  parameters — including the drift tolerance — to shrink proportionally. The
  current placement outside `durations` means drift tolerance stays at its raw
  configured value regardless of scale, creating a mismatch.
- **Config coherence**: Grouping all duration-related parameters under
  `durations` makes the config structure self-documenting and reduces the risk
  of future parameters being accidentally excluded from scaling.

---

# Scope

## Included

- Move `drift_tolerance` from `timing_model` (sibling of `durations`) into
  `timing_model.durations`, positioned immediately after `cvc_reference`.
- Make `drift_tolerance` subject to scale: effective value =
  `round(drift_tolerance * scale)` when `scale != 1.0`; raw value when
  `scale == 1.0`.
- Update the schema (`_phonetize_config.py`): remove `drift_tolerance` from
  `PROCESS_KEYS` and the `timing_model` schema, add it to the `durations`
  schema.
- Update the runtime read path (`phonetize.py`) to read `drift_tolerance` from
  `config['process']['durations']` instead of `config['process']`.
- Update verification (`_phonetize_config.py`) to validate `drift_tolerance`
  inside `durations` and check the scaled effective value.
- Update the config field maps in `config.py` for `phonetizer` and
  `fullprosmaker` tools.
- Update CLI argument definitions in `phonetizer.py` and `fullprosmaker.py`.
- Update `helpmsg.py` help text paths.
- Update `default.yaml` (canonical default).
- Update `demo/akkapros/prosmaker/corpus-demo.yaml`.
- Update `demo/akkapros/lexlinks/construct-demo.yaml`.
- Update `tests/integration_refs/regression_defaults.yaml`.
- Update any test code that references the old path.
- Verify that the scale is applied to `drift_tolerance` and enforce it.

## Not Included

- Changing the default value of `drift_tolerance` (remains `19`).
- Changing the validation rules (remains non-negative integer).
- Renaming `drift_tolerance` itself.
- Changing any other parameter's position or behavior.

---

# Current Behavior

- `drift_tolerance` is declared at
  `phonetize.process.timing_model.drift_tolerance` (sibling of `durations`).
- It is listed in `PROCESS_KEYS` in `_phonetize_config.py`, which means it is
  treated as a top-level process key alongside `geminate_policy`,
  `accentuation_distribution_policy`, and `enable_resync_pause`.
- At runtime (`phonetize.py` line ~1412), it is read as:
  `tolerance = float(config['process']['drift_tolerance'])`
- The `_runtime_view_phonetize_config()` function copies `PROCESS_KEYS` into
  `process` and everything else into `timing_model`, so `drift_tolerance` ends
  up in `process` while `durations` ends up in `timing_model`.
- The scale derivation (`_derive_effective_durations`) only scales leaves under
  `durations`; `drift_tolerance` is outside that tree and is never scaled.
- Verification checks `drift_tolerance` at the old path
  `phonetize.process.timing_model.drift_tolerance`.
- Config field maps in `config.py` reference
  `process.timing_model.drift_tolerance`.
- CLI flags `--drift-tolerance` (phonetizer) and `--phonetize-drift-tolerance`
  (fullprosmaker) map to the old path.
- All YAML files place `drift_tolerance` at the `timing_model` level, before
  `durations`.

---

# Proposed Change

## 1. Schema change (`_phonetize_config.py`)

- Remove `'drift_tolerance'` from `PROCESS_KEYS`.
- Remove the `drift_tolerance` field from the `timing_model` schema dict.
- Add a new `drift_tolerance` field inside the `durations` schema dict,
  immediately after `cvc_reference`, with the same default (`19`), kind
  (`'int'`), and description.

## 2. Runtime read path (`phonetize.py`)

- Change the read in `realize_phone_rows()` from:
  `tolerance = float(config['process']['drift_tolerance'])`
  to:
  `tolerance = float(config['process']['durations']['drift_tolerance'])`

  Note: `config['process']` here is the runtime view where `PROCESS_KEYS` are
  placed under `process` and `durations` is under `timing_model`. Since
  `drift_tolerance` is no longer in `PROCESS_KEYS`, it will be placed under
  `timing_model.durations` by `_runtime_view_phonetize_config()`. The read path
  must therefore be updated to `config['timing_model']['durations']['drift_tolerance']`.

## 3. Scale application

The `_derive_effective_durations()` function already recursively scales all
numeric leaves under `durations` except `scale` itself. Since `drift_tolerance`
will now be a leaf under `durations`, it will automatically be scaled.

However, `drift_tolerance` is an integer (milliseconds), and the scale
multiplication produces a float. The current `_scale_duration_values()` returns
`float(node) * scale` for numeric leaves. The CR must ensure that the scaled
`drift_tolerance` is rounded to the nearest integer, since the runtime uses it
as an integer comparison threshold.

**Required change in `_scale_duration_values()` or `_derive_effective_durations()`:**
When scaling `drift_tolerance`, apply `round()` to the result so the effective
value remains an integer. The simplest approach: after `_scale_duration_values()`
produces the scaled dict, round the `drift_tolerance` leaf specifically.

Alternatively, modify `_scale_duration_values()` to accept an optional set of
paths that should be rounded after scaling. The recommended approach is to
round `drift_tolerance` in `_derive_effective_durations()` after the general
scaling pass.

## 4. Verification (`_phonetize_config.py`)

- Update the `drift_tolerance` validation check to use the new path
  `phonetize.process.timing_model.durations.drift_tolerance`.
- The verification should check the **raw configured** value (before scaling)
  for type/range validation, but the **effective scaled** value should be what
  the runtime actually uses. The current verification already reads from
  `raw_config` for type checks and from `config` (the runtime view) for
  effective checks. Since `drift_tolerance` will now be inside `durations`, the
  verification path must be updated accordingly.

## 5. Config field maps (`config.py`)

- In `TOOL_CONFIG_SECTIONS['phonetizer']`, change:
  `"process.timing_model.drift_tolerance": "drift_tolerance"`
  to:
  `"process.timing_model.durations.drift_tolerance": "drift_tolerance"`
- In `TOOL_CONFIG_SECTIONS['fullprosmaker']`, change:
  `"process.timing_model.drift_tolerance": "phonetize_drift_tolerance"`
  to:
  `"process.timing_model.durations.drift_tolerance": "phonetize_drift_tolerance"`

## 6. CLI argument definitions

- **`phonetizer.py`**: The `--drift-tolerance` flag's `dest` remains
  `drift_tolerance`, but the config path it maps to changes. The
  `_apply_process_flag_overrides()` function iterates over `PROCESS_KEYS` to
  apply overrides. Since `drift_tolerance` is removed from `PROCESS_KEYS`, this
  function will no longer pick it up. The override must be handled separately
  or `PROCESS_KEYS` must be kept but the path mapping updated. The recommended
  approach: keep `drift_tolerance` in `PROCESS_KEYS` for CLI flag purposes but
  update the config path in the field maps. However, since `PROCESS_KEYS` is
  also used by `_runtime_view_phonetize_config()` to split keys into `process`
  vs `timing_model`, removing it from `PROCESS_KEYS` is necessary for correct
  placement. Therefore, the CLI override in `phonetizer.py` must be updated to
  handle `drift_tolerance` as a special case or use the `--option` path.

  **Recommended approach**: Remove `drift_tolerance` from `PROCESS_KEYS`. In
  `phonetizer.py`, update `_apply_process_flag_overrides()` to handle
  `drift_tolerance` separately by writing to the new config path
  `phonetize.process.timing_model.durations.drift_tolerance`. In
  `fullprosmaker.py`, update `_apply_phonetize_process_overrides()` similarly.

- **`fullprosmaker.py`**: The `--phonetize-drift-tolerance` flag's `dest` is
  `phonetize_drift_tolerance`. The `_apply_phonetize_process_overrides()`
  function iterates over `PROCESS_KEYS` with a `phonetize_` prefix. Same
  treatment: handle `drift_tolerance` separately.

## 7. YAML files

All YAML files must move `drift_tolerance` from the `timing_model` level into
`timing_model.durations`, immediately after `cvc_reference`:

- `src/akkapros/config/default.yaml`
- `demo/akkapros/prosmaker/corpus-demo.yaml`
- `demo/akkapros/lexlinks/construct-demo.yaml`
- `tests/integration_refs/regression_defaults.yaml`

## 8. Help text (`helpmsg.py`)

- Update the help key `"phonetizer.drift_tolerance"` description if needed to
  reflect the new location and scaling behavior.
- Update `"fullprosmaker.phonetize_drift_tolerance"` similarly.

## 9. Tests

- Update any test that references the old config path
  `phonetize.process.timing_model.drift_tolerance`.
- Update any test that checks `PROCESS_KEYS` membership.
- Add a test that verifies `drift_tolerance` is scaled when `scale != 1.0`.
- Add a test that verifies `drift_tolerance` is NOT scaled when `scale == 1.0`.
- Add a test that verifies the rounded integer result.

---

# Technical Design

## Schema relocation

In `_phonetize_config.py`:

```python
# REMOVE from timing_model schema:
'drift_tolerance': _field(
    19,
    'int',
    'maximum local timing mismatch tolerated before the algorithm must fail',
),

# REMOVE from PROCESS_KEYS:
'drift_tolerance',

# ADD to durations schema, after 'cvc_reference':
'drift_tolerance': _field(
    19,
    'int',
    'Maximum local timing mismatch tolerated before the algorithm must fail. '
    'Subject to the global duration scale: effective value = '
    'round(drift_tolerance * scale) when scale != 1.0.',
),
```

## Scale rounding

In `_derive_effective_durations()` in `_phonetize_config.py`:

```python
def _derive_effective_durations(durations: dict[str, Any]) -> tuple[dict[str, Any], float]:
    raw_scale = durations.get('scale', 1.0)
    # ... existing validation ...
    scale = float(raw_scale)
    if scale <= 0:
        raise ValueError(...)
    if scale == 1.0:
        return deepcopy(durations), scale
    scaled = _scale_duration_values(deepcopy(durations), scale)
    # Round drift_tolerance to nearest integer after scaling
    if 'drift_tolerance' in scaled:
        scaled['drift_tolerance'] = round(scaled['drift_tolerance'])
    return scaled, scale
```

## Runtime read path

In `phonetize.py`, `realize_phone_rows()`:

```python
# Change from:
tolerance = float(config['process']['drift_tolerance'])
# To:
tolerance = float(config['timing_model']['durations']['drift_tolerance'])
```

## Verification path

In `_phonetize_config.py`, `verify_phonetize_config()`:

```python
# Change from:
if not isinstance(process['drift_tolerance'], int) or ...
    add_failure(
        'phonetize.process.timing_model.drift_tolerance',
        ...
    )

# To:
if not isinstance(durations.get('drift_tolerance'), int) or isinstance(durations.get('drift_tolerance'), bool) or durations.get('drift_tolerance', 0) < 0:
    add_failure(
        'phonetize.process.timing_model.durations.drift_tolerance',
        'drift_tolerance is an integer >= 0',
        'Drift tolerance must be a non-negative integer number of milliseconds.',
    )
```

Note: The verification should check the **raw configured** value (before
scaling) for type/range, since the raw value is what the user configured. The
effective scaled value is what the runtime uses.

## CLI override handling

In `phonetizer.py`, `_apply_process_flag_overrides()`:

```python
def _apply_process_flag_overrides(args: argparse.Namespace, phonetize_config: dict[str, object]) -> dict[str, object]:
    updated = {PHONETIZE_SECTION: phonetize_config}
    for key in PROCESS_KEYS:
        value = getattr(args, key)
        if value is None:
            continue
        updated = set_config_value(updated, f'phonetize.process.timing_model.{key}', value)
    # Handle drift_tolerance separately (now under durations)
    drift_value = getattr(args, 'drift_tolerance', None)
    if drift_value is not None:
        updated = set_config_value(updated, 'phonetize.process.timing_model.durations.drift_tolerance', drift_value)
    return get_section_config(updated, PHONETIZE_SECTION)
```

In `fullprosmaker.py`, `_apply_phonetize_process_overrides()`:

```python
def _apply_phonetize_process_overrides(args: argparse.Namespace) -> dict[str, object]:
    config = build_default_phonetize_config()
    for key in PROCESS_KEYS:
        value = getattr(args, f'phonetize_{key}')
        if value is not None:
            config['process']['timing_model'][key] = value
    # Handle drift_tolerance separately (now under durations)
    drift_value = getattr(args, 'phonetize_drift_tolerance', None)
    if drift_value is not None:
        from akkapros.lib.config import set_config_value, get_section_config
        updated = set_config_value({PHONETIZE_SECTION: config}, 'phonetize.process.timing_model.durations.drift_tolerance', drift_value)
        config = get_section_config(updated, PHONETIZE_SECTION)
    # ... rest of option handling ...
```

## YAML relocation

In all YAML files, change from:

```yaml
    timing_model:
      geminate_policy: "corrective"
      accentuation_distribution_policy: "80_20"
      drift_tolerance: 19
      enable_resync_pause: false
      durations:
        scale: 1.0
        segmental_ceiling: 310
        segmental_floor: 20
        cvc_reference: 300
        mono_mode_accentuation_lengthening: 50
```

To:

```yaml
    timing_model:
      geminate_policy: "corrective"
      accentuation_distribution_policy: "80_20"
      enable_resync_pause: false
      durations:
        scale: 1.0
        segmental_ceiling: 310
        segmental_floor: 20
        cvc_reference: 300
        drift_tolerance: 19
        mono_mode_accentuation_lengthening: 50
```

---

# Files Likely Affected

src/akkapros/lib/_phonetize_config.py  
src/akkapros/lib/phonetize.py  
src/akkapros/lib/config.py  
src/akkapros/lib/helpmsg.py  
src/akkapros/config/default.yaml  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/fullprosmaker.py  
src/akkapros/cli/confwriter.py (indirectly via schema)  
demo/akkapros/prosmaker/corpus-demo.yaml  
demo/akkapros/lexlinks/construct-demo.yaml  
tests/integration_refs/regression_defaults.yaml  
tests/test_phonetize_lib.py  
tests/test_config_support.py  
tests/test_integration.py  

---

# Acceptance Criteria

- [x] `drift_tolerance` is removed from `timing_model` (top level) and added to
      `timing_model.durations` immediately after `cvc_reference`.
- [x] `drift_tolerance` is removed from `PROCESS_KEYS`.
- [x] The schema, verification, and runtime all read/write `drift_tolerance` at
      the new path.
- [x] When `scale == 1.0`, `drift_tolerance` is used as configured (no scaling).
- [x] When `scale != 1.0`, the effective `drift_tolerance` is
      `round(drift_tolerance * scale)`.
- [x] The rounded integer result is used at runtime for drift comparison.
- [x] CLI flags `--drift-tolerance` (phonetizer) and
      `--phonetize-drift-tolerance` (fullprosmaker) correctly write to the new
      config path.
- [x] Config field maps in `config.py` reference the new path.
- [x] All YAML files (`default.yaml`, both demo YAMLs,
      `regression_defaults.yaml`) have `drift_tolerance` at the new position.
- [x] Help text reflects the new location and scaling behavior.
- [x] Existing tests pass after path updates.
- [x] New tests verify scaling behavior for `drift_tolerance`.

---

# Risks / Edge Cases

- **Backward compatibility**: Existing config files that specify
  `drift_tolerance` at the old path will cause an "unknown config key" error.
  The `REMOVED_TIMING_MODEL_KEYS` mechanism in `_phonetize_config.py` should be
  used to provide a clear error message pointing to this CR.
- **CLI flag backward compatibility**: The `--drift-tolerance` and
  `--phonetize-drift-tolerance` flags remain but write to a different config
  path. This is transparent to users.
- **Rounding precision**: `drift_tolerance` is an integer. After scaling, the
  result must be rounded to the nearest integer. Using `round()` with standard
  Python banker's rounding (.5 rounds to even) is acceptable since the scale
  values are typically rational numbers like 0.95, 1.05, etc.
- **Verification vs runtime**: Verification checks the raw configured value for
  type/range. The runtime uses the effective scaled value. These must remain
  consistent: if the raw value is valid, the scaled value should also be valid
  (since scale > 0 preserves non-negativity).

---

# Testing Strategy

Unit tests:

- `drift_tolerance` is no longer in `PROCESS_KEYS`.
- `drift_tolerance` appears in the `durations` schema after `cvc_reference`.
- `scale == 1.0` preserves the raw `drift_tolerance` value.
- `scale == 0.95` produces `round(19 * 0.95) = round(18.05) = 18`.
- `scale == 1.5` produces `round(19 * 1.5) = round(28.5) = 28`.
- Verification rejects non-integer or negative `drift_tolerance` at the new
  path.
- Config field maps resolve the new path correctly.

Integration tests:

- CLI `--drift-tolerance 10` on phonetizer writes to the new config path.
- CLI `--phonetize-drift-tolerance 10` on fullprosmaker writes to the new path.
- Full pipeline with `scale=0.95` uses the scaled drift tolerance.

Test fixtures and configs:

- All test-owned configs must use the new path.
- Tests must be self-sufficient (no dependency on `demo/` or `outputs/`).

---

# Rollback Plan

Revert all changes: move `drift_tolerance` back to `timing_model` level, add it
back to `PROCESS_KEYS`, restore old config paths in field maps and CLI handlers,
restore old YAML structure, and remove the rounding logic.

---

# Related Issues

- [CR-085](085-add-global-duration-scale-to-phonetizer-timing-model.md) —
  Original CR that added `durations.scale` and established the scaling contract.
- [CR-077](077-retune-default-phonetizer-drift-tolerance-and-segmental-floor.md) —
  Previous CR that retuned the default `drift_tolerance` value.

---

# Tasks

## Implementation

- [x] Move `drift_tolerance` in the schema from `timing_model` to `durations`.
- [x] Remove `drift_tolerance` from `PROCESS_KEYS`.
- [x] Add rounding logic in `_derive_effective_durations()` for
      `drift_tolerance`.
- [x] Update runtime read path in `phonetize.py`.
- [x] Update verification path in `_phonetize_config.py`.
- [x] Update config field maps in `config.py`.
- [x] Update CLI override handlers in `phonetizer.py` and `fullprosmaker.py`.
- [x] Update help text in `helpmsg.py`.
- [x] Add `drift_tolerance` to `REMOVED_TIMING_MODEL_KEYS` with reference to
      this CR for backward compatibility.

## Config/YAML

- [x] Update `src/akkapros/config/default.yaml`.
- [x] Update `demo/akkapros/prosmaker/corpus-demo.yaml`.
- [x] Update `demo/akkapros/lexlinks/construct-demo.yaml`.
- [x] Update `tests/integration_refs/regression_defaults.yaml`.

## Tests

- [x] Update existing tests that reference the old path.
- [x] Add tests for `drift_tolerance` scaling behavior.
- [x] Add tests for rounded integer result.
- [x] Verify all tests pass.

## Documentation

- [ ] Update `docs/akkapros/configuration.md` if it documents the old path.
- [ ] Update `docs/akkapros/phonetizer.md` if it documents the old path.

## Review

- [x] Verify that `drift_tolerance` is correctly scaled when `scale != 1.0`.
- [x] Verify that `drift_tolerance` is NOT scaled when `scale == 1.0`.
- [x] Verify backward compatibility error message for old path.
- [x] Verify all YAML files are consistent.

---

# Implementation Blockers

None known.

---

# Notes

- The `_runtime_view_phonetize_config()` function splits config into `process`
  (keys from `PROCESS_KEYS`) and `timing_model` (everything else). After
  removing `drift_tolerance` from `PROCESS_KEYS`, it will naturally land in
  `timing_model.durations`, which is the desired behavior.
- The `_apply_process_flag_overrides()` in `phonetizer.py` and
  `_apply_phonetize_process_overrides()` in `fullprosmaker.py` both iterate
  over `PROCESS_KEYS`. After removal, `drift_tolerance` must be handled as a
  special case in both functions.
- The `run_tests()` function in `phonetizer.py` sets `drift_tolerance=0` as a
  default for its test `_Args` object. This test must be updated to use the new
  config path.
- The `regression_defaults.yaml` has `drift_tolerance: 35` (different from the
  canonical default of `19`). This is intentional for regression testing and
  must be preserved at the new location.
