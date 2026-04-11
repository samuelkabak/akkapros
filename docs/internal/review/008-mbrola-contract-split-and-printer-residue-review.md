---
review_id: review-008
status: Done
created: 2026-04-11
updated: 2026-04-11
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  src/akkapros/lib/phonetize.py,
  src/akkapros/lib/print.py,
  src/akkapros/lib/phoneprep.py,
  src/akkapros/cli/phonetizer.py,
  src/akkapros/cli/printer.py,
  src/akkapros/lib/helpmsg.py,
  docs/akkapros/phonetizer.md,
  docs/akkapros/printer.md,
  docs/akkapros/phonetizer-phone-file-guide.md,
  and docs/internal/cr/045-move-mbrola-pho-output-to-phonetizer.md.
---

# Code and Project Review — MBROLA Contract Split and Printer Residue

## 1. Executive Summary

The repository currently contains two different MBROLA-facing symbol systems,
but they do not serve the same contract. The active `.pho` contract is now the
phonetizer-owned realization-code stream defined by
[CR-045](../cr/045-move-mbrola-pho-output-to-phonetizer.md) and implemented in
`src/akkapros/lib/phonetize.py`, while `src/akkapros/lib/print.py` still keeps
an older X-SAMPA-like MBROLA renderer that is no longer part of the active CLI
surface. That residual printer path is not just stale: if called through the
library write path, it currently writes an empty MBROLA file. The top priority
is therefore to retire or formally quarantine printer-side MBROLA code and to
document phoneprep as a separate machine-sidecar inventory rather than as the
same alphabet used by phonetizer-owned `.pho` export.

## 2. Architecture Assessment

### 2.1 Strengths

- [CR-045](../cr/045-move-mbrola-pho-output-to-phonetizer.md) clearly rehomes
  `.pho` ownership to the phonetizer and explicitly says the active exporter
  emits realization codes rather than printer spellings.
- `src/akkapros/lib/phonetize.py` now has one coherent `.pho` path:
  `REALIZATION_CODE_ROWS` defines the emitted symbol inventory and
  `serialize_mbrola_rows()` emits `symbol duration frequency` lines from
  duration-bearing phone rows.
- `src/akkapros/cli/phonetizer.py` and `docs/akkapros/phonetizer.md` are
  aligned with that active contract and write `<prefix>_ombrola.pho` and
  `<prefix>_mbrola.pho` from phonetizer-owned row streams.
- `src/akkapros/cli/printer.py`, `src/akkapros/lib/helpmsg.py`, and
  `docs/akkapros/printer.md` have already been partially cleaned: the active
  printer CLI no longer exposes MBROLA output as a supported user-facing mode.

### 2.2 Areas for Improvement

- `src/akkapros/lib/print.py` still contains a complete MBROLA conversion path
  based on `MBROLA_CONSONANT_MAP`, `MBROLA_VOWELS_DEFAULT`,
  `MBROLA_VOWELS_EMPHATIC`, `mode == 'mbrola'`, and
  `convert_text_with_ipa_xar_mbrola()`. This is an older symbol-by-symbol
  rendering model, not the active phonetizer-owned `.pho` model.
- The residual printer MBROLA path materially conflicts with the active
  phonetizer contract because it produces X-SAMPA-like tokens such as `X`, `x`,
  `S`, `s.`, `t.`, and split vowel strings like `a a`, while phonetizer-owned
  `.pho` emits realization codes such as `ET`, `HE`, `SI`, `SU`, `TU`, `AA`,
  `AO`, `SP`, and `ZP`.
- `src/akkapros/lib/phoneprep.py` is not wrong in the same way, but it uses yet
  another MBROLA/X-SAMPA-like mapping for MBROLATOR and voice-building sidecars.
  That is a separate tool contract, but the shared `MBROLA_*` naming makes the
  distinction easy to miss.
- The repository therefore has one active `.pho` alphabet and at least two
  residual or auxiliary MBROLA symbol inventories that are not clearly named as
  different things.

## 3. Code Quality Assessment

- The most important concrete defect is in `src/akkapros/lib/print.py`: inside
  `process_file()`, printer computes acute, bold, IPA, and XAR text from phone
  rows, but sets `mbrola_text = ''` and still writes that value when
  `write_mbrola=True`. That means the residual library surface can generate an
  empty MBROLA file instead of either producing valid output or failing loudly.
- The printer self-tests still assert MBROLA examples in `print.py`, which pins
  behavior that the active printer CLI no longer exposes. This keeps obsolete
  behavior alive through tests even after the documented CLI contract moved on.
- `src/akkapros/lib/frontmatter.py` still recognizes `mbrola` as a text format,
  which appears to reflect the same residual printer-era path rather than the
  active phonetizer-owned raw `.pho` artifact contract.
- The active phonetizer `.pho` path is internally coherent: `REALIZATION_CODE_ROWS`
  defines the emitted symbols, `REALIZATION_CODE_METADATA` annotates them, and
  `serialize_mbrola_rows()` emits those codes after timing realization. The main
  problem is not phonetizer quality but stale competing code in printer and the
  ambiguous naming overlap with phoneprep.

## 4. Documentation Assessment

- `docs/akkapros/printer.md` correctly states that speech-synthesis `.pho`
  export no longer belongs to `printer.py` and that users should use
  `phonetizer.py` or `fullprosmaker.py` for MBROLA files.
- `docs/akkapros/phonetizer.md` correctly states that `.pho` export is raw
  three-column output derived from phone rows and governed by phonetize-owned
  intonation settings.
- `docs/akkapros/phonetizer-phone-file-guide.md` correctly treats printer and
  metrics as consumers of `_phone.txt` and `_ophone.txt`, not as owners of
  their own pause or speech-synthesis encodings.
- What remains under-documented is the distinction between:
  - phonetizer-owned realization-code `.pho` export,
  - printer’s residual legacy MBROLA renderer, and
  - phoneprep’s MBROLATOR sidecar mapping.
- Without an explicit note, a reader can easily assume these three MBROLA-ish
  surfaces are supposed to share one alphabet when they currently do not.

## 5. Research / Functional Assessment

- Functionally, the active `.pho` contract now lives in phonetizer, not in
  printer.
- The emitted phonetizer `.pho` symbols are not generic MBROLA/X-SAMPA phones.
  They are realization codes chosen by the repository’s phone-row model.
- The printer MBROLA path is therefore not a second implementation of the same
  exporter. It is a legacy transliteration-style renderer that predates the
  phonetizer-owned `.pho` contract.
- Phoneprep is different again: it prepares machine sidecars for voice-building
  workflows and therefore uses an X-SAMPA-like inventory derived from source
  symbols. That makes it adjacent to MBROLA tooling, but not equivalent to the
  phonetizer-owned `.pho` alphabet.
- The user’s observed mismatch is real. The repository currently has a naming
  collision between:
  - active phonetizer realization-code `.pho` export,
  - legacy printer MBROLA text rendering,
  - phoneprep MBROLA/X-SAMPA sidecar generation.

## 6. Process and Engineering Practices

- The internal governance is behaving correctly here: [CR-045](../cr/045-move-mbrola-pho-output-to-phonetizer.md)
  clearly moved ownership, and the user-facing printer docs were updated.
- The implementation cleanup is incomplete, which means code and tests still
  preserve surfaces that the newer governing record already superseded.
- This is a good example of why later higher-numbered records need explicit
  codebase cleanup or quarantine work, not only documentation changes.

## 7. Recommendations (Priority Order)

1. High: Remove or quarantine printer-side MBROLA rendering in `src/akkapros/lib/print.py`. Minimal next step: create a CR that either deletes the residual `mode == 'mbrola'` path and its tests or explicitly marks it as legacy/internal and prevents empty-file writes.
2. High: Make the active `.pho` alphabet explicit as realization-code output, not X-SAMPA-like output. Minimal next step: add one internal or public note saying that phonetizer `.pho` rows intentionally emit realization codes from `REALIZATION_CODE_ROWS`.
3. Medium: Rename or document phoneprep’s MBROLA maps as MBROLATOR-sidecar inventory rather than treating them as the same contract as phonetizer `.pho`. Minimal next step: add one clarifying note in `phoneprep.py` docs or the next spec record touching phoneprep.
4. Medium: Remove stale printer MBROLA frontmatter and self-test surfaces if they are no longer part of any supported runtime contract. Minimal next step: audit `frontmatter.py`, `print.py` self-tests, and any library-only API path that still mentions `mbrola` as a printer format.
5. Low: Add one repository-level glossary note distinguishing `realization code`, `IPA`, `XAR`, and `MBROLA/X-SAMPA-like sidecar symbols`. Minimal next step: place it in the phonetizer or phoneprep docs.

## 8. Summary Verdict

The active MBROLA `.pho` contract is phonetizer-owned and realization-code-based, but the codebase still contains stale printer MBROLA rendering and a separate phoneprep sidecar alphabet that together create a real, user-visible contract split.