---
adr_id: ADR-045
status: Accepted
created: 2026-04-11
updated: 2026-04-11
superseded_by: null
---

# 45. Three-Pass Phonetizer Intonation and Row-Derived MBROLA

## Plain Summary

Adopt a three-pass phonetizer architecture in which structure, duration, and
intonation are realized in separate ordered passes. Pause typing becomes the
cause-side signal for phrase-level intonation, while the current implementation
scope applies that cause first to the last syllable before the pause.

This matters because intonation is wider than a single phoneme and should not
be mixed into either row construction or duration realization. It also keeps
MBROLA `.pho` export tied to the finalized phone rows rather than allowing a
second pitch or stress system to drift away from the phone-table contract.

## Context and Problem Statement

The accepted phonetizer architecture currently describes two passes:

- Phase 1 builds the row streams
- Phase 2 fills duration

That was sufficient while the phonetizer only needed stable row structure and
later timing realization. It is no longer sufficient once intonation becomes a
first-class contract.

The repository now needs to represent intonation as a row-carried property that
is derived from wider context than a single phoneme. The key cause signal is
pause type: question, statement, exclamation, continuation, or internal pause
with no clause-final intonation.
That pause type informs the preceding phrase, not merely the final phoneme and
not inherently only the final syllable. In the current phonetizer scope, the
visible consequence is applied to the last syllable before the pause, but the
architecture must preserve the more general model that pause type is the cause
and the current syllable-level application is one consequence strategy.

If intonation is assigned during row construction, it risks binding wider
phrase interpretation to a source-facing structural pass. If intonation is
assigned during duration realization, timing and pitch can become entangled and
errors in one domain can damage the other. The project therefore needs one
explicit architectural decision that intonation belongs to an independent pass
after durations are already stable.

The same decision must also settle how MBROLA `.pho` output is derived. The
repository already treats phonetizer-owned phone rows as the active source for
`.pho` export. Once intonation becomes a row-carried property, MBROLA output
must be derived entirely from finalized phone rows plus `f0`, not from direct
stress inference, `_tilde` reparsing, or a second detached pitch model.

## Decision Drivers

- Keep structure, timing, and intonation as separate computational concerns.
- Treat pause type as the linguistic cause of phrase-final intonation.
- Preserve room for future models that spread intonation beyond the last
  syllable.
- Prevent pitch logic from introducing duration regressions or vice versa.
- Keep phonetizer-owned phone rows as the single active source for downstream
  `.pho` export.
- Keep the runtime verifiable with focused unit tests per pass and integration
  tests across the full phonetizer pipeline.

## Considered Options

- Keep the two-pass architecture and assign intonation during Phase 2.
- Keep the two-pass architecture and assign intonation during Phase 1.
- Adopt a third pass that assigns intonation after duration realization.

## Decision Outcome

Chosen option: adopt a third pass that assigns intonation after duration
realization.

Under this decision:

- Pass 1 builds row structure and pause typing from `_tilde`
- Pass 2 realizes duration from the prebuilt rows
- Pass 3 realizes intonation from the duration-bearing rows and effective
  config
- pause type is the cause-side intonation signal, including an explicit
  no-intonation internal type
- the current phonetizer implementation scope applies that signal to the last
  syllable before the pause
- future models may spread the same cause over a wider phrase without changing
  the basic cause-side row contract
- MBROLA `.pho` export is derived entirely from finalized phone rows plus
  `phonetize.process.intonation.f0`

The active phone-table contract therefore becomes structure-first,
then duration, then intonation.

## Pros and Cons of the Options

### Chosen Option

- Pros: separates pitch logic from duration logic cleanly.
- Pros: preserves the linguistic model that pause type informs the phrase.
- Pros: allows the current last-syllable behavior without freezing the system
  into that one strategy forever.
- Pros: keeps `.pho` export tied to the finalized row stream.
- Pros: makes pass-local unit tests and pass-order integration tests natural.
- Cons: increases architecture complexity from two passes to three.
- Cons: requires explicit supersession of the earlier two-pass phonetizer ADR.
- Cons: requires downstream row readers and tests to accept a new finalized
  row contract.

### Other Options

- Assign intonation during Pass 1:
  - Pro: fewer passes.
  - Con: phrase-wide intonation becomes entangled with source-facing structure
    building and punctuation handling.
- Assign intonation during Pass 2:
  - Pro: fewer passes.
  - Con: timing and pitch concerns become coupled, increasing the risk of
    duration mistakes and obscuring verification.

## Implications and Consequences

- The earlier two-pass phonetizer architecture is no longer the active
  contract; it is superseded for current implementation and verification by
  this newer ADR.
- The phone-row contract must carry resolved intonation in finalized outputs.
- Pause typing must be treated as a stable row-level cause signal.
- The internal pause type must remain part of that cause-side inventory and
  must explicitly mean that no clause-final intonation override is applied.
- `.pho` export must consume finalized row fields only.
- Tests must be expanded in both unit and integration layers to cover:
  - pass ordering
  - pause typing
  - final-syllable intonation assignment in current scope
  - MBROLA pitch-target derivation from row-level intonation

## Links

- Superseded architecture ADR: [ADR-040](040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Config/layout ADR: [ADR-043](043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)
- Related REQ: [REQ-032](../req/032-phonetizer-intonation-and-three-pass-finalization.md)
- Implementation CR: [CR-050](../cr/050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
- Existing `.pho` ownership CR: [CR-045](../cr/045-move-mbrola-pho-output-to-phonetizer.md)

## Implementation Notes (optional)

- The current implementation scope applies pause-governed intonation to the
  last syllable before each pause.
- Future phrase-spread models should preserve pause type as the cause-side
  contract and refine only the consequence mapping.
- MBROLA pitch-target generation must respect MBROLA's equal-spacing and
  straight-line interpolation model.

## Reviewed By

- Akkapros maintainers
