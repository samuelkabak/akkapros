# Change Request: Rename "repair" terminology to "accentuation"

CR-ID: CR-004
Status: Draft
Priority: Medium
Created: 2026-03-17
Updated: 2026-03-17
Implements: ADR-023
---

# Summary

Replace the terminology and variables that use "repair/repaired/repairs" with "accentuation/accentuated/accentuations" across the codebase and outputs (printed human table, JSON, CSV, logs, docs). The change clarifies intent: the process is not "fixing" broken text but applying a prosodic accentuation.

---

# Motivation

The word "repair" implies correcting an error. Our processing applies prosodic modifications (lengthening/gemination) to implement accentuation, not to repair damaged text. Renaming improves clarity for users and downstream consumers.

---

# Scope

Included:
- Rename terminology in code identifiers, variable names, function names and comments where they express the concept of prosodic modification (e.g., `repaired` → `accentuated`).
- Update printed outputs (human table labels, JSON keys, CSV headers) to use the new terms.
- Update documentation and examples to use the new terminology.

Not included:
- Backward compatibility shims or aliases — this is a breaking, mechanical rename (the project agreed no compatibility is required).
- Changes to the underlying prosody algorithm or data formats beyond renaming keys/labels.

---

# Current Behavior

Many modules, tests and documentation use the words "repair", "repaired", and "repairs" to describe prosodic modifications and resulting outputs (e.g., `repaired['speech']`, `rep_total_morae`, `Acoustic metrics (repaired)`). These appear in variable names, formatter outputs, JSON/CSV keys, test assertions and docs.

---

# Proposed Change

1. Perform a repository-wide, semantic rename from the following templates:

- `repaired` → `accentuated`
- `repair` → `accentuation`
- `repairs` → `accentuations`

2. Prefer using the canonical forms in code: e.g., `result['accentuated']` instead of `result['repaired']`; CSV/JSON header `accentuated_total_morae` instead of `rep_total_morae`; table heading `Acoustic metrics (accentuated)`.

3. Ensure renames are applied consistently to:
- variable and function names
- formatter labels and printed table headings
- JSON and CSV keys
- test fixtures and assertions
- documentation and CR/ADR pages

4. Run the project's test-suite and fix any failures introduced by renaming.

Implementation note: this is a mechanical refactor. Use search-and-replace guided by code context and run tests frequently to catch missed occurrences.

---

# Files Likely Affected (directional)

- `src/akkapros/lib/*` (metrics, prosody, syllabify, formatters)
- `src/akkapros/cli/*` (metricalc and other CLIs that print the table/CSV/JSON)
- Test files and fixtures (refer to `docs/internal/adr/014-cli-built-in-self-tests.md` for locations)
- Documentation in `docs/` and `docs/internal/cr/`

---

# Acceptance Criteria

- No remaining user-facing outputs contain the words "repair", "repaired" or "repairs"; they use the new terms instead.
- Codebase identifiers that expressed the prosodic modification are renamed to the new terms.
- Tests are updated and pass.
- Documentation updated to use the new terminology.

---

# Risks & Testing

- This is a breaking change for scripts that depended on legacy JSON/CSV keys — document the change in the release notes and CHANGELOG.
- Run full test-suite (canonical `pytest`) after renames.
- Manual smoke test: run `metricalc` on a small input and verify table/JSON/CSV labels update.

---

# Rollback

Revert the commit(s) performing the renames if unexpected issues arise.

---

# Notes

- Use the guidance in `docs/internal/cr/README.md` for CR workflow and `docs/internal/adr/` for architectural context.

