# Tasks for CR-004: Rename repair → accentuation

## Implementation

- [ ] Run a targeted refactor to rename `repaired` → `accentuated`, `repair` → `accentuation`, and `repairs` → `accentuations` across the codebase where the terms refer to prosodic modification.
- [ ] Update formatter code to change printed labels and JSON/CSV keys (human table, `metricalc.py` outputs).
- [ ] Update variable names and function names in `src/akkapros/lib/` and `src/akkapros/cli/` where applicable.

## Tests

- [ ] Locate tests (see `docs/internal/adr/014-cli-built-in-self-tests.md`) and update fixtures and assertions to the new terminology.
- [ ] Run the full test-suite and fix regressions.

## Documentation

- [ ] Update documentation examples, CR/ADR pages, README and any docs that mention the old terms.
- [ ] Add a clear changelog entry explaining the breaking rename and recommended migration steps for downstream users.

## Review & Rollout

- [ ] Create a pull request summarizing the rename and request a review.
- [ ] After merge, run smoke tests on common inputs and CI.

