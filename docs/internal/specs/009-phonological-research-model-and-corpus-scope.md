# Requirement: Phonological Research Model and Corpus Scope

REQ-ID: REQ-009
Status: Implemented (research validated)
Priority: High
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall encode and apply a specific phonological research model
that interprets Akkadian as a stress-timed language, using moraic theory
as its theoretical foundation.  The corpus scope, the stress eligibility
rules, and the three accent hierarchies (LOB, SOB, AOB-provisional) shall
be implemented and documented as explicit, reproducible research decisions,
not as heuristics.

This requirement captures the *research claims* that drive the toolkit's
design, ensuring that the algorithmic choices remain traceable to their
phonological motivation.

---

# Motivation

Without an explicit statement of the research model, the toolkit risks being
used — or evaluated — as a general text-processing tool rather than a
hypothesis-testing instrument for historical prosody.  Encoding the model
here ensures that:

1. Each design decision (e.g., "why not lengthen short vowels?") is
   traceable to a specific phonological constraint.
2. The corpus scope and syllable-weight statistics are versioned alongside
   the code.
3. The three accent styles are understood as *competing hypotheses*, not
   user preferences.

---

# Background: Research Claims (traceable to research notes)

| Claim | Evidence | Source |
|-------|----------|--------|
| Akkadian is stress-timed | VarcoC = 69.09 on the original corpus, compatible with English (70–80) and Dutch (68–78) | Notes 042–044 |
| Academic stress model is incomplete | Provides stress positions but no phrasal timing mechanism | Notes 046–048 |
| Bimoraic unit is the timing target | Cross-linguistic typology; Levantine Arabic CVC observation | Notes 053–054 |
| Short vowels cannot be lengthened | Would neutralize the phonemic short/long contrast | Note 059 |
| Final CVC cannot be geminated | Word-final geminates unattested in Akkadian | Note 058 |
| Prosody realization operations are native | Gemination attested via N-assimilation and T-infix; lengthening attested in morphology | Notes 011–014 |
| CVVC treatment: lengthen, not shorten | Conservative choice; preserves lexical length distinctions | Notes 017–018 |
| ~19% accentuation rate is emergent | Follows from syllable distribution and legal operation constraints; not a design target | Notes 019–020 |
| Corpus: Standard Babylonian literary texts | Three genres (epic, mythological poem, incantation) | Note 018b |
| Corpus size: 4,917 words, 14,684 syllables | From Enūma Eliš II/IV/VI/VII, Erra I, Marduk's Address | Note 042 |

---

# Acceptance Criteria

## Phonological Constraints

- [ ] The algorithm never lengthens a short vowel (CV → CVV is forbidden).
- [ ] The algorithm never geminates a word-final consonant.
- [ ] The algorithm never creates tri-consonantal clusters.
- [ ] Onset gemination is used only as a last resort (no other legal operation exists).

## Syllable Typology

- [ ] The engine correctly classifies syllables into the eight types:
      CV (1µ), V (1µ), CVC (2µ), VC (2µ), CVV (2µ), VV (2µ), CVVC (3µ), VVC (3µ).
- [ ] Repaired types are classified as:
      CVC: (coda gemination = 3µ), CVV: (vowel lengthening = 3µ),
      CVV:C (superheavy lengthening = 4µ), C:V (onset gemination = 2µ).

## Accent Models (Three Hierarchies)

- [ ] **LOB** (Literary Old Babylonian) priority:
      (1) Final superheavy / circumflex-bearing; (2) Rightmost non-final heavy; (3) Final heavy.
      Based on Streck (2022).
- [ ] **SOB** (Standard Old Babylonian) priority:
      (1) Rightmost non-final heavy; (2) Final heavy.
      Based on Huehnergard (2011).
- [ ] **AOB** (Academic Old Babylonian) priority is documented but not exposed as a
      stable production option:
      (1) Final superheavy; (2) Rightmost non-final heavy; (3) First syllable.
      Retained for sensitivity testing.

## Corpus Statistics (reproducible baselines)

- [ ] Corpus syllable distribution (±0.2% tolerance on the full corpus run):
      CV ≈ 35.7%, CVC ≈ 22.0%, CVV ≈ 21.5%, CVVC ≈ 2.5%, VC ≈ 6.0%, V ≈ 7.0%.
- [ ] Original corpus metrics: %V (pause-excluded) ≈ 79.9%, VarcoC ≈ 69.09.
- [ ] Accentuated corpus metrics: VarcoC ≈ 70.67, accentuation rate ≈ 13.63%,
      words merged ≈ 49.9%.
- [ ] Full pipeline results are reproducible using the demo scripts.

---

# User Story (optional)
> As a historical linguist evaluating the toolkit, I want to understand what
> phonological claims are encoded in the algorithm so that I can assess which
> hypotheses are being tested and reproduce the quantitative results independently.

---

# Interface Notes
- No direct CLI interface; this requirement constrains the implementation of
  REQ-002, REQ-003, and REQ-004.
- Reference texts: Huehnergard (2011), Streck (2022), Ramus et al. (1999),
  Dellwo (2006), White & Mattys (2007).
- Corpus files: `data/samples/` (eBL ATF format).

---

# Open Questions
- [ ] TO_BE_CONFIRMED: should the AOB model be removed from the codebase entirely,
      or kept as a non-default research option?
- [ ] TO_BE_CONFIRMED: what is the agreed corpus expansion roadmap (letters, legal
      documents, administrative texts as mentioned in research note 018b)?
- [ ] Should the corpus statistics be auto-validated in a CI test to catch regressions?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (corpus validated)
- Note: The research model is incompletely represented in the codebase docstrings;
  `docs/akkapros/prosody-realization-algorithm.md` is the authoritative prose description.

# Related
- Related ADRs: [ADR-008](../adr/008-bimoraic-prosody-and-accent-styles.md),
  [ADR-009](../adr/009-function-word-and-merge-policy.md),
  [ADR-010](../adr/010-metrics-from-text-and-dual-percent-v.md),
  [ADR-016](../adr/016-diphthong-restoration-constraint-system.md),
  [ADR-017](../adr/017-pause-modeling-and-bimoraic-correction.md),
  [ADR-018](../adr/018-extensible-phonetic-inventory.md)
- External references: `tmp/research-notes.md` (proprietary; not part of the MIT
  licensed codebase)

# Non-Goals
- Does NOT claim to reconstruct the historically attested Akkadian prosody.
  Results are one computationally consistent hypothesis.
- Does NOT address prosody of other ancient Semitic languages (Ugaritic, Eblaite,
  etc.) without toolkit extension.
- Does NOT perform metrical scansion of Akkadian poetry (that is a separate
  application layer beyond this toolkit's scope).

# Security / Safety Considerations
- No direct security implications. Research model decisions should be clearly
  labelled as hypotheses in all published outputs to avoid misrepresentation.
