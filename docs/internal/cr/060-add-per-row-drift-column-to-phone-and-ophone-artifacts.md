---
cr_id: CR-060
status: Blocked
priority: High
impact: Mutative
created: 2026-04-14
updated: 2026-04-14
implements: 'ADR-045, REQ-030, REQ-031, REQ-032'
---

# Change Request: Add Per-Row Drift Column to Phone and Ophone Artifacts

# Summary

Extend the serialized `_phone.txt` and `_ophone.txt` row schema with one new
fixed-width drift column placed immediately after `duration`.

The new column carries the running post-hedging drift state as a four-character
code such as `A000`, `A012`, or `B003`, where `A` means ahead of the beat,
`B` means behind the beat, and the three digits encode the absolute drift in
milliseconds. This CR keeps the existing frontmatter drift summary but adds a
row-level drift trace to the phone artifacts so downstream inspection and later
analysis can see where drift stands after each completed syllable or pause.

This CR narrows the active phone-row serialization contract in
[CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
and adds a more detailed drift-trace surface on top of the drift-summary
behavior documented in [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
and [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md).

---

# Motivation

Current repository behavior exposes drift only as an aggregate report object and
frontmatter summary.

Repository inspection on 2026-04-14 shows the following active behavior:

- `src/akkapros/lib/phonetize.py` serializes phone rows from the current
  `PHONE_ROW_FIELDS` list and therefore emits only the existing row fields.
- The active row schema already includes `duration` and `intonation`, but it
  does not carry any per-row drift state.
- `realize_phone_rows()` currently returns drift summary information such as
  `max`, `mean`, `stddev`, `current`, and a summary `label`, but that data is
  not written into individual `_phone.txt` / `_ophone.txt` rows.
- Downstream tools can read final durations and pause types from rows, but they
  cannot inspect where the running drift stood at each completed syllable or
  completed pause without reproducing solver behavior from implementation code.

That is too coarse for inspection and future analysis. The project needs one
explicit serialized row field that records the drift state after unit-final
hedging has completed, while preserving the existing summary drift contract for
metrics and frontmatter consumers.

---

# Scope

## Included

- Extend the `_phone.txt` / `_ophone.txt` row schema with one new serialized
  field immediately after `duration`.
- Define the new field as a four-character drift-status token.
- Require that the token format is one sign letter plus three digits.
- Define `A` as ahead of the beat and `B` as behind the beat.
- Define the beat as the currently relevant integer multiple `N *
  cvc_reference` used by the live duration solver.
- Define when the per-row drift token is updated: at the end of a syllable and
  at the end of a pause, after all active hedging and legal correction for that
  unit has completed.
- Define what non-unit-final rows carry before the next update point.
- Keep the existing frontmatter drift summary and row-level drift column in
  parallel; this CR does not remove the summary.
- Require all active readers and writers of `_phone.txt` / `_ophone.txt` to
  parse, serialize, preserve, and document the new field.
- Require `metricalc` and the shared metrics library to accept the new
  twelve-field `_phone.txt` / `_ophone.txt` format without ambiguity.
- Update docs, examples, tests, self-tests, and demo artifacts that describe or
  consume the row schema.

## Not Included

- Replacing frontmatter drift summaries with row-level drift traces.
- Changing how drift is solved mathematically beyond the serialization point
  and timing described here.
- Redefining pause ownership, pause typing, or pause insertion policy.
- Adding a metrics formula that directly consumes the new drift column in this
  CR.
- Expanding the drift field beyond four characters.

---

# Current Behavior

Current repository behavior still treats drift as summary metadata rather than
as row-level artifact data.

Observed current behavior:

- The active phone-row schema defined by the current implementation has eleven
  serialized fields and does not include a drift column.
- `serialize_phone_row()` emits all row fields except `text` in hyphen-joined
  form and appends `:text`; there is no drift field between `duration` and
  `intonation` today.
- `parse_phone_row()` expects the current field count and would reject a row
  containing one extra serialized drift field until the schema is updated.
- `realize_phone_rows()` computes running drift internally and returns only a
  summary object with aggregate values such as `max`, `mean`, `stddev`,
  `current`, and `label`.
- `_phone.txt` / `_ophone.txt` examples therefore expose realized durations and
  intonation but not the per-row drift state after a unit is completed.

Under the active contract, a human reading `_phone.txt` can see that a segment
or pause was realized, but cannot see from the row stream alone whether the
solver stood ahead of or behind the beat after the completed syllable or pause
that ends on that row.

---

# Proposed Change

Adopt the following contract.

## 1. Phone-row schema expands to twelve fields

This CR narrows the phone-row schema from eleven serialized fields to twelve.

The canonical phone-row schema becomes:

1. `label`
2. `category`
3. `type`
4. `length`
5. `position`
6. `boundary`
7. `accent`
8. `realization`
9. `duration`
10. `drift`
11. `intonation`
12. `text`

The new `drift` field shall appear immediately after `duration` and immediately
before `intonation` in serialized `_phone.txt` / `_ophone.txt` rows.

Analyst-facing file interpretation:

- `_ophone.txt` is the original or deaccented stream. It shows the same
  realized segment and pause structure after phonetizer processing, but it does
  not carry accentuation from `~`. An analyst should therefore read `_ophone`
  as the baseline timing realization of the deaccented stream.
- `_phone.txt` is the accentuated stream. It carries the same general row
  schema, but the `accent`, `duration`, `drift`, and sometimes downstream
  prosodic consequences may differ because accentuation has been realized.
- The two files are parallel artifacts. A row in `_ophone.txt` is interpreted
  with the same column semantics as a row in `_phone.txt`; the difference is
  which stream the row belongs to, not a different meaning of the columns.

For analyst readability, the serialized row should be understood as:

- structural identity of the segment or pause
- structural role inside the syllable or pause system
- realized duration
- running drift state after the most recently completed unit
- realized intonation token
- source-facing text glyph or pause text that generated the row

This placement makes the row read naturally as:

- what was realized
- how long it lasted
- where the solver stands relative to the beat after the most recently closed
  unit
- what intonation token the row carries

### 1A. Column meanings for analysts

The canonical twelve-field schema should be documented to analysts in a compact
column glossary such as the following.

| Column | Width | Meaning in `_ophone.txt` and `_phone.txt` | Analyst reading guidance |
| --- | --- | --- | --- |
| `label` | fixed | Canonical emitted row label | Identifies the emitted segment or pause family, not the raw input glyph alone |
| `category` | 1 char | Broad row class: consonant, vowel, or silence | Use this first to see whether the row is a segment or a pause |
| `type` | 1 char | Subclass inside the category | Distinguishes consonant/vowel subclasses and pause subtype behavior |
| `length` | 1 char | Phonological or pause length class | For silence rows this is the pause length class; for vowels it distinguishes short vs long; for consonants it retains the emitted schema contract |
| `position` | 1 char | Position inside the syllable or pause role | Analysts use this to see onset, nucleus, coda, or pause placement semantics |
| `boundary` | 1 char | How the row closes or links to the next structural unit | Critical for identifying syllable-final rows, merge behavior, and unit-final drift update points |
| `accent` | 1 char | Accentuation-bearing status of the row | In `_ophone.txt` this normally reflects the deaccented stream; in `_phone.txt` it shows the accentuated stream contract |
| `realization` | fixed | Emitted realization code | This is the phonetizer's realized code inventory, not merely the source symbol |
| `duration` | 4 digits | Realized duration in milliseconds | Read as the final row duration after timing realization |
| `drift` | 4 chars | Signed running drift token after the most recently completed syllable or pause | `A` = ahead, `B` = behind, digits = absolute milliseconds; non-final rows repeat the latest completed-unit value |
| `intonation` | 3 chars | Realized intonation token carried by the row | Read as the row-level contour token already normalized by the phonetizer |
| `text` | variable | Source-facing glyph or pause text associated with the row | Lets analysts relate the realized row back to the originating segment, punctuation, or normalized pause text |

Additional analyst notes:

- `_ophone.txt` and `_phone.txt` use the same glossary. The difference is that
  `_ophone.txt` represents the original/deaccented stream while `_phone.txt`
  represents the accentuated stream.
- Analysts should not infer that a changed `drift` value belongs to the row in
  isolation. The `drift` token belongs to the most recently completed unit, so
  its value becomes newly informative on syllable-final rows and pause rows.
- The `text` field is source-facing and may remain stable even when
  `realization`, `duration`, `drift`, or `intonation` differ between `_ophone`
  and `_phone`.

## 2. Drift token format

The `drift` field is a fixed-width four-character token.

Format:

- first character: `A` or `B`
- next three characters: zero-padded decimal digits `000` through `999`

Meaning:

- `A` = ahead of the beat
- `B` = behind the beat

Special zero rule:

- exact zero shall serialize as `A000`
- `B000` is not an active serialized form under this contract

Interpretation examples:

- `A000` = exactly on the beat / no signed drift carried forward
- `A005` = five milliseconds ahead of the beat
- `A012` = twelve milliseconds ahead of the beat
- `B003` = three milliseconds behind the beat

The token stores the sign plus absolute magnitude in milliseconds. It does not
store a decimal or floating-point representation.

## 3. Beat reference and update timing

The active beat reference is the current integer multiple `N * cvc_reference`
used by the live duration solver for the unit being closed.

The row-level drift token is not recomputed on every segment boundary. It is
updated only when one whole timing unit has finished processing.

Unit-final update points are:

- the final row of a syllable, after all duration assignment, drift discharge,
  vowel correction, accentuation-side hedging, and any other active legal
  correction for that syllable are complete
- the row of a realized pause, after all pause-target selection, drift
  discharge, and any other active legal correction for that pause are complete

This means the token records the drift state after hedging, not a provisional
intermediate value.

## 4. Semantics on non-final rows

Rows that do not end a syllable or pause shall carry the most recently known
completed-unit drift token.

Operationally:

- before the first completed syllable or completed pause in a stream, rows
  shall carry `A000`
- when a row is inside a syllable but does not close that syllable, its `drift`
  field shall still show the drift state from the previous completed unit
- when a row closes a syllable, its `drift` field shall show the newly computed
  post-syllable drift state
- rows following that syllable shall continue to carry the same token until the
  next syllable-final or pause-final update point changes it
- a pause row shall carry the newly computed post-pause drift state for that
  completed pause

This keeps every row self-describing while ensuring that only unit-final rows
change the drift value.

## 5. Normative example

Given a stream where drift is evaluated only at unit-final points, the row-level
`drift` field behaves like this:

- first consonant of `CVC` -> `A000`
- vowel of that same `CVC` -> `A000`
- final consonant of that `CVC` -> `A005`
- next consonant of `CV` -> `A005`
- vowel closing that `CV` -> `A009`
- pause row `S` closing the pause unit -> `A012`
- next consonant of following `CVC` -> `A012`
- vowel of that `CVC` -> `A012`
- final consonant of that `CVC` -> `B003`

Illustrative serialized rows:

```text
C > A000
V > A000
C > A005
C > A005
V > A009
S > A012
C > A012
V > A012
C > B003
```

The important contract point is not the specific numeric values in this example
but the update discipline:

- syllable-final rows and pause rows refresh drift after hedging
- non-final rows repeat the last completed-unit value

## 6. Relationship to frontmatter drift summary

The new `drift` field is additive. It does not replace the existing drift
summary emitted in report objects and serialized frontmatter.

The active contract after this CR is:

- row-level `drift` provides local traceability at serialized row granularity
- frontmatter/report drift summary continues to provide aggregate values such as
  `max`, `mean`, `stddev`, `current`, and any newer counters required by later
  records

Where both surfaces exist, they must remain internally consistent:

- the final unit-final row in a stream shall agree in sign and magnitude with
  the final running drift state represented by the report/frontmatter
  `current` value after the same serialization rounding rules are applied
- row-level drift tokens shall not be back-computed from frontmatter only;
  they must be written from the actual realization traversal

## 7. Reader and writer compatibility requirements

All active phone-row readers and writers shall be updated to the twelve-field
schema.

This includes at minimum:

- phonetizer row construction defaults for unresolved rows
- phonetizer serialization and parse helpers
- printer and metrics file readers that consume `_phone.txt` / `_ophone.txt`
- any row round-trip tests and self-tests
- docs and phone-file guides that list the schema

Compatibility rule:

- after this CR is implemented, the active runtime contract is the twelve-field
  schema
- any transitional backward-compatibility support for older eleven-field files
  is optional implementation detail and is not required by this CR unless a
  later record formalizes it

## 7A. Metricalc and metrics-reader requirements

`metricalc` and the shared metrics-loading path must understand the new schema
as a file-format change, not as a metrics-formula change.

Active reader requirements:

- `metricalc` shall accept `_phone.txt` and `_ophone.txt` rows serialized with
  the new `duration, drift, intonation` sequence in the row head.
- `metricalc` shall not misread the new `drift` token as part of `duration`,
  as part of `intonation`, or as part of `text`.
- Where metrics normalizes rows into `V`, `C`, and `P` intervals, that logic
  shall continue to use the row's structural fields and `duration`; the new
  `drift` column does not change interval classification rules in this CR.
- Where metricalc computes interval metrics, speech metrics, pause metrics, or
  other row-derived outputs, the presence of the `drift` column shall not alter
  the existing formulas unless a later record explicitly says so.
- `metricalc` may ignore row-level `drift` for formula purposes under this CR,
  but it must parse the field correctly and preserve a coherent interpretation
  of the file format.
- `metricalc` shall continue to read drift summary values from phonetizer
  frontmatter wherever the active metrics contract still requires those summary
  surfaces.
- If metrics or metricalc later expose row-level drift diagnostics, that later
  work must build on the same parsed `drift` field defined here rather than on
  a second incompatible row format.

Analyst-facing interpretation for metricalc consumers:

- the new `drift` column is part of the phone-row artifact contract that
  metricalc reads
- in this CR, it is a format-bearing column first, not a new active metrics
  indicator by itself
- the meaning of the column must still be documented in metricalc-facing docs
  so users understand why the row format changed and how to read the files that
  metricalc consumes

## 8. Default unresolved value before duration realization

Because Phase 1 still emits structure before drift is solved, the unresolved
row default shall be `A000`.

That placeholder is allowed only until Phase 2 finishes. Once durations are
realized, every row must carry the correct row-level drift token defined by the
unit-final update rules in this CR.

## 9. Documentation and public examples

The affected public and internal docs shall be updated so they do not keep
teaching the older eleven-field schema.

This explicitly includes documentation that explains:

- the field order of `_phone.txt` / `_ophone.txt`
- the meaning of `duration`
- the meaning of `intonation`
- drift summaries or drift-facing diagnostics

The docs must explain all of the following:

- `drift` is a row field, not only frontmatter data
- `drift` updates at syllable-final and pause-final points only
- non-final rows repeat the latest completed-unit drift token
- `A000` is the canonical zero token
- `A` means ahead of the beat and `B` means behind the beat

---

# Technical Design

Architecture notes:

Components:

- `src/akkapros/lib/phonetize.py`
- `_phone.txt` / `_ophone.txt` serialization and parse helpers
- phone-row consumers in metrics and printer paths
- phonetizer report/frontmatter emission
- docs and examples that describe phone-row layout

Design requirements:

- Extend the in-memory row dictionary shape with `drift`.
- Update the canonical serialized field order to insert `drift` after
  `duration`.
- Initialize row defaults to `drift='A000'` before Phase 2 realization.
- During Phase 2 traversal, keep a running signed drift state as today.
- After each completed syllable and after each completed pause, convert the
  current signed drift to the four-character row token and write it onto the
  unit-final row.
- Copy the last completed-unit token forward to intermediate rows until the
  next unit-final update point occurs.
- Keep the existing aggregate drift summary surfaces in report/frontmatter.
- Ensure parse/serialize round-trips preserve the new field exactly.
- Ensure shared phone-row readers used by metricalc and metrics parse the new
  field order exactly once in one compatible schema path rather than adding a
  metrics-only alternative parser.

Implementation guidance:

- Use one central helper to format the row-level drift token so the same
  sign/rounding/zero rules are reused everywhere.
- Use the same signed drift source that drives the report/frontmatter drift
  summary; do not create a second independent drift calculation path.
- Preserve the existing four-digit `duration` width unchanged.
- Preserve the current intonation token semantics unchanged.

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/lib/print.py`
`src/akkapros/lib/helpmsg.py`
`tests/test_phonetize_lib.py`
`tests/test_metrics_stats.py`
`tests/test_selftests_lib.py`
`tests/test_selftests_cli.py`
`tests/test_integration.py`
`docs/akkapros/phonetizer-phone-file-guide.md`
`docs/akkapros/phonetizer.md`
`docs/akkapros/metrics-computation.md`
`demo/akkapros/prosmaker/results/*_phone.txt`
`demo/akkapros/prosmaker/results/*_ophone.txt`

---

# Acceptance Criteria

- [ ] Given `_phone.txt` or `_ophone.txt` rows are serialized under the active
      contract, when the field order is inspected, then `drift` appears
      immediately after `duration` and immediately before `intonation`.
- [ ] Given a serialized phone row is parsed, when the row uses the new active
      schema, then the parser accepts the twelve-field row and preserves the
      `drift` token exactly.
- [ ] Given metricalc loads `_phone.txt` and `_ophone.txt` under the active
  contract, when rows include the new `drift` field, then file loading
  succeeds without treating the row as malformed.
- [ ] Given metricalc loads `_phone.txt` and `_ophone.txt` under the active
  contract, when the new `drift` field is present, then `duration`,
  `drift`, `intonation`, and `text` are parsed into the correct columns and
  are not shifted relative to the active schema.
- [ ] Given a row is emitted before any completed syllable or completed pause
      has updated running drift, when the row is serialized, then its `drift`
      field is `A000`.
- [ ] Given a row does not close a syllable or a pause, when the row is
      serialized, then its `drift` field equals the most recent completed-unit
      drift token rather than a provisional recomputation.
- [ ] Given a row closes a syllable, when the solver finishes all active
      hedging for that syllable, then that row's `drift` field equals the
      post-syllable drift token.
- [ ] Given a pause row is realized, when the solver finishes all active
      hedging for that pause, then that row's `drift` field equals the
      post-pause drift token.
- [ ] Given the signed drift magnitude is zero, when the row token is
      serialized, then the token is exactly `A000`.
- [ ] Given the signed drift is positive, when the row token is serialized,
      then it begins with `A` and uses three zero-padded digits.
- [ ] Given the signed drift is negative, when the row token is serialized,
      then it begins with `B` and uses three zero-padded digits for the
      absolute magnitude.
- [ ] Given a stream finishes realization, when the final unit-final row is
      inspected together with the drift summary/report output for that same
      stream, then both surfaces agree on the final drift state after the same
      row-token rounding rules are applied.
- [ ] Given docs describing the `_phone.txt` / `_ophone.txt` schema are
      inspected, when field order and semantics are explained, then the new
      `drift` column and its update timing are documented.
- [ ] Given metricalc documentation or help surfaces describe the phone/ophone
  file format it consumes, when the active row schema is explained, then
  the new `drift` column is included with correct meaning and placement.

---

# Risks / Edge Cases

Possible issues:

- Rounding drift to three digits may hide sub-millisecond or higher-precision
  internal values. This CR intentionally prefers a stable fixed-width artifact
  format over full internal precision exposure.
- If a later runtime allows drift magnitude above `999` ms, this four-character
  token would saturate the available width. This CR does not expand the width,
  so implementations must either constrain the serialized magnitude or raise a
  clear error if that case becomes possible.
- Intermediate rows inside long syllables may appear to repeat a stale value;
  that is correct under this contract because drift is only authoritative after
  completed units.
- Any consumer still hard-coded to the eleven-field schema will fail until it is
  updated.
- New pause behaviors from later records must continue to obey the same
  unit-final update rule for the per-row drift token.

---

# Testing Strategy

Unit tests:

- verify phone-row parse/serialize round-trip with the new `drift` field
- verify `A000` is the canonical zero token
- verify positive signed drift formats as `Axyz`
- verify negative signed drift formats as `Bxyz`
- verify non-final rows repeat the last completed-unit drift token
- verify syllable-final rows update the token only after full syllable hedging
- verify pause rows update the token only after full pause hedging
- verify shared metrics/metricalc row loading accepts the twelve-field schema
  and maps `duration`, `drift`, `intonation`, and `text` correctly

Integration tests:

- verify phonetizer emits twelve-field `_phone.txt` / `_ophone.txt` rows
- verify printer and metrics can still read realized phone files with the new
  drift field present
- verify representative demo outputs show the new column in the correct place

Manual verification:

- inspect a representative realized `_phone.txt` and `_ophone.txt` pair and
  confirm that drift changes only on unit-final rows and pause rows
- confirm that the final row-level drift token matches the final drift summary
  exposed in the same file's report/frontmatter path

---

# Rollback Plan

Revert the schema extension and restore the previous eleven-field phone-row
format.

Because this CR changes the serialized row contract, rollback must include:

- parser and serializer rollback
- documentation rollback
- demo artifact rollback
- any consumer changes that were made only to support the new field

---

# Related Issues

- [CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md)
- [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
- [CR-050](050-add-intonation-token-framework-and-silence-typing-to-phonetizer.md)
- [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md)
- [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
- [REQ-030](../req/030-phone-ophone-only-metrics-and-interval-rhythm-computation.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- [REQ-032](../req/032-phonetizer-intonation-and-three-pass-finalization.md)

---

# Tasks

## Implementation

- [ ] Extend the canonical phone-row schema with `drift`
- [ ] Update row builders, serializers, and parsers to the twelve-field format
- [ ] Write per-row drift tokens during duration realization
- [ ] Preserve frontmatter/report drift summary alongside the new row field
- [ ] Update downstream row consumers to accept the new schema

## Tests

- [ ] Add unit coverage for drift-token formatting and row update timing
- [ ] Update round-trip and integration tests for the twelve-field schema
- [ ] Update self-tests and demo validations that inspect phone rows

## Documentation

- [ ] Update phone-file guides and phonetizer docs for the new schema
- [ ] Update examples that show `_phone.txt` / `_ophone.txt` rows
- [ ] Document the difference between row-level drift trace and drift summary

## Review

- [ ] Verify acceptance criteria against representative realized phone files
- [ ] Confirm active docs no longer describe the row schema as eleven fields

---

# Implementation Blockers

## 2026-04-14 - CR sequencing is not yet open for implementation

- Type: `governance conflict`
- Observed: [CR-058](058-remove-synthetic-pause-allocation-from-metricalc.md)
  remains `Draft` and [CR-059](059-restructure-phonetizer-pauses-with-mini-band-recovery-discharge.md)
  remains `Blocked`, while this record is a later CR in the same sequence.
- Why blocked: repository governance requires CRs to be implemented in
  identifier order, so `CR-060` cannot be executed safely as an implementation
  target until the earlier phonetizer/metrics CRs ahead of it are resolved.
- Needed to unblock: move the earlier CRs ahead of this record to `Done`, or
  explicitly re-sequence/split the affected work under maintainer direction.
- Owner: `maintainer`
- Related refs: CR-058, CR-059, docs/internal/README.md

---

# Notes

- This CR is intentionally specification-only. Implementation is deferred.
- The paragraph or pause-type examples discussed elsewhere do not constrain this
  CR. The controlling requirement here is unit-final drift serialization,
  regardless of which specific pause subtype or length later records choose for
  a given structural situation.
