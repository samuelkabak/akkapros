---
review_id: review-004
status: Done
created: 2026-03-29
updated: 2026-03-29
reviewer: GitHub Copilot
scope: >-
  docs/internal/adr/*.md, docs/internal/cr/*.md, docs/internal/req/*.md;
  status-field consistency relative to the policy that all pre-existing records
  other than the newly added CR-024, CR-025, CR-026, REQ-017, and REQ-018
  should already be in a terminal state.
---

# Code and Project Review — Internal Spec Status Consistency

## 1. Executive Summary

The internal documentation set is now status-consistent with the requested rule
that all previously existing ADRs, CRs, and REQs should already be in a
terminal state. Older ADRs are aligned to `Accepted`, older implemented CRs are
aligned to `Done`, `CR-020` remains `Rejected`, and older implemented REQs are
aligned to `Implemented`. The remaining documentation issue is narrower than
status consistency: requirement-to-CR traceability is still partial for some
historically implemented requirements.

## 2. Architecture Assessment

### 2.1 Strengths

- The new documents are internally cross-linked correctly: ADR-033, REQ-018,
  and CR-026 form a coherent set; CR-024, CR-025, REQ-017, and REQ-018 are
  clearly marked as open work.
- All ADRs are now in the terminal `Accepted` state.
- The CR template already defines a coherent terminal workflow vocabulary:
  `Draft`, `Approved`, `Rejected`, `Done`.
- Several older REQs now have explicit implementation links that match the CR
  records, including REQ-008, REQ-011, REQ-012, REQ-013, REQ-015, and REQ-016.

### 2.2 Areas for Improvement

- Status vocabulary is not normalized across ADR, CR, and REQ records.
- Not every historically implemented requirement maps cleanly to one discrete
  implementation CR from internal-doc content alone.
- A few requirement records still need explicit implementation-link decisions or
  a deliberate statement that no single implementation CR is identifiable.

## 3. Code Quality Assessment

- Not applicable to production code; this review concerns document metadata.
- Metadata quality is currently uneven because frontmatter status values mix
  terminal states, workflow states, and narrative comments.

## 4. Documentation Assessment

- The rule in [docs/internal/README.md](docs/internal/README.md) allows mixed
  status vocabularies by document type, and the current records now conform to
  that document-type-specific terminal-state policy.
- The current templates do not enforce a single repository-wide definition of
  “terminal” status across ADRs, CRs, and REQs.
- The CR template itself is internally clear; the remaining documentation gap is
  usually traceability, not CR status vocabulary.

## 5. Research / Functional Assessment

- Functional content of the new specs appears coherent.
- The remaining procedural gap is requirement traceability rather than status
  state.

## 6. Process and Engineering Practices

- ADRs:
  - Terminal and consistent: all ADRs are `Accepted`

- CRs:
  - Template reference status vocabulary: `Draft`, `Approved`, `Rejected`, `Done`
  - Git-log-verified implemented older CRs: `CR-004`, `CR-005`, `CR-012`, and
    `CR-013` have implementation commits and should be treated as completed work
  - Rejected older CRs: `CR-020`
  - Older terminal CRs after harmonization: all pre-existing CRs except
    `CR-020` are `Done`; `CR-020` is `Rejected`
  - Newly open CRs: `CR-024`, `CR-025`, `CR-026` are appropriately `Draft`

- REQs:
  - Harmonized implemented REQs with explicit CR links: `REQ-008` → `CR-004`,
    `REQ-011` → `CR-012`, `REQ-012` → `CR-016` / `CR-017` / `CR-019`,
    `REQ-013` → `CR-018`, `REQ-015` → `CR-022`, `REQ-016` → `CR-023`
  - Older REQs still requiring explicit traceability judgment: examples include
    baseline or research-model requirements such as `REQ-009`, where no single
    implementation CR is identifiable with sufficient confidence from internal
    docs alone
  - Newly open REQs: `REQ-017`, `REQ-018` are appropriately `Draft`

## 7. Recommendations (Priority Order)

1. High: Decide the canonical terminal-state vocabulary for each document type.
Minimal next step: keep `Accepted` for ADRs, keep the CR-template vocabulary
for CRs, and retain `Implemented` as the terminal requirement status where a
requirement has been realized.

2. High: Complete requirement-to-CR traceability where evidence is strong.
Minimal next step: add implementation-CR links for older REQs whenever the
internal content supports the mapping with high confidence.

3. High: Treat the CR set as harmonized against git history. Minimal next step:
keep pre-implementation CRs at `Draft` or `Approved`, use `Done` once a CR has
been implemented, and reserve `Rejected` for abandoned CRs such as `CR-020`.

4. Medium: For requirements that do not map to one discrete CR, record that
fact explicitly instead of leaving traceability implied. Minimal next step: add
a short note in the requirement body when no single implementation CR can be
identified with sufficient confidence.

5. Medium: Normalize status metadata formatting. Minimal next step: avoid
parenthetical prose in `status:` fields, keep explanatory rollout notes in the
document body, and apply this cleanup to remaining requirement records.

## 8. Summary Verdict

The new ADR/CR/REQ additions are coherent with one another. After git-log
verification, ADR acceptance alignment, and CR status harmonization, the
status-consistency issue itself is resolved. Remaining follow-up work is mostly
about requirement traceability, not about ADR or CR terminal states.