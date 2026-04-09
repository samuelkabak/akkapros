---
cr_id: CR-038
status: Done
priority: High
impact: Mutative
created: 2026-04-05
updated: 2026-04-09
implements: 'REQ-003, REQ-004, REQ-005'
---

# Change Request: Distinguish Explicit and Internal Merge Connectors in Tilde Pivot

# Summary

Revise the prosody / prosmaker `_tilde` pivot contract so explicit user-requested
merges and automatic internal prosody merges no longer serialize with the same
connector.

Under this CR:

- `+` means explicit merge inherited from upstream input
- `&` means internal merge introduced by prosody / prosmaker

All downstream consumers of `_tilde.txt` must understand both connectors,
including metrics, printer, phonetizer-facing readers, validation helpers, and
full-pipeline orchestration.

This change is intended to preserve merge provenance directly in the pivot
artifact rather than reconstructing it later from front matter fields such as
`explicit_word_link_count`.

---

# Motivation

The current `_tilde` pivot uses `+` for both user-supplied merge structure and
automatic merges introduced by the prosody algorithm. That collapses two
different facts into one visible marker:

- explicit prosodic structure requested in the input
- automatic grouping introduced internally by the algorithm

When the pivot erases that distinction, downstream consumers must recover it by
indirect means or give up on it. Earlier discussions considered carrying the
difference in front matter, but the current redesign no longer accepts that as
the primary solution. The pivot itself must remain information-complete enough
to propagate merge provenance across stages.

The narrow fix is therefore to reserve one connector for explicit merges and a
second connector for internal merges. This preserves provenance at the stage
boundary where it matters most and avoids forcing metrics or phonetize-stage
consumers to depend on auxiliary counts.

---

# Scope

## Included

- Redefine the `_tilde` pivot contract so it distinguishes explicit and internal
  merges.
- Reserve `+` for explicit user-requested merges inherited from input.
- Reserve `&` for automatic internal merges introduced by prosody.
- Require `prosmaker` / `prosody` to serialize those two cases distinctly.
- Require all `_tilde` consumers to parse and preserve the distinction.
- Require phonetizer-facing contracts to preserve the distinction through
  boundary coding rather than through auxiliary front matter counters.
- Require regression tests and documentation updates for the changed pivot
  contract.

## Not Included

- Changing how the syllabifier treats explicit `+` in upstream input.
- Changing printer-layer visible rendering policy for merge connectors beyond
  consuming the more informative pivot.
- Replacing `_tilde` with a different pivot artifact.
- Introducing new front matter counters to recover the distinction that this CR
  now preserves directly in `_tilde`.

---

# Current Behavior

- Explicit input links already use `+` upstream.
- Prosody / prosmaker also serializes automatic merges using `+` in `_tilde`.
- Metrics, printer, and related consumers therefore see only one merge symbol.
- The pivot cannot by itself distinguish explicit user structure from automatic
  internal grouping.

This makes merge provenance harder to propagate and encourages downstream logic
to depend on side information rather than on the pivot contract itself.

---

# Proposed Change

Adopt the following `_tilde` connector rules.

- `+` marks explicit merge inherited from input.
- `&` marks internal merge created by prosody.
- Space continues to mark an ordinary word boundary.

Serialization requirements:

- If a linked group already exists explicitly in the input, `_tilde` preserves
  `+` at those link positions.
- If prosody creates a merge that was not explicitly requested, `_tilde`
  serializes that merge with `&`.
- Mixed units may contain both connector types when an explicit linked group is
  extended or resolved together with additional internal merging.
- Downstream consumers must not normalize `+` and `&` back into one generic
  merge marker during parsing.

Examples:

- explicit-only unit: `ana+šar~.ri`
- internal-only unit: `ana&šar~.ri`
- mixed unit: `u+ana&šar~.ri`

Propagation requirements:

- Metrics must understand both `+` and `&` as no-pause prosodic connectors.
- Printer must understand both `+` and `&` as internal merge relations while
  retaining any format-specific visible rendering policy.
- Phonetizer-facing contracts must preserve the distinction for internal-unit
  non-final word endings so `_phone` can reconstruct whether a non-final unit
  boundary came from explicit `+` or internal `&`.
- Validation helpers and full-pipeline stage logic must treat both symbols as
  legal `_tilde` structure.

Front matter direction:

- This CR intentionally does not solve the distinction by adding or relying on
  new front matter counters.
- If a downstream stage still records counts for validation, those counts are
  secondary and must not be the only source of merge provenance.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/prosody.py`
- `src/akkapros/cli/prosmaker.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/cli/metricalc.py`
- `src/akkapros/lib/print.py`
- `src/akkapros/cli/printer.py`
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `_tilde` validators, helpers, and docs

Design requirements:

- `_tilde` remains the canonical cross-stage artifact for merge provenance.
- Explicit and internal merges must be distinguishable from the text alone.
- Consumers must treat both `+` and `&` as within-unit links with no pause.
- Consumers that derive richer structure must preserve the provenance
  distinction rather than flattening it immediately.
- The changed connector contract is release-note-worthy because it changes the
  stable pivot format.

Phonetizer alignment:

- The `_phone` contract should preserve non-final word-end provenance inside a
  prosodic unit using distinct boundary codes for explicit versus internal
  merge endings.
- Under the current paired change to CR-036, `boundary=L` is used for internal
  `&`-merge word endings and `boundary=X` is used for explicit `+`-merge word
  endings.

---

# Files Likely Affected

`src/akkapros/lib/prosody.py`
`src/akkapros/cli/prosmaker.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/lib/print.py`
`src/akkapros/cli/printer.py`
`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/cli/fullprosmaker.py`
`tests/`
`docs/akkapros/`

---

# Acceptance Criteria

- [x] `prosmaker` / `prosody` preserves explicit input merges as `+` in
      `_tilde.txt`.
- [x] `prosmaker` / `prosody` serializes automatic internal merges as `&` in
      `_tilde.txt`.
- [x] `_tilde` documentation states clearly that `+` and `&` are both legal
      no-pause merge connectors with different provenance.
- [x] Metrics accepts both `+` and `&` as legal within-unit connectors.
- [x] Printer accepts both `+` and `&` as legal within-unit connectors.
- [x] Phonetizer-facing logic accepts both `+` and `&` and preserves the
      distinction for non-final word endings inside a prosodic unit.
- [x] Full-pipeline orchestration accepts `_tilde` files containing both `+`
      and `&`.
- [x] The merge-provenance distinction no longer depends on introducing a new
      front matter field.
- [x] Unit tests cover parsing and serialization of explicit-only, internal-
      only, and mixed merge chains.
- [x] Integration tests cover representative `_tilde` flows into metrics,
      printer, and phonetizer-facing consumers.
- [x] Documentation updates explain the connector distinction and the reason the
      pivot now carries it directly.
- [x] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [x] Documentation is updated in separate phonetizer and algorithm files,
  configuration/confwriter docs where relevant, and impacted downstream
  program docs such as fullprosmaker.

---

# Risks / Edge Cases

Possible issues:

- Existing `_tilde` fixtures and snapshot-based tests may assume `+` is the only
  merge connector.
- Some consumers may already flatten merge connectors during tokenization and
  will need careful updates.
- Mixed chains such as explicit `+` followed by internal `&` may expose hidden
  parser assumptions about one connector per unit.
- Validator logic that treats `&` as punctuation today may reject valid new
  `_tilde` content unless updated.

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for dual-
  connector parsing, serialization, and provenance-preserving downstream
  consumption

Unit tests:

- prosody serialization preserves explicit `+` links
- prosody serialization emits `&` for automatic merges
- `_tilde` parsing helpers accept both connectors
- metrics tokenization treats both connectors as no-pause unit links
- printer parsing treats both connectors as no-pause unit links
- phonetizer-facing boundary assignment distinguishes explicit versus internal
  non-final word endings

Integration tests:

- `syllabify -> prosmaker -> metrics` with explicit-only links
- `syllabify -> prosmaker -> metrics` with internal-only links
- `syllabify -> prosmaker -> metrics` with mixed `+` and `&`
- `syllabify -> prosmaker -> printer` with mixed `+` and `&`
- representative `_tilde -> _phone` conversion preserving explicit versus
  internal merge provenance

Manual review:

- inspect representative `_tilde` lines for explicit-only, internal-only, and
  mixed merge chains
- inspect CR-036 and phonetizer docs so the boundary contract matches the new
  connector distinction exactly

---

# Rollback Plan

If the split connector contract proves too disruptive, revert the `_tilde`
serialization, parser updates, and related docs together in one coordinated
change. Partial rollback is discouraged because it would leave some consumers
expecting two connectors while others still emit or accept only one.

---

# Related Issues

- [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md)
- [REQ-003](../req/003-bimoraic-prosody-realization-algorithm.md)
- [REQ-004](../req/004-metrics-computation.md)
- [REQ-005](../req/005-multi-format-printer-output.md)
- [REQ-007](../req/007-full-pipeline-orchestration.md)
- [CR-036](036-define-phonetizer-phoneme-framework.md)

---

# Tasks

## Implementation

- [x] Preserve explicit `+` merges in `_tilde`
- [x] Serialize automatic prosody merges as `&`
- [x] Update `_tilde` consumers to accept both connectors
- [x] Preserve the distinction through phonetizer-facing boundary encoding

## Tests

- [x] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [x] Add pytest unit coverage for dual-connector parsing and serialization
- [x] Add pytest integration coverage across prosody, metrics, printer, and
  phonetizer

## Documentation

- [x] Update `docs/akkapros/phonetizer.md` for the changed `_tilde` input
  contract and downstream boundary semantics
- [x] Update `docs/akkapros/phonetizer-algorithm.md` for explicit-versus-
  internal merge provenance rules
- [x] Update `docs/akkapros/configuration.md` and `docs/akkapros/confwriter.md`
  if connector-related examples or validation text are affected
- [x] Update `_tilde` pivot docs, prosody docs, and impacted downstream stage
  docs including `docs/akkapros/fullprosmaker.md` so all `_tilde`
  consumers document the dual connector contract

## Review

- [x] Verify acceptance criteria

---

# Notes for CR-038

This CR changes the information density of the `_tilde` pivot intentionally.
The point is not merely to rename one connector, but to stop collapsing two
different merge sources into one symbol. The pivot should carry that provenance
directly so later stages do not have to reconstruct it indirectly.