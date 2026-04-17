---
req_id: REQ-022
status: Implemented
priority: High
impact: Mutative
created: 2026-04-03
updated: 2026-04-17
related_adrs: 'ADR-001, ADR-003, ADR-004, ADR-021, ADR-036'
implemented_by: 'CR-030, CR-034, CR-067'
---

# Requirement: Package-Wide YAML Config and Confwriter CLI

# Summary

The system shall provide one package-wide YAML configuration contract for the
Python CLIs and a new `confwriter` CLI for creating, inspecting, and
incrementally updating such config files. The package shall add
`src/akkapros/config/default.yaml` containing the full documented default
schema.

Every config-eligible CLI option shall support three-level precedence:
explicit CLI option over YAML config value over built-in default. Existing
default-only operation shall remain supported when `--conf FILE` is not used.

The config model shall contain shared common options such as `prefix` and
`outdir`, and shall not define stage-specific duplicates such as
`metrics_prefix` or `print_prefix`. `fullprosmaker` shall consume the shared
stage sections rather than a duplicated `fullprosmaker` YAML section for those
same options.

---

# Motivation

The package already has coherent per-stage defaults and a shared output-prefix
contract, but users still need to repeat many flags across commands and across
repeated runs. A package-wide YAML config file provides reproducibility and
reduces repeated manual option entry.

The requirement must preserve current behavior for users who do not want config
files. It must also keep the package pipeline coherent by reusing one shared
prefix or outdir contract rather than introducing stage-specific output-prefix
keys.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [x] Given any Python file-processing CLI under `src/akkapros/cli/`, when its
      parser is built, then it exposes a shared `--conf FILE` option.
- [x] Given no `--conf FILE` argument is supplied, when a CLI runs, then the
      current built-in defaults continue to operate.
- [x] Given `--conf FILE` and an input file are supplied, when the config file
      contains the needed non-default settings, then the CLI can run without
      requiring the user to repeat the remaining residual options on the
      command line.
- [x] Given a config key is absent from the YAML file, when the CLI resolves
      effective options, then the built-in default for that option is used.
- [x] Given both a config value and an explicit CLI value are supplied for the
      same option, when effective options are resolved, then the CLI value wins.
- [x] Given the package config schema is materialized in source control, when
      `src/akkapros/config/default.yaml` is inspected, then all supported keys
      are present and documented.
- [x] Given the phonetize stage is part of the config schema, when
      `src/akkapros/config/default.yaml`, emitted help comments, or
      `confwriter` output are inspected, then the nested phonetize keys use the
      approved structure and names exactly, including the current
      `phonetize.process` policies, `phonetize.timing_model.durations.cvc_reference`,
      `phonetize.timing_model.durations.segmental_ceiling`,
      `phonetize.timing_model.durations.segmental_floor`, consonant-class
      `onset` / `coda` / `geminate` anchors with
      `perception_limits.geminate_min` and `perception_limits.gemination_max`,
      vowel perception limits, and pause min/max bands.
- [x] Given `src/akkapros/config/default.yaml` is inspected, when the YAML is
      read, then it documents the stage sections used by `fullprosmaker`
      instead of repeating a duplicated `fullprosmaker` config section.
- [x] Given the config schema contains shared output naming settings, when
      common keys are defined, then `prefix` and `outdir` exist in the common
      config area.
- [x] Given the config schema is inspected, when output-prefix keys are listed,
      then `metrics_prefix`, `print_prefix`, and equivalent stage-specific
      prefix keys are absent.
- [x] Given config keys map to stage behavior, when a CLI reads config, then it
      consumes only the sections relevant to that command plus the shared common
      section.
- [x] Given `fullprosmaker` reads config, when effective options are resolved,
      then it consumes `common` plus the shared stage sections it orchestrates
      rather than a second duplicated full-pipeline section.
- [x] Given all config-eligible CLI options are documented, when users read the
      config documentation, then they can identify the YAML key, the related CLI
      flag, the default value, and the override rule.
- [x] Given documented YAML is emitted, when comments are written, then they
      reuse canonical help text shared with CLI help surfaces.
- [x] Given the new `confwriter` CLI is invoked with `--conf FILE` and one or
      more additional schema-driven operations, when `FILE` does not exist, then the
      command creates a full config file programmatically from the canonical
      schema and applies the supplied overrides.
- [x] Given the new `confwriter` CLI is invoked with `--conf FILE` and one or
      more additional schema-driven operations, when `FILE` already exists, then the
      command updates only the specified config values and preserves the rest of
      the file's effective configuration.
- [x] Given `confwriter` is used to write values, when a user passes repeatable
      `--set key=value` arguments with full YAML-path keys, then the command
      validates those keys against the canonical schema before writing.
- [x] Given a requested `confwriter` key is invalid, when validation fails,
      then the command exits without modifying the config file.
- [x] Given `confwriter --list` is run, when the key inventory is printed, then
      each entry shows the full path, type, default-or-required state, and
      canonical help text.
- [x] Given `confwriter --get KEY` is run, when the key exists in schema, then
      the command prints the current stored effective value for that key.
- [x] Given `confwriter --unset KEY` is run, when the key is valid, then the
      config stores `null` so the option is treated as not explicitly set.
- [x] Given `confwriter --set-default KEY` is run, when the key is valid, then
      the config stores the canonical schema default value explicitly.
- [x] Given a nested config key exists, when `confwriter` addresses it by full
      path such as `phonetize.timing_model.speech.wpm`, then the same schema-
      driven set/get/list/unset/set-default behavior applies.
- [x] Given `confwriter` is run successively with different options, when the
      same config file is updated across multiple invocations, then the file is
      filled incrementally and retains earlier values that were not overridden.
- [x] Given `confwriter` generates a config file, when it writes YAML, then it
      uses programmatic schema emission rather than copying `default.yaml`
      directly.
- [x] Given a user runs `python confwriter.py --conf test.yaml --prefix one`
      and then `python confwriter.py --conf test.yaml --outdir two`, when the
      second command completes, then the resulting config file contains both
      `prefix: one` and `outdir: two` under the correct shared config area.
- [x] Given package docs are updated, when users look for config guidance, then
      one dedicated documentation page fully explains the config file structure,
      common keys, stage-specific keys, override precedence, and `confwriter`
      usage.
- [x] Given the implementation is complete, when tests are run, then unit and
      integration coverage validate config loading, precedence resolution,
      config generation, incremental updates, and representative CLI behavior.
- [x] Given the implementation is complete, when integration tests are run,
      then at least one representative CLI succeeds using `--conf FILE` for
      non-default settings without repeating those settings on the command line.
- [x] Given the implementation is complete, when integration tests are run,
      then at least one representative CLI demonstrates that an explicit CLI
      flag overrides the corresponding value in the config file while other
      config-supplied values still apply.
- [x] Given the implementation is complete, when integration tests are run,
      then a config file created and incrementally updated by successive
      `confwriter` invocations can be consumed successfully by a representative
      package CLI.

---

# User Story (optional)
> As a user running multiple Akkadian prosody tools, I want one YAML file to
> carry my recurring configuration so that I can run commands with `--conf FILE`
> plus the input path and override only the settings I need to change.

---

# Interface Notes
- Common precedence rule:
  - explicit CLI option
  - YAML config value
  - built-in default
- Common config area shall contain at least shared run options such as
  `prefix` and `outdir`.
- The config model shall support stage-specific sections for stage-specific
  options, while avoiding duplicated common keys.
- `fullprosmaker` shall read shared stage sections instead of introducing a
      second YAML namespace for those same stage-owned options.
- `src/akkapros/config/default.yaml` shall be the canonical full example.
- `confwriter` shall expose `--conf FILE` plus schema-driven operations such as
      `--set`, `--get`, `--list`, `--unset`, and `--set-default` rather than a
      proliferating one-flag-per-key writing surface.
- Full YAML-path keys, including nested keys, are part of the `confwriter`
      interface contract.
- Schema comments and emitted key paths must stay aligned with the approved
  nested phonetize contract across config files, CLI help, and dedicated config
  docs.
- Affected components:
  - `src/akkapros/config/default.yaml`
  - Python CLI entrypoints under `src/akkapros/cli/`
  - shared config or schema utilities under `src/akkapros/lib/`
  - user docs for configuration and CLI usage

---

# Open Questions
- [x] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: large
- Migration:
  - add `--conf FILE` without breaking current flag-only runs
  - add `src/akkapros/config/default.yaml`
  - add a dedicated config documentation page
  - update CLI docs to reference shared config support
      - propagate approved phonetize schema changes to config comments,
            `confwriter`, CLI help, and config docs together
      - add new unit and integration tests that cover config-driven runs, CLI
            override precedence, `confwriter` schema operations, nested-key handling,
            and `confwriter`-generated config reuse

# Related
- Related ADRs: [ADR-001](../adr/001-cli-lib-separation.md),
  [ADR-003](../adr/003-output-prefix-convention.md),
  [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md),
  [ADR-021](../adr/021-multi-target-printer-architecture-contract.md),
  [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- Related REQs: [REQ-007](007-full-pipeline-orchestration.md),
  [REQ-016](016-standardized-cli-logging-and-console-options.md)
- Implementation CRs: [CR-030](../cr/030-add-package-wide-yaml-config-and-confwriter.md)
      , [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md)

# Non-Goals
- This requirement does not require config files to become mandatory.
- This requirement does not remove existing CLI flags.
- This requirement does not introduce stage-specific output-prefix keys.
- This requirement does not require non-Python tools outside the package to
  adopt the same config contract in wave one.
- This requirement does not require wave one support for `confwriter --conf FILE`
      with no additional override options.

# Security / Safety Considerations
- Config loading must not silently change visible output naming rules away from
  the accepted shared `prefix` and `outdir` contract.
- Incremental config writing must be deterministic so repeated updates do not
  create unstable or surprising YAML output.
- The config documentation must make override precedence explicit to reduce
  accidental misconfiguration.