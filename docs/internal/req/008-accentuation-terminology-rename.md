# Requirement: Accentuation Terminology Rename (CR-004 Migration)

REQ-ID: REQ-008
Status: Approved (CR-004, pending full implementation)
Priority: Medium
Created: 2026-03-19
Updated: 2026-03-19
---

# Summary

The system shall replace all user-facing occurrences of the words "repair",
"repaired", and "repairs" (referring to prosodic modifications) with
"accentuation", "accentuated", and "accentuations" across code identifiers,
output labels, JSON and CSV keys, printed table headings, CLI help text, tests,
and documentation.

This is a deliberate breaking change accepted by the project (ADR-023).

---

# Motivation

The word "repair" implies correcting an error in the input text. The prosody
realization algorithm does not fix errors; it applies a phonologically grounded
prosodic transformation (mora addition through gemination or vowel lengthening)
to model connected-speech accentuation. Using "repair" misleads users and
downstream consumers about the nature of the operation. The rename to
"accentuation" aligns the terminology with the actual linguistic function.

---

# Acceptance Criteria

## Code Identifiers

- [ ] No remaining variable or function name in `src/akkapros/lib/` carries the
      string `repair`, `repaired`, or `repairs` where it refers to prosodic modification.
- [ ] No remaining variable or function name in `src/akkapros/cli/` carries the
      legacy terms.
- [ ] Renamed forms follow the pattern:
      - `repaired` → `accentuated`
      - `repair` (noun/verb) → `accentuation` / `accentuate`
      - `repairs` → `accentuations`

## Output Labels and Keys

- [ ] JSON output: no key contains `repair`/`repaired`/`repairs` for prosodic fields;
      keys use `accentuated_` prefix or `accentuations` where applicable
      (e.g., `accentuated_total_morae`, `accentuation_rate`).
- [ ] CSV headers: same replacement applied to all column names.
- [ ] Human-readable table headings: `Acoustic metrics (accentuated)` replaces
      `Acoustic metrics (repaired)`.
- [ ] IPA output and printer metadata labels updated accordingly.

## Tests

- [ ] All test fixtures and assertions updated to use the new terms.
- [ ] No test relies on legacy JSON/CSV key strings.
- [ ] Full test suite passes after the rename.

## Documentation

- [ ] All `.md` files in `docs/` updated; no user-facing reference to "repair"
      in the prosodic-modification sense remains.
- [ ] CHANGELOG entry added for the breaking change.
- [ ] Migration notes provided for downstream consumers (e.g., scripts parsing
      JSON/CSV output).

---

# User Story (optional)
> As a downstream tool author parsing `metricalc` JSON output, I want stable,
> semantically accurate field names so that I can build on the API without
> being confused by terminology that implies error correction.

---

# Interface Notes
- Affects: all output formats (table, JSON, CSV), CLI help strings, internal
  variable names.
- Not a change to the algorithm or output format structure; purely a rename.
- Consumers of JSON/CSV output must update key/column parsing after migration.

---

# Open Questions
- [ ] TO_BE_CONFIRMED: are there any third-party scripts or publications already
      citing the legacy `repaired` JSON field names that need a deprecation period?
- [ ] Should legacy key aliases be kept transiently with a deprecation warning?
      (ADR-023 says no, but may need revisiting if external consumers exist.)

---

# Implementation Notes (optional)
- Owner: Samuel KABAK
- Estimated effort: medium (mechanical rename + test updates)
- CR-004 contains the detailed implementation scope and file list.

# Related
- Related ADRs: [ADR-023](../adr/023-rename-repair-to-accentuation.md)
- Implementation CRs: [CR-004](../cr/004-rename-repair-to-accentuation/)

# Non-Goals
- Does NOT change any algorithmic behavior; the output values are unchanged,
  only the labels.
- Does NOT rename the `prosmaker.py` CLI binary itself.

# Security / Safety Considerations
- Pure documentation and identifier rename; no security implications beyond
  maintaining correct documentation of behavior.
