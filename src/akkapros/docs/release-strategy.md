# First Release Strategy (v1.0.0)

## Scope
This document defines a practical versioning and release process for the first public GitHub release of `akkapros`.

## Versioning Strategy
Use Semantic Versioning (`MAJOR.MINOR.PATCH`).

- `MAJOR` (`1.x.x` -> `2.0.0`): incompatible CLI/API/output contract changes.
- `MINOR` (`1.0.x` -> `1.1.0`): backwards-compatible features (new flags, new output format, new optional modules).
- `PATCH` (`1.0.0` -> `1.0.1`): bug fixes and documentation/test updates that do not break workflows.

### Practical Rule For This Project
- Treat CLI flag names and output file naming as part of the public contract.
- If a CLI flag is renamed or removed without compatibility alias, bump `MAJOR`.
- If a new optional flag is added with unchanged defaults, bump `MINOR`.
- If behavior is fixed behind existing flags, bump `PATCH`.

## Release Strategy
Use a lightweight release train with signed tags and GitHub Releases.

1. Freeze release branch (or `main`) for docs/tests only.
2. Ensure `pyproject.toml` version equals the intended tag.
3. Finalize `CHANGELOG.md` for that version.
4. Run sanity checks and test commands.
5. Create annotated tag `v1.0.0`.
6. Publish GitHub Release notes from changelog.
7. After release, open `Unreleased` section for next cycle.

Release-specific operational details should be documented in the release notes, not in this strategy file.
