---
cr_id: CR-100
status: Done
priority: Medium
impact: Mutative
created: 2026-05-08
updated: 2026-05-08
implements: ''
---

# Change Request: Remove Printer `--ipa-proto-semitic` Option

# Summary

Remove the `--ipa-proto-semitic` option from the printer CLI and its
associated code paths in `print.py`, `printer.py`, and `fullprosmaker.py`.
After CR-099 implements `phonetize.realization.replace_proto_semitic`, the
phonetizer output already contains the correct realization codes, so the
printer no longer needs its own IPA-level preserve/replace mapping. The
printer inherits the replacement from the phone rows and uses a single IPA
mapping that directly translates realization codes to IPA symbols.

---

# Motivation

CR-099 moves the proto-Semitic pharyngeal/glottal replacement from the
printer's text-level IPA mapping into the phonetizer's realization layer.
Once CR-099 is implemented and verified, the printer's `--ipa-proto-semitic`
option becomes redundant because:

1. The phonetizer output already contains the correct realization codes
   (`AL` for merged pharyngeals/glottals, `HE` for ḫ).
2. The printer's IPA mapping no longer needs a preserve/replace branch — it
   can use a single mapping from realization codes to IPA symbols.
3. All downstream consumers (IPA, MBROLA, XAR, acute, bold) consistently
   reflect the chosen policy from the phonetizer.

Removing the printer option eliminates a duplicate code path and prevents
confusion when the printer and phonetizer are configured with conflicting
proto-Semitic policies.

---

# Scope

## Included

- Remove `--ipa-proto-semitic` CLI argument from `src/akkapros/cli/printer.py`
- Remove `ipa_proto_semitic` from `print.process` schema in
  `src/akkapros/lib/print.py`
- Remove `IPA_MAP_STRICT` dictionary from `src/akkapros/lib/print.py`
- Rename `IPA_MAP_OB` to `IPA_MAP` (or inline it) in `src/akkapros/lib/print.py`
  since there is now only one IPA mapping
- Remove `ipa_proto_semitic` parameter from all internal functions in
  `print.py` that accept it (`convert_line`, `convert_text`, `convert_lines`,
  `render`, `render_phone_rows`, etc.)
- Remove `--print-ipa-proto-semitic` option from `src/akkapros/cli/fullprosmaker.py`
- Remove `ipa_proto_semitic` from `print.process` section in
  `src/akkapros/config/default.yaml`
- Remove `ipa_proto_semitic` help entries from `src/akkapros/lib/helpmsg.py`
- Update `docs/akkapros/printer.md` to remove the `--ipa-proto-semitic` option
  documentation
- Update `docs/akkapros/phonetizer-algorithm.md` to note that the printer
  inherits the replacement from the phonetizer

## Not Included

- Changes to the phonetizer realization layer (already handled by CR-099)
- Changes to XAR output mapping (XAR already uses apostrophe convergence
  independently)
- Changes to emphatic vowel coloring logic

---

# Current Behavior

The printer accepts `--ipa-proto-semitic {preserve,replace}` (default:
`preserve`). When set to `replace`, the IPA mapping merges `ḥ`, `ʿ`, `ʾ` to
`ʔ` while keeping `ḫ` as `χ`. This mapping is implemented via two dictionaries:

```python
IPA_MAP_STRICT = {
    'b': 'b', 'd': 'd', 'g': 'g', 'k': 'k', 'p': 'p',
    'q': 'q', 'ṭ': 'tˤ', 'ṣ': 'sˤ', 'š': 'ʃ',
    's': 's', 'z': 'z', 'l': 'l', 'm': 'm', 'n': 'n',
    'r': 'r', 'ḥ': 'ħ', 'ḫ': 'χ', 'ʿ': 'ʕ', 'ʾ': 'ʔ',
    'w': 'w', 'y': 'j', 't': 't',
}
IPA_MAP_OB = {
    'b': 'b', 'd': 'd', 'g': 'g', 'k': 'k', 'p': 'p',
    'q': 'q', 'ṭ': 'tˤ', 'ṣ': 'sˤ', 'š': 'ʃ',
    's': 's', 'z': 'z', 'l': 'l', 'm': 'm', 'n': 'n',
    'r': 'r', 'ḥ': 'ʔ', 'ḫ': 'χ', 'ʿ': 'ʔ', 'ʾ': 'ʔ',
    'w': 'w', 'y': 'j', 't': 't',
}
```

The choice between them is selected by `ipa_mode == 'ipa-strict'` vs
`ipa_mode == 'ipa-ob'` in the IPA conversion path.

---

# Proposed Change

## Code Removal

### `src/akkapros/lib/print.py`

1. Remove `IPA_MAP_STRICT` dictionary entirely.
2. Rename `IPA_MAP_OB` to `IPA_MAP` (a single mapping that directly
   translates realization codes to IPA symbols). The mapping stays the same
   as the current `IPA_MAP_OB` because the phonetizer already handles the
   preserve/replace distinction.
3. Remove the `ipa_mode` parameter from all internal functions:
   - `convert_line()`
   - `convert_text()`
   - `convert_lines()`
   - `render()`
   - `render_phone_rows()`
   - `convert_text_with_ipa_xar()`
   - Any other function that accepts `ipa_mode`
4. Remove the `ipa_mode` branching logic: replace
   ```python
   ipa_map = IPA_MAP_STRICT if ipa_mode == 'ipa-strict' else IPA_MAP_OB
   ```
   with
   ```python
   ipa_map = IPA_MAP
   ```
5. Remove the `ipa_proto_semitic` field from the print config schema.

### `src/akkapros/cli/printer.py`

1. Remove the `--ipa-proto-semitic` argument definition.
2. Remove the code that reads the argument and passes it to the print
   functions.

### `src/akkapros/cli/fullprosmaker.py`

1. Remove the `--print-ipa-proto-semitic` option.
2. Remove the code that reads the option and passes it to the printer stage.

### `src/akkapros/config/default.yaml`

1. Remove the `ipa_proto_semitic` key from the `print.process` section.

### `src/akkapros/lib/helpmsg.py`

1. Remove the `printer.ipa_proto_semitic` and `print.ipa_proto_semitic` help
   entries.

## Documentation

### `docs/akkapros/printer.md`

1. Remove the `--ipa-proto-semitic` option from the CLI reference table.
2. Remove any prose describing the IPA proto-Semitic preserve/replace
   distinction.

### `docs/akkapros/phonetizer-algorithm.md`

1. Add a note that the printer inherits the proto-Semitic replacement from
   the phonetizer output and no longer has its own `--ipa-proto-semitic`
   option.

---

# Technical Design

## Components

1. **`src/akkapros/lib/print.py`**: Remove `IPA_MAP_STRICT`, rename
   `IPA_MAP_OB` to `IPA_MAP`, remove `ipa_mode` parameter from all functions,
   remove `ipa_proto_semitic` from config schema.

2. **`src/akkapros/cli/printer.py`**: Remove `--ipa-proto-semitic` CLI arg.

3. **`src/akkapros/cli/fullprosmaker.py`**: Remove `--print-ipa-proto-semitic`
   option.

4. **`src/akkapros/config/default.yaml`**: Remove `ipa_proto_semitic` key.

5. **`src/akkapros/lib/helpmsg.py`**: Remove help entries.

6. **`docs/akkapros/printer.md`**: Remove option documentation.

7. **`docs/akkapros/phonetizer-algorithm.md`**: Add note about printer
   inheritance.

## Data Flow After Removal

```
phonetizer output (phone rows with correct realization codes)
  -> printer reads phone rows
    -> IPA conversion uses single IPA_MAP (no preserve/replace branch)
    -> all outputs (IPA, MBROLA, XAR, acute, bold) consistent
```

---

# Files Likely Affected

```
src/akkapros/lib/print.py              — remove IPA_MAP_STRICT, ipa_mode param, ipa_proto_semitic schema
src/akkapros/cli/printer.py            — remove --ipa-proto-semitic arg
src/akkapros/cli/fullprosmaker.py      — remove --print-ipa-proto-semitic option
src/akkapros/config/default.yaml       — remove ipa_proto_semitic key
src/akkapros/lib/helpmsg.py            — remove help entries
docs/akkapros/printer.md               — remove option documentation
docs/akkapros/phonetizer-algorithm.md  — add inheritance note
```

---

# Acceptance Criteria

- [x] `--ipa-proto-semitic` is no longer accepted by the printer CLI.
- [x] `--print-ipa-proto-semitic` is no longer accepted by fullprosmaker.
- [x] `IPA_MAP_STRICT` is removed from `print.py`.
- [x] `IPA_MAP_OB` is renamed to `IPA_MAP` (single mapping).
- [x] No function in `print.py` accepts an `ipa_mode` parameter.
- [x] The `ipa_proto_semitic` key is removed from `default.yaml`.
- [x] Help entries for `ipa_proto_semitic` are removed from `helpmsg.py`.
- [x] Printer IPA output is identical to the previous `--ipa-proto-semitic=replace`
      behavior when the phonetizer has `replace_proto_semitic = true`.
- [x] Printer IPA output is identical to the previous `--ipa-proto-semitic=preserve`
      behavior when the phonetizer has `replace_proto_semitic = false`.
- [x] All existing tests pass (no regressions from parameter removal).
- [x] Documentation updated.

---

# Risks / Edge Cases

- The `ipa_mode` parameter may be used in test code. All test callers must be
  updated to remove the parameter.
- The `convert_text_with_ipa_xar()` function is used in self-tests within
  `print.py`. Those self-tests must be updated to remove `ipa_mode` arguments.
- The `IPA_MAP_OB` name is referenced in comments and documentation. All
  references must be updated to `IPA_MAP`.

---

# Testing Strategy

## Unit Tests

1. **`test_ipa_output_after_replacement`**: Verify that the printer produces
   correct IPA output when the phonetizer has `replace_proto_semitic = true`
   (e.g., `ḥ` -> `ʔ`).

2. **`test_ipa_output_without_replacement`**: Verify that the printer produces
   correct IPA output when the phonetizer has `replace_proto_semitic = false`
   (e.g., `ḥ` -> `ħ`).

3. **`test_no_ipa_mode_parameter`**: Verify that all printer functions no
   longer accept `ipa_mode`.

## Integration Tests

1. **`test_printer_cli_no_ipa_proto_semitic`**: Verify that the printer CLI
   rejects `--ipa-proto-semitic` with an appropriate error.

2. **`test_fullprosmaker_no_print_ipa_proto_semitic`**: Verify that
   fullprosmaker rejects `--print-ipa-proto-semitic`.

## Test Fixtures

All tests must be self-sufficient: use hardcoded inputs or fixtures under
`tests/`. Do not rely on `demo/`, `outputs/`, or `tmp/`.

---

# Rollback Plan

Restore the removed code from version control. The `--ipa-proto-semitic`
option and its associated code paths can be reinstated by reverting the
changes to the affected files.

---

# Related Issues

- CR-099: [Phonetizer Proto-Semitic Pharyngeal/Glottal Replacement](../cr/099-phonetizer-proto-semitic-replacement.md)
- REQ-049: [Requirement: Phonetizer Proto-Semitic Pharyngeal/Glottal Replacement](../req/049-phonetizer-proto-semitic-replacement.md)
- Printer IPA proto-Semitic: `src/akkapros/lib/print.py` lines 89-104

---

# Tasks

## Implementation

- [x] Remove `IPA_MAP_STRICT` from `print.py`
- [x] Rename `IPA_MAP_OB` to `IPA_MAP` in `print.py`
- [x] Remove `ipa_mode` parameter from all functions in `print.py`
- [x] Remove `ipa_proto_semitic` from print config schema in `print.py`
- [x] Remove `--ipa-proto-semitic` CLI arg from `printer.py`
- [x] Remove `--print-ipa-proto-semitic` option from `fullprosmaker.py`
- [x] Remove `ipa_proto_semitic` key from `default.yaml`
- [x] Remove help entries from `helpmsg.py`

## Tests

- [x] Update existing tests that use `ipa_mode` parameter
- [x] Add tests verifying IPA output correctness after removal
- [x] Add tests verifying CLI rejects removed options
- [x] Test fixtures are self-sufficient and reserved to `tests/`

## Documentation

- [x] Update `docs/akkapros/printer.md` — remove `--ipa-proto-semitic` option
- [x] Update `docs/akkapros/phonetizer-algorithm.md` — add inheritance note

## Review

- [x] Code review
- [x] Verify acceptance criteria
- [x] Run full test suite: `python -m pytest`

---

# Implementation Blockers

This CR MUST NOT be implemented before CR-099 is verified. The printer
`--ipa-proto-semitic` option must remain available until the phonetizer
replacement feature is confirmed working.

---

# Notes

## Migration Path

1. Implement and verify CR-099 (phonetizer replacement).
2. Implement and verify CR-100 (printer option removal).
3. Users who previously used `--ipa-proto-semitic=replace` should configure
   `phonetize.realization.replace_proto_semitic: true` instead.
4. Users who previously used `--ipa-proto-semitic=preserve` (default) need no
   configuration change — the default behavior is identical.

## Self-Test Impact

The `print.py` file contains inline self-tests that use `ipa_mode` and
`IPA_MAP_STRICT`/`IPA_MAP_OB`. These must be updated to use the single
`IPA_MAP` and remove the `ipa_mode` parameter.
