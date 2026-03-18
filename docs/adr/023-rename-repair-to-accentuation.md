---
Status: Accepted
Date: 2026-03-18
---

# 023 — Rename "repair" terminology to "accentuation" and accept the compatibility break

## Plain Summary

Decide to rename the project's public and internal terminology from "repair/repaired/repairs" to "accentuation/accentuated/accentuations" and accept the resulting backward-compatibility break for outputs and identifiers. This is a deliberate, project-level wording decision to better reflect the functional intent of the processing (prosodic accentuation rather than text repair).

## Context and Problem Statement

The codebase, outputs, and documentation currently use the terms "repair", "repaired" and "repairs" to refer to the prosodic modifications the pipeline applies (for example, `repaired['speech']`, `rep_total_morae`, and table headings like "Acoustic metrics (repaired)"). The word "repair" implies correcting broken text, which mischaracterizes the operation: the pipeline applies prosodic accentuation (lengthening, gemination) to realize rhythm, not to correct errors.

This ADR decides whether the project should adopt `accentuation` terminology throughout the codebase and outputs, accepting that the change will be visible to external consumers (file formats, JSON/CSV keys, and printed labels) and therefore constitutes a breaking change.

## Decision Drivers

- Use terminology that accurately reflects the function (prosodic accentuation) and avoids implying an editorial correction.
- Improve clarity for users, readers of outputs, and downstream tooling consuming labels or JSON/CSV keys.
- Maintain code clarity by choosing terms that match domain concepts rather than metaphorical labels.
- Minimize long-term support burden caused by misleading terminology.
- Balance compatibility costs against user-facing clarity and correctness of language.

## Considered Options

- Option A — Keep the current "repair/repairs/repaired" terminology to preserve backward compatibility.
- Option B — Rename to "accentuation/accentuated/accentuations" across code, outputs, and docs, accepting a breaking change.
- Option C — Introduce aliasing/shims to preserve compatibility while gradually migrating to the new terms (adds complexity and prolongs ambiguity).

## Decision Outcome

Chosen option: Option B — Rename the terminology to `accentuation` forms and accept the breaking change.

Rationale: The current term misleads readers and downstream consumers about the nature of the transformation. Consistently using `accentuation` better documents intent, reduces misunderstanding, and aligns naming with linguistic reality. The cost of a one-time migration is outweighed by the long-term clarity and reduced support burden.

## Pros and Cons

### Pros

- Terminology aligns with the actual linguistic operation performed by the pipeline.
- Reduces user confusion and clarifies outputs for downstream consumers.
- Improves maintainability by making variable/function names descriptive of domain behavior.

### Cons

- Breaks backward compatibility for existing consumers that rely on legacy JSON/CSV keys, exported labels, or identifier names.
- Requires code changes, test updates, and documentation revisions.

## Implications and Consequences

- Backwards compatibility: This ADR accepts a breaking, mechanical rename. Consumers must update parsing logic, keys, and scripts as necessary.
- Code changes: Rename variables, functions, and keys where they convey the prosodic modification concept (e.g., `repaired` → `accentuated`, `rep_total_morae` → `accentuated_total_morae`).
- Tests: Update fixtures, assertions, and test names to reflect the new terminology and run the full test-suite.
- Documentation: Update user-facing docs, CLI help, examples, and changelog to explain the new terms and migration steps.
- Rollout: Create a change request (CR-004) that implements the renames and include migration guidance and a short deprecation window in the release notes.

## Migration Notes

- Recommended simple transforms (examples):

- For file headers and JSON keys: replace `repaired` with `accentuated` and `rep_` prefixes with `accentuated_` where applicable.
- For programmatic consumers: update parsing and expectations for CSV/JSON keys and table headings.

## Links

- Conflicting guidance: ADR-022 (format-preservation policy)
- Implementation task: create CR-004 to implement this ADR and follow up with a PR updating identifiers, outputs, and tests.

## Implementation Notes

- Perform repository-wide, semantic renames for identifiers and output keys: `repaired` → `accentuated`, `repair` → `accentuation`, `repairs` → `accentuations`.
- Update formatter outputs, CSV/JSON keys, printed table headings, and IPA/printer metadata labels.
- Add regression tests to ensure no remaining user-facing "repair" strings remain in outputs.

## Reviewed By

- (TBD) Project maintainers and affected downstream consumers. Add reviewer names and approval dates here.

<!-- Usage: this ADR records the decision to rename "repair" terminology to "accentuation". Implement the change in CR-004 and follow-up PRs. -->
