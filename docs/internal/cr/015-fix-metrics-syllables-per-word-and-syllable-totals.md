# Change Request: Fix Metrics Pivot Integrity for Syllable Totals, Linked Words, and Diphthongs

CR-ID: CR-015
Status: Done
Priority: High
Impact: Mutative
Created: 2026-03-25
Updated: 2026-03-25
Implements: ADR-009, ADR-010, ADR-014, REQ-003, REQ-004
---

# Summary

Fix the `_tilde.txt` pivot contract so metrics and print both consume the same fully informative representation.

The consolidated change covers three connected bugs:

- incorrect syllable totals and `syllables_per_word` auditability
- unsyllabified linked function words in `_tilde`
- diphthong-marker loss between prosody, metrics, and print

The root causes are in the pivot serialization layer. Function words were previously flattened in `prosody.py`, and diphthong restoration collapsed the `¨` marker too early, before metrics and print consumed the `_tilde` stage. This CR preserves syllable structure at the source, keeps restored diphthong memory in `_tilde`, removes the metrics-side repair fallback, and updates print to drop `¨` only at final display time.

---

# Motivation

- Root-cause bug fix
- Pipeline integrity
- Remove downstream masking behavior
- Keep one authoritative pivot contract across metrics and print

The prosody-realized pivot format is the contract between stages. If `_tilde.txt` contains unsyllabified Akkadian words or loses diphthong structure before downstream consumers read it, the pipeline is internally inconsistent and the reported outputs are harder to trust. Metrics must not silently repair prosody output that should already be valid, and print must not guess syllable structure that the pivot stage has already erased.

---

# Scope

## Included

- Diagnose the mismatch between visible syllable counts and `syllables_per_word`
- Preserve syllable separators for function words written into `_tilde.txt`
- Preserve restored diphthong memory markers (`¨`) in `_tilde.txt`
- Remove metrics-layer re-syllabification of linked chunks
- Classify valid restored diphthong syllables without falling into `OTHER`
- Ensure print removes `¨` only at final rendering time so accent spans stay syllable-correct
- Surface all counted syllables consistently across text, JSON, and CSV outputs
- Add built-in self-tests and pytest coverage for small-corpus metric consistency and `%V` fallback safety
- Regenerate affected reference outputs

## Not Included

- Changing the function-word inventory itself unless tests prove it is incomplete
- Changing the merge policy from ADR-009
- Changing printer emphasis conventions unrelated to syllable preservation
- Rewriting the pause model or speech-rate model

---

# Current Behavior

When function words participate in prosodic groups, `prosody.py` writes them without internal separators. Restored diphthongs also lose their internal `¨` marker before `_tilde` reaches metrics or print. Example checked-in outputs currently include forms like:

- `ana+i·lī`
- `ina+bi·rī·šu·nu`
- `u+ana+ina+šar·ri`
- `tiā~m·tu`

These are not faithful serializations of the syllabified input. Metrics then encounters hidden noncanonical syllables, and print can bold the wrong span because a diphthong-internal syllable break has already been erased.

---

# Proposed Change

- Serialize merged function words with their syllabified text, not flattened text
- Keep `_tilde.txt` as a proper syllabified pivot format even across `+` links
- Restore diphthongs into `_tilde` with `¨` preserved, for example `ti¨ā~m·tu`
- Remove downstream metrics recovery of missing syllable boundaries
- Teach metrics to treat `¨` as a syllable boundary marker for counting but not as a consonant in acoustic spacing
- Ensure valid restored diphthong syllables classify into existing moraic categories instead of `OTHER`
- Teach print to remove `¨` only after syllable-sensitive accent rendering
- Make `compute_percent_v_from_stats()` safe when cached mora totals are absent

---

# Technical Design

Components:

- `src/akkapros/lib/prosody.py`
- `src/akkapros/lib/metrics.py`
- `src/akkapros/lib/print.py`
- `tests/test_selftests_lib.py`
- `tests/test_metrics_stats.py`
- `tests/test_format_validation.py`
- integration reference metrics fixtures

Implementation details:

- Replace `get_text_flat()` with `get_text()` wherever function words are emitted into result parts for `_tilde` serialization
- Keep backward-merge rollback logic intact while preserving syllable markers in reconstructed groups
- Restore diphthongs into `_tilde` with `¨` kept as pivot memory instead of deleted at the prosody stage
- Remove metrics helper code that re-syllabifies bare segments after parsing `_tilde`
- Split metrics syllable analysis on `¨` and exclude `¨` from consonant/acoustic calculations
- Extend syllable classification so restored diphthong surface forms are mapped by mora profile instead of being treated as unknown
- Add `SYLLABLE_VOWEL_MORA_TOTAL` and derive fallback `%V` values from maintained mora constants instead of a stale local table
- Treat `¨` like a syllable boundary in print, then drop it from acute, bold, IPA, XAR, and MBROLA surface output
- Add `total_syllables` rows/lines where needed so ratios are auditable without recomputation from partial tables
- Add formula checks for:
  - total syllables = sum of syllable-count buckets
  - mean syllables per word = total syllables / total words
  - mean morae per word = total morae / total words
  - pause-per-syllable ratios = raw pause counts / total syllables
  - accentuation rate = accentuated syllables / original total syllables

---

# Files Likely Affected

src/akkapros/lib/prosody.py
src/akkapros/lib/metrics.py
src/akkapros/lib/print.py
tests/test_selftests_lib.py
tests/test_metrics_stats.py
tests/test_format_validation.py
tests/integration_refs/stage_pipeline/expected_e2e_tilde.txt
tests/integration_refs/stage_pipeline/expected_e2e_metrics.txt
tests/integration_refs/stage_pipeline/expected_e2e_metrics.json
tests/integration_refs/stage_pipeline/expected_e2e_metrics.csv
tests/integration_refs/stage_pipeline/expected_e2e_accent_bold.md
tests/integration_refs/fullprosmaker/expected_test_tilde.txt
tests/integration_refs/fullprosmaker/expected_test_metrics.txt
tests/integration_refs/fullprosmaker/expected_test.json
tests/integration_refs/fullprosmaker/expected_test.csv
tests/integration_refs/fullprosmaker/expected_test_accent_bold.md

---

# Acceptance Criteria

- [x] Reported `syllables_per_word.mean` is consistent with the counted total syllables and total words
- [x] `_tilde.txt` preserves syllable separators for Akkadian function words inside linked groups
- [x] `_tilde.txt` preserves restored diphthong memory markers such as `ti¨ā~m·tu`
- [x] Metrics no longer re-syllabifies linked Akkadian chunks as a fallback
- [x] Metrics counts diphthong-marked syllables without classifying them as `OTHER`
- [x] `compute_percent_v_from_stats()` remains correct even when cached mora totals are absent
- [x] Print removes `¨` only at rendering time and bolds the correct accentuated syllable span
- [x] Text metrics output exposes all counted syllables needed to audit the mean
- [x] CSV metrics output exposes all counted syllables needed to audit the mean
- [x] JSON metrics output remains internally consistent with text and CSV
- [x] Built-in metrics self-tests cover the corrected calculations
- [x] Pytest includes small-corpus metrics consistency, print regression, and `%V` fallback tests
- [x] Affected reference outputs are regenerated

---

# Risks / Edge Cases

- Existing checked-in `_tilde` references and metrics gold files will change
- Printer and other downstream consumers may expose slightly different linked surface strings because separators are now preserved
- `_tilde` reference files will now retain `¨` for restored diphthongs
- Restored diphthongs must remain classifiable even though their surface spelling differs from temporary split-stage notation
- Reference fixtures will change as soon as the metrics contract is corrected
- Any downstream tooling that assumed the old hidden-bucket or flattened-diphthong behavior may need minor adaptation

---

# Testing Strategy

Unit tests:

- Small-corpus formula consistency checks from `_proc` input through syllabify + prosody + metrics
- Direct prosody regression for merged function words retaining separators
- Direct regression for diphthong-marker propagation from prosody to metrics and print
- Built-in metrics self-tests for totals, ratios, surfaced output rows, and `%V` fallback safety

Integration tests:

- Existing stage-pipeline and fullprosmaker reference comparisons updated to the corrected outputs

Manual verification:

- Inspect representative `_tilde.txt` lines that previously contained `ana+i·lī`-style flattening
- Inspect representative diphthong lines that now retain `¨` in `_tilde` and bold only the accentuated syllable in print output

---

# Rollback Plan

Restore the previous prosody serialization and metrics fallback, then regenerate references. This would reintroduce the known pipeline inconsistency and should be used only as a temporary emergency rollback.

---

# Related Issues

- User-reported mismatch in `demo corpus-lob-p35_metrics.txt` for `Word statistics / Syllables per word`

---

# Tasks

## Implementation

- [x] Create CR-015
- [x] Fix prosody serialization for function words
- [x] Keep diphthong memory markers in `_tilde`
- [x] Remove metrics recovery fallback
- [x] Classify restored diphthong syllables without `OTHER`
- [x] Move `¨` deletion to print rendering
- [x] Fix metrics syllable analysis and surfaced totals
- [x] Update text, JSON, and CSV outputs consistently

## Tests

- [x] Add metrics self-test coverage for formula consistency
- [x] Add metrics self-test coverage for `%V` fallback safety
- [x] Add pytest small-corpus coverage
- [x] Add pytest diphthong print-mode coverage
- [x] Run targeted metrics and integration tests

## Documentation

- [x] Record the change in the CR
- [x] Regenerate the CR index

## Review

- [x] Verify `_tilde`, metrics, and print outputs against acceptance criteria

---

# Notes for CR-015

CR-015 is the single authoritative record for the connected pivot-format fixes that were initially implemented in multiple steps. The final design keeps `_tilde` information-complete, fixes the root cause upstream, and makes metrics fallbacks safe when cached totals are unavailable.
