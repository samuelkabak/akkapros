---
cr_id: CR-061
status: Done
priority: High
impact: Mutative
created: 2026-04-15
updated: 2026-04-15
implements: 'ADR-041, CR-040, CR-042, CR-044, CR-059, REQ-026, REQ-027, REQ-031'
---

# Change Request: Remove User-Facing Short-Pause and Drift Policy Options

# Summary

Remove the phonetizer timing-model options `short_pause_policy` and
`drift_policy` from all user-facing surfaces and from runtime configuration
contracts.

After this change, behavior is fixed and non-configurable: drift handling must
always follow the current extensible path (running drift, then legal vowel
correction, then drift extension when needed), and short-pause discharge must
follow the current implemented preferred-target discharge behavior.

This CR updates active behavior approved by CR-040, CR-042, CR-044, and CR-059
where those records describe policy branching or user-facing configuration for
these options. Older records remain historical context.

---

# Motivation

The repository currently exposes two policy switches that no longer match the
desired product surface:

- `drift_policy` is still user-facing in config, CLI flags, and docs, but the
  target contract is fixed to extensible behavior.
- `short_pause_policy` has residual config and CLI traces, while the active
  implementation path already behaves as one fixed policy.

Keeping both options public increases cognitive load, broadens test matrix
cost, and creates avoidable docs/config drift.

---

# Scope

## Included

- Remove `short_pause_policy` and `drift_policy` from all user-facing YAML
  configuration surfaces in the repository.
- Remove corresponding CLI flags from `phonetizer` and `fullprosmaker`.
- Remove corresponding help text entries and config-field mappings.
- Remove schema/default/verification enum acceptance for these keys.
- Keep `drift_tolerance` user-facing.
- Preserve runtime behavior by hardwiring:
  - drift handling equivalent to prior `drift_policy=extensible`
  - short-pause discharge equivalent to currently implemented fixed behavior
- Update user-facing documentation under `docs/` to remove these options from
  tables, examples, and prose.
- Update demo YAMLs and other non-temporary YAML assets in the repository to
  remove both keys.
- Update tests/self-tests so they no longer assert or pass removed policy
  options.
- Add migration notes describing removal of these two options.

## Not Included

- Changing pause-band numeric defaults.
- Changing `drift_tolerance` semantics.
- Revising historical internal records except by forward supersession notes.
- Backport compatibility mode that silently accepts removed keys.

---

# Current Behavior

Observed on 2026-04-15:

- `src/akkapros/config/default.yaml` still defines both keys.
- Demo configs in `demo/akkapros/prosmaker/corpus-demo.yaml` and
  `demo/akkapros/lexlinks/construct-demo.yaml` still define both keys.
- CLI surfaces still expose flags:
  - `--short-pause-policy`, `--drift-policy` in `src/akkapros/cli/phonetizer.py`
  - `--phonetize-short-pause-policy`, `--phonetize-drift-policy` in
    `src/akkapros/cli/fullprosmaker.py`
- Config/help plumbing still maps and documents both keys in
  `src/akkapros/lib/config.py` and `src/akkapros/lib/helpmsg.py`.
- Phonetize schema and verification still include both options in
  `src/akkapros/lib/phonetize.py`.
- Runtime branching by `drift_policy` still exists in
  `src/akkapros/lib/phonetize.py`.
- User docs still mention these options (for example,
  `docs/akkapros/phonetizer.md`, `docs/akkapros/phonetizer-algorithm.md`, and
  `docs/akkapros/varco-verification.md`).

---

# Proposed Change

## 1. Remove both options from public contract

The canonical phonetize timing-model contract must no longer include:

- `phonetize.process.timing_model.short_pause_policy`
- `phonetize.process.timing_model.drift_policy`

Any CLI/config surface that currently exposes these options must be removed.

## 2. Fix drift behavior to extensible internally

Phase 2 drift handling must be unconditional and equivalent to the previous
`drift_policy=extensible` branch:

1. apply running drift assignment,
2. apply legal vowel correction,
3. carry unresolved remainder as drift extension,
4. do not fail solely because a removed strict-policy branch is absent.

`drift_tolerance` remains active as a numeric control used by this fixed flow.

## 3. Fix short-pause behavior internally

Short-pause discharge must follow one fixed algorithm equivalent to current
implemented behavior (preferred short-band target derived from the cvc
reference, then legal bounded discharge).

No user-facing switch remains for alternative short-pause policy modes.

## 4. Compatibility and failure mode for removed keys

Supplying removed keys in config-path overrides or config files must fail with
explicit error text indicating the option was removed by CR-061.

Rationale: explicit failure prevents silent reliance on obsolete contract
surface.

## 5. Documentation and YAML cleanup requirements

Implementation must remove these keys from all maintained non-temporary YAML
assets and user-facing docs in this repository.

Historical internal ADR/REQ/CR records may retain prior references as history,
but active docs must describe only the new fixed behavior.

---

# Technical Design

Implementation guidance (non-binding to file internals):

- Delete schema/default fields and enum validations for removed keys.
- Delete CLI args and config mapping entries for removed keys.
- Collapse drift handling code paths to the extensible behavior only.
- Keep short-pause realization algorithm as fixed behavior and remove policy
  branching/plumbing.
- Update generated help text and config docs outputs.
- Update unit/integration/self-tests to remove removed-option permutations and
  assert fixed behavior.

Supersession note:

- Where prior accepted records define branching by `drift_policy` or
  alternatives under `short_pause_policy`, CR-061 is the active contract for
  current implementation and verification.

---

# Files Likely Affected

- `src/akkapros/config/default.yaml`
- `demo/akkapros/prosmaker/corpus-demo.yaml`
- `demo/akkapros/lexlinks/construct-demo.yaml`
- `src/akkapros/cli/phonetizer.py`
- `src/akkapros/cli/fullprosmaker.py`
- `src/akkapros/lib/config.py`
- `src/akkapros/lib/helpmsg.py`
- `src/akkapros/lib/phonetize.py`
- `docs/akkapros/phonetizer.md`
- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/varco-verification.md`
- tests touching phonetizer config/flags/help/runtime branching

---

# Acceptance Criteria

- [x] No maintained non-temporary YAML file in the repository contains
      `short_pause_policy` or `drift_policy`.
- [x] `phonetizer` no longer accepts `--short-pause-policy` or
      `--drift-policy`.
- [x] `fullprosmaker` no longer accepts `--phonetize-short-pause-policy` or
      `--phonetize-drift-policy`.
- [x] Runtime/config mapping/help text no longer expose either option.
- [x] Phase 2 drift behavior matches former extensible behavior by default and
      has no strict branch.
- [x] Short-pause behavior remains stable under one fixed non-configurable
      algorithm.
- [x] Passing removed keys through config file or `--option` path fails with
      explicit removed-option diagnostics.
- [x] User-facing docs under `docs/` and examples are updated to remove these
      options.
- [x] Tests and self-tests are updated and pass with removed-option contract.

---

# Risks / Edge Cases

- Existing user configs may still include removed keys.
- Existing automation may still pass removed CLI flags.
- Historical internal docs will still mention old behavior; readers need clear
  supersession guidance.

Mitigation:

- Fail fast with explicit removal diagnostics.
- Add migration note in user-facing docs.

---

# Testing Strategy

Unit tests:

- config parser rejects removed keys with explicit message
- phonetizer/fullprosmaker arg parsing rejects removed flags
- drift realization path no longer branches on removed policy

Integration tests:

- stage pipeline still succeeds with default config after key removal
- outputs remain stable against refreshed expectations where behavior is
  unchanged

Manual tests:

- run phonetizer and fullprosmaker using prior command lines that included
  removed options and verify clear removal errors
- run documentation examples end to end

---

# Rollback Plan

If regressions are found, restore the previous two options temporarily behind a
deprecation marker and reopen a follow-up CR for phased removal.

---

# Related Issues

- CR-040
- CR-042
- CR-044
- CR-059
- REQ-026
- REQ-027
- REQ-031

---

# Tasks

## Implementation

- [x] Remove both options from config schema/defaults and mapping
- [x] Remove both options from CLI surfaces
- [x] Fix internal drift and short-pause behavior to non-configurable paths
- [x] Add explicit removed-option diagnostics

## Tests

- [x] Update/remove tests tied to policy toggles
- [x] Add rejection tests for removed options
- [x] Re-run phonetizer/fullprosmaker self-tests and project pytest

## Documentation

- [x] Update user docs and examples under `docs/`
- [x] Update non-temporary YAML examples and defaults
- [x] Add migration note for removed options

## Review

- [x] Confirm supersession references are clear
- [x] Verify acceptance criteria

---

# Implementation Blockers

None at draft creation.

---

# Notes

- This CR intentionally removes user-facing configurability for two policy
  switches while preserving current effective runtime behavior.
- Completed on 2026-04-15 with code, YAML, docs, and test updates.
