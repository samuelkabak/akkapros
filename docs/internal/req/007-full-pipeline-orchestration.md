# Requirement: Full Pipeline Orchestration (fullprosmaker)

REQ-ID: REQ-007
Status: Implemented
Priority: High
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall provide a single CLI command (`fullprosmaker.py`) that executes the
complete Akkadian prosody pipeline — syllabification, prosody realization, metrics
computation, and output printing — in one invocation with a shared set of options (prefix,
output directory, extra phoneme symbols). All intermediate files shall be written so that
individual pipeline stages remain inspectable and rerunnable independently.

---

# Motivation

Running five separate CLI tools (atfparser, syllabifier, prosmaker, metricalc, printer)
with consistent flags across a full corpus analysis is tedious and error-prone. A
single orchestration command eliminates flag duplication and ensures that all stages
are applied with the same configuration. It also lowers the barrier for new users who
want immediate results from a raw ATF file.

The orchestrator does not replace individual CLIs; it is a convenience wrapper. Researchers
who want fine-grained control can still invoke stages separately.

---

# Acceptance Criteria

## Pipeline Order

- [ ] Stage 1 (syllabify): reads `<prefix>_proc.txt`, writes `<prefix>_syl.txt`.
- [ ] Stage 2 (prosody realization): reads `<prefix>_syl.txt`, writes `<prefix>_tilde.txt`.
- [ ] Stage 3 (metrics): reads `<prefix>_tilde.txt`, writes metric outputs if metric flags set.
- [ ] Stage 4 (print): reads `<prefix>_tilde.txt`, writes accent outputs if print flags set.
- [ ] Intermediate files `_syl.txt` and `_tilde.txt` are ALWAYS written, regardless of
      which optional stages are selected.

## Shared Options

- [ ] `--prefix` / `-p` propagates to all stages.
- [ ] `--outdir` propagates to all stages.
- [ ] `--extra-vowels` and `--extra-consonants` propagate to syllabifier and metrics.

## Syllabifier Options (prefixed `--syl-`)

- [ ] `--syl-merge-hyphens` maps to syllabifier `--merge-hyphen`.
- [ ] `--syl-merge-lines` maps to syllabifier `--merge-lines`.

## Prosody Options (prefixed `--prosody-`)

- [ ] `--prosody-style {lob,sob}` selects the accent hierarchy (default: `lob`).
- [ ] `--prosody-relax-last` enables + link relaxation.
- [ ] Diphthong restoration is always applied automatically; no separate flag required.

## Metrics Options (prefixed `--metrics-`)

- [ ] `--metrics-table` writes `<prefix>_metrics.txt`.
- [ ] `--metrics-json` writes `<prefix>.json`.
- [ ] `--metrics-csv` writes `<prefix>.csv`.
- [ ] `--metrics-wpm`, `--metrics-pause-ratio`, `--metrics-long-punct-weight` expose the
      corresponding metricalc parameters.

## Print Options (prefixed `--print-`)

- [ ] `--print-acute`, `--print-bold`, `--print-ipa`, `--print-xar` select accent outputs.
- [ ] `--print-ipa-proto-semitic {preserve,replace}` maps to printer's `--ipa-proto-semitic`.
- [ ] `--print-circ-hiatus` maps to printer's `--circ-hiatus`.

## Testing

- [ ] `--test` runs fullprosmaker's own unit tests (CLI resolution) and exits with
      code 0 on pass.
- [ ] `--test-prosody` runs the prosody engine tests.
- [ ] `--test-metrics` runs the metrics tests.
- [ ] `--version` prints the package version, author, license, and repository.

---

# User Story (optional)
> As a corpus analyst, I want to run one command on a cleaned Akkadian text file
> and receive syllabified, accentuated, and metrics-annotated output in one step
> so that I can iterate over multiple texts quickly.

---

# Interface Notes
- Input: `<prefix>_proc.txt` (output of `atfparser.py`).
- Core outputs: `<prefix>_syl.txt`, `<prefix>_tilde.txt` (always written).
- Optional outputs: metrics files, accent files (controlled by flags).
- Affected components: `src/akkapros/cli/fullprosmaker.py`, and all library modules
  under `src/akkapros/lib/`.
- CLI:
  ```
  python src/akkapros/cli/fullprosmaker.py erra_proc.txt \
    --prosody-style lob \
    --metrics-table --metrics-json \
    --print-ipa --print-bold \
    -p erra --outdir outputs
  ```
- Module invocation: `python -m akkapros.cli.fullprosmaker <input> ...`

---

# Open Questions
- [ ] Should `atfparser.py` be wrapped as Stage 0 in `fullprosmaker.py` so a raw ATF
      file can be supplied directly? (Currently the pipeline starts from `_proc.txt`.)
- [ ] TO_BE_CONFIRMED: should `--test-all` run all sub-tests (prosody + metrics + printer)
      in one pass?

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: implemented (mature)

# Related
- Related ADRs: [ADR-004](../adr/004-stage-pipeline-and-pivot-format.md),
  [ADR-001](../adr/001-cli-lib-separation.md),
  [ADR-002](../adr/002-centralized-version-management.md),
  [ADR-003](../adr/003-output-prefix-convention.md)
- Implementation CRs: none currently open

# Non-Goals
- Does NOT call `atfparser.py`; the pipeline starts after ATF normalization.
- Does NOT manage corpus-level batch runs (call metricalc with `--input-list` for that).
- Does NOT push or publish results to external systems.

# Security / Safety Considerations
- Output directory is created as needed; callers should not pass untrusted paths
  from user-supplied web input without sanitization.
