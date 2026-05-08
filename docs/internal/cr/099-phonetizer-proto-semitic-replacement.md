---
cr_id: CR-099
status: Done
priority: Medium
impact: Additive
created: 2026-05-08
updated: 2026-05-08
implements: 'REQ-049'
---

# Change Request: Phonetizer Proto-Semitic Pharyngeal/Glottal Replacement

# Summary

Add a boolean config key `phonetize.realization.replace_proto_semitic` (default
`false`) to the phonetizer. When `true`, the realization codes for input labels
`ETE` (ḥ), `AIN` (ʿ), and `ALE` (ʾ) are all mapped to `AL` (ʔ), while `HET`
(ḫ) remains `HE` (χ). When `false` (default), current behavior is preserved:
`ETE -> ET` (ħ), `HET -> HE` (χ), `AIN -> AI` (ʕ), `ALE -> AL` (ʔ).

This moves the proto-Semitic replacement from the printer's text-level IPA
mapping into the phonetizer's realization layer, so that all downstream
consumers (IPA, MBROLA, XAR, acute, bold) consistently reflect the chosen
policy without each consumer needing its own mapping. Once this CR is
implemented and verified, CR-100 removes the now-redundant printer
`--ipa-proto-semitic` option.

---

# Motivation

The printer currently implements proto-Semitic replacement via
`IPA_MAP_STRICT` / `IPA_MAP_OB` dictionaries in `print.py`. This only affects
IPA output. MBROLA `.pho` export and other formats are not covered. Moving the
replacement to the phonetizer realization layer ensures uniform behavior across
all downstream artifacts and removes the need for the printer's
`--ipa-proto-semitic` option (which will be removed in CR-100).

---

# Scope

## Included

- Add `replace_proto_semitic` boolean field to `phonetize.realization` in
  `_phonetize_config.py`
- Add `allow_experimental` guard: when `replace_proto_semitic = true` and
  `allow_experimental = false`, the phonetizer verification must report a
  failure (following the same pattern as `limit_emphatic_coloring` and
  `enable_resync_pause`)
- Update the `allow_experimental` comment in `default.yaml` to list
  `replace_proto_semitic` among the guarded features
- Modify `_base_realization_for_label` or the realization assignment path in
  `phonetize.py` to apply the replacement when the flag is `true`
- Add unit tests for the replacement logic
- Add integration tests that verify the replacement propagates through the
  full phonetizer pipeline
- Update `docs/akkapros/phonetizer-algorithm.md` to document the new feature
- Update `docs/akkapros/phonetizer-data-model.md` to note the conditional
  realization mapping

## Not Included

- Removal of the printer's `--ipa-proto-semitic` option (deferred to CR-100
  after this feature is verified)
- Changes to XAR output mapping (XAR already uses apostrophe convergence
  independently)
- Changes to emphatic vowel coloring logic

---

# Current Behavior

The phonetizer always maps input labels to fixed realization codes:

| Label | Glyph | Current Realization | IPA | MBROLA/X-SAMPA |
|-------|-------|---------------------|-----|-----------------|
| `ETE` | `ḥ`   | `ET`                | `ħ` | `X`             |
| `HET` | `ḫ`   | `HE`                | `x` | `x`             |
| `AIN` | `ʿ`   | `AI`                | `ʕ` | `H`             |
| `ALE` | `ʾ`   | `AL`                | `ʔ` | `?`             |

The printer separately maps these IPA values in `IPA_MAP_STRICT` (preserve) vs
`IPA_MAP_OB` (replace), but this only affects IPA text output.

---

# Proposed Change

## Config Surface

Add to `PHONETIZE_SCHEMA['process']['realization']` in
`src/akkapros/lib/_phonetize_config.py`:

```python
'replace_proto_semitic': _field(
    False,
    'bool',
    'When true, replace pharyngeal/glottal realizations: '
    'ḥ/ʿ/ʾ -> ʔ (AL), ḫ -> χ (HE). When false (default), '
    'preserve distinct realizations: ḥ -> ħ (ET), ḫ -> χ (HE), '
    'ʿ -> ʕ (AI), ʾ -> ʔ (AL).',
),
```

This key IS guarded by `allow_experimental`: setting `replace_proto_semitic`
to `true` requires `phonetize.process.allow_experimental = true`. When
`allow_experimental` is `false` and `replace_proto_semitic` is `true`, the
phonetizer verification must report a failure. This follows the same pattern
as the existing guards for `limit_emphatic_coloring` and `enable_resync_pause`.

## Realization Logic

Modify the realization assignment in `phonetize.py` so that when
`replace_proto_semitic` is `true`, the following label-to-realization mappings
are overridden:

| Label | Default Realization | Replacement Realization |
|-------|---------------------|-------------------------|
| `ETE` | `ET`                | `AL`                    |
| `AIN` | `AI`                | `AL`                    |
| `ALE` | `AL`                | `AL` (unchanged)        |
| `HET` | `HE`                | `HE` (unchanged)        |

The replacement applies at the point where `_base_realization_for_label` is
called, or equivalently where the first element of
`INPUT_TO_REALIZATION_CODES[label]` is selected. The simplest approach is to
add a helper function:

```python
def _resolve_realization(
    label: str,
    replace_proto_semitic: bool,
) -> str:
    code = INPUT_TO_REALIZATION_CODES[label][0]
    if replace_proto_semitic and label in ('ETE', 'AIN'):
        return 'AL'
    return code
```

Then replace calls to `_base_realization_for_label(label)` with
`_resolve_realization(label, replace_proto_semitic)`.

The `replace_proto_semitic` flag should be read from the effective phonetizer
config at the start of the realization pass and passed through to the
resolution function.

## Affected Code Paths

The realization is assigned in two places in `phonetize.py`:

1. `_new_segment_seed()` — called during Phase 1 row building for each segment
   glyph. This is the primary path for consonant rows.
2. The vowel-coloring pass — vowel rows get their realization from
   `_choose_vowel_realization()`, which is not affected by this change (vowels
   are not proto-Semitic consonants).

The replacement must also apply to the original stream (`_ophone.txt`), which
shares the same row-building code path.

---

# Technical Design

## Components

1. **`src/akkapros/lib/_phonetize_config.py`**: Add the `replace_proto_semitic`
   field to `PHONETIZE_SCHEMA['process']['realization']`.

2. **`src/akkapros/lib/_phonetize_config.py` — verification**: Add the
   `allow_experimental` guard in `verify_phonetize_config()`. Read
   `replace_proto_semitic` from `raw_config['process']['realization']` and
   add a failure when `allow_experimental` is `false` and
   `replace_proto_semitic` is `true`. Follow the exact pattern of the existing
   `limit_emphatic_coloring` guard (lines 660-666 of the current file).

3. **`src/akkapros/config/default.yaml`**: Update the `allow_experimental`
   comment to list `replace_proto_semitic` among the guarded features. The
   current comment reads:
   ```
   # Must be true to enable experimental phonetizer features. Currently guarded
   # features: limit_emphatic_coloring: true (limit coloring to onset‑only) and
   # enable_resync_pause: true. Set to false to block experimental features and
   # cause verification failure if any are enabled.
   ```
   Update to:
   ```
   # Must be true to enable experimental phonetizer features. Currently guarded
   # features: limit_emphatic_coloring: true (limit coloring to onset‑only),
   # enable_resync_pause: true, and replace_proto_semitic: true (merge
   # pharyngeal/glottal realizations). Set to false to block experimental
   # features and cause verification failure if any are enabled.
   ```

4. **`src/akkapros/lib/phonetize.py`**:
   - Add `_resolve_realization(label, replace_proto_semitic)` helper.
   - Modify `_new_segment_seed()` to accept and use the flag.
   - Thread the flag from `build_phone_rows()` through to the row-building
     calls.
   - The flag is read from `config['process']['realization']['replace_proto_semitic']`.

5. **`src/akkapros/lib/print.py`**: No changes in this CR. The printer will
   inherit the replacement from the phonetizer output automatically.

6. **`src/akkapros/cli/printer.py`**: No changes in this CR.

7. **`src/akkapros/cli/fullprosmaker.py`**: No changes in this CR.

## Data Flow

```
build_phone_rows(tilde_text, phonetize_config)
  -> reads config['process']['realization']['replace_proto_semitic']
  -> passes flag to row-building helpers
    -> _new_segment_seed(symbol, replace_proto_semitic)
      -> _resolve_realization(label, replace_proto_semitic)
        -> returns 'AL' for ETE/AIN when flag=true
        -> returns INPUT_TO_REALIZATION_CODES[label][0] otherwise
  -> phone rows written with modified realization codes
    -> downstream consumers (metrics, printer, MBROLA) use the codes as-is
```

---

# Files Likely Affected

```
src/akkapros/lib/_phonetize_config.py    — add config field + verification guard
src/akkapros/config/default.yaml         — update allow_experimental comment
src/akkapros/lib/phonetize.py            — add replacement logic
tests/test_phonetizer_replacement.py     — new unit/integration tests
docs/akkapros/phonetizer-algorithm.md    — document new feature
docs/akkapros/phonetizer-data-model.md   — update realization notes
```

---

# Acceptance Criteria

- [x] Config key `phonetize.realization.replace_proto_semitic` exists with
      default `false`.
- [x] When `allow_experimental = false` and `replace_proto_semitic = true`,
      the phonetizer verification reports a failure.
- [x] When `allow_experimental = true` and `replace_proto_semitic = true`,
      the phonetizer verification passes (no failure for this key).
- [x] The `allow_experimental` comment in `default.yaml` lists
      `replace_proto_semitic` among the guarded features.
- [x] When `replace_proto_semitic = false`, all realizations are identical to
      current behavior (verified by existing tests passing).
- [x] When `replace_proto_semitic = true`:
      - `ETE` (ḥ) rows have realization `AL` instead of `ET`
      - `AIN` (ʿ) rows have realization `AL` instead of `AI`
      - `ALE` (ʾ) rows keep realization `AL` (unchanged)
      - `HET` (ḫ) rows keep realization `HE` (unchanged)
- [x] Replacement applies to both `_phone.txt` and `_ophone.txt` streams.
- [x] Replacement propagates to IPA output (printer inherits from phone rows).
- [x] Replacement propagates to MBROLA `.pho` export.
- [x] Replacement does not affect other phonemes, hiatus markers, or
      vowel-transition markers.
- [x] Replacement does not affect emphatic vowel coloring.
- [x] Unit tests cover the replacement logic directly.
- [x] Integration tests verify the replacement through the full phonetizer
      pipeline.
- [x] Documentation updated.

---

# Risks / Edge Cases

- The `_new_segment_seed()` function is called for every segment glyph. The
  replacement check is a simple boolean + label lookup, so performance impact
  is negligible.
- The `_choose_vowel_realization()` function is not affected because vowels
  are not proto-Semitic consonants.
- The `ARU` (hiatus) label maps to `AL` already — this is correct and
  unaffected by the replacement.
- The `ENA` (vowel transition) label maps to `WA` or `YI` — unaffected.

---

# Testing Strategy

## Unit Tests (`tests/test_phonetizer_replacement.py`)

1. **`test_replace_proto_semitic_default_false`**: Verify that with default
   config, `ETE -> ET`, `HET -> HE`, `AIN -> AI`, `ALE -> AL`.

2. **`test_replace_proto_semitic_true`**: Verify that with
   `replace_proto_semitic = true`, `ETE -> AL`, `AIN -> AL`, `ALE -> AL`,
   `HET -> HE`.

3. **`test_replace_proto_semitic_other_phonemes_unaffected`**: Verify that
   `BET -> BE`, `DAL -> DA`, etc. are unchanged regardless of the flag.

4. **`test_replace_proto_semitic_hiatus_unaffected`**: Verify that `ARU -> AL`
   (hiatus) is unchanged.

5. **`test_replace_proto_semitic_vowel_transition_unaffected`**: Verify that
   `ENA -> WA`/`YI` (vowel transition) is unchanged.

## Integration Tests

1. **`test_replace_proto_semitic_full_pipeline`**: Run the full phonetizer
   pipeline on a small input containing `ḥ`, `ḫ`, `ʿ`, `ʾ` with
   `replace_proto_semitic = true` and verify the output phone rows have the
   expected realization codes.

2. **`test_replace_proto_semitic_ophone`**: Same as above but verify the
   `_ophone.txt` stream also has the replacement applied.

3. **`test_replace_proto_semitic_printer_ipa`**: Run the printer on the
   replaced phone rows and verify the IPA output reflects the replacement
   (e.g., `ḥ` -> `ʔ` instead of `ħ`).

## Test Fixtures

All tests must be self-sufficient: use hardcoded inputs or fixtures under
`tests/`. Do not rely on `demo/`, `outputs/`, or `tmp/`.

---

# Rollback Plan

Set `phonetize.realization.replace_proto_semitic = false` (the default) to
restore the current behavior. No code changes needed for rollback.

---

# Related Issues

- REQ-049: [Requirement: Phonetizer Proto-Semitic Pharyngeal/Glottal Replacement](../req/049-phonetizer-proto-semitic-replacement.md)
- Printer IPA proto-Semitic: `src/akkapros/lib/print.py` lines 89-104
- Printer CLI: `src/akkapros/cli/printer.py` line with `--ipa-proto-semitic`

---

# Tasks

## Implementation

- [x] Add `replace_proto_semitic` field to `PHONETIZE_SCHEMA['process']['realization']`
      in `_phonetize_config.py`
- [x] Add `allow_experimental` guard in `verify_phonetize_config()` in
      `_phonetize_config.py` — read `replace_proto_semitic` from
      `raw_config['process']['realization']` and add a failure when
      `allow_experimental` is `false` and `replace_proto_semitic` is `true`
- [x] Update the `allow_experimental` comment in `src/akkapros/config/default.yaml`
      to list `replace_proto_semitic` among the guarded features
- [x] Add `_resolve_realization()` helper in `phonetize.py`
- [x] Modify `_new_segment_seed()` to accept and use the flag
- [x] Thread the flag from `build_phone_rows()` through to row-building calls

## Tests

- [x] Unit tests for replacement logic
- [x] Integration tests for full pipeline
- [x] Test fixtures are self-sufficient and reserved to `tests/`

## Documentation

- [x] Update `docs/akkapros/phonetizer-algorithm.md` — add section describing
      the new config option and its effect on realizations (added subsection
      "Proto-Semitic Pharyngeal/Glottal Replacement" under Phase 1)
- [x] Update `docs/akkapros/phonetizer-data-model.md` — add note in the
      Input-to-Realization Associations section about the conditional mapping

## Review

- [x] Code review
- [x] Verify acceptance criteria
- [x] Run full test suite: `python -m pytest`

---

# Implementation Blockers

None known.

---

# Notes

## Printer IPA Mapping Reference

The printer's current IPA mapping for reference (will be removed in CR-100):

```python
IPA_MAP_STRICT = {
    ...
    'ḥ': 'ħ', 'ḫ': 'χ', 'ʿ': 'ʕ', 'ʾ': 'ʔ',
    ...
}
IPA_MAP_OB = {
    ...
    'ḥ': 'ʔ', 'ḫ': 'χ', 'ʿ': 'ʔ', 'ʾ': 'ʔ',
    ...
}
```

After this CR is implemented, the phonetizer output will already contain the
correct realization codes, so the printer can use a single IPA mapping that
directly translates realization codes to IPA symbols without a separate
preserve/replace branch.

## Realization Code Inventory (from phonetizer-data-model.md)

| Code | IPA | MBROLA/X-SAMPA | Category | Type | Emphaticity |
|------|-----|----------------|----------|------|-------------|
| `ET` | `ħ` | `X` | `C` | `F` | `P` |
| `HE` | `x` | `x` | `C` | `F` | `P` |
| `AI` | `ʕ` | `H` | `C` | `F` | `P` |
| `AL` | `ʔ` | `?` | `C` | `C` | `P` |

When `replace_proto_semitic = true`, `ETE` and `AIN` labels produce `AL` code
instead of `ET` and `AI` respectively. The IPA and MBROLA values follow from
the code.

# Revision History

- 2026-05-08: Initial draft
- 2026-05-08: Marked as experimental (guarded by allow_experimental), added
  verification guard, expanded Files/Tasks, referenced CR-100
- 2026-05-08: Implemented and verified. All AC satisfied. Status set to Done.
