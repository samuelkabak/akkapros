---
adr_id: ADR-043
status: Proposed
created: 2026-04-08
updated: 2026-04-09
superseded_by: null
---

# 43. Separate Run and Process Config Blocks

## Plain Summary

Separate stage configuration into operational `run` controls and behavior-
defining `process` controls wherever the stage exposes both kinds of settings.
This keeps execution concerns distinct from linguistic or algorithmic
behavior and makes the config easier to audit and document.

The decision also removes the remaining metrics timing knobs from YAML and
moves the existing phonetize policy block under `phonetize.timing_model` so the
whole timing model is grouped under one branch.

## Context and Problem Statement

The current package-wide YAML config mixes different kinds of settings in the
same stage blocks:

- some keys control how the algorithm behaves
- some keys control what artifacts are emitted for a run
- some keys control runtime convenience or output handling

This is manageable for small sections, but it becomes harder to reason about as
stage contracts grow.

Several stage sections already show the problem clearly:

- `atfparse` mixes transliteration-normalization behavior with run toggles
- `syllabify` mixes linguistic processing controls with a run-only title
  override
- `metrics` still exposes timing keys that the current timing-model redesign
  intends to keep internal for now
- `print` mixes output-selection toggles with one phonological rendering policy
- `phonetize` separates `process` from `timing_model`, even though those policy
  controls belong to the timing model contract

The project needs one explicit decision that reorganizes the config by meaning,
not just by stage name.

## Decision Drivers

- Keep operational run controls distinct from process-defining controls
- Reduce accidental mixing of output toggles and linguistic parameters
- Keep the schema clear enough for `confwriter`, help generation, and default
  config comments
- Isolate temporary or redesign-in-progress timing defaults from the public
  metrics config surface
- Keep the phonetize timing model under one coherent top-level branch

## Considered Options

- Keep the current flat stage blocks and document each key more carefully.
- Separate `run` and `process` only for stages that already feel confusing.
- Adopt `run` and `process` subtrees as the normative stage pattern, while
  allowing stages to expose only the subtree they actually need.

## Decision Outcome

Chosen option: adopt `run` and `process` subtrees as the normative stage
pattern, while allowing stages to expose only the subtree they actually need.

Concretely:

- `common` becomes a run-only area.
- `atfparse` is split into `atfparse.process` and `atfparse.run`.
- `syllabify` is split into `syllabify.process` and `syllabify.run`.
- `prosody` exposes only `prosody.process`.
- `metrics` exposes only `metrics.run` for artifact-selection controls.
- `metrics.wpm`, `metrics.pause_ratio`, `metrics.long_punct_weight`, and
  `metrics.explicit_link_count` are removed from the approved config surface.
- `print` is split so `ipa_proto_semitic` becomes `print.process` and all
  artifact-selection toggles remain in `print.run`.
- `phonetize.timing_model` is rehomed under `phonetize.process` so the
  phonetize timing contract remains part of the stage's process block.
- Stages that have no keys in one category do not need to expose an empty
  subtree.

The approved stage mapping is:

- `common.run`: `prefix`, `outdir`, `quiet`, `no_console`, `log`, `log_append`
- `atfparse.process`: `remove_hyphens`, `preserve_case`, `preserve_h`
- `atfparse.run`: `strict`, `append`
- `syllabify.process`: `extra_vowels`, `extra_consonants`,
  `extra_short_punct_chars`, `extra_long_punct_chars`,
  `extra_short_punct_pattern`, `extra_long_punct_pattern`, `number_format`,
  `merge_hyphen`, `merge_lines`
- `syllabify.run`: `title`
- `prosody.process`: `style`, `mora_mode`, `relax_last`
- `metrics.run`: `csv`, `table`, `json`
- `print.process`: `ipa_proto_semitic`
- `print.run`: `acute`, `bold`, `ipa`, `circ_hiatus`, `xar`, `mbrola`,
  `print_merger`
- `phonetize.process.timing_model`: existing phonetize timing-model and
  process-policy keys

## Pros and Cons of the Options

### Chosen Option

- Pros: clarifies which keys change algorithmic behavior and which keys only
  control a run or requested outputs.
- Pros: makes stage sections easier to document and easier to browse in YAML.
- Pros: keeps the phonetize timing contract grouped under the phonetize
  process block instead of reversing the stage-level run/process structure.
- Pros: removes redesign-in-progress metrics timing controls from the public
  YAML surface.
- Cons: breaks existing config paths for several keys.
- Cons: requires coordinated updates across default YAML, help text,
  `confwriter`, runtime resolution, and documentation.
- Cons: requires a migration path for users who already adopted the older key
  layout.

### Other Options

- Keep flat stage blocks:
  - Pro: smallest schema change.
  - Con: continues mixing run/output controls with process semantics.
- Split only some stages:
  - Pro: fewer migration changes.
  - Con: leaves the schema inconsistent and harder to explain.

## Implications and Consequences

- `src/akkapros/config/default.yaml` must be rewritten to use the new subtree
  shape.
- Config schema, path validation, and `confwriter` path inventory must expose
  only the approved new paths.
- CLI help, generated config comments, and configuration docs must use the same
  new path inventory.
- Runtime config resolution must treat removed keys as out of contract rather
  than silently documenting them as still supported.
- Existing records that referenced flat stage keys, or
  top-level `phonetize.process` without the nested `timing_model` subtree
  remain historical; implementation records must cross-reference this ADR when
  changing the active schema.
- The metrics stage must keep the removed timing controls internal until a
  later redesign record re-exposes them deliberately.

## Links

- Related ADR: [ADR-036](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- Related ADR: [ADR-039](039-replacement-of-timing-model.md)
- Related ADR: [ADR-040](040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Related CR: [CR-030](../cr/030-add-package-wide-yaml-config-and-confwriter.md)
- Related CR: [CR-035](../cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- Related REQ: [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)

## Implementation Notes (optional)

- Prefer one canonical schema model that can classify keys by stage and by
  `run` or `process` role before emitting YAML comments or validating paths.
- Backward-compatible aliases are not required by this decision; if they are
  desired, they should be specified explicitly in a follow-up record.
- Migration guidance should include old-path to new-path examples for users who
  already maintain YAML configs.

## Reviewed By

- Pending maintainer review
