---
cr_id: CR-088
status: Done
priority: High
impact: Mutative
created: 2026-04-22
updated: 2026-04-22
implements: 'REQ-046, CR-036, CR-039'
---

# Change Request: Extend emphatic vowel coloring to coda contexts and phoneprep

## Summary

Extend the phonetizer so emphatic vowel coloring is no longer limited to
emphatic onsets. Add a dedicated pre-duration coloring pass that always
preserves the current onset-based rule and, when enabled, also colors vowels
licensed by an emphatic coda in the same syllable and by the immediately
following syllable within the same pause-bounded continuity.

This CR also updates `phoneprep` so its legality rules and reachable diphone
inventory cover the new plain/emphatic and emphatic/plain consonant-vowel
combinations introduced by the extended coloring behavior. The change is
optional at runtime through a new phonetizer realization config flag, but the
default must be enabled.

This CR narrows and supersedes the onset-only coloring wording in
[CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
without changing the emphatic consonant inventory or the existing realization
code inventory from [CR-036](036-define-phonetizer-phoneme-framework.md).

---

## Motivation

Current phonetizer runtime colors a vowel only when an emphatic consonant is in
the onset of the same syllable. That misses cases where an emphatic coda should
color its own nucleus and, in some contexts, the following syllable as well.

The missing behavior causes the live realization algorithm, printer outputs,
and phoneprep legality model to undergenerate emphatic-colored vowels in coda-
driven contexts such as `maq.rab`, while also failing to preserve requested
plain-vowel blocking behavior in syllables whose onset is one of the specified
blockers.

The project needs one explicit contract for these extended coloring rules so
implementation, tests, printer expectations, and `phoneprep` coverage all move
together.

---

## Scope

### Included

- Add one independent phonetizer vowel-coloring pass that runs after Phase 1
  row construction and before Phase 2 duration assignment.
- Keep the existing emphatic-onset coloring behavior, but rehome that logic to
  the new pass so coloring decisions are no longer split across multiple code
  paths.
- Add optional extended coloring behavior for emphatic codas in the same
  syllable.
- Add optional extended coloring behavior for the immediately following
  syllable when it remains inside the same pause-bounded continuity.
- Add a boolean phonetizer config parameter named
  `phonetize.process.realization.extended_emphatic_coloring` with default
  value `true`.
- Update phonetizer config help, defaults, confwriter surfaces, and
  verification/documentation surfaces so the new flag is user-visible and
  testable.
- Update every repository YAML file that serializes active phonetize defaults
  or examples so the new realization key is present wherever the live
  phonetize config surface is represented.
- Update `phoneprep` legality rules, reachable diphone inventory generation,
  and coverage expectations to admit the new colored-vowel contexts.
- Update printer-facing expectations and documentation for IPA and XAR outputs
  that consume colored vowel realizations from phone rows.
- Add focused tests for each configuration state of the new parameter and add
  integration tests for IPA and XAR output changes.
- Add new immutable test fixtures under `tests/` as needed; do not use
  `demo/`, `outputs/`, `tmp/`, or other mutable repository data in tests.
- Add focused documentation updates for phonetizer, printer, configuration,
  and phoneprep.

### Not Included

- Changing the emphatic consonant inventory itself.
- Changing pause ownership, pause durations, resync-pause timing, or the Phase
  2 duration solver.
- Adding new realization codes beyond the existing plain/emphatic vowel codes
  `AA/EE/II/UU` and `AO/EO/IO/UO`.
- Redesigning syllabification or prosody boundaries.
- Changing MBROLA symbol inventory beyond the consequences of existing colored
  vowel mappings becoming reachable in more contexts.

---

## Current Behavior

Current phonetizer runtime assigns emphatic-colored vowels only in
`_finalize_syllable()` when the onset of the same syllable contains an
emphatic consonant. In practice, the current condition is onset-only:

- emphatic onset -> nucleus is colored
- emphatic coda -> no extra coloring effect
- following syllable after emphatic coda -> no extra coloring effect

Current `phoneprep` legality mirrors a stricter post-emphatic-only model in
`is_vowel_valid()`:

- a colored vowel is legal only when the preceding consonant is emphatic
- a colored vowel before an emphatic coda is currently illegal
- reachable diphone generation therefore misses newly required plain/emphatic
  and emphatic/plain consonant-vowel combinations

Current user-facing phonetizer docs also describe Phase 1 as though vowel
coloring were only the existing onset-conditioned realization choice.

---

## Proposed Change

Implement the following behavior.

## 1. Add one dedicated vowel-coloring pass

Create one phonetizer pass that owns all vowel-coloring decisions for a built
row stream.

Required placement:

- input: Phase 1 structural rows after positions, boundaries, and transition
  rows have been resolved
- output: structurally unchanged rows whose vowel `realization` fields have
  been updated where coloring applies
- ordering: this pass runs before any Phase 2 duration assignment logic

The pass must run on both row streams built from `_tilde` input:

- the derived original stream (`_ophone`)
- the accentuated stream (`_phone`)

The pass must not depend on accent marks, duration values, drift values, or
resync-pause insertion.

## 2. Preserve the existing onset rule inside the new pass

The existing onset-conditioned behavior remains part of the live contract.

When a syllable nucleus follows an onset segment whose source glyph is one of
the emphatic consonants `q`, `ṣ`, or `ṭ`, that nucleus must be colored using:

- `AA -> AO`
- `EE -> EO`
- `II -> IO`
- `UU -> UO`

Equivalent long-vowel source labels must continue to map through the same plain
vs emphatic realization pairs already defined in the current realization
inventory.

If implementation moves the onset rule out of `_finalize_syllable()`, that is
required and desirable under this CR. Phase 1 row seeding may initialize plain
vowel realizations, but the new pass becomes the sole owner of coloring.

## 3. Add same-syllable emphatic-coda coloring

When a syllable contains an emphatic consonant in coda position, the nucleus of
that same syllable must also be colored unless the onset of that same syllable
contains a blocking plain consonant.

### 3.1 Trigger set

The coda trigger set is the existing emphatic consonant inventory:

- `q`
- `ṣ`
- `ṭ`

### 3.2 Blocking onset set for same-syllable coda coloring

Same-syllable coda-triggered coloring is blocked when the onset of that same
syllable contains any of these plain consonants:

- `t` (`TAW`)
- `s` (`SAM`)
- `k` (`KAP`)

Interpretation rules:

- the blocker check applies only to the new coda-triggered rule
- the blocker does not disable the existing emphatic-onset rule
- if a syllable is already colored because of an emphatic onset, it stays
  colored regardless of the coda blocker set
- if multiple onset consonants are present, the presence of any blocker member
  suppresses only the coda-triggered same-syllable coloring branch

Normative examples:

- `ma.qâm` -> second syllable vowel is colored because `q` is onset in `qâm`
- `maq.rab` -> first syllable vowel is colored because `q` is coda in `maq`
  and onset `m` is not a blocker
- `saq.rab` -> first syllable vowel remains plain because `q` is coda in `saq`
  but onset `s` blocks same-syllable coda coloring

## 4. Add next-syllable carry from emphatic codas

When a syllable contains an emphatic coda consonant, the nucleus of the
immediately following syllable must also be colored unless the following
syllable onset contains a blocking plain consonant.

This carry applies only to the immediate next syllable in row order. It does
not recursively recolor every later syllable in the continuity span.

### 4.1 Continuity definition

For this CR, "same continuity" means the next syllable is reachable without
crossing a punctuation-owned pause row.

Carry may cross ordinary row boundaries such as:

- `I`
- `E`
- `L`
- `X`
- `F`

Carry must stop before any structural pause row created from input punctuation
or end-of-line material, including rows such as `SES`/`SP` and `ZEN`/`ZP`.

Inserted resync pauses are explicitly excluded from the rule. Because the new
pass runs before duration assignment, the pass normally will not see resync
pause rows at all; if the implementation later reuses the pass on a stream that
contains them, they must not terminate or trigger the continuity logic.

### 4.2 Blocking onset set for next-syllable carry

The next-syllable carry is blocked when the onset of the following syllable
contains any of these plain consonants:

- `t` (`TAW`)
- `s` (`SAM`)
- `k` (`KAP`)

Normative examples:

- `maq.rab` -> both `a` vowels are colored
- `saq.rab` -> first `a` remains plain; second `a` is colored
- `maq.sab` -> first `a` is colored; second `a` remains plain because following
  onset `s` blocks carry

## 5. Config flag and default behavior

Add a new boolean config key:

- `phonetize.process.realization.extended_emphatic_coloring`

Contract:

- default value: `true`
- when `true`: apply the onset rule plus the new coda and next-syllable rules
- when `false`: preserve legacy behavior, meaning only the pre-existing
  emphatic-onset coloring rule applies

This key must be part of:

- the config schema
- the `confwriter` help, list, get, set, default, and verify surfaces that
  expose live phonetize config
- default YAML config
- all repository YAML config files that serialize active phonetize defaults or
  examples
- config rendering/help output
- semantic verification where appropriate for boolean fields
- effective runtime configuration reporting

This key must not be placed under `timing_model`. It belongs under
`phonetize.process.realization` because it governs segmental realization choice
rather than duration behavior.

## 6. Printer impact

No new printer symbol inventory is introduced. The printer already knows how to
render the existing emphatic vowel realizations.

Under this CR, printer behavior changes because additional row contexts may now
emit `AO`, `EO`, `IO`, and `UO` in both `_phone` and `_ophone` streams.

Documentation and tests must therefore update IPA and XAR expectations for
controlled coda-coloring examples.

## 7. Phoneprep legality and coverage updates

`phoneprep` must be updated so its legality model and generated reachable
diphone inventory match the newly reachable colored-vowel contexts.

### 7.1 Runtime goal for phoneprep

`phoneprep` must no longer assume that a colored vowel is legal only after an
emphatic left consonant. It must admit colored vowels in contexts needed to
cover:

- emphatic onset -> colored vowel
- plain onset + emphatic coda -> colored vowel when the runtime blocker set
  does not suppress coloring
- emphatic coda -> following syllable colored vowel when the next onset is not
  blocked

### 7.2 Required diphone coverage expansion

The reachable diphone inventory must include newly legal combinations for both:

- plain consonant -> colored vowel
- colored vowel -> emphatic consonant

and their converse emphatic/plain contexts where they arise from the extended
phonetizer model.

### 7.3 Phoneprep exclusion set requested for recording inventory

For `phoneprep` recording-inventory generation, plain consonants `t`, `d`, and
`k` must not be treated as legal predecessors of emphatic-colored vowels.

This set is intentionally distinct from the phonetizer blocker set used in the
runtime coloring algorithm:

- phonetizer blocker set for coda-driven coloring: `t`, `s`, `k`
- phoneprep recording-inventory exclusion set: `t`, `d`, `k`

The implementation must preserve that distinction exactly as specified in this
CR rather than silently normalizing the two sets.

### 7.4 Phoneprep output surfaces

Update the legality checks and reachable coverage logic that feed:

- generated word patterns
- reachable diphone inventory
- manifest and diphone sidecars
- any coverage summary derived from those inventories

---

## Technical Design

### Phonetizer

Suggested implementation shape:

- build rows structurally as today
- resolve transition rows as today
- run one new helper pass over each row stream before any duration logic
- then continue into `realize_phone_rows()` and later intonation assignment

The pass should operate on syllable/group views derived from row positions and
boundaries rather than reparsing `_tilde` text.

Minimum phonetizer design obligations:

- identify onset, nucleus, and coda rows from row metadata already present on
  the built stream
- detect emphatic onset membership using source glyph or equivalent stable row
  identity
- detect emphatic coda membership using source glyph or equivalent stable row
  identity
- detect blocking onset membership for same-syllable and next-syllable rules
- recolor only vowel rows
- leave consonant realizations unchanged
- avoid touching pause rows and transition rows

### Phoneprep

Suggested implementation shape:

- isolate legality helpers for colored-vowel admission so onset-based and
  coda-based contexts are explicit rather than implicit in one left-neighbor
  rule
- update reachable diphone computation to use the same legality model
- keep long-vowel folding and sidecar symbol mapping unchanged unless coverage
  generation requires new explicit tests only

### Configuration

Add the new boolean under the phonetize realization subsection. The canonical
config path is:

- `phonetize.process.realization.extended_emphatic_coloring`

The implementation must update the grouped phonetize config schema and all
rendered/default YAML surfaces accordingly. This includes repository-owned demo
and regression-default YAML files where the live phonetize config is serialized.

---

## Files Likely Affected

`src/akkapros/lib/phonetize.py`

`src/akkapros/lib/_phonetize_config.py`

`src/akkapros/cli/confwriter.py`

`src/akkapros/config/default.yaml`

`tests/integration_refs/regression_defaults.yaml`

`demo/akkapros/prosmaker/corpus-demo.yaml`

`demo/akkapros/lexlinks/construct-demo.yaml`

`src/akkapros/lib/phoneprep.py`

`src/akkapros/lib/print.py`

`tests/test_phonetize_lib.py`

`tests/test_phoneprep_lib.py`

`tests/test_print_merger.py`

`tests/test_integration.py`

`tests/test_config_support.py`

`tests/` fixture files added for this feature

`docs/akkapros/phonetizer-algorithm.md`

`docs/akkapros/phonetizer-data-model.md`

`docs/akkapros/phonetizer-phone-file-guide.md`

`docs/akkapros/phonetizer.md`

`docs/akkapros/printer.md`

`docs/akkapros/configuration.md`

`docs/akkapros/phoneprep.md`

`docs/akkapros/mbrola-voice-prep.md`

---

## Acceptance Criteria

- [x] Phonetizer exposes `phonetize.process.realization.extended_emphatic_coloring` as a boolean config key with default `true`.
- [x] When the new flag is `false`, phonetizer preserves legacy onset-only vowel coloring behavior.
- [x] When the new flag is `true`, a syllable nucleus is colored when its onset is emphatic, matching current behavior.
- [x] When the new flag is `true`, a syllable nucleus is colored when its coda contains `q`, `ṣ`, or `ṭ` and its onset does not contain `t`, `s`, or `k`.
- [x] When the new flag is `true`, the immediate following syllable nucleus is colored from an emphatic coda when that following onset does not contain `t`, `s`, or `k` and no punctuation-owned pause row intervenes.
- [x] Focused phonetizer tests cover both configuration states of `extended_emphatic_coloring` using explicit test-local config rather than inherited defaults.
- [x] Controlled phonetizer tests prove: `maq.rab` colors both vowels, `saq.rab` colors only the second vowel, and `maq.sab` colors only the first vowel.
- [x] Controlled phonetizer tests prove that `ma.qâm` still colors the second syllable from emphatic onset behavior.
- [x] Integration tests verify IPA output changes for at least one same-syllable coda case and one next-syllable carry case using immutable test-owned fixtures.
- [x] Printer tests confirm IPA/XAR outputs reflect the new row realizations for at least one same-syllable coda case and one next-syllable carry case.
- [x] Integration tests verify XAR output changes for at least one same-syllable coda case and one next-syllable carry case using immutable test-owned fixtures.
- [x] `phoneprep` legality and reachable diphone inventory include newly legal plain->colored and colored->emphatic combinations required by the extended phonetizer behavior.
- [x] `phoneprep` excludes plain `t`, `d`, and `k` as predecessors of emphatic-colored vowels in its recording-inventory generation path.
- [x] Every repository YAML file that serializes active phonetize defaults or examples includes `phonetize.process.realization.extended_emphatic_coloring`.
- [x] `confwriter` surfaces render and verify the new realization key.
- [x] Any new fixtures or configs added for this feature live under `tests/` and do not depend on mutable repository data outside `tests/`.
- [x] Documentation is updated to explain the new pass, the new config key, and the revised vowel-coloring contexts.

---

## Risks / Edge Cases

- Syllables with multiple onset consonants need a deterministic rule for blocker membership; this CR resolves that by treating blocker presence as existential (`any blocker member present`).
- The runtime blocker set (`t`, `s`, `k`) and the `phoneprep` recording-inventory exclusion set (`t`, `d`, `k`) intentionally differ; tests must guard against accidental collapse to one shared set.
- The next-syllable carry must not jump across punctuation-owned pause rows.
- The next-syllable carry must not be made recursive beyond the immediate next syllable unless a later CR explicitly extends it.
- Long vowels and circumflex vowels must recolor through the existing realization mapping only; no new long-vowel code family should be invented.

---

## Testing Strategy

Unit tests:

- Add narrow `phonetize` tests on hand-built `_tilde` inputs that isolate onset coloring, same-syllable coda coloring, blocker suppression, and next-syllable carry.
- Add explicit config-controlled tests for `extended_emphatic_coloring=true` and `false`.
- Add `phoneprep` tests for legality decisions and reachable diphone inventory entries covering newly legal colored-vowel contexts.
- Add `phoneprep` tests that prove the special exclusion of plain `t`, `d`, and `k` from predecessor-to-colored-vowel generation.
- Add printer tests for IPA/XAR rendering from controlled phone rows or small pipeline fixtures.
- Add config-support/confwriter tests that prove the new key is rendered, loaded, and verified at the `phonetize.process.realization` path.

Integration tests:

- Add end-to-end or narrow pipeline regressions that confirm colored-vowel realizations propagate into emitted IPA artifacts for a coda-driven example under immutable test-owned fixtures.
- Add end-to-end or narrow pipeline regressions that confirm colored-vowel realizations propagate into emitted XAR artifacts for a coda-driven example under immutable test-owned fixtures.

Manual verification:

- Run the phonetizer on controlled examples equivalent to `ma.qâm`, `maq.rab`, `saq.rab`, and `maq.sab` with the new flag both enabled and disabled.
- Run `phoneprep` coverage generation and confirm the reachable inventory now contains the new required diphones.

Verification commands should use test-owned inputs or hardcoded strings only. Do not rely on mutable artifacts under `demo/`, `outputs/`, `tmp/`, or other mutable repository locations.

---

## Rollback Plan

Disable the new behavior by setting
`phonetize.process.realization.extended_emphatic_coloring: false` if an
immediate runtime rollback is needed.

If a code rollback is required, revert the dedicated coloring-pass changes, the
new config key, and the `phoneprep` legality expansion together so the runtime,
coverage generator, and documentation return to one consistent onset-only
model.

---

## Related Issues

- Extends the Phase 1 realization-selection contract in [CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- Preserves the realization inventory from [CR-036](036-define-phonetizer-phoneme-framework.md)

---

## Tasks

### Implementation

- [x] Add the independent phonetizer coloring pass before duration assignment
- [x] Move existing onset-based coloring ownership into that pass
- [x] Add same-syllable emphatic-coda coloring with blocker handling
- [x] Add next-syllable carry with pause-bounded stopping logic
- [x] Add the new config key and default
- [x] Place the new key under `phonetize.process.realization`, not `timing_model`
- [x] Update confwriter and grouped config rendering/verification surfaces
- [x] Update all repository YAML config files that serialize active phonetize defaults or examples
- [x] Update `phoneprep` legality and reachable diphone generation
- [x] Verify printer surfaces consume the expanded realization contexts correctly

### Tests

- [x] Add phonetizer unit tests for onset, coda, blocker, and carry cases
- [x] Add config-toggle regression tests for enabled vs disabled extended coloring
- [x] Add or update immutable test fixtures under `tests/` for the new phonetizer and printer cases
- [x] Add `phoneprep` legality and inventory regression tests
- [x] Add printer regressions for IPA colored-vowel outputs
- [x] Add printer regressions for XAR colored-vowel outputs
- [x] Add config-support/confwriter regressions for the new realization key
- [x] Add or update one integration regression using controlled test-owned inputs

### Documentation

- [x] Update phonetizer user docs to describe the new coloring pass and config flag
- [x] Update configuration docs so the new parameter is documented under `phonetize.process.realization`
- [x] Update data-model docs to describe the newly reachable realization contexts
- [x] Update printer docs/examples affected by colored-vowel outputs
- [x] Update `phoneprep` and MBROLA voice-prep docs for the expanded legality/coverage model

### Review

- [x] Review runtime blocker-set vs phoneprep exclusion-set distinction
- [x] Verify all acceptance criteria

---

## Implementation Blockers

None at implementation time.

---

## Notes

- This CR is intentionally implementation-ready and should be sufficient for an
  instruction such as `implement CR-088` without reconstructing the request
  from chat history.
- The difference between the phonetizer blocker set (`t`, `s`, `k`) and the
  `phoneprep` exclusion set (`t`, `d`, `k`) is preserved exactly because the
  request specified different sets for runtime coloring and recording-inventory
  generation.
