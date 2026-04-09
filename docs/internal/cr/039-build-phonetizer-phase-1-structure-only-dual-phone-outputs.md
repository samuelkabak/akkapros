---
cr_id: CR-039
status: Done
priority: High
impact: Mutative
created: 2026-04-05
updated: 2026-04-09
implements: 'ADR-040, REQ-024, REQ-025'
---

# Change Request: Build phonetizer phase 1 structure-only dual phone outputs

# Summary

Implement the first phase of the phonetizer program and associated phonetize
library.

This CR implements only structural row generation, not timing realization.

Under this CR:

- input is `<prefix>_tilde.txt`
- the phonetizer builds two phone-row lists from that input:
  - original / deaccented rows
  - accentuated rows
- every emitted row has all ten CR-036 fields populated in exact order:
  - `label, category, type, length, position, boundary, accent, realization, duration, text`
- every emitted row uses `duration=0000`
- outputs are written as:
  - `<prefix>_ophone.txt` for the original stream
  - `<prefix>_phone.txt` for the accentuated stream
- emitted rows use the CR-036 realization-side inventory, including the
  dedicated two-character `realization` code and the split `type` / `length`
  contract

The original stream is derived from the accentuated `_tilde` input by:

- removing `~`
- replacing `&` with space
- preserving lexical merge `+`

The duration-computation pass is explicitly out of scope for this CR.

Big-picture requirement chain for implementation context:

- [REQ-024](../req/024-replacement-of-timing-model.md): umbrella program story
- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md): two-phase phonetizer architecture

---

# Motivation

The phonetizer cannot wait for the final timing algorithms before it becomes
testable. The project first needs a working structural builder that converts the
accentuated prosody pivot into deterministic phone-row artifacts.

That builder must emit both the original and accentuated streams because later
timing work will compare them and update durations differently while relying on
the same structural contract.

Implementing structure generation first also enables a strong automatic test:
the system can reconstruct the relevant `_tilde` structure from emitted rows and
verify that the row builder preserved the distinctions it was supposed to carry.

---

# Scope

## Included

- Implement a phonetize library entry point for Phase 1 structural row
  generation.
- Implement a phonetizer CLI entry point that reads `<prefix>_tilde.txt`.
- Derive an original/deaccented structural input from the accentuated `_tilde`
  source by removing `~` and replacing `&` with space.
- Build two phone-row lists: original and accentuated.
- Populate all row fields required by the current `_phone` contract,
  including the exact ten-field order from CR-036.
- Set `duration=0000` on every Phase 1 row.
- Write the original rows to `<prefix>_ophone.txt`.
- Write the accentuated rows to `<prefix>_phone.txt`.
- Add extensive unit tests for row building and automatic reconstruction from
  output rows.
- Require Phase 1 row construction to honor the CR-036 split between
  realization-side `label` and source-side labels, the split between `type`
  and `length`, and the two-character `realization` code inventory.
- Define the phase-1 realization-selection rules needed to choose among the
  CR-036 one-to-many input-to-realization mappings while building rows from
  `_tilde`.

## Not Included

- Implementing either of the later duration algorithms.
- Assigning final non-zero duration values.
- Redefining the row schema from CR-036.
- Replacing `_tilde` as the input artifact.
- Finalizing metrics-side consumption of Phase 2 timing outputs.
- Defining Phase 2 duration-distribution fallback behavior or timing-model
  ceilings beyond what is structurally required for Phase 1.

---

# Current Behavior

The repository has internal records for the phonetize stage and for `_phone`
row structure, but it does not yet have a CR that explicitly scopes the first
implementation step as structure-only row generation with dual outputs.

Without that narrowed implementation scope, the first phonetizer build risks
drifting into premature duration logic or into a single-stream design that does
not make the original form explicit.

---

# Proposed Change

Implement Phase 1 of the phonetizer exactly as follows.

## 1. Input and stream derivation

The phonetizer reads `<prefix>_tilde.txt`.

From that single input, it builds two structural source views:

- accentuated view: the `_tilde` content as provided
- original view: the same content after:
  - `~ -> ''`
  - `& -> ' '`

Important preservation rules:

- explicit lexical merge `+` is preserved in the original view
- ordinary internal syllable separator `·` is preserved
- enclitic dash `-` is preserved
- explicit merge `+`, internal merge `&`, enclitic dash `-`, and ordinary
  syllable separator `·` must not be collapsed during accentuated-row building

Normative examples:

| Accentuated `_tilde` input | Derived original view |
| --- | --- |
| `u+ana&šar~.ri` | `u+ana šar.ri` |
| `gi.mir&dad~.mē` | `gi.mir dad.mē` |
| `šit·ku·nat-ma` | `šit·ku·nat-ma` |
| `ana+šar~.ri` | `ana+šar.ri` |
| `u&ana+šar~.ri` | `u ana+šar.ri` |

## 2. Phase 1 row generation

For both structural views, the implementation builds a list of phone rows using
the existing `_phone` row contract.

Phase 1 is also the owning step for realization selection. Where CR-036
documents one-to-many input-to-realization mappings, the phonetizer must apply
the phase-1 realization-selection rules during row construction from `_tilde`.
Those rules are part of this CR rather than CR-036 because they are runtime
row-building behavior, not static contract inventory.

Phase 1 obligations:

- all non-duration fields are fully populated
- rows use the exact CR-036 field order:
  - `label, category, type, length, position, boundary, accent, realization, duration, text`
- rows preserve the CR-036 split semantics:
  - `type` carries structural class
  - `length` carries phonological short/long status
  - `realization` carries the two-character realization code
- every row uses `duration=0000`
- row ordering preserves input reading order
- original and accentuated streams remain separate artifacts
- row generation must use the CR-036 realization-side inventory rather than
  emitting source-side labels directly
- row generation must resolve CR-036 one-to-many mappings into one concrete
  emitted `realization` code per row, using the phase-1 realization-selection
  rules defined in this CR

### 2.1 Phase-1 realization-selection rules

The realization-selection rules below apply during Phase 1 row construction
from `_tilde`. They choose one concrete realization code wherever CR-036
documents one-to-many input-to-realization mappings.

#### Emphatic-conditioned vowel realizations in `CV` and `CVV`

When a vowel nucleus immediately follows an onset consonant whose emitted
realization has `Emphaticity=E`, the vowel must use its emphatic-colored
realization variant.

This rule applies to syllable shapes `CV` and `CVV`.

Normative mapping rule:

- low vowel nucleus -> `AO` instead of `AA`
- mid vowel nucleus -> `EO` instead of `EE`
- high front vowel nucleus -> `IO` instead of `II`
- high back vowel nucleus -> `UO` instead of `UU`

The emitted consonant row remains unchanged. The emphatic effect is expressed
through the vowel row's `realization` code.

Normative examples:

| Input sequence | Input labels | Emitted realization codes | Why |
| --- | --- | --- | --- |
| `qa` | `QUP` + `AYA` | `QU` + `AO` | `QU` has emphaticity `E`, so low vowel uses emphatic variant |
| `qā` | `QUP` + `AWA` | `QU` + `AO` | Same rule for `CVV` |
| `sa` | `SAM` + `AYA` | `SA` + `AA` | `SA` has emphaticity `P`, so plain vowel remains plain |
| `sā` | `SAM` + `AWA` | `SA` + `AA` | Same plain rule for `CVV` |

#### Vowel-transition realization type

The vowel-transition symbol `¨` is realized according to the immediately
preceding realized vowel row and immediately following realized vowel row.

Constraints:

- the vowel-transition row always occurs after a vowel and before a vowel
- the two neighboring vowels must be different
- identical realized-vowel pairs are not valid vowel-transition cases under
  this rule

Selection rule:

- emit `YI` when the transition is realized as IPA `j`
- emit `WA` when the transition is realized as IPA `w`

Normative table:

| First Realization | Second Realization | Realization IPA | Realization Code |
| --- | --- | --- | --- |
| `II`, `IO` | `AA`, `UU`, `EE` | `j` | `YI` |
| `UU`, `UO` | `AA`, `II`, `EE` | `w` | `WA` |
| `EE`, `EO` | `AA`, `II` | `j` | `YI` |
| `EE`, `EO` | `UU` | `w` | `WA` |
| `AA`, `AO` | `II`, `EE` | `j` | `YI` |
| `AA`, `AO` | `UU` | `w` | `WA` |

Interpretation note:

- this rule governs the one-to-many CR-036 mapping `ENA -> WA | YI`
- the surrounding realized vowel rows determine whether the emitted
  vowel-transition row uses glide type `j` or `w`
- this table is written in realization-space to avoid ambiguity between input
  vowel labels and emitted vowel realizations

## 3. Output files

The CLI writes:

- `<prefix>_ophone.txt` for the original row list
- `<prefix>_phone.txt` for the accentuated row list

Under this CR, both outputs are valid Phase 1 artifacts with zero durations.
The accentuated file name remains `_phone.txt` even though duration realization
has not yet happened.

## 4. Automatic reconstruction requirement

Phase 1 must support automatic testing by reconstructing the relevant input
structure from the emitted phone rows.

At minimum, tests must be able to verify that the emitted rows preserve enough
information to recover the structural distinctions that governed row building.

That reconstruction-relevant information must come from explicit row fields
already defined by CR-036, especially `boundary`, `accent`, `realization`,
`length`, and `text`, rather than from hidden implementation state.

For the accentuated stream, reconstruction must preserve where the input used:

- `~`
- `·`
- `-`
- `&`
- `+`

For the original stream, reconstruction must preserve the derived original
view, not the accentuated source.

Examples of what the autotest must be able to prove:

- rows built from `šit·ku·nat-ma` reconstruct `šit·ku·nat-ma`
- accentuated rows built from `u+ana&šar~.ri` reconstruct `u+ana&šar~.ri`
- original rows built from that same input reconstruct `u+ana šar.ri`
- accentuated rows built from `gi.mir&dad~.mē` reconstruct `gi.mir&dad~.mē`
- original rows built from that same input reconstruct `gi.mir dad.mē`

## 5. Library/CLI split

Implementation should keep structure generation in library code and limit the
CLI to file I/O, option handling, and output materialization.

Expected components:

- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/lib/constants.py`
- `src/akkapros/lib/diphthongs.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/fullprosmaker.py`
- `tests/`
- phonetizer docs under `docs/akkapros/`

Design requirements:

- Phase 1 must not embed or guess the later duration algorithms.
- Phase 1 must produce two explicit row lists, not one list plus an implicit
  derivation rule hidden in tests.
- Phase 1 must rely on the `_phone` contract already defined elsewhere.
- Phase 1 must implement the CR-036 row contract exactly, including the
  ten-field order, split `type` / `length` semantics, and the dedicated
  two-character `realization` field.
- Phase 1 must be the only stage that reads `_tilde` to choose emitted row
  identities, including the choice among one-to-many realization mappings from
  CR-036.
- The original stream derivation rule must be deterministic and documented in
  code-level tests.
- The emitted rows must support automatic reconstruction checks from output
  back to the applicable input structure.
- Phase 1 must use the CR-036 canonical realization-side inventory for emitted
  labels/codes, including short versus long pause rows, hiatus rows, and
  vowel-transition rows.
- Extensive unit tests are mandatory because later duration work will assume
  the structural builder is already correct.

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/lib/constants.py`
`src/akkapros/lib/diphthongs.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/cli/fullprosmaker.py`
`tests/`
`docs/akkapros/`

---

# Acceptance Criteria

- [x] A phonetize library entry point exists for Phase 1 structural row
      generation from `<prefix>_tilde.txt` content.
- [x] A phonetizer CLI exists that reads `_tilde.txt` and writes
      `<prefix>_ophone.txt` and `<prefix>_phone.txt`.
- [x] The original stream is derived by removing `~` and replacing `&` with
      space, while preserving `+`.
- [x] Phase 1 populates all required row fields from the `_phone` contract.
- [x] Phase 1 emits rows in the exact CR-036 field order:
  `label, category, type, length, position, boundary, accent, realization, duration, text`.
- [x] Phase 1 preserves the CR-036 split between `type` and `length` and emits
  a dedicated two-character `realization` code on every row.
- [x] Phase 1 resolves any CR-036 one-to-many input-to-realization mappings
      during row construction and emits one concrete realization code per row.
- [x] Phase 1 realizes vowels following emphatic onset consonants in `CV` and
  `CVV` with the emphatic-colored vowel codes `AO`, `EO`, `IO`, or `UO`
  as appropriate.
- [x] Phase 1 resolves `ENA` vowel-transition rows to `YI` or `WA` from the
  immediately surrounding vowels according to the normative table in this
  CR.
- [x] Every Phase 1 row uses `duration=0000`.
- [x] Original and accentuated outputs are both emitted for the same input.
- [x] Unit tests cover accentuated and original stream derivation for
      representative inputs with `~`, `·`, `-`, `&`, and `+`.
- [x] Unit tests cover automatic reconstruction of the applicable input string
      from emitted rows.
- [x] Unit tests cover emitted-row correctness for representative hiatus,
  vowel-transition, and short/long pause rows under the CR-036 inventory.
- [x] Unit tests cover cases where the original stream differs from the
      accentuated stream only by `~` removal.
- [x] Unit tests cover cases where the original stream differs because `&`
      becomes space while `+` remains preserved.
- [x] Integration tests cover CLI generation of both `_ophone.txt` and
      `_phone.txt` from a representative `_tilde.txt` sample.
- [x] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [x] Documentation is updated in separate phonetizer and algorithm files,
  configuration/confwriter docs where the new stage surface is described,
  and impacted downstream program docs such as fullprosmaker.

---

# Risks / Edge Cases

Possible issues:

- The implementation may accidentally normalize `+` and `&` together during
  original-stream derivation, which would erase lexical merge structure.
- The implementation may accidentally apply deaccentuation rules to the
  accentuated stream as well as to the original stream.
- The implementation may blur the distinction between ordinary internal `·`
  and enclitic `-` separators if reconstruction checks are weak.
- The implementation may postpone too much logic into the future duration pass,
  leaving Phase 1 rows structurally incomplete.

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for
  original/accentuated stream derivation, row construction, reconstruction,
  and dual-output CLI behavior

Unit tests:

- derive original view from accentuated `_tilde`
- preserve explicit lexical merge `+` during original derivation
- replace internal merge `&` with space during original derivation
- remove `~` from the original derivation only
- build accentuated rows with `duration=0000`
- build original rows with `duration=0000`
- verify exact CR-036 row-field order in emitted rows
- verify `type`, `length`, and `realization` are populated separately rather
  than collapsed
- verify representative hiatus, vowel-transition, and pause rows use CR-036
  realization-side labels/codes
- verify one-to-many CR-036 mappings are resolved in Phase 1 rather than left
  ambiguous in emitted rows
- verify emphatic onset + vowel cases such as `qa` and `qā` emit `AO` rather
  than `AA`
- verify non-emphatic onset + vowel cases such as `sa` and `sā` remain plain
- verify vowel-transition `ENA` emits `YI` or `WA` according to the first and
  second vowel pair table
- reconstruct accentuated input from accentuated rows for representative cases
- reconstruct derived original input from original rows for representative cases
- cover ordinary internal syllables, enclitic dashes, explicit merges, and
  internal merges in separate and mixed examples

Representative examples should include at least:

- `šit·ku·nat-ma`
- `ana+šar~.ri`
- `u+ana&šar~.ri`
- `gi.mir&dad~.mē`
- `u&ana+šar~.ri`

Integration tests:

- CLI run emits both `_ophone.txt` and `_phone.txt`
- emitted rows remain parseable by the repository's row reader/parsing helpers
- round-trip autotest logic can be run over CLI-produced fixtures

Manual review:

- inspect representative dual outputs side by side
- inspect library/CLI separation so row building is not trapped in CLI-only code

---

# Rollback Plan

If Phase 1 proves too large, roll back to documentation-only phonetizer records
and defer implementation until after a narrower preparatory CR. Partial
rollback that leaves only one of `_ophone` or `_phone` would be misleading and
is discouraged.

---

# Related Issues

- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- [ADR-039](../adr/039-replacement-of-timing-model.md)
- [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- [CR-036](036-define-phonetizer-phoneme-framework.md)
- [CR-038](038-distinguish-explicit-and-internal-merge-connectors-in-tilde-pivot.md)

---

# Tasks

## Implementation

- [x] Add Phase 1 structure-building library code in `src/akkapros/lib/phonetize.py`
- [x] Add phonetizer CLI wiring for `_tilde` input and dual output files
- [x] Implement deterministic derivation of the original stream from the
      accentuated `_tilde` input
- [x] Build original and accentuated phone-row lists with `0000` durations
- [x] Add reconstruction helpers or test helpers for automatic row-based
      verification of applicable input structure

## Tests

- [x] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [x] Add extensive pytest unit coverage for stream derivation, row building,
  and automatic reconstruction
- [x] Add pytest integration coverage for dual-output CLI generation

## Documentation

- [x] Create or update `docs/akkapros/phonetizer.md` as the detailed Phase 1
  stage and CLI reference
- [x] Create or update `docs/akkapros/phonetizer-algorithm.md` as the detailed
  Phase 1 row-construction and derivation reference distinct from the CLI
  page
- [x] Update `docs/akkapros/configuration.md`, `docs/akkapros/confwriter.md`,
  and generated/default config comments anywhere the Phase 1 stage surface
  or phonetize keys are described
- [x] Update impacted downstream program docs, including
  `docs/akkapros/fullprosmaker.md`, for dual outputs and stage ordering

---

# Notes for CR-039

Assumptions recorded in this CR:

- CR-039 owns phase-1 realization selection because that choice happens while
  reading `_tilde` and constructing concrete phone rows.
- CR-039 remains structure-only: it chooses row identity and emits
  `duration=0000`, but it does not perform duration realization.

Open questions for approval, but not blockers to drafting this CR:

- What is the final deterministic rule set for choosing among the CR-036
  one-to-many mappings during row construction beyond the emphatic-conditioned
  vowel rules and vowel-transition rules specified here?