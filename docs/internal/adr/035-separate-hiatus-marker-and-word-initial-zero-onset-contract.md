---
adr_id: ADR-035
status: Accepted
created: 2026-04-02
updated: 2026-04-05
superseded_by: null
---

# 35. Separate Hiatus Marker and Word-Initial Zero-Onset Contract

## Plain Summary

Keep `DIPH_SEPARATOR = '¨'` for its existing diphthong-transition role and add
`HIATUS_MARKER = '˙'` for word-initial vowel hiatus, creating two internal
pseudo-consonants with distinct meanings, while `·` remains the
only syllable-boundary marker.

This decision replaces the earlier draft direction that would have broadened
`DIPH_SEPARATOR` into a general zero-onset symbol. Printer outputs and
metricalc outputs remain unchanged.

## Context and Problem Statement

The current codebase already uses `¨` in diphthong-related processing and
preserves it through the internal pipeline. The earlier CR-029 draft proposed
broadening that same symbol so it would also represent word-initial vowel
hiatus. That is no longer the intended design.

The code still needs an explicit internal representation for word-initial vowel
hiatus. A printer-side inferred glottal path currently covers some of that
behavior, but it does so without a dedicated internal symbol distinct from the
existing diphthong-transition marker.

The earlier implementation attempt aligned with the broader draft was
discarded before this ADR rewrite. This decision therefore applies to a clean
code state rather than to a partially migrated implementation.

The project needs one explicit decision that keeps the established meaning of
`DIPH_SEPARATOR` and introduces a separate symbol for the different internal
role.

## Decision Drivers

- Preserve the existing semantics of `DIPH_SEPARATOR`
- Keep diphthong transition distinct from word-initial hiatus
- Keep pseudo-consonants distinct from the syllable-boundary marker
- Make the internal contract explicit without changing visible outputs
- Keep last-resort prosody serialization testable and unambiguous

## Considered Options

- Keep `¨` as diphthong-only and retain printer-side inference for word-initial hiatus.
- Redefine `¨` as one general transition pseudo-consonant for both roles.
- Introduce a second symbol for word-initial hiatus while keeping `¨` for diphthongs.

## Decision Outcome

Chosen option: Introduce a second symbol for word-initial hiatus while keeping
`¨` for diphthongs.

Concretely:

- `DIPH_SEPARATOR = '¨'` remains unchanged.
- `HIATUS_MARKER = '˙'` is added as a new constant.
- `¨` remains the internal pseudo-consonant placeholder for diphthong or
  split-vowel transition behavior.
- `˙` becomes the internal pseudo-consonant placeholder for word-initial vowel
  hiatus.
- `·` remains the syllable-boundary marker.
- In a diphthong-transition form such as `tiam`, the internal split remains
  `ti¨am`, and the syllabified form remains `ti·¨am`.
- In a word-initial hiatus form such as `ana`, the internal representation
  becomes `˙ana`, and the syllabified form becomes `˙a·na`.
- In last-resort prosody on a word-initial hiatus syllable, the serialized form
  is `˙~V`, not `~V`.
- Existing visible outputs from printer and metricalc remain normative and
  must not change.

## Pros and Cons of the Options

### Introduce a second symbol for word-initial hiatus while keeping `¨` for diphthongs (chosen)

- Good, because the existing meaning of `DIPH_SEPARATOR` is preserved.
- Good, because diphthong transition and word-initial hiatus remain explicit
  and distinct.
- Good, because the internal representation becomes clearer without changing
  visible outputs.
- Good, because last-resort prosody can target the explicit `˙` symbol.
- Bad, because two internal pseudo-consonants must now be documented and
  handled consistently.
- Bad, because some helpers and fixtures must distinguish the two symbols.

### Keep `¨` as diphthong-only and retain printer-side inference for word-initial hiatus

- Good, because it minimizes short-term internal changes.
- Bad, because word-initial hiatus remains partly implicit and stage-local.
- Bad, because the internal contract remains less explicit than desired.

### Redefine `¨` as one general transition pseudo-consonant for both roles

- Good, because it uses only one internal symbol.
- Bad, because it changes the meaning of `DIPH_SEPARATOR`.
- Bad, because it collapses two internal roles that are now intentionally kept
  separate.

## Implications and Consequences

- Keep `DIPH_SEPARATOR` unchanged and add `HIATUS_MARKER`.
- Add both symbols to the effective internal consonant inventory in the
  normalization-hooks block.
- Update syllabifier, prosody, front matter, metrics, and printer internals so
  they can consume `˙` without changing final visible outputs.
- Keep diphthong logic and documentation tied to `DIPH_SEPARATOR` rather than
  silently moving that meaning to `HIATUS_MARKER`.
- Correct any documentation that describes `¨` as carrying the new zero-onset
  role.
- Update only the intended intermediate fixtures where `˙` appears.
- Do not update printer-output or metricalc-output expectations merely to
  accommodate this feature.
- Do not assume any residual code cleanup from the earlier draft, because that
  implementation attempt was discarded before this decision record was updated.

## Links

- Related ADR: [ADR-007](007-two-phase-diphthong-processing.md)
- Related ADR: [ADR-016](016-diphthong-restoration-constraint-system.md)
- Related ADR: [ADR-021](021-multi-target-printer-architecture-contract.md)
- Related ADR: [ADR-022](022-output-format-public-contract-boundaries.md)
- Related CR: [CR-029](../cr/029-introduce-separate-hiatus-marker-for-word-initial-vowel-hiatus.md)
- Related REQ: [REQ-021](../req/021-separate-hiatus-marker-for-word-initial-vowel-hiatus.md)

## Implementation Notes (optional)

- Update high-risk syllabifier logic minimally and regression-first.
- Specify the normalization-hooks block with both additions:
  `AKKADIAN_CONSONANTS.add(DIPH_SEPARATOR)` and
  `AKKADIAN_CONSONANTS.add(HIATUS_MARKER)`.
- Update last-resort prosody serialization for the word-initial hiatus case to
  `˙~V`.
- Preserve unchanged printer outputs and unchanged metricalc outputs as
  acceptance boundaries.

## Reviewed By

- Pending maintainer review
