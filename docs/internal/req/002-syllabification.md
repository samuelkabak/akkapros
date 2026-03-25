# Requirement: Akkadian Syllabification

REQ-ID: REQ-002
Status: Implemented
Priority: High
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall convert clean Akkadian text (output of REQ-001) to syllabified
form following Huehnergard (2011) syllabification rules. It shall insert syllable
boundaries, mark word endings, handle hyphens as prosodic boundaries, expand
adjacent vowels (diphthong phase 1), and preserve non-Akkadian escaped chunks
unchanged.

---

# Motivation

Prosody realization and metrics computation both operate on syllable-level
representations. Without a consistent, rule-governed syllabification layer,
downstream tools cannot reliably detect syllable weight or apply phonological
operations. The syllabifier also inserts glottal stops between vowels in hiatus
(diphthong expansion) so that every vowel sequence is unambiguously parsed into
two syllables—a requirement of the moraic algorithm.

Line structure (verse boundaries) must be preserved because it encodes phrasing
information used by the prosody engine.

---

# Acceptance Criteria

- [ ] Given Akkadian text, when syllabified, syllable boundaries are marked with `·`
      (middle dot) and word endings are marked with `¦`.
- [ ] Given a hyphenated construct `bīt-šarrim`, when syllabified with default settings,
      the hyphen is preserved as a prosodic boundary (`-`), not converted to a dot.
- [ ] Given `--merge-hyphen`, hyphens are converted to syllable separators (dots).
- [ ] Given adjacent vowels in hiatus (e.g. `ua`), a glottal stop `ʾ` is inserted between
      them so the segment is split into two syllables.
- [ ] Given `[punctuations/foreign text]` in the input, the content is wrapped in `⟦...⟧` escape
      syntax and internal whitespace is preserved unchanged.
- [ ] Given CR-005 escape syntax (`{{text}}` or `{tag{text}}`), escaped chunks pass
      through without syllabification.
- [ ] Given `+` linker between words, it is preserved in output as a prosodic-attachment
      marker.
- [ ] Given `--merge-lines`, single newlines become spaces and two+ consecutive newlines
      become a single paragraph break. Without the flag, all newlines are preserved.
- [ ] The set of recognised vowels and consonants is extensible via `--extra-vowels` and
      `--extra-consonants` CLI flags.
- [ ] `--test` runs the built-in ≥40-case test suite and exits with code 0 on full pass.
- [ ] All output is UTF-8; no Unicode character is silently dropped or replaced.
- [ ] Output file name follows the convention `<prefix>_syl.txt`.

---

# User Story (optional)
> As a researcher running the prosody pipeline, I want clean syllabified text
> with unambiguous word and syllable boundaries so that I can feed it to the
> prosody realization engine without manual review.

---

# Interface Notes
- Input: `<prefix>_proc.txt` (clean Akkadian text).
- Output: `<prefix>_syl.txt`.
- Markers in output:

  | Marker | Meaning |
  |--------|---------|
  | `·` | Syllable separator |
  | `¦` | Word-ending marker |
  | `-` | Hyphen boundary (preserved by default) |
  | `+` | Linker boundary (prosodic attachment) |
  | `⟦...⟧` | Escaped non-Akkadian chunk |

- Affected components: `src/akkapros/cli/syllabifier.py`, `src/akkapros/lib/syllabify.py`.

---

# Open Questions
- [ ] Should the glottal-stop diphthong expansion be toggleable via a CLI flag for use
      with texts that already disambiguate hiatus?
- [ ] Is `·` (U+00B7) the final stable separator character, given font rendering
      variation on some terminals?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature; test suite covers ~40 cases)
- **WARNING**: `tokenize_line()` and `syllabify_text()` in `syllabify.py` are
  high-risk functions. Do not rewrite without full test-suite coverage. Add a test
  case before modifying these functions (see copilot-instructions.md).

# Related
- Related ADRs: [ADR-006](../adr/006-syllabifier-line-and-hyphen-policy.md),
  [ADR-007](../adr/007-two-phase-diphthong-processing.md)
- Implementation CRs: none currently open

# Non-Goals
- Does NOT perform morphological analysis or lemmatization.
- Does NOT assign stress; stress assignment is handled by REQ-003.
- Does NOT parse non-Akkadian segments (they are escaped and passed through).

# Security / Safety Considerations
- Input originates from trusted internal pipeline output. No user-supplied code
  execution occurs during syllabification.
- Unicode normalisation must not silently alter diacritic characters distinctive
  to Akkadian phonology (e.g., macron ā, circumflex â).
