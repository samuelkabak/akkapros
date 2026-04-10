---
req_id: REQ-029
status: Draft
priority: High
impact: Mutative
created: 2026-04-08
updated: 2026-04-10
related_adrs: 'ADR-043, ADR-036, ADR-039, ADR-040'
implemented_by: 'CR-044'
---

# Requirement: Stage Config Run/Process Separation

# Summary

The grouped YAML config shall separate stage options into `run` and `process`
subtrees wherever both categories exist. `run` keys describe execution-time or
artifact-selection behavior, while `process` keys describe the linguistic,
phonological, or algorithmic behavior of a stage.

The common config section shall become run-only. The metrics timing keys
currently exposed in YAML shall be removed from the config surface, and the
current phonetize timing-model branch shall move under
`phonetize.process.timing_model`.

---

# Motivation

The current schema mixes output toggles, runtime convenience controls, and
process-defining controls in the same stage blocks. That makes the config
harder to audit and harder to document clearly.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the common config section is inspected, when approved keys are
      listed, then the section exposes only `common.run`.
- [ ] Given `common.run` is inspected, when its keys are listed, then they are
      exactly `prefix`, `outdir`, `quiet`, `no_console`, `log`, and
      `log_append`.
- [ ] Given the `atfparse` stage config is inspected, when keys are grouped,
      then `atfparse.process` contains exactly `remove_hyphens`,
      `preserve_case`, and `preserve_h`.
- [ ] Given the `atfparse` stage config is inspected, when keys are grouped,
      then `atfparse.run` contains exactly `strict` and `append`.
- [ ] Given the `syllabify` stage config is inspected, when keys are grouped,
      then `syllabify.run` contains exactly `title`.
- [ ] Given the `syllabify` stage config is inspected, when keys are grouped,
      then `syllabify.process` contains exactly `extra_vowels`,
      `extra_consonants`, `extra_short_punct_chars`,
      `extra_long_punct_chars`, `extra_short_punct_pattern`,
      `extra_long_punct_pattern`, `number_format`, `merge_hyphen`, and
      `merge_lines`.
- [ ] Given the `prosody` stage config is inspected, when keys are grouped,
      then the approved surface exposes `prosody.process` only and that block
      contains exactly `style`, `mora_mode`, and `relax_last`.
- [ ] Given the `metrics` stage config is inspected, when keys are grouped,
      then the approved surface exposes `metrics.run` only and that block
      contains exactly `csv`, `table`, and `json`.
- [ ] Given the `metrics` stage config is inspected, when removed keys are
      checked, then `metrics.wpm`, `metrics.pause_ratio`,
      `metrics.long_punct_weight`, and `metrics.explicit_link_count` are absent
      from the approved config surface, emitted default YAML, `confwriter`
      inventory, and config documentation.
- [ ] Given the `print` stage config is inspected, when keys are grouped, then
      `print.process` contains exactly `ipa_proto_semitic`.
- [ ] Given the `print` stage config is inspected, when keys are grouped, then
      `print.run` contains exactly `acute`, `bold`, `ipa`, `circ_hiatus`,
      `xar`, `mbrola`, and `print_merger`.
- [ ] Given the `phonetize` stage config is inspected, when timing-model and
      process-policy keys are grouped, then the approved surface exposes
      `phonetize.process.timing_model` and does not expose top-level
      `phonetize.timing_model` or the old flat `phonetize.process.*` contract.
- [ ] Given the phonetize process timing-model block is inspected, when keys
      are listed, then it contains the timing-model and process-policy keys
      previously approved for phonetize under the current timing-model
      redesign.
- [ ] Given the phonetize process timing-model block is materialized in
      emitted grouped config, when canonical defaults are inspected, then
      `phonetize.process.timing_model.accentuation_distribution_policy`
      defaults to `85_15` and `phonetize.process.timing_model.drift_policy`
      defaults to `extensible`.
- [ ] Given the approved config surface is materialized in
      `src/akkapros/config/default.yaml`, when stage comments and paths are
      inspected, then they use the new `run` / `process` grouping consistently.
- [ ] Given the config schema is consumed by `confwriter`, when full path
      inventory is listed or validated, then only the new paths are approved
      and removed paths are not presented as current contract.
- [ ] Given program help or config documentation is generated from the approved
      schema, when stage options are displayed, then the display uses the same
      new run/process grouping and removed keys are absent.
- [ ] Given this mutative schema change is documented, when migration behavior
      is described, then the documentation states whether old paths are rejected
      or otherwise handled explicitly rather than leaving compatibility
      implicit.

---

# User Story (optional)
> As a maintainer or user reading the shared config, I want run controls and
> process controls separated by meaning so that the file is easier to audit,
> easier to document, and easier to navigate by role.

---

# Interface Notes
- Approved common shape:
  - `common.run.*`
- Approved stage grouping principle:
  - `run` for execution-time, emission, or convenience controls
  - `process` for linguistic, phonological, or algorithmic controls
- Approved stage shapes:
  - `atfparse.process.*`, `atfparse.run.*`
  - `syllabify.process.*`, `syllabify.run.*`
  - `prosody.process.*`
  - `metrics.run.*`
  - `print.process.*`, `print.run.*`
      - `phonetize.process.timing_model.*`
- Removed paths include:
  - `metrics.wpm`
  - `metrics.pause_ratio`
  - `metrics.long_punct_weight`
  - `metrics.explicit_link_count`
      - top-level `phonetize.timing_model.*`
- Affected components:
  - `src/akkapros/config/default.yaml`
  - config schema and config-loading helpers under `src/akkapros/lib/`
  - `confwriter` path inventory and validation
  - CLI help text and config documentation
---

# Open Questions
- [x] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - rewrite the default YAML skeleton to the new grouped shape
  - update schema validation and path discovery together
  - update help text and config docs from the same schema source
  - decide explicitly how old config paths fail or migrate

# Related
- Related ADRs: [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md),
  [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md),
  [ADR-039](../adr/039-replacement-of-timing-model.md),
  [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Implementation CRs: [CR-044](../cr/044-restructure-stage-config-into-run-and-process-blocks.md)

# Non-Goals
- This requirement does not redesign the underlying stage algorithms.
- This requirement does not re-expose metrics timing controls under new names.
- This requirement does not redesign the broader shared path policy for config
      values beyond the explicit stage regrouping described here.

# Security / Safety Considerations
- The schema and docs must not continue advertising removed keys as approved
      current contract.
