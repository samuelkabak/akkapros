---
adr_id: ADR-042
status: Proposed
created: 2026-04-07
updated: 2026-04-07
superseded_by: null
---

# 42. Effective Runtime Config Object, Path Overrides, and Program-Scoped Help

## Plain Summary

Every runtime CLI that consumes package configuration shall resolve one
effective in-memory config object before processing starts. That object is
seeded from canonical defaults, optionally overlaid by `--conf FILE`, and then
overridden by explicit CLI values, with repeatable `-t/--option KEY=VALUE`
path overrides taking final precedence.

Config-backed dedicated flags such as `--style` remain temporarily supported for
compatibility, but they become deprecated compatibility aliases rather than the
preferred long-term interface. Help output becomes schema-aware and
program-scoped, so `program.py --help` shows the common section plus the config
sections relevant to that program, while `program.py --help SOME.PATH` shows
only the requested subtree.

## Context and Problem Statement

[ADR-036](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
established package-wide YAML configuration and the basic precedence rule of
CLI over config over defaults. [ADR-037](037-centralized-help-message-registry-for-cli-and-config-docs.md)
established one shared help-text registry for CLI help and config comments.

Those decisions solved schema ownership and documentation drift, but the
runtime model is still underspecified in four important ways:

- the repository does not yet define one explicit effective in-memory config
  object that all runtime CLIs and libraries consume
- the repository does not yet require a universal path-based override surface
  for config-backed settings across runtime CLIs
- the repository does not yet define when program-scoped validation must run
  against the effective config
- the repository does not yet define program-scoped `--help PATH` behavior or
  how deprecated dedicated flags should appear during the transition

The user requirement is to make the config object a real runtime object whether
or not `--conf` is supplied, to prefer schema-path overrides over dedicated
flags, to validate the relevant config sections before processing, and to make
help output program-aware and path-aware.

`confwriter` is intentionally outside the runtime-resolution part of this
decision because it is a config-authoring tool rather than a config-consuming
processing tool.

## Decision Drivers

- Make runtime option resolution deterministic and uniform across the pipeline
- Prefer one canonical config vocabulary over many duplicated dedicated flags
- Preserve compatibility while steering users toward schema-path overrides
- Ensure every processing CLI validates the config it will actually use
- Make help output more discoverable without duplicating per-program prose
- Keep `confwriter` distinct as a config-authoring tool rather than a runtime
  processing CLI

## Considered Options

- Keep the current mixed model in which `--conf` is optional, dedicated flags
  remain primary, and no universal path-override surface or path-scoped help
  is required.
- Add one effective runtime config object, universal `-t/--option KEY=VALUE`
  overrides, per-program validation, and program-scoped help while keeping
  dedicated flags as deprecated compatibility aliases.
- Remove dedicated config-backed flags immediately and require only
  `--conf FILE` plus `-t/--option KEY=VALUE` for all config-backed settings.

## Decision Outcome

Chosen option: add one effective runtime config object, universal path-based
overrides, per-program validation, and program-scoped help, while keeping
dedicated config-backed flags as deprecated compatibility aliases during the
transition.

Concretely:

- Every config-consuming runtime CLI resolves one effective in-memory config
  object before library processing begins.
- That effective config object is always seeded from canonical defaults.
- If `--conf FILE` is supplied, file values overlay that in-memory default
  object.
- If `--conf FILE` is not supplied, the in-memory default object still exists
  and remains the runtime config source.
- Dedicated config-backed CLI flags continue to work for compatibility, but
  they are deprecated compatibility aliases rather than the preferred primary
  interface.
- Repeatable `-t KEY=VALUE` and `--option KEY=VALUE` become the preferred
  universal override surface for config-backed settings on runtime CLIs.
- Path-based overrides have higher precedence than dedicated config-backed CLI
  flags.
- The effective precedence becomes:
  - `-t/--option KEY=VALUE`
  - explicit dedicated config-backed CLI flag
  - `--conf FILE` value
  - canonical in-memory defaults
- Validation runs against the effective config after all overrides are applied
  and before any processing begins.
- Validation scope is program-relative: each runtime CLI validates `common`
  plus the config sections it actually consumes.
- For single-stage tools, `program.py --help` is equivalent to
  `program.py --help <that program's canonical config root>` with `common`
  included in the default help output.
- For orchestrators such as `fullprosmaker`, default help shows `common` plus
  the shared stage sections relevant to that program rather than inventing a
  second duplicate config namespace.
- `program.py --help SOME.PATH` prints only the requested schema/help subtree.
- Deprecated dedicated config-backed flags remain documented in help output,
  but they must appear after the active config-path-driven help sections.
- CLI-only operational arguments that are not part of the config schema, such
  as positional input files, `--help`, `--test`, and config-authoring
  operations, remain CLI-only and are not deprecated by this ADR.
- `confwriter` is excluded from the runtime effective-config-object rule and
  from runtime processing validation, although it may still reuse the schema,
  help registry, and validation metadata for config-authoring operations.

## Pros and Cons of the Options

### Chosen Option

- Pros: makes runtime config resolution explicit and uniform across the
  pipeline.
- Pros: preserves compatibility while clearly preferring one canonical
  schema-path interface.
- Pros: ensures validation is performed on the actual effective config rather
  than on a partial pre-merge view.
- Pros: makes help output more useful for users who think in config paths.
- Pros: keeps `confwriter` conceptually clean as a config-authoring tool.
- Cons: requires coordinated updates across config loading, parser helpers,
  help rendering, validation, and documentation.
- Cons: creates a transition period where both deprecated dedicated flags and
  preferred path overrides coexist.

### Other Options

- Keep the current mixed model:
  - Pro: less implementation work immediately.
  - Con: runtime resolution remains inconsistent and path-based config usage is
    still secondary.
- Remove dedicated flags immediately:
  - Pro: simpler long-term interface.
  - Con: too disruptive for current users and existing CLI docs.

## Implications and Consequences

- Runtime CLIs need one shared resolution helper that materializes the
  effective config object before processing.
- Dedicated config-backed flags should resolve through canonical schema paths
  so deprecation aliases cannot drift away from the config model.
- Program definitions need an explicit inventory of which config roots they
  consume for validation and default help rendering.
- Validation must happen after merging defaults, file values, dedicated flags,
  and `-t/--option` overrides.
- Help rendering must reuse the centralized help registry from [ADR-037]
  together with schema metadata and program-to-root mappings.
- Documentation must shift from flag-first explanations to config-first
  explanations, while still documenting deprecated dedicated flags during the
  transition.
- `confwriter` remains a config-authoring exception and must not be forced into
  the runtime effective-config-object workflow.

## Links

- Related ADR: [ADR-001](001-cli-lib-separation.md)
- Related ADR: [ADR-014](014-cli-built-in-self-tests.md)
- Related ADR: [ADR-031](031-factual-runtime-records-and-structured-self-test-output.md)
- Related ADR: [ADR-036](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- Related ADR: [ADR-037](037-centralized-help-message-registry-for-cli-and-config-docs.md)
- Related REQ: [REQ-010](../req/010-built-in-self-tests-and-test-infrastructure.md)
- Related REQ: [REQ-016](../req/016-standardized-cli-logging-and-console-options.md)
- Parent config REQ: [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)
- Existing config CR: [CR-030](../cr/030-add-package-wide-yaml-config-and-confwriter.md)
- Existing confwriter CR: [CR-034](../cr/034-simplify-confwriter-command-surface-with-set-get-list-unset-and-set-default.md)
- Requirement created under this ADR: [REQ-028](../req/028-effective-runtime-config-object-path-overrides-and-program-scoped-help.md)

## Implementation Notes (optional)

- The preferred implementation should centralize runtime config resolution and
  program-root metadata in shared library code rather than duplicating it in
  CLI modules.
- Deprecated dedicated flags should emit deprecation warnings through the
  project logging/output policy rather than ad hoc `print()` calls.
- The first implementation wave should cover all config-consuming runtime CLIs
  under `src/akkapros/cli/` except `confwriter`.

## Reviewed By

- Pending maintainer review