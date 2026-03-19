# Requirement: Rhythmic Metrics Computation

REQ-ID: REQ-004
Status: Implemented
Priority: High
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall compute a set of quantitative rhythmic and structural metrics from
prosody-realized pivot text (`*_tilde.txt`) without requiring audio recordings.
It shall report metrics for both the original (non-accentuated) and accentuated
text so that the effect of prosody realization can be compared.  Results shall be
output in one or more of three formats: human-readable table, JSON, and CSV.
The computation shall support configurable pause-ratio and speech-rate parameters,
and batch processing of multiple input files.

---

# Motivation

Research must establish quantitatively that Akkadian text patterns with stress-timed
languages (VarcoC ≈ 69–72), not syllable-timed (VarcoC ≈ 50–55) or mora-timed
(VarcoC ≈ 35–40). Because no audio recordings of ancient Akkadian exist, metrics
must be derived from symbolic text using explicit mora-duration assumptions. Reporting
dual metrics (original and accentuated) isolates the contribution of the prosody
realization algorithm. The %V pause correction is required to make text-derived %V
comparable to values measured from living languages (research note 041).

---

# Acceptance Criteria

## Metric Families

- [ ] The system computes `Total syllables` by counting syllable nuclei in the pivot text.
- [ ] The system classifies every syllable into one of the eight canonical types:
      CV, CVC, CVV, CVVC, VC, V, VV, VVC and reports their counts and percentages.
- [ ] The system computes total morae for both original and accentuated text.
- [ ] The system computes `%V (pause-excluded)` = vowel morae / total morae × 100.
- [ ] The system computes `%V (pause-corrected)` using the configured pause ratio (default 35%).
- [ ] The system computes `ΔC` (standard deviation of consonantal intervals in morae).
- [ ] The system computes `MeanC` (arithmetic mean of consonantal intervals in morae).
- [ ] The system computes `VarcoC` = ΔC / MeanC × 100 (rate-normalized, unitless).
- [ ] `ΔC` and `MeanC` are also reported in seconds, derived from mora duration.
- [ ] The system computes merge statistics: words merged, prosodic units formed,
      average merged-unit size.
- [ ] The system computes accentuation statistics: accentuation rate (%), breakdown
      by accentuation type (vowel lengthening, coda gemination, onset gemination).
- [ ] The system estimates speech rate (words per minute), syllables per second,
      mora duration, and word duration from WPM parameter.
- [ ] Pause budget is split into `short_pauseable_boundaries` and
      `long_pauseable_boundaries`; long-pause weight is configurable (`--long-punct-weight`).
- [ ] Short pause durations are corrected to even-mora values (bimoraic correction).
- [ ] All metrics are reported for BOTH sections: original and accentuated.

## Output Formats

- [ ] `--table` produces `<prefix>_metrics.txt`, a human-readable text table.
- [ ] `--json` produces `<prefix>_metrics.json`.
- [ ] `--csv` produces `<prefix>_metrics.csv`.
- [ ] If no format flag is given, `--table` is enabled automatically.
- [ ] Batch mode: `--input-list <file>` accepts a file with one input path per line
      and processes all files, writing combined/merged output.
- [ ] `--test` runs the built-in test suite and exits with code 0 on pass.

## Parameterisation

- [ ] `--wpm <float>`: words per minute for speech-rate estimation (default: 165).
- [ ] `--pause-ratio <float>`: pause percentage of total time (default: 35).
- [ ] `--long-punct-weight <float>`: weight of long pauses vs short (default: 2.0).
- [ ] `--extra-consonants` and `--extra-vowels` extend character recognition.

---

# User Story (optional)
> As a historical linguist, I want to compare the VarcoC of original and accentuated
> Akkadian text against published values for English (70–80) and French (50–55)
> so that I can confirm or refute the stress-timed classification.

---

# Interface Notes
- Input: `<prefix>_tilde.txt` (prosody-realized pivot).
- Outputs: `<prefix>_metrics.txt`, `<prefix>_metrics.json`, `<prefix>_metrics.csv`.
- Affected components: `src/akkapros/cli/metricalc.py`, `src/akkapros/lib/metrics.py`.
- CLI: `python src/akkapros/cli/metricalc.py <tilde.txt> --table --json --csv -p <prefix>`

---

# Open Questions
- [ ] Should bootstrap confidence intervals be added for VarcoC to support statistical
      reporting in publications? (Research note 043 currently omits them on the
      grounds that the corpus is large and the key sensitivity is the pause-ratio
      assumption, not sampling variance.)
- [ ] Should the mora-to-seconds mapping be user-configurable rather than derived
      from `--wpm`?
- [ ] TO_BE_CONFIRMED: is the dual %V design (ADR-010) the final arrangement for
      CSV column headers after the accentuation rename (CR-004)?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature)
- Note: After CR-004 (accentuation rename), all JSON/CSV keys and table headings must
  use `accentuated` in place of `repaired`.

# Related
- Related ADRs: [ADR-010](../adr/010-metrics-from-text-and-dual-percent-v.md),
  [ADR-017](../adr/017-pause-modeling-and-bimoraic-correction.md)
- Implementation CRs: [CR-002](../cr/002-fix-mora-stats-with-tilde/),
  [CR-004](../cr/004-rename-repair-to-accentuation/)

# Non-Goals
- Does NOT compute F0 (fundamental frequency), intensity, or duration from real audio.
- Does NOT perform statistical significance testing between languages (addressed in
  external research publications, not in the toolkit itself).
- Does NOT validate that VarcoC falls in any particular range; it computes and reports.

# Security / Safety Considerations
- Batch mode reads file paths from a list file; callers must ensure the list is from
  a trusted source to prevent path traversal if paths are user-supplied.
