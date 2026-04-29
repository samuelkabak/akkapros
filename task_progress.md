# CR-093 Implementation Progress

## Phase 1: Spec Update (DONE)
- [x] Update CR-093 to Draft with new `mono_mode_accentuation_lengthening` parameter
- [x] Update REQ-048 to Draft with new approach

## Phase 2: Implementation
- [ ] Add `mono_mode_accentuation_lengthening` field to `PHONETIZE_SCHEMA` in `_phonetize_config.py`
- [ ] Add validation for `mono_mode_accentuation_lengthening` in `verify_phonetize_config()`
- [ ] Update `_shape_reference()` to accept `mono_lengthening` parameter
- [ ] In `realize_phone_rows()`, resolve `mono_mode_accentuation_lengthening` and apply it in mono mode
- [ ] Update the `accentuation_distribution_policy` config description
- [ ] Update `helpmsg.py` with the new parameter's help text
- [ ] Update `default.yaml` with the new parameter
- [ ] Update existing CR-093 tests to expect configurable elongation instead of zero
- [ ] Add test for `mono_mode_accentuation_lengthening = 0` (no elongation)
- [ ] Update integration test reference files for mono mode
- [ ] Run full test suite
- [ ] Update indexes
- [ ] Verify all ACs
