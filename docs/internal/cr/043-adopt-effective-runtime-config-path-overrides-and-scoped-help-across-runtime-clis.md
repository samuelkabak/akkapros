---
cr_id: CR-043
status: Draft
priority: High
impact: Mutative
created: 2026-04-07
updated: 2026-04-07
implements: 'ADR-042, REQ-028, REQ-022'
---

# Change Request: Adopt effective runtime config, path overrides, and scoped help across runtime CLIs

# Summary

Adopt one explicit effective runtime config object across config-consuming
runtime CLIs, add universal repeatable `-t/--option KEY=VALUE` overrides, and
standardize program-scoped plus path-scoped help rendering.

This change keeps `--conf FILE` as an input source when present, but it also
requires every runtime CLI to materialize the same config object in memory when
`--conf` is absent. Dedicated config-backed flags such as `--style` remain
available temporarily as deprecated compatibility aliases, while path-based
schema overrides become the preferred interface. `confwriter` is explicitly
excluded from the runtime-resolution model because it edits config rather than
using runtime config for pipeline processing.

---

# Motivation

[ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md)
and [ADR-037](../adr/037-centralized-help-message-registry-for-cli-and-config-docs.md)
established the package-wide YAML schema and the shared help-text registry, but
they do not yet give runtime CLIs one fully specified operational model.

Current risk areas:

- some commands may still behave as if parser defaults are the runtime source
  when `--conf` is absent instead of using one explicit effective config object
- config-backed dedicated flags may continue to grow as a parallel interface
  instead of becoming compatibility aliases over canonical schema paths
- validation may happen too early, too late, or against the wrong subset of
  config
- help output may continue to expose a flat flag-centric surface even after the
  schema-path model becomes preferred

The repository now needs one implementation CR that makes the runtime config
model, override precedence, validation point, and help behavior concrete across
runtime CLIs.

---

# Scope

## Included

- Add one shared runtime config-resolution helper for config-consuming runtime
  CLIs under `src/akkapros/cli/`.
- Require that helper to materialize an effective in-memory config object from
  canonical defaults even when `--conf FILE` is absent.
- Overlay `--conf FILE` values onto that in-memory default object when a file
  is supplied.
- Keep dedicated config-backed CLI flags working, but mark them deprecated.
- Add universal repeatable `-t KEY=VALUE` and `--option KEY=VALUE` parsing for
  config-backed overrides on runtime CLIs.
- Make path-based overrides higher precedence than dedicated config-backed
  flags.
- Run program-scoped config validation after all overrides are applied and
  before processing begins.
- Standardize `--help` so default help is program-scoped and `--help SOME.PATH`
  is subtree-scoped.
- Render deprecated dedicated config-backed flags after active help sections.
- Keep CLI-only non-config options such as input files, `--help`, `--test`,
  and similar operational controls outside the deprecation wave.
- Update documentation for the new preferred interface and the compatibility
  transition.
- Add built-in `run_tests()` coverage and pytest coverage for resolution,
  deprecation, validation, and help behavior.

## Not Included

- Removing deprecated dedicated config-backed flags in the same change.
- Forcing `confwriter` into the runtime-processing config-resolution model.
- Moving positional input paths or other CLI-only operational arguments into
  the persisted config schema.
- Creating a duplicate `fullprosmaker` config namespace for stage-owned
  settings.

---

# Current Behavior

The repository already has `--conf FILE` support work underway and a shared
config schema, but the runtime operational model is still incomplete.

Current gaps:

- the internal spec does not yet require every runtime CLI to work from one
  effective config object in memory
- the preferred schema-path override interface is not yet standardized across
  runtime CLIs
- config-backed dedicated flags are not yet framed as deprecated aliases over
  schema paths
- program-relative validation timing is not yet standardized
- help behavior is not yet defined as both program-scoped and path-scoped

---

# Proposed Change

Adopt the following runtime CLI contract.

## 1. Effective runtime config resolution

Every config-consuming runtime CLI other than `confwriter` resolves one
effective config object before processing starts.

Resolution order:

1. materialize canonical defaults in memory
2. if `--conf FILE` is supplied, overlay file values on that in-memory config
3. apply explicit dedicated config-backed CLI flags
4. apply repeatable `-t/--option KEY=VALUE` path overrides

Result:

- the runtime libraries consume one effective config object regardless of
  whether a config file was supplied
- missing file keys still inherit canonical defaults
- path overrides become the highest-precedence config-backed interface

## 2. Dedicated flag deprecation model

Dedicated config-backed flags remain functional during the transition.

Examples:

- `--style`
- `--phonetize-geminate-policy`
- similar dedicated flags that correspond directly to persisted config keys

Required behavior:

- keep them working
- mark them deprecated in help text and docs
- position them after the active config-path help sections
- ensure they still map to canonical schema paths rather than to independent
  local option state

CLI-only operational arguments that are not config-backed remain active and are
not deprecated in this CR.

## 3. Program-relative validation

Before any runtime CLI begins its main processing, it validates the effective
config it will actually use.

Validation scope:

- always validate `common`
- validate the program's owned or consumed config sections
- for orchestrators such as `fullprosmaker`, validate the relevant shared stage
  sections instead of a duplicated fullprosmaker config block

Validation must run after defaults, file values, dedicated flags, and path
overrides are merged.

## 4. Help behavior

Default help becomes program-scoped.

Required behavior:

- `program.py --help` prints the default program-scoped help view
- for single-stage tools, that default view is the relevant stage root plus the
  `common` view
- `program.py --help SOME.PATH` prints only the requested schema/help subtree
- deprecated dedicated config-backed flags appear in a final deprecated section
  after the active config-path content
- help content must continue to work for old dedicated flags and the new
  schema-path-driven interface in the same release wave

Representative example required by this CR:

- `python phonetizer.py --help` is equivalent to the default phonetizer help
  view for `common` plus `phonetize`
- `python phonetizer.py --help phonetize` prints the same phonetizer-owned
  config help view
- `python phonetizer.py --help phonetize.timing_model.durations` prints only
  that subtree

## 5. Documentation transition

Documentation must become config-first rather than dedicated-flag-first.

Required documentation outcomes:

- explain the effective config object model
- explain the precedence rule with `-t/--option` at highest priority
- explain which CLI arguments remain CLI-only and non-deprecated
- document deprecated dedicated config-backed flags clearly as compatibility
  aliases
- document program-scoped and path-scoped help behavior

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- shared validation helpers under `src/akkapros/lib/`
- config-consuming runtime CLI entrypoints under `src/akkapros/cli/`
- `src/akkapros/config/default.yaml`
- documentation under `docs/akkapros/`

Design requirements:

- centralize runtime config resolution in shared library code rather than in
  one-off CLI implementations
- centralize program-to-config-root metadata for both validation and help
  rendering
- keep dedicated config-backed flags mapped to canonical schema paths so the
  deprecated aliases cannot drift
- ensure `-t/--option` parsing is schema-aware and uses full config paths
- validate after merge and before processing
- preserve the `confwriter` exception: it manipulates config values but does
  not participate in the runtime effective-config-object model
- keep help text sourced from the canonical help registry and schema metadata
- place deprecated options after active sections in rendered help output
- preserve existing parser behavior for CLI-only operational arguments

Suggested implementation direction:

- one shared resolver returns the effective config object and the program's
  relevant config-root inventory
- one shared parser/helper registers repeatable `-t/--option` support for
  runtime CLIs
- one shared help renderer supports both default program views and explicit
  path-subtree views
- one shared adapter maps deprecated dedicated flags to canonical schema paths
- one shared validation entry point validates `common` plus program-relative
  config sections after all overrides are merged

---

# Files Likely Affected

`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/lib/`
`src/akkapros/config/default.yaml`
`src/akkapros/cli/atfparser.py`
`src/akkapros/cli/syllabify.py`
`src/akkapros/cli/prosmaker.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/cli/metricalc.py`
`src/akkapros/cli/printer.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/cli/phoneprep.py`
`docs/akkapros/configuration.md`
`docs/akkapros/confwriter.md`
`docs/akkapros/atfparser.md`
`docs/akkapros/syllabifier.md`
`docs/akkapros/prosmaker.md`
`docs/akkapros/phonetizer.md`
`docs/akkapros/metricalc.md`
`docs/akkapros/printer.md`
`docs/akkapros/fullprosmaker.md`
`docs/akkapros/phoneprep.md`
`docs/GETTING_STARTED.md`
`README.md`
`tests/`

---

# Acceptance Criteria

- [ ] Every config-consuming runtime CLI other than `confwriter` resolves one
      effective in-memory config object before library processing begins.
- [ ] When `--conf FILE` is absent, runtime CLIs still materialize that
      effective config object from canonical defaults in memory.
- [ ] When `--conf FILE` is present, file values overlay the in-memory default
      config and missing file keys still inherit canonical defaults.
- [ ] Runtime CLIs accept repeatable `-t KEY=VALUE` and `--option KEY=VALUE`
      overrides for full schema paths.
- [ ] `-t/--option` overrides take precedence over dedicated config-backed CLI
      flags.
- [ ] Dedicated config-backed CLI flags remain functional but are marked
      deprecated.
- [ ] CLI-only non-config arguments remain functional and are not marked
      deprecated.
- [ ] Effective config validation runs after all merge layers are applied and
      before processing begins.
- [ ] Validation scope is program-relative: `common` plus the config sections
      the command actually consumes.
- [ ] `fullprosmaker` validates the shared stage sections it consumes rather
      than a duplicated `fullprosmaker` config namespace.
- [ ] `python phonetizer.py --help` produces the default program-scoped help
      view for `common` plus `phonetize`.
- [ ] `python phonetizer.py --help phonetize` produces the same phonetizer-
      owned section help view.
- [ ] `python phonetizer.py --help phonetize.timing_model.durations` prints
      only that subtree.
- [ ] Default help output keeps deprecated dedicated config-backed flags, but
      they appear after the active config-path-driven sections.
- [ ] Help rendering continues to document both the deprecated dedicated
      options and the new preferred path-based override method during the
      transition.
- [ ] Built-in `run_tests()` coverage is added or updated in affected modules
      for runtime config resolution, path overrides, deprecation aliases,
      validation timing, and scoped help behavior.
- [ ] Pytest coverage includes focused unit tests for merge precedence,
      path-based override parsing, help rendering, and program-relative
      validation.
- [ ] Pytest coverage includes integration tests for representative runtime
      CLIs using defaults only, config-file-driven runs, dedicated-flag plus
      path-override precedence, and scoped help output.
- [ ] Documentation is updated across configuration docs and affected program
      docs to explain the effective config object, `-t/--option` usage,
      deprecated dedicated flags, CLI-only arguments, validation timing, and
      program-scoped help.

---

# Risks / Edge Cases

Possible issues:

- some CLI modules may still keep local option state separate from the effective
  config object and thereby violate the unified model
- deprecated dedicated flags may drift from canonical schema paths if alias
  mapping is not centralized
- help rendering for orchestrators may become confusing if program-relative
  root inventories are not explicit and documented
- validation may be run on the wrong subtree if program-root ownership is not
  centralized
- users may treat CLI-only operational arguments as deprecated accidentally
  unless docs separate them clearly from config-backed flags

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for
  effective-config materialization, merge precedence, path-override parsing,
  deprecated alias handling, validation timing, and scoped help rendering

Unit tests:

- defaults-only effective-config materialization without `--conf`
- file-over-default merge behavior with missing file keys inheriting defaults
- dedicated config-backed flag over file precedence
- `-t/--option` over dedicated-flag precedence
- invalid path-override key rejection
- invalid path-override value rejection
- program-relative validation scope selection
- default help rendering for a representative single-stage CLI
- subtree help rendering for a representative path such as
  `phonetize.timing_model.durations`
- deprecated-option ordering at the end of help output
- `confwriter` exclusion from runtime-resolution behavior

Integration tests:

- representative CLI run with no `--conf` and one or more path overrides
- representative CLI run with `--conf FILE` plus no additional overrides
- representative CLI run where a deprecated dedicated flag overrides file state
- representative CLI run where `-t/--option` overrides both file and dedicated
  config-backed flags
- `phonetizer --help`, `phonetizer --help phonetize`, and
  `phonetizer --help phonetize.timing_model.durations` output checks
- `fullprosmaker` validation-path coverage over shared stage sections

Manual review:

- inspect help output ordering for active sections versus deprecated flags
- inspect docs to confirm config-first guidance and clear treatment of CLI-only
  arguments
- inspect runtime code paths to confirm libraries consume the effective config
  object rather than separate ad hoc parser state

---

# Rollback Plan

If the unified runtime-resolution model proves too disruptive, remove
`-t/--option` from runtime CLIs, restore the earlier dedicated-flag-first
behavior, and revert scoped help rendering in one coordinated change. Partial
rollback is discouraged because mixed precedence and mixed help models would
leave the active interface ambiguous.

---

# Related Issues

- [ADR-042](../adr/042-effective-runtime-config-object-path-overrides-and-program-scoped-help.md)
- [ADR-037](../adr/037-centralized-help-message-registry-for-cli-and-config-docs.md)
- [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- [REQ-028](../req/028-effective-runtime-config-object-path-overrides-and-program-scoped-help.md)
- [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)
- [CR-030](030-add-package-wide-yaml-config-and-confwriter.md)
- [CR-031](031-centralize-cli-help-text-for-cli-and-config-doc-emission.md)
- [CR-034](034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md)

---

# Tasks

## Implementation

- [ ] Add one shared effective-runtime-config resolver for config-consuming
      runtime CLIs
- [ ] Add repeatable `-t/--option KEY=VALUE` parsing to runtime CLIs
- [ ] Map deprecated dedicated config-backed flags to canonical schema paths
- [ ] Add program-relative config-root inventories for validation and help
- [ ] Validate effective config before processing begins
- [ ] Add program-scoped and path-scoped help rendering
- [ ] Keep CLI-only operational arguments active and non-deprecated
- [ ] Preserve the `confwriter` exception from the runtime-resolution model

## Tests

- [ ] Add or extend detailed built-in `run_tests()` coverage in affected
      modules
- [ ] Add pytest unit coverage for resolution, precedence, validation, and
      help rendering
- [ ] Add pytest integration coverage for representative defaults-only,
      config-file, alias, and path-override flows

## Documentation

- [ ] Update `docs/akkapros/configuration.md` for the effective config object,
      precedence rule, and `-t/--option`
- [ ] Update `docs/akkapros/confwriter.md` to document the `confwriter`
      exception from the runtime-resolution model and its relationship to the
      schema-path workflow
- [ ] Update affected program docs under `docs/akkapros/` so runtime CLIs are
      documented config-first and dedicated config-backed flags are marked
      deprecated
- [ ] Update `docs/GETTING_STARTED.md` and `README.md` with the preferred
      runtime pattern: `--conf FILE` plus optional `-t/--option`
- [ ] Document scoped help behavior and deprecated-option ordering

## Review

- [ ] Verify acceptance criteria

---

# Notes for CR-043

This CR deliberately treats the runtime config object as a first-class runtime
artifact rather than as an incidental parser side effect. The main transition
goal is to make config-path usage the preferred interface without breaking
existing users in the same wave.