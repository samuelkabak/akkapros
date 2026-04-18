---
review_id: review-012
status: Done
created: 2026-04-18
updated: 2026-04-18
reviewer: GitHub Copilot (GPT-5.4)
scope: >-
  src/akkapros/lib/phonetize.py,
  src/akkapros/lib/metrics.py,
  docs/akkapros/phonetizer.md,
  docs/akkapros/phonetizer-phone-file-guide.md,
  docs/akkapros/phonetizer-algorithm.md,
  docs/akkapros/metrics-computation.md,
  tests/test_phonetize_lib.py,
  tests/test_metrics_stats.py,
  and demo/akkapros/lexlinks/results/erra_construct_phone.txt.
---

# Code and Project Review — Phonetizer Drift Column and Drift Statistics Semantics

## 1. Executive Summary

The current implementation does not print drift evolution segment by segment in
column 10 of `_phone.txt` / `_ophone.txt`. The live runtime writes a
completed-unit drift token: non-final segment rows repeat the most recently
completed unit's drift, and the token is updated only when a pause row is
completed or when a syllable reaches its final row. The front matter drift
statistics are derived from the same completed-unit history, not from every row
token and not from a hypothetical segment-by-segment accumulation. The public
docs are mostly consistent with this behavior already, but the terminology can
still mislead readers into inferring a segmental drift trace that the runtime
does not actually model.

## 2. Architecture Assessment

### 2.1 Strengths

- The live solver keeps one explicit running `drift_cursor` in
  `src/akkapros/lib/phonetize.py` and updates it in one place during Phase 2,
  which makes the semantics auditable.
- Public docs already state the essential contract in several places: the drift
  column is described as a post-unit token written after the most recently
  completed syllable or pause, and non-final rows are documented as repeats.
- `metrics.py` does not recompute drift from row data. It consumes the phonetize
  summary from front matter, which avoids downstream reinterpretation drift.

### 2.2 Areas for Improvement

- The column appears on every row, so readers can easily mistake it for a
  per-segment trace even though the runtime does not update it segment by
  segment.
- The term `drift` alone is slightly under-specified for user-facing reading.
  If the project wants to contrast this with a true per-segment trace, the
  current value should be named more explicitly in docs as completed-unit drift
  or prosodic drift.
- No focused test appears to state in one sentence that drift summary metrics
  are sampled once per completed syllable or pause. The behavior is present in
  code and implied in docs, but the specific interpretation is not pinned by a
  narrow explanatory test name.

## 3. Code Quality Assessment

- In `realize_phone_rows()`, `drift_history` is appended exactly once after a
  pause row is realized and exactly once after a syllable unit is realized.
  This means the summary statistics are unit-level samples.
- Before each syllable is finalized, every row in that syllable is assigned the
  `last_completed_drift_token`, so onset and internal rows show stale/repeated
  drift until the unit closes.
- Only the last row of the realized syllable gets the newly computed token.
  That matches the observed behavior where the drift column is piecewise
  constant across a syllable rather than cumulative row by row.
- The returned report computes `max`, `mean`, and `stddev` directly from
  `drift_history`, so the statistics reflect completed-unit drift samples, not
  every displayed row token and not every emitted segment duration.
- This is not a bug in implementation consistency. It is a semantic choice in
  the data model.

## 4. Documentation Assessment

- `docs/akkapros/phonetizer-phone-file-guide.md` is materially correct here. It
  says the field is a four-character post-unit drift token and that non-final
  rows repeat the most recent completed-unit value.
- `docs/akkapros/phonetizer.md` is also materially correct. It says row-level
  drift changes only on syllable-final rows and pause rows.
- `docs/akkapros/phonetizer-algorithm.md` likewise states that the drift field
  is the post-unit drift token written after the most recently completed
  syllable or pause.
- `docs/akkapros/metrics-computation.md` correctly states that metricalc reads
  drift summary values from front matter rather than deriving them from phone
  rows.
- What is still missing is one explicit sentence tying these together: the
  reported drift statistics are statistics over the completed-unit drift history
  maintained by the phonetizer, not over a segment-by-segment drift trace.

## 5. Research / Functional Assessment

Functionally, the current runtime supports prosodic-unit drift, not segmental
drift.

- A consonant or vowel row receives a realized duration, but drift is evaluated
  against syllable or pause targets after the relevant unit is assembled.
- There is no segment-level reference model in the current solver equivalent to
  saying `len(CV) = 0.5 * len(CVC)` for each individual emitted row in the way
  your example assumes.
- Under the active design, consonants and vowels contribute to a unit's
  realized total, and only then does the solver compare the realized unit to
  `shape_ref` or the pause target and update `drift_cursor`.
- Because of that design, a segment-by-segment cumulative drift printout would
  be a different metric than the one currently implemented.

Concrete verification from the repository:

- In `src/akkapros/lib/phonetize.py`, pause handling appends to `drift_history`
  after the pause is realized.
- In the same function, syllable handling appends to `drift_history` after the
  syllable total is realized and any fold-to-branch logic is applied.
- The lexlinks artifact
  `demo/akkapros/lexlinks/results/erra_construct_phone.txt` reports front matter
  drift values `max: 251.0`, `mean: 15.8072`, `stddev: 58.8582`, which are the
  phonetizer's own summary outputs for that stream.

## 6. Process and Engineering Practices

- The runtime, tests, and public docs are aligned on the core fact that row
  drift is post-unit rather than per-segment.
- The main engineering gap is terminology precision, not implementation drift.
- Because metricalc consumes phonetizer front matter directly, any later
  semantic rename or clarification must keep that cross-stage contract explicit.

## 7. Recommendations (Priority Order)

1. High: Add one explicit user-facing documentation sentence stating that drift
   `max`, `mean`, and `stddev` are computed over completed syllable/pause drift
   samples, not over every segment row. Minimal next step: update
   `docs/akkapros/phonetizer-phone-file-guide.md` and `docs/akkapros/metrics-computation.md`.
2. High: If the preferred interpretation is `prosodic drift`, standardize that
   terminology in docs and examples so readers do not infer a segmental trace.
   Minimal next step: add a short glossary note or parenthetical label such as
   `post-unit (prosodic) drift`.
3. Medium: Add a focused test name that explicitly states the summary is sampled
   from completed units only. Minimal next step: add one narrow regression test
   around `realize_phone_rows()` and the returned report.
4. Medium: If future research needs true segmental drift, define it as a new
   metric rather than reinterpreting the existing drift column. Minimal next
   step: write a CR or review defining per-segment reference durations and the
   intended relation to the current post-unit drift trace.

## 8. Summary Verdict

The current system is internally consistent: the printed drift column and drift
statistics represent completed-unit prosodic drift, not segment-by-segment
drift, and the remaining need is documentation/naming precision rather than a
runtime bug fix.
