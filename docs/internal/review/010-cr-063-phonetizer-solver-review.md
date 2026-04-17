---
review_id: review-010
status: Done
created: 2026-04-17
updated: 2026-04-17
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  docs/internal/cr/063-tune-the-phonetizer-solver.md,
  src/akkapros/lib/phonetize.py,
  docs/akkapros/phonetizer-algorithm.md,
  docs/akkapros/phonetizer-phone-file-guide.md,
  docs/akkapros/phonetizer.md,
  tests/test_phonetize_lib.py,
  and tests/test_integration.py.
---

# Code and Project Review — CR-063 Phonetizer Solver

## 1. Executive Summary

The live phonetizer implementation is substantially aligned with the merged
[CR-063](../cr/063-tune-the-phonetizer-solver.md). The reviewed code in
[src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
implements the core CR-063 requirements directly: ordinary long-vowel recovery
is capped below `very_long_min`, beat folding is fixed rather than
configurable, equivalent-checkpoint mini pauses apply on both drift sides, and
folding is deferred until the prosodic-unit-closing `F` boundary. The main
problems are now public-document drift rather than runtime drift. Three items
need strict correction: the public algorithm page still cites deleted
`CR-064`/`CR-065`, the phone-file guide shows pause-row examples that do not
match the live row contract, and the main phonetizer page still claims that
long pauses must always reset drift to zero even though the live pause solver
selects an in-band beat multiple and may retain residual drift. Unit coverage
is strong and branch-oriented; integration coverage is good for artifact and
pipeline behavior but still thinner than the unit suite for the newest CR-063
solver branches.

## 2. Architecture Assessment

### 2.1 Strengths

- [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  keeps the solver logic concentrated in a small set of phase-owning helpers,
  especially `_vowel_bounds()`, `_normalize_drift_to_nearest_branch()`,
  `_pause_duration_and_drift()`, `_maybe_insert_mini_pause()`,
  `_should_fold_completed_syllable()`, and `realize_phone_rows()`.
- The runtime separation between row construction, duration realization, and
  later intonation assignment remains clear and matches the project’s staged
  phonetizer model.
- The CR-063 changes were implemented at the actual decision points rather than
  patched downstream. The long-vowel cap is enforced in vowel bounds, the
  merged-unit fold restriction is enforced at unit completion, and the debug
  checkpoint invariant is enforced centrally.
- The unit-test suite in
  [tests/test_phonetize_lib.py](../../../tests/test_phonetize_lib.py)
  is unusually explicit. The numbered path tests give good branch visibility
  across normalization, long-vowel recovery, accent distribution, same-
  consonant handling, mini pauses, pause discharge, and drift token writing.

### 2.2 Areas for Improvement

- [docs/akkapros/phonetizer-algorithm.md](../../akkapros/phonetizer-algorithm.md)
  still names deleted `CR-064` and `CR-065` in its governing-record section
  even though those changes were merged into
  [CR-063](../cr/063-tune-the-phonetizer-solver.md). This is active governance
  drift, not just stale prose.
- [docs/akkapros/phonetizer-phone-file-guide.md](../../akkapros/phonetizer-phone-file-guide.md)
  contains pause-row examples whose `boundary` and `accent` fields do not match
  the live runtime contract produced by `_new_pause_row()` in
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py).
  That makes the guide unsafe as a direct parsing reference.
- [docs/akkapros/phonetizer.md](../../akkapros/phonetizer.md)
  still states that long pauses must reset the running drift reserve to zero.
  The live `_pause_duration_and_drift()` logic does not implement a special
  long-pause zero-reset rule; it picks a preferred in-band multiple and can
  preserve residual drift when exact discharge is unavailable.
- The integration suite exercises artifact production and selected solver
  outcomes, but the newest CR-063 branches are still represented more strongly
  in unit tests than in CLI-level end-to-end assertions.

## 3. Code Quality Assessment

- No implementation mismatch was found between
  [CR-063](../cr/063-tune-the-phonetizer-solver.md) and the reviewed solver
  code in [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py)
  for the following behaviors:
  ordinary non-accentual long-vowel capping,
  residual-drift retention,
  fixed beat folding,
  equivalent-checkpoint mini pauses,
  positive-drift mini-pause targeting,
  merged-unit deferred folding, and
  `DEBUG_CHRONO` checkpoint validation.
- The solver code is easier to audit now than in earlier iterations because
  the folded-versus-raw drift distinction is represented explicitly in control
  flow instead of being hidden in later formatting.
- The remaining quality risk is interpretive rather than algorithmic: future
  maintainers could rely on stale public docs and infer behavior that the code
  no longer exposes.
- A smaller maintainability issue remains in
  [tests/test_phonetize_lib.py](../../../tests/test_phonetize_lib.py): some
  test names still reflect the removed optional-fold era, especially the path
  names at 1.4 and 1.5. The assertions are correct, but the labels now encode
  an obsolete mental model.

## 4. Documentation Assessment

- [docs/akkapros/phonetizer-algorithm.md](../../akkapros/phonetizer-algorithm.md)
  is otherwise the strongest public explanation of the live solver. Its step
  order, long-vowel cap, equivalent-branch fold logic, merged-unit `F`-only
  folding, mini-pause targeting, and `DEBUG_CHRONO` invariant all align with
  the reviewed runtime.
- The governing-record section of
  [docs/akkapros/phonetizer-algorithm.md](../../akkapros/phonetizer-algorithm.md)
  must be repaired so the public document reflects the current merged internal
  contract instead of referencing deleted CR files.
- [docs/akkapros/phonetizer-phone-file-guide.md](../../akkapros/phonetizer-phone-file-guide.md)
  correctly explains raw drift on internal `L`/`X`/`E`/`I` rows and canonical
  drift only after `F` or pause closure. However, its sample pause rows are not
  trustworthy until the field values are corrected to match the live row
  emitter.
- [docs/akkapros/phonetizer.md](../../akkapros/phonetizer.md)
  is directionally correct about the artifact surface and downstream role of
  `_ophone.txt` and `_phone.txt`, but it compresses the pause solver too much.
  The statement that long pauses must reset drift to zero is stricter than the
  implementation, and the page would benefit from one explicit note that raw
  unfolded drift may appear on internal merged-unit closures before the final
  `F` row folds it.

## 5. Research / Functional Assessment

Functionally, the CR-063 solver is in good shape.

- The live implementation is deterministic and directly inspectable in
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py).
- The strongest unit coverage appears in
  [tests/test_phonetize_lib.py](../../../tests/test_phonetize_lib.py), which
  explicitly covers:
  `-303 -> +3` normalization,
  deferred fold across a merged unit,
  ordinary long-vowel capping below `very_long_min`,
  positive-drift mini-pause insertion,
  pause residual carry,
  row-level drift token behavior, and
  debug checkpoint failure handling.
- The integration surface in
  [tests/test_integration.py](../../../tests/test_integration.py)
  confirms the stage pipeline, active downstream handoff, short-vowel anchor
  stability under altered `cvc_reference`, and mini-pause insertion without
  corrupting reconstructed `_tilde` text.
- A focused verification slice was also run through the existing task
  `verify-cr060-schema-slice`, which passed `103` tests in `1.77s`. That is a
  useful confirmation that the reviewed phonetizer and downstream contract are
  currently consistent.

The remaining functional coverage gap is not absence of testing, but test-layer
distribution. The newest CR-063 solver branches are well covered at unit level,
while CLI-level assertions do not yet pin every branch that the public docs now
describe.

## 6. Process and Engineering Practices

- The merged governance model is stronger than the current public references.
  [CR-063](../cr/063-tune-the-phonetizer-solver.md) is now the active contract,
  so public docs should stop pointing readers at deleted split records.
- The repository’s path-complete phonetizer unit tests are a strong engineering
  practice and materially improve auditability of solver changes.
- The current review was grounded in code inspection of
  [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py),
  document inspection of the three public phonetizer pages, test inspection of
  [tests/test_phonetize_lib.py](../../../tests/test_phonetize_lib.py) and
  [tests/test_integration.py](../../../tests/test_integration.py), and one
  targeted verification task run.
- No implementation blocker remains at the solver level. The practical next
  engineering work is documentation repair plus a small amount of end-to-end
  coverage broadening.

## 7. Recommendations (Priority Order)

1. High, strict necessary: repair
   [docs/akkapros/phonetizer-algorithm.md](../../akkapros/phonetizer-algorithm.md)
   so its governing-record section points only to the active merged contract in
   [CR-063](../cr/063-tune-the-phonetizer-solver.md). Minimal next step:
   replace the deleted `CR-064`/`CR-065` references with merged `CR-063`
   wording.
2. High, strict necessary: correct the pause-row examples in
   [docs/akkapros/phonetizer-phone-file-guide.md](../../akkapros/phonetizer-phone-file-guide.md)
   to match the live pause-row emitter in
   [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py).
   Minimal next step: update the sample rows so pause examples use the runtime
   `boundary` and `accent` values.
3. High, strict necessary: revise
   [docs/akkapros/phonetizer.md](../../akkapros/phonetizer.md)
   so pause behavior matches `_pause_duration_and_drift()` in
   [src/akkapros/lib/phonetize.py](../../../src/akkapros/lib/phonetize.py).
   Minimal next step: remove the claim that long pauses must always reset drift
   to zero and describe the actual in-band preferred-multiple behavior.
4. Medium, nice to have: add one short note to
   [docs/akkapros/phonetizer.md](../../akkapros/phonetizer.md)
   stating that internal merged-unit closures may expose raw unfolded drift on
   `L`, `X`, `E`, or `I` rows until the unit-closing `F` row is realized.
5. Medium, nice to have: add one or two CLI-level integration assertions in
   [tests/test_integration.py](../../../tests/test_integration.py)
   for the most specific CR-063 behaviors now covered only in unit tests,
   especially deferred folding across a merged unit and capped long-vowel
   recovery with residual drift.
6. Low, nice to have: rename the stale optional-fold-era unit-test labels in
   [tests/test_phonetize_lib.py](../../../tests/test_phonetize_lib.py)
   so the test names no longer imply a removed user policy surface.

## 8. Summary Verdict

The CR-063 phonetizer solver implementation is functionally sound and strongly
unit-tested; it is ready to stand as the active runtime baseline once the three
public-document contract mismatches identified in this review are corrected.