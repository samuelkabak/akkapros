---
cr_id: CR-032
status: Draft
priority: High
impact: Mutative
created: 2026-04-03
updated: 2026-04-03
implements: 'ADR-038, REQ-023'
---

# Change Request: Require Prefixes, Rename Config Sections, and Inherit Syllabify Settings

# Summary

Tighten the grouped-config implementation so prefix-dependent tools require a
non-null effective prefix, config sections use library-stage names, the four
additive punctuation-extension settings are renamed to explicit `extra_*`
forms in config keys and syllabifier-facing CLI flags, and metrics inherits
those settings plus `extra_vowels` / `extra_consonants` from upstream front
matter instead of configuring them independently.

This CR coordinates the contract correction requested after the first grouped-
config rollout.

---

# Motivation

- Fix null-prefix ambiguity in artifact-producing CLIs.
- Make additive punctuation settings visibly additive.
- Prevent metrics from diverging from syllabification punctuation behavior or
  character recognition behavior.
- Align config naming with the library-stage architecture.

The current grouped-config contract is workable but internally inconsistent.
This CR narrows and clarifies the contract rather than expanding it.

---

# Scope

## Included

- Require non-null effective `prefix` in every prefix-dependent CLI.
- Require `confwriter` to reject writes that would leave the shared prefix null.
- Rename config sections from CLI-wrapper names to library-stage names.
- Rename the four additive punctuation-extension settings to explicit
  `extra_*` names in config keys and in syllabifier-facing CLI options using
  `--extra-*` flag forms.
- Remove independent ownership of those four settings plus
  `extra_vowels` / `extra_consonants` from metrics config.
- Remove the corresponding punctuation-extension options plus
  `--extra-vowels` / `--extra-consonants` from the metricalc CLI, since
  metricalc must read inherited values from input front matter rather than
  from command-line flags.
- Propagate those settings through YAML front matter from syllabify to prosody
  and consume them in metrics from the input file.
- Update tests and documentation accordingly.

## Not Included

- Redesigning unrelated config keys.
- Introducing a new fullprosmaker YAML section.
- Broad frontmatter redesign beyond the inherited punctuation-setting path
  needed for this CR.

---

# Current Behavior

The current grouped-config rollout still allows a null shared prefix, still
uses CLI-wrapper section names, still names four additive punctuation settings
without the `extra_` qualifier on the syllabifier/config side, and still lets
metrics own separate config and CLI copies of those settings plus its own
copies of `extra_vowels` and `extra_consonants`.

This means users can build configs that remain partly invalid for output naming
and can theoretically diverge punctuation behavior and character recognition
between syllabification and metrics.

---

# Proposed Change

Adopt the following behavior.

- Prefix-dependent CLIs reject execution unless the effective prefix is set.
- `confwriter` rejects config creation or update when the effective shared
  prefix would remain null.
- Config sections are renamed to the library-stage map:
  - `atfparse`
  - `syllabify`
  - `prosody`
  - `metrics`
  - `print`
- The four additive punctuation-extension settings are renamed to:
  - `extra_short_punct_chars`
  - `extra_long_punct_chars`
  - `extra_short_punct_pattern`
  - `extra_long_punct_pattern`
- The syllabifier-owned character-set settings are:
  - `extra_vowels`
  - `extra_consonants`
- The corresponding syllabifier CLI flags use dash-form names:
  - `--extra-short-punct-chars`
  - `--extra-long-punct-chars`
  - `--extra-short-punct-pattern`
  - `--extra-long-punct-pattern`
- The syllabifier owns these settings, writes them into front matter, prosmaker
  preserves them, and metricalc reads them from the input file.
- Metricalc does not expose independent CLI flags for these settings and does
  not retain them in the metrics config section.

---

# Technical Design

Architecture notes:

Components:
- shared config validation and schema emission under `src/akkapros/lib/`
- frontmatter propagation logic under `src/akkapros/lib/frontmatter.py`
- CLI wrappers under `src/akkapros/cli/`
- canonical config example under `src/akkapros/config/default.yaml`

Design requirements:

- Prefix validation must occur before processing begins.
- Config writing must never persist a runnable config with null shared prefix.
- Config section labels must follow library-stage naming, not wrapper naming.
- Metrics must not own an independent configurable copy of the four additive
  punctuation-extension settings or of `extra_vowels` / `extra_consonants`.
- Metricalc must not expose independent command-line flags for those inherited
  settings.
- Frontmatter propagation of these settings must be deterministic and explicit.
- Documentation and tests must migrate together with the contract.

Representative migration examples:

- section rename: `prosmaker` -> `prosody`
- section rename: `metricalc` -> `metrics`
- key rename: `short_punct_chars` -> `extra_short_punct_chars`
- key rename: `long_punct_pattern` -> `extra_long_punct_pattern`
- syllabifier CLI rename: `--short-punct-pattern` ->
  `--extra-short-punct-pattern`
- metricalc CLI removal: inherited punctuation-extension flags removed;
  metricalc reads front matter instead
- metricalc CLI removal: `--extra-vowels` and `--extra-consonants` removed;
  metricalc reads front matter instead

---

# Files Likely Affected

`src/akkapros/config/default.yaml`
`src/akkapros/lib/config.py`
`src/akkapros/lib/frontmatter.py`
`src/akkapros/lib/helpmsg.py`
`src/akkapros/cli/`
`docs/akkapros/`
`docs/GETTING_STARTED.md`
`README.md`
`tests/`

---

# Acceptance Criteria

- [ ] Prefix-dependent CLIs reject null effective prefix.
- [ ] `confwriter` rejects writes that would leave the shared prefix null.
- [ ] Config sections use library-stage names instead of CLI-wrapper names.
- [ ] The four additive punctuation-extension settings use the new `extra_*`
  names in config and in syllabifier CLI surfaces using `--extra-*` flag
  forms.
- [ ] Metrics no longer owns separate config copies of those four settings or
  of `extra_vowels` / `extra_consonants`.
- [ ] Metricalc no longer exposes separate CLI flags for those inherited
  settings.
- [ ] Syllabifier emits those settings into front matter, prosmaker preserves
  them, and metricalc consumes them from the input file.
- [ ] Tests are updated for section renames, prefix validation, renamed options,
      and frontmatter inheritance.
- [ ] User-facing and developer-facing docs are updated.

---

# Risks / Edge Cases

Possible issues:

- existing user configs will need migration to the new section names
- existing tests and fixtures may rely on nullable prefix behavior
- frontmatter propagation bugs could leave metrics without the inherited values
- compatibility questions may arise for legacy configs that still use the older
  CLI-wrapper section names

---

# Testing Strategy

Unit tests:

- prefix validation for prefix-dependent tools
- `confwriter` rejection of null effective prefix
- schema validation for renamed section names and renamed additive keys
- metricalc CLI coverage verifying inherited syllabify-owned flags are not
  exposed
- frontmatter propagation and preservation of the syllabify-owned settings,
  including `extra_vowels` and `extra_consonants`

Integration tests:

- config-driven runs with renamed library-stage sections
- failure path for null prefix in config-backed execution
- syllabify -> prosody -> metrics pipeline run verifying inherited punctuation
  settings are consumed downstream

Manual review:

- inspect config docs and examples for the section rename map and renamed keys
- verify the prefix rule is explained consistently across docs

---

# Rollback Plan

If the contract correction proves too disruptive, revert the new validation and
rename rules together, restoring the earlier grouped-config contract from the
first rollout. Partial rollback is discouraged because it would reintroduce
mixed naming and ownership semantics.

---

# Related Issues

- [ADR-038](../adr/038-mandatory-prefix-library-named-config-sections-and-inherited-punctuation-options.md)
- [REQ-023](../req/023-mandatory-prefix-library-named-config-sections-and-inherited-punctuation-settings.md)
- [CR-030](030-add-package-wide-yaml-config-and-confwriter.md)

---

# Tasks

## Implementation

- [ ] Enforce mandatory effective prefix in prefix-dependent tools
- [ ] Enforce non-null effective prefix in `confwriter`
- [ ] Rename config sections to the library-stage names
- [ ] Rename the four additive punctuation-extension settings to `extra_*`
  config keys and syllabifier `--extra-*` flags
- [ ] Remove metrics ownership of those four settings plus `extra_vowels` /
  `extra_consonants`
- [ ] Remove the corresponding inherited punctuation flags and
  `--extra-vowels` / `--extra-consonants` from metricalc CLI
- [ ] Propagate and consume the inherited settings through front matter

## Tests

- [ ] Add or update unit tests for prefix validation and schema renames
- [ ] Add or update integration tests for inherited punctuation settings in metrics

## Documentation

- [ ] Update config reference docs and examples
- [ ] Update developer-facing docs and migration notes

## Review

- [ ] Verify acceptance criteria