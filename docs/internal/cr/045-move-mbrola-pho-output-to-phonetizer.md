---
cr_id: CR-045
status: Draft
priority: High
impact: Mutative
created: 2026-04-08
updated: 2026-04-09
implements: 'ADR-040, ADR-043, REQ-025, REQ-029'
---

# Change Request: Move MBROLA `.pho` Output to Phonetizer

# Summary

Move MBROLA text emission out of the print stage and make it a phonetizer-owned
artifact derived directly from duration-bearing phone rows.

Under this change, phonetize becomes responsible for writing two MBROLA-style
files:

- `<prefix>_mbrola.pho` for the accentuated stream
- `<prefix>_ombrola.pho` for the original stream

The emitted `.pho` rows shall use `_` for silence, realization codes for
non-silence phonemes, integer millisecond durations from phone rows, and
intonation-derived F0 values sourced from a phonetize-owned intonation block.
For now, only baseline `f0` and stressed-syllable `stress_rise` affect emitted
Hz values.

---

# Motivation

The current internal direction is split across two incompatible ownership
models:

- the phonetizer owns the canonical row-level phonetic structure and timing
- the print stage still carries MBROLA as if it were only another surface
  rendering toggle

That split is no longer coherent once MBROLA output needs to reflect exact row
durations, silence normalization, and gemination collapse. Those behaviors are
native consequences of the phonetizer contract, not of the printer contract.

The repository therefore needs one explicit change record that rehomes MBROLA
export to the stage that already owns the underlying data model.

---

# Scope

## Included

- Reassign MBROLA `.pho` emission from print to phonetize.
- Define phonetizer-owned artifact names exactly as:
  - `<prefix>_mbrola.pho`
  - `<prefix>_ombrola.pho`
- Define the `.pho` source as the finalized phoneme-row streams produced by the
  phonetizer pipeline after duration realization.
- Define the emitted row format exactly as:
  - `phoneme_or_silence duration_in_ms frequency_in_hz`
- Define `_` as the emitted silence symbol.
- Define realization code as the emitted symbol for every non-silence phoneme
  row.
- Define contiguous identical emitted symbols with identical emitted frequency
  values as mergeable in `.pho` export by summing durations, especially to
  collapse gemination sequences.
- Add phonetize-owned intonation configuration under `phonetize.process`.
- Define default intonation values including `f0: 120` and `stress_rise: 2`.
- Define additional reserved intonation parameters for later use:
  `question_final_rise`, `statement_final_fall`, `exclamation_rise`, and
  `continuation_rise`.
- Define that, for now, only stressed syllables in the accentuated output use
  an F0 rise above baseline.
- Remove MBROLA from the approved print-stage config and print-stage artifact
  contract.
- Require downstream config, help, and documentation to treat MBROLA as a
  phonetizer artifact rather than a print artifact.

## Not Included

- Audio synthesis.
- MBROLA voice building or MBROLATOR integration.
- Redesign of the realization-code inventory itself.
- Redesign of the phonetizer timing model beyond adding intonation
  configuration.
- Applying question, statement-final, exclamatory, or continuation intonation
  contours in this change.
- Backward-compatible support for printer-owned MBROLA flags unless a later
  record adds that explicitly.

---

# Current Behavior

The active phonetizer records already make phonetize responsible for dual phone
streams and duration-bearing phone rows, but the grouped-config redesign still
lists MBROLA under `print.run.mbrola` and older printer records still describe
MBROLA as a printer output.

That leaves ownership ambiguous:

- the print stage appears to own whether MBROLA is emitted
- the phonetizer owns the row data required to emit correct `.pho` timing

As a result, the current internal contract does not yet specify where MBROLA
export actually belongs or how `.pho` rows are derived from the canonical phone
rows.

---

# Proposed Change

Adopt the following contract.

## 1. Stage ownership

- MBROLA text export is a phonetizer responsibility.
- The print stage does not emit MBROLA artifacts.
- Any current or historical printer references to MBROLA remain historical and
  are superseded for active implementation by this CR.

## 2. Artifact names

The phonetizer shall write these files:

- accentuated stream: `<prefix>_mbrola.pho`
- original stream: `<prefix>_ombrola.pho`

The accentuated `.pho` file is derived from the accentuated phone-row stream.
The original `.pho` file is derived from the original phone-row stream.

## 3. Config placement

Because the current active config regrouping places stage behavior under the
phonetize `process` block, the intonation config for MBROLA export shall live
at:

- `phonetize.process.intonation.f0`
- `phonetize.process.intonation.stress_rise`
- `phonetize.process.intonation.question_final_rise`
- `phonetize.process.intonation.statement_final_fall`
- `phonetize.process.intonation.exclamation_rise`
- `phonetize.process.intonation.continuation_rise`

Default values:

```yaml
phonetize:
  process:
    intonation:
      # Baseline pitch for the speaker's voice in Hertz (Hz)
      # Typical values: 80-180 Hz for male, 150-300 Hz for female
      # This is the neutral pitch around which intonation changes occur
      f0: 120

      # Pitch increase on stressed syllables, measured in semitones
      stress_rise: 2

      # Pitch rise at the end of a yes/no question, measured in semitones
      question_final_rise: 3

      # Pitch fall at the end of a statement, measured in semitones
      statement_final_fall: -2

      # Pitch rise on an exclamation or emphatic word, measured in semitones
      exclamation_rise: 4

      # Pitch rise indicating the speaker will continue speaking, measured in semitones
      continuation_rise: 1
    timing_model:
      ...
```

No `print.run.mbrola` key remains in the approved config surface after this
change.

Semitone relation:

| To calculate | Formula |
|--------------|---------|
| Semitone interval from `f0_1` to `f0_2` | `semitones = 12 x log2(f0_2 / f0_1)` |
| Target frequency after semitone change | `f0_2 = f0_1 x 2^(semitones / 12)` |

Representative examples from the default baseline `f0 = 120` Hz:

| Operation | Semitones | Result |
|-----------|-----------|--------|
| Stress rise | `+2` | about `134.7` Hz |
| Question rise | `+3` | about `142.7` Hz |
| Statement fall | `-2` | about `106.9` Hz |

For implementation guidance, stressed-syllable F0 is computed as:

```python
baseline_f0 = 120
stress_f0 = baseline_f0 * (2 ** (stress_rise / 12))
```

## 4. Row source and export timing

- `.pho` export shall run from phonetizer-owned phoneme rows, not from printer
  text rendering.
- Export shall occur only after duration realization has assigned integer
  millisecond durations to those rows.
- The exporter shall operate separately on the original and accentuated row
  streams.

## 5. Emitted symbol mapping

- Silence rows emit `_`.
- Non-silence rows emit the canonical realization code already carried by the
  phone row.
- The exporter shall not substitute raw source glyphs or printer-side surface
  spellings in place of realization codes.

## 6. Emitted line format

Each emitted `.pho` line shall contain exactly three whitespace-separated
fields:

```text
phoneme_or_silence duration_in_ms frequency_in_hz
```

Normative constraints:

- `phoneme_or_silence` is either `_` or one realization code
- `duration_in_ms` is the merged integer millisecond duration
- `frequency_in_hz` is the emitted row F0 derived from
  `phonetize.process.intonation`

## 7. Intonation mapping for current scope

For this CR, only stressed-syllable rise is active.

Normative rules:

- the original stream uses baseline `phonetize.process.intonation.f0` for all
  emitted `.pho` rows
- the accentuated stream uses baseline
  `phonetize.process.intonation.f0` for non-stressed rows
- rows belonging to stressed syllables in the accentuated stream use an F0
  derived from `f0` and `stress_rise`
- `question_final_rise`, `statement_final_fall`, `exclamation_rise`, and
  `continuation_rise` are part of the approved config surface but are not yet
  applied by this CR

## 8. Adjacent-row merge rule

Before writing `.pho`, the exporter shall merge contiguous rows whenever their
emitted symbol and emitted frequency would both be identical.

Merge rule:

- if two neighboring rows would emit the same `phoneme_or_silence` symbol,
  and the same `frequency_in_hz`, they collapse into one `.pho` row
- the merged row duration is the sum of the input durations
- the emitted symbol is unchanged
- the emitted F0 is unchanged

This merge rule applies generally and is specifically required for gemination,
where consecutive identical phoneme rows would otherwise produce artificial
duplication in `.pho` output. It must not merge across a stress-driven F0
change.

---

# Technical Design

Architecture notes:

Components:
- phonetizer row builder and duration realization pipeline
- phonetizer `.pho` exporter
- grouped config schema and default YAML emission
- `confwriter` path inventory and help text
- phonetizer CLI and any pipeline wrapper that exposes phonetizer outputs
- print-stage config/help/docs that currently mention MBROLA

Data flow:
- `_tilde` input feeds phonetizer structure generation
- phonetizer produces original and accentuated phone-row streams
- duration realization assigns integer millisecond durations
- MBROLA export traverses each row stream and writes `.pho`

Normative design constraints:
- `.pho` export must not introduce a second phoneme-classification system
- `.pho` export must consume the same canonical realization-code inventory
  already approved for phone rows
- silence normalization must happen in the exporter, with `_` as the sole
  silence symbol
- intonation controls belong to `phonetize.process.intonation`, not to an
  MBROLA-specific subtree
- the current scope applies only baseline `f0` and stressed-syllable
  `stress_rise`; other approved intonation parameters are reserved for later
  CRs
- row merging happens at export time and does not alter the canonical row
  streams themselves
- printer help, config, and docs must stop advertising MBROLA as a print-stage
  output

---

# Files Likely Affected

`docs/internal/cr/035-add-phonetize-stage-config-and-phone-artifact-contract.md`
`docs/internal/cr/036-define-phonetizer-phoneme-framework.md`
`docs/internal/cr/039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md`
`docs/internal/cr/040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md`
`docs/internal/cr/044-restructure-stage-config-into-run-and-process-blocks.md`
`docs/internal/req/025-two-phase-phonetizer-structure-and-duration-pipeline.md`
`docs/internal/req/029-stage-config-run-process-separation-and-common-outdir-removal.md`
`docs/internal/adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md`
`docs/internal/adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md`
`docs/akkapros/phoneprep.md`
`docs/akkapros/printer.md`
`docs/akkapros/configuration.md`

---

# Acceptance Criteria

- [ ] The active internal contract defines MBROLA `.pho` export as a phonetizer
      responsibility rather than a print-stage responsibility.
- [ ] The approved phonetizer artifact set includes `<prefix>_mbrola.pho` for
      the accentuated stream.
- [ ] The approved phonetizer artifact set includes `<prefix>_ombrola.pho` for
      the original stream.
- [ ] The approved config surface exposes `phonetize.process.intonation.f0`
  with default value `120`.
- [ ] The approved config surface exposes
  `phonetize.process.intonation.stress_rise`.
- [ ] The approved config surface also exposes
  `question_final_rise`, `statement_final_fall`, `exclamation_rise`, and
  `continuation_rise` under `phonetize.process.intonation`.
- [ ] The approved config surface no longer exposes `print.run.mbrola` as a
      current contract path.
- [ ] Each `.pho` line is specified as exactly three fields in the order
      `phoneme_or_silence duration_in_ms frequency_in_hz`.
- [ ] Silence rows emit `_`.
- [ ] Non-silence rows emit canonical realization codes from phone rows.
- [ ] `.pho` durations are derived from finalized integer millisecond phone-row
      durations.
- [ ] Original-stream `.pho` rows use baseline
  `phonetize.process.intonation.f0`.
- [ ] Stressed syllables in the accentuated output use an F0 rise derived from
  `phonetize.process.intonation.f0` and
  `phonetize.process.intonation.stress_rise`.
- [ ] `question_final_rise`, `statement_final_fall`, `exclamation_rise`, and
  `continuation_rise` are documented as approved config parameters but are
  not yet applied in this CR.
- [ ] Contiguous identical emitted symbols with identical emitted frequency are
  merged by summing durations before `.pho` serialization.
- [ ] The merge rule is explicitly documented as applying to gemination.
- [ ] Print-stage docs, help, and config references no longer present MBROLA as
      a print-stage output toggle.

---

# Risks / Edge Cases

Possible issues:

- historical printer records may continue to imply MBROLA ownership unless they
  are explicitly cross-linked as superseded for active implementation
- export-time merging must not collapse rows across a stressed/unstressed F0
  boundary even when the phoneme symbol is identical
- export-time merging must avoid crossing intervening silence rows or other
  non-identical emitted symbols
- docs could drift if config regrouping and phonetizer artifact docs are not
  updated together

---

# Testing Strategy

Specification-level verification:

- confirm the config inventory no longer lists `print.run.mbrola`
- confirm the config inventory lists `phonetize.process.intonation.f0`
- confirm the config inventory lists `phonetize.process.intonation.stress_rise`
- confirm the config inventory lists the reserved later-use parameters under
  `phonetize.process.intonation`
- confirm phonetizer artifact docs include both `.pho` outputs
- confirm printer docs no longer advertise MBROLA output

Implementation-level tests to require later:

- export accentuated phone rows to `<prefix>_mbrola.pho`
- export original phone rows to `<prefix>_ombrola.pho`
- serialize silence rows as `_`
- serialize phoneme rows using realization codes
- apply baseline `f0` to original-stream rows
- apply stressed-syllable F0 rise to accentuated stressed rows
- compute stressed F0 from semitone change using the approved formula
- merge adjacent identical emitted symbols by summed duration only when emitted
  frequency is also identical
- preserve separate rows when symbols differ or silence intervenes

---

# Rollback Plan

If this change is rejected, keep MBROLA as a printer-owned output and remove
the phonetizer-owned `.pho` artifacts and config subtree from the active
contract.

---

# Related Issues

- Extends the phonetizer artifact and config work in
  [CR-035](035-add-phonetize-stage-config-and-phone-artifact-contract.md)
- Depends on the phonetizer row contract in
  [CR-036](036-define-phonetizer-phoneme-framework.md)
- Interacts with the dual-stream architecture in
  [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)
- Narrows the config regrouping in
  [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md),
  [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md), and
  [CR-044](044-restructure-stage-config-into-run-and-process-blocks.md)
- Supersedes active implementation assumptions that still place MBROLA under
  printer-owned config or output selection

---

# Tasks

## Specification Follow-Up

- [ ] Update phonetizer contract records to include `.pho` artifacts.
- [ ] Update config regrouping records to remove `print.run.mbrola`.
- [ ] Update printer-facing records to mark MBROLA ownership as historical.

## Review

- [ ] Confirm no printer-owned MBROLA compatibility flag is required.
- [ ] Approve the `phonetize.process.intonation` config surface and initial
  parameter inventory.
- [ ] Confirm only `f0` and `stress_rise` are active in this CR.

---

# Notes for CR-045

Assumption: this CR follows the current regrouped phonetize config layout from
ADR-043 and therefore places intonation controls under
`phonetize.process.intonation` while keeping timing parameters under
`phonetize.process.timing_model`.

Assumption: for the present CR, only stressed syllables in the accentuated
output receive a pitch rise. Punctuation-driven contour application is
explicitly deferred to later records.

The original-stream filename uses `_ombrola` intentionally so the pair stays
coherent with the existing `ophone` / `phone` distinction.