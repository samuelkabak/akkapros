---
adr_id: ADR-038
status: Proposed
created: 2026-04-03
updated: 2026-04-03
superseded_by: null
---

# 38. Mandatory Prefix, Library-Named Config Sections, and Inherited Punctuation Options

## Plain Summary

Tighten the package-wide config contract so output prefixes are required,
config-section names follow library-stage names, and syllabification-owned
extension settings are inherited downstream through front matter instead of
being reconfigured independently in metrics.

This resolves inconsistencies introduced by the first grouped-config rollout and
restores one authoritative source for output naming and punctuation behavior.

## Context and Problem Statement

The grouped config introduced in [ADR-036](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
made recurring settings easier to reuse, but it also surfaced four structural
problems.

First, `prefix` remained nullable even for programs whose artifact naming
contract depends on it. Second, four punctuation-extension options in the
syllabifier are semantically additive but are not named as additive options.
Third, metricalc currently owns duplicated extension settings for punctuation
and character-set recognition even though metrics should not be allowed to
diverge from the syllabification rules used to produce the input, and
metricalc still exposes independent runtime flags for the character-set pair.
Fourth, config-section names still follow CLI wrapper names rather than the
corresponding library-stage names.

The project needs one explicit follow-up decision that narrows the config
contract and clarifies ownership boundaries between stages.

## Decision Drivers

- Preserve one deterministic output-naming contract.
- Make additive option semantics visible in both YAML and CLI naming.
- Prevent downstream syllabification drift between syllabification and metrics.
- Align config-section names with the library-stage architecture already used by
  the pipeline and frontmatter records.
- Keep the config model testable and explicit rather than heuristic.

## Considered Options

- Keep nullable prefixes and rely on per-CLI fallback naming behavior.
- Keep current section names and duplicate extension-setting ownership in both
  syllabifier and metricalc.
- Require prefixes, rename sections to library-stage names, and move
  syllabification-owned extension settings upstream to syllabification with
  downstream inheritance.

## Decision Outcome

Chosen option: require prefixes for prefix-based tools, rename config sections
to library-stage names, and treat the syllabification extension settings as
syllabification-owned inherited options.

Concretely:

- For every CLI whose outputs use the shared prefix contract, effective
  `prefix` is mandatory.
- `confwriter` must refuse to write a config whose effective shared `prefix`
  remains null.
- Runtime CLIs that require a prefix must reject execution when the effective
  configured prefix is null and no explicit CLI prefix was supplied.
- The four additive punctuation-extension settings are renamed to:
  - `extra_short_punct_chars`
  - `extra_long_punct_chars`
  - `extra_short_punct_pattern`
  - `extra_long_punct_pattern`
- The syllabifier-owned character-set extension settings are:
  - `extra_vowels`
  - `extra_consonants`
- Their syllabifier CLI flags use the matching `--extra-...` dash forms.
- These settings are owned by the syllabification stage, emitted into YAML
  front matter by the syllabifier, preserved by prosmaker, and consumed by
  metricalc from the input file rather than from an independent metrics config
  section.
- Metricalc does not expose independent CLI flags for these inherited settings
  and does not retain them in the metrics config section.
- Config-section names use library-stage names rather than CLI wrapper names.
  The stage map is:
  - `atfparse`
  - `syllabify`
  - `prosody`
  - `metrics`
  - `print`

## Pros and Cons of the Options

### Chosen Option

- Pros: eliminates null-prefix ambiguity for artifact-producing CLIs.
- Pros: makes additive punctuation options self-describing in YAML and CLI help.
- Pros: prevents metrics from silently using punctuation settings or character
  classes different from the settings that shaped the syllabified input.
- Pros: avoids a misleading metricalc rename that would imply those settings
  remain user-configurable there.
- Pros: aligns the config surface with the library-stage architecture and the
  existing stage vocabulary used elsewhere in the repository.
- Cons: requires a mutative config-schema migration.
- Cons: requires updates to tests, docs, config examples, and any saved user
  config files.

### Other Options

- Keep nullable prefixes:
  - Pro: less migration work.
  - Con: keeps runtime naming behavior ambiguous and inconsistent.
- Keep duplicated extension settings in metrics:
  - Pro: preserves local control for metricalc.
  - Con: allows invalid divergence from the syllabification stage.

## Implications and Consequences

- Config validation must distinguish between tools that use the shared prefix
  contract and tools that do not.
- Existing config examples and tests must migrate from CLI-name sections to
  library-name sections.
- Frontmatter propagation requirements become more important because metricalc
  now depends on inherited punctuation-extension settings and inherited extra
  vowel/consonant settings from upstream files.
- The first config rollout described in [ADR-036](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
  remains historical context; this ADR tightens that contract rather than
  rewriting it out of existence.

## Links

- Related ADR: [ADR-003](003-output-prefix-convention.md)
- Related ADR: [ADR-004](004-stage-pipeline-and-pivot-format.md)
- Related ADR: [ADR-036](036-package-wide-yaml-configuration-and-cli-override-precedence.md)
- Related REQ: [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md)
- Related REQ: [REQ-022](../req/022-package-wide-yaml-config-and-confwriter.md)

## Implementation Notes (optional)

- The migration should add explicit config-validation errors for null prefix in
  prefix-dependent tools.
- The migration should update both config keys and config-writing flags to the
  new additive punctuation names, but only for config and the syllabifier-facing
  CLI surface.
- The migration should remove the inherited punctuation-extension flags and the
  independent `--extra-vowels` / `--extra-consonants` flags from metricalc
  rather than renaming them there.
- The migration should update documented examples and fixtures to the library-
  named section map defined by this ADR.

## Reviewed By

- Pending maintainer review