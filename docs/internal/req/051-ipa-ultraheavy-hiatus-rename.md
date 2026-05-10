---
req_id: REQ-051
status: Implemented
priority: Medium
impact: Mutative
created: 2026-05-10
updated: 2026-05-10
related_adrs: 'ADR-052'
implemented_by: 'CR-102'
---

# Requirement: Rename `print.run.circ_hiatus` to `print.run.ipa_ultraheavy_hiatus`

# Summary

The printer option that controls whether circumflex vowels (â, î, û, ê) are
split into hiatus in IPA output shall be renamed from `circ_hiatus` to
`ipa_ultraheavy_hiatus` across all surfaces: config key, CLI flags, Python
parameters, and help registry keys. No behavioural change accompanies this
rename.

---

# Motivation

The name `circ_hiatus` is ambiguous: it does not convey that this option only
affects IPA output, nor that it targets ultraheavy (circumflex) vowels
specifically. The new name `ipa_ultraheavy_hiatus` makes the scope explicit:

- `ipa_` — only affects IPA-mode rendering
- `ultraheavy_` — only applies to circumflex vowels (â, î, û, ê)
- `hiatus` — the expansion strategy (split into two hiatus syllables)

This aligns with the naming convention established by CR-101's
`ultraheavy_hiatus_enable` (phonetizer-level expansion), making the
distinction between the two related but separate options clearer.

---

# Acceptance Criteria

- [x] Config key `print.run.circ_hiatus` is replaced by `print.run.ipa_ultraheavy_hiatus`
- [x] Printer CLI flag `--circ-hiatus` is replaced by `--ipa-ultraheavy-hiatus`
- [x] Fullprosmaker CLI flag `--print-circ-hiatus` is replaced by `--print-ipa-ultraheavy-hiatus`
- [x] All Python function parameters named `circ_hiatus` in the print layer are renamed to `ipa_ultraheavy_hiatus`
- [x] All YAML files use the new key name
- [x] Help registry keys use the new name
- [x] No behavioural change: `ipa_ultraheavy_hiatus=true` produces identical output to the old `circ_hiatus=true`
- [x] All existing tests pass without modification

---

# Interface Notes

| Surface | Old | New |
|---|---|---|
| Config key | `print.run.circ_hiatus` | `print.run.ipa_ultraheavy_hiatus` |
| Printer CLI flag | `--circ-hiatus` | `--ipa-ultraheavy-hiatus` |
| Fullprosmaker CLI flag | `--print-circ-hiatus` | `--print-ipa-ultraheavy-hiatus` |
| Python parameter | `circ_hiatus` | `ipa_ultraheavy_hiatus` |
| Help registry key (config) | `print.run.circ_hiatus` | `print.run.ipa_ultraheavy_hiatus` |
| Help registry key (printer) | `printer.circ_hiatus` | `printer.ipa_ultraheavy_hiatus` |
| Help registry key (fullprosmaker) | `fullprosmaker.print_circ_hiatus` | `fullprosmaker.print_ipa_ultraheavy_hiatus` |
| Help registry key (print) | `print.circ_hiatus` | `print.ipa_ultraheavy_hiatus` |
| Config dest (printer) | `run.circ_hiatus` → `circ_hiatus` | `run.ipa_ultraheavy_hiatus` → `ipa_ultraheavy_hiatus` |
| Config dest (fullprosmaker) | `run.circ_hiatus` → `print_circ_hiatus` | `run.ipa_ultraheavy_hiatus` → `print_ipa_ultraheavy_hiatus` |

---

# Open Questions

None.

---

# Related

- Related ADRs: [ADR-052](../adr/052-legalize-ultraheavy-hiatus-options.md)
- Implementation CRs: [CR-102](../cr/102-rename-circ-hiatus-to-ipa-ultraheavy-hiatus.md)

# Non-Goals

- No change to the phonetizer-owned `ultraheavy_hiatus_enable` option (under `phonetize.process.realization`)
- No deprecation period or backward-compatible alias for the old name
- No behavioural change to how the option works
