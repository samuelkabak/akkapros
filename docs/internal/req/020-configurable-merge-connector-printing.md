---
req_id: REQ-020
status: Implemented
priority: High
impact: Mutative
created: 2026-03-31
updated: 2026-03-31
related_adrs: 'ADR-011, ADR-021, ADR-022, ADR-027'
implemented_by: 'CR-028'
---

# Requirement: Configurable Merge-Connector Printing

# Summary

The system shall add a new printing option named `print_merger` that controls
how the merge connector `‿` is rendered in `_accent_acute`, `_accent_bold`, and
`_accent_xar` outputs.

When `--print-merger` is present, the printer shall render the merge connector
literally as `‿`, matching current behavior. When the option is absent, the
default behavior shall replace each printed merge connector `‿` with a regular
space ` ` in those user-facing outputs.

This requirement applies to both standalone `printer` usage and the printer
stage triggered through `fullprosmaker`. The selected behavior shall also be
recorded in YAML front matter option metadata.

---

# Motivation

The current printer emits `‿` in user-facing acute, bold, and XAR outputs.
That is useful for explicit prosodic inspection, but it is not always the best
default for readers who want a smoother reading text or downstream publication
material where the visual connector is distracting.

Users need a simple switch that preserves the current explicit connector when
desired, while making the more typographically neutral space-separated output
the default behavior. Because this changes emitted text and existing snapshots,
the behavior must be specified explicitly and covered by regression tests.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [x] Given `printer` is run without `--print-merger`, when `_accent_acute`
      output is generated, then merge connectors are rendered as spaces rather
      than literal `‿` characters.
- [x] Given `printer` is run without `--print-merger`, when `_accent_bold`
      output is generated, then merge connectors are rendered as spaces rather
      than literal `‿` characters.
- [x] Given `printer` is run without `--print-merger`, when `_accent_xar`
      output is generated, then merge connectors are rendered as spaces rather
      than literal `‿` characters.
- [x] Given `printer` is run with `--print-merger`, when `_accent_acute`,
      `_accent_bold`, or `_accent_xar` outputs are generated, then merge
      connectors are rendered literally as `‿`, preserving current behavior.
- [x] Given `fullprosmaker` is run without `--print-merger`, when it generates
      printer-stage acute, bold, or XAR outputs, then merge connectors are
      rendered as spaces by default.
- [x] Given `fullprosmaker` is run with `--print-merger`, when it generates
      printer-stage acute, bold, or XAR outputs, then merge connectors are
      rendered literally as `‿`.
- [x] Given IPA output is generated, when `--print-merger` is omitted or
      supplied, then IPA behavior is unchanged unless the implementation
      already routes IPA through the same merge-rendering helper and the
      project explicitly decides otherwise.
- [x] Given printer output front matter is emitted, when `--print-merger` is
      absent, then `metadata.options.print_merger` is present with value
      `false`.
- [x] Given printer output front matter is emitted, when `--print-merger` is
      supplied, then `metadata.options.print_merger` is present with value
      `true`.
- [x] Given `fullprosmaker` generates downstream printer artifacts, when front
      matter options are inherited, then `metadata.options.print_merger` is
      preserved in the generated print outputs.
- [x] Given the implementation is complete, when regression tests are run,
      then existing tests are updated where necessary to match the new default
      space-rendering behavior and new coverage verifies the opt-in `‿`
      behavior.
- [x] Given documentation is updated, when users read printer and
      full-pipeline docs, then they can see that the new default is space
      rendering and that `--print-merger` restores literal `‿` printing.

---

# User Story (optional)
> As a user generating readable accent outputs, I want merged words to print
> with ordinary spaces by default, while still being able to opt back into the
> explicit `‿` connector when I need prosodic inspection.

---

# Interface Notes
- CLI additions:
  - `printer --print-merger`
  - `fullprosmaker --print-merger`
- Default behavior:
  - no flag means render printed merge connector as space in acute, bold, and
    XAR outputs
- Opt-in behavior:
  - `--print-merger` means render printed merge connector as literal `‿`
- YAML front matter:
  - `metadata.options.print_merger: true|false`
- Affected components:
  - `src/akkapros/lib/print.py`
  - `src/akkapros/cli/printer.py`
  - `src/akkapros/cli/fullprosmaker.py`
  - front matter option propagation helpers as needed
  - printer and full-pipeline tests
  - printer and full-pipeline documentation

---

# Open Questions
- [x] IPA output remains unaffected by `--print-merger`; the option applies
      only to acute, bold, and accented XAR rendering.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: small
- Preferred implementation shape: centralize merge-connector rendering in the
  printer layer rather than branching separately in each formatter.
- Migration: update existing expected outputs and regression references that
  currently assert literal `‿` in acute, bold, and XAR outputs.

# Related
- Related ADRs: [ADR-011](../adr/011-multi-format-printer-outputs.md),
  [ADR-021](../adr/021-multi-target-printer-architecture-contract.md),
  [ADR-022](../adr/022-output-format-public-contract-boundaries.md),
  [ADR-027](../adr/027-yaml-front-matter-for-cli-pipeline-files.md)
- Related REQs: [REQ-005](005-multi-format-printer-output.md),
  [REQ-007](007-full-pipeline-orchestration.md),
  [REQ-013](013-cli-file-front-matter-and-metadata-propagation.md),
  [REQ-010](010-built-in-self-tests-and-test-infrastructure.md)
- Implementation CRs: [CR-028](../cr/028-configurable-merge-connector-printing.md)

# Non-Goals
- This requirement does not change the underlying `_tilde.txt` pivot format.
- This requirement does not change merge detection or prosodic grouping logic.
- This requirement does not require changes to metrics computations.
- This requirement does not change output filenames.

# Security / Safety Considerations
- This is primarily a presentation-contract change, but the selected printing
  mode must be recorded in front matter so generated artifacts remain
  interpretable.
- Documentation must call out that the default behavior changes, because
  downstream snapshot consumers may otherwise misread the changed outputs.