---
adr_id: ADR-034
status: Proposed
created: 2026-03-30
updated: 2026-03-30
superseded_by: null
---

# 34. Prosody Mora Modes and Explicit-Link Locking

## Plain Summary

Keep the current bimoraic prosody behavior as the default, but add a second
mono-mode that removes mora-parity gating while keeping the existing
accentuation hierarchy and legality rules.
At the same time, preserve explicit `+` links as user-imposed prosodic locks:
words linked before the eligible tail must not be accentuated even if they are
content words.

## Context and Problem Statement

The current prosody engine implements a bimoraic model where accentuation is
attempted only when a word or resolved unit has odd mora parity. Researchers
now need a comparative mode aligned with the conventional academic model, where
accentuation is not conditioned on odd/even parity.

However, explicit `+` links already carry user-supplied prosodic structure. The
new mode must not make linked pre-tail words freely accentuable merely because
parity gating is removed. The implementation must therefore separate three
questions that are partially conflated in the current code:

- whether a token or unit is structurally eligible for accentuation
- whether the current mora mode imposes a parity gate before attempting it
- whether merging should continue because no legal internal accentuation site
  exists

## Decision Drivers

- Preserve backward compatibility for the default prosody model
- Support direct comparison with the academic non-bimoraic workflow
- Preserve explicit user-supplied prosodic structure
- Keep merge traversal deterministic and scientifically explainable
- Avoid conflating parity state with structural eligibility

## Considered Options

- Extend the current parity-gated design with a second mora mode and explicit
  structural locking.
- Replace bimoraic gating entirely with mono-style always-accentuate behavior.
- Keep the current behavior only and require academic comparisons outside the
  repository.

## Decision Outcome

Chosen option: keep the current bimoraic mode as default, add a mono-mode that
removes parity gating for eligible standalone words and units, and explicitly
preserve user-provided `+` links as structural locks on pre-tail linked words.

Under this decision:

- `bi` remains the default and preserves current outputs.
- `mono` attempts accentuation for eligible non-function standalone words even
  when their mora count is already even.
- Explicit `+` chains continue to form mandatory prosodic groups.
- Within an explicit `+` chain, words before the eligible tail remain
  ineligible for accentuation even when they are content words.
- Merge traversal remains deterministic, but mono-mode must not rely on the
  old parity-based notion that an even unit is already resolved.

## Pros and Cons of the Options

### Dual-mode prosody with explicit-link locking (chosen)

- Good, because it preserves the current bimoraic model unchanged for existing
  users.
- Good, because it adds a direct comparison mode for academic stress practice.
- Good, because it keeps user-marked `+` structure authoritative.
- Good, because it clarifies the difference between structural eligibility and
  parity gating.
- Bad, because implementation must carefully refactor decision points that
  currently assume parity and eligibility are the same thing.

### Replace bimoraic gating entirely

- Good, because implementation would become simpler in the short term.
- Bad, because it would break the repository's current core realization model.
- Bad, because it would invalidate existing outputs, tests, and documentation.

### Keep current behavior only

- Good, because no new logic is required.
- Bad, because it blocks in-repository comparison with the academic model.

## Implications and Consequences

- `prosmaker` and `fullprosmaker` must expose a `--mora-mode {bi|mono}` option,
  defaulting to `bi`.
- Front matter must record the selected `mora_mode` so downstream artifacts are
  interpretable.
- The implementation should replace parity-only `needs_accentuation` semantics
  with a clearer mode-aware eligibility or attempt policy.
- Mono-mode changes the role of merge traversal: merge is no longer skipped
  just because a unit is even; instead, merge decisions should depend on
  structural constraints and the availability of legal internal accentuation.
- Tests must preserve all existing bimoraic expectations unchanged and add new
  mono-mode coverage.
- User documentation must explain that mono-mode changes the trigger for
  accentuation, not the underlying `lob` / `sob` site-selection hierarchy.

## Links

- Related ADR: [ADR-008](008-bimoraic-prosody-and-accent-styles.md)
- Related ADR: [ADR-009](009-function-word-and-merge-policy.md)
- Related ADR: [ADR-020](020-deterministic-merge-traversal.md)
- Related REQ: [REQ-019](../req/019-prosody-mora-mode-selection.md)
- Related CR: [CR-027](../cr/027-add-prosody-mora-mode-selection.md)
- Code: `src/akkapros/lib/prosody.py`
- CLI: `src/akkapros/cli/prosmaker.py`
- CLI: `src/akkapros/cli/fullprosmaker.py`

## Implementation Notes (optional)

- Prefer a mode-aware predicate such as "should attempt accentuation" or
  equivalent over reusing parity-only `needs_accentuation` naming.
- Preserve explicit-link locking as a structural rule independent of parity.
- Validate mono-mode against examples where a formerly even standalone word now
  accentuates, while linked pre-tail words remain protected.

## Reviewed By

- Pending maintainer review