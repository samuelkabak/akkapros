---
cr_id: CR-102
status: Done
priority: Medium
impact: Cosmetic
created: 2026-05-10
updated: 2026-05-10
implements: ''
---

# Change Request: Rename `print.run.circ_hiatus` to `print.run.ipa_ultraheavy_hiatus`

# Summary

Rename the printer option `circ_hiatus` (config key `print.run.circ_hiatus`,
CLI flags `--circ-hiatus` / `--print-circ-hiatus`) to `ipa_ultraheavy_hiatus`
(config key `print.run.ipa_ultraheavy_hiatus`, CLI flags
`--ipa-ultraheavy-hiatus` / `--print-ipa-ultraheavy-hiatus`).

This is a pure renaming — no behavioural change, no new feature, no removal of
existing functionality. The option continues to control whether circumflex
vowels (â, î, û, ê) are split into hiatus in IPA output.

---

# Motivation

The name `circ_hiatus` is ambiguous: it does not convey that this option only
affects IPA output, nor that it targets ultraheavy (circumflex) vowels
specifically. The new name `ipa_ultraheavy_hiatus` makes the scope explicit:

- `ipa_` — only affects IPA-mode rendering
- `ultraheavy_` — only applies to circumflex vowels (â, î, û, ê)
- `hiatus` — the expansion strategy (split into two hiatus syllables)

---

# Scope

## Included

- Rename the config key `print.run.circ_hiatus` → `print.run.ipa_ultraheavy_hiatus`
- Rename the Python parameter `circ_hiatus` → `ipa_ultraheavy_hiatus` in all
  internal function signatures
- Rename the CLI flag `--circ-hiatus` → `--ipa-ultraheavy-hiatus` (printer)
- Rename the CLI flag `--print-circ-hiatus` → `--print-ipa-ultraheavy-hiatus` (fullprosmaker)
- Rename the help registry keys and help text labels
- Update all YAML files that reference `circ_hiatus`
- Update governance records that list `circ_hiatus` as an approved key
- Update user-facing documentation if any reference exists

## Not Included

- Any behavioural change to how the option works
- Any change to the phonetizer-owned `ultraheavy_hiatus_enable` option (that is
  a separate config key under `phonetize.process.realization`)
- Any deprecation period or backward-compatible alias

---

# Current Behavior

The option `print.run.circ_hiatus` (default: `false`) controls whether
circumflex vowels (â, î, û, ê) are split into hiatus in IPA output. When
enabled, `qû` renders as `qʊ.ʊ` instead of `qʊː`.

The option is exposed on these surfaces:

| Surface | Current name |
|---|---|
| Config key | `print.run.circ_hiatus` |
| Printer CLI flag | `--circ-hiatus` |
| Fullprosmaker CLI flag | `--print-circ-hiatus` |
| Python parameter | `circ_hiatus` |
| Help registry key (config) | `print.run.circ_hiatus` |
| Help registry key (printer) | `printer.circ_hiatus` |
| Help registry key (fullprosmaker) | `fullprosmaker.print_circ_hiatus` |
| Help registry key (print) | `print.circ_hiatus` |
| Config dest (printer) | `run.circ_hiatus` → `circ_hiatus` |
| Config dest (fullprosmaker) | `run.circ_hiatus` → `print_circ_hiatus` |

---

# Proposed Change

Every occurrence of `circ_hiatus` (in the print.run context) is renamed to
`ipa_ultraheavy_hiatus`. The mapping is:

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

# Technical Design

## Config schema

**`src/akkapros/config/default.yaml`** — rename key `circ_hiatus` to
`ipa_ultraheavy_hiatus` under `print.run`. Update the inline comment to reflect
the new name.

**`src/akkapros/lib/config.py`** — three changes:

1. `CONFIG_SCHEMA[PRINT_SECTION]['run']`: rename key `'circ_hiatus'` →
   `'ipa_ultraheavy_hiatus'`
2. `TOOL_CONFIG_SECTIONS['printer']` field map: rename
   `'run.circ_hiatus': 'circ_hiatus'` →
   `'run.ipa_ultraheavy_hiatus': 'ipa_ultraheavy_hiatus'`
3. `TOOL_CONFIG_SECTIONS['fullprosmaker']` field map: rename
   `'run.circ_hiatus': 'print_circ_hiatus'` →
   `'run.ipa_ultraheavy_hiatus': 'print_ipa_ultraheavy_hiatus'`

## Help messages

**`src/akkapros/lib/helpmsg.py`** — rename four registry keys:

- `'print.run.circ_hiatus'` → `'print.run.ipa_ultraheavy_hiatus'`
- `'printer.circ_hiatus'` → `'printer.ipa_ultraheavy_hiatus'`
- `'fullprosmaker.print_circ_hiatus'` → `'fullprosmaker.print_ipa_ultraheavy_hiatus'`
- `'print.circ_hiatus'` → `'print.ipa_ultraheavy_hiatus'`

## Printer CLI

**`src/akkapros/cli/printer.py`** — rename:

- `_resolve_ipa_options()`: parameter `circ_hiatus` → `ipa_ultraheavy_hiatus`
- `_Args.__init__()`: attribute `circ_hiatus` → `ipa_ultraheavy_hiatus`
- Test cases: rename `circ_hiatus` → `ipa_ultraheavy_hiatus`
- `parser.add_argument('--circ-hiatus', ...)` → `'--ipa-ultraheavy-hiatus'`
- `args.circ_hiatus` → `args.ipa_ultraheavy_hiatus`
- `circ_hiatus=circ_hiatus` → `ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus`

## Fullprosmaker CLI

**`src/akkapros/cli/fullprosmaker.py`** — rename:

- `_resolve_ipa_options()`: parameter `print_circ_hiatus` → `print_ipa_ultraheavy_hiatus`
- `_Args.__init__()`: attribute `print_circ_hiatus` → `print_ipa_ultraheavy_hiatus`
- Test cases: rename `print_circ_hiatus` → `print_ipa_ultraheavy_hiatus`
- `parser.add_argument('--print-circ-hiatus', ...)` → `'--print-ipa-ultraheavy-hiatus'`
- `args.print_circ_hiatus` → `args.print_ipa_ultraheavy_hiatus`
- `circ_hiatus=circ_hiatus` → `ipa_ultraheavy_hiatus=ipa_ultraheavy_hiatus`

## Print library

**`src/akkapros/lib/print.py`** — rename parameter `circ_hiatus` →
`ipa_ultraheavy_hiatus` in all functions that carry it:

- `_flush_syllable()`
- `_convert_word()`
- `_convert_non_bracket_part()`
- `_convert_non_bracket_part_ipa()`
- `convert_line()`
- `convert_text_with_ipa()`
- `convert_text_with_ipa_xar()`
- `_convert_bold_markdown_lines()`
- `process_file()`
- All internal call sites passing `circ_hiatus=...`
- Test code at bottom: rename `circ_hiatus_cases` → `ipa_ultraheavy_hiatus_cases`

**`src/akkapros/lib/_print_ipa.py`** — same parameter renames as `print.py`
for all functions that carry `circ_hiatus`:

- `_flush_syllable()`
- `_convert_word()`
- `_convert_non_bracket_part()`
- `_convert_non_bracket_part_ipa()`
- `convert_line()`
- `convert_text_with_ipa()`
- `convert_text_with_ipa_xar()`
- `_convert_bold_markdown_lines()`

**`src/akkapros/lib/_print_pho.py`** — rename:

- `_render_phone_rows()`: parameter `circ_hiatus` → `ipa_ultraheavy_hiatus`
- `process_file()`: parameter `circ_hiatus` → `ipa_ultraheavy_hiatus`
- All internal call sites

## Print tests

**`src/akkapros/lib/tests/print_tests.py`** — rename:

- `circ_hiatus_cases` → `ipa_ultraheavy_hiatus_cases`
- Test label `'Ipa circ hiatus'` → `'Ipa ultraheavy hiatus'`
- `convert_line(inp, 'ipa', circ_hiatus=True)` → `convert_line(inp, 'ipa', ipa_ultraheavy_hiatus=True)`

## YAML files

- **`demo/akkapros/prosmaker/corpus-demo.yaml`**: rename `circ_hiatus: false` → `ipa_ultraheavy_hiatus: false`
- **`demo/akkapros/lexlinks/construct-demo.yaml`**: rename `circ_hiatus: false` → `ipa_ultraheavy_hiatus: false`
- **`tests/integration_refs/regression_defaults.yaml`**: rename `circ_hiatus: false` → `ipa_ultraheavy_hiatus: false`

## Governance records

- **`docs/internal/req/029-stage-config-run-process-separation-and-common-outdir-removal.md`** (line 81):
  update the list of approved `print.run` keys: `circ_hiatus` → `ipa_ultraheavy_hiatus`
- **`docs/internal/adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md`** (line 114):
  update the approved stage mapping: `circ_hiatus` → `ipa_ultraheavy_hiatus`
- **`docs/internal/cr/044-restructure-stage-config-into-run-and-process-blocks.md`** (line 151):
  update the proposed YAML example: `circ_hiatus` → `ipa_ultraheavy_hiatus`

## User-facing documentation

- **`docs/akkapros/`** — search for any references to `circ_hiatus` and update.
  No results found in current scan, but verify after implementation.

---

# Files Likely Affected

```
src/akkapros/config/default.yaml
src/akkapros/lib/config.py
src/akkapros/lib/helpmsg.py
src/akkapros/lib/print.py
src/akkapros/lib/_print_ipa.py
src/akkapros/lib/_print_pho.py
src/akkapros/lib/tests/print_tests.py
src/akkapros/cli/printer.py
src/akkapros/cli/fullprosmaker.py
demo/akkapros/prosmaker/corpus-demo.yaml
demo/akkapros/lexlinks/construct-demo.yaml
tests/integration_refs/regression_defaults.yaml
docs/internal/req/029-stage-config-run-process-separation-and-common-outdir-removal.md
docs/internal/adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md
docs/internal/cr/044-restructure-stage-config-into-run-and-process-blocks.md
```

---

# Acceptance Criteria

- [x] `print.run.circ_hiatus` is no longer a valid config key;
      `print.run.ipa_ultraheavy_hiatus` is the active key
- [x] `--circ-hiatus` is no longer a valid CLI flag for printer;
      `--ipa-ultraheavy-hiatus` is the active flag
- [x] `--print-circ-hiatus` is no longer a valid CLI flag for fullprosmaker;
      `--print-ipa-ultraheavy-hiatus` is the active flag
- [x] All Python function parameters named `circ_hiatus` in the print layer are
      renamed to `ipa_ultraheavy_hiatus`
- [x] All YAML files use the new key name
- [x] Help text and `confwriter` inventory use the new key name
- [x] Governance records that list `circ_hiatus` as an approved key are updated
- [x] All existing tests pass without modification (behaviour is unchanged)
- [x] No behavioural change: `ipa_ultraheavy_hiatus=true` produces identical
      output to the old `circ_hiatus=true`

---

# Risks / Edge Cases

- The phonetizer-owned option `ultraheavy_hiatus_enable` (under
  `phonetize.process.realization`) has a similar name but is a completely
  separate option. The rename must not touch that option.
- The `circ_hiatus_cases` variable in `print_tests.py` is a local test variable
  and must be renamed to avoid confusion with the old config key name.
- The `_resolve_ipa_options()` function in both CLIs returns a tuple
  `(write_ipa, ipa_ultraheavy_hiatus)` — the return value unpacking at call
  sites must be updated consistently.

---

# Testing Strategy

- Run the full test suite: `python -m pytest`
- Run print-specific tests: `python -m pytest tests/ -k "print"`
- Run CLI resolution tests: `python -m pytest tests/ -k "cli"`
- Verify that `confwriter --list` shows `print.run.ipa_ultraheavy_hiatus` and
  not `print.run.circ_hiatus`
- Verify that `confwriter --get print.run.circ_hiatus` raises a `ConfigError`
- Verify that `--ipa-ultraheavy-hiatus` works in printer and fullprosmaker

---

# Rollback Plan

Revert all renames in the files listed above. The old name `circ_hiatus` will
be restored as the active config key, CLI flag, and parameter name.

---

# Related Issues

- [REQ-029](../req/029-stage-config-run-process-separation-and-common-outdir-removal.md) —
  lists `circ_hiatus` as an approved `print.run` key (to be updated)
- [ADR-043](../adr/043-separate-run-and-process-config-blocks-and-remove-common-outdir.md) —
  approved stage mapping includes `circ_hiatus` (to be updated)
- [CR-044](044-restructure-stage-config-into-run-and-process-blocks.md) —
  proposed YAML example includes `circ_hiatus` (to be updated)

---

# Tasks

## Implementation

- [x] Rename config key in `src/akkapros/config/default.yaml`
- [x] Rename schema key and field maps in `src/akkapros/lib/config.py`
- [x] Rename help registry keys in `src/akkapros/lib/helpmsg.py`
- [x] Rename parameter and CLI flag in `src/akkapros/cli/printer.py`
- [x] Rename parameter and CLI flag in `src/akkapros/cli/fullprosmaker.py`
- [x] Rename parameter in `src/akkapros/lib/print.py`
- [x] Rename parameter in `src/akkapros/lib/_print_ipa.py`
- [x] Rename parameter in `src/akkapros/lib/_print_pho.py`
- [x] Rename test variable and calls in `src/akkapros/lib/tests/print_tests.py`
- [x] Update YAML files: `demo/akkapros/prosmaker/corpus-demo.yaml`,
      `demo/akkapros/lexlinks/construct-demo.yaml`,
      `tests/integration_refs/regression_defaults.yaml`

## Documentation

- [x] Update `docs/internal/req/029-*.md`
- [x] Update `docs/internal/adr/043-*.md`
- [x] Update `docs/internal/cr/044-*.md`
- [x] Update `docs/akkapros/` if any reference exists

## Verification

- [x] Run full test suite
- [x] Verify `confwriter --list` shows new key
- [x] Verify `confwriter --get print.run.circ_hiatus` fails
- [x] Verify CLI flags work with new names

---

# Implementation Blockers

No blockers known.

---

# Notes

## Code flow (from call graph analysis)

The `circ_hiatus` parameter flows through these call chains:

**Printer CLI** (`src/akkapros/cli/printer.py`):
```
main() → _resolve_ipa_options(args) → returns (write_ipa, circ_hiatus)
       → process_file(..., circ_hiatus=circ_hiatus, ...)
```

**Fullprosmaker CLI** (`src/akkapros/cli/fullprosmaker.py`):
```
main() → _resolve_ipa_options(args) → returns (output_ipa, circ_hiatus)
       → run_pipeline(..., circ_hiatus=circ_hiatus, ...)
       → process_file(..., circ_hiatus=circ_hiatus, ...)
```

**Print library** (`src/akkapros/lib/print.py`):
```
process_file() → convert_text_with_ipa() → convert_line() → _convert_word()
              → _convert_non_bracket_part() → _convert_non_bracket_part_ipa()
              → _flush_syllable()
```

The same chain exists in `_print_ipa.py`. The `_print_pho.py` path is shorter:
```
process_file() → _render_phone_rows()
```

## Related but distinct option

The phonetizer has its own option `ultraheavy_hiatus_enable` under
`phonetize.process.realization` (introduced by CR-101). That option controls
whether the phonetizer emits an ultraheavy marker in phone rows. It is a
completely separate concern from the printer's IPA hiatus splitting. The rename
in this CR must not touch that option.
