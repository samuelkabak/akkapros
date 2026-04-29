---
review_id: REVIEW-015
status: Done
created: 2026-04-29
reviewed_cr: CR-093
reviewer: '@spec'
---

# CR-093 Polish Review: Configurable Mono-Mode Accentuation Lengthening

## Summary

A polishing review of CR-093 implementation, checking consistency between code,
documentation, config files, and tests. No serious problems found. Minor
documentation inconsistencies identified below.

---

## Files Inspected

| File | Role |
|------|------|
| `src/akkapros/lib/phonetize.py` | Primary implementation |
| `src/akkapros/lib/_phonetize_config.py` | Schema, validation, config rendering |
| `src/akkapros/config/default.yaml` | Package default config |
| `tests/test_phonetize_lib.py` | Unit tests |
| `tests/integration_refs/regression_defaults.yaml` | Integration test reference config |
| `demo/akkapros/prosmaker/corpus-demo.yaml` | Demo config |
| `demo/akkapros/lexlinks/construct-demo.yaml` | Demo config |
| `docs/internal/cr/093-skip-accent-elongation-in-mono-mode.md` | CR document |
| `docs/internal/req/048-skip-accent-elongation-in-mono-mode.md` | REQ document |

---

## Findings

### 1. Resolved: `_shape_reference()` now used as generic target calculator

**Severity:** ✅ Resolved by refactoring

**Observation (initial):** The `_shape_reference()` function had a
`mono_lengthening` parameter and `mora_mode == 'mono'` branch, but was only
called with `accentuated=False`, so the mono branch was never entered. The
mono elongation was applied separately in `realize_phone_rows()` via
`_apply_accent_increment()`, and the drift calculation manually computed
`accent_target` rather than using `_shape_reference()`.

**Resolution:** The code was refactored so that `_shape_reference()` is now
called with `accentuated=True` and `mono_lengthening` to compute the total
target duration (base shape + accentuation increment) for the drift
calculation:

```python
total_target = _shape_reference(
    analysis, config, accentuated=True,
    mora_mode=mora_mode, mono_lengthening=mono_lengthening,
)
accent_target = total_target - shape_ref
drift_after_assignment = entry_drift + (emitted_total - total_target)
```

This makes `_shape_reference()` the single source of truth for target
durations in both accentuated and non-accentuated paths, and the
`mono_lengthening` parameter is now actively used.

### 2. Minor: `regression_defaults.yaml` has `drift_tolerance: 35` vs `default.yaml` has `drift_tolerance: 19`

**Severity:** Cosmetic (pre-existing, not CR-093 related)

**Observation:** The integration test reference config
(`tests/integration_refs/regression_defaults.yaml`) has `drift_tolerance: 35`
while the package default (`src/akkapros/config/default.yaml`) has
`drift_tolerance: 19`. This is a pre-existing difference and not related to
CR-093, but noted for awareness.

**Recommendation:** No action needed for this review.

### 3. Config file consistency: all 4 YAML files now have the new parameter

**Severity:** ✅ Clean

All four YAML files with `cvc_reference` now include
`mono_mode_accentuation_lengthening: 50` immediately after `cvc_reference: 300`:

- `src/akkapros/config/default.yaml` ✅
- `tests/integration_refs/regression_defaults.yaml` ✅
- `demo/akkapros/prosmaker/corpus-demo.yaml` ✅
- `demo/akkapros/lexlinks/construct-demo.yaml` ✅

### 4. Schema description consistency

**Severity:** ✅ Clean

The `accentuation_distribution_policy` description in
`_phonetize_config.py` (line 105) correctly mentions both modes:
"In bi mode, the total increment is 0.5 * cvc_reference (one mora).
In mono mode, the total increment is mono_mode_accentuation_lengthening ms."

The `mono_mode_accentuation_lengthening` field description (lines 143-147)
is consistent with the CR-093 doc.

### 5. Validation consistency

**Severity:** ✅ Clean

`verify_phonetize_config()` (lines 837-844) validates
`mono_mode_accentuation_lengthening` against `[0, round(0.5 * cvc_reference)]`,
matching the CR-093 spec.

### 6. Test coverage

**Severity:** ✅ Clean

Tests cover:
- Mono mode applies 50ms elongation (default) ✅
- Mono mode with 0 elongation (no elongation) ✅
- Mono mode uses half-beat synchronization basis ✅
- Mono mode applies elongation for CVC shapes ✅
- Mono mode applies elongation for CVVC shapes ✅
- Bi-mode regression (elongation preserved) ✅

### 7. Intonation path

**Severity:** ✅ Clean

`realize_row_intonation()` is unchanged. Intonation assignment is independent
of `mora_mode`.

### 8. Synchronization basis (CR-080)

**Severity:** ✅ Clean

`_resolve_synchronization_basis()` is unchanged. Mono mode still uses
half-beat basis.

---

## Overall Assessment

**Status:** Clean — no blocking issues found.

The implementation is consistent with the CR-093 specification. All acceptance
criteria are satisfied. The refactoring made `_shape_reference()` the single
source of truth for target durations in both accentuated and non-accentuated
paths.

---

## Verification Commands

```bash
python -m pytest --tb=short -q    # 367 passed
python scripts/update-indexes.py  # indexes regenerated
```
