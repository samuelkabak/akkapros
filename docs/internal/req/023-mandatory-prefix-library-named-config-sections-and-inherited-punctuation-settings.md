---
req_id: REQ-023
status: Draft
priority: High
impact: Mutative
created: 2026-04-03
updated: 2026-04-03
related_adrs: 'ADR-003, ADR-004, ADR-036, ADR-038'
implemented_by: 'CR-032'
---

# Requirement: Mandatory Prefix, Library-Named Config Sections, and Inherited Syllabify Settings

# Summary

The system shall tighten the grouped-config contract so that prefix-dependent
tools require a non-null effective prefix, config sections use library-stage
names, and the syllabification stage owns the additive punctuation-extension
settings plus `extra_vowels` and `extra_consonants`, with those settings
inherited downstream through YAML front matter.

This requirement is a follow-up to the first grouped-config rollout. It fixes
inconsistencies introduced by that rollout without broadening scope beyond the
current Python pipeline tools.

---

# Motivation

Nullable prefixes, CLI-name section labels, and duplicated syllabify-option
ownership create ambiguity in both configuration and runtime behavior. The
pipeline already has a stage architecture and a frontmatter-propagation model,
so the grouped-config contract should align with those existing structures
instead of competing with them.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given a CLI whose outputs use the shared prefix contract, when effective
      options are resolved, then `prefix` is mandatory.
- [ ] Given a prefix-dependent CLI receives no explicit CLI prefix and the
      effective config value for the shared prefix remains null, when the CLI is
      run, then execution is rejected with a clear validation error before stage
      processing begins.
- [ ] Given `confwriter` is asked to create or update a config file, when the
      effective shared prefix would remain null after applying overrides, then
      the command rejects the write.
- [ ] Given a valid config file for prefix-dependent tools, when the shared
      prefix is inspected, then it is not null.
- [ ] Given the additive punctuation-extension settings are materialized in YAML
      or CLI options, when they are named, then they use these canonical names:
      `extra_short_punct_chars`, `extra_long_punct_chars`,
      `extra_short_punct_pattern`, and `extra_long_punct_pattern`.
- [ ] Given CLI flags exist for those four settings, when users inspect help or
      docs, then the syllabifier-facing flags use the matching `--extra-...`
      dash-form names rather than the earlier ambiguous names.
- [ ] Given config sections are materialized in source control, when the schema
      is inspected, then section names follow the library-stage names rather
      than the CLI wrapper names.
- [ ] Given the full current pipeline stage map is applied to config sections,
      when the config is
      inspected, then the sections are `atfparse`, `syllabify`, `prosody`,
      `metrics`, and `print`, alongside `common`.
- [ ] Given the syllabifier resolves effective values for the four additive
      punctuation-extension settings plus `extra_vowels` and
      `extra_consonants`, when it writes output, then those values are emitted
      into YAML front matter for downstream reuse.
- [ ] Given prosmaker reads a syllabifier-produced input file, when it writes
      downstream output, then it preserves those inherited syllabify-owned
      extension values in the output front matter.
- [ ] Given metricalc reads a pipeline input file produced upstream, when it
-      resolves punctuation-extension behavior and character recognition, then
      it consumes the inherited values from input front matter rather than from
      an independent metrics config section.
- [ ] Given metricalc consumes those inherited syllabify-owned extension
      settings from input front matter, when its CLI and config surfaces are
      inspected, then they do not expose separate options for those four
      punctuation settings or for `extra_vowels` / `extra_consonants`.
- [ ] Given grouped config is inspected after this change, when punctuation-
      extension ownership is reviewed, then the metrics section does not define
      separate copies of those four syllabification-owned settings.
- [ ] Given grouped config is inspected after this change, when syllabify-owned
      character-set extension ownership is reviewed, then the metrics section
      does not define separate copies of `extra_vowels` or
      `extra_consonants`.
- [ ] Given docs are updated, when users read config and CLI guidance, then the
      rename map, mandatory-prefix rule, and inherited punctuation-setting rule
      are explained explicitly.
- [ ] Given tests are updated, when unit and integration suites are run, then
      they cover prefix validation, config-section rename behavior, option-name
      migration, and frontmatter-based syllabify-setting inheritance into
      metricalc.

---

# User Story (optional)
> As a user of the grouped pipeline config, I want one valid shared prefix and
> one authoritative source of syllabifier extension settings so that generated
> files are named predictably and downstream metrics cannot silently diverge
> from upstream syllabification behavior.

---

# Interface Notes
- Shared prefix contract:
  - applies to prefix-dependent artifact-producing CLIs
  - rejects null effective prefix at runtime
  - rejects config writes that leave the shared prefix null
- Config section map used by this requirement:
  - `common`
  - `atfparse`
  - `syllabify`
  - `prosody`
  - `metrics`
  - `print`
- Renamed additive punctuation settings:
  - `extra_short_punct_chars`
  - `extra_long_punct_chars`
  - `extra_short_punct_pattern`
  - `extra_long_punct_pattern`
- Additional inherited syllabifier character-set settings:
      - `extra_vowels`
      - `extra_consonants`
- Matching syllabifier CLI flags:
      - `--extra-short-punct-chars`
      - `--extra-long-punct-chars`
      - `--extra-short-punct-pattern`
      - `--extra-long-punct-pattern`
- Metricalc surface rule:
      - does not rename or retain independent CLI/config options for these four
            punctuation settings or for `extra_vowels` / `extra_consonants`
      - reads inherited values from input front matter instead
- Affected components:
  - `src/akkapros/config/default.yaml`
  - `src/akkapros/lib/config.py`
  - CLI wrappers under `src/akkapros/cli/`
  - `src/akkapros/lib/frontmatter.py`
  - user and developer documentation

---

# Open Questions
- [x] None.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: large
- Migration:
      - rename config sections and config-writing flags to the library-stage names
  - require a non-null effective shared prefix for prefix-dependent tools
      - rename the four additive punctuation-extension settings in YAML and in
            syllabifier-facing CLI flags
      - remove duplicated ownership of those settings plus `extra_vowels` /
            `extra_consonants` from metrics config
      - remove duplicated ownership of those settings plus `extra_vowels` /
            `extra_consonants` from metricalc CLI
  - propagate them through front matter from syllabify to prosody to metrics

# Related
- Related ADRs: [ADR-003](../adr/003-output-prefix-convention.md),
  [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md),
  [ADR-036](../adr/036-package-wide-yaml-configuration-and-cli-override-precedence.md),
  [ADR-038](../adr/038-mandatory-prefix-library-named-config-sections-and-inherited-punctuation-options.md)
- Related REQs: [REQ-013](013-cli-file-front-matter-and-metadata-propagation.md),
  [REQ-022](022-package-wide-yaml-config-and-confwriter.md)
- Implementation CRs: [CR-032](../cr/032-require-prefixes-rename-config-sections-and-inherit-punctuation-settings.md)

# Non-Goals
- This requirement does not redefine the broader grouped-config concept from the
  earlier rollout.
- This requirement does not add new punctuation semantics beyond renaming the
      additive settings and clarifying their ownership.
- This requirement does not require non-Python tools outside the current
  package pipeline to adopt the same section naming in this wave.

# Security / Safety Considerations
- Rejecting null prefixes reduces accidental output naming drift and unintended
  artifact placement.
- Frontmatter inheritance of punctuation settings and extra vowel/consonant
      settings must remain explicit and deterministic so downstream stages do not
      silently infer mismatched behavior.