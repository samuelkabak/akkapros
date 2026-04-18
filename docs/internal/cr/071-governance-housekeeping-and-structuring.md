---
cr_id: CR-071
status: Done
priority: Medium
impact: Mutative
created: 2026-04-18
updated: 2026-04-18
implements: 'ADR-048, REQ-037'
---

# Change Request: Governance Housekeeping and Structuring

## Summary

Define and tighten the repository contract for housekeeping of `docs/internal/`
and align the supporting governance scripts with that contract.

The current governance folder already has a documented layout and workflow, but
the helper scripts do not fully implement the documented identifier and indexing
rules. In particular, the README promises canonical identifiers beyond `999`
such as `CR-A00`, while the current housekeeping scripts still assume only
three-digit numeric prefixes in key paths. This CR formalizes the missing
housekeeping/structuring rules and requires the associated scripts to support
the active governance contract rather than silently narrowing it.

---

## Motivation

- Governance housekeeping improvement
- Script/contract alignment
- Maintenance hardening

The repository now depends on `docs/internal/` as an active governance layer.
That makes the folder layout, numbering rules, generated indexes, and commit
helper behavior part of the working engineering contract rather than informal
convenience tooling.

Quick review findings grounded in the current repository:

- `docs/internal/README.md` defines base-36 continuation after `999` and allows
  canonical references such as `CR-A00`.
- `scripts/update-indexes.py` still matches only `NNN-...` filenames for ADRs,
  CRs, and REQs, and only 1-3 digit numeric forms for reviews.
- `scripts/git-commit-cr.py` currently rejects any CR identifier that is not
  exactly three digits and therefore cannot operate on future canonical CR IDs
  such as `A00`.
- `tests/test_git_commit_cr_script.py` codifies the three-digit-only behavior,
  which means the limitation is both implemented and tested.
- Current housekeeping behavior is therefore narrower than the documented
  governance policy.

This CR addresses that mismatch directly instead of allowing the governance
folder to drift into a documented-but-unenforced state.

---

## Scope

### Included

- Define the active housekeeping contract for `docs/internal/` structure,
  numbering, generated indexes, and CR commit-helper behavior.
- Require governance scripts to support the documented canonical identifier
  scheme used by the internal governance README.
- Require index generation to include all valid governance records under the
  active naming scheme, including higher identifiers after `999`.
- Require housekeeping tools to report unsupported or malformed governance files
  explicitly instead of silently omitting them from generated outputs.
- Require the commit helper to accept canonical CR identifiers, resolve the
  matching CR file, and build the commit subject from the CR title.
- Require test coverage for the supported governance numbering and housekeeping
  paths.
- Require the governance README and any script help text to describe the same
  authoritative rules.

### Not Included

- Changing production runtime behavior outside governance/documentation tools.
- Reorganizing `docs/internal/` into a different set of top-level folders.
- Renumbering existing ADRs, CRs, REQs, or reviews.
- Defining new document types beyond `adr/`, `cr/`, `req/`, and `review/`.

---

## Current Behavior

Current documented governance structure in `docs/internal/README.md` states:

- `docs/internal/` contains `adr/`, `cr/`, `req/`, and `review/`
- identifiers continue after `999` as `A00`, `A01`, ...
- canonical references may use forms such as `CR-A00`
- index pages are maintained by `python scripts/update-indexes.py`
- CR implementation commits must use the pattern
  `Implement CR-{CR number}: {CR title}`

Current script behavior does not fully match that contract:

- `scripts/update-indexes.py` only indexes ADR/CR/REQ files whose names match
  `^(\d{3})-...\.md$`
- the review indexer only accepts numeric forms such as `001-review.md` or
  `review-001.md`
- `scripts/git-commit-cr.py` requires the CLI argument to be exactly three
  digits and searches only for files matching `{cr_number}-*.md`
- `tests/test_git_commit_cr_script.py` asserts that non-three-digit CR numbers
  are rejected

Current consequence:

- the documented governance numbering policy cannot be carried through the
  housekeeping scripts once identifiers move beyond three-digit numeric form
- valid future governance records may be silently skipped by index generation
- the commit helper cannot build canonical commit subjects for future CR IDs

---

## Proposed Change

Adopt the following governance-housekeeping contract.

### 1. Authoritative structure contract

- `docs/internal/README.md` remains the authoritative human-readable contract
  for governance folder structure, numbering, and housekeeping expectations.
- `scripts/update-indexes.py` and `scripts/git-commit-cr.py` must implement the
  same active identifier rules documented there.
- If the documented numbering model changes later, the scripts and their tests
  must be updated in the same change set.

### 2. Canonical identifier support

- Governance housekeeping tooling must support the documented identifier family:
  `000` through `999`, then `A00` through `A99`, then `B00` and onward.
- This applies at minimum to ADR, CR, and REQ file discovery and sorting.
- Review tooling must also have an explicit documented stance: either support
  the same higher-order identifier family or state clearly and consistently that
  reviews remain numeric-only. Silent ambiguity is not allowed.

### 3. Index-generation behavior

- Index generation must include every valid governance file that follows the
  active naming contract for its document type.
- Sorting must preserve governance order across numeric and post-`999`
  identifiers.
- Unsupported or malformed files in the governance folders must be surfaced
  explicitly through a warning or non-zero failure path rather than being
  silently ignored.
- The generated index format may remain otherwise unchanged.

### 4. CR commit-helper behavior

- The CR commit helper must accept canonical CR identifiers in the same format
  the governance README defines, including post-`999` forms when they become
  valid.
- It must resolve the unique matching CR file from `docs/internal/cr/` and
  extract the title from the CR heading.
- It must continue building the commit subject in the canonical form
  `Implement CR-{ID}: {title}`.
- Error messages must describe identifier-format problems in terms of the
  active contract rather than the legacy three-digit-only rule.

### 5. Housekeeping verification

- Governance tooling must be covered by focused tests for discovery, ordering,
  and commit-subject generation under the active identifier policy.
- The repository should have a documented housekeeping path that maintainers can
  run after adding, renaming, or removing governance files.
- That housekeeping path must include index refresh and verification of any
  script assumptions relevant to governance records.

---

## Technical Design

Architecture notes:

Components:

- `docs/internal/README.md`
- `docs/internal/adr/index.md`
- `docs/internal/cr/index.md`
- `docs/internal/req/index.md`
- `docs/internal/review/index.md`
- `scripts/update-indexes.py`
- `scripts/git-commit-cr.py`
- script-focused tests

Implementation direction:

- Centralize or standardize governance identifier parsing so the README, indexer,
  and commit helper operate on one consistent notion of valid IDs.
- Replace three-digit-only filename discovery in the indexer with parsing that
  supports the documented post-`999` identifier progression.
- Replace three-digit-only CLI validation in the CR commit helper with
  canonical-ID validation aligned to the README.
- Add explicit handling for malformed governance filenames so omissions are not
  silent.
- Add or update tests that pin discovery, sorting, and commit-message behavior
  across both numeric and post-numeric identifiers.

Design constraint:

- This CR is a governance-tooling contract change, not a production-feature
  change. The work must stay scoped to `docs/internal/`, governance scripts,
  and their tests/docs.

---

## Files Likely Affected

`docs/internal/README.md`
`docs/internal/adr/index.md`
`docs/internal/cr/index.md`
`docs/internal/req/index.md`
`docs/internal/review/index.md`
`scripts/update-indexes.py`
`scripts/git-commit-cr.py`
`tests/test_git_commit_cr_script.py`

---

## Acceptance Criteria

- [x] The governance README and the housekeeping scripts describe and implement
      the same identifier policy.
- [x] `scripts/update-indexes.py` indexes valid ADR/CR/REQ files beyond `999`
      according to the documented canonical numbering scheme.
- [x] Review indexing has an explicit and enforced contract for higher-order
      identifiers instead of an implicit silent omission path.
- [x] `scripts/update-indexes.py` surfaces malformed or unsupported governance
      filenames explicitly.
- [x] `scripts/git-commit-cr.py` accepts canonical CR identifiers supported by
      the governance policy and builds commit messages in canonical form.
- [x] Legacy three-digit identifiers continue to work.
- [x] Automated tests cover identifier parsing, ordering, discovery, and commit
      message generation for governance tooling.
- [x] Governance housekeeping steps are documented clearly enough that a
      maintainer can refresh indexes and verify the contract after record
      changes.

---

## Risks / Edge Cases

- Existing tests currently pin the narrower three-digit-only rule and will need
  coordinated updates once the broader identifier contract becomes active in the
  scripts.
- Review files currently use numeric patterns only; broadening review IDs may
  require either explicit support or an explicit exception policy.
- If malformed files continue to be skipped silently, maintainers may falsely
  believe generated indexes are complete.
- Sorting across numeric and post-`999` identifiers must be deterministic and
  documented to avoid future ordering disputes.

---

## Testing Strategy

Unit tests:

- identifier parser accepts `071`, `999`, `A00`, `A01`, and `B00` as valid
  governance IDs where applicable
- index generation orders mixed identifier families correctly
- malformed governance filenames trigger an explicit warning or failure path
- CR commit helper builds `Implement CR-A00: ...` for a valid post-`999` CR

Integration tests:

- regenerate governance indexes in a fixture repo tree containing mixed valid
  identifiers and verify output completeness/order

Manual tests:

- run the housekeeping flow after adding a synthetic higher-order governance
  record and confirm that indexes and commit helper behavior remain aligned with
  the documented policy

---

## Rollback Plan

If broader identifier support cannot be delivered safely, revert the scripts
and README to one explicitly documented numeric-only governance policy.

Do not keep the current mixed state where the README promises higher-order
identifiers but the housekeeping scripts silently reject them.

---

## Related Issues

- [CR-070](070-coalesce-consecutive-eol-pause-rows-while-preserving-repeated-eol-text.md)
- `docs/internal/README.md`
- `scripts/update-indexes.py`
- `scripts/git-commit-cr.py`
- `tests/test_git_commit_cr_script.py`

---

## Tasks

### Implementation

- [x] Align governance identifier parsing across README, indexer, and commit
      helper
- [x] Extend or explicitly constrain review-ID handling
- [x] Add explicit malformed-file reporting to governance housekeeping scripts

### Tests

- [x] Add script tests for post-`999` identifier discovery and ordering
- [x] Add commit-helper tests for canonical non-numeric CR identifiers
- [x] Retain coverage for legacy numeric identifiers

### Documentation

- [x] Update governance README housekeeping guidance if script behavior changes
- [x] Document the authoritative housekeeping flow for governance records

### Review

- [x] Verify that generated indexes include every valid governance record under
      the active naming policy
- [x] Verify that the commit helper emits canonical commit messages for valid CR
      identifiers

---

## Implementation Blockers

---

## Notes

- This CR is based on a quick repository review of the current governance README,
  index-generation script, CR commit helper, and existing script tests.
- Implementation remains deferred; this record defines the missing governance
  housekeeping contract only.
