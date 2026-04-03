---
cr_id: CR-029
status: Draft
priority: High
impact: Mutative
created: 2026-04-01
updated: 2026-04-03
implements: 'ADR-035, REQ-021'
---

# Change Request: Introduce Separate Hiatus Marker for Word-Initial Vowel Hiatus

# Summary

Revise CR-029 so that the internal symbol used for word-initial vowel hiatus is
no longer folded into `DIPH_SEPARATOR`. Instead, introduce a separate symbol
`HIATUS_MARKER = '˙'` while keeping `DIPH_SEPARATOR = '¨'` unchanged in name,
meaning, and existing diphthong-transition behavior.

The change remains internal to the pipeline contract. Intermediate stage
representations may change where vowel-initial words receive the new marker,
but printer outputs and metricalc outputs remain unchanged.

---

# Motivation

- Preserve the existing semantics of `DIPH_SEPARATOR`
- Keep diphthong-transition handling separate from word-initial hiatus
- Make internal zero-onset handling explicit without overloading one symbol
- Preserve current visible outputs from printer and metricalc

The earlier draft of CR-029 broadened `DIPH_SEPARATOR` into a general
transition pseudo-consonant for vowel-initial zero onset. That is no longer the
desired direction. The revised change keeps the prior diphthong-transition
contract intact and introduces a distinct marker for the separate internal role.

This is intentionally a narrow revision. The goal is not to redesign
accentuation, mora handling, or output formats. The goal is to preserve the
existing `¨` semantics and add `˙` only where a dedicated internal hiatus
marker is needed.

The broader implementation attempt associated with the earlier draft was
discarded before this specification rewrite. This CR therefore assumes no
residual code changes remain from the rolled-back version.

---

# Scope

## Included

- Keep `DIPH_SEPARATOR = '¨'` unchanged in name and function.
- Introduce `HIATUS_MARKER = '˙'` as a distinct internal pseudo-consonant for
  word-initial vowel hiatus.
- Add `HIATUS_MARKER` to `AKKADIAN_CONSONANTS` in the internally sensitive
  normalization-hooks block.
- Keep `·` as the only syllable-boundary marker.
- Represent vowel-initial words with `HIATUS_MARKER` in internal stage output,
  for example `ana -> ˙a·na¦`.
- Preserve existing diphthong-transition behavior using `DIPH_SEPARATOR`, for
  example `tiam -> ti¨am -> ti·¨am`.
- Update downstream internal consumers so they can distinguish `¨` from `˙`.
- Keep printer outputs unchanged.
- Keep metricalc outputs unchanged.
- Update internal documentation to reflect the separated symbol roles.

## Not Included

- Renaming `DIPH_SEPARATOR`.
- Changing the semantics of `DIPH_SEPARATOR`.
- Changing visible printer glyphs or output formatting.
- Changing visible metricalc output.
- Changing prosody-selection rules, merge policy, or mora-mode logic.
- Broadening this CR beyond the word-initial vowel-hiatus use case without a
  separate decision.
- Cleaning up residual code changes from the earlier draft, because those
  changes were already discarded before this rewrite.

---

# Current Behavior

Current behavior is split across stages:

1. `DIPH_SEPARATOR` (`¨`) is already used internally for diphthong or
   split-vowel transition handling.
2. Word-initial vowel onset behavior is not represented with a dedicated
   internal symbol distinct from `DIPH_SEPARATOR`.
3. Some downstream behavior, especially printer-side IPA handling, relies on
   stage-local inference rather than on one explicit internal marker dedicated
   to word-initial hiatus.
4. The rolled-back CR-029 draft attempted to solve this by redefining
   `DIPH_SEPARATOR` itself.

Problems with that draft direction:

- it collapses two distinct internal meanings into one symbol
- it changes the documented semantics of `DIPH_SEPARATOR`
- it makes the internal representation less explicit rather than more explicit
- it creates unnecessary conceptual drift in documentation and tests

---

# Proposed Change

Adopt the following internal contract.

- `DIPH_SEPARATOR = '¨'` remains unchanged.
- `HIATUS_MARKER = '˙'` is added as a new internal symbol.
- `¨` continues to mean diphthong transition or split-vowel onset behavior.
- `˙` means word-initial vowel hiatus or zero-onset placeholder.
- `·` remains the only syllable-boundary marker.

The constants block shall be specified as follows:

```python
# ---- Internally sensitive normalization hooks -----------------------------
# Do not inline these mutations back into the base sets. Some downstream code
# relies on the distinction between canonical inventory and internal parsing
# hooks, even when the effective runtime set includes the same characters.
# Treat diphthongs as consonant clusters for syllabification.
AKKADIAN_CONSONANTS.add(DIPH_SEPARATOR)
AKKADIAN_CONSONANTS.add(HIATUS_MARKER)
```

Positional semantics:

- In a diphthong or split-vowel case, `V·¨V` means `·` is the syllable boundary
  and `¨` is the onset placeholder of the following syllable.
- In a word-initial hiatus case, `˙V...` means the syllable begins with an
  explicit internal zero-onset placeholder.
- A leading `˙` is not a syllable boundary and must not create an empty
  syllable in counters, validators, or metrics helpers.
- If prosody last resort targets a syllable beginning with `˙`, the tilde
  follows the marker: `˙V -> ˙~V`.

Examples:

- `ana -> ˙a·na¦`
- `tiam -> ti¨am -> ti·¨am`
- `˙a -> ˙~a` in last-resort accentuation

Output invariants:

- printer outputs remain unchanged
- metricalc outputs remain unchanged

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/constants.py`
- `src/akkapros/lib/syllabify.py`
- `src/akkapros/lib/prosody.py`
- `src/akkapros/lib/print.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/lib/frontmatter.py`
- `src/akkapros/lib/diphthongs.py`
- generated diphthong helper code and related tests

Design requirements:

- The new symbol split is semantic, not cosmetic.
- `DIPH_SEPARATOR` must remain diphthong-specific.
- `HIATUS_MARKER` must be used for word-initial vowel hiatus.
- Neither `¨` nor `˙` may be documented as a syllable boundary.
- Internal consumers must remain able to distinguish lexical `ʾ`,
  `DIPH_SEPARATOR`, and `HIATUS_MARKER`.
- Printer must consume the explicit internal marker semantics without changing
  visible outputs.
- metricalc must consume the explicit internal marker semantics without
  changing visible outputs.
- Prosody last-resort serialization for word-initial hiatus must become `˙~V`
  rather than `~V`.

Known sensitive areas:

- `syllabify.py` preprocessing and serialization
- `prosody.py` last-resort accentuation placement
- `print.py` zero-onset handling for IPA while preserving unchanged outputs
- `metrics.py` and related helpers that must not misread leading `˙` as a
  free-standing separator
- `frontmatter.py` syllable-count helpers

---

# Files Likely Affected

`src/akkapros/lib/constants.py`
`src/akkapros/lib/syllabify.py`
`src/akkapros/lib/prosody.py`
`src/akkapros/lib/print.py`
`src/akkapros/lib/metrics.py`
`src/akkapros/lib/frontmatter.py`
`src/akkapros/lib/diphthongs.py`
`tests/test_metrics_stats.py`
`tests/test_gencode_diphthongs.py`
`tests/test_format_validation.py`
`tests/test_integration.py`
`tests/test_prosody_mora_mode.py`
`tests/test_selftests_cli.py`
`tests/test_selftests_lib.py`
`docs/akkapros/syllabifier.md`
`docs/akkapros/diphthong-processing.md`
`docs/akkapros/prosmaker.md`
`docs/akkapros/printer.md`
`docs/akkapros/metrics-computation.md`
`README.md`

---

# Acceptance Criteria

- [ ] `DIPH_SEPARATOR = '¨'` remains unchanged in name and function.
- [ ] `HIATUS_MARKER = '˙'` is introduced as a separate constant.
- [ ] The internally sensitive normalization-hooks block contains both
      `AKKADIAN_CONSONANTS.add(DIPH_SEPARATOR)` and
      `AKKADIAN_CONSONANTS.add(HIATUS_MARKER)`.
- [ ] Given a vowel-initial word such as `ana`, when syllabified, then the
      internal representation begins with `HIATUS_MARKER`, for example
      `˙a·na¦`.
- [ ] Given a diphthong-transition case such as `tiam`, when internally split,
      then the representation remains `ti¨am`, and when syllabified it remains
      `ti·¨am`.
- [ ] Given `*_syl.txt` or `*_tilde.txt` contains leading `˙`, when syllable
      counts are computed, then `˙` is treated as onset structure and no empty
      syllable is created.
- [ ] Given prosody last resort targets a syllable beginning with `˙`, when the
      syllable is accentuated, then the result is `˙~V`, not `~V`.
- [ ] Given printer consumes updated internal input, when final output is
      generated, then visible printer artifacts remain unchanged.
- [ ] Given metricalc consumes updated internal input, when final output is
      generated, then visible metricalc artifacts remain unchanged.
- [ ] Internal documentation distinguishes `DIPH_SEPARATOR` from
      `HIATUS_MARKER` clearly and consistently.

---

# Risks / Edge Cases

Possible issues:

- accidental conflation of `DIPH_SEPARATOR` and `HIATUS_MARKER`
- visible-output regressions if `HIATUS_MARKER` is not fully suppressed or
  correctly interpreted downstream
- false empty syllables if leading `˙` is treated as a separator rather than as
  onset structure
- partial doc updates that still describe `¨` as carrying the new role

---

# Testing Strategy

Unit tests:

- constants coverage for distinct `DIPH_SEPARATOR` and `HIATUS_MARKER`
- syllabifier test for `ana -> ˙a·na¦`
- syllabifier regression test preserving `tiam -> ti¨am -> ti·¨am`
- prosody test for `˙a -> ˙~a`
- front matter tests proving leading `˙` does not create a false syllable
- metrics tests proving leading `˙` is consumed as onset structure
- printer tests proving unchanged visible outputs
- metricalc regression tests proving unchanged visible outputs

Integration tests:

- update only affected intermediate fixtures where `˙` now appears
- confirm final printer artifacts remain unchanged
- confirm final metricalc artifacts remain unchanged

Manual review:

- verify all internal docs describe `¨` and `˙` with separate meanings

---

# Rollback Plan

If the change proves too disruptive, revert the introduction of
`HIATUS_MARKER`, restore the prior draft state of the internal docs, and remove
the new symbol from the normalization-hooks specification. No output-format
migration is required because printer and metricalc outputs remain unchanged.

---

# Related Issues

- [ADR-035](../adr/035-separate-hiatus-marker-and-word-initial-zero-onset-contract.md)
- [REQ-021](../req/021-separate-hiatus-marker-for-word-initial-vowel-hiatus.md)

---

# Tasks

## Implementation

- [ ] Add `HIATUS_MARKER` to shared constants
- [ ] Update syllabifier serialization for word-initial vowel hiatus
- [ ] Update prosody serialization for `˙~V`
- [ ] Update downstream consumers to distinguish `¨` from `˙`
- [ ] Update internal and user-facing docs

## Tests

- [ ] Add unit coverage for the new marker
- [ ] Update only the intended intermediate fixtures
- [ ] Verify printer outputs remain unchanged
- [ ] Verify metricalc outputs remain unchanged
