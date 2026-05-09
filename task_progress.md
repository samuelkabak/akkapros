# CR-101 Implementation Progress

## Implementation Tasks

- [x] Add `ultraheavy_hiatus_enable` field to `_phonetize_config.py`
- [x] Add experimental guard in `verify_phonetize_config()`
- [x] Add `_choose_ultraheavy_transition()` function
- [x] Add `_expand_ultraheavy_rows()` function
- [x] Add `produce_ultraheavy_rows()` function
- [x] Integrate expansion into the phonetizer output pipeline (both CLIs)
- [x] Add front matter propagation
- [x] Add config key to `default.yaml`
- [x] Add help text to `helpmsg.py`

## Tests

- [ ] Unit tests for `_expand_ultraheavy_rows()`
- [ ] Unit tests for `_choose_ultraheavy_transition()`
- [ ] Unit tests for timing and intonation calculation
- [ ] Unit tests for rising intonation (R token) across the three segments
- [ ] Unit tests for constant intonation (H token) across the three segments
- [ ] Integration tests for full pipeline with `ultraheavy_hiatus_enable = true`
- [ ] Test fixtures and configs are self-sufficient and reserved to `tests/`
- [ ] Test configs updated with `ultraheavy_hiatus_enable` parameter

## Documentation

- [ ] Update `docs/akkapros/phonetizer-algorithm.md`
- [ ] Update demo YAML configs in `demo/akkapros/`

## Verification

- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Verify acceptance criteria
- [ ] Mark CR-101 as Done
- [ ] Mark REQ-050 as Implemented
