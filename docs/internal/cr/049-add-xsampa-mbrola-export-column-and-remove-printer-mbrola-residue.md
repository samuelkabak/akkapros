---
cr_id: CR-049
status: Done
priority: High
impact: Mutative
created: 2026-04-11
updated: 2026-04-11
implements: 'ADR-040, REQ-025, REQ-029'
---

# Change Request: Add X-SAMPA MBROLA Export Column and Remove Printer MBROLA Residue

# Summary

Change the active phonetizer-owned `.pho` contract so MBROLA export emits
conventional X-SAMPA-like symbols derived from the internal realization-code
inventory, instead of emitting the internal realization codes themselves.

Under this change, `REALIZATION_CODE_ROWS` becomes the canonical source of truth
for both internal realization codes and their MBROLA/X-SAMPA export forms. The
internal realization code remains the repository’s reference inventory for phone
rows and future TTS backends, but phonetizer-owned MBROLA `.pho` output shall
emit the dedicated X-SAMPA mapping column. The CR also removes residual printer
MBROLA support from `print.py` and `printer.py`, and explicitly keeps
`phoneprep.py` unchanged as a separate MBROLATOR-sidecar workflow.

---

# Motivation

The current repository state contains an architectural split that is now too
visible to leave implicit.

- The active phonetizer-owned `.pho` exporter in `src/akkapros/lib/phonetize.py`
  emits internal realization codes such as `ET`, `HE`, `AA`, `AO`, `SP`, and
  `ZP`.
- MBROLA historically expects arbitrary tokens at runtime, but conventional
  practice and surrounding tooling are X-SAMPA-like rather than repository-
  specific two-letter realization mnemonics.
- `src/akkapros/lib/print.py` still contains an older MBROLA/X-SAMPA-like
  symbol renderer that is no longer part of the active printer contract.
- `src/akkapros/lib/phoneprep.py` contains a separate MBROLA/X-SAMPA-like
  mapping for voice-building sidecars and MBROLATOR workflows.

The repository therefore needs one explicit contract change that separates the
internal realization inventory from the emitted MBROLA/X-SAMPA export surface,
without collapsing them into one thing. The internal code remains canonical for
`_phone.txt`, `_ophone.txt`, runtime logic, and future backends. The MBROLA
backend becomes one downstream rendering of that internal inventory.

---

# Scope

## Included

- Add an explicit MBROLA/X-SAMPA export column or equivalent canonical field to
  the phonetizer realization-code inventory.
- Define the active phonetizer-owned `.pho` exporter in terms of that new
  realization-code-to-MBROLA mapping instead of direct emission of realization
  codes.
- Keep internal realization codes as the canonical row-level reference in
  `_phone.txt` and `_ophone.txt`.
- Define the normative MBROLA/X-SAMPA export mapping for every active
  realization code, including pause codes.
- Remove residual MBROLA rendering from `src/akkapros/lib/print.py` and any
  remaining printer-facing library surfaces.
- Remove residual printer MBROLA tests and printer MBROLA documentation.
- Update phonetizer docs and tests to reflect the new X-SAMPA-like `.pho`
  output.
- Keep `phoneprep.py` behavior and its sidecar mapping unchanged.
- Add explicit tests and docs that state phoneprep remains a separate
  MBROLATOR-sidecar workflow and is not rewritten to consume the phonetizer
  `.pho` mapping.

## Not Included

- Redesigning the internal realization-code inventory itself.
- Redesigning phonetizer timing, drift, or intonation behavior.
- Changing the structure or semantics of `_phone.txt` or `_ophone.txt`.
- Unifying phoneprep sidecars with phonetizer `.pho` output.
- Adding support for non-MBROLA TTS backends in this CR.

---

# Current Behavior

Repository state on 2026-04-11 shows the following active and residual
behavior.

- `src/akkapros/lib/phonetize.py` defines `REALIZATION_CODE_ROWS` with an
  internal `code` and IPA-like `ipa` value, then emits the internal code in
  `serialize_mbrola_rows()`.
- `src/akkapros/cli/phonetizer.py` writes `<prefix>_ombrola.pho` and
  `<prefix>_mbrola.pho` from that realization-code export.
- [CR-045](045-move-mbrola-pho-output-to-phonetizer.md) explicitly requires
  phonetizer-owned `.pho` export and explicitly requires non-silence rows to
  emit realization codes.
- `src/akkapros/lib/print.py` still contains `MBROLA_CONSONANT_MAP`,
  `MBROLA_VOWELS_DEFAULT`, `MBROLA_VOWELS_EMPHATIC`, `mode == 'mbrola'`, and
  MBROLA self-tests, even though printer CLI no longer exposes MBROLA as a
  supported output.
- `src/akkapros/lib/print.py` currently sets `mbrola_text = ''` in
  `process_file()`, so any residual library path that still tries to write a
  printer-owned MBROLA file produces an empty file.
- `src/akkapros/lib/phoneprep.py` contains a separate MBROLA/X-SAMPA-like
  symbol mapping used for recording scripts, diphone manifests, and MBROLATOR
  preparation sidecars.

This means the active `.pho` exporter, residual printer code, and phoneprep
sidecar workflow currently use three different MBROLA-adjacent representations.

---

# Proposed Change

Adopt the following contract.

## 1. Internal realization codes remain canonical

- Internal realization codes remain the canonical symbols stored in phone rows,
  including `_phone.txt`, `_ophone.txt`, and in-memory phonetizer processing.
- The MBROLA/X-SAMPA export is a derived rendering from those internal codes.
- Future TTS exporters may derive from the same internal realization inventory
  without changing the row contract.

## 2. Add a canonical MBROLA/X-SAMPA export field to the realization inventory

- `REALIZATION_CODE_ROWS` shall gain one explicit field for MBROLA/X-SAMPA
  export, or an equivalent canonical metadata field derived directly from the
  table.
- `REALIZATION_CODE_METADATA` shall expose that value so downstream export code
  does not need a second detached mapping dictionary.
- The committed contract shall be keyed by internal realization code, not by a
  mixed external dictionary over Akkadian letters and IPA glyphs.

Rationale:

- A scratch list mixing Akkadian source letters and IPA symbols is acceptable as
  design input, but the committed repository contract should not depend on a
  mixed-key mapping because the active runtime inventory is the realization-code
  table.
- The canonical stable key is the internal realization code row itself.

## 3. Normative MBROLA/X-SAMPA export mapping

The active mapping shall be:

| Internal code | IPA-like value | MBROLA/X-SAMPA export |
|---------------|----------------|-----------------------|
| `BE` | `b` | `b` |
| `DA` | `d` | `d` |
| `GI` | `ɡ` | `g` |
| `KA` | `k` | `k` |
| `PA` | `p` | `p` |
| `TU` | `tˤ` | `t.` |
| `QU` | `q` | `q` |
| `SU` | `sˤ` | `s.` |
| `SA` | `s` | `s` |
| `ZI` | `z` | `z` |
| `SI` | `ʃ` | `S` |
| `LA` | `l` | `l` |
| `MI` | `m` | `m` |
| `NA` | `n` | `n` |
| `RE` | `r` | `r` |
| `ET` | `ħ` | `X` |
| `HE` | `x` | `x` |
| `AI` | `ʕ` | `H` |
| `AL` | `ʔ` | `?` |
| `WA` | `w` | `w` |
| `YI` | `j` | `j` |
| `TA` | `t` | `t` |
| `AA` | `a` | `a` |
| `EE` | `e` | `e` |
| `II` | `i` | `i` |
| `UU` | `u` | `u` |
| `AO` | `ɑ` | `a.` |
| `EO` | `ɛ` | `e.` |
| `IO` | `ɨ` | `i.` |
| `UO` | `ʊ` | `u.` |
| `SP` | `|` | `_` |
| `ZP` | `‖` | `_` |

Clarifications:

- Silence is not a separate phoneme row family outside the realization table.
  Both pause realizations `SP` and `ZP` export as `_`.
- Long-vowel quantity remains encoded by duration, not by duplicating the symbol
  in `.pho` output. Therefore no extra long-vowel symbol entries are required in
  the mapping table.
- The user-provided inventory is materially complete once normalized to the
  active internal realization rows. What was missing as an explicit contract was:
  - `GI -> g` as the normalized output for the current IPA-like `ɡ` row
  - pause export for `SP` and `ZP`
  - an explicit statement that length remains in duration, not in symbol

## 4. Phonetizer `.pho` exporter behavior

- `serialize_mbrola_rows()` shall emit the MBROLA/X-SAMPA export value from the
  realization metadata, not the internal realization code.
- The exporter shall continue to emit three-column rows:

```text
mbrola_symbol duration_in_ms frequency_in_hz
```

- The exporter shall continue to merge contiguous rows when both the emitted
  MBROLA symbol and emitted frequency are identical.
- The exporter shall continue to use `_` for silence rows.

Representative examples:

- a row with realization `ET` emits `X`
- a row with realization `AL` emits `?`
- a row with realization `AO` emits `a.`
- pause rows with realization `SP` or `ZP` emit `_`

## 5. Remove MBROLA from print and printer

- `src/akkapros/lib/print.py` shall no longer expose MBROLA as a rendering mode.
- Residual MBROLA helpers, mappings, tests, and write paths shall be removed or
  explicitly retired from the active printer contract.
- `src/akkapros/cli/printer.py` shall remain MBROLA-free.
- Any frontmatter or text-format registry entries that exist only for
  printer-owned MBROLA text files shall be removed or explicitly rehomed if they
  no longer serve an active artifact.

## 6. Keep phoneprep unchanged

- `src/akkapros/lib/phoneprep.py` remains unchanged in behavior.
- Its MBROLA/X-SAMPA-like sidecar mapping remains a phoneprep-owned workflow for
  recording scripts, manifests, and MBROLATOR preparation.
- This CR does not require phoneprep to read, emit, or align itself with the
  phonetizer `.pho` symbol contract beyond documentation that the two surfaces
  are intentionally separate.

## 7. Supersession note

- This CR explicitly supersedes the part of
  [CR-045](045-move-mbrola-pho-output-to-phonetizer.md) that requires phonetizer
  `.pho` export to emit internal realization codes directly.
- The stage ownership decision in CR-045 remains active: MBROLA `.pho` files are
  still phonetizer-owned and not printer-owned.
- The changed active contract is only the emitted non-silence symbol surface:
  phonetizer now emits MBROLA/X-SAMPA values derived from internal realization
  codes rather than the internal codes themselves.

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/phonetize.py`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/lib/print.py`
- `src/akkapros/cli/printer.py`
- `src/akkapros/lib/frontmatter.py`
- `src/akkapros/lib/phoneprep.py`
- `docs/akkapros/phonetizer.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `docs/akkapros/printer.md`
- `docs/akkapros/mbrola-voice-prep.md`
- `tests/test_phonetize_lib.py`
- `tests/test_integration.py`

Implementation direction:

- Extend the realization inventory with one MBROLA/X-SAMPA export field.
- Update realization metadata accessors to expose that field directly.
- Rewrite phonetizer `.pho` serialization to emit the new field.
- Keep internal phone-row `realization` values unchanged.
- Remove printer-side MBROLA conversion code, stale self-tests, and stale empty
  write paths.
- Preserve phoneprep logic exactly, but clarify in docs that it is a separate
  MBROLATOR-sidecar mapping workflow.

Compatibility note:

- This is a mutative artifact change for `<prefix>_ombrola.pho` and
  `<prefix>_mbrola.pho`.
- It is also a mutative library-surface cleanup in `print.py` if callers still
  rely on residual MBROLA mode there.

---

# Files Likely Affected

`src/akkapros/lib/phonetize.py`
`src/akkapros/cli/phonetizer.py`
`src/akkapros/lib/print.py`
`src/akkapros/lib/frontmatter.py`
`docs/akkapros/phonetizer.md`
`docs/akkapros/phonetizer-phone-file-guide.md`
`docs/akkapros/printer.md`
`docs/akkapros/mbrola-voice-prep.md`
`tests/test_phonetize_lib.py`
`tests/test_integration.py`
`docs/internal/cr/index.md`

---

# Acceptance Criteria

- [ ] The realization inventory exposes one canonical MBROLA/X-SAMPA export value
      per internal realization code.
- [ ] Phonetizer-owned `.pho` export emits that MBROLA/X-SAMPA value instead of
      the internal realization code.
- [ ] Internal phone rows continue to store the internal realization code rather
      than the MBROLA/X-SAMPA export value.
- [ ] Both pause realizations `SP` and `ZP` export as `_`.
- [ ] Long-vowel quantity remains encoded by duration and is not represented by
      duplicated symbol strings in `.pho` export.
- [ ] The exported mapping includes normalized support for the current `GI` row
      as `g` even though the current descriptive IPA-like value is `ɡ`.
- [ ] Printer library code no longer exposes an active MBROLA rendering mode or
      a stale empty MBROLA file write path.
- [ ] Printer tests no longer assert MBROLA rendering behavior.
- [ ] Phonetizer tests assert representative `.pho` rows using MBROLA/X-SAMPA
      symbols instead of internal realization codes.
- [ ] Integration tests assert the new `.pho` symbol surface and keep
      `_phone.txt` / `_ophone.txt` realization codes unchanged.
- [ ] Docs for phonetizer explain that `.pho` emits MBROLA/X-SAMPA derived from
      internal realization codes.
- [ ] Docs for printer no longer describe MBROLA as a printer surface beyond any
      historical note needed for migration clarity.
- [ ] Docs for phoneprep explicitly state that phoneprep remains unchanged and
      that its sidecar mapping is separate from phonetizer `.pho` export.
- [ ] Release-facing docs note that `.pho` output symbols changed from internal
      realization codes to MBROLA/X-SAMPA values.

---

# Risks / Edge Cases

Possible issues:

- downstream users may currently parse `.pho` rows expecting realization codes
  rather than X-SAMPA-like symbols
- removing residual printer MBROLA code may break undocumented library-only use
  if such callers still exist
- readers may assume phoneprep sidecars must now match phonetizer `.pho` exactly,
  even though this CR intentionally keeps them separate
- symbol merging behavior in `.pho` export may change in edge cases where two
  different realization codes now share the same exported MBROLA symbol

---

# Testing Strategy

Unit tests:

- update `tests/test_phonetize_lib.py` so `.pho` assertions check exported
  MBROLA/X-SAMPA symbols, including pause export as `_`
- add metadata tests for the new realization-inventory MBROLA export field
- remove or rewrite stale MBROLA assertions in `src/akkapros/lib/print.py`

Integration tests:

- update `tests/test_integration.py` to assert phonetizer `.pho` output changed
  while `_phone.txt` and `_ophone.txt` realization codes remain unchanged
- verify printer outputs remain unaffected except for removal of obsolete MBROLA
  library surfaces

Regression tests for unchanged behavior:

- verify `phoneprep.py` outputs and sidecar mapping remain byte-stable unless a
  separate record changes them

Manual review:

- compare the realization table, emitted `.pho` rows, and docs to ensure the
  new mapping is specified once and reused consistently

---

# Rollback Plan

If downstream consumers cannot yet absorb the new `.pho` symbol surface,
restore realization-code emission temporarily while preserving phonetizer stage
ownership, then reopen the mapping change in a narrower follow-up record.

---

# Related Issues

- [CR-045](045-move-mbrola-pho-output-to-phonetizer.md)
- [CR-047](047-close-phonetizer-pause-and-downstream-consumption-gaps.md)
- [REQ-025](../req/025-two-phase-phonetizer-structure-and-duration-pipeline.md)
- [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md)
- [review-008](../review/008-mbrola-contract-split-and-printer-residue-review.md)

---

# Tasks

## Implementation

- [ ] Add the MBROLA/X-SAMPA export field to the realization inventory
- [ ] Update phonetizer `.pho` export to use that field
- [ ] Remove residual printer MBROLA code and empty write path

## Tests

- [ ] Update phonetizer unit tests for X-SAMPA `.pho` output
- [ ] Update integration tests for `.pho` output changes
- [ ] Add regression coverage showing phoneprep remains unchanged

## Documentation

- [ ] Update phonetizer docs
- [ ] Update phone-file guide docs
- [ ] Update printer docs
- [ ] Update MBROLA voice-prep docs to clarify phoneprep remains separate
- [ ] Update release-facing notes

## Review

- [ ] Verify acceptance criteria
- [ ] Confirm mapping completeness and consistency across code, tests, and docs

---

# Implementation Blockers

None currently.

---

# Notes

- The user-provided symbol list is sufficient as a design seed, but the stable
  committed contract should be attached to internal realization codes rather than
  implemented as a mixed external-symbol dictionary.
- This CR intentionally preserves the internal realization-code layer so future
  non-MBROLA TTS backends can derive from the same canonical inventory.