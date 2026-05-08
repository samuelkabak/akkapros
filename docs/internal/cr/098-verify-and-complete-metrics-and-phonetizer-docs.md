---
cr_id: CR-098
status: Done
priority: Medium
impact: Additive
created: 2026-05-08
updated: 2026-05-08
implements: ''
---

# Change Request: Verify and Complete Metrics and Phonetizer Documentation

# Summary

Verify that `docs/akkapros/metrics-computation.md` and `docs/akkapros/phonetizer-algorithm.md` accurately describe the current implementation, and update them where information is missing, incorrect, or stale. This is a documentation-only CR: no production code, test code, or governance records are to be modified.

The two target docs were last updated incrementally through CR-051, CR-064, CR-065, CR-078, CR-079, CR-080, and CR-094, but several implementation changes since then (CR-082 through CR-097) may have introduced gaps or inaccuracies that the docs do not reflect.

---

# Motivation

- User-facing documentation must describe the actual behavior of the toolkit, not an earlier version of it.
- `metrics-computation.md` and `phonetizer-algorithm.md` are the primary research-facing references for how the toolkit computes rhythm metrics and assigns phone-row durations. Inaccuracies here mislead downstream users and reviewers.
- Several recent CRs (CR-082 corrective geminate coda ratio, CR-084 pre-pausal final anchors, CR-085 global duration scale, CR-088/089 emphatic coloring, CR-093/096 mono-mode accentuation lengthening, CR-094 metrics split, CR-095 drift tolerance in durations bloc) changed implementation details that the docs may not fully capture.
- This CR is a normal documentation maintenance task and does not require a new ADR or REQ.

---

# Scope

## Included

- `docs/akkapros/metrics-computation.md`: verify every section against the current implementation in `src/akkapros/lib/_metrics_stats.py`, `src/akkapros/lib/_metrics_output.py`, and `src/akkapros/lib/metrics.py`.
- `docs/akkapros/phonetizer-algorithm.md`: verify every section against the current implementation in `src/akkapros/lib/phonetize.py` and `src/akkapros/lib/_phonetize_config.py`.
- Update the two docs to match current behavior. Add missing details, correct wrong statements, remove stale references.
- Run `python scripts/sync_doc_flowcharts.py` (or the equivalent flowchart sync mechanism) to regenerate any Mermaid flowcharts that need updating.
- Run `python scripts/update-indexes.py` if any governance records are added or renamed (not expected for this CR, but verify).

## Not Included

- No changes to `src/`, `tests/`, `scripts/`, `demo/`, or any other non-documentation files.
- No new governance records (ADRs, REQs, CRs) beyond this CR itself.
- No changes to `docs/internal/` governance files.
- No changes to other user-facing docs (`docs/akkapros/`) beyond the two target files.

---

# Current Behavior

## metrics-computation.md

The doc describes:
- Interval-based phone-driven metrics from paired `_ophone.txt` and `_phone.txt` inputs.
- Normalization to V/C/P interval classes, coalescence, rhythm formulas (%V, %C, meanV, meanC, ΔV, ΔC, VarcoV, VarcoC, rPVI-C, nPVI-V).
- Structural statistics (syllable, word, mora, merge, accentuation, prominence).
- Unit drift reporting and phonetizer diagnostics.
- Speech metrics (total duration, pause duration, articulate duration, pause ratio, WPM).

Known gaps to verify:
1. The `compute_interval_metrics` function in `_metrics_stats.py` uses `_population_std_dev` (divides by N, not N-1) for ΔV and ΔC. The doc says "population_standard_deviation" — confirm this is correct.
2. The `VarcoV` and `VarcoC` formulas in the doc use `(ΔV / meanV) * 100` — verify against code at line 1095-1096 of `_metrics_stats.py`.
3. The `rPVI-C` and `nPVI-V` formulas — verify against `_rpvi` and `_npvi` implementations.
4. The doc mentions `%C` in the rhythm formulas section but the code computes `percent_c` as `(sum(consonantal) / total_duration) * 100` — verify this is documented.
5. The "Structural Statistics" section mentions prominence statistics with `function_word_count` and `explicit_word_link_count` — verify these match `build_prominence_statistics` and `_prominence_counts_from_phone_rows`.
6. The "Unit Drift Reporting" section lists diagnostic fields — verify against `_extract_phonetizer_diagnostics` field specs (lines 1114-1134 of `_metrics_stats.py`). The code now also supports `adjusted_non_accented_long_vowel_count`, `shortened_non_accented_long_vowel_count`, `lengthened_non_accented_long_vowel_count` — are these documented?
7. The "Word Counts" section describes how word counts are derived — verify against `process_phone_pair` and `reconstruct_tilde_from_phone_rows`.

## phonetizer-algorithm.md

The doc describes:
- Phase 1 row building from `_tilde.txt` input.
- Phase 2 duration solver with drift cursor, synchronization basis, accentuation routing, long-vowel recovery, pause realization, resync pauses.
- Phase 3 intonation assignment.
- Hiatus and vowel transition processing.
- Unit drift reporting and metrics handoff.

Known gaps to verify:
1. **Synchronization basis** (lines 143-148 of the doc): says accentuated stream with `mora_mode = bi` uses `cvc_reference`, accentuated with `mora_mode = mono` uses `0.5 * cvc_reference`, original stream uses `0.5 * cvc_reference`. Verify against `_resolve_synchronization_basis` (lines 568-579 of `_phonetize_config.py`): the code returns `cvc_reference / 2.0` for both `allow_accentuation=False` and `mora_mode == 'mono'`, and `cvc_reference` for `allow_accentuation=True` with `mora_mode == 'bi'`. This matches the doc.
2. **Mono-mode accentuation** (CR-093/096): the doc mentions `basic_accentuation_lengthening` at line 149 but the main accentuation section (lines 510-545) only describes the bimoraic model. The doc should describe mono-mode accentuation routing where `total_increment = basic_accentuation_lengthening` (default 50 ms) instead of `round_half_up(0.5 * cvc_reference)`. See `_apply_accent_increment` call at lines 1486-1494 of `phonetize.py`.
3. **Pre-pausal final anchors** (CR-084): the doc mentions `coda_final`, `short_final`, `long_final` at lines 398-400 but should verify the description matches the code at `_consonant_anchor` (lines 819-837) and `_vowel_anchor` (lines 852-863) of `phonetize.py`. The doc says "If the immediately following realized unit is a punctuation-owned short or long pause" — verify this matches `_pause_row_triggers_final_anchors` (lines 87-93).
4. **Global duration scale** (CR-085): the doc does not mention `duration_scale` at all. The code applies scale via `_scale_duration_values` and `_derive_effective_durations`. The doc should mention that all numeric duration leaves are scaled by the global `duration_scale` factor (default 1.0, no-op).
5. **Corrective geminate coda ratio** (CR-082): the doc mentions `geminate_policy = corrective` at lines 406-410 but should verify the description of `geminate_coda_ratio` matches the code at lines 1268-1273 of `phonetize.py`.
6. **Emphatic vowel coloring** (CR-088/089): the doc mentions the vowel-coloring pass at lines 71-74 but should verify the description matches `_apply_emphatic_vowel_coloring` (lines 455-488 of `phonetize.py`), especially the coda-driven extension and `limit_emphatic_coloring` flag.
7. **Drift tolerance in durations bloc** (CR-095): the doc mentions `drift_tolerance = 19` at line 121 but should verify this is now under `timing_model.durations.drift_tolerance` and is subject to the global scale.
8. **Accentuation routing** (lines 510-545): the doc says "short vowels are not accentuation targets" and lists the policy family. Verify the `_apply_accent_increment` function: it uses `_primary_accent_index` and `_adjacent_accent_index` to determine which segments receive the increment. The doc should also describe the mono-mode path.
9. **Resync pause** (lines 568-601): the doc says `enable_resync_pause` defaults to false. Verify against the schema at line 109-113 of `_phonetize_config.py`: default is `False`. The doc should mention this toggle.
10. **Phase 3 intonation** (lines 666-683): the doc says the original stream "shares pause-governed contour assignment for question, statement, exclamation, and continuation pauses." Verify against `realize_row_intonation` (lines 937-977 of `phonetize.py`): the function applies pause-governed intonation to both streams regardless of the `accentuated` flag, but stress intonation is exclusive to the accentuated stream. This matches the doc.
11. **Unit drift reporting** (lines 686-711): the doc lists diagnostic fields. Verify against the return dict of `realize_phone_rows` (lines 1619-1655 of `phonetize.py`). The code now also returns `adjusted_non_accented_long_vowel_count`, `shortened_non_accented_long_vowel_count`, `lengthened_non_accented_long_vowel_count` — are these documented?
12. **Worked examples** (lines 603-663): verify the `qat` example (286 ms total, -14 ms drift) against the current default config values (closure onset=89, sonorant coda=87, short vowel=110, cvc_reference=300). The example uses `qat` where `q` is closure (89), `a` is short vowel (110), `t` is sonorant coda (87) = 286 ms. Target is 300 ms. Drift = 286 - 300 = -14 ms. This matches.
13. **Hiatus and vowel transition** (lines 257-335): verify the description matches `_consonant_anchor` (lines 819-837) and the special realization config values (hiatus=35, vowel_transition=25). The doc says hiatus uses closure timing class and vowel transition uses sonorant timing class — verify against `_consonant_timing_key` (lines 809-816).

---

# Proposed Change

Update the two target documentation files to accurately reflect the current implementation. Specific changes:

## metrics-computation.md

1. **Rhythm Formulas section**: Verify and if needed correct the formula notation for `%C` (it is documented but should be explicit). Ensure the formulas match `compute_interval_metrics` exactly.
2. **Structural Statistics section**: Add documentation for the three new diagnostic fields `adjusted_non_accented_long_vowel_count`, `shortened_non_accented_long_vowel_count`, `lengthened_non_accented_long_vowel_count` if they are emitted in the output (they are in `_extract_phonetizer_diagnostics` but may not be rendered in `_metrics_output.py` — verify).
3. **Unit Drift Reporting section**: Verify the field list matches `_extract_phonetizer_diagnostics` exactly. Add any missing fields.
4. **General**: Verify all cross-references to code paths, file names, and function names are correct.

## phonetizer-algorithm.md

1. **Timeline Model section**: Add a subsection or note about the global `duration_scale` factor and how it affects all numeric duration leaves.
2. **Accentuation Routing section**: Add description of mono-mode accentuation routing where `total_increment = basic_accentuation_lengthening` (default 50 ms) instead of `round_half_up(0.5 * cvc_reference)`. Clarify that the policy family and distribution mechanics are the same.
3. **Step Order section**: Verify the description of `geminate_policy = corrective` with `geminate_coda_ratio` matches the code. The doc currently says "the coda receives `pair_total * geminate_coda_ratio` and the onset receives the exact remainder" — verify this is accurate.
4. **Pre-pausal final anchors**: Verify the description of when `coda_final`, `short_final`, `long_final` are used matches `_pause_row_triggers_final_anchors`. The doc says "punctuation-owned short or long pause" — verify resync pauses are excluded.
5. **Emphatic vowel coloring**: Verify the description of the vowel-coloring pass matches `_apply_emphatic_vowel_coloring`, especially the coda-driven extension and `limit_emphatic_coloring` flag behavior.
6. **Resync Pauses section**: Add a note that `enable_resync_pause` defaults to `False` and must be explicitly enabled.
7. **Unit Drift Reporting section**: Add the three new diagnostic fields if they are emitted.
8. **Worked Examples**: Verify all numeric examples against current default config values. Update if defaults have changed.
9. **Hiatus and Vowel Transition Processing section**: Verify the description of timing class inheritance and special realization anchors matches the code.

---

# Technical Design

No architectural changes. This is a documentation audit and update.

**Verification methodology:**
1. For each section of each doc, read the corresponding implementation code and compare.
2. For formula sections, trace the exact computation path in the code and compare to the doc's mathematical notation.
3. For config-dependent sections, check the default config values in `_phonetize_config.py` and compare to any hardcoded numbers in the doc.
4. For flowchart sections, run the flowchart sync script to regenerate from the current workflow data.
5. For diagnostic field lists, compare the doc's list against the actual return dict keys in the code.

---

# Files Likely Affected

- `docs/akkapros/metrics-computation.md` — update to match current implementation
- `docs/akkapros/phonetizer-algorithm.md` — update to match current implementation

---

# Acceptance Criteria

- [x] `docs/akkapros/metrics-computation.md` accurately describes the current interval metrics computation, including all rhythm formulas, structural statistics, unit drift reporting, and phonetizer diagnostics.
- [x] `docs/akkapros/phonetizer-algorithm.md` accurately describes the current phonetizer algorithm, including Phase 1/2/3, synchronization basis, mono-mode accentuation, pre-pausal final anchors, global duration scale, corrective geminate coda ratio, emphatic vowel coloring, resync pause toggle, and all diagnostic fields.
- [x] All numeric examples in the worked-examples section of `phonetizer-algorithm.md` are verified against current default config values.
- [x] All Mermaid flowcharts in both docs are regenerated from current workflow data (run flowchart sync script).
- [x] No production code, test code, or governance records were modified.
- [x] Both docs pass Markdown link checking (run `python scripts/check_md_links.py`).

---

# Risks / Edge Cases

- The flowchart sync script may not exist or may have a different name. Check `scripts/` for the correct tool. If no automated flowchart sync exists, the flowcharts may need manual verification against the code.
- Some diagnostic fields listed in the code's return dict may not be rendered in the human-readable output (`_metrics_output.py`). The doc should describe what is actually emitted, not just what the code computes internally.
- The doc may reference intermediate file formats or pipeline stages that have been renamed or removed. Each reference must be verified.

---

# Testing Strategy

No tests are needed for this documentation-only CR. Verification is manual:
1. Read each doc section and compare against the corresponding implementation code.
2. Run `python scripts/check_md_links.py` to verify Markdown links.
3. Run the flowchart sync script if one exists.
4. Review the final diff for accuracy.

---

# Rollback Plan

Revert the two doc files to their pre-CR state using `git checkout HEAD -- docs/akkapros/metrics-computation.md docs/akkapros/phonetizer-algorithm.md`.

---

# Related Issues

- CR-051: Align and enrich research-facing package documentation
- CR-064: Correct user-facing docs and remove internal governance references
- CR-065: Add code-derived Mermaid flowcharts to user-facing docs
- CR-078: Document hiatus and vowel transition processing
- CR-079: Add pause-governed intonation to ophone
- CR-080: Add half-beat synchronization for mono and ophone
- CR-082: Add corrective geminate coda share ratio
- CR-084: Add pre-pausal final duration anchors
- CR-085: Add global duration scale to phonetizer timing model
- CR-088: Extend emphatic vowel coloring to coda contexts
- CR-089: Rename extended_emphatic_coloring to limit_emphatic_coloring
- CR-093: Configurable mono-mode accentuation lengthening
- CR-094: Split metrics.py
- CR-095: Move drift_tolerance into durations bloc
- CR-096: Rename mono_mode_accentuation_lengthening to basic_accentuation_lengthening

---

# Tasks

## Documentation Audit

- [x] Audit `docs/akkapros/metrics-computation.md` against current implementation
- [x] Audit `docs/akkapros/phonetizer-algorithm.md` against current implementation

## Documentation Updates

- [x] Update `docs/akkapros/metrics-computation.md` with corrections and additions
- [x] Update `docs/akkapros/phonetizer-algorithm.md` with corrections and additions

## Verification

- [x] Regenerate Mermaid flowcharts (run flowchart sync script)
- [x] Run `python scripts/check_md_links.py` to verify links
- [x] Review final diff for accuracy

---

# Implementation Blockers

No blockers known.

---

# Notes

## Detailed Audit Checklist for metrics-computation.md

### Rhythm Formulas (lines 78-105)
- [ ] `%V = (sum(V) / Total) * 100` — verify against `compute_interval_metrics` line 1089
- [ ] `%C = (sum(C) / Total) * 100` — verify against line 1090
- [ ] `meanV = arithmetic_mean(V)` — verify against `_mean` (line 1014-1015)
- [ ] `meanC = arithmetic_mean(C)` — same
- [ ] `ΔV = population_standard_deviation(V)` — verify against `_population_std_dev` (lines 1005-1011): divides by N, not N-1
- [ ] `ΔC = population_standard_deviation(C)` — same
- [ ] `VarcoV = (ΔV / meanV) * 100` — verify against line 1095
- [ ] `VarcoC = (ΔC / meanC) * 100` — verify against line 1096
- [ ] `rPVI-C = mean(abs(C[k] - C[k+1]))` — verify against `_rpvi` (lines 1018-1022)
- [ ] `nPVI-V = 100 * mean(abs((V[k] - V[k+1]) / ((V[k] + V[k+1]) / 2)))` — verify against `_npvi` (lines 1025-1038)
- [ ] Fallback rules: "fewer than two intervals -> Δ and the PVI metric report 0" — verify against lines 1093-1098

### Structural Statistics (lines 150-203)
- [ ] Verify prominence statistics description matches `build_prominence_statistics` (lines 1482-1499)
- [ ] Verify speech metrics fields match `compute_speech_metrics_from_rows` (lines 979-1000)
- [ ] Verify the doc says "The older synthetic `Speech rate (...)`, standalone `Pause metrics:`, and `Pause duration allocation` blocks are no longer part of the active metrics contract" — confirm this is still accurate

### Unit Drift Reporting (lines 205-226)
- [ ] Verify field list against `_extract_phonetizer_diagnostics` (lines 1112-1145)
- [ ] Check if `adjusted_non_accented_long_vowel_count`, `shortened_non_accented_long_vowel_count`, `lengthened_non_accented_long_vowel_count` are documented (they are in the code's field_specs but may not be rendered in output)

## Detailed Audit Checklist for phonetizer-algorithm.md

### Timeline Model (lines 134-187)
- [ ] Verify synchronization basis description matches `_resolve_synchronization_basis` (lines 568-579)
- [ ] Verify nominal non-accentuated targets (CV, CVC, CVV, CVVC) match `_shape_reference` (lines 1039-1053)
- [ ] Verify accentuated shapes add `0.5 * cvc_reference` — matches `_shape_reference` line 1052
- [ ] Add description of mono-mode: `basic_accentuation_lengthening` instead of `0.5 * cvc_reference`
- [ ] Add description of global `duration_scale`

### Step Order (lines 391-468)
- [ ] Verify step 4 (geminate policy) description matches code at lines 1268-1277
- [ ] Verify drift folding formula (lines 424-429) matches `_normalize_drift_to_nearest_branch` (lines 906-915)
- [ ] Verify accent increment formula (lines 445-453) matches `_apply_accent_increment` (lines 1169-1249)
- [ ] Verify long-vowel cleanup description (lines 455-463) matches code at lines 1523-1550

### Accentuation Routing (lines 510-545)
- [ ] Verify `AA = round_half_up(0.5 * cvc_reference)` matches `_round_half_up` (lines 900-903)
- [ ] Verify policy family list matches `ACCENTUATION_DISTRIBUTION_SHARES` (lines 18-26 of `_phonetize_config.py`)
- [ ] Verify default policy is `80_20` — matches line 103-108
- [ ] Verify primary/adjacent routing by accent shape matches `_primary_accent_index` and `_adjacent_accent_index`
- [ ] Add mono-mode routing description

### Resync Pauses (lines 568-601)
- [ ] Verify resync band defaults (100-200) match config at lines 220-224
- [ ] Add note about `enable_resync_pause` defaulting to `False`

### Unit Drift Reporting (lines 686-711)
- [ ] Verify field list against `realize_phone_rows` return dict (lines 1619-1655)
- [ ] Check if `adjusted_non_accented_long_vowel_count`, `shortened_non_accented_long_vowel_count`, `lengthened_non_accented_long_vowel_count` are documented

### Worked Examples (lines 603-663)
- [ ] Verify `qat` example (286 ms, -14 ms drift) against current defaults
- [ ] Verify resync-pause examples against current defaults
- [ ] Verify the resync pause row format example (line 662) matches `_new_resync_pause_row` (lines 537-551)

---

# Handoff Summary

This CR is ready for implementation. The implementing agent (`@change`) should:

1. Read both target docs in full.
2. Read the relevant implementation files (`_metrics_stats.py`, `_metrics_output.py`, `phonetize.py`, `_phonetize_config.py`) to verify each section.
3. Apply corrections and additions to both docs.
4. Regenerate flowcharts if the sync script exists.
5. Verify Markdown links.
6. Do NOT modify any production code, test code, or governance records.

Implementation is explicitly deferred to a later `@change` agent invocation.

# Revision History

- 2026-05-08: Initial draft
- 2026-05-08: Documentation audit and updates completed. All AC verified. Status set to Done.
