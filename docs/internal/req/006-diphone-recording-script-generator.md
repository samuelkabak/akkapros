# Requirement: Diphone Recording Script Generator (phoneprep)

REQ-ID: REQ-006
Status: Implemented
Priority: Medium
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall generate a coverage-optimised Akkadian recording script for
MBROLA diphone voice construction. It shall produce a human-readable recording
prompt file (with syllable dots and delimited utterances), deterministic machine
sidecars (manifest TSV, diphone index TSV, compact word list), and optionally
an interactive HTML recording assistant. The generator must respect Akkadian
phonotactic legality constraints and aim to cover every legal diphone transition
at a configurable target coverage level.

---

# Motivation

Building a synthesized Akkadian voice requires a diphone inventory captured from
recordings. The set of legal Akkadian diphone transitions is large (~1000+ pairs
after applying phonotactic rules). Manually constructing a minimal-coverage word
list is intractable. An automated, coverage-driven generator allows systematic,
reproducible recording campaigns while minimizing recording time and cost.

The HTML recording assistant reduces the operational complexity of coordinating
recording sessions and provides event-logged timing data that downstream
segmentation tools can use.

---

# Acceptance Criteria

## Core Coverage

- [ ] The generator constructs words that obey Akkadian phonotactic legality
      (no illegal consonant clusters, no final geminates, valid syllable patterns).
- [ ] The generator targets a per-diphone coverage count configurable via `--coverage`
      (default: 3).
- [ ] Three canonical word pattern templates are used:
      Pattern 1 (VC·CVC·CV), Pattern 2 (CV·CVC·CVC), Pattern 3 (CVV·CVVC).
- [ ] Emphatic consonants (`q`, `ṣ`, `ṭ`) receive dedicated coverage handling;
      `--two-batch-emphatic` builds two recording batches (plain-first, then mixed).
- [ ] A stochastic optimizer runs within `--max-iterations` rounds and evaluates
      `--candidate-pool-size` candidates per selection step.
- [ ] `--seed <int>` enables fully reproducible generation.
- [ ] `--non-vv-target-ratio` sets a soft completion threshold for non-VV targets;
      `--strict-max-non-vv` enforces a hard cap.

## Outputs

- [ ] `<output>.txt` — human recording script; utterances wrapped in `_..._`,
      syllable boundaries marked with `.`, grouped by pattern class.
- [ ] `<base>_manifest.tsv` — one row per utterance with MBROLA symbols, full
      diphone list, pattern ID, and batch tag (unless `--no-sidecars`).
- [ ] `<base>_diphones.tsv` — one row per diphone cursor position (unless `--no-sidecars`).
- [ ] `<base>_words.txt` — compact MBROLA-symbol word list (unless `--no-sidecars`).
- [ ] `<base>_recording_helper.html` — interactive controller with event logging
      (only when `--with-html-recording-helper`).

## Inventory Extensibility

- [ ] Plain consonants, emphatic consonants, plain vowels (short/long), and colored
      vowels (short/long) are all override-able via CLI flags.
- [ ] `--debug-reduced-set` enables a reduced inventory for testing.
- [ ] Long vowels are represented in MBROLA notation as `(x x)` pairs, not single symbols.

## Testing

- [ ] `--test` runs built-in self-tests and exits with code 0 on pass.

---

# User Story (optional)
> As a speech engineer preparing for an Akkadian MBROLA voice build, I want a
> minimal recording script that covers all legal diphone transitions at least 3
> times, together with machine-readable sidecars, so that I can automate
> segmentation and diphone dataset construction.

---

# Interface Notes
- Input: none (self-contained generator; no pipeline input file).
- Outputs: see Outputs section above.
- Affected components: `src/akkapros/cli/phoneprep.py`.
- Demo launchers: `demo/akkapros/phoneprep/phoneprep-demo.ps1` (Windows),
  `demo/akkapros/phoneprep/phoneprep-demo.sh` (Unix).
- CLI example:
  ```
  python src/akkapros/cli/phoneprep.py --coverage 3 --with-html-recording-helper \
    --seed 100 --output demo/akkapros/phoneprep/results/phoneprep.txt
  ```

---

# Open Questions
- [ ] TO_BE_CONFIRMED: what is the total number of legal Akkadian diphone transitions
      in the current inventory model, and does 3× coverage saturate the set at the
      878-word corpus size?
- [ ] Should the HTML recording assistant produce JSON event logs or a simpler
      timestamp CSV?
- [ ] Is `--recording-max-words` (default 1000) the right upper bound for chunk size,
      or should this default be configurable per voice build?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature; 878-word coverage demonstrated)
- Segmenter (WAV segmentation from event log) is PLANNED but not yet released.

# Related
- Related ADRs: [ADR-012](../adr/012-phoneprep-coverage-and-sidecars.md)
- Implementation CRs: none currently open
- Downstream: `docs/akkapros/mbrola-voice-prep.md` describes the full TTS pipeline
  handoff to MBROLATOR.

# Non-Goals
- Does NOT record audio (human-performed or TTS-generated).
- Does NOT segment WAV files (planned future component).
- Does NOT compile a MBROLA voice binary; that is performed by MBROLATOR (external).
- Does NOT target non-Akkadian phoneme inventories without explicit CLI overrides.

# Security / Safety Considerations
- The HTML recording assistant is a static file; it does not contact external servers.
- `--output` path should be validated to avoid directory traversal when called from
  automated scripts.
