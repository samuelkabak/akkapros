---
cr_id: CR-068
status: Done
priority: High
impact: Mutative
created: 2026-04-17
updated: 2026-04-18
implements: REQ-022, REQ-027, REQ-031
---

# Change Request: Ratio Based Parameters

## Summary

The phonetizer timing defaults currently reflect the retuned surface approved in
CR-067, with `cvc_reference = 306` and the corresponding closure, fricative,
and sonorant timing rows exposed through the shared config schema, confwriter,
and repository YAML examples.

This CR updates those default values to a new ratio-based parameter set centered
on `cvc_reference = 300` and a revised consonant timing table. The change is a
default-value retune only: it does not rename config keys, change the accepted
schema structure, or alter the active legality relations already documented in
REQ-027 and REQ-031.

Some listed values are intentionally unchanged and are restated in the new table
to avoid ambiguity about the complete intended default row.

This CR updates the defaults most recently set by CR-067 where the two records
overlap. CR-067 remains the historical source for the schema names and timing
surface shape, but CR-068 becomes the active default-value contract for the
phonetizer timing table.

---

## Motivation

Why is this change needed?

- Timing-parameter retune
- Config default clarification
- Confwriter default clarification
- YAML-surface synchronization

The repository currently exposes one coherent phonetizer timing table across the
runtime defaults, emitted config comments, and tracked YAML examples. When the
intended default ratios change, those surfaces must be updated together so users
do not see conflicting default values across `default.yaml`, `confwriter`, and
demo configs.

The requested change is not a schema redesign. It is a coordinated retune of
default values that must land consistently across all tracked YAML files and all
generated or emitted config-help surfaces to avoid users inferring stale ratios
from older defaults.

---

## Scope

## Included

- Change the active default `phonetize.timing_model.durations.cvc_reference`
  from `306` to `300`
- Change the active default closure timing row to:
  `onset = 89`, `coda = 87`, `geminate = 155`,
  `special_realization.hiatus = 18`,
  `perception_limits.geminate_min = 130`, and
  `perception_limits.gemination_max = 220`
- Change the active default fricative timing row to:
  `onset = 102`, `coda = 100`, `geminate = 180`,
  `perception_limits.geminate_min = 150`, and
  `perception_limits.gemination_max = 250`
- Change the active default sonorant timing row to:
  `onset = 92`, `coda = 90`, `geminate = 162`,
  `special_realization.vowel_transition = 11`,
  `perception_limits.geminate_min = 135`, and
  `perception_limits.gemination_max = 250`
- Treat the repeated unchanged values `closure.special_realization.hiatus = 18`,
  `fricative.perception_limits.gemination_max = 250`, and
  `sonorant.special_realization.vowel_transition = 11` as part of the normative
  replacement default table rather than as implied carryover only
- Update the canonical config default file at
  `src/akkapros/config/default.yaml`
- Update the confwriter-emitted default/help surface so generated config files
  and schema-backed key inspection expose the same new defaults
- Update all tracked project YAML files, which at the time of this CR are:
  `src/akkapros/config/default.yaml`,
  `demo/akkapros/lexlinks/construct-demo.yaml`, and
  `demo/akkapros/prosmaker/corpus-demo.yaml`
- Update any affected internal or user-facing config documentation that lists
  these defaults explicitly
- Update or add verification coverage that pins the new default values in the
  shared config surface and the phonetizer runtime defaults

## Not Included

- Renaming any phonetizer config keys
- Changing `segmental_ceiling`, `segmental_floor`, vowel defaults, or pause-band
  defaults unless a later approved record explicitly requires that
- Changing the accepted semantic invariant formulas in REQ-027
- Changing the active Phase 2 duration algorithm beyond what necessarily follows
  from the new numeric defaults
- Adding new tracked YAML files beyond the three currently present in the
  repository

---

## Current Behavior

The repository currently exposes these phonetizer timing defaults in
`src/akkapros/config/default.yaml`:

- `cvc_reference = 306`
- `consonants.closure.onset = 108`
- `consonants.closure.coda = 103`
- `consonants.closure.geminate = 195`
- `consonants.closure.special_realization.hiatus = 18`
- `consonants.closure.perception_limits.geminate_min = 180`
- `consonants.closure.perception_limits.gemination_max = 221`
- `consonants.fricative.onset = 137`
- `consonants.fricative.coda = 142`
- `consonants.fricative.geminate = 224`
- `consonants.fricative.perception_limits.geminate_min = 210`
- `consonants.fricative.perception_limits.gemination_max = 250`
- `consonants.sonorant.onset = 89`
- `consonants.sonorant.coda = 70`
- `consonants.sonorant.geminate = 163`
- `consonants.sonorant.special_realization.vowel_transition = 11`
- `consonants.sonorant.perception_limits.geminate_min = 152`
- `consonants.sonorant.perception_limits.gemination_max = 182`

The same default family is expected to remain synchronized across the canonical
config file, confwriter output, and the two tracked demo YAML files, because
REQ-022 treats those surfaces as one shared config contract.

The current active contract for the schema names and legality bands comes from
REQ-022, REQ-027, REQ-031, and CR-067. Those records currently assume the newer
schema names `gemination_max` and `elongation_max`, but they do not yet encode
the ratio-based default table requested here.

---

## Proposed Change

The phonetizer shall adopt the following replacement default timing table for
the shared config surface:

```yaml
cvc_reference: 300
consonants:
  closure:
    onset: 89
    coda: 87
    geminate: 175
    special_realization:
      hiatus: 35
    perception_limits:
      geminate_min: 145
      gemination_max: 260
  fricative:
    onset: 115
    coda: 112
    geminate: 210
    perception_limits:
      geminate_min: 163
      gemination_max: 290
  sonorant:
    onset: 105
    coda: 100
    geminate: 190
    special_realization:
      vowel_transition: 25
    perception_limits:
      geminate_min: 148
      gemination_max: 275
```

Normative rules:

- The table above replaces the current phonetizer default row wherever these
  defaults are materialized or emitted.
- The repeated unchanged values in the requested table remain explicitly present
  in documentation and YAML output so users can read the full intended ratio set
  from one place without inferring omitted carryover.
- The config schema structure and key names introduced by earlier accepted
  records remain unchanged.
- Shared verification and confwriter must treat these new numbers as the active
  documented defaults for warning comparisons, emitted help, and generated YAML.
- All tracked YAML files in the repository must expose the same new defaults
  after the change.

---

## Technical Design

Implementation shape:

- update the canonical phonetizer default values in the shared config source of
  truth used to materialize `default.yaml` and runtime defaults
- update confwriter default emission and help-text pathways that surface current
  default values for phonetizer timing keys
- update all tracked repository YAML examples so they stay aligned with the new
  canonical defaults
- update any tests that pin the previous default numbers so they now verify the
  ratio-based set
- update public and internal config documentation wherever these default values
  are listed explicitly

Design constraints:

- keep `gemination_max`, `elongation_max`, `segmental_ceiling`, and
  `segmental_floor` naming unchanged
- preserve the current semantic invariant structure from REQ-027 unless a value
  in the new table would violate that structure; if any invariant would fail,
  implementation must stop and raise a follow-up spec issue rather than silently
  weakening the invariant contract
- keep the YAML inventory scope exact and synchronized with the repository as of
  this CR

---

## Files Likely Affected

src/akkapros/config/default.yaml
src/akkapros/lib/phonetize.py
demo/akkapros/lexlinks/construct-demo.yaml
demo/akkapros/prosmaker/corpus-demo.yaml
tests/test_config_support.py
tests/test_phonetize_lib.py
docs/akkapros/configuration.md
docs/akkapros/confwriter.md
docs/akkapros/phonetizer.md
docs/internal/req/022-package-wide-yaml-config-and-confwriter.md
docs/internal/req/027-phonetize-config-semantic-invariants-for-shared-verification.md
docs/internal/req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md

---

## Acceptance Criteria

- [x] `phonetize.timing_model.durations.cvc_reference` defaults to `300`
- [x] The default closure row becomes `onset = 89 / coda = 87 / geminate = 175` with `hiatus = 35`, `geminate_min = 145`, and `gemination_max = 260`
- [x] The default fricative row becomes `onset = 115 / coda = 112 / geminate = 210` with `geminate_min = 163` and `gemination_max = 290`
- [x] The default sonorant row becomes `onset = 105 / coda = 100 / geminate = 190` with `vowel_transition = 25`, `geminate_min = 148`, and `gemination_max = 275`
- [x] `src/akkapros/config/default.yaml` documents the new default table
- [x] `confwriter` emits and reports these same defaults for the affected keys
- [x] The tracked demo YAML files at `demo/akkapros/lexlinks/construct-demo.yaml` and `demo/akkapros/prosmaker/corpus-demo.yaml` expose the same new defaults
- [x] No tracked project YAML file retains the superseded default values for these keys after the change
- [x] Runtime default resolution used by phonetizer tests reflects the new values without changing the approved key names
- [x] Config-facing docs that enumerate these values are updated in the same implementation slice
- [x] Verification coverage is updated so the new default values are pinned in config and phonetizer tests

---

## Risks / Edge Cases

Possible issues:

- The new ratio-based values may interact with existing semantic invariant
  checks in REQ-027; implementation must verify that all ordering relations
  still hold
- A partial update could leave `default.yaml`, confwriter output, and demo YAMLs
  inconsistent even if runtime defaults change correctly
- Existing docs or tests may still embed old numeric literals from CR-067 and
  would become stale if not updated together
- Because some values are intentionally unchanged, implementers could overlook
  them and omit them from emitted documentation instead of treating the full
  table as the active normative default set

---

## Testing Strategy

Unit tests:

- verify runtime phonetizer defaults expose the new `cvc_reference` and
  consonant timing values
- verify config-support helpers and shared default-resolution paths expose the
  same values
- verify confwriter default generation or key listing reflects the new defaults

Integration tests:

- verify config-driven runs consume the updated defaults without schema-name
  regressions
- verify tracked YAML examples remain loadable after the default retune

Manual tests:

- inspect `src/akkapros/config/default.yaml` and confirm the full ratio-based
  table is present
- inspect the two tracked demo YAML files and confirm they match the canonical
  default table for the affected keys
- inspect confwriter output or `--list` / `--get` surfaces and confirm the same
  defaults are reported there

---

## Rollback Plan

Restore the superseded CR-067 default numbers for `cvc_reference` and the three
consonant timing rows across the shared runtime defaults, `default.yaml`,
confwriter output, tracked demo YAML files, tests, and config documentation.

---

## Related Issues

- [CR-067](067-cap-adjacent-short-vowel-accent-spill-below-long-min.md)
- [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)
- [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)

---

## Tasks

## Implementation

- [ ] Update the canonical phonetizer default values to the ratio-based table
- [ ] Update `default.yaml` and all tracked demo YAML files
- [ ] Update confwriter default emission and help surfaces for the affected keys
- [ ] Update any runtime default consumers that embed the superseded values

## Tests

- [ ] Update config and phonetizer tests that pin the affected default values
- [ ] Add or refresh coverage that checks confwriter and tracked YAML alignment

## Documentation

- [ ] Update config-facing docs that enumerate these defaults
- [ ] Update any internal requirement or contract text that cites the older
  numeric defaults explicitly

## Review

- [ ] Verify the new defaults still satisfy the active REQ-027 invariants
- [ ] Verify all three tracked YAML files match the canonical default table
- [ ] Verify acceptance criteria

---

## Implementation Blockers

None currently.

---

## Notes

- This CR is intentionally limited to the requested default-value retune.
- Implementation was verified as present in the repository on 2026-04-18 and
  the CR status was updated to `Done`.
