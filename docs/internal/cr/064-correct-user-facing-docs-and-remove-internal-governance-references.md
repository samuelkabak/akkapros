---
cr_id: CR-064
status: Done
priority: High
impact: Mutative
created: 2026-04-17
updated: 2026-04-17
implements: None
---

# Change Request: Correct User-Facing Docs and Remove Internal Governance References

# Summary

Correct the user-facing package documentation so it no longer exposes internal
software-management artifacts and so the phonetizer public documentation aligns
with the live implementation.

This CR responds to the findings in
`docs/internal/review/010-cr-063-phonetizer-solver-review.md` and to the
developer-facing policy now stated in `docs/internal/README.md`: user-facing
documentation must describe package behavior directly and must not cite ADRs,
CRs, REQs, review files, or `docs/internal/` paths. The immediate target is the
phonetizer public documentation set, but the CR also requires a broader scrub of
user-facing package docs that currently expose internal governance references.

---

# Motivation

Why is this change needed?

- Documentation correctness
- Public/private boundary hygiene
- Research-facing clarity

The current public documentation leaks internal governance records into
research-facing pages and also contains several phonetizer statements that no
longer match the live solver. This is now a documentation contract bug: readers
can be sent to deleted CRs, can see pause-row examples that do not match the
runtime row format, and can be told pause behavior that the solver does not
actually implement.

---

# Scope

## Included

- Correct the governing-record section in
  `docs/akkapros/phonetizer-algorithm.md` so it no longer cites deleted split
  CRs or any internal governance artifacts.
- Correct `docs/akkapros/phonetizer-phone-file-guide.md` so its pause-row
  examples match the live pause-row contract emitted by `phonetize.py`.
- Correct `docs/akkapros/phonetizer.md` so its pause behavior, residual-drift
  description, and merged-unit raw-drift explanation match the live solver.
- Remove user-facing references to ADRs, CRs, REQs, review files, and
  `docs/internal/` paths from public package documentation, including pages
  under `docs/akkapros/` and onboarding docs under `docs/`.
- Replace internal-record references with direct behavioral explanations,
  stable public wording, or ordinary cross-links between user-facing pages.
- Update any affected examples, prose, and cross-references so the user-facing
  documentation remains coherent after the internal references are removed.

## Not Included

- Any production code change in `src/`.
- Any test change unless a later implementation CR explicitly decides public-doc
  corrections also need additional coverage or verification helpers.
- Any change to the content of historical internal ADR/CR/REQ/review files
  beyond ordinary cross-link maintenance if needed.

---

# Current Behavior

User-facing documentation currently contains both implementation-alignment
errors and internal-governance leakage.

Known phonetizer public-doc problems identified by review:

- `docs/akkapros/phonetizer-algorithm.md` cites deleted `CR-064` and `CR-065`
  and also exposes internal-record framing directly to the reader.
- `docs/akkapros/phonetizer-phone-file-guide.md` includes pause-row examples
  whose field values do not match the live row contract emitted by
  `src/akkapros/lib/phonetize.py`.
- `docs/akkapros/phonetizer.md` states that long pauses must reset drift to
  zero even though the live pause solver selects a preferred in-band beat
  multiple and may retain residual drift. The page also under-explains raw
  unfolded drift on internal merged-unit closures.

Known broader public-doc governance leaks already observed under `docs/akkapros/`
include references such as:

- `CR-005` syntax wording in `fullprosmaker.md` and `syllabifier.md`
- CR/REQ wording in `varco-verification.md`
- CR wording in `metrics-coverage-matrix.md`
- ADR/CR links in `utils.md`
- ADR wording in `release-strategy.md`

These references violate the current policy in `docs/internal/README.md` that
internal software-management artifacts are developer-facing only.

---

# Proposed Change

Revise the public documentation so it stands on its own without exposing the
internal governance layer.

Desired behavior:

- User-facing docs describe current package behavior directly.
- Public docs may cross-link to other public docs, but not to `docs/internal/`
  artifacts.
- Historical CR/ADR/REQ identifiers are removed from public prose unless a new
  explicit public-facing policy later permits some separate stable form of
  changelog-style reference.
- The phonetizer public docs must match the live solver and row contract.

For the three reviewed phonetizer pages, the public-doc contract after this CR
must be:

- no internal-governance section or wording aimed at internal record lineage
- correct pause-row examples
- correct residual-drift behavior for both short and long pauses
- explicit explanation that internal merged-unit closures may carry raw
  unfolded drift until the unit-closing `F` boundary is realized

---

# Technical Design

Explain how it should be implemented.

Components:

- `docs/akkapros/phonetizer-algorithm.md`
- `docs/akkapros/phonetizer-phone-file-guide.md`
- `docs/akkapros/phonetizer.md`
- Other user-facing docs under `docs/akkapros/`
- User-facing onboarding docs under `docs/`

Approach:

1. Audit user-facing docs for any occurrence of:
   - `ADR-`
   - `CR-`
   - `REQ-`
   - `review-`
   - `docs/internal`
2. For each occurrence, decide whether it is:
   - a behavior explanation that should be rewritten in direct public language,
   - a user-facing cross-link that should instead point to another public doc,
   - or stale governance/context wording that should simply be removed.
3. For the phonetizer doc set, verify prose and examples against the live code
   in `src/akkapros/lib/phonetize.py` rather than against deleted or historical
   spec splits.
4. Keep internal-governance context only in `docs/internal/` artifacts such as
   CRs, REQs, ADRs, and reviews.

Documentation rewrite rules:

- Prefer stable behavioral wording over implementation-history wording.
- Public docs must not tell readers that behavior was “removed in CR-061” or
  “defined by REQ-030”; instead they must state the current behavior directly.
- Public docs must not ask the reader to consult internal records to understand
  package behavior.
- When public docs need cross-reference, they should link only to other
  user-facing documentation pages that exist in `docs/` or `docs/akkapros/`.

Verification guidance:

- Use targeted searches over user-facing docs to confirm removal of internal
  governance references.
- Re-read the affected phonetizer pages against `src/akkapros/lib/phonetize.py`
  to confirm prose/examples match runtime behavior.

---

# Files Likely Affected

docs/akkapros/phonetizer-algorithm.md  
docs/akkapros/phonetizer-phone-file-guide.md  
docs/akkapros/phonetizer.md  
docs/akkapros/fullprosmaker.md  
docs/akkapros/syllabifier.md  
docs/akkapros/varco-verification.md  
docs/akkapros/metrics-coverage-matrix.md  
docs/akkapros/utils.md  
docs/akkapros/release-strategy.md  
docs/GETTING_STARTED.md  

The exact file list may expand if the audit finds other user-facing pages under
`docs/` or `docs/akkapros/` with internal-artifact references.

---

# Acceptance Criteria

- [x] `docs/akkapros/phonetizer-algorithm.md` no longer cites deleted CR files,
      no longer exposes ADR/CR/REQ lineage to the public reader, and still
      describes the live phonetizer solver accurately.
- [x] `docs/akkapros/phonetizer-phone-file-guide.md` pause-row examples match
      the live pause-row contract emitted by `src/akkapros/lib/phonetize.py`.
- [x] `docs/akkapros/phonetizer.md` no longer claims that long pauses must
      always reset drift to zero and instead documents the actual preferred-
      multiple plus residual-drift behavior.
- [x] `docs/akkapros/phonetizer.md` explicitly explains that internal merged-
      unit closures may show raw unfolded drift until the unit-closing `F`
      boundary is realized.
- [x] User-facing documentation under `docs/` and `docs/akkapros/` contains no
      references to ADR identifiers, CR identifiers, REQ identifiers, review
      identifiers, or `docs/internal/` paths.
- [x] Any removed internal reference is replaced either by direct behavioral
      wording or by a user-facing cross-reference that keeps the page readable.
- [x] Internal documentation policy in `docs/internal/README.md` remains the
      developer-facing source of truth for the public/internal documentation
      separation.

---

# Risks / Edge Cases

Possible issues:

- Removing internal references too mechanically could leave pages under-
  explained if direct replacement prose is not added.
- Some pages currently mix user guidance with developer-facing verification
  language; those must be rewritten carefully rather than simply stripped.
- A broad grep-only cleanup could miss indirect wording such as “Removed in
  CR-061” if only links are inspected.
- Some docs under `docs/akkapros/` may function partly as research notes rather
  than end-user manuals; this CR still treats them as user-facing because they
  are outside `docs/internal/`.

---

# Testing Strategy

Documentation verification:

- search user-facing docs for `ADR-`, `CR-`, `REQ-`, `review-`, and
  `docs/internal`
- manually review the phonetizer public docs against the live runtime behavior

Manual checks:

- inspect the corrected pause-row examples against the actual pause-row field
  contract
- inspect corrected pause-drift prose against `_pause_duration_and_drift()`
- inspect merged-unit drift prose against `_should_fold_completed_syllable()`
  and `realize_phone_rows()`

---

# Rollback Plan

If a public-doc rewrite introduces ambiguity or factual drift, revert only the
affected documentation edits and rework the public wording without restoring
references to internal governance artifacts.

---

# Related Issues

- `docs/internal/review/010-cr-063-phonetizer-solver-review.md`
- `docs/internal/README.md`
- `docs/internal/cr/063-tune-the-phonetizer-solver.md`

---

# Tasks

## Implementation

- [x] Audit user-facing docs under `docs/` and `docs/akkapros/` for internal
      governance references.
- [x] Rewrite `docs/akkapros/phonetizer-algorithm.md` into purely user-facing
      behavioral documentation.
- [x] Rewrite `docs/akkapros/phonetizer-phone-file-guide.md` examples and any
      dependent wording to match the live row contract.
- [x] Rewrite `docs/akkapros/phonetizer.md` pause and drift wording to match
      the live solver.
- [x] Remove or replace remaining internal-artifact references from the rest of
      the user-facing docs found by the audit.

## Tests

- [x] Run documentation search checks confirming that no user-facing docs still
      contain ADR/CR/REQ/review/internal-path references.
- [x] Manually compare the corrected phonetizer public docs against the live
      runtime behavior in `src/akkapros/lib/phonetize.py`.

## Documentation

- [x] Keep the developer-facing public/internal separation rule in
      `docs/internal/README.md` synchronized with this CR.
- [x] Update user-facing cross-links as needed so removed internal references do
      not leave broken reading paths.

## Review

- [x] Verify that the three phonetizer public-doc findings from review-010 are
      fully resolved.
- [x] Verify that broader user-facing docs no longer expose internal governance
      artifacts.


---

# Implementation Blockers

Leave empty unless implementation becomes blocked.


---

# Notes

- This CR is documentation-only. It does not request a runtime solver change.
- The goal is not to erase internal history from `docs/internal/`; the goal is
  to keep that governance layer out of the user-facing documentation surface.
- The phonetizer-specific corrections in this CR come directly from the review
  findings already recorded in review-010 and should be treated as strict
  corrections, not optional polish.