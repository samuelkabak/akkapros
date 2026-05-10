---
adr_id: ADR-052
status: Accepted
created: 2026-05-10
updated: 2026-05-10
supersedes: 'ADR-043 (partial: updates approved print.run key list)'
---

# ADR-052: Ultraheavy Hiatus Options

## Plain Summary

Two new configuration options for handling ultraheavy (circumflex) vowels are
accepted into the project's permanent config surface:

1. **`phonetize.process.realization.ultraheavy_hiatus_enable`** (CR-101) —
   experimental phonetizer-level expansion of circumflex vowels into
   vowel+transition+vowel triplets in dedicated `_yphone.txt` and
   `_ymbrola.pho` output files.

2. **`print.run.ipa_ultraheavy_hiatus`** (CR-102) — printer-level IPA hiatus
   splitting for circumflex vowels, renamed from the ambiguous `circ_hiatus`.

Both options are now part of the stable config schema. Older governance records
that listed `circ_hiatus` as an approved `print.run` key are superseded by this
ADR.

---

## Context and Problem Statement

CR-101 introduced `ultraheavy_hiatus_enable` as an experimental feature gated
behind `allow_experimental`. CR-102 renamed the printer's `circ_hiatus` option
to `ipa_ultraheavy_hiatus` for clarity. These changes need formal ADR-level
acceptance to become permanent parts of the config surface.

Additionally, older governance records (REQ-029, ADR-043, CR-044) reference
`circ_hiatus` as an approved `print.run` key. Rather than modifying those
historical records, this ADR supersedes them on this specific point.

---

## Decision Drivers

- **Clarity:** The name `ipa_ultraheavy_hiatus` is self-documenting; `circ_hiatus` was ambiguous
- **Consistency:** Both options now use the `ultraheavy_hiatus` naming convention
- **Preserve history:** Older governance records remain as-is; this ADR overrides them on the specific key name
- **Stability:** Both options are implemented, tested, and verified

---

## Considered Options

- **Option A (chosen):** Accept both options as permanent via a new ADR, superseding older records on the specific key name
- **Option B:** Modify older governance records (REQ-029, ADR-043, CR-044) to update the key name — rejected because it rewrites history
- **Option C:** Leave the rename undocumented at the ADR level — rejected because the config surface needs formal governance

---

## Decision Outcome

**Chosen: Option A.** Both ultraheavy hiatus options are accepted as permanent
parts of the config surface. Older records that reference `circ_hiatus` as an
approved key are superseded by this ADR on that specific point.

---

## Pros and Cons of the Options

### Chosen Option (Option A)

- Pros:
  - Preserves historical governance records unchanged
  - Provides a single authoritative reference for both options
  - Follows the incremental governance model (newer records override older)
- Cons:
  - Requires readers to check this ADR alongside older records

### Other Options

- Option B (modify older records):
  - Pros: single source of truth in each record
  - Cons: rewrites history, violates governance policy of preserving older records
- Option C (no ADR):
  - Pros: minimal effort
  - Cons: no formal governance for the new config surface

---

## Implications and Consequences

- `print.run.circ_hiatus` is no longer a valid config key; `print.run.ipa_ultraheavy_hiatus` is the active key
- `phonetize.process.realization.ultraheavy_hiatus_enable` is a permanent config key (still gated behind `allow_experimental`)
- REQ-029, ADR-043, and CR-044 are superseded by this ADR on the specific point of the `print.run` key name
- No code changes needed — both CR-101 and CR-102 are already implemented

---

## Links

- [CR-101](../cr/101-ultraheavy-marker-phone-and-mbrola-output.md) — Ultraheavy Marker Phone and MBROLA Output
- [CR-102](../cr/102-rename-circ-hiatus-to-ipa-ultraheavy-hiatus.md) — Rename `print.run.circ_hiatus` to `print.run.ipa_ultraheavy_hiatus`
- [REQ-051](../req/051-ipa-ultraheavy-hiatus-rename.md) — Requirement for the rename
- [REQ-050](../req/050-ultraheavy-marker-phone-and-mbrola-output.md) — Requirement for ultraheavy phonetizer expansion
- [ADR-043](043-separate-run-and-process-config-blocks-and-remove-common-outdir.md) — Superseded on the specific `print.run` key name
