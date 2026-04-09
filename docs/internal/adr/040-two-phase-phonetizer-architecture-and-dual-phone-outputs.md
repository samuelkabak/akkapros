---
adr_id: ADR-040
status: Accepted
created: 2026-04-05
updated: 2026-04-09
superseded_by: null
---

# 40. Two-Phase Phonetizer Architecture and Dual Phone Outputs

## Plain Summary

Adopt a two-phase phonetizer architecture.

Phase 1 builds complete phone-row structure with `duration=0000` for every row.
Phase 2 later applies duration algorithms by traversing those prebuilt rows.

The phonetizer reads `<prefix>_tilde.txt` and produces two canonical streams:

- original rows in `<prefix>_ophone.txt`
- accentuated rows in `<prefix>_phone.txt`

The original stream is derived from the accentuated `_tilde` input by removing
accent marker `~` and replacing internal merge `&` with ordinary space, while
preserving explicit lexical merge `+` and other structural separators.

## Context and Problem Statement

The repository is introducing a phonetize stage between prosody and metrics.
That stage must serve two needs at once:

- preserve enough structure to recover the prosodic input faithfully
- allow later timing algorithms to operate over explicit phone-row structure

If structure derivation and duration assignment are mixed together in one pass,
the phonetizer becomes harder to test and harder to extend. Timing experiments
would need to rebuild row structure every time, and round-trip validation would
become entangled with timing logic.

The project therefore needs an architectural decision that the phonetizer first
materializes structure and only later realizes durations.

## Decision Drivers

- Keep the phonetizer structurally testable before timing algorithms are final.
- Make original and accentuated row streams explicit rather than implicit.
- Preserve enough information to reconstruct input `_tilde` structure from
  emitted rows.
- Allow later duration algorithms to iterate on one stable row contract.
- Keep the stage architecture aligned with the broader timing-model redesign.

## Considered Options

- Build rows and durations in one combined pass.
- Build one accentuated row stream only and infer the original form later.
- Build two row streams up front, then run duration realization later over each
  stream.

## Decision Outcome

Chosen option: build two row streams up front, then run duration realization as
a later pass over those rows.

Under this decision:

- `_tilde` is the only required phonetizer input artifact
- the phonetizer derives an original/deaccented structural stream from that
  input
- Phase 1 emits complete rows with `0000` duration placeholders
- Phase 2 is a later traversal that updates only duration-bearing content while
  reading already-resolved structure

File outputs are fixed as follows:

- `<prefix>_ophone.txt` for the original stream
- `<prefix>_phone.txt` for the accentuated stream

The original stream derivation rule is part of the architecture:

- remove `~`
- replace `&` with space
- preserve `+`
- preserve other separator distinctions needed for round-trip structure

## Pros and Cons of the Options

### Chosen Option

- Pros: gives later duration work a stable structural substrate.
- Pros: supports focused unit testing of structural row generation.
- Pros: makes round-trip verification possible before timing logic exists.
- Pros: keeps original and accentuated streams explicit for downstream
  comparison.
- Cons: requires two row lists instead of one.
- Cons: Phase 1 outputs temporarily carry placeholder durations.

### Other Options

- Combined structure-and-duration pass:
  - Pro: one traversal only.
  - Con: harder to test, harder to evolve, harder to compare timing models.
- Accentuated-only row stream:
  - Pro: less immediate output.
  - Con: loses explicit original-vs-accentuated comparison as a first-class
    artifact.

## Implications and Consequences

- The phonetize library should expose a structural builder that can operate
  without any finalized duration algorithm.
- The phonetizer CLI should be able to emit valid `_ophone` and `_phone` files
  even before Phase 2 exists.
- Tests should be able to reconstruct relevant `_tilde` input structure from
  emitted rows to verify that the phonetizer is not silently normalizing away
  critical distinctions.
- Later duration CRs should update the two row streams by traversal rather than
  silently rebuilding them with different structural assumptions.

## Links

- Related REQ: [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- Parent ADR: [ADR-039](039-replacement-of-timing-model.md)
- Parent pipeline context: [ADR-004](004-stage-pipeline-and-pivot-format.md)
- First implementation CR: [CR-039](../cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- Related contract CRs: [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md), [CR-036](../cr/036-define-phonetizer-phoneme-framework.md)

## Implementation Notes (optional)

- The first implementation CR should stop after Phase 1 row construction and
  round-trip validation support.
- The actual duration algorithms are intentionally deferred to later child CRs.

## Reviewed By

- Accepted during CR-039 implementation and verification.