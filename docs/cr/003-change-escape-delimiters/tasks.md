# Tasks for CR-003: Change escape delimiters to ⟦ / ⟧

## Implementation

- [ ] Update `OPEN_ESCAPE` and `CLOSE_ESCAPE` in `src/akkapros/lib/constants.py` to `⟦` and `⟧`.
- [ ] Refactor `src/akkapros/lib/syllabify.py` and `src/akkapros/lib/prosody.py` to reference the constants instead of hardcoded characters; ensure parsing logic uses the constants everywhere.
- [ ] Search the repository for literal `‹` and `›` and update occurrences in code/tests/docs to either reference the constants or the new delimiters where appropriate.
- [ ] Enlarge the code analysis beyond syllabify/prosody: inspect other modules and CLI tools to ensure no other component hardcodes the old delimiters or assumes those characters.

## Tests

- [ ] Locate and update tests that reference `‹`/`›`. The test plan and locations are described in `docs/adr/014-cli-built-in-self-tests.md`. Use that document to find and adapt test files.
- [ ] Run the project's canonical test-suite (e.g. `pytest`) and fix regressions arising from the delimiter change.

## Documentation

- [ ] Update documentation pages and examples that mention the old escape markers (search `docs/` and `docs/cr/`).
- [ ] If no documentation currently describes the escape mechanism, add a short explanatory note to the `syllabifier` and `prosmaker` docs describing the escape delimiters and their purpose.
- [ ] Add a brief migration note in release notes or CHANGELOG advising downstream users to replace `‹`→`⟦` and `›`→`⟧` where those characters were used as escape markers.

## Review & Rollout

- [ ] Create a pull request with the changes and request review.
- [ ] Coordinate with any external consumers if they rely on literal `‹`/`›` in their scripts.
- [ ] After merge, run a smoke test on typical input files to ensure no parsing regressions.
