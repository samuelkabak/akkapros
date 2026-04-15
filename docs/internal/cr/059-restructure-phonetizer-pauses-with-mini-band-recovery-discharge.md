---
cr_id: CR-059
status: Done
priority: High
impact: Mutative
created: 2026-04-14
updated: 2026-04-15
implements: 'ADR-046, REQ-033, REQ-031'
---

# Change Request: Clarify Phonetizer Duration and Drift Assignment with Hard Short Vowels

## Summary

Rewrite the active CR-059 so it describes the phonetizer timing algorithm as a
timeline solver organized by `cvc_reference` beat units, explicitly extracts the
currently implemented solver, and states the requested new solver as a small,
targeted change.

The requested change is narrow. The phonetizer keeps the same syllable classes,
the same `cvc_reference` beat mapping, the same drift-cursor model, the same
accentuation increment of `0.5 * cvc_reference`, and the same pause-band idea,
including the mini-pause recovery concept already introduced in this CR family.
The change is that short vowels cease to be a flexible recovery space. They
become hard anchors like singleton consonants. Long vowels remain flexible
inside their legal range, pauses remain flexible inside their legal ranges, and
the default `drift_tolerance` changes to `0`.

This rewrite also requires the CR itself to contain both algorithms side by
side, with an explicit comparison, so implementers and reviewers can see
exactly what changed and what did not.

---

## Motivation

The current internal records do not frame this change clearly enough.

Repository inspection on 2026-04-15 shows the following live Phase 2 behavior in
`src/akkapros/lib/phonetize.py`:

- `realize_phone_rows()` still solves syllables and pauses against a running
  signed `drift_cursor`.
- `_shape_reference()` still maps the non-accentuated syllable targets to
  `CV = 0.5 * cvc_reference`, `CVV = 1.0 * cvc_reference`,
  `CVC = 1.0 * cvc_reference`, and `CVVC = 1.5 * cvc_reference`, then adds
  `0.5 * cvc_reference` for accentuated shapes.
- `_apply_vowel_correction()` still treats the syllable nucleus as the ordinary
  post-drift recovery space.
- `_vowel_bounds()` currently allows short vowels to move inside the short
  perceptual band, which by default is `40 .. 122` ms.
- `_pause_duration_and_drift()` still realizes short and long pauses as legal
  pause-band durations that try to discharge running drift.

That live behavior matches the older stability-first model from
[REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md):
drift first, then vowel correction, then policy branch. But your requested
change is more specific than that general statement. You want the current solver
to be preserved except for one important narrowing:

- consonants remain hard anchors
- short vowels also become hard anchors
- long vowels remain the syllable-internal flexible recovery space
- pauses remain the inter-unit flexible recovery space
- mini pauses remain available as non-punctuation recovery pauses
- `drift_tolerance` defaults to `0`

Without an explicit old-versus-new statement in the CR, the requested change is
too easy to misread as either a broad redesign or a pause-only change. It is
neither.

---

## Scope

### Included

- Restate the phonetizer timing model as a timeline divided into
  `cvc_reference` units.
- Preserve the existing syllable inventory used by Phase 2:
  non-accentuated `CV`, `CVC`, `CVV`, `CVVC` and accentuated `C:V`, `CVC:`,
  `CVV:`, `CVV:C`.
- Preserve the current entry condition that every syllable begins with a
  consonant or pseudo-consonant in phonetizer timing terms, including hiatus
  and vowel-transition rows.
- Preserve the grouping model: syllables belong to words, words belong to
  merged units, `&` marks algorithmic merges, `+` marks user-declared merges,
  and a single standalone word is also a merged unit.
- Preserve the distinction between punctuation-owned short and long pauses and
  phonetizer-inserted mini pauses.
- Extract the currently implemented solver into an explicit algorithm statement
  inside this CR.
- State the requested new solver as an explicit algorithm statement inside this
  CR.
- Add a comparison table that shows exactly what changes and what stays the
  same.
- Change the active solver contract so short-vowel duration is never altered by
  ordinary drift recovery.
- Preserve long-vowel flexibility within legal bounds.
- Preserve pause-band flexibility within legal bounds.
- Preserve the accentuation increment model: accentuation still adds exactly
  `0.5 * cvc_reference` and still does not use short vowels as its target.
- Preserve the mini-pause recovery idea already introduced in this CR family:
  when no punctuation-owned pause follows a merged unit boundary and the stream
  is ahead of the beat by at least the configured mini threshold, the
  phonetizer may insert a mini pause to bring drift as close as possible to
  zero.
- Change the default `drift_tolerance` to `0` while retaining the parameter for
  now.
- Require the implementation shape to keep `drift_tolerance` easy to remove in
  a later follow-up.
- Require public phonetizer algorithm docs to explain the final algorithm
  clearly, especially in `docs/akkapros/phonetizer-algorithm.md`.

### Not Included

- Replacing the two-phase-plus-intonation architecture.
- Changing the syllable inventory or beat mapping itself.
- Changing the accentuation-distribution policy family.
- Removing `drift_tolerance` in this CR.
- Redesigning metrics output, pause-metrics tables, or unrelated downstream
  reporting surfaces.
- Reopening punctuation classification or pause-type precedence beyond the mini
  recovery rule already in scope.

---

## Current Behavior

The currently implemented Phase 2 solver can be stated as follows.

### 1. Stable timing context at phonetizer entry

- The row stream has already been built.
- Every timing syllable begins with a consonant or pseudo-consonant.
- The active non-accentuated syllable inventory is `CV`, `CVC`, `CVV`, `CVVC`.
- The active accentuated syllable inventory is `C:V`, `CVC:`, `CVV:`, `CVV:C`.
- Words may be standalone or part of merged units.
- Spaces and punctuation separate merged units.
- Punctuation and line breaks create voluntary short or long pauses.

### 2. Extracted current algorithm

The live code in `src/akkapros/lib/phonetize.py` currently behaves as this
algorithm:

1. Partition the row stream into syllables and pauses.
2. For each non-pause syllable, assign baseline onset anchors first, optional
   coda anchors second, and nucleus anchor third.
3. If a coda is followed by the same onset consonant, pre-assign the next onset
   through the geminate rule.
4. If the stream is accentuated and the syllable carries accentuation, add
   exactly `0.5 * cvc_reference` using the configured accentuation-distribution
   policy. This augmentation targets accentable consonants or long-vowel space,
   not short vowels.
5. Compute the syllable target `shape_ref` from the `cvc_reference` timeline.
6. Compute the post-assignment drift as:

   ```text
   drift_after_assignment = drift_cursor + (realized_total - shape_ref)
   ```

7. Apply ordinary vowel correction inside the legal bounds of the nucleus
   category.
   - For a short vowel, the current implementation allows motion inside the
     short-vowel band.
   - For a long vowel, the current implementation allows motion inside the
     long/very-long band.
8. If the remaining absolute drift still exceeds `drift_tolerance`, branch by
   `drift_policy`.
   - `strict`: fail.
   - `extensible`: keep the remaining drift and continue.
9. When a punctuation-owned pause is reached, choose a legal duration inside
   the pause band that tries to discharge drift toward the nearest beat.
   - Short pauses may leave residual drift.
   - Long pauses may absorb the remaining drift completely.

### 3. Consequence of the current implementation

In the current solver, short vowels are still part of the ordinary recovery
space.

With the default example values:

- `cvc_reference = 305`
- `closure/onset = 70`
- `short_vowel = 85`
- `closure/coda = 70`
- `drift_tolerance = 12`
- `long_min = 123`, so the short-vowel ceiling is `122`

For a `CVC` syllable realized initially as `70 + 85 + 70 = 225 ms`, the target
is `305 ms`, so the stream is `80 ms` ahead of the beat:

```text
drift = 225 - 305 = -80 ms
```

Under the current solver, `12 ms` may remain as tolerated drift, and the
remaining `68 ms` is offered to vowel correction. Since the short vowel can be
extended from `85` to `122`, the solver uses `37 ms` of that room and emits:

```text
70 + 122 + 70 = 262 ms
```

The syllable is still `43 ms` ahead of the beat, so the stream carries
`-43 ms` of drift forward.

That is precisely the behavior being narrowed by this rewrite.

---

## Proposed Change

Adopt the following contract.

### 1. Unchanged timing foundation

The following remain unchanged:

- the timeline is organized in `cvc_reference` beat units
- `CV = 0.5 * cvc_reference`
- `CVC = 1.0 * cvc_reference`
- `CVV = 1.0 * cvc_reference`
- `CVVC = 1.5 * cvc_reference`
- accentuation still adds exactly `0.5 * cvc_reference`
- words and merged units remain the phrasal grouping layer
- punctuation-owned pauses remain short or long voluntary pauses
- mini pauses remain non-punctuation recovery pauses

### 2. Requested new algorithm

The requested solver is the current solver with one narrow but important
reclassification of recovery space.

Algorithm B, the requested solver, is:

1. Partition the row stream into syllables and pauses.
2. For each non-pause syllable, assign baseline onset anchors first, optional
   coda anchors second, and nucleus anchor third.
3. If a coda is followed by the same onset consonant, pre-assign the next onset
   through the geminate rule.
4. If the stream is accentuated and the syllable carries accentuation, add
   exactly `0.5 * cvc_reference` using the configured accentuation-distribution
   policy. This part remains unchanged.
5. Compute the syllable target from the `cvc_reference` timeline.
6. Compute post-assignment drift in the same way as before.
7. Apply ordinary recovery with this new legality split:
   - singleton consonants remain hard
   - short vowels also remain hard
   - long vowels remain flexible within their legal range
   - pauses remain flexible within their legal ranges
8. If the current unit is a punctuation-owned short or long pause, choose the
   legal pause duration that brings the stream as close as possible to the beat.
   - If zero drift is reachable inside the band, realize that pause at the
     beat-aligned point.
   - If zero drift is not reachable inside the band, clamp inside the band and
     carry the remainder forward.
9. If the current position is after a merged unit boundary, there is no
  punctuation-owned pause, and the stream is ahead of the beat by at least the
  mini threshold, the phonetizer may insert one mini pause inside the
  configured mini band.
   The inserted mini pause shall choose the legal mini-band duration that brings
   drift as close as possible to zero.
10. `drift_tolerance` remains a parameter, but its default is `0`. The active
    default behavior therefore becomes immediate residual-drift accounting
    rather than tolerance-band hiding.

### 3. Short-vowel rule

The new hard rule is:

- Ordinary drift recovery shall never modify a short vowel.

This means:

- `CV` and `CVC` syllables may finish ahead of or behind the beat and carry
  that mismatch in drift.
- Their recovery must come later through a long vowel, a punctuation-owned
  pause, a mini pause, or retained drift.
- The phonetizer shall not use the short-vowel perceptual band as ordinary
  local repair space anymore.

### 4. Worked comparison example

Using the same example values as above:

- `CVC` initial realization: `70 + 85 + 70 = 225 ms`
- target: `305 ms`
- initial drift: `-80 ms`

#### Old solver

- Allows short-vowel correction.
- Extends the vowel from `85` to `122`.
- Emits `262 ms`.
- Carries `-43 ms` forward.

#### New solver

- Does not alter the short vowel.
- Keeps the syllable at `225 ms`.
- With default `drift_tolerance = 0`, carries the full `-80 ms` forward.
- Later compensation must come from a long vowel, a punctuation-owned pause, a
  mini pause, or continued drift.

### 5. Mini-pause recovery rule

The mini pause introduced in this CR family remains active and is reinterpreted
inside the new solver as follows.

- Mini pauses are not part of the lexical phoneme structure.
- They are not punctuation-owned and are not voluntary clause pauses.
- They exist only as phonetizer-inserted drift-recovery gaps.
- They may be inserted only after a merged unit boundary where no punctuation-
  owned pause already exists.
- They use the configured `mini.min .. mini.max` band.
- They are triggered when `drift_cursor <= -pauses.mini.min` unless a later
  record introduces a separate trigger key.

### 6. Accentuation model remains unchanged

This CR does not change the accentuation model.

- Every accentuated syllable still gains `0.5 * cvc_reference`.
- That increment is still realized through accentable consonants or long-vowel
  duration according to the configured accentuation-distribution policy.
- Short vowels are not used as accentuation targets.

### 7. Refactorability requirement

Although `drift_tolerance` remains in scope for this CR, the implementation
shape required by this specification must keep it isolated enough that a later
record can remove it cleanly without having to redesign the whole solver.

That means the implementation should treat tolerance as a narrow policy layer,
not as the conceptual core of the timing algorithm.

---

## Technical Design

### Current-versus-new comparison

| Topic | Current extracted solver | Requested solver |
| --- | --- | --- |
| Timeline reference | `cvc_reference` | unchanged |
| Non-accentuated classes | `CV`, `CVC`, `CVV`, `CVVC` | unchanged |
| Accentuated classes | `C:V`, `CVC:`, `CVV:`, `CVV:C` | unchanged |
| Consonants | hard anchors | unchanged |
| Short vowels | flexible recovery space inside short-vowel bounds | hard anchors, never used by ordinary drift recovery |
| Long vowels | flexible recovery space | unchanged |
| Pauses | flexible recovery space inside legal band | unchanged |
| Mini pause | CR-059 family feature | retained |
| Accent increment | `+ 0.5 * cvc_reference` | unchanged |
| Default `drift_tolerance` | `12` in live code | `0` |
| Future tolerance removal | not stated clearly | implementation must remain easy to refactor |

### Components likely affected by implementation

- `src/akkapros/lib/phonetize.py`
- `src/akkapros/config/default.yaml`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `docs/akkapros/phonetizer-algorithm.md`
- related phonetizer user docs and tests

Recommended implementation direction:

- isolate ordinary nucleus correction by vowel class instead of one generic
  vowel-correction path
- exclude short-vowel rows from ordinary drift correction
- leave long-vowel correction and pause correction intact
- introduce the mini-pause insertion path at post-merged-unit boundaries only
- set the default `drift_tolerance` to `0`
- keep tolerance handling structurally separable for later removal

---

## Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/config/default.yaml`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/cli/fullprosmaker.py`
`tests/test_phonetize_lib.py`
`tests/test_config_support.py`
`tests/test_selftests_cli.py`
`tests/test_selftests_lib.py`
`tests/test_integration.py`
`docs/akkapros/phonetizer-algorithm.md`
`docs/akkapros/phonetizer.md`
`docs/akkapros/configuration.md`

---

## Acceptance Criteria

- [x] Given CR-059 is reviewed, when its algorithm sections are read, then it
      contains one extracted current algorithm and one requested new algorithm
      written as separate, explicit solver descriptions.
- [x] Given CR-059 is reviewed, when its comparison section is read, then it
      states directly that the change is the reclassification of short vowels
      from flexible recovery space to hard anchors.
- [x] Given the active solver is implemented under this CR, when ordinary drift
      recovery is applied to a `CV` or `CVC` syllable, then the short vowel is
      not lengthened or shortened.
- [x] Given the active solver is implemented under this CR, when ordinary drift
      recovery is applied to a `CVV` or `CVVC` syllable, then the long vowel may
      still move inside its legal range.
- [x] Given the active solver is implemented under this CR, when a punctuation-
      owned short or long pause is realized, then the pause duration is chosen
      inside its legal band so the resulting drift is as close to zero as that
      band allows.
- [x] Given the active solver is implemented under this CR, when a merged unit
  ends without punctuation and `drift_cursor <= -pauses.mini.min`, then one
  mini pause may be inserted to bring drift as close to zero as the mini
  band allows.
- [x] Given the default phonetize timing config is inspected, when
      `drift_tolerance` is read, then the active default is `0`.
- [x] Given the active solver is implemented under this CR, when accentuation is
      realized, then the solver still adds exactly `0.5 * cvc_reference` and
      does not use short vowels as accentuation targets.
- [x] Given the phonetizer algorithm docs are updated during implementation,
      when `docs/akkapros/phonetizer-algorithm.md` is read, then it explains the
      timeline model, the hard-short-vowel rule, the long-vowel and pause
      recovery space, and the mini-pause rule clearly.
- [x] Given implementation code is reviewed, when tolerance handling is traced,
      then `drift_tolerance` remains isolated enough to be removable by a later
      narrow follow-up.

---

## Risks / Edge Cases

- Hardening short vowels will increase the amount of drift carried forward out
  of `CV` and `CVC` syllables.
- Mini-pause insertion must not cascade repeatedly across the same local
  boundary.
- Lowering `drift_tolerance` to `0` will change emitted timings and may expose
  more visible drift in diagnostics and tests.
- If long-vowel and pause recovery are not kept clearly separated from the new
  hard-short-vowel rule, implementation may accidentally preserve the old
  behavior under a new name.
- Public docs may incorrectly describe mini pauses as punctuation pauses unless
  the distinction is stated explicitly.

---

## Testing Strategy

Unit tests:

- short-vowel syllables do not change nucleus duration during ordinary drift
  recovery
- long-vowel syllables still permit legal nucleus correction
- punctuation-owned pauses minimize drift inside their bands
- mini pauses are inserted only at eligible non-punctuation merged-unit
  boundaries
- default `drift_tolerance` is `0`
- accentuation still adds `0.5 * cvc_reference` without targeting short vowels

Integration tests:

- representative `_phone.txt` and `_ophone.txt` outputs show increased carried
  drift on `CV`/`CVC` shapes and later recovery through long vowels or pauses
- public phonetizer docs and config help align with the new timing contract

Manual verification:

- inspect a worked `CVC` example and confirm the solver no longer extends the
  short vowel for ordinary drift recovery

---

## Rollback Plan

Revert the implementation that hardens short vowels and restore the earlier
generic nucleus-correction behavior.

Because this CR changes emitted timing behavior rather than only renaming
parameters, rollback would restore the earlier local solver semantics as well as
the earlier default tolerance.

---

## Related Issues

- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
- [ADR-041](../adr/041-stability-first-phonetizer-timing-control-and-validation-boundary.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- [ADR-046](../adr/046-phonetizer-mini-band-and-row-derived-pause-reporting.md)
- [REQ-033](../req/033-phonetizer-pause-bands-and-pause-metrics-reporting.md)

---

## Tasks

### Implementation

- [x] Exclude short vowels from ordinary drift-correction logic
- [x] Preserve long-vowel and pause-band correction paths
- [x] Add or retain mini-pause insertion at eligible merged-unit boundaries
- [x] Change default `drift_tolerance` to `0`
- [x] Keep tolerance handling isolated for later removal

### Tests

- [x] Add unit coverage for hard short vowels
- [x] Add unit coverage for long-vowel recovery and pause recovery
- [x] Add unit coverage for mini-pause eligibility
- [x] Update config and integration tests for the new default tolerance

### Documentation

- [x] Update public phonetizer timing documentation
- [x] Rewrite `docs/akkapros/phonetizer-algorithm.md` around the clarified
      timeline model and old-vs-new contrast

### Review

- [x] Verify the implementation against the extracted current algorithm and the
      requested new algorithm in this CR

---

## Implementation Blockers

Leave empty unless implementation discovers a new blocker.

---

## Notes

- This CR is intentionally specification-only. Implementation is deferred.
- The public-doc update requested by the user is part of the implementation
  follow-through, but this Internal Spec Writer task does not modify files
  outside `docs/internal/`.
- Repository grounding for the extracted current solver came from inspection of
  `src/akkapros/lib/phonetize.py`, especially `_shape_reference()`,
  `_vowel_bounds()`, `_apply_vowel_correction()`, `_pause_duration_and_drift()`,
  and `realize_phone_rows()`.
