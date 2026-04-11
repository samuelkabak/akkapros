---
cr_id: CR-050
status: Done
priority: High
impact: Mutative
created: 2026-04-11
updated: 2026-04-11
implements: 'ADR-045, REQ-032, ADR-043, REQ-029, REQ-030, REQ-031'
---

# Change Request: Add Third-Pass Intonation Framework and Silence Typing to Phonetizer

# Summary

Replace the current phonetizer intonation parameter naming based on `*_rise`
and `*_fall` with a compact symbolic intonation-token model rooted in `f0`,
extend the phone-row contract so pause rows carry explicit silence subtype and
per-row intonation data, and extend the phonetizer runtime from two passes to
three ordered passes.

This CR introduces one canonical three-character intonation token for emitted
phone rows, defines a normalized config surface for stress and clause-final
intonation presets, classifies pause rows by punctuation-driven silence type,
expands the serialized phone-row schema from ten fields to eleven fields, and
requires MBROLA `.pho` emission to be derived entirely from the finalized
phoneme table plus `f0`. The change is grounded in the current repository
reality that phonetizer, not printer, owns pause rows and `.pho` pitch
emission, and that spaces between words do not create silence rows while
punctuation and line breaks do.

---

# Motivation

The current intonation surface is too narrow and too asymmetric for the next
phonetizer step.

Today the active config exposes:

- `stress_rise`
- `question_final_rise`
- `statement_final_fall`
- `exclamation_rise`
- `continuation_rise`

Those keys hard-code direction words into parameter names, treat only one shape
as explicit, and do not provide a reusable token that can travel with emitted
rows. At the same time, current pause rows all use `category=S, type=S` and do
not distinguish question, statement, exclamation, continuation, or internal
non-intonational pauses even though the punctuation that created the pause is
already available to the phonetizer.

This matters because the repository now treats phone rows as the active
handoff for downstream timing, pause semantics, metrics, printer behavior, and
phonetizer-owned `.pho` export. Intonation therefore needs a stable row-level
contract rather than a small set of stage-local scalar knobs.

The repository also needs the specification to say explicitly that pause type is
the cause and final-syllable intonation is the current consequence strategy.
In this version of the phonetizer, the contour touches the last syllable before
the pause, but the architecture must preserve the possibility that later models
spread the same pause-governed intonation across a wider phrase.

It also matters because the current internal phonetizer architecture is still
described as a two-pass system:

- Phase 1 builds rows and leaves `duration=0000`
- Phase 2 fills durations on the prebuilt rows

The new intonation behavior does not fit cleanly into either existing pass.
The repository needs one explicit contract that Phase 1 now leaves both
duration and intonation unresolved, Phase 2 fills duration only, and a new
Phase 3 fills intonation only, using the row stream and pause typing already
materialized by earlier passes.

---

# Scope

## Included

- Replace `stress_rise`, `question_final_rise`, `statement_final_fall`,
  `exclamation_rise`, and `continuation_rise` with a symbolic intonation-token
  framework under `phonetize.process.intonation`.
- Extend the phonetizer runtime from two passes to three ordered passes.
- Require Phase 1 to fill all row information except duration and final
  intonation.
- Require Phase 2 to fill duration only.
- Require Phase 3 to fill intonation only.
- Keep `phonetize.process.intonation.f0` as the reference baseline for all
  intonation interpretation.
- Define the canonical three-character intonation token format used by emitted
  phone rows.
- Allow the config surface to use the compact two-character preset form shown
  below, with normalization to the canonical three-character row token.
- Add an `intonation` field to the phone-row schema.
- Preserve `duration` as a four-digit field. This CR does not reduce duration
  width because the active long-pause contract already reaches `1200-1780` ms.
- Classify silence rows by subtype derived from the punctuation or line break
  that created the pause.
- Define the punctuation-precedence and normalization rules that map pause-creating
  input material to silence subtype.
- Pin the current observed behavior that spaces do not create silence rows and
  that punctuation and line breaks do.
- Define how the last syllable before a pause receives the pause-governed
  intonation preset.
- Define MBROLA `.pho` output as a deterministic derivation from finalized
  phone rows and `f0`, not from direct reparsing of source text or separate
  stress inference.
- Define the MBROLA pitch-tail contract as one symbol, one duration, and a
  variable-length evenly spaced pitch-target list.
- Update the active phone-row serialization contract from ten fields to eleven
  fields.
- Require docs, config inventory, help surfaces, and tests to align with the
  new intonation-token and silence-typing contract.

## Not Included

- Implementing new production code in this CR document.
- Redesigning the duration solver beyond the row and config changes required to
  carry intonation information.
- Audio synthesis beyond the current phonetizer-owned `.pho` exporter.
- General-purpose preprocessing of arbitrary modern-language text into
  Akkadian-safe lexical expansions.
- Expanding symbols such as `&`, `+`, `/`, currencies, or numbers into spoken
  Akkadian words automatically.
- Changing the active four-digit duration contract.

---

# Current Behavior

Repository inspection on 2026-04-11 shows the following live behavior.

- `src/akkapros/lib/phonetize.py` currently exposes `f0`, `stress_rise`,
  `question_final_rise`, `statement_final_fall`, `exclamation_rise`, and
  `continuation_rise` in `PHONETIZE_SCHEMA`.
- The active default config in `src/akkapros/config/default.yaml` still uses
  those same keys.
- The current internal architecture still treats phonetizer as a two-pass
  system in which Phase 1 builds rows and Phase 2 fills duration.
- `PHONE_ROW_FIELDS` currently contains ten fields:
  `label`, `category`, `type`, `length`, `position`, `boundary`, `accent`,
  `realization`, `duration`, and `text`.
- Current segment rows initialize no intonation field.
- Current pause rows are created by `_new_pause_row(text, is_long=...)` and all
  use `category='S'`, `type='S'`, `position='S'`, with `length='S'` for short
  pauses and `length='L'` for long pauses.
- Current pause classification is punctuation-driven:
  - spaces are skipped and do not create pause rows
  - explicit punctuation and explicit line breaks do create pause rows
  - newline currently yields a long pause row with text `<EOL>`
  - armored punctuation suites are classified as one long pause if any long cue
    is present, otherwise one short pause if any short cue is present
- Current phone-row serialization uses hyphen-separated fixed fields followed
  by `:text`.
- Current duration placeholders and realized row durations use four digits,
  including `0000` as the placeholder and `1200-1780` for long pauses.
- Current `.pho` output is still described by older governing records as a
  three-field line ending in one emitted frequency value per row.

Observed grounding:

- `SHORT_PAUSE_PUNCTUATION_CHARS` currently includes `,`, `;`, `:`, `—`, `–`,
  parentheses, quotation marks, `/`, `\`, `|`, and daggers.
- `LONG_PAUSE_PUNCTUATION_CHARS` currently includes `.`, `?`, `!`, brackets,
  braces, angle brackets, `*`, and `#`.
- Current row serialization logic cannot support a three-digit duration-only
  contract because long pauses already exceed `999` ms.

---

# Proposed Change

Adopt the following contract.

## 1. Three-pass phonetizer contract

The active phonetizer runtime becomes a three-pass process.

### Pass 1: row construction

Pass 1 remains the only pass that reads `_tilde` and source-facing punctuation
material.

Pass 1 obligations:

- build the original and accentuated phone-row streams
- fill all structural row fields already owned by the row contract
- classify pause rows by silence subtype
- resolve realization codes and boundary semantics
- leave `duration` unresolved
- leave `intonation` unresolved

Pass 1 therefore fills everything except duration and intonation.

### Pass 2: duration realization

Pass 2 keeps the current duration role.

Pass 2 obligations:

- traverse the prebuilt row streams only
- fill `duration` in place
- not rewrite structural fields or final intonation values

### Pass 3: intonation realization

Pass 3 is new.

Pass 3 obligations:

- traverse the finalized duration-bearing row streams only
- fill `intonation` in place
- treat pause subtype as the cause-side intonation signal for the preceding
  phrase
- in the current implementation scope, assign that cause to the last syllable
  before each pause
- assign ordinary stress intonation where no pause-final override applies
- not consult `_tilde`, raw source text, or direct punctuation reparsing after
  Pass 1

Discipline constraints:

- Pass 2 and Pass 3 must both derive their decisions from the row stream plus
  effective config, not from upstream text artifacts.
- Final serialized `_phone.txt` and `_ophone.txt` artifacts are the post-Pass-3
  finalized rows.
- Historical or debug exposure of earlier pass snapshots is outside the active
  downstream contract unless a later record formalizes it.

## 2. Intonation remains relative to `f0`

- `phonetize.process.intonation.f0` remains the only absolute pitch anchor.
- Every intonation token is interpreted relative to `f0`.
- No intonation token stores an absolute Hertz value.
- The reference is always `f0`.

## 3. Canonical row token format

Every emitted phone row shall carry one canonical three-character intonation
code in the format `Z9Z`:

- first character = type/direction family
- second character = semitone size as one digit `0-9`
- third character = shape code

Canonical token families:

| Family | Meaning | Canonical shape | Notes |
| --- | --- | --- | --- |
| `H` | High, constant target above `f0` | `C` | constant family |
| `L` | Low, constant target below `f0` | `C` | constant family |
| `M` | Medium, neutral reference at `f0` | `C` | `M0C` is the neutral token |
| `R` | Rising | `L` | linear rise |
| `F` | Falling | `L` | linear fall |
| `P` | Peak: rise, plateau, fall | `E` | plateau is 33.3% of duration |
| `V` | Valley: fall, plateau, rise | `E` | plateau is 33.3% of duration |

Canonical-shape constraints:

- `H`, `L`, and `M` always use shape `C`.
- `R` and `F` always use shape `L`.
- `P` and `V` always use shape `E`.
- No other shapes are supported.
- `M` is only valid as `M0C` in the active contract.

Representative canonical row tokens:

- `H2C`
- `L2C`
- `M0C`
- `R1L`
- `F1L`
- `P2E`
- `V2E`

Interpretation notes:

- `H2C` means two semitones above `f0` with the high/constant family.
- `F1L` means one semitone downward relative to `f0` with a linear fall.
- `P2E` means rise to +2 semitones, hold a short equal plateau, then return.
- `V2E` means fall below reference, hold a short equal plateau, then return.

## 4. Config surface and normalization

The user-facing config surface under `phonetize.process.intonation` shall be:

```yaml
phonetize:
  process:
    intonation:
      f0: 120
      stress: H2
      question: H3
      statement: L2
      exclamation: H4
      continuation: H1
```

Normalization rule:

- The config surface may use the compact two-character preset form shown above.
- That compact form is normalized to the canonical row token by adding the only
  legal shape for the chosen family.
- Therefore:
  - `H2 -> H2C`
  - `L2 -> L2C`
  - `M0 -> M0C`
  - `R1 -> R1L`
  - `F1 -> F1L`
  - `P2 -> P2E`
  - `V2 -> V2E`

Config constraints:

- Remove `stress_rise`.
- Remove `question_final_rise`.
- Remove `statement_final_fall`.
- Remove `exclamation_rise`.
- Remove `continuation_rise`.
- Add `stress`.
- Add `question`.
- Add `statement`.
- Add `exclamation`.
- Add `continuation`.

The new config keys govern syllable-level intonation presets, not direct Hz
output values.

## 5. Syllable-scoped intonation interpretation

The emitted row token shall be syllable-scoped rather than one-point scoped.

Normative consequences:

- A syllable assigned a non-neutral intonation preset carries that preset
  through the whole syllable duration rather than applying it to only one row
  and immediately resetting neighboring rows.
- When a last syllable before a pause is governed by a pause-final contour, the
  rows of that whole syllable inherit the same non-neutral intonation token.
- When no pause-governed override applies, the active stressed syllable in the
  accentuated stream receives the configured `stress` preset.
- The original stream remains neutral unless a later accepted record says
  otherwise.

This directly rules out a one-row spike model such as:

- `m M0C`
- `a M0C`
- `n H2C`
- `a M0C`
- `l M0C`

for a final-syllable rising target.

Instead the governed final syllable remains under the same preset across the
syllable rows.

## 6. Silence subtype classification

Pause rows remain `category='S'`, but `type` shall no longer be the generic
`S` for every silence row.

Pause-row subtype inventory:

| Category | Type | Meaning | Expected length |
| --- | --- | --- | --- |
| `S` | `Q` | question pause | `L` |
| `S` | `S` | statement pause | `L` |
| `S` | `E` | exclamation pause | `L` |
| `S` | `C` | continuation pause | `S` |
| `S` | `I` | internal no-intonation pause | `S` by default, may be `L` if created by long-only unsupported class |

Subtype semantics:

- `Q` applies when the punctuation suite contains a question mark.
- `E` applies when the punctuation suite contains an exclamation mark.
- `S` applies when the punctuation suite contains a period or a line break with
  statement force.
- `C` applies to continuation punctuation such as comma, semicolon, colon, and
  hesitation ellipsis.
- `I` applies when a pause is created for separation or sanitization but should
  not impose clause-final intonation.

## 7. Punctuation grouping and precedence

If several punctuation marks are grouped into one consumed punctuation suite,
classification precedence is:

1. question
2. exclamation
3. statement
4. continuation
5. internal

This precedence applies after the phonetizer has grouped the punctuation suite
into one pause-producing chunk.

Examples:

- `?!` -> `Q`
- `!?` -> `Q`
- `!!.` -> `E`
- `...:` -> `C`
- bare newline -> `S`

## 8. Pause-creating punctuation mapping

The phonetizer-facing punctuation mapping shall reduce the active repository
punctuation surface to the following pause classes.

Primary pause-producing cues:

| Input material | Silence subtype | Length class | Intonation effect |
| --- | --- | --- | --- |
| `.` | `S` | `L` | statement |
| `\n` | `S` | `L` | statement |
| `?` | `Q` | `L` | question |
| `!` | `E` | `L` | exclamation |
| `,` | `C` | `S` | continuation |
| `;` | `C` | `S` | continuation |
| `:` | `C` | `S` | continuation |
| `...` | `C` | `S` | continuation |
| `…` | `C` | `S` | continuation |
| `—` | `C` | `S` | continuation |
| `–` | `C` | `S` | continuation |

Normalization and sanitization rules:

- In modern prose, a bare line break without a period is treated as statement
  force for phonetizer pause typing.
- If several punctuation marks occur together, they are one grouped suite and
  are classified by the precedence above.
- Symbols that cannot be produced directly by the phonetizer and cannot be
  replaced by an active phonetic equivalent shall not trigger a lexical
  expansion in this CR.
- Instead, those symbols shall be handled as pause material with subtype `I`
  unless a higher-priority cue in the same suite upgrades the group to `Q`,
  `E`, `S`, or `C`.

Repository-facing sanitization guidance:

- quotation marks and similar wrappers may create separation but no intonation
  on their own, therefore they map to subtype `I`
- bracket-like wrappers may still produce separation but do not themselves
  impose question, statement, exclamation, or continuation intonation unless a
  higher-priority punctuation cue is present in the same suite
- symbols such as `&`, `+`, `#`, `*`, `/`, `\`, `|`, and currency-like
  punctuation must not be automatically expanded to modern-language words under
  this CR; if they survive to the phonetizer as punctuation material, they map
  to subtype `I` unless grouped with a higher-priority cue

## 9. Last-syllable override before a pause

The configured clause-final intonation presets apply to the last syllable before
an emitted pause row according to the silence subtype of that pause row.

Architectural clarification:

- the pause row is the cause-side signal
- the last-syllable contour is the current consequence strategy
- later accepted records may spread the same cause-side signal more broadly
  across the phrase without changing pause typing itself

Mapping:

- pause type `Q` -> apply `phonetize.process.intonation.question`
- pause type `S` -> apply `phonetize.process.intonation.statement`
- pause type `E` -> apply `phonetize.process.intonation.exclamation`
- pause type `C` -> apply `phonetize.process.intonation.continuation`
- pause type `I` -> apply no clause-final override

Precedence between stress and pause-final contour:

- the pause-governed contour overrides the ordinary stress preset on the final
  syllable before that pause
- syllables not governed by a pause-final override use the ordinary stress or
  neutral behavior

## 10. Phone-row schema expands to eleven fields

The canonical phone-row schema becomes:

1. `label` (3 char)
2. `category` (1 char)
3. `type` (1 char)
4. `length` (1 char)
5. `position` (1 char)
6. `boundary` (1 char)
7. `accent` (1 char)
8. `realization` (2 char)
9. `duration` (4 digit)
10. `intonation` (3 char)
11. `text` (varying char)

Schema constraints:

- `duration` remains four digits.
- The placeholder duration remains `0000`.
- The new `intonation` field carries canonical three-character tokens such as
  `M0C`, `H2C`, `L2C`, `R1L`, `F1L`, `P2E`, or `V2E`.
- The active finalized row stream uses resolved canonical row tokens such as
  `M0C`, `H2C`, `L2C`, `R1L`, `F1L`, `P2E`, or `V2E`.
- Pass 1 may keep the field unresolved internally because final row intonation
  belongs to Pass 3.
- Pause rows also carry an `intonation` token. For subtype `I`, the default is
  `M0C`. For `Q`, `S`, `E`, and `C`, the row token must align with the pause's
  governing preset or a neutralized pause-specific token derived from it; the
  implementation choice must be documented consistently across code and docs.

Serialization update:

- The serialized head gains the new `intonation` field before `:text`.
- Parsers, serializers, docs, tests, and downstream consumers must all treat
  the phone-row line as eleven fixed fields plus source text.

## 11. MBROLA `.pho` derivation from finalized phone rows

MBROLA output must be derived entirely from the finalized phone-row stream plus
`phonetize.process.intonation.f0`.

Source discipline:

- `.pho` export must not re-read `_tilde`, raw input text, or punctuation text
  once the finalized phone-row stream exists.
- `.pho` export must not recompute stress or pause type from source text.
- `.pho` export must consume only finalized phone rows, row durations, row
  realizations, row intonation, and `f0`.

Line format:

```text
phoneme_or_silence duration_in_ms pitch_target_1 [pitch_target_2 ... pitch_target_n]
```

Normative constraints:

- `phoneme_or_silence` is derived from the finalized phone row.
- `duration_in_ms` is the finalized four-digit row duration merged as allowed by
  the active exporter rules.
- every emitted pitch target is derived from the row intonation token and `f0`
- pitch targets are emitted in Hertz
- non-silence rows may emit more than two pitch targets when the selected
  intonation family requires a non-linear contour such as peak or valley

MBROLA timing rule:

- when one phoneme line of duration `D` emits `N` pitch targets, MBROLA places
  them at equal positions `0`, `D / (N - 1)`, `2D / (N - 1)`, ... , `D`
- MBROLA interpolates linearly between adjacent pitch targets
- the exporter must therefore choose pitch-target counts and repeated target
  values so the resulting evenly spaced linear interpolation respects the row's
  token family semantics as closely as the MBROLA model allows

Family-to-contour guidance:

- constant families (`H`, `L`, `M`) emit a constant contour at the resolved
  target level
- linear families (`R`, `F`) emit a monotonic start-to-end contour
- equal families (`P`, `V`) emit a rise-or-fall, plateau, and return contour
  using evenly spaced repeated targets consistent with MBROLA's equal-spacing
  model

Semitone-to-Hz conversion:

- positive semitone offsets are computed from `f0` by
  `target_hz = f0 * 2^(semitones / 12)`
- negative semitone offsets are computed from `f0` by the same formula using a
  negative semitone value

This means MBROLA output is no longer specified as one emitted frequency value
per line. The active contract is a variable-length pitch-target tail derived
from finalized phone rows.

## 12. Supersession note

This CR explicitly supersedes the older intonation-config portion of
[CR-045](045-move-mbrola-pho-output-to-phonetizer.md) where that record approves
`stress_rise`, `question_final_rise`, `statement_final_fall`,
`exclamation_rise`, and `continuation_rise` as the active long-term intonation
surface.

The stage-ownership decision from CR-045 remains active:

- phonetizer still owns `.pho` export
- `phonetize.process.intonation` remains the correct process subtree
- what changes here is the symbolic token contract, row carriage,
  punctuation-driven silence typing, and the `.pho` pitch-tail contract

This CR also narrows [CR-036](036-define-phonetizer-phoneme-framework.md) by
replacing the prior ten-field row schema with the eleven-field schema above,
and narrows [CR-047](047-close-phonetizer-pause-and-reconstruction-gaps.md) by
making pause subtype explicit rather than leaving all pause rows under one
silence type.

This CR explicitly narrows the earlier two-phase architecture described by
[ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md),
[REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md),
[CR-039](039-build-phonetizer-phase-1-structure-only-dual-phone-outputs.md),
and [CR-040](040-realize-phonetizer-phase-2-durations-from-prebuilt-rows.md)
by extending the phonetizer from two passes to three ordered passes:
structure, duration, and intonation.

The active architecture and whole-intonation requirement are now formalized by
[ADR-045](../adr/045-three-pass-phonetizer-intonation-and-row-derived-mbrola.md)
and [REQ-032](../req/032-phonetizer-intonation-and-three-pass-finalization.md).

The row-traversal discipline from those records remains active. What changes is
the pass count and the ownership of final row-level intonation realization.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/config/default.yaml`
- phonetizer config verification and help generation surfaces
- phone-row serializer and parser
- `.pho` export logic that derives pitch-target lists from row-level intonation
  and `f0`
- `docs/internal/adr/045-three-pass-phonetizer-intonation-and-row-derived-mbrola.md`
- `docs/internal/req/032-phonetizer-intonation-and-three-pass-finalization.md`
- phonetizer docs and phone-row guide
- integration and unit tests covering pause typing and row serialization

Design direction:

- Normalize config presets such as `H2` to canonical row tokens such as `H2C`.
- Add the `intonation` field to all in-memory and serialized phone rows.
- Keep Pass 1 responsible for row building and pause typing while leaving both
  duration and final intonation unresolved.
- Keep Pass 2 responsible for duration only.
- Add Pass 3 as an in-place intonation traversal over duration-bearing rows.
- Classify pause rows by subtype at pause-row creation time, using punctuation
  grouping and precedence rules.
- Apply the governing pause-final preset to the last syllable before that pause.
- Keep spaces as non-pause separators.
- Keep duration four digits and preserve current long-pause ranges.
- Ensure `.pho` emission reads finalized row-level intonation rather than
  reconstructing pitch only from `accent` plus one stress-rise scalar.
- Emit MBROLA pitch-target tails according to MBROLA's equal-spacing and
  straight-line interpolation model.

Compatibility note:

- This is a deliberate row-contract break for `_phone.txt` and `_ophone.txt`.
- Downstream readers must be updated together.
- Because duration remains four digits, the schema change is additive in field
  count but not a numeric-range contraction.

---

# Files Likely Affected

`docs/internal/cr/045-move-mbrola-pho-output-to-phonetizer.md`
`docs/internal/cr/036-define-phonetizer-phoneme-framework.md`
`docs/internal/cr/047-close-phonetizer-pause-and-reconstruction-gaps.md`
`docs/internal/req/029-stage-config-run-process-separation-and-common-outdir-removal.md`
`docs/internal/req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md`
`src/akkapros/lib/phonetize.py`
`src/akkapros/config/default.yaml`
`docs/akkapros/phonetizer.md`
`docs/akkapros/phonetizer-phone-file-guide.md`
`docs/akkapros/configuration.md`
`tests/test_phonetize_lib.py`
`tests/test_integration.py`

---

# Acceptance Criteria

- [ ] The approved phonetizer config surface no longer exposes `stress_rise`,
      `question_final_rise`, `statement_final_fall`, `exclamation_rise`, or
      `continuation_rise`.
- [ ] The active phonetizer runtime is specified as three ordered passes rather
  than two.
- [ ] Phase 1 is specified as filling everything except duration and final
  intonation.
- [ ] Phase 2 is specified as filling duration only.
- [ ] Phase 3 is specified as filling intonation only.
- [ ] The approved phonetizer config surface exposes `f0`, `stress`,
      `question`, `statement`, `exclamation`, and `continuation` under
      `phonetize.process.intonation`.
- [ ] Config values `H2`, `L2`, `M0`, `R1`, `F1`, `P2`, and `V2` normalize to
      canonical row tokens `H2C`, `L2C`, `M0C`, `R1L`, `F1L`, `P2E`, and `V2E`.
- [ ] The phone-row schema is explicitly updated from ten fields to eleven
      fields by adding `intonation` before `text`.
- [ ] The `duration` field remains four digits, and the placeholder remains
      `0000`.
- [ ] Neutral non-overridden rows default to `M0C`.
- [ ] The phonetizer still treats spaces between words as connected speech and
      does not emit pause rows for spaces alone.
- [ ] The phonetizer emits pause rows for punctuation and line breaks.
- [ ] Pause rows are typed as `Q`, `S`, `E`, `C`, or `I` rather than the single
      generic silence type.
- [ ] Question-mark-bearing punctuation suites classify as `Q`.
- [ ] Exclamation-mark-bearing punctuation suites classify as `E` unless a
      question mark in the same suite upgrades the whole group to `Q`.
- [ ] Period-bearing suites and bare line breaks classify as `S` unless a
      higher-priority cue in the same suite upgrades the group.
- [ ] Comma, semicolon, colon, ellipsis, and dash continuation cues classify as
      `C` unless a higher-priority cue in the same suite upgrades the group.
- [ ] Unsupported or non-lexically-expanded punctuation material maps to
      no-intonation subtype `I` unless grouped with a higher-priority cue.
- [ ] The last syllable before a pause receives the pause-governed contour for
      `Q`, `S`, `E`, or `C`, while `I` applies no clause-final override.
- [ ] The `.pho` pitch path is documented and tested as consuming row-level
  intonation tokens relative to `f0`.
- [ ] The active `.pho` contract is documented as a variable-length pitch-tail
  format derived entirely from finalized phone rows plus `f0`, not as a
  one-frequency three-field line.
- [ ] The MBROLA equal-spacing rule for emitted pitch targets is documented in
  the active contract.
- [ ] Public documentation and the phone-row reading guide are updated to show
      the new config surface, row schema, and silence subtype meanings.

---

# Risks / Edge Cases

Possible issues:

- The compact config form `H2` can be misread as the full canonical row token;
  docs and validators must state that the stored row token is normalized to
  `H2C`.
- The shift from two passes to three is a direct architectural narrowing of
  older accepted records and must therefore be cross-linked explicitly to avoid
  implementation drift.
- Existing phone-row consumers will break until they are updated for the extra
  field.
- Punctuation suites containing both no-intonation wrappers and clause-final
  punctuation need explicit tests so precedence remains stable.
- Bare newline semantics in poetry and wrapped prose must be pinned clearly to
  avoid printer/phonetizer drift.
- The implementation must choose and document whether pause rows themselves
  carry the same clause token as the preceding syllable or a neutralized pause
  token derived from the same preset.
- MBROLA equal-spacing means not every desired contour can be placed at an
  arbitrary internal time point, so the exporter mapping must be designed for
  the actual MBROLA interpolation model rather than for abstract free-timing
  contours.

---

# Testing Strategy

Unit tests:

- intonation-token parser and normalizer
- pass-order tests that prove Phase 3 consumes row data rather than upstream
  text
- config verification rejects illegal family/shape combinations
- phone-row serialization and parsing with the added `intonation` field
- pause-row classification for `Q`, `S`, `E`, `C`, and `I`
- precedence tests for grouped suites such as `?!`, `!!.`, `...`, and bare
  newline
- verification that spaces do not create pause rows
- `.pho` pitch-target expansion tests for constant, linear, and equal families

Integration tests:

- phonetizer output reflects eleven-field rows
- final-syllable rows before typed pauses carry the expected normalized
  intonation token
- `.pho` export consumes finalized row-level intonation and `f0`
- `.pho` output shape reflects MBROLA's variable-length evenly spaced
  pitch-target contract

Manual verification:

- inspect representative `_phone.txt`, `_ophone.txt`, and `.pho` artifacts for
  one statement, one question, one exclamation, one continuation, and one
  internal-sanitization case

---

# Rollback Plan

Revert to the previous scalar intonation config and ten-field row contract in
one coordinated change if downstream adoption proves incomplete.

Because this is a schema change, rollback must include:

- config docs and defaults
- parser/serializer contract
- phonetizer `.pho` intonation mapping
- downstream row readers
- pass-order documentation if the repository returns from three passes to two

---

# Related Issues

- [CR-045](045-move-mbrola-pho-output-to-phonetizer.md)
- [CR-036](036-define-phonetizer-phoneme-framework.md)
- [CR-047](047-close-phonetizer-pause-and-reconstruction-gaps.md)
- [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md)
- [REQ-031](../req/031-phonetizer-phase-2-syllable-scoped-duration-realization.md)
- [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md)
- [ADR-040](../adr/040-two-phase-phonetizer-architecture-and-dual-phone-outputs.md)

---

# Tasks

## Implementation

- [ ] Replace the scalar intonation config keys with the symbolic preset keys
- [ ] Add row-level intonation storage and normalization
- [ ] Add the third intonation pass after duration realization
- [ ] Add typed silence rows and punctuation-precedence handling
- [ ] Update `.pho` pitch emission to read finalized row-level intonation and
  emit MBROLA pitch-target tails

## Tests

- [ ] Add unit coverage for token normalization and validation
- [ ] Add pause-typing tests
- [ ] Add serializer/parser regression tests for the 11-field row format
- [ ] Add integration coverage for final-syllable contour assignment

## Documentation

- [ ] Update phonetizer docs and config docs
- [ ] Update the phone-row reading guide
- [ ] Add examples for statement, question, exclamation, continuation, and
      internal pauses

## Review

- [ ] Review the row-schema break against downstream consumers
- [ ] Verify acceptance criteria

---

# Implementation Blockers

Leave empty unless implementation later discovers a spec weakness that prevents
safe execution.

---

# Notes

Evidence gathered for this CR:

- `src/akkapros/lib/phonetize.py` already proves that spaces do not emit pause
  rows, while punctuation and line breaks do.
- `src/akkapros/lib/phonetize.py` already uses four-digit duration placeholders
  and long-pause ranges above three digits.
- The current ten-field row contract and scalar intonation config are active and
  therefore must be superseded explicitly rather than changed implicitly.
- The current repository also still documents a two-pass phonetizer and a
  one-frequency `.pho` line, so this CR supersedes both of those narrower
  assumptions explicitly.

Implementation is deferred.
