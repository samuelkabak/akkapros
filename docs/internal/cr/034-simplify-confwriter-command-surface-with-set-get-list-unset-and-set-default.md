---
cr_id: CR-034
status: Done
priority: High
impact: Mutative
created: 2026-04-04
updated: 2026-04-08
implements: 'ADR-036, ADR-037, REQ-022'
---

# Change Request: Simplify confwriter command surface with set get list unset and set-default

# Summary

Replace the current option-per-key `confwriter` command surface with a smaller,
schema-driven interface centered on `--set`, `--get`, `--list`, `--unset`, and
`--set-default`.

The new interface should make `confwriter` a usable YAML authoring and
inspection tool rather than a mirror of every config option as a dedicated CLI
flag. It should validate key paths against the canonical schema, explain the
available keys and their meaning, and avoid modifying the config file when the
requested operation is invalid.

This includes the phonetizer timing-model subtree as it grows. As new
phonetize keys are introduced by later phonetizer records, `confwriter`
remains responsible for rejecting unknown keys, accepting only schema-valid
values, and surfacing the new key/value model through schema-driven help.

---

# Motivation

The current `confwriter` surface does not scale well as the number of config
keys grows. It produces an increasingly ugly and noisy `--help` output and
forces the tool to expose many repetitive `--foo` / `--no-foo` toggles that are
better represented as schema-backed config operations.

The user intent for `confwriter` is broader than incremental key writing. The
tool should also help users understand what the YAML contains, what a valid key
looks like, what type each key expects, and what value a key currently holds.

Representative current pain points include repetitive output such as:

- `--print-xar`
- `--no-print-xar`
- `--print-mbrola`
- `--no-print-mbrola`
- `--print-print-merger`
- `--no-print-print-merger`

This CR replaces that growing flag inventory with a more durable config-editor
interface.

---

# Scope

## Included

- Replace per-option config-writing flags in `confwriter` with a smaller
  operation-oriented CLI.
- Add repeatable `--set key=value` operations using full YAML-path keys.
- Add `--list` support for schema-backed option discovery.
- Add `--list SUBSTRING` filtering by key-name substring.
- Add `--get KEY` support for reading the current effective stored value.
- Add `--unset KEY` support for clearing an explicit config value by writing
  `null`.
- Add `--set-default KEY` support for writing the schema default value
  explicitly.
- Require strict validation of key paths and values before any config file is
  modified.
- Require `confwriter` output to explain key meaning using canonical help text.
- Require the same validation and documentation behavior for nested
  `phonetize` keys introduced by later phonetizer records, including
  `phonetize.process` and `phonetize.timing_model`.
- Update docs and tests for the new interface.

## Not Included

- Redesigning the package-wide YAML schema itself.
- Changing the general `--conf FILE` config-loading contract for other CLIs.
- Replacing normal CLI `--help` behavior outside `confwriter`.
- Introducing a new YAML syntax beyond the current restricted subset.

---

# Current Behavior

`confwriter` currently exposes many dedicated CLI flags that map directly to
individual config keys. That approach works for a small option set but becomes
too complex and visually noisy as the schema grows.

The current interface also makes `confwriter` primarily a write-through tool
rather than a discovery tool. Users cannot rely on one compact, schema-driven
surface to list valid keys, inspect current values, clear explicit values back
to absence, or explicitly write schema defaults when they want them.

---

# Proposed Change

Adopt the following command surface.

- Setting values:
  - `python confwriter --conf FILE --set key1=value1 --set key2=value2`
- Listing keys and help text:
  - `python confwriter --conf FILE --list`
  - `python confwriter --conf FILE --list atfparse`
- Reading one value:
  - `python confwriter --conf FILE --get common.log_append`
- Clearing one key back to absence:
  - `python confwriter --conf FILE --unset prosody.style`
- Writing one key back to its schema default explicitly:
  - `python confwriter --conf FILE --set-default prosody.style`

Key-path rules:

- Keys use the full YAML path, for example:
  - `common.prefix`
  - `atfparse.remove_hyphens`
  - `prosody.style`
  - `phonetize.process.geminate_policy`
  - `phonetize.timing_model.speech.wpm`
- Unknown keys are rejected.
- Example invalid key:
  - `common.strict`
- If any requested `--set`, `--get`, `--unset`, or `--set-default` key is
  invalid, the command exits with an error and must not modify the config file.

Listing format:

- `--list` prints each known key with:
  - full path
  - type display
  - default value or required marker
  - canonical help text
- Representative output shape:
  - `common.prefix { TEXT } (required) : Shared output prefix used by file-producing CLIs.`
  - `atfparse.preserve_h { true | false } (default: false) : Preserve original h/H characters.`

Filtering behavior:

- `--list SUBSTRING` shows only keys whose full path contains that substring.
- Example:
  - `--list atfparse`
  - lists all keys containing `atfparse`
  - `--list timing_model`
  - lists nested timing-related keys once that subtree exists in schema

Getter behavior:

- `--get KEY` prints the stored effective config value for that key.
- Example:
  - `--get common.log_append`
  - prints `false`

Unset behavior:

- `--unset KEY` clears the explicit YAML value by writing `null`.
- This represents the option as absent-from-config so downstream program logic
  can interpret the absence using its own effective-default behavior.
- Representative examples:
  - `--unset prosody.style` -> `null`
  - `--unset common.log` -> `null`

Set-default behavior:

- `--set-default KEY` writes the schema default value explicitly.
- Representative examples:
  - `--set-default prosody.style` -> `lob`
  - `--set-default common.log_append` -> `false`

Null interpretation note:

- `null` in the stored config means the option is not explicitly set by the
  config file and should be interpreted by the consuming program as absence.
- Where current runtime code already interprets nullable strings as empty
  effective strings, that existing behavior remains the downstream
  interpretation of the absent config value.

Help behavior:

- `--help` remains the standard entry point for overall command usage.
- The detailed inventory of keys belongs to `--list`, not to a giant parser
  surface full of one-flag-per-key options.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/cli/confwriter.py`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/config/default.yaml`

Design requirements:

- `confwriter` key validation must reuse the canonical config schema.
- Full-path validation must work for both flat keys and nested keys.
- `--set` parsing must accept repeatable `key=value` forms.
- Value parsing must be schema-aware rather than string-only.
- `--unset` must clear the YAML value to `null` rather than writing a schema
  default.
- `--set-default` must write the schema default value explicitly.
- `--list` output must reuse canonical help text and schema metadata.
- The tool must fail before writing if any requested key or value is invalid.
- A failed run must leave the config file unchanged.
- The new interface should remove the need for mirrored `--foo` / `--no-foo`
  writing flags.

Suggested operation model:

- parse command mode from requested operations
- load canonical schema
- validate requested keys
- validate and normalize requested values
- if all operations are valid, update or inspect config data
- write only for successful mutating operations

Representative validation expectations:

- `--set common.prefix=erra` -> valid
- `--set atfparse.remove_hyphens=false` -> valid
- `--set phonetize.process.geminate_policy=cumulative` -> valid only if that
  exact key path exists in the canonical schema
- `--set phonetize.process.accentuation_distribution_policy=85_15` -> valid
  only if that exact key path exists in the canonical schema and the policy
  value is one of the schema-approved options
- `--set phonetize.timing_model.speech.wpm=170` -> valid once phonetize
  timing keys exist in schema
- `--set phonetize.timing_model.durations.segmental_ceiling=210` -> valid only
  if that exact key path exists in the canonical schema; otherwise reject
  without modifying the file
- `--set common.strict=true` -> invalid key; exit without modifying file
- `--unset prosody.style` -> write `null`
- `--unset common.log` -> write `null`
- `--set-default prosody.style` -> write `lob`

Open implementation detail to resolve during coding:

- Whether `--get` and `--list` should require `--conf FILE` when only reading
  schema/default information, or whether they may support schema-only output
  when no file exists yet. This CR assumes `--conf FILE` remains part of the
  normal invocation shape but leaves final UX wording to implementation.

---

# Files Likely Affected

`src/akkapros/cli/confwriter.py`
`src/akkapros/lib/config.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/config/default.yaml`
`docs/akkapros/configuration.md`
`README.md`
`tests/`

---

# Acceptance Criteria

- [x] `confwriter` supports repeatable `--set key=value` operations using full
      YAML-path keys.
- [x] `confwriter` rejects unknown keys such as `common.strict`.
- [x] If any requested `--set` key or value is invalid, the command exits with
      an error and does not modify the config file.
- [x] `confwriter --list` prints the full key inventory with path, type,
      default-or-required state, and canonical help text.
- [x] `confwriter --list SUBSTRING` filters the key inventory by substring in
      the full key path.
- [x] The same operations support nested schema keys such as
  `phonetize.process.geminate_policy` and
  `phonetize.timing_model.speech.wpm` when such keys exist in the canonical
  schema.
- [x] The same operations support phonetize process keys and phonetize timing-
  model keys added by later phonetizer records, and reject mistyped or unknown
  phonetize keys before any write occurs.
- [x] `confwriter --get KEY` prints the current stored effective value for that
      key.
- [x] `confwriter --unset KEY` writes `null` so the option is treated as not
  explicitly set in the config.
- [x] `confwriter --set-default KEY` writes the schema default value
  explicitly.
- [x] `--unset prosody.style` resets the key to `null`.
- [x] `--unset common.log` resets the key to `null`.
- [x] `--set-default prosody.style` resets the key to `lob`.
- [x] `--help` remains concise and no longer exposes the current explosion of
      one-key-per-flag config-writing options.
- [x] Public docs explain the new `confwriter` usage model.
- [x] Tests cover set/get/list/unset behavior, key validation, no-write-on-
      error behavior, and representative output formatting.
- [x] Built-in `run_tests()` coverage is updated in affected modules, and
  pytest coverage remains split between detailed unit checks and
  representative integration flows.
- [x] Documentation is updated in `docs/akkapros/confwriter.md`,
  `docs/akkapros/configuration.md`, generated/default config comments, and
  any downstream program docs that show config-edit workflows or phonetize
  key examples.

---

# Risks / Edge Cases

Possible issues:

- schema types may be presented unclearly in `--list` output
- invalid partial batches could accidentally write some keys before failing
- users may expect old `--foo` / `--no-foo` writer flags to continue working
- nullable-string versus empty-string semantics may be documented unclearly
- users may confuse `--unset` with `--set-default` unless the distinction is
  explained clearly
- substring filtering may be ambiguous if matching is case-sensitive or not

---

# Testing Strategy

Built-in self-tests (`run_tests()`):

- add or extend detailed `run_tests()` coverage in affected modules for
  set/get/list/unset/set-default behavior, no-write-on-error guarantees, and
  schema-aware phonetize path handling

Unit tests:

- valid `--set` with boolean, string, float, and enum-like values
- valid `--set` with nested-path keys once nested schema blocks exist
- valid `--set` with phonetize process keys and phonetize timing-model keys
  once those subtrees exist in schema
- invalid `--set` with an out-of-contract
  `phonetize.process.accentuation_distribution_policy` value
- invalid key rejection
- invalid value rejection for a valid key
- invalid phonetize timing-model key rejection with no file modification
- `--unset` writes `null` consistently
- `--set-default` writes schema defaults consistently
- `--list` formatting and filtering
- `--get` output for existing values and default-backed values
- no file modification on failed validation

Integration tests:

- build a config through repeated `--set` operations
- build a config through repeated `--set` operations including at least one
  nested-path key
- inspect it with `--get`
- reset values with `--unset`
- restore defaults with `--set-default`
- verify deterministic YAML after successful edits

Manual review:

- inspect `confwriter --help` for reduced noise
- inspect `confwriter --list` output for clarity and discoverability

---

# Rollback Plan

If the new operation-oriented surface proves too disruptive, restore the prior
per-option writer flags together with their docs and tests. Partial rollback is
discouraged because mixed command styles would create avoidable user confusion.

---

# Related Issues

- [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- [ADR-037](../adr/037-centralized-help-message-registry-for-cli-and-config-docs.md)
- [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)
- [CR-030](030-add-package-wide-yaml-config-and-confwriter.md)
- [CR-031](031-centralize-cli-help-text-for-cli-and-config-doc-emission.md)
- [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)

---

# Tasks

## Implementation

- [x] Replace per-option writer flags with set/get/list/unset/set-default operations
- [x] Reuse canonical schema validation for key paths and values
- [x] Ensure failed validation leaves the config file unchanged
- [x] Implement schema-aware display formatting for `--list`
- [x] Implement null-clearing semantics for `--unset`
- [x] Implement schema-default writing for `--set-default`

## Tests

- [x] Add or extend detailed built-in `run_tests()` coverage in affected
  modules
- [x] Add pytest unit tests for set/get/list/unset behavior and schema-aware
  validation
- [x] Add pytest regression/integration tests for no-write-on-error behavior
  and representative config-edit workflows

## Documentation

- [x] Create or update `docs/akkapros/confwriter.md` as the detailed command
  reference for the new operation-oriented model
- [x] Update `docs/akkapros/configuration.md` and generated/default config
  comments so key-edit examples match the canonical schema
- [x] Remove stale examples using one-key-per-flag writer options from all
  impacted docs
- [x] Update any impacted downstream program docs, for example
  `docs/akkapros/fullprosmaker.md`, wherever config-edit workflows or
  phonetize-key examples are shown
- [x] Keep `docs/akkapros/phonetizer.md` and
  `docs/akkapros/phonetizer-algorithm.md` synchronized anywhere they
  reference `confwriter`-driven phonetize configuration

## Review

- [x] Verify acceptance criteria

---

# Notes for CR-034

This CR intentionally focuses on the `confwriter` command surface rather than
the broader config schema. It is a usability and scalability correction for the
tooling around the existing YAML contract, and it distinguishes clearly between
clearing an explicit config value and writing a schema default value.