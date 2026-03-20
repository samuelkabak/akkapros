# Change Request: Use rare bracket delimiters for escape markers (⟦ ⟧)

CR-ID: CR-003
Status: Done
Priority: Medium
Created: 2026-03-17
Updated: 2026-03-17

---

# Summary

Replace the current escape delimiters `OPEN_ESCAPE = '‹'` and `CLOSE_ESCAPE = '›'` with the rare bracket pair `⟦` (OPEN) and `⟧` (CLOSE) across the codebase (syllabification, prosody, tests and documentation). This avoids accidental parsing errors when texts contain the existing `‹`/`›` characters.

---

# Motivation

The characters `‹`/`›` can legitimately appear in input text (editor annotations, copy/paste from external sources), which risks introducing parsing errors or incorrect escape handling. The bracket pair `⟦`/`⟧` is extremely rare in source texts and is a safer choice for explicit escape markers.

---

# Scope

Included:
- Change delimiter constants in `src/akkapros/lib/constants.py` from `‹`/`›` to `⟦`/`⟧`.
- Update `src/akkapros/lib/syllabify.py` and `src/akkapros/lib/prosody.py` to use the constants (not hardcoded chars) and update any parsing logic that assumes the old characters.
- Update unit tests that hardcode `‹`/`›` to use the new delimiters or reference the constants.
- Update documentation that mentions the escape markers (docs/ and CR/ADR pages) to reference `⟦`/`⟧`.

Not included:
- Any downstream external consumers that hardcode the old delimiters (these will need separate coordination).

---

# Current Behavior

- `src/akkapros/lib/constants.py` defines `OPEN_ESCAPE = '‹'` and `CLOSE_ESCAPE = '›'`.
- Syllabifier and prosody code and tests use these characters; several tests hardcode them.
- Documentation refers to the current escape characters in examples.

---

# Proposed Change

1. Update `OPEN_ESCAPE`/`CLOSE_ESCAPE` in `src/akkapros/lib/constants.py` to `⟦` and `⟧` respectively.
2. Audit `src/akkapros/lib/syllabify.py` and `src/akkapros/lib/prosody.py` to ensure they import and use the constants rather than literal characters; where literal occurences exist, refactor to reference `OPEN_ESCAPE`/`CLOSE_ESCAPE`.
3. Update all tests that assert or construct strings with the old delimiters to use the constants (import from `akkapros.lib.constants`) or the new literal `⟦`/`⟧`.
	- Note: the test plan and locations are documented in `docs/internal/adr/014-cli-built-in-self-tests.md`; use that document to locate and update the relevant tests.
4. Update documentation files that mention the escape markers to show `⟦` and `⟧` in examples.
5. Run the project's test-suite (per `docs/internal/adr/014-cli-built-in-self-tests.md`) and fix any failures caused by hardcoded characters. ensure you run the canonical `pytest` invocation used by the project.

The change should be implemented as a minimal, mechanical refactor: constant update + replace hardcoded usages with constant references or the new literals in tests/docs.

---

# Files Likely Affected

- `src/akkapros/lib/constants.py`
- `src/akkapros/lib/syllabify.py`
- `src/akkapros/lib/prosody.py`
- Tests that reference the escape markers (search for `‹` or `›`).
- Documentation files under `docs/` and `docs/internal/cr/` which mention the delimiters.

---

# Acceptance Criteria

- `OPEN_ESCAPE` and `CLOSE_ESCAPE` are set to `⟦` and `⟧` in `src/akkapros/lib/constants.py`.
- `syllabify.py` and `prosody.py` reference the constants (no logic depends on literal `‹`/`›`).
- All tests that previously used `‹`/`›` are updated and pass for the two modules.
- Documentation examples reflect the new delimiters.

---

# Risks & Edge Cases

- Some external scripts or saved data might contain the old delimiters; note this in release notes and provide a short migration note (search-and-replace `‹`→`⟦`, `›`→`⟧` where intended as escapes).
- Terminal or font rendering may vary; ensure documentation uses proper Unicode escapes or an explanatory note in case a user cannot easily type these characters.

---


# Testing Strategy

- Search the repo for literal `‹` or `›` occurrences and update tests accordingly.
- Locate tests using the guidance in `docs/internal/adr/014-cli-built-in-self-tests.md`.
- Run the canonical test-suite (e.g. `pytest`) and fix any regressions caused by the delimiter change.

---

# Rollback

Revert the single commit changing the constants and updated files if unexpected breakage occurs; changes are local and mechanical.

---

# Notes

No further questions — the request is clear. I will prepare the implementation patch after you approve this CR.

---

# Tasks

## Implementation

- [ ] Update `OPEN_ESCAPE` and `CLOSE_ESCAPE` in `src/akkapros/lib/constants.py` to `⟦` and `⟧`.
- [ ] Refactor `src/akkapros/lib/syllabify.py` and `src/akkapros/lib/prosody.py` to reference the constants instead of hardcoded characters; ensure parsing logic uses the constants everywhere.
- [ ] Search the repository for literal `‹` and `›` and update occurrences in code/tests/docs to either reference the constants or the new delimiters where appropriate.
- [ ] Enlarge the code analysis beyond syllabify/prosody: inspect other modules and CLI tools to ensure no other component hardcodes the old delimiters or assumes those characters.

## Tests

- [ ] Locate and update tests that reference `‹`/`›`. The test plan and locations are described in `docs/internal/adr/014-cli-built-in-self-tests.md`. Use that document to find and adapt test files.
- [ ] Run the project's canonical test-suite (e.g. `pytest`) and fix regressions arising from the delimiter change.

## Documentation

- [ ] Update documentation pages and examples that mention the old escape markers (search `docs/` and `docs/internal/cr/`).
- [ ] If no documentation currently describes the escape mechanism, add a short explanatory note to the `syllabifier` and `prosmaker` docs describing the escape delimiters and their purpose.
- [ ] Add a brief migration note in release notes or CHANGELOG advising downstream users to replace `‹`→`⟦` and `›`→`⟧` where those characters were used as escape markers.

## Review & Rollout

- [ ] Create a pull request with the changes and request review.
- [ ] Coordinate with any external consumers if they rely on literal `‹`/`›` in their scripts.
- [ ] After merge, run a smoke test on typical input files to ensure no parsing regressions.
