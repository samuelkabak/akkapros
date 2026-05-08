---
req_id: REQ-049
status: Implemented
priority: Medium
impact: Additive
created: 2026-05-08
updated: 2026-05-08
related_adrs: ''
implemented_by: 'CR-099'
---

# Requirement: Phonetizer Proto-Semitic Pharyngeal/Glottal Replacement

# Summary

The phonetizer shall support a configurable proto-Semitic pharyngeal/glottal
replacement policy in the realization layer. When enabled, the realization codes
for `ḥ`, `ʿ`, and `ʾ` converge to the same glottal-stop realization (`AL` /
`ʔ`), while `ḫ` remains distinct as `HE` / `χ`. When disabled (default), the
current distinct realizations are preserved: `ḥ -> ET` / `ħ`, `ḫ -> HE` / `χ`,
`ʿ -> AI` / `ʕ`, `ʾ -> AL` / `ʔ`.

This feature is parallel to the printer's `--ipa-proto-semitic {preserve,replace}`
option but operates at the phonetizer realization level so that the replacement
propagates through all downstream consumers (metrics, printer, MBROLA export)
without requiring each consumer to implement its own mapping.

---

# Motivation

The printer currently implements proto-Semitic replacement as a text-level IPA
mapping (`IPA_MAP_STRICT` vs `IPA_MAP_OB`). This means:

1. The replacement only affects IPA output, not MBROLA `.pho` export or XAR output.
2. Each downstream consumer would need its own mapping if the feature were needed
   beyond IPA.
3. The phonetizer is the natural place for phoneme-level realization decisions.

Moving the replacement to the phonetizer realization layer ensures that all
downstream artifacts (IPA, MBROLA, XAR, acute, bold) consistently reflect the
chosen policy. Once this feature is implemented and verified, the printer's
`--ipa-proto-semitic` option can be removed because the phonetizer output
already encodes the correct realization.

---

# Acceptance Criteria

- [x] Given `phonetize.realization.replace_proto_semitic = false` (default),
      when the phonetizer processes input containing `ḥ`, `ḫ`, `ʿ`, `ʾ`, then
      the realization codes are `ET` (ħ), `HE` (χ), `AI` (ʕ), `AL` (ʔ)
      respectively — identical to current behavior.
- [x] Given `phonetize.realization.replace_proto_semitic = true`, when the
      phonetizer processes input containing `ḥ`, `ʿ`, `ʾ`, then the realization
      codes are all `AL` (ʔ), while `ḫ` remains `HE` (χ).
- [x] The replacement applies to both the accentuated (`_phone.txt`) and
      original (`_ophone.txt`) streams.
- [x] The replacement applies to all downstream artifacts: IPA, MBROLA `.pho`,
      XAR, acute, and bold outputs — without requiring separate mapping in each
      consumer.
- [x] The config key `phonetize.realization.replace_proto_semitic` is a boolean
      with default `false`.
- [x] The config key is guarded by `allow_experimental`: setting it to `true`
      requires `phonetize.process.allow_experimental = true`. When
      `allow_experimental` is `false` and `replace_proto_semitic` is `true`,
      the phonetizer verification must report a failure.
- [x] The `allow_experimental` default comment in `default.yaml` is updated to
      list `replace_proto_semitic` among the guarded features.
- [x] Edge case: the replacement does not affect other phonemes (e.g., `b`, `d`,
      `g`, `k`, `p`, `t`, `ṭ`, `q`, `ṣ`, `s`, `z`, `š`, `l`, `m`, `n`, `r`,
      `w`, `y`, vowels, pauses).
- [x] Edge case: the replacement does not affect hiatus (`˙`) or vowel-transition
      (`¨`) markers.
- [x] Edge case: the replacement does not affect emphatic vowel coloring
      (emphatic coloring is driven by the source consonant's emphaticity, not
      by the realization code).

---

# User Story (optional)

> As a researcher working with Old Babylonian texts, I want to configure the
> phonetizer to merge pharyngeal/glottal realizations so that the output
> reflects the OB phonological merger, without needing separate IPA mapping
> in the printer.

---

# Interface Notes

- Input: `phonetize.realization.replace_proto_semitic` boolean in YAML config
- Output: modified realization codes in phone-row streams and all downstream artifacts
- Affected components:
  - `src/akkapros/lib/_phonetize_config.py` — add config field
  - `src/akkapros/lib/phonetize.py` — apply replacement in realization assignment
  - `src/akkapros/lib/print.py` — remove `--ipa-proto-semitic` (deferred to CR)
  - `src/akkapros/cli/printer.py` — remove `--ipa-proto-semitic` (deferred to CR)
  - `src/akkapros/cli/fullprosmaker.py` — remove `--print-ipa-proto-semitic` (deferred to CR)
  - `docs/akkapros/phonetizer-algorithm.md` — document new feature
  - `docs/akkapros/phonetizer-data-model.md` — update realization inventory notes
  - `docs/akkapros/printer.md` — remove `--ipa-proto-semitic` option (deferred to CR)

---

# Open Questions

- [ ] Should the replacement also affect the `_ophone.txt` stream, or only the
      accentuated `_phone.txt` stream? (Current design: both, for consistency.)

---

# Implementation Notes (optional)

- Owner: @change agent
- Estimated effort: small
- Migration: After implementation and verification, the printer's
  `--ipa-proto-semitic` option and its associated code paths should be removed
  in a follow-up CR. The printer will inherit the replacement from the
  phonetizer output and no longer needs its own mapping.

# Related

- Implementation CR: [CR-099](../cr/099-phonetizer-proto-semitic-replacement.md)
- Printer IPA proto-Semitic: `src/akkapros/lib/print.py` lines 89-104 (`IPA_MAP_STRICT`, `IPA_MAP_OB`)

# Non-Goals

- This requirement does NOT change the printer's `--ipa-proto-semitic` option.
  That removal is a separate implementation step after this feature is verified.
- This requirement does NOT change the XAR output mapping (XAR already uses
  apostrophe convergence independently).
- This requirement does NOT affect emphatic vowel coloring logic.

# Security / Safety Considerations

- None. This is a phoneme-level realization mapping with no security implications.

# Revision History

- 2026-05-08: Initial draft
- 2026-05-08: Marked replace_proto_semitic as experimental (guarded by allow_experimental)
- 2026-05-08: Implemented by CR-099. All AC satisfied. Status set to Implemented.
