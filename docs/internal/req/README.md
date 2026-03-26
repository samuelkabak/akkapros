# Requirements

This folder holds system-level requirement documents for features or behaviors that need formal description before implementation.

See the `index.md` for an auto-generated list of requirement documents. The
index is ordered latest-first (highest numeric `NNN` at the top).

How to add a new requirement

1. Copy the `000-req-template.md` in this folder.
2. Create `NNN-short-kebab-title.md` (use 3-digit prefix for ordering). When
	adding a new requirement, choose the next sequential `NNN`; the index will
	list requirements with the newest (greatest `NNN`) first.
3. Fill `REQ-ID`, `Summary`, `Acceptance Criteria`, and `Interface Notes`.
4. Open a Change Request (CR) if implementation work is required and link the requirement.

Naming and conventions

- Use `NNN-short-kebab-title.md` for filenames (e.g., `001-password-reset.md`).
- Use the `REQ-` identifier inside the file for cross-references.

## Impact field

Each requirement file should include an `Impact:` header field (one of
`Additive` or `Mutative`) immediately after `Priority:` in the file header.
- `Additive` means the requirement only adds new behaviour or features and does
	not change existing behaviour, APIs or output formats.
- `Mutative` means the requirement may change existing behaviour, replace
	outputs, or otherwise be breaking for downstream consumers.

When creating or reviewing requirements, choose `Additive` when the change is
purely additive; otherwise prefer `Mutative`. If the document does not provide
enough information to make a determination, default to `Mutative`.

***
