# Tasks for CR-001

## Implementation

- [ ] Add `mora_stats['total']` in `analyze_text()` and verify with unit tests
- [ ] Compute `original['speech']` in `process_filetext()` by calling `compute_speech_rate()` with the original stats
- [ ] Update `format_table()` to add `Total morae number` lines, move/rename the speech blocks, and format ΔC/MeanC with seconds
- [ ] Update `format_csv()` to include the new CSV rows
- [ ] Update JSON pruning in `metricalc.py` to preserve new fields

## Tests

- [ ] Unit test for `analyze_text()` total morae
- [ ] Unit test for `process_filetext()` to assert `original['speech']` presence and numeric fields
- [ ] Test for `format_table()` output ordering and presence of new lines
- [ ] CSV output test for new rows

## Documentation

- [ ] Update `docs/` README and CLI examples to mention new fields
- [ ] Add notes to release-notes/unreleased.md

- [ ] Update `docs/akkapros/metrics-computation.md` with definitions and examples for `total_morae` and ΔC/MeanC seconds
- [ ] Update `docs/akkapros/metricalc.md` to document new output fields and table layout changes

## Review

- [ ] Code review
- [ ] Verify acceptance criteria and tests

