# Change Request: Rejected lex-input metrics extension

CR-ID: CR-020
Status: Rejected
Priority: High
Impact: Mutative
Created: 2026-03-26
Updated: 2026-03-27
Implements: None
---

# Summary

This CR proposed adding lexical-aware metrics counters derived from a dedicated
`_lex.txt` companion file and a `--lex-input` option. The proposal is rejected
because the dependency it relied on has been discarded in favor of pipeline-wide
front matter and metadata propagation.

If this metrics enhancement is revived later, it must be redesigned to consume
approved front matter metadata instead of a lex-only side channel.

---

# Motivation

The original proposal depended on `CR-018` as a lexical-output mechanism for
metadata propagation. That approach is no longer the approved direction.

Rejecting this CR preserves traceability while preventing implementation work
against an obsolete metadata contract.

---

# Scope

## Included

- Record that the lex-input design path is not approved.
- Preserve the historical rationale for rejection.
- Redirect future work to the front matter contract.

## Not Included

- Any implementation work for `_lex.txt`-based metrics inputs.
- Any new metrics schema or CLI changes under this CR.

---

# Current Behavior

Metrics outputs do not yet include the lex-input-based counters proposed in the
original draft of this CR. The pipeline also does not use `_lex.txt` as the
approved metadata propagation mechanism.

---

# Proposed Change

No change is approved under this CR.

Any future request for construct-noun or related propagated counters in metrics
must be refiled or amended against the front matter design introduced by
[ADR-027](../adr/027-yaml-front-matter-for-cli-pipeline-files.md),
[REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md), and
[CR-018](018-add-cli-file-front-matter-and-metadata-propagation.md).

---

# Technical Design

Not applicable. The previously proposed `_lex.txt` pairing and `--lex-input`
surface are rejected.

---

# Files Likely Affected

No implementation files are authorized by this CR in its rejected state.

---

# Acceptance Criteria

- [ ] No implementation proceeds on the rejected `_lex.txt` / `--lex-input`
      design path under `CR-020`.
- [ ] Any revived work is specified against the approved front matter contract
      rather than the discarded lexical-output dependency.

---

# Risks / Edge Cases

Possible issues:

- Historical readers may assume `CR-020` remains active unless they notice the
  rejected status.
- A future metrics change could accidentally revive `_lex.txt` coupling if the
  rejection rationale is ignored.

---

# Testing Strategy

No implementation testing applies because this CR is rejected.

---

# Rollback Plan

No rollback applies. This document records a rejected proposal.

---

# Related Issues

- Rejected because the earlier lex-output path was discarded and replaced by
  [ADR-027](../adr/027-yaml-front-matter-for-cli-pipeline-files.md),
  [REQ-013](../req/013-cli-file-front-matter-and-metadata-propagation.md), and
  [CR-018](018-add-cli-file-front-matter-and-metadata-propagation.md).
- Still conceptually adjacent to metrics-output work in
  [CR-017](017-word-mora-statistics-reorg.md) and
  [CR-019](019-metrics-deltac-meanc-dual-lines-and-varcoc-unitless.md).

---

# Tasks

## Implementation

- [ ] None. Rejected.

## Tests

- [ ] None. Rejected.

## Documentation

- [ ] Ensure related specs point to front matter instead of `_lex.txt`.

## Review

- [ ] Reopen only if a new metrics request is written against the front matter
      contract.

---

# Notes for CR-020

This document remains in the repository as a historical record of a rejected
design path. The rejection is intentional and not a temporary pause.
