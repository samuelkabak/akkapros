---
cr_id: CR-096
status: Draft
priority: Medium
impact: Mutative
created: 2026-05-01
updated: 2026-05-01
implements: ''
---

# Change Request: Rename `mono_mode_accentuation_lengthening` to `basic_accentuation_lengthening`

# Summary

Rename the config parameter `mono_mode_accentuation_lengthening` (under `phonetize.process.timing_model.durations`) to `basic_accentuation_lengthening`. The behavior, default value (50 ms), validation range (`[0, round(0.5 * cvc_reference)]`), and all runtime semantics are unchanged. Only the name changes.

The rename affects the schema definition in `_phonetize_config.py`, the runtime read path in `phonetize.py`, the validation logic in `verify_phonetize_config()`, the config description strings, all YAML config files, the test code, and all governance documents that reference the old name.

---

# Motivation

- The name `mono_mode_accentuation_lengthening` is misleading: the parameter controls the accentuation lengthening value (default 50 ms) that is applied when the bimoraic model is not in use — it is the **basic** (default) elongation, as opposed to the **extra** lengthening (`0.5 * cvc_reference`) imposed by the bimoraic model. The old name incorrectly ties this value to "mono mode" as a prosody concept.
- The parameter applies whenever the accentuation model does not use the full bimoraic increment, which may extend beyond mono prosody mode in future use cases.
- `basic_accentuation_lengthening` more accurately describes the parameter's role: it is the basic accentuation elongation value (50 ms by default), as opposed to the extra mora-length increment (`0.5 * cvc_reference`) used in the bimoraic model.
- The word "basic" qualifies the **accentuation lengthening** (the amount of elongation), not the mode. Neither mono mode nor bi mode is "basic" — rather, 50 ms is the basic elongation, while `0.5 * cvc_reference` is extra lengthening beyond the basic value.
- This is a pure rename — no behavioral changes, no new features, no deprecation period.

---

# Scope

## Included

- Rename the schema field key from `'mono_mode_accentuation_lengthening'` to `'basic_accentuation_lengthening'` in `PHONETIZE_SCHEMA` in `_phonetize_config.py`.
- Update the field description string to use the new name.
- Update the `accentuation_distribution_policy` description string to reference the new name.
- Update the runtime read path in `phonetize.py` (`realize_phone_rows()`) to read `'basic_accentuation_lengthening'` instead of `'mono_mode_accentuation_lengthening'`.
- Update the validation logic in `verify_phonetize_config()` in `_phonetize_config.py`:
  - Variable name `mono_lengthening` → `basic_lengthening`.
  - Validation path string `'phonetize.process.timing_model.durations.mono_mode_accentuation_lengthening'` → `'phonetize.process.timing_model.durations.basic_accentuation_lengthening'`.
  - Error message strings referencing the old name.
- Update the `_shape_reference()` parameter name `mono_lengthening` → `basic_lengthening` in `phonetize.py` (internal parameter, but should match the concept).
- Update all YAML config files:
  - `src/akkapros/config/default.yaml`
  - `demo/akkapros/prosmaker/corpus-demo.yaml`
  - `demo/akkapros/lexlinks/construct-demo.yaml`
  - `tests/integration_refs/regression_defaults.yaml`
- Update test code:
  - `tests/test_phonetize_lib.py` — update all references in test function names, docstrings, comments, and assertions.
  - `tests/test_config_support.py` — update the string assertion that checks for the parameter name in the default YAML.
- Update governance documents:
  - `docs/internal/cr/093-skip-accent-elongation-in-mono-mode.md` — update all references to the old name in the CR body (the CR is `Done` but serves as the authoritative spec for this feature; references to the parameter name should reflect the current name).
  - `docs/internal/req/048-skip-accent-elongation-in-mono-mode.md` — update all references.
  - `docs/internal/review/015-cr093-polish-review.md` — update all references.
  - `docs/internal/cr/095-move-drift-tolerance-into-durations-bloc.md` — update the YAML examples that show the old name (this CR is `Draft` and should reference the new name).
- Update `task_progress.md` if it references the old name (informational only, not a governance record).
- Run `python scripts/update-indexes.py` after the CR is created.

## Not Included

- No behavioral changes to the parameter's default, validation, or runtime semantics.
- No changes to the `accentuation_distribution_policy` parameter or its behavior.
- No changes to the prosody layer or any other part of the pipeline.
- No deprecation or backward-compatibility shim for the old name — this is a hard rename.
- No changes to the `_shape_reference()` function signature beyond the parameter rename (the function is internal).

---

# Current Behavior

The config parameter `mono_mode_accentuation_lengthening` is defined under `phonetize.process.timing_model.durations` with:
- Default: 50 ms
- Type: int
- Validation: `[0, round(0.5 * cvc_reference)]`
- Description: "Additional duration in milliseconds attributed to accentuated syllables in mono mora mode..."

The parameter is referenced in:
1. `_phonetize_config.py`: schema definition, validation logic, config description strings
2. `phonetize.py`: runtime read in `realize_phone_rows()`, `_shape_reference()` parameter
3. 4 YAML config files
4. 2 test files
5. 4 governance documents (CR-093, REQ-048, REVIEW-015, CR-095)
6. `task_progress.md`

---

# Proposed Change

Rename `mono_mode_accentuation_lengthening` to `basic_accentuation_lengthening` everywhere it appears. The new name uses the same default (50), same type (int), same validation range, and same runtime behavior.

The `_shape_reference()` internal parameter `mono_lengthening` should be renamed to `basic_lengthening` for consistency.

---

# Technical Design

## 1. Schema change (`_phonetize_config.py`)

Change the field key and description:

```python
# Before:
'mono_mode_accentuation_lengthening': _field(
    50,
    'int',
    'Additional duration in milliseconds attributed to accentuated syllables in mono mora mode. '
    'Unlike bi mode where accentuation adds one mora (0.5 * cvc_reference) and forces prosodic '
    'units to multiples of two morae, mono mode uses this smaller configurable elongation. '
    'The value is distributed using the same accentuation_distribution_policy as bi mode. '
    'Default: 50 ms. Validation range: [0, round(0.5 * cvc_reference)].',
),

# After:
'basic_accentuation_lengthening': _field(
    50,
    'int',
    'Basic accentuation lengthening in milliseconds applied to accentuated syllables '
    'when the bimoraic model is not in use. Unlike bi mode where accentuation adds one mora '
    '(0.5 * cvc_reference) — extra lengthening beyond the basic value — this is the '
    'baseline elongation (default 50 ms). '
    'The value is distributed using the same accentuation_distribution_policy as bi mode. '
    'Default: 50 ms. Validation range: [0, round(0.5 * cvc_reference)].',
),
```

## 2. Config description update (`_phonetize_config.py`)

Update the `accentuation_distribution_policy` description string to reference the new name:

```python
# Before:
'In mono mode, the total increment is mono_mode_accentuation_lengthening ms.'

# After:
'When using basic accentuation lengthening (not the bimoraic model), the total increment is basic_accentuation_lengthening ms.'
```

## 3. Validation update (`_phonetize_config.py`)

```python
# Before:
mono_lengthening = float(durations.get('mono_mode_accentuation_lengthening', 50))
mono_lengthening_max = round(0.5 * cvc_reference)
if not (0 <= mono_lengthening <= mono_lengthening_max):
    add_failure(
        'phonetize.process.timing_model.durations.mono_mode_accentuation_lengthening',
        f'0 <= mono_mode_accentuation_lengthening <= round(0.5 * cvc_reference) = {mono_lengthening_max}',
        f'Mono-mode accentuation lengthening {mono_lengthening} is outside the allowed range [0, {mono_lengthening_max}].',
    )

# After:
basic_lengthening = float(durations.get('basic_accentuation_lengthening', 50))
basic_lengthening_max = round(0.5 * cvc_reference)
if not (0 <= basic_lengthening <= basic_lengthening_max):
    add_failure(
        'phonetize.process.timing_model.durations.basic_accentuation_lengthening',
        f'0 <= basic_accentuation_lengthening <= round(0.5 * cvc_reference) = {basic_lengthening_max}',
        f'Basic accentuation lengthening {basic_lengthening} is outside the allowed range [0, {basic_lengthening_max}].',
    )
```

## 4. Runtime read path (`phonetize.py`)

In `realize_phone_rows()`:

```python
# Before:
mono_lengthening = float(config['timing_model']['durations'].get('mono_mode_accentuation_lengthening', 50))

# After:
basic_lengthening = float(config['timing_model']['durations'].get('basic_accentuation_lengthening', 50))
```

Update all downstream uses of the `mono_lengthening` variable to `basic_lengthening`.

## 5. `_shape_reference()` parameter rename (`phonetize.py`)

```python
# Before:
def _shape_reference(analysis, config, *, accentuated, mora_mode='bi', mono_lengthening=0.0):

# After:
def _shape_reference(analysis, config, *, accentuated, mora_mode='bi', basic_lengthening=0.0):
```

Update the function body to use `basic_lengthening` instead of `mono_lengthening`.

## 6. YAML config files

In all four YAML files, change:

```yaml
# Before:
        mono_mode_accentuation_lengthening: 50

# After:
        basic_accentuation_lengthening: 50
```

## 7. Test files

### `tests/test_phonetize_lib.py`

- Update the docstring of `test_cr093_mono_mode_applies_configurable_elongation()` to reference the new name.
- Update any comments that reference `mono_lengthening` or `mono_mode_accentuation_lengthening`.
- The test logic itself (constructing phone rows, asserting durations) does not need to change — only the parameter name in the config dict passed to the test setup.

### `tests/test_config_support.py`

- Update the string assertion that checks for the parameter name in the default YAML output:

```python
# Before:
assert text.index("cvc_reference: 300") < text.index("drift_tolerance: 19") < text.index("mono_mode_accentuation_lengthening: 50")

# After:
assert text.index("cvc_reference: 300") < text.index("drift_tolerance: 19") < text.index("basic_accentuation_lengthening: 50")
```

## 8. Governance documents

### `docs/internal/cr/093-skip-accent-elongation-in-mono-mode.md`

Replace all occurrences of `mono_mode_accentuation_lengthening` with `basic_accentuation_lengthening`. Update the title and summary to reflect the new name. Add a revision history entry documenting the rename.

### `docs/internal/req/048-skip-accent-elongation-in-mono-mode.md`

Replace all occurrences of `mono_mode_accentuation_lengthening` with `basic_accentuation_lengthening`. Update the summary and interface notes.

### `docs/internal/review/015-cr093-polish-review.md`

Replace all occurrences of `mono_mode_accentuation_lengthening` with `basic_accentuation_lengthening`.

### `docs/internal/cr/095-move-drift-tolerance-into-durations-bloc.md`

Replace the YAML examples that show `mono_mode_accentuation_lengthening: 50` with `basic_accentuation_lengthening: 50`.

---

# Files Likely Affected

| File | Change |
|------|--------|
| `src/akkapros/lib/_phonetize_config.py` | Schema key, description strings, validation logic |
| `src/akkapros/lib/phonetize.py` | Runtime read path, `_shape_reference()` parameter |
| `src/akkapros/config/default.yaml` | YAML key rename |
| `demo/akkapros/prosmaker/corpus-demo.yaml` | YAML key rename |
| `demo/akkapros/lexlinks/construct-demo.yaml` | YAML key rename |
| `tests/integration_refs/regression_defaults.yaml` | YAML key rename |
| `tests/test_phonetize_lib.py` | Docstrings, comments, config dict keys |
| `tests/test_config_support.py` | String assertion |
| `docs/internal/cr/093-skip-accent-elongation-in-mono-mode.md` | All references |
| `docs/internal/req/048-skip-accent-elongation-in-mono-mode.md` | All references |
| `docs/internal/review/015-cr093-polish-review.md` | All references |
| `docs/internal/cr/095-move-drift-tolerance-into-durations-bloc.md` | YAML examples |
| `task_progress.md` | Informational references (if any) |

---

# Acceptance Criteria

- [ ] The schema field key is `'basic_accentuation_lengthening'` in `PHONETIZE_SCHEMA`.
- [ ] The field description uses the new name and updated wording.
- [ ] The `accentuation_distribution_policy` description references `basic_accentuation_lengthening`.
- [ ] The validation logic in `verify_phonetize_config()` uses the new config path and error messages.
- [ ] The runtime read in `realize_phone_rows()` reads `'basic_accentuation_lengthening'`.
- [ ] The `_shape_reference()` parameter is renamed to `basic_lengthening`.
- [ ] All four YAML config files use `basic_accentuation_lengthening: 50`.
- [ ] All test references use the new name.
- [ ] All governance documents (CR-093, REQ-048, REVIEW-015, CR-095) use the new name.
- [ ] The full test suite passes (`python -m pytest`).
- [ ] No references to `mono_mode_accentuation_lengthening` remain in `src/`, `tests/`, or `demo/`.
- [ ] Governance indexes are regenerated (`python scripts/update-indexes.py`).

---

# Risks / Edge Cases

- **No backward-compatibility shim**: Any user config files that use the old name will silently ignore the parameter (the runtime uses `.get('basic_accentuation_lengthening', 50)` with a fallback to the default). Users must update their configs. This is acceptable because:
  - The parameter was introduced in CR-093 (April 2026) and is relatively new.
  - The project is in active development (pre-v1.0).
  - The rename is part of a broader naming cleanup.
- **CR-095 conflict**: CR-095 is currently `Draft` and references the old name in its YAML examples. This CR must be implemented before or concurrently with CR-095 to avoid merge conflicts. If CR-095 is implemented first, this CR must update the CR-095 YAML examples as part of its scope.
- **No behavioral change**: The rename is purely cosmetic. All tests should pass without logic changes.

---

# Testing Strategy

Unit tests:

- Run the full test suite: `python -m pytest` — all tests must pass.
- The existing CR-093 tests in `test_phonetize_lib.py` construct config dicts with the parameter name. These must be updated to use the new name, and the tests must still pass.
- The `test_config_support.py` assertion checks the emitted YAML text for the parameter name. This must be updated.

Integration tests:

- Run `python -m pytest tests/ -k "integration"` to verify integration test reference files are updated.

Manual verification:

- `grep -r "mono_mode_accentuation_lengthening" src/ tests/ demo/` should return no results after implementation.
- `grep -r "basic_accentuation_lengthening" src/ tests/ demo/` should return results in the expected files.

---

# Rollback Plan

Revert the rename: change all occurrences of `basic_accentuation_lengthening` back to `mono_mode_accentuation_lengthening` in all affected files. No behavioral changes to revert.

---

# Related Issues

- `CR-093`: Introduced the parameter as `mono_mode_accentuation_lengthening`.
- `REQ-048`: Requirement for the configurable mono-mode accentuation lengthening.
- `REVIEW-015`: Polish review of CR-093 implementation.
- `CR-095`: Draft CR that references the old name in YAML examples.

---

# Tasks

## Implementation

- [ ] Rename schema field key in `_phonetize_config.py` from `'mono_mode_accentuation_lengthening'` to `'basic_accentuation_lengthening'`.
- [ ] Update field description string in `_phonetize_config.py`.
- [ ] Update `accentuation_distribution_policy` description string in `_phonetize_config.py`.
- [ ] Update validation logic in `verify_phonetize_config()` in `_phonetize_config.py`.
- [ ] Update runtime read path in `phonetize.py` (`realize_phone_rows()`).
- [ ] Rename `_shape_reference()` parameter `mono_lengthening` → `basic_lengthening` in `phonetize.py`.
- [ ] Update all four YAML config files.
- [ ] Update `tests/test_phonetize_lib.py` (docstrings, comments, config keys).
- [ ] Update `tests/test_config_support.py` (string assertion).

## Governance Documents

- [ ] Update `docs/internal/cr/093-skip-accent-elongation-in-mono-mode.md`.
- [ ] Update `docs/internal/req/048-skip-accent-elongation-in-mono-mode.md`.
- [ ] Update `docs/internal/review/015-cr093-polish-review.md`.
- [ ] Update `docs/internal/cr/095-move-drift-tolerance-into-durations-bloc.md`.
- [ ] Update `task_progress.md` if it references the old name.

## Verification

- [ ] Run `python -m pytest` — full suite passes.
- [ ] Run `grep -r "mono_mode_accentuation_lengthening" src/ tests/ demo/` — no results.
- [ ] Run `python scripts/update-indexes.py` — indexes regenerated.

---

# Implementation Blockers

No blockers known at draft time.

---

# Notes

- The internal variable name `mono_lengthening` in `_shape_reference()` and `realize_phone_rows()` is renamed to `basic_lengthening` for consistency, but this is an internal implementation detail. The public-facing change is the config key name.
- The `accentuation_distribution_policy` description string references the parameter by name. This must be updated to avoid confusion.
- CR-095 (Draft) references the old name in its YAML examples. If CR-095 is approved and implemented before this CR, the YAML examples in CR-095 will need to be updated as part of this CR's scope. If this CR is implemented first, CR-095 should be updated to use the new name before it is approved.
