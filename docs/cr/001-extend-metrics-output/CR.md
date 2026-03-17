# Change Request: Extend metrics output (table, JSON, CSV) and speech-rate fields

CR-ID: CR-001
Status: Done
Priority: Medium
Created: 2026-03-16
Updated: 2026-03-16

---

# Summary

Add additional mora and speech-rate related fields to the metrics outputs (human table, JSON and CSV) and rearrange the table layout so that speech-rate sections appear before acoustic metrics for both original and repaired text. The change requires small additions to the metrics computation and to the three output formatters.

In short: expose total mora counts (original and repaired), compute and expose speech metrics for the original text (not just repaired), show ΔC and MeanC both in mora units and in seconds (using the corresponding `mora_duration`), and move/rename the speech-rate section in the human table.

---

# Motivation

Researchers and downstream tools require explicit total mora counts and consistent speech-rate diagnostics for both original and repaired texts. Presenting ΔC/MeanC only in mora units hides an important, human-readable time-scale interpretation. Moving the speech-rate block earlier in the table groups timing-related outputs together and improves readability.

---

# Scope

## Included

- Add total mora count to the statistics returned by `analyze_text()` (for original and repaired analyses), as `mora_stats['total']`
- Compute `speech` metrics for the original text (currently only repaired speech is computed)
- Extend the human table formatter to:
  - show `Total morae number:` after `Std dev morae per syllable:` (original and repaired)
  - show `Speech rate (original):` before `Acoustic metrics (original):`
  - show `Speech rate (repaired):` before `Acoustic metrics (repaired):` (rename)
  - show ΔC and MeanC with both mora and seconds notation using the corresponding `mora_duration`
- Extend CSV output to include the new fields (total morae, original speech metrics, ΔC/MeanC in seconds)
- Ensure JSON output contains the new fields (no pruned information removed)
- Add/update unit tests, and update CLI help/docs where appropriate

## Not Included

- Changing any downstream data consumers (external scripts) — those will consume the new JSON/CSV shape separately
- Changing default CLI flags for output format selection

---

# Current Behavior

- `analyze_text()` returns `mora_stats` with `mean` and `std` but does not return the total mora count array or total morae number.
- `process_filetext()` computes `speech` metrics only for repaired text.
- `format_table()` prints `Acoustic metrics (original)` before any speech-rate block and prints the repaired `speech` block after `Acoustic metrics (repaired)`; it does not show total morae number.
- `format_csv()` and JSON output do not provide mora totals or ΔC/MeanC in seconds.

---

# Proposed Change

1. Update `analyze_text()` to compute and return total morae (the sum of `morae_list`) alongside `mora_stats`, using the key `mora_stats['total']`.

2. Update `process_filetext()` to compute `speech` metrics for the original preprocessed text (call `compute_speech_rate(preprocessed_original, original_stats, wpm, pause_ratio)`) and attach it to `result['original']['speech']` (parallel to `result['repaired']['speech']`).

3. In `format_table()`:
   - Print `Speech rate (original):` (using `result['original']['speech']`) immediately before `Acoustic metrics (original):` and include the same indicators currently displayed for repaired speech.
   - After the existing `Std dev morae per syllable:` line (original and repaired), add `  Total morae number: <int>` using the new `mora_stats['total']` value.
   - Move the repaired speech-rate block so it appears before `Acoustic metrics (repaired):`, and rename its title to `Speech rate (repaired):`.
   - Update the ΔC and MeanC display lines (original and repaired) to append the corresponding time in seconds:
       ΔC: <deltaC_mora> mora (<deltaC_mora * mora_duration> s) (consonant-interval SD)
       MeanC: <meanC_mora> mora (<meanC_mora * mora_duration> s) (mean consonant interval)
     Use `mora_duration` from the corresponding `speech` object (`original['speech']['mora_duration']` and `repaired['speech']['mora_duration']`). When `mora_duration` is zero or unavailable, omit the seconds part or use `0.000 s`.

4. In `format_csv()`:
  - Add rows for `original_total_morae` and `rep_total_morae`.
  - Add original speech metrics rows: `orig_sps_speech`, `orig_sps_articulation`, `orig_syllable_duration`, `orig_mora_duration`, `orig_word_duration`.
  - Keep repaired speech rows and add prefixed equivalents for symmetry: `rep_sps_speech`, `rep_sps_articulation`, `rep_syllable_duration`, `rep_mora_duration`, `rep_word_duration`.
  - Add ΔC/MeanC-in-seconds rows for both original and repaired: `ΔC_seconds`, `MeanC_seconds`, `rep_ΔC_seconds`, `rep_MeanC_seconds`.

5. In JSON output (produced by `metricalc.py --json`): ensure the new `original['speech']` block and `mora_stats['total']` fields are present and not pruned by the existing `json` pruning logic. Update the pruning helper if necessary to avoid removing the new fields.

6. Update unit tests and add a new test case that asserts the presence and correctness (non-negativity / numeric type) of the new fields in the returned `process_filetext()` structure and in the formatted table/CSV lines.

7. Update documentation to reflect the new outputs and table layout. Specifically update:
  - `docs/akkapros/metrics-computation.md` — add definitions and equations for `total_morae`, and explain ΔC/MeanC in seconds using `mora_duration`.
  - `docs/akkapros/metricalc.md` — update CLI examples and output descriptions to list the new fields and the changed table ordering.
  - README and any CLI help examples that mention output field names or CSV/JSON schema.

---

# Technical Design

Files to update (primary):

- `src/akkapros/lib/metrics.py`
  - `analyze_text()` — compute `mora_stats['total']` and keep `morae_list` internal or return its sum.
  - `process_filetext()` — compute `speech` for original and attach to `result['original']['speech']`.
  - `compute_acoustic_metrics()` can remain unchanged; seconds are computed in formatters using `mora_duration`.
  - `format_table()` — re-order and augment the printed table as described.
  - `format_csv()` — add new CSV rows.

- `src/akkapros/cli/metricalc.py`
  - JSON pruning helper — ensure we do not remove the new `speech`/`mora_stats['total']` fields.
  - CLI help text examples (optional) to show new outputs.

- Tests: tests exercising metrics and formatters

Data flow notes:

- `analyze_text()` already computes per-syllable morae (via `morae_list`). Add a sum and insert into `mora_stats['total']`.
- `compute_speech_rate()` computes `mora_duration` based on `stats['mora_stats']['mean']`. For `original['speech']`, call `compute_speech_rate(preprocessed_original, original_stats, ...)` and then display `mora_duration` accordingly.

Backward compatibility:

- Adding `mora_stats['total']` and `original['speech']` are additive changes and should be backward compatible. The CSV/JSON schema will change; document the change in release notes.

---


# Files Likely Affected

src/akkapros/lib/metrics.py
src/akkapros/cli/metricalc.py
docs/akkapros/metrics-computation.md
docs/akkapros/metricalc.md
docs/README.md (if CLI docs mention metrics outputs)

---

# Acceptance Criteria

- [ ] `process_filetext()` returns `original['speech']` with the same keys as `repaired['speech']`.
- [ ] `analyze_text()` returns `mora_stats['total']` as integer sum of morae.
- [ ] `format_table()` shows `Total morae number:` after `Std dev morae per syllable:` for both original and repaired.
- [ ] `format_table()` shows `Speech rate (original):` before `Acoustic metrics (original):` and `Speech rate (repaired):` before `Acoustic metrics (repaired):`.
- [ ] ΔC and MeanC lines show both mora and seconds (seconds computed using the respective `mora_duration`).
- [ ] CSV output includes `original_total_morae`, `rep_total_morae`, original speech metrics rows, and ΔC/MeanC in seconds rows.
- [ ] JSON output includes `original['speech']` and `mora_stats['total']`.
- [ ] Unit tests added and passing.

---

# Risks / Edge Cases

- If `mora_stats['mean']` is zero, `mora_duration` may become infinite or 0; formatters must guard against division by zero and display `0.000 s` or omit seconds.
- Consumers of JSON/CSV may need updates; document schema changes clearly in release notes.

---

# Testing Strategy

- Add unit tests for `analyze_text()` verifying `mora_stats['total']` matches expected sums from small synthetic inputs.
- Add unit tests for `process_filetext()` verifying `original['speech']` exists and numeric.
- Add tests for `format_table()` to verify ordering and presence of the new lines.
- Add CSV output test that checks for presence of the new CSV rows.

---

# Rollback Plan

Revert the changes in a single commit if issues are discovered; because the change is additive, rollback should restore previous CSV/JSON shapes.

---

# Related Issues

- Metrics output improvements discussion
- Documentation tasks for CLI examples
