---
cr_id: CR-079
status: Done
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-19
implements: 'CR-039, CR-045, CR-050'
---

# Change Request: Add Pause-Governed Intonation to ophone and Document Original-Stream Production

## Summary

Update the phonetizer contract so the original stream in `_ophone.txt` receives phrase-level and punctuation-governed intonation, even though it remains deaccented and does not receive stress accentuation.

This CR also makes the `_ophone` production contract explicit in one place. `_ophone` is not a structure-only or pre-timing snapshot. It is the finalized original-stream phone artifact derived from the `_tilde` input by removing accent markers and replacing internal merge `&` with space, then running the phonetizer's original-stream realization pipeline through finalized row output and final intonation assignment. The same clarification must be reflected in the user-facing documentation, including how `_ombrola.pho` is derived from `_ophone`.

This CR narrows the active `CR-050` intonation contract. `CR-050` made intonation assignment effectively contingent on the accentuated path. After this change, pause-governed intonation is shared by both finalized phone streams, while stress intonation remains exclusive to the accentuated stream.

This CR does not freeze the exact original-stream duration or beat-following policy. A newer directly relevant record may narrow how `_ophone` handles pause targeting, mini-pause insertion, drift discharge, or other synchronization behavior without changing the intonation and artifact-documentation goals defined here.

---

## Motivation

- Behavioral correction to the active phone-stream contract
- Documentation gap around `_ophone` and `_ombrola` production
- Alignment between original and accentuated outputs
- Removal of an implementation asymmetry that currently conflates phrase intonation with accentuation

Current live behavior makes `_ophone` fully duration-realized and pause-aware, but it suppresses all non-neutral intonation because the intonation pass returns early when the stream is non-accentuated. That leaves `_ophone` inconsistent with its own punctuation structure and with its corresponding `_ombrola.pho` output contract.

The original stream should remain original only in the narrow sense that accent marks are removed and accent-driven duration extension is absent. Phrase-level intonation from punctuation and pause type is a separate operation and must still apply to the original stream.

---

## Scope

### Included

- Update the phonetizer contract so `_ophone.txt` receives pause-governed intonation.
- Preserve the existing rule that `_ophone.txt` does not receive stress intonation from accent-bearing syllables.
- Define `_ophone.txt` explicitly as the finalized original-stream phone artifact rather than a structure-only or pre-timing artifact.
- Define `_ombrola.pho` explicitly as a serialization of the finalized `_ophone` rows.
- Require user-facing documentation that explains how `_ophone`, `_phone`, `_ombrola`, and `_mbrola` are produced and how they differ.
- Require documentation to state that phrase and punctuation intonation is independent from accentuation.
- Require tests that pin the new `_ophone` intonation behavior explicitly rather than relying on mutable defaults.

### Not Included

- Adding stress accentuation to `_ophone.txt`.
- Changing how the original stream is derived from `_tilde`.
- Redesigning the duration solver, drift model, or pause-band model beyond what is required to apply shared pause intonation.
- Redesigning the MBROLA serializer beyond the intonation consequences of the new `_ophone` contract.
- Converting `_ophone` into a debug or pre-pass artifact.

---

## Current Behavior

The live phonetizer already builds two row streams from `_tilde`:

- original stream: remove `~`, replace `&` with space
- accentuated stream: keep the accentuated `_tilde` content

Both streams then proceed through row construction and duration realization. `_ophone.txt` therefore already carries the original stream's own duration, drift, pause, mini-pause, and frontmatter diagnostics.

Verified current behavior from the active implementation:

- `_ophone.txt` is derived from `derive_original_tilde_text()` by removing `~` and converting `&` to a space.
- The original stream is passed through `build_phone_rows()`, `realize_phone_rows(..., allow_accentuation=False)`, and then serialized as `_ophone.txt`.
- The accentuated stream is passed through `build_phone_rows()`, `realize_phone_rows(..., allow_accentuation=True)`, and then serialized as `_phone.txt`.
- `_ombrola.pho` is emitted from the finalized original row stream and `_mbrola.pho` is emitted from the finalized accentuated row stream.
- `_ophone.txt` frontmatter currently reports metrics that belong to the original realized stream itself, including post-unit drift, pause counts, mini-pause counts, and drift-tolerance diagnostics.

The current asymmetry is in the intonation pass:

- row intonation is initialized to neutral for all rows
- the intonation function returns immediately for the original stream because `accentuated=False`
- as a result, `_ophone.txt` retains neutral `M0C` on every row
- `_ombrola.pho` therefore emits flat baseline `f0` targets only, even on punctuation-governed phrase boundaries

This means the original stream is fully realized in duration but not fully realized in phrase intonation, even though pause typing and punctuation classification are already available on its finalized rows.

---

## Proposed Change

Adopt the following contract.

### 1. Separate phrase intonation from stress accentuation

Pause-governed and punctuation-governed intonation is independent from accentuation.

After this CR:

- both `_ophone.txt` and `_phone.txt` must receive pause-governed intonation assignments based on finalized pause rows and pause subtypes
- only `_phone.txt` may receive non-pause stress intonation from accent-bearing syllables
- `_ophone.txt` must remain neutral on non-pause syllables unless a pause-governed contour assigns an intonation token to the preceding syllable

This yields the intended split:

- shared across both streams: phrase-final and punctuation-driven intonation
- exclusive to accentuated stream: ordinary stress intonation

### 2. Explicit original-stream artifact contract

`_ophone.txt` is the finalized original-stream phone artifact.

It must be documented and implemented as follows:

1. Start from the accentuated `_tilde` input.
2. Derive original text by:
   - removing `~`
   - converting internal merge `&` to a space
   - preserving the remaining structural material used by the row builder
3. Build original rows from that derived original text.
4. Run the original-stream realization path that produces finalized duration-bearing rows for `_ophone.txt`, with accent-driven extension disabled.
5. Run the intonation pass on the finalized original rows.
6. Apply pause-governed intonation on the original stream in the same way as on the accentuated stream.
7. Do not apply ordinary stress intonation to original-stream syllables solely because the corresponding accentuated stream contains accentuation.

This contract means `_ophone.txt` is not a raw baseline, not a Phase 1 dump, and not a pre-intonation artifact.

The exact timing behavior of that original-stream realization path is outside the scope of this CR and may be narrowed by a newer directly relevant record.

### 3. `_ombrola.pho` contract after this change

`_ombrola.pho` remains a serialization of the finalized `_ophone` rows.

After this CR:

- `_ombrola.pho` must continue to use the original stream's realized durations
- `_ombrola.pho` must reflect pause-governed intonation inherited from `_ophone.txt`
- `_ombrola.pho` must not apply stress intonation that depends on accent-bearing syllables, because `_ophone.txt` remains deaccented

As a result, `_ombrola.pho` is no longer flat baseline `f0` everywhere. It remains original with respect to accentuation, but it is no longer intonationally neutral at punctuation-governed phrase boundaries.

### 4. Documentation requirements

User-facing documentation must include a clear section that explains the production of:

- `_ophone.txt`
- `_phone.txt`
- `_ombrola.pho`
- `_mbrola.pho`

That section must state explicitly:

- `_ophone.txt` and `_phone.txt` are both finalized phone artifacts
- `_ophone.txt` is original only in accentuation terms, not in solver-stage terms
- phrase and punctuation intonation is shared by both streams
- ordinary stress intonation is exclusive to `_phone.txt`
- `_ombrola.pho` is derived from finalized `_ophone` rows and `_mbrola.pho` from finalized `_phone` rows

If diagrams are updated, use the existing generated-flowchart workflow rather than hand-authored Mermaid blocks.

---

## Technical Design

Implementation should update the row-intonation pass so pause-governed contour assignment is executed for both streams, while stress-token assignment remains gated to the accentuated stream.

Minimum behavioral design:

- initialize all rows to neutral intonation as today
- for both streams, inspect finalized pause rows and their pause types
- for both streams, assign the pause-governed intonation token to the pause row and to the preceding syllable according to the existing pause-to-intonation mapping
- for the accentuated stream only, assign ordinary stress intonation to accent-bearing syllables where no pause-final override applies
- preserve the existing rule that punctuation-derived pause type is the cause-side signal for phrase intonation

Likely implementation surfaces:

- `src/akkapros/lib/phonetize.py`
  - `realize_row_intonation()`
  - `_mbrola_rows()` if any serializer adjustment is needed after row-level intonation changes
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- user-facing phonetizer docs describing phone and MBROLA artifacts

Documentation design:

- update the main phonetizer user-facing documentation page that already explains Phase 1, Phase 2, and Phase 3 behavior
- explain the original-stream derivation and finalization process in prose, not only by artifact names
- avoid internal governance references in public docs

Testing design:

- add or update focused library tests for `realize_row_intonation()` so `_ophone` receives pause-governed intonation even when `accentuated=False`
- add or update integration coverage showing that original-stream rows at phrase boundaries are no longer all `M0C`
- add or update MBROLA-focused coverage showing that `_ombrola.pho` reflects punctuation-driven contour changes while still lacking stress-driven contour changes
- keep tests explicit about config values they depend on

---

## Files Likely Affected

src/akkapros/lib/phonetize.py  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/fullprosmaker.py  
docs/akkapros/phonetizer-algorithm.md  
docs/akkapros/phonetizer.md  
scripts/sync_doc_flowcharts.py  
tests/test_phonetize_lib.py  
tests/test_integration.py  
tests/test_doc_flowcharts.py  

The final implementation may touch only a subset of these files, but the CR should be executable from this list without broad additional code archaeology.

---

## Acceptance Criteria

- [x] `_ophone.txt` receives pause-governed intonation on finalized rows.
- [x] `_ophone.txt` does not receive ordinary stress intonation from accent-bearing syllables.
- [x] `_phone.txt` continues to receive both ordinary stress intonation and pause-governed intonation.
- [x] `_ophone.txt` frontmatter remains the diagnostic frontmatter for the original realized stream under the active original-stream timing contract.
- [x] `_ombrola.pho` is derived from finalized `_ophone` rows and reflects the updated original-stream intonation.
- [x] `_ombrola.pho` still does not add accent-driven stress contour that depends on accentuation.
- [x] User-facing documentation explicitly explains how `_ophone.txt`, `_phone.txt`, `_ombrola.pho`, and `_mbrola.pho` are produced and how they differ.
- [x] Any user-facing diagram updates use the repository's existing generated-flowchart workflow.
- [x] Focused library and integration verification pass for the updated intonation contract.

---

## Risks / Edge Cases

- The implementation may accidentally assign ordinary stress intonation to `_ophone.txt` while trying to share pause-governed contours.
- Documentation may continue to describe `_ophone.txt` as if it were a pre-timing or pre-intonation baseline.
- `_ombrola.pho` expectations may need explicit updates in tests and demos because it will no longer be flat baseline `f0` at punctuation-governed boundaries.
- Existing helper logic may implicitly assume that the non-accentuated path is globally intonation-neutral and require small refactoring.

---

## Testing Strategy

Unit or focused library tests:

- verify that a non-accentuated stream with a statement, question, exclamation, or continuation pause receives the corresponding pause-governed intonation token on the preceding syllable and pause row
- verify that a non-accentuated stream without pause-governed contour remains neutral on ordinary non-pause syllables
- verify that accent-bearing stress intonation still appears only in the accentuated stream

Integration tests:

- verify that `_ophone.txt` for a representative pipeline artifact contains non-neutral intonation where punctuation-governed contour is expected
- verify that `_ombrola.pho` is no longer flat baseline `f0` everywhere when the source contains punctuation-governed phrase boundaries
- verify that `_phone.txt` and `_mbrola.pho` retain their current accent-driven contour behavior

Documentation verification:

- run the focused doc-flowchart verification path if diagrams are updated
- confirm the user-facing docs explain original-stream derivation and finalization directly

---

## Rollback Plan

Revert the shared pause-intonation change and restore the previous `_ophone` intonation-neutral behavior if the implementation proves unstable.

If the difficulty is documentation-only, revert the doc changes separately while keeping the behavior change isolated for further review.

---

## Related Issues

- `CR-039` for original-stream derivation
- `CR-045` for phonetizer-owned MBROLA artifacts
- `CR-050` for the current intonation framework that this CR narrows
- `CR-078` for adjacent user-facing phonetizer documentation work
- `CR-080` for mora-mode-aware beat alignment and relaxed original-stream timing

---

## Tasks

### Implementation

- [x] Update the original-stream intonation pass to apply pause-governed contours.
- [x] Preserve stress-only contour assignment as accentuated-stream behavior.
- [x] Ensure `_ombrola.pho` reflects finalized `_ophone` row intonation.

### Tests

- [x] Add or update focused library tests for original-stream pause intonation.
- [x] Add or update integration tests for `_ophone.txt` and `_ombrola.pho`.

### Documentation

- [x] Update user-facing phonetizer documentation for `_ophone` and `_ombrola` production.
- [x] Update generated diagrams if the documentation flow requires them.

### Review

- [x] Verify acceptance criteria.
- [x] Confirm the new CR text is sufficient as the primary implementation prompt.

---

## Implementation Blockers

No blockers known at draft time.
