---
cr_id: CR-093
status: Done
priority: High
impact: Mutative
created: 2026-04-28
updated: 2026-04-29
implements: 'REQ-048'
---

# Change Request: Configurable Mono-Mode Accentuation Lengthening

## Summary

Introduce a new configurable parameter `mono_mode_accentuation_lengthening` under `phonetize.process.timing_model.durations` that controls the additional duration (in ms) attributed to accentuated syllables in mono mora mode. Unlike bi mode — where accentuation adds one full mora (`0.5 * cvc_reference`) and forces prosodic units to multiples of two morae — mono mode uses a smaller, configurable elongation whose value is set by this parameter.

The parameter is scalable with `scale` like all other duration values. Its default is 50 ms, with validation range `[0, round(0.5 * cvc_reference)]` using a dynamic maximum computed from the configured `cvc_reference`.

The additional duration is distributed using the same `accentuation_distribution_policy` as bi mode.

---

## Motivation

- Mono-mode prosody does not use bimoraic parity gating; accentuation is not about balancing mora counts.
- The `0.5 * cvc_reference` elongation is a bimoraic concept that adds an extra mora's worth of duration to accentuated syllables.
- However, completely skipping accentuation elongation in mono mode (as in the previous version of this CR) is too rigid — a small, configurable elongation is appropriate for mono mode.
- The `~` marker should still drive intonation (pitch contour) in mono mode.
- This change makes mono-mode phonetizer output configurable: researchers can set the mono-mode accentuation lengthening to 0 (no elongation) or any value up to `round(0.5 * cvc_reference)`.

---

## Scope

### Included

- Add `mono_mode_accentuation_lengthening` field to `PHONETIZE_SCHEMA` under `durations`, after `cvc_reference`.
- Default value: 50 ms.
- Validation: min = 0, max = `round(0.5 * cvc_reference)` (dynamic, computed from the configured `cvc_reference`).
- Scalable with `scale` like all other duration values.
- In `realize_phone_rows()`, when `mora_mode == "mono"` and `allow_accentuation=True` and `analysis['accent_shape'] is not None`:
  - Apply `mono_mode_accentuation_lengthening` ms instead of `0.5 * cvc_reference`.
  - Distribute using the same `accentuation_distribution_policy` mechanism.
- Keep the `~` marker's effect on intonation: `realize_row_intonation()` must still assign the `stress` intonation token to accentuated syllables in mono mode.
- Keep the synchronization basis as already defined by `CR-080` (half-beat for mono).
- Update the `accentuation_distribution_policy` config description to clarify it applies in both modes but with different elongation amounts.
- Update `helpmsg.py` with the new parameter's help text.
- Update `confwriter` to emit the new parameter.
- Update all project config files that include phonetizer durations.
- Update tests: mono-mode accentuation tests must now expect the configurable elongation instead of zero elongation.
- Update integration test reference files for mono mode.

### Not Included

- Changing the synchronization basis logic from `CR-080`.
- Changing how `realize_row_intonation()` works — intonation assignment is unchanged.
- Changing bi-mode behavior in any way.
- Changing the prosody layer's accentuation logic.
- Removing the `accentuation_distribution_policy` config option — it remains valid for both modes.

---

## Current Behavior

In `realize_phone_rows()` (phonetize.py), when `allow_accentuation=True` and `analysis['accent_shape'] is not None`:

- **Bi mode:** `_apply_accent_increment()` is called with `0.5 * cvc_reference` as the total increment, distributed via `accentuation_distribution_policy`.
- **Mono mode (current CR-093 implementation):** The entire accentuation elongation block is skipped — `accent_target` stays `0.0` and no increment is applied.

The proposed change replaces the "skip entirely" behavior with a configurable elongation.

---

## Proposed Change

### 1. Add `mono_mode_accentuation_lengthening` to schema

Add a new field under `phonetize.process.timing_model.durations`:

```python
'mono_mode_accentuation_lengthening': _field(
    50,
    'int',
    'Additional duration in milliseconds attributed to accentuated syllables in mono mora mode. '
    'Unlike bi mode where accentuation adds one mora (0.5 * cvc_reference) and forces prosodic '
    'units to multiples of two morae, mono mode uses this smaller configurable elongation. '
    'The value is distributed using the same accentuation_distribution_policy as bi mode. '
    'Default: 50 ms. Validation range: [0, round(0.5 * cvc_reference)].',
),
```

### 2. Update `_shape_reference()` to use the new parameter

When `mora_mode == "mono"` and `accentuated=True`, use `mono_mode_accentuation_lengthening` instead of `one_mora_ref`:

```python
def _shape_reference(analysis, config, *, accentuated, mora_mode='bi', mono_lengthening=0):
    target = base_map[analysis['base_shape']]
    if accentuated and analysis['accent_shape'] is not None:
        if mora_mode == 'mono':
            target += mono_lengthening
        else:
            target += one_mora_ref
    return target
```

### 3. Update `realize_phone_rows()` for mono mode

When `mora_mode == "mono"` and `allow_accentuation=True` and `analysis['accent_shape'] is not None`:

- Resolve `mono_mode_accentuation_lengthening` from config.
- Call `_apply_accent_increment()` with the mono lengthening value instead of `0.5 * cvc_reference`.
- Set `accent_target = mono_mode_accentuation_lengthening` (or the realized portion after distribution caps).
- The drift calculation uses `shape_ref` without the accentuation mora (since `_shape_reference` already handles this).

### 4. Update config description

Update the `accentuation_distribution_policy` field description to clarify it applies in both modes.

### 5. Keep intonation assignment unchanged

`realize_row_intonation()` already checks `accentuated` and `row['accent'] == 'A'` to assign the `stress` intonation token. This logic is independent of `mora_mode` and must remain unchanged.

---

## Technical Design

### Schema addition

```python
'mono_mode_accentuation_lengthening': _field(
    50,
    'int',
    'Additional duration in milliseconds attributed to accentuated syllables in mono mora mode. '
    'Unlike bi mode where accentuation adds one mora (0.5 * cvc_reference) and forces prosodic '
    'units to multiples of two morae, mono mode uses this smaller configurable elongation. '
    'The value is distributed using the same accentuation_distribution_policy as bi mode. '
    'Default: 50 ms. Validation range: [0, round(0.5 * cvc_reference)].',
),
```

### Validation

In `verify_phonetize_config()`, add a check that `mono_mode_accentuation_lengthening` is within `[0, round(0.5 * cvc_reference)]`.

### Runtime resolution

In `realize_phone_rows()`, resolve the mono lengthening value from the runtime config:

```python
mono_lengthening = float(durations.get('mono_mode_accentuation_lengthening', 50))
```

### Accentuation distribution

The `_apply_accent_increment()` function currently uses `one_mora_ref` (which is `0.5 * cvc_reference`) as the total increment. For mono mode, pass `mono_lengthening` instead. The distribution logic (primary_share / adjacent_share) remains the same.

### Changes to `_shape_reference()`

```python
def _shape_reference(analysis, config, *, accentuated, mora_mode='bi', mono_lengthening=0):
    one_mora_ref, two_mora_ref, three_mora_ref = _timing_refs(config)
    base_map = {
        'CV': one_mora_ref,
        'CVV': two_mora_ref,
        'CVC': two_mora_ref,
        'CVVC': three_mora_ref,
    }
    target = base_map[analysis['base_shape']]
    if accentuated and analysis['accent_shape'] is not None:
        if mora_mode == 'mono':
            target += mono_lengthening
        else:
            target += one_mora_ref
    return target
```

---

## Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/lib/_phonetize_config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/lib/confwriter.py` (if exists)
`tests/test_phonetize_lib.py`
`tests/test_integration.py`
`tests/integration_refs/` (mono-mode reference files)

---

## Acceptance Criteria

- [x] Given mono-mode input with accentuated syllables, when `realize_phone_rows()` processes them, then `mono_mode_accentuation_lengthening` ms is applied (distributed via `accentuation_distribution_policy`) instead of `0.5 * cvc_reference`.
- [x] Given mono-mode input with accentuated syllables, when `realize_row_intonation()` processes them, then the `stress` intonation token is still assigned to accentuated syllables.
- [x] Given bi-mode input with accentuated syllables, when `realize_phone_rows()` processes them, then the `0.5 * cvc_reference` elongation is applied exactly as before (backward compatibility).
- [x] Given mono-mode input without accentuated syllables, when `realize_phone_rows()` processes them, then behavior is unchanged (no regression for non-accentuated syllables).
- [x] Given any mode, when `realize_row_intonation()` processes rows, then intonation assignment is unchanged.
- [x] The `mono_mode_accentuation_lengthening` parameter defaults to 50 ms and validates within `[0, round(0.5 * cvc_reference)]`.
- [x] The `accentuation_distribution_policy` config description clarifies it applies in both modes.
- [x] Existing bi-mode tests pass without modification.
- [x] New tests pin mono-mode accentuation timing with the configurable elongation.
- [x] Integration test reference files for mono mode are updated.

---

## Risks / Edge Cases

- If `mono_mode_accentuation_lengthening` is set to 0, mono mode behaves as in the previous CR-093 (no elongation).
- If `mono_mode_accentuation_lengthening` exceeds the segmental caps, the distribution solver caps it at the legal maximum (same as bi mode behavior).
- The dynamic max `round(0.5 * cvc_reference)` ensures the mono elongation never exceeds the bi-mode mora increment.
- Legacy mono-mode inputs without the parameter use the default (50 ms).

---

## Testing Strategy

Unit tests:

- Add a test that constructs mono-mode phone rows with an accentuated syllable and verifies that `mono_mode_accentuation_lengthening` ms is applied.
- Add a test that constructs mono-mode phone rows with `mono_mode_accentuation_lengthening = 0` and verifies no elongation.
- Add a test that constructs bi-mode phone rows with an accentuated syllable and verifies that the elongation is applied (regression guard).
- Verify that `_shape_reference()` with `mora_mode='mono'` and `accentuated=True` uses `mono_lengthening` instead of `one_mora_ref`.

Integration tests:

- Run a representative mono pipeline and verify that accentuated syllables in `_phone.txt` have durations consistent with the configured elongation.
- Run a representative bi pipeline and verify that accentuated syllables still show the full mora elongation.

All tests must be self-sufficient: use hardcoded inputs or fixtures under `tests/`, not files from `demo/`, `outputs/`, or `tmp/`.

---

## Rollback Plan

Revert the mono-mode changes in `realize_phone_rows()` and `_shape_reference()` to restore the previous behavior (skip entirely). Remove the `mono_mode_accentuation_lengthening` parameter from the schema. Bi-mode behavior is unaffected.

---

## Related Issues

- `CR-027`: Introduced prosody mora mode selection (bi/mono).
- `CR-080`: Added half-beat synchronization for mono mode in the phonetizer.
- `REQ-019`: Requirement for prosody mora mode selection.
- `REQ-048`: Requirement for this CR.

---

## Tasks

### Implementation

- [x] Add `mono_mode_accentuation_lengthening` field to `PHONETIZE_SCHEMA` in `_phonetize_config.py`.
- [x] Add validation for `mono_mode_accentuation_lengthening` in `verify_phonetize_config()`.
- [x] Update `_shape_reference()` to accept `mono_lengthening` parameter.
- [x] In `realize_phone_rows()`, resolve `mono_mode_accentuation_lengthening` and apply it in mono mode.
- [x] Update the `accentuation_distribution_policy` config description.
- [x] Update `helpmsg.py` with the new parameter's help text.
- [x] Update `confwriter` to emit the new parameter.
- [x] Update all project config files that include phonetizer durations.

### Tests

- [x] Update existing CR-093 tests to expect configurable elongation instead of zero.
- [x] Add test for `mono_mode_accentuation_lengthening = 0` (no elongation).
- [x] Add test for bi-mode regression (elongation preserved).
- [x] Update integration test reference files for mono mode.

### Documentation

- [x] Update user-facing phonetizer docs.
- [x] Update the `mono_mode_accentuation_lengthening` help text.

### Review

- [x] Verify acceptance criteria.
- [x] Confirm compatibility with `CR-080` (synchronization basis unchanged).

---

## Implementation Blockers

No blockers known at draft time.

---

## Revision History

| Date | Change | Reason |
|------|--------|--------|
| 2026-04-28 | Initial draft | CR created |
| 2026-04-28 | Status → Done | All AC verified, 367/367 tests pass |
| 2026-04-29 | Status → Draft, full rewrite | New approach: configurable `mono_mode_accentuation_lengthening` parameter instead of skipping entirely |
| 2026-04-29 | Status → Done | All AC verified, 367/367 tests pass, tests updated for configurable elongation |

---

## Notes

The key insight is that mono-mode prosody does not use bimoraic balancing, so the `0.5 * cvc_reference` elongation is inappropriate. However, a smaller configurable elongation (default 50 ms) is appropriate for mono mode. The `~` marker's role in mono mode is primarily intonational (pitch contour), with a configurable durational component.

This CR does not change the synchronization basis logic from `CR-080`. Mono mode still uses half-beat synchronization (`0.5 * cvc_reference`) for pause targeting, mini-pause recovery, and drift normalization. Only the accentuation-specific elongation is changed.
