---
cr_id: CR-070
status: Done
priority: High
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
implements: 'ADR-040, REQ-036'
---

# Change Request: Coalesce Consecutive EOL Pause Rows While Preserving Repeated EOL Text

## Summary

Reduce multiple consecutive newline-owned phonetizer pause rows to one logical
newline pause row, while preserving the exact newline multiplicity in the row's
source-facing `text` field.

Today the phonetizer emits one long `<EOL>` pause row for each encountered
newline. Under this CR, input such as `ba\n\n\nma` must no longer yield three
separate newline-owned silence rows. It must yield the same pause-row
structure as `ba\nma` for timing and row partitioning purposes, but the single
newline-owned row must preserve the repeated source content in its `text`
field as `<EOL><EOL><EOL>` so `_ophone.txt` and `_phone.txt` remain able to
reconstruct the consumed `_tilde` input faithfully.

---

## Motivation

The current phonetizer preserves explicit newlines too literally at the row
level.

That is useful for structural visibility, but it also means that several
consecutive newlines create several successive long pause rows even when the
desired runtime pause structure should treat them as one structural newline
event. The repository now needs a narrower contract: preserve newline ownership
separately from punctuation ownership, but collapse repeated adjacent newline-
owned pause rows into one row-level event.

This change is motivated by two goals:

- keep `<EOL>` structurally distinct from punctuation suites
- avoid multiplying pause rows when several line breaks occur together

The user requirement is specifically that `ba\n\n\nma` and `ba\nma` share the
same pause-row structure, while the serialized text field still preserves the
fact that three explicit line breaks were present in the first input.

---

## Scope

## Included

- Keep newline handling as a phonetizer branch separate from punctuation-suite
  grouping.
- Change the phonetizer row-building contract so one run of one or more
  consecutive `\n` characters produces one newline-owned long pause row rather
  than one row per newline.
- Require the source-facing `text` field of that pause row to contain one
  `<EOL>` token per consumed newline, concatenated in order with no loss of
  multiplicity.
- Require `ba\nma` and `ba\n\n\nma` to have the same count and placement of
  newline-owned pause rows in `_phone.txt` / `_ophone.txt`.
- Require reconstruction helpers and downstream consumers that interpret pause
  row `text` to treat repeated `<EOL>` tokens in one row as repeated literal
  newlines.
- Preserve the current rule that punctuation suites and newline-owned pauses are
  distinct causes and are not merged into one punctuation-plus-newline suite.
- Preserve the current rule that a punctuation suite immediately followed by
  newlines still yields a punctuation-owned pause row plus one newline-owned
  pause row, not a fused combined row.
- Update tests and docs for direct phonetizer row building, reconstruction, and
  any downstream consumer that reads `<EOL>` pause text.

## Not Included

- Defining paragraph-break semantics beyond this coalescing rule.
- Collapsing punctuation-owned pause rows with following newline-owned pause
  rows into one combined pause event.
- Introducing a new paragraph subtype, label, or duration policy in this CR.
- Changing how one isolated newline is typed today.

---

## Current Behavior

Current repository behavior emits one long pause row per explicit newline.

Observed live behavior in `src/akkapros/lib/phonetize.py`:

- `build_phone_rows()` handles `\n` in a dedicated branch before ordinary
  punctuation-suite grouping.
- Each encountered newline triggers `_finish('F')` and then appends one new
  long pause row with `text = '<EOL>'`.
- There is currently no coalescing step for consecutive newline characters.
- Therefore `\n\n\n` becomes three adjacent newline-owned long pause rows.
- Punctuation suites are still grouped separately by `_consume_pause_suite()`;
  that helper stops at whitespace or newline and therefore never absorbs the
  following newline into the punctuation suite.

Current consequence:

- `ba\nma` and `ba\n\n\nma` do not share the same pause-row structure today.
- The current row stream makes newline multiplicity explicit only through row
  count, not through one row's `text` field.

This behavior is consistent with the current contract in [CR-047](047-close-phonetizer-pause-and-reconstruction-gaps.md)
and [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md),
but it is narrower than the requested behavior.

---

## Proposed Change

Adopt the following contract.

## 1. Consecutive newline coalescing

- When the phonetizer Phase 1 row builder encounters one or more consecutive
  newline characters, it shall emit exactly one newline-owned long pause row
  for that consecutive run.
- The emitted row remains newline-owned rather than punctuation-owned.
- The row keeps the same structural role currently used for newline pauses:
  one long pause row closing the preceding syllable/unit.

Normative consequence:

- `ba\nma` yields one newline-owned pause row.
- `ba\n\n\nma` also yields one newline-owned pause row.

## 2. Text-field preservation of multiplicity

- The newline-owned pause row must preserve the exact count of consumed
  newlines in its `text` field.
- The canonical row text is the literal concatenation of `<EOL>` once per
  consumed newline.

Examples:

- `\n` -> `<EOL>`
- `\n\n` -> `<EOL><EOL>`
- `\n\n\n` -> `<EOL><EOL><EOL>`

This preserves input fidelity even though row count is reduced.

## 3. Reconstruction contract

- Reconstruction from `_phone.txt` / `_ophone.txt` back to `_tilde` must treat
  repeated `<EOL>` tokens inside one newline-owned pause row as repeated
  newline characters.
- The active reconstruction helper must therefore not rely only on exact text
  equality with a single `<EOL>` token.
- A row whose `text` is `<EOL><EOL><EOL>` must reconstruct as `\n\n\n`.

## 4. Punctuation boundary preservation

- This CR does not allow punctuation suites to absorb following newline-owned
  pauses.
- A punctuation suite followed by one or more newlines still yields:
  - one punctuation-owned pause row for the punctuation suite
  - one newline-owned long pause row for the consecutive newline run
- The newline run may coalesce internally, but it must remain separate from the
  punctuation suite.

Illustrative result shape:

- `ba..?\n\nma` -> one punctuation-owned row for `..?`, then one newline-owned
  row whose `text` is `<EOL><EOL>`.

## 5. Downstream interpretation

- Downstream stages may continue to treat the newline-owned row as one pause
  unit for timing and grouping purposes.
- This CR intentionally leaves open whether repeated `<EOL>` multiplicity later
  influences paragraph-sensitive pause duration or intonation policy.
- Until a later paragraph-aware CR is accepted, repeated `<EOL>` multiplicity in
  one row is informational and reconstructive, not a new duration-control rule.

---

## Technical Design

Architecture notes:

Components:

- `src/akkapros/lib/phonetize.py`
- `tests/test_phonetize_lib.py`
- `tests/test_integration.py`
- docs describing phone-row and reconstruction behavior

Implementation direction:

- Replace the current single-newline branch in `build_phone_rows()` with logic
  that consumes a maximal run of adjacent newline characters.
- Emit one newline-owned long pause row for that run.
- Set the row `text` field to repeated `<EOL>` tokens matching the consumed run
  length.
- Update reconstruction logic so a newline-owned row with repeated `<EOL>` text
  expands back into the same count of literal newlines.
- Preserve current punctuation-suite grouping boundaries so newline coalescing
  does not alter punctuation ownership.

Contract note:

- This CR narrows CR-047 and CR-050 only in how newline multiplicity is
  serialized at the row-count level. It does not replace the rule that newline
  remains structurally separate from punctuation suites.

---

## Files Likely Affected

`src/akkapros/lib/phonetize.py`
`tests/test_phonetize_lib.py`
`tests/test_integration.py`
`docs/akkapros/phonetizer-phone-file-guide.md`
`docs/akkapros/phonetizer.md`
`docs/internal/cr/070-coalesce-consecutive-eol-pause-rows-while-preserving-repeated-eol-text.md`

---

## Acceptance Criteria

- [x] A maximal run of one or more adjacent `\n` characters produces exactly
      one newline-owned long pause row in Phase 1 phone-row construction.
- [x] The emitted row `text` field contains one `<EOL>` token per consumed
      newline, concatenated in order.
- [x] `ba\nma` and `ba\n\n\nma` produce the same count and placement of
      newline-owned pause rows.
- [x] Reconstruction from phone rows back to `_tilde` preserves repeated
      newlines from repeated `<EOL>` tokens in a single row `text` field.
- [x] A punctuation suite followed by repeated newlines still yields a separate
      punctuation-owned pause row plus one newline-owned pause row.
- [x] Existing behavior for one isolated newline remains otherwise unchanged.
- [x] Unit tests pin the one-newline and many-newline cases directly.
- [x] Integration coverage pins at least one phone-artifact case where repeated
      newlines are coalesced into one row with repeated `<EOL>` text.
- [x] User-facing phonetizer docs describe the repeated-`<EOL>` text contract.

---

## Risks / Edge Cases

- Any current consumer that assumes newline-owned rows always have
  `text == '<EOL>'` will need to be updated to accept repeated `<EOL>` tokens.
- Reconstruction helpers may silently under-reconstruct if they keep exact
  single-token comparison logic.
- Metrics or printer code that treats row text as a display string rather than
  a structural token stream may need clarification once repeated `<EOL>` text
  becomes legal.
- This CR does not yet answer whether `<EOL><EOL>` should later imply a
  paragraph-specific duration or intonation effect.

---

## Testing Strategy

Unit tests:

- one isolated newline still yields one newline-owned long pause row
- three consecutive newlines yield one newline-owned long pause row with
  `text = '<EOL><EOL><EOL>'`
- punctuation plus repeated newline yields two rows, not one fused row
- reconstruction expands repeated `<EOL>` text back into repeated literal
  newlines

Integration tests:

- phonetizer CLI emits phone artifacts preserving repeated newline multiplicity
  in one row text field
- downstream reconstruction or round-trip checks remain faithful

Manual tests:

- compare representative `_ophone.txt` output for `ba\nma` and `ba\n\n\nma`
  and verify equal pause-row structure but different newline multiplicity in
  the final `text` column

---

## Rollback Plan

Restore the current one-row-per-newline behavior if downstream readers or
reconstruction tooling prove too coupled to exact single `<EOL>` row text.
That rollback would revert to emitting one newline-owned row per literal
newline and remove repeated `<EOL>` text from the row contract.

---

## Implementation Blockers

### 2026-04-18 - Earlier CR Not Done

- Type: missing dependency
- Observed: [CR-020](020-metrics-word-stats-lex-input.md) is listed in [docs/internal/cr/index.md](../cr/index.md) as `Rejected`, not `Done`.
- Why blocked: The prior repository CR workflow text treated any earlier CR not marked `Done` as blocking, which incorrectly included earlier `Rejected` CRs.
- Needed to unblock: Clarify the sequencing workflow so terminal earlier CR states `Done` and `Rejected` are both non-blocking.
- Owner: Internal Spec Writer
- Related refs: [docs/internal/cr/index.md](../cr/index.md), [CR-020](020-metrics-word-stats-lex-input.md)
- Resolved on: 2026-04-18
- Resolution: Updated [docs/internal/README.md](../README.md) so earlier CRs in terminal states `Done` and `Rejected` do not block later CR implementation.

---

## Related Issues

- [CR-047](047-close-phonetizer-pause-and-reconstruction-gaps.md)
- [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
- [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md)
- [CR-060](060-add-per-row-drift-column-to-phone-and-ophone-artifacts.md)

---

## Tasks

## Implementation

- [x] Coalesce consecutive newline runs into one newline-owned pause row
- [x] Preserve newline multiplicity in the row `text` field via repeated
      `<EOL>` tokens
- [x] Update reconstruction logic for repeated `<EOL>` token expansion

## Tests

- [x] Unit tests for one-newline and many-newline row construction
- [x] Unit tests for punctuation-row plus newline-row separation
- [x] Integration tests for serialized phone artifacts and round-trip fidelity

## Documentation

- [x] Update phonetizer phone-row docs for repeated `<EOL>` row text
- [x] Update any reconstruction or artifact-reading docs affected by the new
      newline text contract

## Review

- [x] Verify acceptance criteria against direct row probes and serialized phone
      artifacts
- [x] Verify no punctuation-suite grouping regression is introduced by newline
      coalescing

---

## Notes

- This CR intentionally keeps newline ownership separate from punctuation-suite
  ownership.
- Paragraph-break-specific pause semantics are intentionally deferred to a later
  record.
