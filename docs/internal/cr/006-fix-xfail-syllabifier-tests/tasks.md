# Tasks for CR-006: Fix xfail in syllabifier tests

## Implementation

- [x] Reproduce the failing `akkapros.cli.syllabifier --test` self-test locally and capture stdout/stderr.
- [x] Add focused regression unit tests in `tests/` reproducing the failing cases (diphthong separator, CR-003 tokens, `{{ }}` spacing).
- [x] Complete the incomplete CR-003 escape-delimiter implementation in syllabifier tokenization.
- [x] Implement minimal fix in `src/akkapros/lib/syllabify.py` (tokenization / diphthong expansion / `{{ }}` handling).
- [x] Remove the runtime `pytest.xfail(...)` that soft-skips the syllabifier self-test.

## Tests

- [x] Run `python -m akkrapros.cli.syllabifier --test` and confirm exit code 0.
- [x] Run `python -m akkrapros.cli.fullprosmaker --test-all` and confirm success.
- [x] Run the full pytest suite and verify no regressions.

## Documentation

- [x] Update `docs/akkapros/diphthong-processing.md` and add notes on `{{ }}` reserved-delimiter spacing if behaviour changes.

## Review & Rollout

- [x] Create a pull request summarizing the fix and request review.
- [x] After merge, ensure CI runs and passes without the xfail.
