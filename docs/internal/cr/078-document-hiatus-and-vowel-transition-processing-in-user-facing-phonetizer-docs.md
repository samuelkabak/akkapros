---
cr_id: CR-078
status: Done
priority: Medium
impact: Additive
created: 2026-04-19
updated: 2026-04-19
implements: 'CR-065'
---

# Change Request: Document Hiatus and Vowel Transition Processing in User-Facing Phonetizer Docs

## Summary

Add a clear user-facing documentation section that explains how hiatus and vowel-transition rows are processed by the live phonetizer, including singleton timing, accentuated `C:V` handling, emitted realizations, and the current limit of the implementation.

The section should be added under an explicit title such as `Hiatus and Vowel Transition Processing` in the most appropriate phonetizer documentation page, and it must include a Mermaid flowchart generated through the existing code-derived flowchart workflow rather than a hand-drawn diagram. The new documentation must describe current accepted behavior only. It must not silently "correct" the implementation in prose or imply that accentuated special rows already use the full ordinary onset-to-gemination range.

This CR is documentation-only. It does not request any runtime or test-behavior changes.

---

## Motivation

Why is this change needed?

- User-facing documentation clarity
- Phonetizer behavior transparency
- Public-doc alignment with accepted implementation
- Drift prevention between prose, diagrams, and code

The current implementation for hiatus and vowel-transition rows is subtle. It distinguishes singleton special-realization timing from accentuated onset behavior, and it also distinguishes timing-class inheritance from anchor inheritance. That behavior has now been reviewed and accepted as the active implementation contract, but the explanation exists only in an internal review artifact.

A user-facing phonetizer document should explain this behavior directly so readers do not need to inspect code or internal governance to understand what the live solver does.

---

## Scope

### Included

- Add a user-facing section with an explicit heading such as `Hiatus and Vowel Transition Processing`.
- Explain row typing for hiatus and vowel-transition markers.
- Explain singleton unstressed timing from the dedicated `special_realization` config values.
- Explain accentuated `C:V` behavior for these rows.
- Explain the difference between:
  - emitted phonetic realization,
  - timing-class inheritance, and
  - singleton anchor inheritance.
- State explicitly that accentuated hiatus inherits the closure-class runtime ceiling and accentuated vowel transition inherits the sonorant-class runtime ceiling.
- State explicitly that the current implementation does not promote accentuated hiatus or accentuated vowel transition into the full ordinary onset-to-gemination range of those classes.
- Add a Mermaid flowchart for this behavior using the repository's existing generated-flowchart contract.
- Update any directly adjacent user-facing prose needed to keep the page coherent after the new section is inserted.

### Not Included

- Changing runtime behavior in `src/akkapros/lib/phonetize.py`.
- Changing config defaults or timing values.
- Reinterpreting the accepted implementation as a bug.
- Hand-authoring a Mermaid diagram directly in prose without going through the code-derived flowchart workflow.
- Adding internal governance references to public docs.

---

## Current Behavior

The current user-facing phonetizer docs explain the live solver at stage and phase level, but they do not yet contain a dedicated section that explains the accepted current behavior for hiatus and vowel-transition rows.

The accepted implementation is already known and should be treated as the source behavior to document. The implementer should not need to rediscover these facts from `src/akkapros/lib/phonetize.py` before writing the public section.

The accepted current behavior is:

- hiatus rows are special consonant-like rows that use the closure timing class
- vowel-transition rows are special consonant-like rows that use the sonorant timing class
- unstressed singleton rows use their dedicated `special_realization` durations
- accentuated onset rows may receive accent increment and inherit the runtime class ceiling of their phonetic correspondence
- accentuation does not currently replace the special singleton anchor with the ordinary class onset anchor
- accentuation does not currently force these rows into the full ordinary onset-to-gemination band

No current user-facing phonetizer page explains that full behavior in one place.

Verified implementation details to document directly:

- Symbol typing: hiatus markers are classified as consonant rows of type `H`; vowel-transition markers are classified as consonant rows of type `T`.
- Timing-class mapping: `H` follows the closure timing class; `T` follows the sonorant timing class.
- Singleton unstressed anchors: hiatus uses `consonants.closure.special_realization.hiatus`; vowel transition uses `consonants.sonorant.special_realization.vowel_transition`.
- Emitted realization behavior: hiatus is not just an abstract placeholder and has its own emitted realization path; vowel-transition rows resolve contextually to glide-like outputs such as `WA` or `YI`.
- Accentuated onset behavior: if a hiatus or vowel-transition row is accent-bearing in onset position, the syllable is analyzed as accent shape `C:V`, and in `C:V` the special row is the primary accent segment that may receive accent increment.
- Runtime upper ceiling when accentuated: accentuated hiatus inherits closure `perception_limits.gemination_max`; accentuated vowel transition inherits sonorant `perception_limits.gemination_max`.
- What is not implemented: accentuation does not replace the special singleton anchor with ordinary class onset, does not force the row across `geminate_min`, does not force the row toward the ordinary class `geminate` target, and does not promote hiatus or vowel transition into the full ordinary onset-to-gemination range.
- Effective stressed ranges under the current solver: hiatus runs from `special_realization.hiatus` up to closure `gemination_max`, and vowel transition runs from `special_realization.vowel_transition` up to sonorant `gemination_max`; these are not the same as closure `onset` to closure `gemination_max` or sonorant `onset` to sonorant `gemination_max`.

---

## Proposed Change

Add a new user-facing documentation section that describes the current accepted implementation contract for hiatus and vowel-transition processing.

The section should appear in the phonetizer documentation page where readers already learn how live Phase 1 and Phase 2 behavior works. The default target page is:

- `docs/akkapros/phonetizer-algorithm.md`

The implementation may additionally update one nearby user-facing phonetizer page if a short cross-reference or brief summary is needed for navigation, but the full behavior contract should live in one primary page rather than being fragmented across multiple public docs.

The prose must describe the following points explicitly and accurately:

1. Hiatus and vowel-transition markers are modeled as special consonant-like rows.
2. Hiatus follows the closure timing class; vowel transition follows the sonorant timing class.
3. Singleton unstressed rows take their duration directly from:
   - `consonants.closure.special_realization.hiatus`
   - `consonants.sonorant.special_realization.vowel_transition`
4. If such a row is accentuated as onset `C:V`, it can receive accent increment.
5. The runtime upper ceiling for that increment is inherited from the corresponding class:
   - closure `perception_limits.gemination_max` for hiatus
   - sonorant `perception_limits.gemination_max` for vowel transition
6. The current implementation does not:
   - replace the special singleton anchor with ordinary class onset,
   - force the row across `geminate_min`,
   - or force the row toward the ordinary class `geminate` target.
7. The effective current stressed range is therefore:
   - hiatus: `special_realization.hiatus` to closure `gemination_max`
   - vowel transition: `special_realization.vowel_transition` to sonorant `gemination_max`
   and not the full ordinary onset-to-gemination band.

The implementer may reuse the wording substance of the following already-verified explanatory summary, adapted for public docs:

- Hiatus and vowel-transition markers are modeled as special consonant-like rows.
- Hiatus follows the closure timing class; vowel transition follows the sonorant timing class.
- Singleton unstressed rows take their duration directly from the dedicated `special_realization` config values.
- If such a row is accentuated as onset `C:V`, it can receive accent increment.
- The runtime upper ceiling for that increment is inherited from the corresponding class.
- The current implementation does not replace the special singleton anchor with ordinary class onset or force the row into the full ordinary onset-to-gemination band.

The page must also include a generated Mermaid flowchart that summarizes this behavior at user-facing level. The diagram must be concise and should likely show:

- symbol enters Phase 1 as hiatus or transition marker
- row is typed as `H` or `T`
- unstressed path uses `special_realization`
- accentuated `C:V` path keeps special anchor but inherits class ceiling
- hiatus path maps to closure ceiling
- transition path maps to sonorant ceiling
- note-level outcome that the current solver does not promote either row to ordinary onset lower bounds

The flowchart must be generated through the existing repository mechanism established by `CR-065`, with the same placeholder and verification pattern already used in user-facing docs.

---

## Technical Design

Implementation should follow the existing user-facing generated-flowchart workflow.

Primary doc target:

- `docs/akkapros/phonetizer-algorithm.md`

Likely supporting surfaces:

- `scripts/sync_doc_flowcharts.py`
- repository-owned flowchart descriptor or source structure used by that script
- `tests/test_doc_flowcharts.py`

Documentation rules:

- Public docs must describe current behavior directly and must not cite `docs/internal/` artifacts.
- The new section should be explicit, technically precise, and readable without code inspection.
- The prose should distinguish between:
  - special singleton timing,
  - accentuated extension,
  - class ceiling,
  - and ordinary class onset/geminate behavior that is not currently implemented.
- The section must not present future or hypothetical behavior as current fact.

Flowchart rules:

- Use the existing generated-flowchart placeholder contract in the target doc.
- Do not hand-author a Mermaid block directly from prose.
- Keep the diagram at user-facing detail level.
- The flowchart should summarize the behavior, not replace the prose.

Suggested flowchart content, already aligned to the accepted implementation:

- input hiatus or transition marker enters Phase 1 row building
- row is typed as `H` or `T`
- unstressed path uses `special_realization.hiatus` or `special_realization.vowel_transition`
- accentuated onset path is analyzed as `C:V`
- accentuated hiatus keeps the special anchor but inherits closure `gemination_max`
- accentuated vowel transition keeps the special anchor but inherits sonorant `gemination_max`
- end-state note that the current solver does not promote either row to the ordinary onset lower bound

Preferred placement in the target page:

- after the general Phase 2 solver explanation or within the area where special timing behavior is already discussed
- with a heading that is explicit enough to be searchable by readers, such as `Hiatus and Vowel Transition Processing`

---

## Files Likely Affected

docs/akkapros/phonetizer-algorithm.md  
docs/akkapros/phonetizer.md  
scripts/sync_doc_flowcharts.py  
tests/test_doc_flowcharts.py  

The final implementation may touch only a subset of these files if the primary doc page and existing flowchart source can be updated without broader changes.

---

## Acceptance Criteria

- [x] A user-facing phonetizer doc contains a dedicated explicit section for hiatus and vowel-transition behavior.
- [x] The section explains singleton unstressed timing from the dedicated `special_realization` config values.
- [x] The section explains accentuated `C:V` handling for hiatus and vowel-transition rows.
- [x] The section explicitly states that hiatus inherits the closure-class runtime ceiling and vowel transition inherits the sonorant-class runtime ceiling.
- [x] The section explicitly states that the current implementation does not promote accentuated special rows into the full ordinary onset-to-gemination range of those classes.
- [x] The section avoids internal-governance references and describes behavior directly.
- [x] The target page includes a generated Mermaid flowchart covering this behavior.
- [x] The generated flowchart is produced and verified through the repository's existing flowchart-generation contract rather than being handwritten.
- [x] Documentation verification passes after the new prose and flowchart are added.

---

## Risks / Edge Cases

Possible issues:

- The prose may accidentally overstate the implementation and imply ordinary onset lower bounds that are not currently enforced.
- The flowchart may become too detailed and drift into helper-level internal behavior.
- The documentation update may duplicate material already present elsewhere in the phonetizer docs instead of consolidating it cleanly.
- A hand-authored Mermaid diagram could bypass the repository's code-derived flowchart safeguards if the CR does not restate that requirement clearly.

---

## Testing Strategy

Documentation verification:

- Regenerate or verify the target Mermaid block through the repository's existing flowchart sync/verification path.
- Run the focused doc-flowchart verification tests.
- Confirm that the updated target doc contains the generated block and expected explicit heading.

Code-reading verification for doc correctness:

- Verify row typing, special singleton anchors, accent-shape handling, and class-ceiling behavior against `src/akkapros/lib/phonetize.py`.
- Verify that the public prose matches current behavior and does not describe unimplemented onset-lower-bound promotion.

Manual review:

- Confirm that a reader can understand the difference between singleton special timing and accentuated class-ceiling inheritance without reading internal governance docs.

---

## Rollback Plan

Revert the user-facing section and generated flowchart block if the prose or diagram proves inaccurate.

If the difficulty is not wording but unresolved behavior ambiguity, stop the documentation update and create a narrower corrective spec for the behavior before republishing public docs.

---

## Related Issues

- `CR-065` for the code-derived Mermaid flowchart contract in user-facing docs
- `CR-064` for the rule that public docs describe behavior directly without internal governance references
- `review-013` for the accepted internal description of current hiatus and vowel-transition processing

---

## Tasks

### Implementation

- [ ] Add the new user-facing section to the chosen phonetizer doc.
- [ ] Add or update the generated-flowchart source so this behavior has a dedicated Mermaid block.
- [ ] Insert the generated block into the target doc using the established placeholder contract.
- [ ] Add any minimal cross-reference needed from nearby phonetizer docs.

### Tests

- [ ] Run the flowchart sync/verification path.
- [ ] Run focused doc-flowchart verification tests.
- [ ] Verify that the prose matches the accepted current implementation.

### Documentation

- [ ] Keep the wording explicitly user-facing.
- [ ] Avoid internal governance references in public docs.
- [ ] State the non-implemented lower-bound promotion behavior clearly enough to avoid reader confusion.

### Review

- [ ] Verify acceptance criteria.
- [ ] Verify the flowchart remains user-facing and generated.
- [ ] Verify the doc does not imply runtime behavior changes.

---

## Implementation Blockers

Leave empty.

---

## Notes

This CR is intentionally documentation-only.

It should be implementable from the CR itself plus the existing generated-flowchart contract, without broad governance reconstruction or fresh code archaeology.

`review-013` remains useful as historical support, but it should not be necessary to read that review just to perform the doc update described here.
