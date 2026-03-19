# Requirement: Bimoraic Prosody Realization Algorithm

REQ-ID: REQ-003
Status: Implemented
Priority: High
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall apply a moraic prosody realization algorithm to syllabified Akkadian
text that (a) selects a stress-eligible syllable within each prosodic unit, (b) adds
exactly one mora to that syllable using a phonologically legal operation, and (c)
merges consecutive words when a standalone word has no eligible syllable or an odd
mora total, until a bimoraic (even-mora) unit is achieved. The algorithm shall support
LOB (Literary Old Babylonian) and SOB (Standard Old Babylonian) accent style variants.
Function words must attach to adjacent content words before accentuation.

---

# Motivation

Acoustic analysis of the Standard Babylonian corpus shows VarcoC ≈ 69.09, consistent
with stress-timed languages (research notes 042–044). The academic lexical stress model
(Huehnergard 2011; Streck 2022) identifies *where* stress can fall but provides no
mechanism for phrasal timing. A stress-timed language requires variable timing between
fixed stress peaks, which demands operations that extend prominent syllables and compress
or group unstressed ones. The bimoraic realization algorithm fills this gap using only
phonological operations already attested in Akkadian (N-assimilation → gemination,
vowel lengthening, anaptyxis).

Key phonological constraints that must be respected:
- Short vowels (CV, V) cannot be lengthened (would neutralize the phonemic short/long contrast).
- Word-final consonants cannot be geminated (word-final geminates are unattested).
- Only coda consonants are available for gemination; onset gemination is last resort.
- Tri-consonantal clusters are forbidden; operations must not create them.

---

# Acceptance Criteria

## Algorithm Core

- [ ] Given a syllabified word with an odd mora total and an eligible syllable, when
      processed, exactly one mora is added to the selected syllable and a `~` marker
      is placed on it.
- [ ] Given a CVV or VV syllable as candidate, when accentuated, the vowel is
      lengthened (extra-long) and `~` is appended after the vowel.
- [ ] Given a CVVC or VVC syllable as candidate, when accentuated, the vowel length is
      extended (superheavy with `~`) and the coda consonant is preserved.
- [ ] Given a CVC or VC non-final syllable as candidate, when accentuated, the coda is
      geminated and `~` is appended to the syllable.
- [ ] Given a word-final CVC syllable, when processed, it is NOT geminated (constraint:
      word-final gemination is illegal).
- [ ] Given a word with only CV or V syllables and no merge partner, when processed,
      onset gemination is used as a last resort (applied to the first syllable).
- [ ] Given a word with an odd mora total that cannot be resolved internally, when
      processed, the word is merged forward (marked with `+`) with the next word and
      the merged unit is retried.
- [ ] Given a merged unit that still cannot be resolved at a forward punctuation
      boundary, when processed, backward merge is attempted.
- [ ] Given function words (prepositions, conjunctions, particles, pronouns), when
      processed, they attach to adjacent content words before accentuation is attempted.
- [ ] Diphthong restoration is applied after accentuation: temporary glottal-stop
      split markers are removed from `_tilde.txt` output.

## Accent Styles

- [ ] Given `--style lob`, the priority hierarchy is:
      1. Final superheavy (CVVC / VVC, including circumflex finals)
      2. Rightmost non-final heavy
      3. Final heavy
- [ ] Given `--style sob`, the priority hierarchy is:
      1. Rightmost non-final heavy
      2. Final heavy
- [ ] Both styles use identical legal operations and merge/unmerge logic; they differ
      only in syllable selection priority.

## Output

- [ ] Output file is `<prefix>_tilde.txt`.
- [ ] `+` in output marks merged/prosodically linked words (no pause between them).
- [ ] Space in output marks ordinary word boundaries.
- [ ] `~` marks the prosody-realized (accentuated) syllable.
- [ ] `--test` runs the built-in test suite and exits with code 0 on pass.
- [ ] `--test-diphthongs` runs diphthong restoration tests specifically.

## Bimoraic Well-Formedness

- [ ] Each standalone word or merged unit, after processing, has an even mora total.
- [ ] The algorithm terminates in finite steps for any input (bounded by total morae).

---

# User Story (optional)
> As a researcher, I want the prosody realization engine to produce rhythmically
> coherent accentuated text such that downstream metrics confirm a VarcoC in the
> stress-timed range.

---

# Interface Notes
- Input: `<prefix>_syl.txt` (output of REQ-002).
- Output: `<prefix>_tilde.txt` (the project's central pivot format).
- Pivot format markers:

  | Symbol | Meaning |
  |--------|---------|
  | `·` / `-` | Syllable separators |
  | `+` | Merged words (prosodic unit, no pause) |
  | space | Ordinary word boundary |
  | `~` | Accentuated syllable marker |

- Affected components: `src/akkapros/cli/prosmaker.py`, `src/akkapros/lib/prosody.py`.
- CLI: `python src/akkapros/cli/prosmaker.py <input_syl.txt> --style lob -p <prefix> --outdir <dir>`

---

# Open Questions
- [ ] Should an AOB (Academic Old Babylonian) style be re-introduced for comparison
      purposes? (Research note 064 sets it aside; reconsider if needed for validation.)
- [ ] Should `--relax-last` behaviour be documented as a stability guarantee or
      remain experimental?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature)
- Validation: 100% accuracy on 4-line, 27-word hand-analysed sample before corpus run.
- Corpus result: ~19% of syllables accentuated; ~50% of words merged.
- Sensitivity: two competing CVVC hypotheses (lengthen vs. shorten) yield VarcoC
  difference < 0.1, within the 95% CI band (research note 043).

# Related
- Related ADRs: [ADR-008](../adr/008-bimoraic-prosody-and-accent-styles.md),
  [ADR-009](../adr/009-function-word-and-merge-policy.md),
  [ADR-016](../adr/016-diphthong-restoration-constraint-system.md),
  [ADR-017](../adr/017-pause-modeling-and-bimoraic-correction.md),
  [ADR-018](../adr/018-extensible-phonetic-inventory.md),
  [ADR-020](../adr/020-deterministic-merge-traversal.md)
- Implementation CRs: none currently open

# Non-Goals
- Does NOT perform syntactic parsing or semantic analysis.
- Does NOT export audio; audio synthesis is the responsibility of the TTS pipeline
  (phoneprep + MBROLATOR, covered separately).
- Does NOT claim to reconstruct the historically attested prosody of Akkadian;
  it is one computationally consistent hypothesis.

# Security / Safety Considerations
- No external data sources or network access during processing.
- Input validation: malformed tilde format from corrupted intermediate files could
  produce incorrect output silently; consider adding a format-validation guard.
