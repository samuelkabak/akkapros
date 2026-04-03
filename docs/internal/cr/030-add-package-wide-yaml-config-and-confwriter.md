---
cr_id: CR-030
status: Draft
priority: High
impact: Mutative
created: 2026-04-03
updated: 2026-04-03
implements: 'ADR-036, REQ-022'
---

# Change Request: Add Package-Wide YAML Config Support and Confwriter CLI

# Summary

Add package-wide YAML config support for the Python CLIs, including a shared
`--conf FILE` option, a canonical `src/akkapros/config/default.yaml`, and a new
`confwriter` CLI that creates and incrementally updates config files
programmatically.

The design keeps existing defaults working, keeps the current output-prefix
convention coherent through shared common keys such as `prefix` and `outdir`,
and forbids stage-specific duplicates such as `metrics_prefix` and
`print_prefix`. Explicit CLI options override config values.

The documented YAML shall be generated from canonical schema and canonical help
text, and `fullprosmaker` shall read the shared stage sections instead of a
duplicated `fullprosmaker` config block.

---

# Motivation

- Reduce repeated CLI flag entry across the package
- Make reusable run profiles first-class and documented
- Keep output naming coherent through one shared prefix or outdir model
- Preserve current default behavior for users who do not use config files
- Provide a supported way to create and update config files incrementally

Users currently need to repeat many flags across separate commands and across
repeated runs. This is especially awkward when a user wants to keep one stable
set of configuration choices but vary only the input file or one or two flags.

The package already has coherent stage behavior and a shared output naming
convention. This change extends that coherence to configuration management.

---

# Scope

## Included

- Add a shared `--conf FILE` option to Python file-processing CLIs in the package.
- Define a package-wide YAML schema with shared common options and stage-specific sections.
- Create `src/akkapros/config/default.yaml` with all supported keys present and richly documented.
- Keep shared common output settings in one common location, including `prefix`
  and `outdir`.
- Exclude `metrics_prefix`, `print_prefix`, and equivalent stage-specific prefix keys.
- Exclude a duplicated `fullprosmaker` config section for stage-owned options.
- Define option precedence as explicit CLI option over YAML config value over built-in default.
- Add a new CLI program named `confwriter`.
- Require `confwriter` to create missing config files programmatically from the
  canonical schema rather than by copying `default.yaml`.
- Require `confwriter` to update existing config files incrementally when new
  override flags are supplied.
- Require documented YAML emission to reuse centralized canonical help text.
- Add complete user-facing documentation for the config file and `confwriter`.
- Add tests for config loading, precedence, schema emission, and incremental updates.
- Add new integration tests that exercise real CLI runs driven by config files.

## Not Included

- Making config files mandatory for normal CLI use.
- Removing current CLI flags.
- Introducing stage-specific output-prefix keys.
- Extending the first rollout beyond Python package CLIs.
- Replacing the accepted output-prefix convention with arbitrary per-stage file names.
- Requiring wave-one support for `confwriter --conf FILE` with no additional
  override options.

---

# Current Behavior

Current CLI behavior is primarily flag-driven. Users can rely on built-in
defaults and can pass options directly on each command invocation, but there is
no package-wide YAML config contract and no supported CLI for incrementally
building such config files.

Consequences of the current state:

- repeated configuration must be re-entered manually
- cross-command run profiles are harder to reuse consistently
- users must maintain their own ad hoc notes or shell wrappers for stable option sets
- the package has no canonical config-file documentation surface

---

# Proposed Change

Adopt the following behavior.

- File-processing CLIs accept `--conf FILE`.
- When `--conf FILE` is omitted, existing default-driven behavior continues.
- When `--conf FILE` is supplied, the CLI reads relevant config values from YAML.
- Explicit CLI flags override config values.
- The package ships `src/akkapros/config/default.yaml` as a full documented
  config example.
- The config contains one shared common location for `prefix` and `outdir`.
- The config shall not contain `metrics_prefix`, `print_prefix`, or equivalent
  stage-specific prefix keys.
- `fullprosmaker` reads the relevant shared stage sections rather than an extra
  duplicated `fullprosmaker` YAML section.
- A new `confwriter` CLI creates missing config files from the canonical schema
  programmatically and updates existing files incrementally.

Representative usage:

- `python some_cli.py --conf run.yaml input_file`
- `python confwriter.py --conf test.yaml --prefix something`
- `python confwriter.py --conf test.yaml --outdir something_else`

After the second `confwriter` invocation above, the resulting YAML must contain
both the earlier `prefix` value and the newer `outdir` value unless either was
explicitly changed.

---

# Technical Design

Architecture notes:

Components:
- Python CLI entrypoints under `src/akkapros/cli/`
- shared config schema and loading helpers under `src/akkapros/lib/`
- `src/akkapros/config/default.yaml`
- dedicated config documentation in `docs/akkapros/`

Design requirements:

- The config schema must be package-wide, not stage-fragmented.
- The schema must distinguish shared common keys from stage-specific keys.
- Shared output keys must include `prefix` and `outdir` in one common area.
- Stage-specific output-prefix duplicates are forbidden.
- `fullprosmaker` must consume stage sections instead of owning a duplicate
  copy of syllabifier, prosody, metrics, and printer settings in YAML.
- Config generation must be programmatic from canonical schema definitions.
- Documented config emission must reuse centralized help text.
- Config writing must be deterministic and incremental.
- CLI wrappers must remain thin; config resolution belongs in shared library code.
- User docs must include one complete config reference page.

Suggested schema shape:

- `common`: package-wide keys such as `prefix`, `outdir`, and other keys that
  are shared across multiple tools
- stage-specific sections keyed by tool or functional domain, for example
  `atfparser`, `syllabifier`, `prosmaker`, `metricalc`, and `printer`

`fullprosmaker` is a pipeline runner and shall reuse those stage sections for
its config-backed option resolution.

The exact key inventory must cover all supported config-eligible options.

---

# Files Likely Affected

`src/akkapros/config/default.yaml`
`src/akkapros/lib/`
`src/akkapros/cli/`
`docs/akkapros/`
`docs/GETTING_STARTED.md`
`README.md`
`tests/`

---

# Acceptance Criteria

- [ ] Python file-processing CLIs accept `--conf FILE`.
- [ ] Existing flag-only runs remain valid without `--conf FILE`.
- [ ] The effective precedence is CLI option over config value over built-in default.
- [ ] `src/akkapros/config/default.yaml` exists and contains the full documented schema.
- [ ] Shared config contains `prefix` and `outdir` in one common area.
- [ ] Shared config does not contain `metrics_prefix`, `print_prefix`, or equivalent duplicates.
- [ ] Shared config does not contain a duplicated `fullprosmaker` section for
  stage-owned options.
- [ ] `confwriter` exists as a dedicated CLI.
- [ ] If `confwriter --conf FILE --some-option ...` is run and `FILE` does not
      exist, the tool creates a full config programmatically and applies the
      supplied overrides.
- [ ] If `confwriter --conf FILE --some-option ...` is run and `FILE` already
      exists, the tool updates only the specified values and preserves other
      previously stored values.
- [ ] Successive `confwriter` runs incrementally fill the same config file.
- [ ] Generated YAML comments are sourced from centralized canonical help text.
- [ ] A dedicated user-facing config documentation page exists and is complete.
- [ ] Tests cover precedence resolution, full-schema generation, incremental
      updates, and representative CLI config-driven runs.
- [ ] New integration tests cover config-file-driven CLI behavior, including a
  run that uses `--conf FILE` for non-default settings, a run where an
  explicit CLI flag overrides the config file, and a run where a config
  file previously produced by successive `confwriter` invocations is used
  by a package CLI.

---

# Risks / Edge Cases

Possible issues:

- accidental duplication of common keys into stage-specific sections
- ambiguous precedence if config loading is mixed inconsistently with parser defaults
- unstable YAML emission that causes noisy diffs on repeated writes
- partial CLI rollout that leaves some commands outside the shared config contract
- documentation drift between `default.yaml`, the canonical schema, and user docs

---

# Testing Strategy

Unit tests:

- config schema default emission
- config loading and merge precedence
- rejection or absence of stage-specific prefix duplicates
- `confwriter` creation of a missing config file
- `confwriter` incremental update of an existing config file

Integration tests:

- add new integration tests that invoke representative CLIs with
  `--conf FILE input_file` and assert the config file actually drives the run
- add new integration tests where explicit CLI flags override config values at
  runtime while the same config file still supplies the remaining settings
- add a new integration test that uses a config file built incrementally by
  successive `confwriter` runs and then executes a representative CLI from that
  file
- add documentation or golden-file checks for deterministic emitted YAML
  structure

Manual review:

- verify that `default.yaml` and the dedicated config docs describe the same
  keys and override rules

---

# Rollback Plan

If the feature proves too disruptive, remove the new `--conf FILE` integration,
remove `confwriter`, and restore flag-only operation as the sole supported CLI
configuration path. Because current defaults remain valid during rollout,
backout does not require changing output artifacts.

---

# Related Issues

- [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)

---

# Tasks

## Implementation

- [ ] Add shared config schema and loading helpers
- [ ] Add `src/akkapros/config/default.yaml`
- [ ] Add `--conf FILE` to supported Python CLIs
- [ ] Add `confwriter`
- [ ] Add complete config documentation

## Tests

- [ ] Add config precedence tests
- [ ] Add config generation tests
- [ ] Add incremental `confwriter` update tests
- [ ] Add new config-file integration tests for config-driven CLI runs
- [ ] Add new config-file integration tests for CLI-overrides-config behavior
- [ ] Add new config-file integration tests for `confwriter`-generated config reuse