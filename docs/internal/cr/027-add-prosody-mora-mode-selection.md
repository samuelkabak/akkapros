---
cr_id: CR-027
status: Done
priority: High
impact: Mutative
created: 2026-03-30
updated: 2026-03-31
implements: 'ADR-034, REQ-019'
---

# Change Request: Add Prosody Mora Mode Selection

# Summary

Add a new CLI option `--mora-mode {bi|mono}` to both `prosmaker` and
`fullprosmaker`, with `bi` as the default.

`bi` must preserve the current behavior exactly. `mono` must keep the existing
accentuation hierarchy, legality rules, and structural grouping rules, but it
must stop requiring odd mora parity before accentuation is attempted for
eligible standalone words and prosodic units.

---

# Motivation

The current prosody engine is designed around bimoraicity and therefore uses
odd/even mora parity as a gate for accentuation. That is appropriate for the
project's primary realization model, but it prevents direct comparison with the
traditional academic model in Assyriology, where accentuation is not filtered
through a bimoraic odd-parity prerequisite.

This CR introduces an explicit research-facing switch so the same pipeline can
be run in either mode without changing default behavior or forking logic.

---

# Scope

## Included

- Add `--mora-mode {bi,mono}` to `prosmaker`.
- Add `--mora-mode {bi,mono}` to `fullprosmaker` and pass it through to the
  prosody stage.
- Make prosody eligibility mode-aware for both standalone words and merged
  units.
- Preserve explicit `+` pre-tail locking so user-linked words remain
  non-accentuable even when they are content words.
- Preserve current `bi` behavior exactly.
- Propagate `mora_mode` through YAML front matter option metadata.
- Add self-tests and pytest coverage for the new mode.
- Update user-facing documentation to describe both modes precisely.
- Extend the demo corpus wrapper scripts so they also generate a
  `corpus-mono-lob_*` branch from the shared syllabified corpus output.

## Not Included

- Replacing or renaming the current `lob` / `sob` style system.
- Changing the current repair/accentuation operation inventory.
- Changing metrics formulas or printer behavior except through normal
  downstream consumption of changed prosody output.
- Changing current output filenames or creating dedicated mono-mode file
  suffixes.

---

# Current Behavior

The current implementation hard-codes odd-parity gating in the prosody layer.
At minimum, the present audit identifies these gates:

1. `Word.needs_accentuation`
   - returns true only when `accentuated_morae % 2 == 1`

2. `MergedUnit.needs_accentuation`
   - returns true only when `morae % 2 == 1`

3. `ProsodyEngine.accentuation_line(...)`
   - skips standalone words when `not word.needs_accentuation`
   - skips merged candidates when `not unit.needs_accentuation`
   - otherwise applies the existing `lob` / `sob` candidate-selection rules

This means an even-mora standalone word is left untouched under current
behavior unless it participates in some later merge path that changes the
combined unit's parity.

---

# Proposed Change

Introduce a new mora-mode concept with these semantics:

- `bi`
  - current behavior unchanged
  - accentuation attempt is gated by odd mora parity

- `mono`
  - same candidate-selection priorities and same legality rules
  - same function-word exclusion and explicit-link grouping semantics
  - same explicit-link locking semantics for all linked words before the
    eligible tail
  - same structural grouping and last-resort behavior
  - no odd-parity prerequisite before attempting accentuation on an eligible
    standalone word or eligible prosodic unit
  - no forward merge in `mono`; after a unit is determined by grouping rules,
    the engine tries internal accentuation and then falls directly to last
    resort if no legal candidate exists

Expected effect of `mono`:

- even-mora eligible words may become odd after one accentuation
- odd-mora eligible words may become even after one accentuation
- units that previously short-circuited because they were already even no
  longer do so solely for that reason
- explicit `+` linked words before the tail remain protected from accentuation
  in both modes

Backward-compatibility rule:

- invoking either CLI with no `--mora-mode` argument must produce the same
  outputs as today, subject only to unrelated existing nondeterminism if any

---

# Technical Design

Architecture notes:

Components:
- `src/akkapros/lib/prosody.py`
- `src/akkapros/cli/prosmaker.py`
- `src/akkapros/cli/fullprosmaker.py`
- front matter option propagation helpers already used by stage CLIs

Design direction:
- introduce an explicit mora-mode value at the prosody-engine boundary
- thread that value through both standalone-word and merged-unit resolution
- avoid duplicating parity logic in multiple branches

Preferred implementation shape:
- add a mode-aware policy object, enum, or helper that answers whether
  accentuation should be attempted for a given eligible unit
- use that policy in the current decision points instead of hard-coded parity
  checks embedded separately in `Word`, `MergedUnit`, and engine branches
- keep candidate selection methods focused on choosing *where* to accentuate,
  not *whether* the current mode permits an attempt
- keep explicit-link locking as a separate structural constraint so mono mode
  does not accidentally accentuate user-linked pre-tail words
- avoid treating parity as a generic completion test in mono mode; resolution
  should depend on legal candidate availability and structural constraints

CLI contract:
- `prosmaker --mora-mode {bi,mono}`
- `fullprosmaker --mora-mode {bi,mono}`
- default is `bi`
- invalid values are rejected by standard CLI choice validation

Front matter contract:
- prosody outputs must record `metadata.options.mora_mode`
- full-pipeline outputs must preserve the same option in inherited metadata

Testing contract:
- existing bi-mode self-tests remain unchanged and must still pass
- new mono-mode self-tests are added as separate expectations
- pytest adds targeted coverage for CLI parsing, option propagation, and
  representative mono-mode output differences

Documentation contract:
- update prosody algorithm docs to distinguish bimoraic gating from accent site
  selection
- update CLI docs for `prosmaker` and `fullprosmaker`
- document front matter option emission so downstream analyses can identify the
  processing mode used

---

# Files Likely Affected

`src/akkapros/lib/prosody.py`
`src/akkapros/cli/prosmaker.py`
`src/akkapros/cli/fullprosmaker.py`
`src/akkapros/lib/frontmatter.py` or shared CLI option helpers if required
`docs/akkapros/prosmaker.md`
`docs/akkapros/fullprosmaker.md`
`docs/akkapros/prosody-realization-algorithm.md`
- `demo/akkapros/prosmaker/corpus-demo.ps1`
- `demo/akkapros/prosmaker/corpus-demo.sh`
- `demo/README.md`
`README.md` or `docs/GETTING_STARTED.md` if CLI option summaries are mirrored
`tests/test_integration_append_frontmatter.py`
`tests/test_selftests_cli.py`
prosody self-tests in `src/akkapros/lib/prosody.py`
additional pytest files for prosody/fullprosmaker CLI behavior as needed

---

# Acceptance Criteria

- [x] `prosmaker` accepts `--mora-mode` with choices `bi` and `mono`.
- [x] `fullprosmaker` accepts `--mora-mode` with choices `bi` and `mono`.
- [x] Omitting `--mora-mode` keeps current behavior exactly.
- [x] Explicit `--mora-mode bi` is behaviorally identical to the current
      implementation.
- [x] `mono` removes the odd-parity prerequisite for eligible standalone words.
- [x] `mono` removes the odd-parity prerequisite for eligible explicit linked
  units and structurally determined standalone units, while preserving
  their current grouping rules.
- [x] Explicit `+` linked words before the eligible tail remain ineligible for
  accentuation in both modes, even when they are content words.
- [x] Function-word handling is unchanged in both modes.
- [x] Existing `lob` / `sob` candidate selection and legality constraints are
      unchanged in both modes.
- [x] `mono` does not forward-merge unresolved units; it tries internal
  accentuation on the structurally determined unit and then falls directly
  to last resort.
- [x] Prosody front matter records `metadata.options.mora_mode`.
- [x] Full-pipeline outputs preserve `metadata.options.mora_mode` through
      option propagation.
- [x] Existing self-tests and pytest tests pass without rewriting their current
      expected bi-mode outputs.
- [x] New self-tests and pytest cases cover mono-mode behavior.
- [x] User documentation explains the exact difference between `bi` and `mono`.
- [x] Demo corpus wrapper scripts additionally generate a `corpus-mono-lob_*`
  branch from the shared `corpus_syl.txt` output.

---

# Risks / Edge Cases

Possible issues:

- If parity gating is removed in only one branch, standalone words and explicit
  groups may diverge semantically.
- If `needs_accentuation` remains parity-only while CLI introduces `mono`, the
  new option may appear to work in some paths and silently fail in others.
- Explicit `+` groups have special locking behavior; mono-mode must not break
  that contract while removing parity gating.
- Mono mode can make the old "already resolved because even" shortcut invalid,
  so any hidden forward-merge assumptions must be removed from mono paths.
- Front matter inheritance must not drop `mora_mode`, or downstream metrics and
  printed artifacts may become ambiguous.
- Documentation must not imply that `mono` changes accent site priorities; it
  changes the eligibility gate, not the selection hierarchy.

---

# Testing Strategy

Unit/self-tests:

- keep all current bi-mode expectations exactly as they are
- add mono-mode cases for even-mora standalone words that now accentuate
- add mono-mode cases for odd-mora standalone words that still accentuate
- add mono-mode cases showing that unresolved standalone words and explicit
  `+` groups fall directly to last resort without forward merge, while pre-tail
  linked words remain locked from accentuation
- add regression coverage for function-word groups where the final content host
  must carry the grouped-unit accentuation or last-resort repair
- add CLI parsing tests for accepted and rejected `--mora-mode` values

Integration tests:

- verify prosody front matter includes `metadata.options.mora_mode`
- verify `fullprosmaker` propagates `mora_mode` into prosody and downstream
  outputs
- verify representative mono-mode runs differ from bi-mode where expected while
  default runs remain unchanged

Manual/spec review:

- inspect docs and example command lines for exact terminology
- inspect front matter examples to ensure `mora_mode` is visible and stable

---

# Rollback Plan

If mono-mode causes regressions, disable the new CLI option and revert the
mode-aware eligibility changes while keeping the default `bi` path intact.
Because `bi` remains the default, rollback can be done by removing the new mode
without migrating existing users.

---

# Related Issues

- Formal requirement: [REQ-019](../req/019-prosody-mora-mode-selection.md)
- Related existing requirement: [REQ-003](../req/003-bimoraic-prosody-realization-algorithm.md)
- Related existing requirement: [REQ-007](../req/007-full-pipeline-orchestration.md)
- Related existing requirement: [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md)
- Related existing requirement: [REQ-010](../req/010-built-in-self-tests-and-test-infrastructure.md)

---

# Tasks

## Implementation

- [x] Add `--mora-mode` to `prosmaker`.
- [x] Add `--mora-mode` to `fullprosmaker` and pass it to the prosody stage.
- [x] Introduce a centralized mode-aware accentuation eligibility rule.
- [x] Apply that rule consistently to standalone words, merged units, and
      explicit linked-unit resolution.
- [x] Record `mora_mode` in front matter options.

## Tests

- [x] Preserve and re-run all existing bi-mode expectations unchanged.
- [x] Add mono-mode self-tests to prosody library coverage.
- [x] Add pytest coverage for CLI parsing and front matter propagation.
- [x] Add regression coverage for representative mono-mode output changes.
- [x] Update the demo corpus wrapper scripts to emit `corpus-mono-lob_*`
  artifacts from the shared syllabified corpus.

## Documentation

- [x] Update `prosmaker` CLI docs.
- [x] Update `fullprosmaker` CLI docs.
- [x] Update prosody algorithm docs to explain `bi` versus `mono`.
- [x] Add at least one front matter example showing `metadata.options.mora_mode`.
- [x] Update demo documentation to describe the additional mono-mode LOB demo
  branch.

## Review

- [x] Verify implementation matches [ADR-034](../adr/034-prosody-mora-modes-and-explicit-link-locking.md).
- [x] Verify backward compatibility of default behavior.

Implemented on 2026-03-30.

Corrected on 2026-03-31 to align mono-mode semantics with the accepted model:

- mono mode determines units from structural grouping only
- mono mode does not forward-merge unresolved units
- mono mode falls directly to last resort when no internal candidate exists
- a grouped function-word bug was found and corrected: the final content host
  in a function-word group could be emitted without resolving the grouped unit
  prosodically; grouped function-word units are now resolved under the active
  mora mode with the function-word prefix locked and the last content word as
  the eligible host

Verification run:

- `pytest tests/test_prosody_mora_mode.py tests/test_integration_append_frontmatter.py tests/test_metrics_stats.py tests/test_selftests_cli.py tests/test_integration.py -q`
- Result: `56 passed`

---

# Notes for CR-027

This CR intentionally asks for a smart modification rather than duplicated
branching. The key design constraint is to separate the question "is this unit
eligible for an accentuation attempt under the current mora mode?" from the
existing question "which syllable and operation should be chosen under `lob` or
`sob`?".

The current code audit suggests that the hard-coded parity gate is concentrated
around `needs_accentuation` on `Word` and `MergedUnit`, plus the short-circuit
branches in `ProsodyEngine.accentuation_line(...)`. That makes this area the
correct primary design target, but implementation should confirm all other
parity-dependent call sites before coding.