---
cr_id: CR-044
status: Draft
priority: High
impact: Mutative
created: 2026-04-08
updated: 2026-04-09
implements: 'ADR-043, REQ-029'
---

# Change Request: Restructure Stage Config into Run and Process Blocks

# Summary

Restructure the grouped YAML config so each stage exposes `run` and `process`
subtrees according to the approved stage mapping, remove the remaining metrics
timing knobs from the config surface, and move the phonetize process-policy
block under `phonetize.timing_model`.

This CR coordinates the schema, default YAML, help text, `confwriter`, and
runtime-resolution changes required to make the new config shape the active
contract.

---

# Motivation

The current config shape still mixes operational run controls with
process-defining behavior in the same stage blocks. That weakens readability,
complicates documentation, and makes schema discovery less clear.

The config surface therefore needs one explicit mutative change that
reorganizes the stage keys by meaning.

---

# Scope

## Included

- Restructure `common` into a run-only block.
- Split `atfparse` into `process` and `run` blocks.
- Split `syllabify` into `process` and `run` blocks.
- Keep `prosody` as a process-only stage block.
- Reduce `metrics` to a run-only block containing only artifact-selection
  controls.
- Remove `metrics.wpm`, `metrics.pause_ratio`, `metrics.long_punct_weight`, and
  `metrics.explicit_link_count` from the config surface.
- Split `print` into `process` and `run` blocks.
- Move the current top-level `phonetize.timing_model` block under
  `phonetize.process` so the timing model remains part of the stage's process
  contract.
- Update `src/akkapros/config/default.yaml` comments, ordering, and path layout
  to the new schema.
- Update schema validation, `confwriter` inventory, and path-based set/get/list
  behavior to the new path inventory.
- Update runtime config resolution, CLI help text, and user-facing config docs.
- Add tests covering the new path inventory and rejection or explicit handling
  of removed paths.

## Not Included

- Redesigning the linguistic or algorithmic behavior behind existing stage
  options.
- Re-exposing metrics timing controls under alternative config paths.
- A general removal of every path-bearing config value.
- Silent backward-compatible aliasing unless another record specifies it
  explicitly.

---

# Current Behavior

The current config materialization still uses mixed stage blocks such as:

- `atfparse.remove_hyphens` alongside `atfparse.strict`
- `syllabify.title` alongside syllabification process controls
- `metrics.wpm` and `metrics.pause_ratio` in public YAML
- `print.ipa_proto_semitic` alongside output toggles
- top-level `phonetize.process.*` beside `phonetize.timing_model.*`
- `common.outdir` alongside other shared run keys in the same flat block

That shape does not separate run controls from process controls.

---

# Proposed Change

Adopt the following grouped-config shape exactly.

```yaml
common:
  run:
    prefix: "akkapros"
    outdir: "."
    quiet: false
    no_console: false
    log: null
    log_append: false

atfparse:
  process:
    remove_hyphens: false
    preserve_case: false
    preserve_h: false
  run:
    strict: false
    append: false

syllabify:
  process:
    extra_vowels: ""
    extra_consonants: ""
    extra_short_punct_chars: ""
    extra_long_punct_chars: ""
    extra_short_punct_pattern: []
    extra_long_punct_pattern: []
    number_format: ""
    merge_hyphen: false
    merge_lines: false
  run:
    title: null

prosody:
  process:
    style: "lob"
    mora_mode: "bi"
    relax_last: false

metrics:
  run:
    csv: false
    table: false
    json: false

print:
  process:
    ipa_proto_semitic: "preserve"
  run:
    acute: false
    bold: false
    ipa: false
    circ_hiatus: false
    xar: false
    mbrola: false
    print_merger: false

phonetize:
  process:
    timing_model:
      # moved here from the previous top-level phonetize.timing_model block
      ...
  run:
    ...
```

Normative rules:

- stages may omit `run` or `process` only when they have no keys in that
  category
- removed keys are out of contract and must not remain in emitted default YAML,
  help text, `confwriter` listings, or docs
- the phonetize timing contract remains otherwise unchanged except for moving
  the timing-model subtree under `phonetize.process`
- within the migrated `phonetize.process.timing_model` subtree, canonical
  defaults include `accentuation_distribution_policy: 85_15` and
  `drift_policy: extensible`
- metrics timing defaults removed from config are internal runtime concerns
  until a later redesign re-exposes them deliberately

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/config/default.yaml`
- config schema and resolution helpers under `src/akkapros/lib/`
- `src/akkapros/cli/confwriter.py`
- CLI entrypoints that read grouped config
- centralized help-text registry and generated config comments
- configuration docs under `docs/akkapros/`
- tests covering config inventory and runtime resolution

Design requirements:

- the canonical schema must classify each config key by stage and by role
  (`run` or `process`)
- `default.yaml`, `confwriter`, help text, and docs must all emit the same new
  path inventory
- removed paths must not be documented as current contract
- migration behavior for removed paths must be explicit and testable
- `phonetize.process.timing_model` must replace top-level
  `phonetize.timing_model` consistently across schema, help, docs, and
  examples
- runtime config loading must resolve the new nested paths without reintroducing
  mixed old names in public help or generated YAML

Suggested implementation direction:

- centralize config-path classification in one schema source of truth
- regenerate default-comment emission from that source rather than hand-editing
  one surface at a time
- keep path rejection or migration handling explicit in schema validation and
  tests

---

# Files Likely Affected

`src/akkapros/config/default.yaml`
`src/akkapros/lib/`
`src/akkapros/cli/`
`docs/akkapros/`
`README.md`
`tests/`

---

# Acceptance Criteria

- [ ] `src/akkapros/config/default.yaml` uses `common.run` and exposes
  `common.run.outdir`.
- [ ] `atfparse` config paths are rehomed to `atfparse.process.*` and
      `atfparse.run.*` exactly as specified by [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md).
- [ ] `syllabify` config paths are rehomed to `syllabify.process.*` and
      `syllabify.run.*` exactly as specified by [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md).
- [ ] `prosody` exposes only `prosody.process.*`.
- [ ] `metrics` exposes only `metrics.run.csv`, `metrics.run.table`, and
      `metrics.run.json`.
- [ ] `metrics.wpm`, `metrics.pause_ratio`, `metrics.long_punct_weight`, and
      `metrics.explicit_link_count` are absent from the active schema,
      generated default YAML, `confwriter` key inventory, and config docs.
- [ ] `print` exposes `print.process.ipa_proto_semitic` and the approved
      `print.run.*` artifact toggles only.
- [ ] Top-level `phonetize.timing_model.*` is removed from the active schema.
- [ ] `phonetize.process.timing_model.*` exposes the migrated phonetize timing-
  model and process-policy keys.
- [ ] `phonetize.process.timing_model.accentuation_distribution_policy`
  defaults to `85_15` in emitted grouped config.
- [ ] `phonetize.process.timing_model.drift_policy` defaults to
  `extensible` in emitted grouped config.
- [ ] `confwriter --list`, `--get`, `--set`, `--unset`, and `--set-default`
      operate on the new paths and do not advertise removed paths as current
      contract.
- [ ] Runtime config resolution for stage CLIs and `fullprosmaker` reads the
      new paths consistently.
- [ ] User-facing config documentation and generated help comments present the
      new run/process grouping consistently.
- [ ] Tests cover both the new path inventory and the explicit handling of
      removed legacy paths.

---

# Risks / Edge Cases

Possible issues:

- partial migration where `default.yaml`, `confwriter`, and docs disagree about
  the approved path inventory
- accidental reintroduction of removed metrics timing keys through help text or
  runtime fallback code
- unclear behavior for legacy config files if removed paths are neither rejected
  nor migrated explicitly
- confusion if `phonetize.process` survives in examples after the schema moves
  it under `timing_model`

---

# Testing Strategy

Unit tests:

- schema inventory reflects the new `run` / `process` grouping
- removed paths are rejected or handled explicitly as documented
- nested phonetize path migration is validated consistently

Integration tests:

- `confwriter` emits the new grouped YAML structure
- representative CLIs resolve settings from the new grouped paths
- config documentation and emitted comments stay aligned with schema output

Manual tests:

- inspect generated default YAML for stage grouping and removed keys
- inspect `confwriter --list` output for only the approved new paths
- inspect help text and config docs for stale legacy path references

---

# Rollback Plan

Revert the new schema record and restore the previous flat path inventory in the
schema, default YAML, docs, and `confwriter` surfaces together.

---

# Related Issues

- Related ADR: [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)
- Related REQ: [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md)
- Historical config baseline: [CR-030](030-add-package-wide-yaml-config-and-confwriter.md)
- Historical phonetize config baseline: [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)

---

# Tasks

## Implementation

- [ ] Rewrite the canonical schema to the new grouped path layout
- [ ] Update runtime resolution for stage CLIs and `fullprosmaker`
- [ ] Move phonetize process-policy paths under `timing_model`
- [ ] Remove the specified metrics timing keys from the public config surface

## Tests

- [ ] Add schema-inventory coverage for new paths
- [ ] Add removed-path rejection or migration coverage
- [ ] Add representative runtime-resolution coverage for the new layout

## Documentation

- [ ] Update `default.yaml` comments and ordering
- [ ] Update config docs and generated help surfaces
- [ ] Add migration guidance for old-to-new config paths

## Review

- [ ] Review path inventory against [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md)
- [ ] Verify acceptance criteria

---

# Notes for CR-044

This CR intentionally separates schema organization from algorithm redesign.
It changes how approved config paths are grouped and exposed; it does not by
itself change the linguistic semantics of the existing stage options.
