# Requirement: Multi-Format Printer Output

REQ-ID: REQ-005
Status: Implemented
Priority: High
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall convert prosody-realized pivot text (`*_tilde.txt`) into one or more
user-facing output formats: acute-accented text, bold-marked Markdown, IPA transcription,
XAR practical reading orthography, and MBROLA/X-SAMPA-like synthesis format. Each format
is controlled by a dedicated CLI flag. IPA output supports configurable pharyngeal/glottal
policy and speculative circumflex-hiatus splitting.

---

# Motivation

Different consumers of the Akkadian prosody toolkit have different needs: philologists
want a compact reading text with stress marks; editors want Markdown for publication;
phoneticians want IPA for perceptual studies; computational linguists working on speech
synthesis need MBROLA-ready output; learners benefit from the XAR practical orthography
with consistent vowel-length and emphatic marking. A single printer stage driven by the
same pivot ensures consistency: all formats are downstream views of one canonical
accentuated representation.

---

# Acceptance Criteria

## Acute Format

- [ ] Given `--acute`, `<prefix>_accent_acute.txt` is written.
- [ ] Given a tilde-marked syllable, the acute accent (`´`) is placed on the accentuated
      vowel in the output.

## Bold Markdown Format

- [ ] Given `--bold`, `<prefix>_accent_bold.md` is written.
- [ ] Tilde-marked syllables are wrapped in `**...**` (Markdown bold); the `~` marker
      is removed from the output text.

## IPA Format

- [ ] Given `--ipa`, `<prefix>_accent_ipa.txt` is written.
- [ ] Standard Akkadian consonants are mapped to IPA symbols.
- [ ] Long vowels are marked with the IPA length marker (ː).
- [ ] Stress is marked with the IPA primary stress mark (ˈ) on the accentuated syllable.
- [ ] Post-emphatic vowel coloring is applied in IPA output (vowels near `q`, `ṣ`, `ṭ`
      are rendered as pharyngealized/colored variants).
- [ ] Given `--ipa-proto-semitic preserve`, pharyngeal `ḥ` and glottal `ʿ`, `ʾ` are
      preserved as distinct IPA symbols (strict Old Akkadian mode).
- [ ] Given `--ipa-proto-semitic replace` (the default), pharyngeals merge to their OB
      equivalents and glottals are represented by a single practical symbol.
- [ ] Given `--circ-hiatus`, circumflex vowels are split into a hiatus pair in IPA
      (speculative mode, e.g., `qû → qʊ.ʊ`).
- [ ] IPA output includes pause tags at boundary positions.
- [ ] The mapping is explicit in code and documented; silent mapping changes require
      a release note.

## XAR Orthography Format

- [ ] Given `--xar`, both `<prefix>_accent_xar.txt` and `<prefix>_xar.txt` are written.
- [ ] Emphatic consonants are represented with the agreed marked XAR glyphs:
      `q` → `ꝗ`, `ṭ` → `ꞓ`, `ṣ` → `ɉ`.
- [ ] Long (macron) vowels are doubled (e.g., `ā` → `aa`).
- [ ] Circumflex vowels use the two-vowel memory forms (e.g., `â` → `eâ`).
- [ ] Grave accent marks emphatic coloring on adjacent vowels.
- [ ] Pharyngeals `ʿ`, `ʾ` are mapped to `'` in the final reader text.
- [ ] `_accent_xar.txt` carries accentuation marks; `_xar.txt` is the plain (unaccented)
      version.

## MBROLA Format

- [ ] Given `--mbrola`, `<prefix>_accent_mbrola.txt` is written.
- [ ] Output uses X-SAMPA-like notation compatible with MBROLA synthesis input.
- [ ] `--test` runs built-in printer tests and exits with code 0 on pass.

## Defaults

- [ ] If no output-format flag is given, `--acute` and `--bold` are both generated.

---

# User Story (optional)
> As a digital humanities editor, I want to generate Markdown text with stressed
> syllables in bold so I can embed it in a publication without post-processing.
>
> As a phonetician, I want IPA output with configurable emphatic policy so I can
> inspect the prosodic predictions in a notation I can directly read.

---

# Interface Notes
- Input: `<prefix>_tilde.txt` (prosody-realized pivot).
- Outputs:
  - `<prefix>_accent_acute.txt`
  - `<prefix>_accent_bold.md`
  - `<prefix>_accent_ipa.txt`
  - `<prefix>_accent_xar.txt`, `<prefix>_xar.txt`
  - `<prefix>_accent_mbrola.txt`
- Affected components: `src/akkapros/cli/printer.py`, `src/akkapros/lib/print.py`.
- CLI: `python src/akkapros/cli/printer.py <tilde.txt> --ipa --ipa-proto-semitic replace -p <prefix>`

---

# Open Questions
- [ ] Is the `--circ-hiatus` mode considered stable or experimental? Should it carry
      a warning in the output file header?
- [ ] TO_BE_CONFIRMED: are the XAR circumflex memory forms finalized, or is the
      two-vowel encoding still provisional?
- [ ] Should the MBROLA output include duration values derived from mora duration, or
      leave timing to the synthesizer?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature)
- IPA mapping tables are part of the public contract; versioned with release notes.

# Related
- Related ADRs: [ADR-011](../adr/011-multi-format-printer-outputs.md),
  [ADR-019](../adr/019-ipa-output-variant-policy.md)
- Implementation CRs: [CR-004](../cr/004-rename-repair-to-accentuation/)

# Non-Goals
- Does NOT perform audio synthesis; MBROLA output is a text representation requiring
  a separate MBROLA synthesizer (external tool).
- Does NOT back-convert IPA or XAR to the internal tilde format.

# Security / Safety Considerations
- No user-supplied code is executed during formatting.
- Unicode output: ensure XAR special glyphs (U+A757, U+A793, U+0249) are present in
  target fonts before deploying rendered documents.
