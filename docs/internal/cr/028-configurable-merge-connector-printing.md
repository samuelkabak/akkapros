---
cr_id: CR-028
status: Done
priority: High
impact: Mutative
created: 2026-03-31
updated: 2026-03-31
implements: 'REQ-020'
---

# Change Request: Configurable Merge-Connector Printing

# Summary

Add a new CLI option `--print-merger` to `printer` and `fullprosmaker` so
users can choose whether the merge connector `‿` is shown literally in acute,
bold, and XAR outputs.

The new default shall be to print a regular space instead of `‿` when the flag
is absent. Supplying `--print-merger` shall preserve the current visible-`
‿` behavior.

---

# Motivation

The printer currently surfaces prosodic merging explicitly with `‿` in several
user-facing outputs. That is valuable for analysis, but it is too marked as a
default reading format for some use cases. The project needs an opt-in model:
space-separated output by default, literal connector only when requested.

Because this changes rendered text and therefore fixtures, demos, and user
expectations, the behavior must be formalized as a compatibility-sensitive
output change rather than treated as an ad hoc formatting tweak.

---

# Scope

## Included

- Add `--print-merger` to `printer`.
- Add `--print-merger` to `fullprosmaker` and pass it through to the printer
  stage.
- Make acute, bold, and XAR renderers honor the new merge-connector mode.
- Change the default printed behavior from literal `‿` to space for those
  outputs.
- Record `print_merger` in YAML front matter options.
- Update regression tests, reference outputs, and documentation affected by the
  default-output change.

## Not Included

- Changing the `_tilde.txt` pivot format or the merge logic in prosody.
- Reinterpreting metrics prominence statistics.
- Changing file naming or stage ordering.
- Changing unrelated printer formatting behavior beyond merge-connector
  rendering.

---

# Current Behavior

The current printer emits the merge connector `‿` directly in user-facing acute,
bold, and XAR outputs. There is no CLI switch to suppress or replace it.

As a result:

1. `printer` always exposes the connector explicitly in those outputs.
2. `fullprosmaker` inherits the same explicit rendering in its printer-stage
   outputs.
3. Existing regression references and demos are pinned to literal `‿` in those
   formats.

---

# Proposed Change

Introduce an explicit print-layer switch with these semantics:

- default behavior, no flag:
  - acute, bold, and XAR outputs replace each visible `‿` with a regular space
- opt-in behavior, `--print-merger` supplied:
  - acute, bold, and XAR outputs render `‿` literally, preserving current
    behavior

Front matter behavior:

- printer outputs record `metadata.options.print_merger`
- `fullprosmaker` propagates the same option to generated printer outputs

Compatibility note:

- this is an intentional user-facing default-output change
- existing regression references and demos that assert visible `‿` will need
  to be updated unless they explicitly opt back in with `--print-merger`

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/print.py`
- `src/akkapros/cli/printer.py`
- `src/akkapros/cli/fullprosmaker.py`
- front matter option propagation helpers already used by stage CLIs

Design direction:
- handle merge-connector rendering in one shared printer-layer policy rather
  than per-format ad hoc substitutions
- keep the internal prosodic representation unchanged
- apply the policy only to the specified user-facing formats: acute, bold, XAR

CLI contract:
- `printer --print-merger`
- `fullprosmaker --print-merger`
- absence of the flag means render spaces instead of `‿`

Front matter contract:
- generated print outputs record `metadata.options.print_merger: true|false`

Testing contract:
- update current snapshots that depend on the default connector rendering
- add explicit coverage for both default-space and opt-in-connector modes

Documentation contract:
- update printer docs to describe the new default and the opt-in flag
- update full pipeline docs where printer options are summarized

---

# Files Likely Affected

`src/akkapros/lib/print.py`
`src/akkapros/cli/printer.py`
`src/akkapros/cli/fullprosmaker.py`
`docs/akkapros/printer.md`
`docs/akkapros/fullprosmaker.md`
`docs/GETTING_STARTED.md` or `README.md` if printer options are mirrored there
printer self-tests and pytest coverage for printer/fullprosmaker outputs
integration reference artifacts and demo outputs that currently show literal `‿`

---

# Acceptance Criteria

- [x] `printer` accepts `--print-merger`.
- [x] `fullprosmaker` accepts `--print-merger`.
- [x] Without `--print-merger`, acute outputs replace printed `‿` with spaces.
- [x] Without `--print-merger`, bold outputs replace printed `‿` with spaces.
- [x] Without `--print-merger`, XAR outputs replace printed `‿` with spaces.
- [x] With `--print-merger`, acute, bold, and XAR outputs preserve literal `‿`.
- [x] Printer output front matter records `metadata.options.print_merger`.
- [x] Full-pipeline printer outputs preserve `metadata.options.print_merger`
      through option propagation.
- [x] Existing tests are updated where necessary for the new default behavior.
- [x] New tests cover both default-space and explicit-connector modes.
- [x] Documentation explains that the new default is space rendering and that
      `--print-merger` restores literal `‿` printing.

---

# Risks / Edge Cases

Possible issues:

- Snapshot-heavy tests and demo outputs will change even though prosodic logic
  itself is unchanged.
- If the merge connector is replaced too early in the pipeline, internal logic
  could accidentally lose information needed by downstream formatting.
- If only some printer formats adopt the new policy, outputs may become
  inconsistent and confusing.
- Front matter must reflect the selected mode so users can distinguish whether
  a space reflects formatting choice or absence of merging.

---

# Testing Strategy

Unit/self-tests:

- printer default rendering replaces `‿` with spaces in acute output
- printer default rendering replaces `‿` with spaces in bold output
- printer default rendering replaces `‿` with spaces in XAR output
- `--print-merger` preserves literal `‿` in those outputs

Integration tests:

- `fullprosmaker` printer outputs use default space rendering without the flag
- `fullprosmaker` printer outputs preserve `‿` when the flag is supplied
- print-output front matter records `print_merger` correctly

Manual/spec review:

- inspect representative printer outputs in both modes
- inspect documentation examples for consistency with the new default

---

# Rollback Plan

If the new default causes unacceptable downstream disruption, revert to literal
`‿` as the default while keeping the internal design ready for a future
reintroduction of the option under a clearer migration plan.

---

# Related Issues

- Formal requirement: [REQ-020](../req/020-configurable-merge-connector-printing.md)
- Related existing requirement: [REQ-005](../req/005-multi-format-printer-output.md)
- Related existing requirement: [REQ-007](../req/007-full-pipeline-orchestration.md)
- Related existing requirement: [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md)
- Related existing requirement: [REQ-010](../req/010-built-in-self-tests-and-test-infrastructure.md)

---

# Tasks

## Implementation

- [x] Add `--print-merger` to `printer`.
- [x] Add `--print-merger` to `fullprosmaker` and pass it to the printer stage.
- [x] Centralize merge-connector rendering policy in the printer layer.
- [x] Record `print_merger` in print-output front matter options.

## Tests

- [x] Update existing expected outputs for the new default space rendering.
- [x] Add explicit tests for `--print-merger` preserving `‿`.
- [x] Add full-pipeline coverage for propagation and output behavior.

## Documentation

- [x] Update printer docs.
- [x] Update fullprosmaker docs.
- [x] Update any mirrored getting-started or README printer examples.

## Review

- [x] Confirm whether IPA output should remain unaffected.
- [x] Verify that the default-output change is reflected consistently in docs,
      tests, and demos.

IPA output remains unaffected. Plain `_xar.txt` also remains space-separated; the configurable visible connector applies only to acute, bold, and accented XAR rendering.

---

# Notes for CR-028

This CR is intentionally scoped as a print-layer contract change, not a
prosody-layer change. The merge relation remains encoded internally; only its
visible rendering in selected user-facing outputs changes.

The main compatibility cost is fixture churn: many regression references may
need to be updated because the absence of the new flag changes the default text
rendering.