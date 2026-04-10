---
req_id: REQ-028
status: Implemented
priority: High
impact: Mutative
created: 2026-04-07
updated: 2026-04-10
related_adrs: 'ADR-042, ADR-037, ADR-036'
implemented_by: 'CR-043'
---

# Requirement: Effective Runtime Config Object, Path Overrides, and Program-Scoped Help

# Summary

Every config-consuming runtime CLI shall resolve one effective in-memory config
object before processing. That object shall always begin from canonical default
values, optionally layer `--conf FILE` values on top, and then layer explicit
CLI overrides, with repeatable `-t/--option KEY=VALUE` overrides taking final
precedence over dedicated config-backed flags such as `--style`.

This requirement also standardizes two user-facing behaviors across runtime
CLIs: validation must run against the program-relative effective config before
processing begins, and `--help` must become both program-scoped and path-
scoped. `confwriter` is explicitly excluded from the runtime-resolution part of
this requirement because it edits config state rather than consuming runtime
config for pipeline processing.

---

# Motivation

The package already has a package-wide YAML schema and centralized help text,
but the operational model is still too flag-centric and not explicit enough
about the actual runtime config object. Users need one coherent rule: runtime
tools should always work from an effective config in memory, regardless of
whether that config came from a file or from defaults.

The same change is needed for discoverability. If schema paths are becoming the
preferred interface, users need a universal `-t/--option KEY=VALUE` surface, a
clear deprecation story for dedicated config-backed flags, and help output that
can explain either the whole program view or one specific config subtree.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given any config-consuming runtime CLI other than `confwriter`, when the
      command starts normal processing, then it first resolves one effective
      in-memory config object and passes that effective config into library
      processing.
- [ ] Given no `--conf FILE` argument is supplied, when a runtime CLI resolves
      its effective config, then the config object is still materialized in
      memory from canonical defaults before CLI overrides are applied.
- [ ] Given defaults-only runtime materialization includes the phonetize-owned
      subtree, when canonical runtime defaults are inspected, then
      `phonetize.process.timing_model.accentuation_distribution_policy=85_15`
      and `phonetize.process.timing_model.drift_policy=extensible` are present
      in the effective config.
- [ ] Given `--conf FILE` is supplied, when the file omits some supported keys,
      then those missing keys still retain canonical default values in the
      effective in-memory config object.
- [ ] Given a config-backed dedicated CLI flag and a matching config-file value
      are both supplied, when effective config is resolved, then the dedicated
      CLI flag overrides the file value.
- [ ] Given a repeatable `-t KEY=VALUE` or `--option KEY=VALUE` override and a
      matching dedicated CLI flag are both supplied, when effective config is
      resolved, then the path-based override wins.
- [ ] Given a repeatable `-t KEY=VALUE` or `--option KEY=VALUE` override and a
      matching config-file value are both supplied, when effective config is
      resolved, then the path-based override wins.
- [ ] Given a runtime CLI supports config-backed settings, when its parser is
      built, then it accepts repeatable `-t KEY=VALUE` and
      `--option KEY=VALUE` overrides for full schema paths.
- [ ] Given a path-based override references an unknown key path or provides an
      invalid value for a known key path, when the command validates effective
      config, then processing fails before the program begins its main work.
- [ ] Given a runtime CLI is about to process input, when effective config has
      been resolved, then the command validates `common` plus the config
      sections relevant to that program before processing begins.
- [ ] Given `fullprosmaker` is about to run, when effective config is
      validated, then validation covers `common` plus the shared stage sections
      relevant to that orchestration run rather than a duplicated
      `fullprosmaker` config block.
- [ ] Given a config-backed dedicated option such as `--style` still exists,
      when runtime CLIs are documented and rendered in help output, then that
      dedicated option is marked deprecated rather than presented as the
      preferred interface.
- [ ] Given a deprecated dedicated config-backed option still exists, when help
      output is rendered, then deprecated options appear after the active
      config-path-driven sections.
- [ ] Given a runtime CLI is invoked with `python phonetizer.py --help`, when
      help is rendered, then the output is equivalent to the default phonetizer
      program view for `common` plus `phonetize`.
- [ ] Given a runtime CLI is invoked with `python phonetizer.py --help phonetize`,
      when help is rendered, then the output is the same scoped config help as
      the default phonetizer program view for that owned section.
- [ ] Given a runtime CLI is invoked with
      `python phonetizer.py --help phonetize.process.timing_model.durations`,
      when help is rendered, then only that requested schema/help subtree is
      printed.
- [ ] Given a runtime CLI has no `--conf FILE`, when a user supplies only a
      positional input plus one or more path overrides, then the command still
      resolves a valid effective config from defaults plus those overrides.
- [ ] Given some command-line arguments are not part of the config schema, when
      the CLI interface is documented, then those CLI-only arguments remain
      supported and are not deprecated by this requirement.
- [ ] Given positional input paths, explicit source selectors, `--help`,
      `--test`, and config-authoring operations are not config-backed values,
      when the interface is reviewed, then they remain CLI-only rather than
      being forced into the config schema.
- [ ] Given `confwriter` is reviewed against this requirement, when runtime
      config resolution rules are applied, then `confwriter` is excluded from
      the effective-runtime-config-object model because it edits config rather
      than using runtime config for pipeline processing.
- [ ] Given documentation is updated, when users read config and CLI guidance,
      then the docs explain the effective config object, override precedence,
      universal `-t/--option` usage, deprecated dedicated flags, CLI-only
      arguments, validation timing, and scoped help behavior.

---

# User Story (optional)
> As a user running one or more Akkadian pipeline programs, I want every
> runtime CLI to behave as if it is using one explicit config object in memory
> so that file-based config, default values, and command-line overrides all
> follow one consistent rule.

---

# Interface Notes
- Effective precedence:
  - `-t/--option KEY=VALUE`
  - explicit dedicated config-backed CLI flag (deprecated compatibility alias)
  - `--conf FILE` value
  - canonical in-memory defaults
- Runtime scope:
  - applies to config-consuming runtime CLIs under `src/akkapros/cli/`
  - does not apply to `confwriter` as a runtime-processing model
- Validation timing:
  - after defaults, file values, dedicated flags, and path overrides are
    merged
  - before library processing begins
  - against `common` plus the sections the command actually consumes
- Help behavior:
  - `program.py --help` prints the default program-scoped help view
  - `program.py --help SOME.PATH` prints the requested schema/help subtree only
  - default help view includes the relevant `common` view and the command's
    owned or consumed config sections
      - phonetize-owned subtree examples use `phonetize.process.timing_model.*`
  - deprecated dedicated flags remain visible but are rendered after active
    sections
- CLI-only arguments:
  - positional input paths
  - `--help`
  - `--test`
  - other operational arguments not represented in schema
- Affected components:
  - runtime CLI entrypoints under `src/akkapros/cli/`
  - shared config-resolution utilities under `src/akkapros/lib/`
  - shared validation helpers under `src/akkapros/lib/`
  - shared help registry under `src/akkapros/lib/helpmsg.py`

---

# Open Questions
- [x] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: large
- Migration:
  - centralize runtime config resolution before per-program processing
  - add universal `-t/--option` parsing to runtime CLIs
  - mark dedicated config-backed flags as deprecated but keep them functional
  - add scoped help rendering with program-root mappings
  - update docs to prefer config-path usage over dedicated config-backed flags

# Related
- Related ADRs: [ADR-042](../adr/042-effective-runtime-config-object-path-overrides-and-program-scoped-help.md), [ADR-037](../adr/037-centralized-help-message-registry-for-cli-and-config-docs.md), [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- Parent REQ: [REQ-022](022-package-wide-yaml-config-and-confwriter.md)
- Implementation CRs: [CR-043](../cr/043-adopt-effective-runtime-config-path-overrides-and-scoped-help-across-runtime-clis.md)

# Non-Goals
- This requirement does not remove deprecated dedicated config-backed flags in
  the same wave that introduces path-based overrides.
- This requirement does not force CLI-only operational arguments into the
  config schema.
- This requirement does not make `confwriter` a runtime-processing CLI.
- This requirement does not require one duplicated `fullprosmaker` config
  namespace.

# Security / Safety Considerations
- Validating the effective config before processing reduces the chance that a
  command starts work with an internally inconsistent runtime view.
- One canonical precedence rule reduces user confusion about which value is in
  force.
- Keeping CLI-only operational arguments out of schema helps avoid polluting
  persisted config files with one-off runtime paths or execution controls.