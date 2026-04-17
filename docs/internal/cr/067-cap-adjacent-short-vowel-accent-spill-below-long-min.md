---
cr_id: CR-067
status: Done
priority: High
impact: Mutative
created: 2026-04-17
updated: 2026-04-17
implements: ADR-046, REQ-022, REQ-027, REQ-031, REQ-035
---

# Change Request: Narrow Short-Vowel Spill and Adopt Class-Local Gemination Max Caps

## Summary

The live phonetizer solver currently has two linked timing-contract problems.

First, accent-distribution spill into an adjacent short vowel may rise all the
way to `phonetize.process.timing_model.durations.vowels.perception_limits.long_min`.
With the current defaults, that means an adjacent short vowel may be emitted at
`123 ms`, which is already the first value in the long-vowel field.

Second, consonant saturation logic still uses the global
`timing_model.durations.segmental_ceiling` instead of class-local maxima. That
keeps the solver from expressing separate hard upper bounds for closure,
fricative, and sonorant geminate-like outcomes, even though the config model
already separates those classes everywhere else.

Third, the timing config has no explicit cross-category floor parameter that can
validate all consonant and vowel minima through one shared lower bound. The new
`segmental_floor` parameter is needed for config, confwriter, and YAML-surface
clarity, but it is validation-only and must not become a runtime timing knob in
the solver.

This CR narrows the active solver contract so adjacent short-vowel spill must
stop at `long_min - 1`, it introduces class-local
`perception_limits.gemination_max` values that replace `segmental_ceiling` inside
the consonant-timing algorithm while keeping `segmental_ceiling` in the config
schema as a cross-parameter validation ceiling, and it adds
`segmental_floor = 10` immediately after `segmental_ceiling` in the timing
config as a shared validation floor for vowel and consonant minima.

This CR also requires the implementation to land with matching documentation
updates and focused unit-test coverage for both the short-vowel boundary and
the new class-local gemination-max behavior. All newly introduced or retuned
parameters in this CR must be documented explicitly rather than left implicit in
schema or code comments alone.

This CR narrows the active solver contract documented in CR-063 and aligns it
with the earlier phonetizer reasoning already recorded in CR-059, where the
short-vowel ceiling under `long_min = 123` was explicitly identified as
`122 ms`. It also updates the phonetizer timing-parameter contract inherited
from the earlier config and confwriter records so class-local gemination maxima,
not the global `segmental_ceiling`, govern consonant saturation inside the
solver.

---

## Motivation

Why is this change needed?

- Bug fix
- Contract clarification
- Solver-category boundary repair
- Timing-parameter retune
- Config and confwriter contract clarification
- Validation-surface extension

The current implementation path in
[src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
returns `long_min` itself from `_accent_adjacent_vowel_limit()` for adjacent
short vowels. That permits outputs such as the `IYA ... 0123` row currently
present in
[demo/akkapros/lexlinks/results/erra_construct_phone.txt](../../../demo/akkapros/lexlinks/results/erra_construct_phone.txt).

That behavior is hard to defend as a phonological category boundary because a
short vowel that reaches `123 ms` has already crossed into the configured long
field. The solver should not represent a vowel as short while also letting its
duration enter the long-vowel category.

At the same time, the current timing model still treats consonant saturation
through the one global `segmental_ceiling = 310`, even though consonant timing
is otherwise class-specific. The requested retune introduces narrower class-
local maxima and updated fricative and vowel defaults so the solver’s hard
stops match the intended phonetic categories more closely.

The requested `segmental_floor` addition complements that ceiling by making the
shared lower validation boundary explicit. The floor is not meant to drive
runtime realization. It exists so config, confwriter, and repository YAML files
can declare one minimum bound that all vowel and consonant minima must satisfy,
including hiatus and vowel-transition special realizations.

---

## Scope

## Included

- Narrow the adjacent-accent spill contract for short vowels from `long_min` to
  `long_min - 1`
- Require emitted adjacent short-vowel outcomes to remain strictly below the
  long-vowel field
- Change the default timing values to:
  `consonants.fricative.geminate = 224`,
  `consonants.fricative.perception_limits.geminate_min = 210`, and
  `vowels.perception_limits.elongation_max = 250`
- Add `perception_limits.gemination_max` for each consonant class with defaults:
  `closure = 221`, `fricative = 250`, and `sonorant = 182`
- Add `segmental_floor` immediately after `segmental_ceiling` with default
  `10`
- Require the solver to use class-local `gemination_max` values instead of
  `segmental_ceiling` for consonant saturation logic
- Keep `segmental_ceiling` in the config schema and verification surface as a
  global validation ceiling across consonant `gemination_max` values and
  `vowels.perception_limits.elongation_max`
- Use `segmental_floor` only for validation of vowel and consonant minima,
  including hiatus and vowel-transition minima, and not elsewhere in the
  algorithm
- Update the config and confwriter contract so `default.yaml`, emitted comments,
  and all currently existing project YAML files expose the new defaults and
  keys
- Concretely, the YAML update scope includes all three YAML files currently in
  the repository:
  `src/akkapros/config/default.yaml`,
  `demo/akkapros/lexlinks/construct-demo.yaml`, and
  `demo/akkapros/prosmaker/corpus-demo.yaml`
- Require same-CR documentation updates in public phonetizer docs and the
  relevant internal config/verification records
- Require same-CR documentation to explicitly list and explain all new
  parameters introduced by this CR, including `segmental_floor` and every new
  or retuned max/min key
- Require same-CR unit-test additions or updates that pin the new boundary and
  class-local maximum behavior
- Update phonetizer runtime tests, demo artifacts, and public phonetizer docs
  that currently allow or show `123 ms` adjacent short-vowel outcomes
- Make the supersession relationship to CR-063 explicit

## Not Included

- Changing ordinary non-accentual long-vowel recovery rules
- Changing the configured value of `long_min` itself
- Retuning `cvc_reference`, pause bands, or beat-folding behavior
- Reclassifying emitted rows by changing their `length` column from `S` to `L`
  as a workaround
- Removing `segmental_ceiling` from the config schema entirely
- Using `segmental_floor` as a runtime realization control outside validation

---

## Current Behavior

The live solver currently computes the adjacent-vowel ceiling with:

- `_accent_adjacent_vowel_limit()` in
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
- for `row['length'] == 'S'`, it returns `long_min`

With the active defaults inspected in the runtime config model:

- `short = 85`
- `long_min = 123`

the live solver therefore permits a short vowel to be extended from `85 ms` up
to `123 ms` during accent spill.

The live timing model currently also exposes these defaults:

- `consonants.fricative.geminate = 279`
- `consonants.fricative.perception_limits.geminate_min = 152`
- `vowels.perception_limits.elongation_max = 240`
- no `segmental_floor` key after `segmental_ceiling`
- no class-local `perception_limits.gemination_max` key for closure, fricative,
  or sonorant

And the live solver currently relies on one global consonant ceiling:

- `_consonant_maximum()` in
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  returns `timing_model.durations.segmental_ceiling`
- that ceiling is used in same-consonant and accent-distribution saturation
  paths instead of a class-local maximum

Observed repository evidence:

- [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  defines `long_min = 123`
- [src/akkapros/config/default.yaml](../../../src/akkapros/config/default.yaml)
  currently defines `segmental_ceiling = 310`,
  `fricative.geminate = 279`,
  `fricative.perception_limits.geminate_min = 152`, and
  `vowels.perception_limits.elongation_max = 240`
- current config surfaces do not expose a shared lower validation bound named
  `segmental_floor`
- [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  currently returns `long_min` for adjacent short vowels in
  `_accent_adjacent_vowel_limit()`
- [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  currently routes consonant maxima through `_consonant_maximum()` backed by
  `segmental_ceiling`
- [demo/akkapros/lexlinks/results/erra_construct_phone.txt](../../../demo/akkapros/lexlinks/results/erra_construct_phone.txt)
  contains `IYA|V|H|S|N|N|F|II|0123|-253|H2C|i`
- [docs/internal/cr/059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
  already states that with `long_min = 123`, the short-vowel ceiling is
  `122 ms`
- [docs/internal/req/022-package-wide-yaml-config-and-confwriter.md](../req/022-package-wide-yaml-config-and-confwriter.md)
  and [docs/internal/req/027-phonetize-config-semantic-invariants-for-shared-verification.md](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
  currently describe a config/verification surface centered on
  `segmental_ceiling` plus `geminate_min`, but not class-local `gemination_max`

This leaves the repository with a direct code/spec mismatch: the implementation
admits a value that the internal phonetizer reasoning already treats as outside
the short-vowel field.

---

## Proposed Change

The phonetizer solver shall treat adjacent accent spill into a short vowel as a
strictly sub-long outcome, and it shall replace the current global consonant
ceiling with class-local gemination maxima.

Normative rule:

- when the adjacent spill target is a short vowel, its legal upper bound is
  `long_min - 1`
- the solver must never emit an adjacent short-vowel duration equal to or
  greater than `long_min`

Normative default-parameter changes:

- `segmental_floor = 10`
- `consonants.fricative.geminate = 224`
- `consonants.fricative.perception_limits.geminate_min = 210`
- `vowels.perception_limits.elongation_max = 250`
- `consonants.closure.perception_limits.gemination_max = 221`
- `consonants.fricative.perception_limits.gemination_max = 250`
- `consonants.sonorant.perception_limits.gemination_max = 182`

Normative solver rule:

- consonant saturation paths that currently consult `segmental_ceiling` must
  instead use the active class-local `perception_limits.gemination_max`
- `segmental_ceiling` remains part of the config schema and semantic
  verification surface, but it is no longer the runtime algorithm’s direct
  consonant ceiling
- `segmental_floor` is added immediately after `segmental_ceiling` in the
  timing config, but it is validation-only and is not used elsewhere in the
  algorithm
- semantic verification must ensure, for each consonant class, that there is
  no required ordering relation between `onset` and `coda` themselves
- semantic verification must ensure, for each consonant class, that both
  `onset < geminate_min <= geminate <= gemination_max <= segmental_ceiling` and
  `coda < geminate_min <= geminate <= gemination_max <= segmental_ceiling`
- semantic verification must therefore enforce both
  `geminate <= gemination_max` and
  `gemination_max <= segmental_ceiling` for every consonant class
- semantic verification must also ensure
  `segmental_floor <= vowels.short_min`,
  `segmental_floor <= vowels.long_min`,
  `segmental_floor <= vowels.very_long_min`,
  `segmental_floor <= closure.special_realization.hiatus`,
  `segmental_floor <= sonorant.special_realization.vowel_transition`, and
  all onset, coda, and `geminate_min` values are greater than or equal to
  `segmental_floor`
- semantic verification must also ensure
  `vowels.perception_limits.elongation_max <= segmental_ceiling`
- the change is not complete unless the new runtime behavior is documented in
  the public phonetizer docs and pinned by focused unit tests

Normative documentation rule:

- public docs, internal config/verification records, confwriter-emitted help,
  and all repository YAML surfaces must explicitly document all new parameters
  introduced by this CR, including `segmental_floor`, class-local
  `gemination_max`, and the retuned fricative and vowel elongation-max defaults

Under the current defaults this means:

- `long_min = 123`
- maximum adjacent short-vowel spill outcome = `122`

As a result, rows such as:

```text
IYA|V|H|S|N|N|F|II|0123|...|i
```

must no longer be emitted when that row remains a short-vowel row.

This change narrows CR-063 rather than replacing it wholesale. All other
accent-distribution and drift rules from CR-063 remain in force unless they are
directly inconsistent with this stricter boundary or with the class-local
geminate-max retune defined here.

---

## Technical Design

Explain how it should be implemented.

Architecture notes:

Components:

- phonetizer Phase 2 accent-increment routing
- phonetizer config and semantic verification rules
- confwriter-emitted phonetize timing surface
- solver-facing unit coverage
- demo/reference phone artifacts
- public phonetizer algorithm documentation

Storage:

- no new persistent storage
- refreshed demo/reference artifacts will reflect the narrowed ceiling
- repository-owned YAML examples will need refreshed phonetize timing defaults
- config surfaces will gain one additional timing key, `segmental_floor`

API changes:

- additive config-schema change under consonant `perception_limits` through the
  new `gemination_max` key
- additive config-schema change under `timing_model.durations` through the new
  `segmental_floor` key
- emitted phone-row durations for adjacent short vowels may decrease by 1 ms in
  cases that currently hit `long_min`
- emitted consonant durations may now saturate at class-local maxima instead of
  the one global `segmental_ceiling`

Implementation shape:

- change the adjacent short-vowel legality ceiling from `long_min` to
  `long_min - 1`
- change the relevant timing defaults in the built-in config and repository YAML
  examples
- insert `segmental_floor` immediately after `segmental_ceiling` in the config
  schema, confwriter output, and all current project YAML files
- add class-local `perception_limits.gemination_max` keys for closure,
  fricative, and sonorant
- replace runtime uses of `_consonant_maximum()` backed by
  `segmental_ceiling` with class-local maximum lookup based on consonant class
- keep `segmental_ceiling` in config emission, confwriter help/comments, and
  semantic verification as a global validation ceiling rather than a runtime
  saturation control
- use `segmental_floor` only in validation and documentation surfaces to check
  vowel minima, consonant anchors/minima, hiatus minimum, and transition
  minimum; do not use it elsewhere in the runtime solver
- update semantic verification and related config-contract records so
  `gemination_max` participates in the ordered consonant timing invariants
- update semantic verification and related config-contract records so
  `segmental_floor` participates in the lower-bound timing invariants
- preserve the existing broader legality space for long-vowel and accent-bearing
  long-vowel outcomes
- add or update targeted tests that prove a short vowel adjacent to the primary
  accent can stop at `122` but not `123` under the active defaults
- add or update tests that prove consonant saturation uses `gemination_max`
  per class and that config validation still checks all maxima against
  `segmental_ceiling`
- refresh demo/reference outputs that currently lock in `0123` for adjacent
  short-vowel spill
- update public solver prose so the short-vowel categorical boundary is stated
  explicitly
- update public and internal docs so every new parameter added or retuned by
  this CR is listed and explained explicitly

---

## Files Likely Affected

src/akkapros/lib/phonetize.py
src/akkapros/config/default.yaml
demo/akkapros/lexlinks/construct-demo.yaml
demo/akkapros/prosmaker/corpus-demo.yaml
tests/test_phonetize_lib.py
tests/test_integration.py
tests/test_config_support.py
demo/akkapros/lexlinks/results/erra_construct_phone.txt
docs/akkapros/phonetizer-algorithm.md
docs/akkapros/phonetizer-phone-file-guide.md
docs/internal/req/022-package-wide-yaml-config-and-confwriter.md
docs/internal/req/027-phonetize-config-semantic-invariants-for-shared-verification.md

---

## Acceptance Criteria

- [x] Adjacent accent spill into a short vowel is capped at `long_min - 1`
- [x] No emitted short-vowel row reaches `long_min` or greater through adjacent
      accent spill
- [x] Under the active defaults, a short vowel may stop at `122 ms` but not at
      `123 ms`
- [x] The active defaults become `fricative.geminate = 224`,
  `fricative.perception_limits.geminate_min = 210`, and
  `vowels.perception_limits.elongation_max = 250`
- [x] `segmental_floor = 10` is added immediately after `segmental_ceiling`
      across the config surface
- [x] Each consonant class exposes `perception_limits.gemination_max` with the
  defaults `closure = 221`, `fricative = 250`, and `sonorant = 182`
- [x] The consonant-timing algorithm no longer uses `segmental_ceiling` as its
  direct runtime saturation ceiling
- [x] Consonant saturation uses the class-local `gemination_max` value that
  corresponds to the active consonant class
- [x] `segmental_ceiling` remains present in config, confwriter output, and
  semantic verification as a global validation ceiling over consonant
  `gemination_max` values and `vowels.perception_limits.elongation_max`
- [x] `segmental_floor` is used only for validation of vowel and consonant
  minima, including hiatus and vowel-transition minima, and not elsewhere in
  the algorithm
- [x] Semantic verification treats `gemination_max` as part of the ordered
  consonant timing invariant for each class
- [x] Semantic verification enforces the `segmental_floor` lower bound across
  vowel minima, consonant anchors/minima, hiatus minimum, and transition
  minimum
- [x] Existing long-vowel ordinary-recovery and accent-bearing long-vowel rules
      remain unchanged
- [x] Focused unit tests cover the narrowed short-vowel ceiling
- [x] Focused config or verification tests cover the new `gemination_max`
  defaults and invariant checks
- [x] Unit-test coverage is added or updated in the same implementation change,
  not deferred to a follow-up
- [x] All currently existing project YAML files reflect the new defaults and
  keys
- [x] The required YAML set explicitly includes
  `src/akkapros/config/default.yaml`,
  `demo/akkapros/lexlinks/construct-demo.yaml`, and
  `demo/akkapros/prosmaker/corpus-demo.yaml`
- [x] Refreshed demo/reference artifacts no longer contain the current
      `...|0123|...` adjacent-short-vowel example where the row remains short
- [x] Public phonetizer documentation states the stricter boundary and the
  class-local `gemination_max` behavior clearly
- [x] The relevant internal config and verification records are updated to match
  the new config surface and invariants
- [x] Documentation explicitly lists and explains all new parameters introduced
      or retuned by this CR

---

## Risks / Edge Cases

Possible issues:

- Some existing gold artifacts may change by only `1 ms`, which is easy to miss
  in manual review but still contract-significant
- If drift is preserved instead of using that last `1 ms`, some downstream
  drift summaries may shift slightly
- Any tests or docs that currently treat `123 ms` as a valid short-vowel spill
  outcome will need refresh
- Existing config-verification records and tests currently centered on
  `segmental_ceiling` may need explicit narrowing language so `gemination_max`
  becomes the runtime ceiling without making the validation contract ambiguous
- The new `segmental_floor` key could be misread as a runtime timing control if
  the docs do not state clearly that it is validation-only
- The requested fricative retune sharply raises `geminate_min` while lowering
  `geminate`, so the ordering invariants in the older config-verification
  records may need deliberate rewrite rather than silent reinterpretation

---

## Testing Strategy

Unit tests:

- adjacent short-vowel spill stops at `long_min - 1`
- adjacent short-vowel spill never emits `long_min`
- long-vowel accent distribution remains unchanged
- consonant saturation uses class-local `gemination_max` for closure,
  fricative, and sonorant paths
- config verification accepts the new defaults and checks
  `gemination_max <= segmental_ceiling`
- config verification accepts `segmental_floor = 10` and checks all required
  vowel and consonant minima against it

Documentation verification:

- public phonetizer docs describe both the stricter short-vowel boundary and
  the class-local `gemination_max` shift
- internal config and verification records describe the new keys, defaults, and
  invariants without leaving `segmental_ceiling` as the runtime consonant cap
- confwriter-emitted comments and config-facing docs explicitly document all new
  parameters added or retuned by this CR

Integration tests:

- representative phone-row outputs no longer emit `0123` on a short-vowel row
  in the affected path
- repository YAML-driven runs reflect the new timing defaults and class-local
  maxima

Manual tests:

- inspect the affected span in
  [demo/akkapros/lexlinks/results/erra_construct_phone.txt](../../../demo/akkapros/lexlinks/results/erra_construct_phone.txt)
  and confirm the short-vowel row no longer enters the long field
- inspect current config values and confirm the emitted maximum short-vowel
  spill under `long_min = 123` is `122`
- inspect all three current project YAML files and confirm they expose the new
  fricative values, the new vowel elongation max, and the new `gemination_max` keys:
  `src/akkapros/config/default.yaml`,
  `demo/akkapros/lexlinks/construct-demo.yaml`, and
  `demo/akkapros/prosmaker/corpus-demo.yaml`
- inspect those same YAML files and confirm `segmental_floor` appears
  immediately after `segmental_ceiling`
- inspect confwriter output and confirm `segmental_ceiling` is still emitted as
  a validation-facing key while class-local `gemination_max` is visible as the
  runtime-relevant consonant maximum
- inspect confwriter output and documentation surfaces and confirm all new
  parameters are documented explicitly, including `segmental_floor`

---

## Rollback Plan

Explain how to revert if needed.

Restore the previous adjacent short-vowel ceiling of `long_min`, remove the new
class-local `gemination_max` keys or stop using them in the solver, restore the
earlier fricative and vowel-max defaults, remove `segmental_floor`, then
refresh tests, demo artifacts, and docs back to the earlier broader behavior.

---

## Related Issues

- [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
- [CR-063](063-tune-the-phonetizer-solver.md)
- [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)
- [REQ-027](../req/027-phonetize-config-semantic-invariants-for-shared-verification.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- [REQ-035](../req/035-phonetizer-phase2-path-complete-unit-test-coverage.md)

---

## Tasks

## Implementation

- [x] Narrow `_accent_adjacent_vowel_limit()` so short-vowel adjacency stops at
      `long_min - 1`
- [x] Update the phonetizer timing defaults to the requested fricative and vowel
  values
- [x] Add `segmental_floor = 10` immediately after `segmental_ceiling` in the
  config schema, confwriter surface, and all current project YAML files
- [x] Add class-local `perception_limits.gemination_max` keys and use them in the
  runtime consonant saturation logic instead of `segmental_ceiling`
- [x] Refresh affected phone-row gold artifacts
- [x] Refresh all three currently existing project YAML files:
  `src/akkapros/config/default.yaml`,
  `demo/akkapros/lexlinks/construct-demo.yaml`, and
  `demo/akkapros/prosmaker/corpus-demo.yaml`

## Tests

- [x] Add or update focused unit coverage for the `122` vs `123` boundary
- [x] Add or update focused unit coverage for class-local `gemination_max`
  behavior and validation
- [x] Add or update focused validation coverage for `segmental_floor` and its
  lower-bound checks
- [x] Refresh integration or demo-gold assertions affected by the narrowed cap

## Documentation

- [x] Update public phonetizer docs to state that adjacent short-vowel spill is
      strictly sub-long
- [x] Update internal config and verification records that still describe
  `segmental_ceiling` as the runtime consonant ceiling
- [x] Document all new parameters introduced or retuned by this CR, including
  `segmental_floor`, the class-local `gemination_max` keys, and the retuned
  fricative/vowel elongation-max defaults
- [x] Ensure documentation changes ship in the same implementation slice as the
  runtime and test changes

## Review

- [x] Verify acceptance criteria
- [x] Confirm the new CR is treated as the active narrower contract relative to
  CR-063
- [x] Confirm the config/confwriter surface and repository YAML files are all
  covered by the updated contract

---

## Implementation Blockers

Leave the section empty if no blockers are known.

---

## Notes

This CR remains targeted rather than general. It does not reopen the full
CR-063 solver rewrite, pause logic, or broader timing-model architecture. It
repairs one categorical short-vowel boundary and one consonant-ceiling design
issue, then pushes those narrower changes through the phonetizer config,
confwriter, and repository YAML surfaces.

For this CR, `segmental_floor` is a validation-only config parameter. It is not
intended to alter runtime realization beyond the config-verification layer.

Assumption: the user request spelling `sonorante` refers to the existing
repository timing class name `sonorant`.
