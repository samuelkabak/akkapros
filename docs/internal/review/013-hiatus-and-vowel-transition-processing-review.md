---
review_id: review-013
status: Done
created: 2026-04-19
updated: 2026-04-19
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  src/akkapros/lib/phonetize.py,
  demo/akkapros/lexlinks/construct-demo.yaml,
  and the live phonetizer timing-model behavior for hiatus and vowel-transition rows.
---

# Code and Project Review — Hiatus and Vowel Transition Processing

## 1. Executive Summary

The current phonetizer implementation treats hiatus and vowel-transition markers as special consonant-like rows with two distinct timing regimes. In unstressed singleton use, they take their duration directly from the dedicated `special_realization` config values. In accentuated onset use (`C:V`), they keep their special singleton anchor as the starting point but inherit the timing class of their phonetic correspondence for the runtime upper ceiling: hiatus follows the closure class and vowel transition follows the sonorant class. The important limitation is that accentuation does not promote them into the ordinary class onset-to-gemination band. The runtime gives them the class-correct maximum, but not the class-correct lower bound.

## 2. Architecture Assessment

### 2.1 Strengths

- The row model distinguishes hiatus and vowel-transition markers explicitly rather than silently treating them as ordinary lexical consonants.
- Runtime timing-class assignment is coherent with phonetic interpretation: hiatus rows are handled as closure-like and vowel-transition rows are handled as sonorant or glide-like.
- The config contract makes the singleton special realizations explicit and auditable through dedicated keys.
- The runtime and verifier are aligned on the fact that singleton hiatus and vowel-transition realizations are lighter than ordinary onset and coda anchors.

### 2.2 Areas for Improvement

- The implementation does not currently promote accentuated hiatus or accentuated vowel-transition rows into the ordinary singleton-to-geminate range of their correspondence class.
- The distinction between timing class inheritance and anchor inheritance is subtle and easy to misread without a dedicated note.
- User-facing phonetizer docs should eventually explain that accentuated special rows inherit the class upper ceiling but keep the special singleton anchor unless the algorithm is changed later.

## 3. Code Quality Assessment

- Symbol classification maps hiatus markers to category `C`, type `H`, and vowel-transition markers to category `C`, type `T` in `src/akkapros/lib/phonetize.py`.
- Timing-class dispatch maps `H` with ordinary closures and `T` with ordinary sonorants. This is what makes later runtime ceilings class-correct.
- Singleton anchor selection is explicit: `H` uses `consonants.closure.special_realization.hiatus`, and `T` uses `consonants.sonorant.special_realization.vowel_transition`.
- Accent-shape analysis identifies stressed onset cases as `C:V`, so special rows in onset position can receive accent increment as onset-bearing consonant rows.
- Accent increment limits use `_consonant_maximum()` for the primary accent segment, so `H` inherits closure `gemination_max` and `T` inherits sonorant `gemination_max`.
- No runtime rule forces accentuated `H` or `T` to start from ordinary class onset, cross `geminate_min`, or target the ordinary class `geminate` value. They begin from the special singleton anchor and may extend upward only as far as the class-local maximum and available increment allow.

## 4. Documentation Assessment

This review documents the current implementation contract explicitly.

### 4.1 Hiatus and Vowel Transition Processing

#### Row Typing

- Hiatus markers are classified as consonant rows of type `H`.
- Vowel-transition markers are classified as consonant rows of type `T`.
- The emitted realizations are still phonetic correspondences rather than abstract placeholders: hiatus has its own emitted realization path, and vowel-transition rows resolve contextually to glide-like outputs such as `WA` or `YI`.

#### Singleton Unstressed Timing

- A singleton hiatus row takes its duration directly from `consonants.closure.special_realization.hiatus`.
- A singleton vowel-transition row takes its duration directly from `consonants.sonorant.special_realization.vowel_transition`.
- The verifier requires both special singleton values to stay above `segmental_floor` and below both the ordinary onset and coda anchors of their timing class.

#### Accentuated `C:V` Timing

- If a hiatus or vowel-transition row is the stressed onset of a syllable, the syllable is analyzed as accent shape `C:V`.
- In that case, the special row participates as the primary accent segment and can receive accent increment.
- The runtime ceiling for that increment is inherited from the timing class of the row's phonetic correspondence:
  - hiatus uses the closure class `perception_limits.gemination_max`
  - vowel transition uses the sonorant class `perception_limits.gemination_max`

#### What Is Not Implemented

The current implementation does not do the following:

- It does not replace the special singleton anchor with the ordinary class onset anchor when the row is accentuated.
- It does not force accentuated hiatus into the full closure onset-to-gemination range.
- It does not force accentuated vowel transition into the full sonorant onset-to-gemination range.
- It does not require accentuated special rows to reach `geminate_min`.
- It does not force accentuated special rows toward the ordinary class `geminate` target.

The effective current stressed range is therefore:

- hiatus: from `special_realization.hiatus` upward to closure `gemination_max`
- vowel transition: from `special_realization.vowel_transition` upward to sonorant `gemination_max`

It is not:

- hiatus: from closure `onset` upward to closure `gemination_max`
- vowel transition: from sonorant `onset` upward to sonorant `gemination_max`

## 5. Research / Functional Assessment

Functionally, the implementation is internally consistent.

- It preserves the idea that hiatus and vowel-transition rows are special lightweight singleton realizations when unstressed.
- It also preserves the idea that accentuated special rows should inherit the timing class of their phonetic correspondence for runtime extension.
- The current model therefore captures the upper-bound side of phonetic correspondence but not the full lower-bound side.

This means the implementation supports the following interpretation:

- unstressed special rows are special and light
- stressed special rows are still special at baseline, but they may expand within the runtime ceiling of the corresponding consonant class

If the intended phonological contract is stronger than that, the gap is not in accidental behavior but in a specific unimplemented rule: promotion of accentuated special rows from special singleton anchor to ordinary class onset or ordinary class geminate band.

## 6. Process and Engineering Practices

- The implementation is auditable because the relevant behavior is localized in a small set of helpers for row typing, anchor selection, accent-shape analysis, and accent increment limits.
- The verifier already encodes the singleton-lightness assumption, which reduces the risk of accidental config drift away from the intended special-row semantics.
- The main engineering need is documentation precision, not a corrective patch, given that the current implementation has now been explicitly accepted.

## 7. Recommendations (Priority Order)

1. High: Preserve this current behavior as the active implementation contract unless and until a later CR explicitly promotes accentuated special rows into the full ordinary onset-to-gemination band.
2. High: When a user-facing phonetizer document is updated outside internal-doc-only mode, copy the substance of Section 4.1 directly so the behavior is explained without requiring code reading.
3. Medium: If future work wants stronger phonetic correspondence for accentuated special rows, specify the change explicitly as a new contract rather than treating the current behavior as a bug.
4. Medium: If that future change is made, add focused tests that distinguish singleton special anchors from accentuated ordinary-class lower bounds.

## 8. Summary Verdict

The current phonetizer implementation treats hiatus and vowel-transition rows as special singleton realizations that inherit the correct consonant class for accentuated runtime ceilings, but it does not currently promote them into the ordinary onset-to-gemination range of that class when stressed.
