---
adr_id: ADR-036
status: Proposed
created: 2026-04-03
updated: 2026-04-03
superseded_by: null
---

# 36. Package-Wide YAML Configuration and CLI Override Precedence

## Plain Summary

Add one package-wide YAML configuration model that all Python CLIs can read via
`--conf FILE`, while preserving current built-in defaults. Users should be able
to run a file-processing CLI with just `--conf FILE` plus the input file when
the YAML already carries the remaining settings.

The YAML model uses one coherent shared namespace for common options such as
`prefix` and `outdir`, rather than stage-specific duplicates such as
`metrics_prefix` or `print_prefix`. Command-line options always override config
file values, and config file values override built-in defaults.

`fullprosmaker` is treated as a pipeline runner over existing stage sections,
not as the owner of a second duplicated YAML section for those same options.

## Context and Problem Statement

The package currently exposes many CLI flags across stage tools such as
`atfparser`, `syllabifier`, `prosmaker`, `metricalc`, `printer`,
`fullprosmaker`, and `phoneprep`. This is manageable for one-off runs, but it
becomes repetitive and error-prone when a user wants to reuse the same option
set across multiple texts or multiple pipeline stages.

The project already has an accepted output-prefix convention in
[ADR-003](003-output-prefix-convention.md) and an implemented full-pipeline
wrapper in [REQ-007](../req/007-full-pipeline-orchestration.md). What is still
missing is one canonical configuration contract that applies across the package
and one safe way to create or incrementally update such config files without
copy-pasting examples by hand.

The project needs one explicit decision that:

- defines a package-wide YAML configuration schema
- defines precedence between built-in defaults, config values, and CLI flags
- keeps one coherent `prefix` and `outdir` contract across the package
- introduces a dedicated config-writing CLI
- keeps `fullprosmaker` aligned with shared stage sections instead of duplicating them
- preserves existing default behavior for users who do not adopt config files

## Decision Drivers

- Reduce repeated CLI flag entry across the package
- Preserve backward-compatible default behavior
- Keep the package-wide pipeline coherent through one shared prefix or outdir model
- Avoid duplicated stage-specific output-prefix knobs
- Keep CLI/lib separation intact by centralizing config logic in shared code
- Provide deterministic, documented config generation rather than manual file copying

## Considered Options

- Keep the current flag-only CLI model and document recommended shell aliases.
- Add a package-wide YAML config file plus CLI override precedence.
- Add per-stage config files instead of one package-wide schema.

## Decision Outcome

Chosen option: Add a package-wide YAML config file plus CLI override precedence.

Concretely:

- All Python file-processing CLIs in the package gain a shared `--conf FILE`
  option.
- Existing built-in defaults remain valid when no config file is supplied.
- When `--conf FILE` is supplied, the CLI loads config values from YAML.
- When a corresponding CLI flag is also supplied explicitly, the CLI flag wins.
- The effective precedence is:
  - explicit CLI option
  - YAML config value
  - built-in default
- The package adds `src/akkapros/config/default.yaml` as the canonical,
  fully-populated, documented default config file.
- The documented YAML comments are emitted from centralized canonical help text.
- The config schema contains one shared place for common options such as
  `prefix` and `outdir`.
- The schema does not define `metrics_prefix`, `print_prefix`, or equivalent
  stage-specific output-prefix keys.
- The schema does not define a duplicated `fullprosmaker` section for stage-
  owned options; `fullprosmaker` reads the relevant shared stage sections.
- The package adds a new CLI program named `confwriter` that creates or updates
  YAML config files programmatically from the canonical schema rather than by
  copying `default.yaml`.

## Pros and Cons of the Options

### Package-wide YAML config plus CLI override precedence (chosen)

- Good, because repeated option entry across the package is reduced.
- Good, because the package gains one explicit, documented configuration
  contract.
- Good, because command-line users keep existing defaults and can adopt config
  files incrementally.
- Good, because output naming stays coherent under one shared `prefix` and
  `outdir` model.
- Bad, because all CLIs must participate in one shared schema and precedence rule.
- Bad, because docs and tests must now cover both flag-only and config-driven use.

### Keep the current flag-only model

- Good, because no new schema or config writer is needed.
- Bad, because repeated multi-CLI option entry remains error-prone.
- Bad, because users must manage reproducible runs outside the package.

### Per-stage config files

- Good, because each CLI can evolve its own config independently.
- Bad, because one package-wide run profile becomes fragmented.
- Bad, because shared options such as `prefix` and `outdir` can drift or be duplicated.

## Implications and Consequences

- Introduce a shared config-loading layer in library code and keep CLI wrappers
  thin, consistent with [ADR-001](001-cli-lib-separation.md).
- Add `src/akkapros/config/default.yaml` as the canonical materialized example
  of the full schema.
- Document every config key in the YAML file and in dedicated user-facing docs.
- Reuse centralized help text when emitting config comments so CLI help and YAML
  comments do not drift.
- Ensure all config-eligible options remain overridable from the command line.
- Keep one common output-prefix contract aligned with [ADR-003](003-output-prefix-convention.md).
- Add a dedicated `confwriter` CLI that creates missing config files from the
  canonical schema programmatically and updates existing files incrementally.
- Keep stage-specific output naming coherent by rejecting stage-specific prefix
  keys such as `metrics_prefix` and `print_prefix`.
- Add integration coverage that exercises real CLI runs from config files,
  verifies CLI-overrides-config precedence in end-to-end command execution, and
  proves that config files produced incrementally by `confwriter` are reusable
  by representative package CLIs.

## Links

- Related ADR: [ADR-001](001-cli-lib-separation.md)
- Related ADR: [ADR-003](003-output-prefix-convention.md)
- Related ADR: [ADR-004](004-stage-pipeline-and-pivot-format.md)
- Related ADR: [ADR-021](021-multi-target-printer-architecture-contract.md)
- Related REQ: [REQ-007](../req/007-full-pipeline-orchestration.md)
- Related REQ: [REQ-016](../req/016-standardized-cli-logging-and-console-options.md)

## Implementation Notes (optional)

- Prefer a schema model in library code that can both validate and emit the
  canonical config structure.
- `default.yaml` is a checked-in, documented materialization of that schema,
  but `confwriter` must not generate files by copying it byte-for-byte.
- `confwriter` should write keys in deterministic order so repeated updates are
  stable and diff-friendly.
- The first rollout should cover Python CLI entrypoints under `src/akkapros/cli/`.
- The first rollout only guarantees the user-specified `confwriter` case of
  `--conf FILE` plus at least one override option.
- The implementation should add dedicated integration tests for config-file
  workflows rather than relying only on unit coverage of config parsing.

## Reviewed By

- Pending maintainer review