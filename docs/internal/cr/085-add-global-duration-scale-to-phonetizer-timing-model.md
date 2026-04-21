---
cr_id: CR-085
status: Done
priority: High
impact: Mutative
created: 2026-04-19
updated: 2026-04-21
implements: 'REQ-045'
---

# Change Request: Add Global Duration Scale to Phonetizer Timing Model

# Summary

Add `phonetize.process.timing_model.durations.scale` as the first key in the
phonetizer `durations` block with default `1.0`, and apply it as a global
multiplier for all other numeric leaves in that `durations` tree when the
value differs from `1.0`.

The implementation shall special-case `scale == 1.0` so the original configured
values are used directly, avoiding unnecessary float multiplication on the
default path. The applied scale shall be reported in phonetizer frontmatter,
logs, and metrics outputs using one canonical metadata field name.

Repository inspection on 2026-04-19 shows that no `scale` key currently exists,
the phonetizer reads duration values directly from the merged timing table, and
frontmatter/metrics currently report solver diagnostics but not a global timing
multiplier. This CR adds that missing control and reporting surface.

---

# Motivation

The current timing table is detailed and useful, but global retuning requires a
large coordinated edit across many keys. A single scale parameter reduces that
friction while preserving the existing detailed table.

Because the user explicitly wants `1.0` to behave as true identity rather than
`value * 1.0`, the implementation must treat the default path specially.

---

# Scope

## Included

- Add `durations.scale: 1.0` as the first key in the `durations` block.
- Validate `scale` as positive numeric input.
- Apply the scale to all duration leaves under `durations` except `scale`
  itself when `scale != 1.0`.
- Use unscaled configured values directly when `scale == 1.0`.
- Ensure runtime, verification, and reporting use one coherent effective
  duration view.
- Record the applied scale in phonetizer frontmatter.
- Surface the applied scale in phonetizer logs.
- Surface the applied scale in metrics outputs that summarize phonetizer timing
  context.
- Update config/help/demo/doc/test surfaces.

## Not Included

- Removing or renaming existing duration keys.
- Changing metrics formulas beyond reporting the applied scale.
- Scaling unrelated config outside the `durations` block.

---

# Current Behavior

Observed current behavior on 2026-04-19:

- the phonetizer timing defaults and `src/akkapros/config/default.yaml` have no
  `durations.scale` key
- runtime helpers such as `_consonant_anchor()`, `_vowel_anchor()`,
  `_vowel_bounds()`, `_timing_refs()`, and pause helpers read directly from the
  merged duration table
- `verify_phonetize_config()` validates the raw configured duration table
- phonetizer frontmatter currently records solver diagnostics but not an applied
  global timing scale
- metrics extracts phonetizer diagnostics from frontmatter but has no scale
  field to report

The repository therefore has no single runtime multiplier and no reporting path
for such a multiplier.

---

# Proposed Change

## 1. Add the new key at the top of `durations`

The canonical timing table begins with:

- `durations.scale: 1.0`

## 2. Derive one effective duration table

- If `scale == 1.0`, use the original configured duration values directly.
- If `scale != 1.0`, multiply every other numeric duration value under
  `durations` by the scale before runtime use.
- `durations.scale` itself is configuration metadata and is never scaled.

The same effective table must be used by runtime realization and by any
verification/reporting surface that depends on current effective durations.

## 3. Report the applied scale

The phonetizer must record the applied scale in emitted frontmatter and expose
it in logging. Metrics outputs that summarize phonetizer timing context must
also surface the same scalar.

Canonical reporting field:

- `metadata.data.phonetize.duration_scale`

Contract:

- Frontmatter written by phonetizer includes
  `metadata.data.phonetize.duration_scale`.
- Metrics extraction includes `duration_scale` in phonetizer diagnostics when
  present in input frontmatter.
- Human-readable metrics output prints the same `duration_scale` value in the
  diagnostics section.

## 4. Keep the contract visible everywhere

The new key must appear consistently in:

- default YAML
- schema/help/config-path inventory
- demo YAML
- phonetizer/configuration docs
- tests that pin default and override behavior

---

# Technical Design

Concrete execution surfaces:

- extend the default timing-model schema in `src/akkapros/lib/phonetize.py` and
  `src/akkapros/config/default.yaml`
- introduce one helper that derives the effective duration table from
  `durations.scale`, with a true no-op path at `1.0`
- update `verify_phonetize_config()` so it validates `scale > 0` and does not
  allow the scaled effective table to violate active timing invariants after
  conversion to runtime values
- route runtime anchor helpers and reference helpers through that effective
  table
- add the canonical frontmatter field
  `metadata.data.phonetize.duration_scale`
- update metrics extraction and human-readable metrics output to surface the
  applied scale from frontmatter
- update logging/help/docs/tests/demo configs accordingly

Recommended reporting contract:

- frontmatter: `metadata.data.phonetize.duration_scale`
- logs: include the active scale in phonetizer timing-model summaries
- metrics: expose the same value in JSON/text where phonetizer timing context
  is summarized

Implementation order contract:

1. Add config key and schema/help visibility.
2. Add effective-duration derivation helper and route runtime through it.
3. Route verification through the same effective-duration view.
4. Add frontmatter/logging reporting.
5. Add metrics extraction/reporting wiring.
6. Update tests and public docs.

---

# Files Likely Affected

src/akkapros/lib/phonetize.py  
src/akkapros/lib/metrics.py  
src/akkapros/lib/helpmsg.py  
src/akkapros/config/default.yaml  
src/akkapros/cli/phonetizer.py  
src/akkapros/cli/confwriter.py  
tests/test_phonetize_lib.py  
tests/test_config_support.py  
tests/test_integration.py  
tests/test_metrics_stats.py  
docs/akkapros/configuration.md  
docs/akkapros/phonetizer.md  
docs/akkapros/metrics-computation.md  
docs/akkapros/phonetizer-phone-file-guide.md  
demo/akkapros/lexlinks/construct-demo.yaml  
demo/akkapros/prosmaker/corpus-demo.yaml  

---

# Acceptance Criteria

- [x] `durations.scale: 1.0` exists and is the first key in the canonical
      `durations` block.
- [x] `scale == 1.0` uses original configured values directly.
- [x] `scale != 1.0` multiplies every other duration leaf under `durations`.
- [x] The effective scaled table is used coherently by runtime realization.
- [x] Verification rejects non-positive scale values and does not silently allow
      invalid scaled effective relations.
- [x] Phonetizer frontmatter records the applied scale.
- [x] Phonetizer logs and metrics outputs surface the applied scale.
- [x] Default/help/demo/doc/test surfaces reflect the new key.

---

# Risks / Edge Cases

- Applying scale in some helpers but not others would create mismatched timing
  behavior across segments, pauses, and references.
- Rounding or scaling after verification could produce an effective table that
  violates ordering relations unless validation uses the same effective view.
- Forgetting the `1.0` no-op path would introduce pointless float noise into
  the default runtime.

---

# Testing Strategy

Unit tests:

- default config exposes `durations.scale = 1.0`
- `scale == 1.0` preserves original values exactly
- non-default scale changes effective anchors/references coherently
- verification rejects invalid scale values
- frontmatter and metrics report the applied scale

Integration tests:

- CLI path override for `durations.scale` changes emitted phone-row durations
- metrics output reflects the same scale value recorded by phonetizer

Manual checks:

- inspect default/help/demo/doc surfaces to confirm `scale` appears first in the
  `durations` block

Verification commands (implementation handoff):

- `pytest tests/test_config_support.py -q`
- `pytest tests/test_phonetize_lib.py -q`
- `pytest tests/test_metrics_stats.py -q`
- `pytest tests/test_integration.py -q`

---

# Rollback Plan

Remove `durations.scale`, restore direct use of configured duration values, and
remove the added reporting fields.

---

# Related Issues

- [REQ-045](../req/045-global-phonetizer-duration-scale.md)
- [CR-068](068-ratio-based-parameters.md)

---

# Tasks

## Implementation

- [x] Add `durations.scale`
- [x] Derive one effective scaled duration table
- [x] Route runtime and verification through that table
- [x] Surface the applied scale in frontmatter, logs, and metrics outputs

## Tests

- [x] Update config/help surface tests
- [x] Add runtime/metrics reporting coverage for scale

## Documentation

- [x] Update phonetizer/configuration/metrics docs and demo YAML examples

## Review

- [x] Verify the `1.0` path is a true no-op

---

# Implementation Blockers
