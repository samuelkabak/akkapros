---
cr_id: CR-037
status: Draft
priority: High
impact: Mutative
created: 2026-04-05
updated: 2026-04-05
implements: 'ADR-004, REQ-004, REQ-005, REQ-011'
---

# Change Request: Preserve punctuation armor in tilde pivot

# Summary

Change the internal `_tilde` pivot contract so that punctuation and escaped
non-Akkadian chunks armored by the syllabifier as `⟦...⟧` remain armored in the
output of prosmaker.

Under this CR:

- `prosmaker` preserves punctuation armor when writing `<prefix>_tilde.txt`
- `metricalc` is updated to consume the armored `_tilde` contract directly
- `printer` is updated to consume armored `_tilde` and de-armor only when
  producing user-facing output
- punctuation tokenization and short/long pause identification remain in
  metrics for now, but the logic must be isolated in one dedicated helper that
  is easy to reuse later from `phonetizer`

Because `_tilde` is the central internal pivot defined by
[ADR-004](../adr/004-stage-pipeline-and-pivot-format.md), this CR requires
extensive testing and explicit documentation updates across all affected
internal and user-facing stage contracts.

---

# Motivation

The syllabifier already performs the hard and explicit work of identifying
punctuation and preserve-block content and armoring it as `⟦...⟧`. If prosmaker
later removes that armor and writes ordinary punctuation back into `_tilde`, the
metrics stage must detect and classify punctuation again from plain text.

That is a weaker contract than the upstream stage already provided. It makes
metrics sensitive to formatting drift, duplicates parsing responsibility, and
reduces the scientific value of the strict punctuation-classification policy
defined by [REQ-011](../req/011-punctuation-whitelist-and-cli-extension.md).

Keeping the armor in `_tilde` preserves explicit punctuation structure at the
main internal pivot while still allowing the printer to present ordinary text to
users. This makes later punctuation tokenization easier, improves pause-class
identification, and prepares the logic for future migration into the phonetizer
stage without forcing that migration now.

---

# Scope

## Included

- Redefine the `_tilde` pivot contract so armored punctuation and escaped spans
  survive the prosody stage unchanged.
- Require `prosmaker` to preserve `⟦...⟧` armor in `<prefix>_tilde.txt`.
- Require `metricalc` to read the armored `_tilde` representation directly.
- Require `printer` to read the armored `_tilde` representation and restore
  normal visible punctuation only in user-facing outputs.
- Keep punctuation tokenization and short/long pause identification in metrics
  for the current architecture step.
- Require that metrics isolate this punctuation-to-pause handling in one
  dedicated helper function with a narrow reusable interface, because the logic
  is expected to move later to `phonetizer`.
- Require extensive unit, integration, and pivot-contract regression testing.
- Require documentation updates for prosody, metrics, printer, and full-pipeline
  descriptions.

## Not Included

- Moving punctuation tokenization logic into `phonetizer` in this CR.
- Redesigning the underlying short-pause versus long-pause model.
- Replacing metrics as the current owner of pause classification.
- Redesigning the phonetizer artifact contract beyond acknowledging future reuse.
- Changing user-facing printer outputs other than the internal source they read.

---

# Current Behavior

- [REQ-002](../req/002-syllabification.md) specifies that punctuation and
  non-Akkadian chunks are armored as `⟦...⟧` in syllabifier output.
- [REQ-004](../req/004-metrics-computation.md) specifies that metrics consumes
  `_tilde`.
- [REQ-005](../req/005-multi-format-printer-output.md) specifies that printer
  also consumes `_tilde`.
- The current internal contract does not explicitly require prosmaker to keep
  punctuation armored in `_tilde`.
- If prosmaker restores raw punctuation into `_tilde`, both metrics and printer
  depend on a weaker and less explicit pivot format than the syllabifier had
  already produced.

This creates a sensitive stage boundary at the central pivot.

---

# Proposed Change

Adopt the following `_tilde` pivot contract.

- `⟦...⟧` escape armor is part of the internal pivot representation, not a
  temporary syllabifier-only convenience.
- `prosmaker` shall preserve armored punctuation and escaped chunks when it
  writes `<prefix>_tilde.txt`.
- `_tilde` remains an internal pivot and may therefore retain machine-oriented
  markers that are not meant for direct end-user presentation.
- `metricalc` shall consume the armored representation directly rather than
  relying on raw punctuation restored by prosody.
- `printer` shall consume the armored representation and perform de-armoring as
  part of output rendering.

Metrics-side handling requirements:

- Metrics continues to own punctuation tokenization and short/long pause
  identification in this transition step.
- That handling must be isolated in one dedicated helper function or helper
  family with a small explicit interface.
- The helper must accept armored punctuation input and return a normalized
  classification suitable for pause accounting.
- The helper must be documented as intentionally reusable from a later
  phonetizer migration.
- Metrics must not scatter punctuation parsing across unrelated code paths.

Printer-side handling requirements:

- Printer must accept armored punctuation in `_tilde` as a supported input
  contract.
- Printer must de-armor punctuation only when generating user-facing formats.
- Visible printer outputs should remain unchanged unless a later CR explicitly
  changes presentation behavior.

Pivot-format invariants:

- Accentuation markers, hiatus markers, word markers, and punctuation armor may
  co-exist in `_tilde`.
- Punctuation classification decided upstream remains explicit in the internal
  pivot instead of being re-inferred from plain text.
- This pivot-format change is release-note-worthy because it changes the stable
  intermediate contract defined by [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md).

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
- `src/akkapros/cli/fullprosmaker.py`
- related stage and contract documentation

Design requirements:

- `_tilde` remains the central internal pivot for downstream analysis and
  rendering, but now with punctuation armor preserved as part of the contract.
- The prosody stage must preserve `⟦...⟧` chunks as structurally opaque units
  except where prosody-specific metadata markers already have defined behavior.
- Metrics must expose one explicit helper for armored punctuation tokenization
  and short/long pause classification.
- The metrics helper must be easy to call from a later phonetizer stage without
  requiring metrics-wide state.
- Printer must isolate its de-armoring behavior to presentation rendering,
  rather than redefining the pivot contract.
- Full-pipeline orchestration and documentation must reflect the changed pivot
  contract.

Suggested helper expectations for metrics:

- Input: one armored punctuation or escaped token from `_tilde`, plus the
  declared punctuation configuration context.
- Output: normalized pause/punctuation classification sufficient for metrics
  accounting, including short versus long pause class when applicable.
- Failure mode: explicit error on armored content that cannot be classified
  under the declared punctuation rules.

This CR intentionally keeps the logic in metrics for now, because the immediate
goal is to stabilize the pivot contract first. The later migration of this logic
into `phonetizer` should reuse the isolated helper design rather than re-derive
punctuation semantics from scratch.

---

# Files Likely Affected

`src/akkapros/lib/prosody.py`
`src/akkapros/cli/prosmaker.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/lib/print.py`
`src/akkapros/cli/printer.py`
`src/akkapros/cli/fullprosmaker.py`
`docs/akkapros/prosmaker.md`
`docs/akkapros/metricalc.md`
`docs/akkapros/metrics-computation.md`
`docs/akkapros/printer.md`
`docs/akkapros/fullprosmaker.md`
`tests/test_integration.py`
`tests/test_metrics_stats.py`
`tests/test_print_merger.py`
`tests/test_selftests_cli.py`
`tests/test_selftests_lib.py`

---

# Acceptance Criteria

- [ ] `prosmaker` preserves armored punctuation and escaped chunks as `⟦...⟧`
      when writing `<prefix>_tilde.txt`.
- [ ] `_tilde` is documented as allowing punctuation armor as part of the
      stable internal pivot contract.
- [ ] `metricalc` accepts armored punctuation in `_tilde` as its supported
      input contract.
- [ ] `printer` accepts armored punctuation in `_tilde` as its supported input
      contract.
- [ ] `printer` restores normal visible punctuation only during rendering of
      user-facing outputs.
- [ ] Visible printer outputs remain unchanged for existing valid fixtures,
      unless a later CR explicitly changes presentation behavior.
- [ ] Metrics retains ownership of punctuation tokenization and short/long
      pause identification in this architecture step.
- [ ] Metrics exposes a dedicated helper function or helper family for armored
      punctuation tokenization and pause classification.
- [ ] The dedicated metrics helper is documented and shaped for later reuse by
      `phonetizer`.
- [ ] Metrics does not scatter punctuation tokenization logic across unrelated
      code paths after this change.
- [ ] The new pivot contract is covered by extensive unit tests.
- [ ] The new pivot contract is covered by extensive integration tests across at
      least `syllabify -> prosmaker -> metrics` and `syllabify -> prosmaker -> printer`.
- [ ] Regression fixtures verify that punctuation armored in `_syl` remains
      armored in `_tilde`.
- [ ] Regression fixtures verify that metrics can classify short versus long
      pause behavior from armored punctuation without relying on raw restored
      punctuation.
- [ ] Regression fixtures verify that printer still emits unchanged visible
      punctuation in user-facing outputs.
- [ ] User-facing and developer-facing docs are updated extensively to explain
      the pivot-format change and its rationale.
- [ ] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [ ] Documentation is updated in separate phonetizer and algorithm files,
  configuration/confwriter docs where relevant, and impacted downstream
  program docs such as fullprosmaker.

---

# Risks / Edge Cases

Possible issues:

- This is a pivot-format change, so its blast radius is larger than a normal
  stage-local edit.
- Existing tests or downstream tools may assume raw punctuation in `_tilde`.
- Prosody logic may accidentally alter armored spans if the boundaries are not
  treated as opaque during serialization.
- Printer and metrics may drift if one consumes armored punctuation and the
  other silently de-arms earlier.
- The isolated metrics helper may still grow hidden dependencies if not kept
  deliberately narrow.

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for
  punctuation armor preservation, metrics pause classification, printer
  de-armoring boundaries, and stage-contract invariants

Unit tests:

- prosody serialization preserves armored punctuation unchanged in `_tilde`
- metrics armored-punctuation helper classifies representative short-pause and
  long-pause tokens correctly
- metrics armored-punctuation helper fails explicitly on unsupported armored
  punctuation content
- printer de-armors only at rendering time and not in pivot parsing utilities
- printer user-facing renderers preserve current visible punctuation behavior

Integration tests:

- `syllabify -> prosmaker -> metrics` run with punctuation-bearing fixtures
  where `_syl` and `_tilde` are both asserted explicitly
- `syllabify -> prosmaker -> printer` run with punctuation-bearing fixtures
  where `_tilde` stays armored and rendered output is de-armored
- full-pipeline orchestration coverage proving the changed pivot contract is
  handled consistently across stage boundaries

Pivot-contract regression tests:

- add or update gold fixtures for `_syl`, `_tilde`, metrics outputs, and printer
  outputs where punctuation and preserve blocks are present
- include mixed-content cases combining Akkadian text, punctuation, escaped
  spans, hiatus markers, and accent markers
- verify no silent de-armoring occurs before printer-facing output generation

Manual review:

- inspect the documented `_tilde` contract in user and internal docs
- inspect the metrics helper interface for narrow, reusable design
- inspect release notes or unreleased notes for the pivot-format change

Because this changes a central pivot format, testing must be treated as
extensive and mandatory rather than as a minimal smoke-test addition.

---

# Rollback Plan

If the armored `_tilde` contract proves too disruptive, revert prosmaker,
metrics, and printer together to the prior raw-punctuation pivot behavior in one
coordinated rollback. Partial rollback is discouraged because mixed contracts
would leave the central pivot ambiguous and break stage interoperability.

---

# Related Issues

- [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md)
- [REQ-004](../req/004-metrics-computation.md)
- [REQ-005](../req/005-multi-format-printer-output.md)
- [REQ-011](../req/011-punctuation-whitelist-and-cli-extension.md)
- [CR-003](003-change-escape-delimiters.md)
- [CR-012](012-enforce-punctuation-whitelist-and-cli-extension.md)
- [review-005](../review/005-punctuation-armor-through-tilde-review.md)

---

# Tasks

## Implementation

- [ ] Preserve `⟦...⟧` armor in prosmaker `_tilde` output
- [ ] Update metrics to consume armored `_tilde`
- [ ] Isolate metrics punctuation tokenization and pause classification in a
      dedicated reusable helper
- [ ] Update printer to consume armored `_tilde` and de-armor at render time
- [ ] Update full-pipeline orchestration for the changed pivot contract

## Tests

- [ ] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [ ] Add extensive pytest unit coverage for prosody serialization, metrics
  helper behavior, and printer de-armoring
- [ ] Add extensive pytest integration coverage for both metrics-facing and
  printer-facing stage paths
- [ ] Add pivot gold fixtures covering punctuation-bearing `_syl` and `_tilde`

## Documentation

- [ ] Update `docs/akkapros/phonetizer.md` for the changed pivot input contract
  and downstream stage expectations
- [ ] Update `docs/akkapros/phonetizer-algorithm.md` for punctuation armor and
  pause-classification semantics
- [ ] Update `docs/akkapros/configuration.md` and `docs/akkapros/confwriter.md`
  if punctuation-related config or examples are affected
- [ ] Update user docs for prosmaker, metrics, printer, and
  `docs/akkapros/fullprosmaker.md`
- [ ] Update internal docs that describe `_tilde` as the pivot contract
- [ ] Record the pivot-format change in release-facing notes

## Review

- [ ] Verify acceptance criteria
- [ ] Confirm the isolated metrics helper is reusable enough for later
      phonetizer migration

---

# Notes for CR-037

This CR intentionally changes an internal pivot format. That is the point of the
change, not an incidental side effect. The design goal is to preserve explicit
punctuation structure through internal processing, keep metrics as the temporary
owner of pause classification, and prepare that logic for later extraction to
phonetizer without requiring two separate re-parsing designs.