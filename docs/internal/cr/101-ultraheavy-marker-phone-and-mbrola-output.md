---
cr_id: CR-101
status: Done
priority: Medium
impact: Additive
created: 2026-05-09
updated: 2026-05-09
implements: 'REQ-050'
---

# Change Request: Ultraheavy Marker Phone and MBROLA Output

# Summary

Add a configurable `ultraheavy_hiatus_enable` option to the phonetizer realization
layer. When enabled, circumflex vowels (`â`, `ê`, `î`, `û`) are expanded from
a single long-vowel segment into three segments (vowel + transition + vowel)
in dedicated output files `<prefix>_yphone.txt` and `<prefix>_ymbrola.pho`,
produced alongside the standard `<prefix>_phone.txt` and `<prefix>_mbrola.pho`.

This is an experimental feature gated behind
`phonetize.process.allow_experimental = true`.

---

# Motivation

- The printer's `--circ-hiatus` option splits circumflex vowels into hiatus
  in IPA output only, without affecting the phone-row timing model, MBROLA
  export, or metrics computation
- Researchers need a phonetizer-level expansion that produces independent
  phone and MBROLA artifacts with proper timing (vowel + transition + vowel)
  and intonation propagation
- The feature is experimental and must be gated behind
  `phonetize.process.allow_experimental = true`

---

# Scope

## Included

- New config key `phonetize.process.realization.ultraheavy_hiatus_enable` (bool, default false)
- Experimental guard in `_phonetize_config.py` verification
- New function to expand circumflex vowel rows into three rows (vowel + transition + vowel)
- New output files `<prefix>_yphone.txt` and `<prefix>_ymbrola.pho`
- Timing: split original duration Z into U1 + T + U2 where T = vowel_transition (taken from config file `...sonorant.special_realization.vowel_transition`)
- Intonation: preserve original contour across the three segments, same start, same end, constant on the vowel transition, linear on the U1 and U2)
- Front matter propagation of the option activation
- Unit tests and integration tests
- Documentation updates (`docs/akkapros/phonetizer-algorithm.md`)
- Help message updates (`src/akkapros/lib/helpmsg.py`)
- Demo YAML config updates (`demo/akkapros/`)
- Test config updates (`tests/`)

## Not Included

- No changes to the standard `<prefix>_phone.txt` or `<prefix>_mbrola.pho` output
- No changes to the printer's `--circ-hiatus` behavior
- No metrics computation for the ultraheavy files
- No changes to the prosody or syllabify stages

---

# Current Behavior

The phonetizer processes circumflex vowels (`â`, `ê`, `î`, `û`) as single
long-vowel segments with label `AWI`/`EWI`/`IWI`/`UWI`, length `L`, and
realization code `AA`/`EE`/`II`/`UU` (plain) or `AO`/`EO`/`IO`/`UO`
(emphatic). They are output in the standard `<prefix>_phone.txt` and
`<prefix>_mbrola.pho` files as single rows with a single duration and
intonation contour.

The printer's `--circ-hiatus` option splits these vowels in IPA output only
(e.g., `qû → qʊ.ʊ`), but this is a printer-level text transformation that
does not affect the phone-row structure, timing, or MBROLA export.

---

# Proposed Change

## 1. New config key

Add `ultraheavy_hiatus_enable` to the `realization` block in
`src/akkapros/config/default.yaml`:

```yaml
realization:
  ultraheavy_hiatus_enable: false
  # ... existing keys ...
```

Add the corresponding field definition in `_phonetize_config.py`:

```python
'ultraheavy_hiatus_enable': _field(False, 'bool', 'Expand circumflex vowels into vowel+transition+vowel in yphone/ymbrola output.'),
```

## 2. Experimental guard

In `_phonetize_config.py` `verify_phonetize_config()`, add:

```python
if ultraheavy_hiatus_enable and not allow_experimental:
    add_failure(
        'phonetize.process.allow_experimental',
        'allow_experimental must be true when ultraheavy_hiatus_enable is true',
        'Experimental feature ultraheavy_hiatus_enable: true (expand circumflex vowels) is enabled but allow_experimental is false. Set phonetize.process.allow_experimental to true to enable experimental features.',
    )
```

## 3. Ultraheavy expansion function

Add a new function in `phonetize.py` (or a new `_phonetize_ultraheavy.py`
module) that:

1. Takes the fully realized phone rows (after Phase 2 durations and Phase 3
   intonation are assigned)
2. Identifies rows where the original input symbol is a circumflex vowel
   (`â`, `ê`, `î`, `û`) — these have labels `AWI`, `EWI`, `IWI`, `UWI`
3. For each such row, replaces it with three rows:

   **Row 1 (first vowel):**
   - Same label, category `V`, type from vowel height, length `S` (short)
   - Same boundary, accent, text as original
   - Realization: same as original (e.g., `AA` or `AO`)
   - Duration: U1 = floor(0.5 * (Z - T))
   - Intonation: start_freq = original_start, end_freq = floor(midpoint)

   **Row 2 (transition):**
   - Label: `ENA` (transition), category `C`, type `T`, length `S`
   - Boundary: `I` (internal), accent: `F` (none)
   - Realization: determined by vowel quality:
     - `AA`/`AO` → `AL` (glottal stop `ʔ`)
     - `UU`/`UO` → `WA` (labiovelar glide `w`)
     - `EE`/`II`/`EO`/`IO` → `YI` (palatal glide `j`)
   - Duration: T = `vowel_transition` (from config file `...sonorant.special_realization.vowel_transition`)
   - Intonation: constant frequency at midpoint value
   - Text: empty string

   **Row 3 (second vowel):**
   - Same label, category `V`, type from vowel height, length `S` (short)
   - Boundary: same as original, accent: `F` (none)
   - Realization: same as original
   - Duration: U2 = ceiling(0.5 * (Z - T))
   - Intonation: start_freq = ceiling(midpoint), end_freq = original_end
   - Text: empty string

### Transition realization mapping

| Original realization | Transition realization | IPA | MBROLA X-SAMPA |
|---|---|---|---|
| `AA` (a) | `AL` | `ʔ` | `?` |
| `AO` (ɑ) | `AL` | `ʔ` | `?` |
| `UU` (u) | `WA` | `w` | `w` |
| `UO` (ʊ) | `WA` | `w` | `w` |
| `EE` (e) | `YI` | `j` | `j` |
| `II` (i) | `YI` | `j` | `j` |
| `EO` (ɛ) | `YI` | `j` | `j` |
| `IO` (ɨ) | `YI` | `j` | `j` |

### Timing formula

```
Z = original duration in ms
T = vowel_transition (from config, default 25 ms)
U1 = floor(0.5 * (Z - T))
U2 = ceiling(0.5 * (Z - T))
```

If `Z - T` is negative or zero, the expansion should not be applied (the
original row is kept as-is).

### Intonation formula

Original intonation token: `[HLMRFPV][0-9][CLE]` with start frequency F1
and end frequency F2 (derived from the token's contour type).

```
mid_freq = F1 + (F2 - F1) * (U1 / Z)
```

- Row 1: linear rise from F1 to mid_freq over U1 ms
- Row 2: constant mid_freq over T ms
- Row 3: linear rise from mid_freq to F2 over U2 ms

Use floor/ceiling to avoid decimal frequencies.

## 4. Output file generation

After the standard `<prefix>_phone.txt` and `<prefix>_mbrola.pho` are
produced, if `ultraheavy_hiatus_enable = true`:

1. Copy the fully realized phone rows
2. Apply the ultraheavy expansion to the copy
3. Serialize the expanded rows to `<prefix>_yphone.txt` (same format as
   `_phone.txt`)
4. Generate MBROLA output from the expanded rows to `<prefix>_ymbrola.pho`
   (same format as `_mbrola.pho`)

The `y` files are independent: they incorporate all previous realization
options (mora_mode, replace_proto_semitic, limit_emphatic_coloring, etc.)
because the expansion operates on the already-realized rows.

## 5. Front matter propagation

Add `ultraheavy_hiatus_enable: true` to the front matter of the `_yphone.txt` and
`_ymbrola.pho` files so downstream consumers can detect that ultraheavy
expansion was applied.

## 6. Help messages

Add to `src/akkapros/lib/helpmsg.py`:

```python
"phonetize.process.realization.ultraheavy_hiatus_enable": "Experimental: expand circumflex vowels into vowel+transition+vowel in yphone/ymbrola output (requires allow_experimental=true).",
```

## 7. Demo YAML configs

Add `ultraheavy_hiatus_enable: true` to the relevant demo configs in
`demo/akkapros/` to exercise the feature.

## 8. Test config updates

Add `ultraheavy_hiatus_enable: true` to the relevant test configs in
`tests/` (e.g., `tests/integration_refs/regression_defaults.yaml` or
dedicated test fixtures) to exercise the feature in the test suite.

---

# Technical Design

## Architecture

The ultraheavy expansion is a post-processing step applied after the standard
phone rows are fully realized (Phase 2 durations + Phase 3 intonation). It
operates on a copy of the rows so the standard output is unaffected.

### Flow

```
realize_phone_rows() → standard rows
  ├─ serialize → _phone.txt
  ├─ serialize → _mbrola.pho
  └─ if ultraheavy_hiatus_enable:
       copy rows
       expand circumflex rows in copy
       serialize → _yphone.txt
       serialize → _ymbrola.pho
```

### New function: `_expand_ultraheavy_rows()`

```python
def _expand_ultraheavy_rows(
    rows: list[dict[str, str]],
    vowel_transition_duration: int,
) -> list[dict[str, str]]:
    """Expand circumflex vowel rows into vowel+transition+vowel triplets.

    Args:
        rows: Fully realized phone rows (after Phase 2 and Phase 3).
        vowel_transition_duration: Duration of the transition segment in ms
            (from config: durations.consonants.sonorant.special_realization.vowel_transition).

    Returns:
        New list of rows with circumflex vowels expanded.
    """
```

### Circumflex vowel detection

A circumflex vowel row is identified by its label being in `{'AWI', 'EWI', 'IWI', 'UWI'}`.
These correspond to the input characters `â`, `ê`, `î`, `û`.

### Transition realization selection

```python
def _choose_ultraheavy_transition(realization_code: str) -> str:
    """Choose the transition realization for an ultraheavy expansion.

    Args:
        realization_code: The realization code of the circumflex vowel
            (e.g., 'AA', 'AO', 'UU', 'UO', 'EE', 'II', 'EO', 'IO').

    Returns:
        The transition realization code ('AL', 'WA', or 'YI').
    """
    if realization_code in {'AA', 'AO'}:
        return 'AL'
    if realization_code in {'UU', 'UO'}:
        return 'WA'
    if realization_code in {'EE', 'II', 'EO', 'IO'}:
        return 'YI'
    return 'AL'  # fallback
```

---

# Files Likely Affected

- `src/akkapros/config/default.yaml` — add `ultraheavy_hiatus_enable: false`
- `src/akkapros/lib/_phonetize_config.py` — add field definition, experimental guard
- `src/akkapros/lib/phonetize.py` — add expansion function, integrate into output pipeline
- `src/akkapros/lib/helpmsg.py` — add help text
- `src/akkapros/lib/tests/phonetize_tests.py` — add unit tests
- `tests/` — add integration tests
- `tests/integration_refs/` — update test configs (e.g., `regression_defaults.yaml`)
- `docs/akkapros/phonetizer-algorithm.md` — document the feature
- `demo/akkapros/*.yaml` — add `ultraheavy_hiatus_enable: true` to relevant configs

---

# Acceptance Criteria

- [x] `ultraheavy_hiatus_enable = false` (default): no change in behavior, no `_y*` files produced
- [x] `ultraheavy_hiatus_enable = true` + `allow_experimental = true`: `_yphone.txt` and
      `_ymbrola.pho` are produced alongside standard files
- [x] `ultraheavy_hiatus_enable = true` + `allow_experimental = false`: verification error raised
- [x] Each circumflex vowel in input produces exactly 3 rows in `_yphone.txt`
- [x] Non-circumflex vowels and consonants are unchanged in `_yphone.txt`
- [x] Timing: U1 + T + U2 = Z (original duration), with U1 = floor, U2 = ceiling
- [x] Intonation: frequency contour preserved across the three segments
- [x] Transition realization follows the mapping table
- [x] `_yphone.txt` and `_ymbrola.pho` incorporate mora_mode, replace_proto_semitic,
      limit_emphatic_coloring settings
- [x] Front matter of `_yphone.txt` and `_ymbrola.pho` includes `ultraheavy_hiatus_enable: true`
- [x] Help message is accurate
- [x] Demo YAML configs are updated
- [x] Test configs are updated
- [x] Unit tests pass
- [x] Integration tests pass

---

# Risks / Edge Cases

- **Zero or negative split**: If Z ≤ T, the expansion should not be applied
  (the original row is kept as-is)
- **Accentuated circumflex vowels**: The accent mark (`~`) should be preserved
  on the first vowel segment of the expansion
- **Emphatic coloring**: Emphatic realizations (`AO`, `EO`, `IO`, `UO`) must
  be preserved in both vowel segments
- **Boundary codes**: The last segment should inherit the original boundary
  code; internal boundaries should be `I`
- **Text field**: Only the first segment should carry the original text;
  transition and second segment should have empty text
- **Drift field**: The drift of the original row should be distributed or
  assigned to the first segment; transition and second segment get neutral drift
- **Pause rows**: Pause rows are unaffected by the expansion
- **Resync pause rows**: Resync pause rows are unaffected

---

# Testing Strategy

## Unit tests (in `src/akkapros/lib/tests/phonetize_tests.py`)

- `_expand_ultraheavy_rows` with no circumflex vowels → rows unchanged
- `_expand_ultraheavy_rows` with one circumflex vowel → 3 rows produced
- `_expand_ultraheavy_rows` with multiple circumflex vowels → each expanded
- `_expand_ultraheavy_rows` with Z ≤ T → row kept as-is
- `_choose_ultraheavy_transition` for each realization code
- Timing calculation: U1 + T + U2 = Z
- Intonation calculation: frequencies match original contour
  - Rising intonation (R token): verify linear rise across U1 + T + U2
  - Constant intonation (H token): verify constant frequency across all three segments
- Accentuated circumflex vowel: accent preserved on first segment
- Emphatic realization: both vowel segments use emphatic code

## Integration tests (in `tests/`)

- Run full phonetizer pipeline with `ultraheavy_hiatus_enable = true` on a sample
  containing circumflex vowels
- Verify `_yphone.txt` and `_ymbrola.pho` are produced
- Verify `_yphone.txt` has correct row count (original + 2 per circumflex vowel)
- Verify `_ymbrola.pho` has correct symbol/duration/intonation lines
- Verify standard `_phone.txt` and `_mbrola.pho` are unchanged

## Manual verification

- Run on a real Akkadian text containing `qû`, `lâ`, `šî`, `bê` etc.
- Inspect the `_yphone.txt` rows for correct structure
- Inspect the `_ymbrola.pho` for correct MBROLA format

---

# Rollback Plan

Revert all changes:

1. Remove `ultraheavy_hiatus_enable` from `default.yaml`
2. Remove field definition and guard from `_phonetize_config.py`
3. Remove expansion function and output integration from `phonetize.py`
4. Remove help text from `helpmsg.py`
5. Revert test changes
6. Revert documentation changes
7. Revert demo YAML changes

---

# Related Issues

- Printer `--circ-hiatus` option (conceptual parallel)
- REQ-050 (this CR implements it)

---

# Tasks

## Implementation

- [x] Add `ultraheavy_hiatus_enable` field to `_phonetize_config.py`
- [x] Add experimental guard in `verify_phonetize_config()`
- [x] Add `_choose_ultraheavy_transition()` function
- [x] Add `_expand_ultraheavy_rows()` function
- [x] Integrate expansion into the phonetizer output pipeline
- [x] Add front matter propagation
- [x] Add config key to `default.yaml`
- [x] Add help text to `helpmsg.py`

## Tests

- [x] Unit tests for `_expand_ultraheavy_rows()`
- [x] Unit tests for `_choose_ultraheavy_transition()`
- [x] Unit tests for timing and intonation calculation
- [x] Unit tests for rising intonation (R token) across the three segments
- [x] Unit tests for constant intonation (H token) across the three segments
- [x] Integration tests for full pipeline with `ultraheavy_hiatus_enable = true`
- [x] Test fixtures and configs are self-sufficient and reserved to `tests/`
- [x] Test configs updated with `ultraheavy_hiatus_enable` parameter

## Documentation

- [x] Update `docs/akkapros/phonetizer-algorithm.md`
- [x] Update demo YAML configs in `demo/akkapros/`

## Review

- [x] Code review
- [x] Verify acceptance criteria

---

# Implementation Blockers

No blockers known.

---

# Notes

## Design rationale

The `y` prefix was chosen to distinguish ultraheavy files from standard files
without conflicting with existing suffixes (`_phone.txt`, `_mbrola.pho`).
The letter `y` stands for "ultraheavy" (circumflex → ultraheavy).

The expansion is applied after all other realization options so that
`mora_mode`, `replace_proto_semitic`, `limit_emphatic_coloring`, etc. are
already resolved in the source rows. This ensures the `_y*` files are
consistent with the standard output.

## Example

Input: `qû`

Standard phone row for `û`:
```
label=UWI, category=V, type=H, length=L, position=P, boundary=F, accent=F, realization=UU, duration=0180, drift=+000, intonation=R1C, text=û
```

Ultraheavy expansion (3 rows):
```
label=UWI, category=V, type=H, length=S, position=P, boundary=I, accent=F, realization=UU, duration=0077, drift=+000, intonation=R1C, text=û
label=ENA, category=C, type=T, length=S, position=P, boundary=I, accent=F, realization=WA, duration=0025, drift=+000, intonation=M0C, text=
label=UWI, category=V, type=H, length=S, position=P, boundary=F, accent=F, realization=UU, duration=0078, drift=+000, intonation=R1C, text=
```

Where:
- Z = 180 ms, T = 25 ms
- U1 = floor(0.5 * (180 - 25)) = floor(77.5) = 77
- U2 = ceiling(0.5 * (180 - 25)) = 78
- Original intonation R1C (rising): start 120 Hz, end 135 Hz
- mid_freq = 120 + (135 - 120) * (77 / 180) = 120 + 15 * 0.428 = 126.42 → 126
- Row 1: R1C from 120 to 126 over 77 ms
- Row 2: M0C constant at 126 over 25 ms
- Row 3: R1C from 126 to 135 over 78 ms
