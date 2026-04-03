---
req_id: REQ-021
status: Draft
priority: High
impact: Mutative
created: 2026-04-01
updated: 2026-04-03
related_adrs: 'ADR-007, ADR-016, ADR-021, ADR-022, ADR-035'
implemented_by: 'CR-029'
---

# Requirement: Separate Hiatus Marker for Word-Initial Vowel Hiatus

# Summary

The system shall preserve `DIPH_SEPARATOR = '¨'` for diphthong-transition
handling and introduce a distinct internal marker `HIATUS_MARKER = '˙'` for
word-initial vowel hiatus across the syllabifier and downstream pipeline.

The canonical code identifiers shall therefore remain separate:
`DIPH_SEPARATOR` for `¨` and `HIATUS_MARKER` for `˙`. The system shall not
redefine `DIPH_SEPARATOR` to cover the word-initial hiatus case.

The system shall insert `HIATUS_MARKER` for vowel-initial words in internal
stage output. When it precedes a vowel at word start, it shall function as the
onset of that syllable for syllabification purposes while remaining invisible
in final printer outputs. `DIPH_SEPARATOR` shall continue to represent the
transition onset placeholder in diphthong or split-vowel contexts.

For regression scope, only intermediate stage outputs that intentionally encode
the new marker are expected to change. Printer outputs and metricalc outputs
shall remain unchanged.

---

# Motivation

The pipeline already uses `¨` internally for diphthong or split-vowel
processing. The earlier CR-029 draft proposed broadening that symbol into a
general transition pseudo-consonant for vowel-initial zero onset. That is no
longer the desired contract.

This requirement instead keeps the existing diphthong-transition meaning of
`DIPH_SEPARATOR` intact and adds a new symbol for the separate internal role of
word-initial hiatus. This keeps the contract explicit without changing final
user-visible output.

All code changes related to the earlier broader draft were discarded before
this requirement rewrite. No residual implementation cleanup is assumed.

---

# Acceptance Criteria
*Verifiable conditions that must be met. Use Given/When/Then format where appropriate.*

- [ ] Given the shared constants module, when the internal markers are defined,
      then `DIPH_SEPARATOR = '¨'` and `HIATUS_MARKER = '˙'` exist as separate
      constants.
- [ ] Given the internally sensitive normalization-hooks block, when the
      effective consonant inventory is assembled, then it contains both
      `AKKADIAN_CONSONANTS.add(DIPH_SEPARATOR)` and
      `AKKADIAN_CONSONANTS.add(HIATUS_MARKER)`.
- [ ] Given internal or user-facing documentation refers to syllable
      boundaries, when these markers are described, then `·` is identified as
      the syllable-boundary marker and neither `¨` nor `˙` is described as a
      boundary.
- [ ] Given a clean vowel-initial word such as `ana`, when syllabified, then
      the output begins with `HIATUS_MARKER`, for example `˙a·na¦`.
- [ ] Given a diphthong-transition source such as `tiam`, when it is internally
      split, then the split form remains `ti¨am`, and when syllabified the form
      remains `ti·¨am`.
- [ ] Given an existing diphthong case such as `tiāmtu`, when syllabified and
      then prosody-processed, then `DIPH_SEPARATOR` continues to mark the
      transition without regression.
- [ ] Given `*_syl.txt` or `*_tilde.txt` contains a leading `HIATUS_MARKER`,
      when syllable counts are computed for logs, front matter, or validation
      helpers, then the marker is treated as onset structure and no empty
      leading syllable is counted.
- [ ] Given `HIATUS_MARKER` appears at word onset, when downstream parsing or
      metrics logic runs, then it behaves as consonant-like onset structure and
      does not create false split segments.
- [ ] Given prosody applies last-resort accentuation to a syllable beginning
      with `˙`, when the output is serialized, then the tilde follows `˙`, for
      example `˙a -> ˙~a`.
- [ ] Given printer consumes internal stage output containing `¨` and `˙`, when
      acute output is generated, then the visible text is unchanged.
- [ ] Given printer consumes internal stage output containing `¨` and `˙`, when
      bold output is generated, then the visible text is unchanged.
- [ ] Given printer consumes internal stage output containing `¨` and `˙`, when
      IPA output is generated, then the visible text is unchanged.
- [ ] Given printer consumes internal stage output containing `¨` and `˙`, when
      accented XAR, plain XAR, or MBROLA output is generated, then the visible
      text is unchanged.
- [ ] Given metricalc consumes updated internal stage input, when regression
      tests compare current outputs to existing references, then the outputs
      remain unchanged.
- [ ] Given source input contains an explicit lexical `ʾ`, `DIPH_SEPARATOR`, or
      `HIATUS_MARKER`, when the pipeline processes the word, then those remain
      distinguishable in internal representations.
- [ ] Given the implementation is complete, when regression tests are run, then
      unit tests, embedded self-tests, and integration tests demonstrate that
      only the intended intermediate-stage outputs changed.
- [ ] Given user-facing and developer-facing documentation are updated, when
      users read those docs, then they can distinguish `DIPH_SEPARATOR`
      behavior, `HIATUS_MARKER` behavior, and visible output behavior.

---

# User Story (optional)
> As a researcher using the Akkadian prosody pipeline, I want word-initial
> vowel hiatus to be represented with a marker distinct from the
> diphthong-transition symbol so that the internal contract stays explicit
> without changing final reading outputs.

---

# Interface Notes
- Input stages affected:
  - `*_proc.txt` into syllabifier
  - `*_syl.txt` into prosody
  - `*_tilde.txt` into downstream formatting and metrics paths
- Intermediate examples:
  - `ana -> ˙a·na¦`
  - `tiam -> ti¨am -> ti·¨am`
  - `˙a -> ˙~a` in word-initial last-resort accentuation
- Positional rule:
  - word-initial `˙V` is onset structure, not a free-standing boundary
  - in `V·¨V`, `·` is the boundary and `¨` is the onset placeholder of the
    following syllable
  - `¨` and `˙` are distinct internal pseudo-consonants and must not be merged
- Output invariants:
  - printer outputs unchanged
  - metricalc outputs unchanged
- Affected components:
  - `src/akkapros/lib/constants.py`
  - `src/akkapros/lib/syllabify.py`
  - `src/akkapros/lib/prosody.py`
  - `src/akkapros/lib/print.py`
  - `src/akkapros/lib/metrics.py`
  - `src/akkapros/lib/frontmatter.py`

---

# Open Questions
- [x] No helper or test renaming follow-up is required from the rolled-back
      draft, because the related code changes were discarded before this rewrite.

---

# Implementation Notes (optional)
- Owner: TBD
- Estimated effort: medium
- Migration:
  - update intermediate fixtures only where word-initial `˙` is introduced
  - keep printer and metricalc references byte-identical
  - update docs that currently conflate the zero-onset case with
    `DIPH_SEPARATOR`
      - no code-side cleanup migration is required from the rolled-back draft

# Related
- Related ADRs: [ADR-007](../adr/007-two-phase-diphthong-processing.md),
  [ADR-016](../adr/016-diphthong-restoration-constraint-system.md),
  [ADR-021](../adr/021-multi-target-printer-architecture-contract.md),
  [ADR-022](../adr/022-output-format-public-contract-boundaries.md),
  [ADR-035](../adr/035-separate-hiatus-marker-and-word-initial-zero-onset-contract.md)
- Implementation CRs: [CR-029](../cr/029-introduce-separate-hiatus-marker-for-word-initial-vowel-hiatus.md)

# Non-Goals
- This requirement does not rename `DIPH_SEPARATOR`.
- This requirement does not change the meaning of `DIPH_SEPARATOR`.
- This requirement does not change visible printer outputs.
- This requirement does not change visible metricalc outputs.
- This requirement does not change merge policy, mora mode, or accent-placement
  policy beyond the serialization of `˙~V` in the specific last-resort case.

# Security / Safety Considerations
- This is a compatibility-sensitive internal-representation change. If poorly
  implemented, it can silently corrupt syllable counts or create visible-output
  regressions.
- Unicode handling must preserve both `¨` and `˙` exactly through the internal
  pipeline.
- Documentation must clearly state that these are internal technical symbols,
  not user-facing orthographic characters.
