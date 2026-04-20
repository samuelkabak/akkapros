---
cr_id: CR-080
status: Done
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-21
implements: 'CR-039, CR-040, CR-047, CR-059, CR-079'
---

# Change Request: Add Half-Beat Synchronization for Mono and ophone

## Summary

Update the phonetizer timing contract so synchronization basis is derived from the upstream `mora_mode` carried in the input frontmatter, and so the original stream in `_ophone.txt` also synchronizes on the half-beat basis used by mono timing.

After this change, the phonetizer must detect `metadata.options.mora_mode` from the input `_tilde` frontmatter. The accentuated stream in `_phone.txt` keeps the existing bimoraic synchronization basis when `mora_mode` is `bi`, using `cvc_reference`. The accentuated stream switches to a monomoraic synchronization basis when `mora_mode` is `mono`, using `0.5 * cvc_reference`. The original stream in `_ophone.txt` must also synchronize on `0.5 * cvc_reference`, using the same half-beat mechanism as mono timing.

That synchronization basis must govern the exact timing logic used for ordinary long-vowel drift correction, mini-pause insertion, and beat-aware pause targeting inside the configured short and long pause bands. Internally, the implementation may operate at `0.1 ms` precision so odd `cvc_reference` values can be handled without forcing premature rounding. Final emitted row durations remain integer milliseconds.

This CR updates the active execution surface described in `CR-079`. `CR-079` remains the record for adding pause-governed intonation and documenting the original-stream artifacts, but it must not be read as requiring `_ophone.txt` to keep synchronization on full `cvc_reference` beats.

---

## Motivation

- Correct beat selection for `mora_mode=mono`
- Remove a rhythm-model mismatch between mono prosody and bi-beat phonetizer synchronization
- Bring `_ophone.txt` onto the same half-beat synchronization basis as mono timing
- Unify the implementation mechanism for mono synchronization and original-stream synchronization
- Allow correct handling of odd `cvc_reference` values without unstable integer-only internal arithmetic

The current phonetizer uses `cvc_reference` as the active synchronization basis for several timing decisions, regardless of upstream mora mode and regardless of whether the stream is accentuated or original. That is acceptable for bimoraic timing, but it is not correct for the mono prosody mode where the operative beat should be one mora rather than two.

The current original stream also synchronizes against full `cvc_reference` beats. That is no longer desired. `_ophone.txt` should still be synchronized, but its synchronization basis should follow the same half-beat logic used for mono timing. These two operations can and should be designed in common rather than as unrelated special cases.

---

## Scope

### Included

- Detect `mora_mode` from input frontmatter during phonetizer execution.
- Define a synchronization basis that may depend on both stream type and `mora_mode`.
- Keep synchronization basis = `cvc_reference` for the accentuated stream when `mora_mode=bi`.
- Set synchronization basis = `0.5 * cvc_reference` for the accentuated stream when `mora_mode=mono`.
- Set synchronization basis = `0.5 * cvc_reference` for the original stream in `_ophone.txt`.
- Apply that synchronization basis to:
  - ordinary long-vowel drift correction,
  - mini-pause insertion,
  - selection of the exact pause duration inside the configured short-pause band,
  - selection of the exact pause duration inside the configured long-pause band,
  - drift normalization or folding logic that currently assumes a full `cvc_reference` beat.
- Permit internal arithmetic at `0.1 ms` precision so odd `cvc_reference` values can produce stable half-beat synchronization.
- Require documentation that explains the common half-beat mechanism for mono timing and `_ophone.txt` timing.
- Require tests that pin mode-aware and stream-aware synchronization behavior explicitly.

### Not Included

- Changing how upstream prosody chooses accent locations for `mono` versus `bi`.
- Changing the semantic meaning of `cvc_reference` itself.
- Replacing the existing pause-band ranges.
- Removing drift reporting entirely from phonetizer artifacts.
- Changing the original-stream derivation rule from `_tilde`.
- Changing the pause-governed intonation goal introduced by `CR-079`.
- Removing original-stream synchronization altogether.

---

## Current Behavior

The active phonetizer currently uses `cvc_reference` as the synchronization foot for multiple behaviors, with no mora-mode distinction inside the phonetizer runtime and no half-beat override for the original stream.

Verified current behavior:

- `_tilde` frontmatter already carries `metadata.options.mora_mode`, for example `mora_mode: "mono"` in the mono demo artifact.
- `realize_phone_streams(..., input_frontmatter)` already receives the input frontmatter, but the runtime timing logic does not currently derive an active beat from `mora_mode`.
- `_timing_refs()` derives one-, two-, and three-mora references from `cvc_reference`, but beat-sensitive pause and drift logic still uses raw `cvc_reference` directly.
- `_preferred_pause_target()` enumerates integer multiples of `cvc_reference` inside the short and long pause bands.
- `_pause_duration_and_drift()` computes mini-pause recovery and pause discharge against `cvc_reference`-based targets.
- `_maybe_insert_mini_pause()` tries to close either `abs(drift)` or `abs(drift - cvc_reference)` and therefore assumes a full-`cvc_reference` beat cycle.
- ordinary long-vowel correction also works against drift values created by that same beat model.

The original stream currently follows the same full-beat recovery logic as the accentuated stream except that accent-driven extension is disabled. In particular, `_ophone.txt` today still synchronizes on `cvc_reference` rather than on `0.5 * cvc_reference`.

That full-beat original-stream synchronization is the behavior this CR changes.

---

## Proposed Change

Adopt the following contract.

### 1. Derive synchronization basis from stream type and `mora_mode`

The phonetizer must read `metadata.options.mora_mode` from the input frontmatter supplied with the `_tilde` artifact.

The runtime timing layer must derive a synchronization basis as follows:

- accentuated stream with `mora_mode=bi` -> synchronization basis = `cvc_reference`
- accentuated stream with `mora_mode=mono` -> synchronization basis = `0.5 * cvc_reference`
- original stream in `_ophone.txt` -> synchronization basis = `0.5 * cvc_reference`

If `mora_mode` is missing, the implementation may fall back to the historical bimoraic beat only as a compatibility fallback. The preferred and expected path is to consume the explicit frontmatter value propagated from upstream prosody.

This synchronization basis is a timing-control quantity. It does not redefine the meaning of `cvc_reference` as the heavy-syllable reference used elsewhere in the timing model.

### 2. Apply the synchronization basis to beat-aware synchronization behaviors

Every phonetizer behavior that currently synchronizes against a repeating `cvc_reference` beat must instead synchronize against the derived synchronization basis.

This includes at minimum:

- exact target choice inside short-pause bands
- exact target choice inside long-pause bands
- mini-pause insertion and discharge target selection
- drift normalization or branch-folding that currently wraps by `cvc_reference`
- ordinary long-vowel drift correction behavior insofar as it uses drift values computed relative to the repeating beat

For the accentuated stream in `mora_mode=mono`, the result must be that pause targeting and mini-pause recovery operate on one-mora beats rather than two-mora beats.

For the original stream in `_ophone.txt`, the result must be that synchronization also operates on one-mora beats rather than full `cvc_reference` beats.

### 3. Use a common half-beat mechanism for mono and `_ophone.txt`

The half-beat synchronization mechanism used for mono timing and for `_ophone.txt` should be designed in common.

That common mechanism should cover at minimum:

- half-beat candidate generation inside pause bands
- half-beat drift wrapping or normalization
- half-beat mini-pause discharge logic
- half-beat long-vowel drift correction logic

The original stream is therefore not a relaxed no-sync branch. It remains synchronized, but its synchronization basis follows the mono-style half beat.

### 4. Allow `0.1 ms` internal precision for odd `cvc_reference`

To support odd `cvc_reference` values, the implementation may compute synchronization targets, drift values, and intermediate duration adjustments at `0.1 ms` precision internally.

Requirements:

- internal synchronization arithmetic may use `0.1 ms` precision
- emitted row durations remain integer milliseconds
- rounding must happen only at stable serialization boundaries, not before synchronization targets are computed

This permission exists specifically so `0.5 * cvc_reference` remains workable when `cvc_reference` is odd.

### 5. Interaction with `CR-079`

`CR-079` remains valid for pause-governed intonation and for documenting the original-stream artifacts, but it must not be interpreted as requiring `_ophone.txt` to keep synchronization on full `cvc_reference` beats.

The updated reading is:

- `_ophone.txt` is still a finalized original-stream artifact
- `_ophone.txt` still receives pause-governed intonation after `CR-079`
- `_ophone.txt` now synchronizes on `0.5 * cvc_reference`

---

## Technical Design

Implementation should introduce a small runtime concept equivalent to `synchronization_basis`, derived from stream type and the input frontmatter.

Minimum design requirements:

- read `mora_mode` from `input_frontmatter['metadata']['options']` when available
- derive `synchronization_basis` from `cvc_reference`, stream type, and `mora_mode`
- use `synchronization_basis` anywhere the solver currently assumes a repeating `cvc_reference` beat for pause targeting, drift wrapping, or mini-pause recovery
- preserve `cvc_reference` itself for heavy-syllable and accent-target calculations unless a later record changes that separately
- permit internal `0.1 ms` precision in synchronization arithmetic before final integer-millisecond emission

Original-stream design requirements:

- keep the original stream inside the synchronized timing path
- switch the original stream from full-beat synchronization to half-beat synchronization
- reuse the same half-beat machinery used for mono timing wherever practical

Likely implementation surfaces:

- `src/akkapros/lib/phonetize.py`
  - frontmatter-aware synchronization-basis resolution helper
  - `_preferred_pause_target()`
  - `_pause_duration_and_drift()`
  - `_normalize_drift_to_nearest_branch()`
  - `_maybe_insert_mini_pause()`
  - `realize_phone_rows()`
  - `realize_phone_streams()` if it must pass stream-aware synchronization mode
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- user-facing phonetizer documentation
- integration and library tests for mono timing and original-stream half-beat synchronization

Documentation requirements:

- explain that upstream prosody `mora_mode` now affects downstream beat alignment in phonetize
- explain that `_ophone.txt` now uses the same half-beat synchronization basis as mono timing
- explain that original and accentuated streams differ by accentuation and synchronization basis selection, not by one being synchronized and the other unsynchronized
- avoid internal governance references in public docs

---

## Files Likely Affected

src/akkapros/lib/phonetize.py  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/fullprosmaker.py  
docs/akkapros/phonetizer-algorithm.md  
docs/akkapros/phonetizer.md  
tests/test_phonetize_lib.py  
tests/test_integration.py  

The final implementation may touch only a subset of these files, but the CR should be executable from this list without requiring broad additional archaeology.

---

## Acceptance Criteria

- [x] The phonetizer reads `mora_mode` from input frontmatter when realizing `_tilde` into phone artifacts.
- [x] In the accentuated stream with `mora_mode=bi`, beat-aware synchronization continues to align to `cvc_reference`.
- [x] In the accentuated stream with `mora_mode=mono`, beat-aware synchronization aligns to `0.5 * cvc_reference`.
- [x] In `_ophone.txt`, synchronization changes from `cvc_reference` to `0.5 * cvc_reference`.
- [x] In the accentuated stream with `mora_mode=mono`, beat-aware pause targeting uses the half-beat basis for choosing exact pause durations inside legal short and long ranges.
- [x] In `_ophone.txt`, beat-aware pause targeting also uses the half-beat basis.
- [x] In the accentuated stream with `mora_mode=mono`, beat-aware mini-pause insertion uses the half-beat basis.
- [x] In `_ophone.txt`, mini-pause and long-vowel drift-correction behavior remain synchronized but use the half-beat basis rather than full `cvc_reference`.
- [x] Internal synchronization arithmetic may use `0.1 ms` precision, while emitted row durations remain integer milliseconds.
- [x] `_ophone.txt` remains a finalized original-stream artifact and is still compatible with the pause-governed intonation work described by `CR-079`.
- [x] Documentation explains both the mono half-beat rule and the `_ophone.txt` half-beat rule.
- [x] Focused library and integration verification pass for mono and original-stream half-beat synchronization behavior.

---

## Risks / Edge Cases

- Some helper logic may silently assume `cvc_reference` is always the repeating beat and miss one of the synchronization paths.
- Mixed assumptions about `cvc_reference` versus active beat could produce inconsistent drift reporting.
- Early integer rounding could distort half-beat synchronization when `cvc_reference` is odd.
- Compatibility fallback for missing `mora_mode` must be specified narrowly so tests do not become ambiguous.

---

## Testing Strategy

Focused library tests:

- verify active beat resolution from input frontmatter for `bi` and `mono`
- verify mono beat selection changes exact pause targeting inside the legal short and long pause bands
- verify mono beat selection changes mini-pause eligibility or inserted duration behavior where appropriate
- verify original-stream synchronization basis changes from full beat to half beat
- verify original-stream pause targeting, mini-pause behavior, and long-vowel correction all use the half-beat basis
- verify odd `cvc_reference` values remain stable under internal `0.1 ms` synchronization arithmetic

Integration tests:

- verify representative mono pipeline artifacts differ from equivalent bi artifacts in beat-aligned pause and recovery behavior
- verify `_ophone.txt` changes from full-beat to half-beat synchronization behavior
- verify `_phone.txt` still follows beat-aware timing with `mono` using a half-`cvc_reference` basis
- verify odd-`cvc_reference` scenarios remain consistent after serialization rounding

Documentation verification:

- confirm the user-facing docs explain the new beat selection rule and the shared half-beat mechanism clearly
- run any focused doc verification required by the touched doc surface

---

## Rollback Plan

Revert the active-beat derivation and restore the historical `cvc_reference` beat everywhere if the change destabilizes synchronization.

Revert the `_ophone.txt` half-beat override separately if needed, while keeping the mono half-beat work isolated for further review.

---

## Related Issues

- `CR-039` for original-stream derivation
- `CR-040` for duration realization on prebuilt rows
- `CR-047` for phonetizer pause handling
- `CR-059` for mini-pause recovery and discharge
- `CR-079` for original-stream intonation and artifact documentation

---

## Tasks

### Implementation

- [x] Add frontmatter-driven synchronization-basis resolution from `mora_mode` and stream type.
- [x] Switch beat-aware synchronization from raw `cvc_reference` to the derived synchronization basis where required.
- [x] Reuse the half-beat mechanism for mono timing and `_ophone.txt` timing.

### Tests

- [x] Add or update focused library tests for mono beat and `_ophone.txt` half-beat synchronization.
- [x] Add or update integration coverage for mono and original-stream synchronization artifacts.

### Documentation

- [x] Update user-facing phonetizer docs for mora-mode-aware beat alignment.
- [x] Update user-facing phonetizer docs for `_ophone.txt` half-beat synchronization.

### Review

- [x] Verify acceptance criteria.
- [x] Confirm compatibility with `CR-079`.

---

## Implementation Blockers

No blockers known at draft time.
