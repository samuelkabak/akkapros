# Release Strategy for akkapros

## Document Purpose
This document defines the versioning and release process for `akkapros`.
It incorporates ADR-002, which requires centralized version management.

## Versioning Strategy
We follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`) as defined at
[semver.org](https://semver.org/).

| Version Bump | When to Use | Examples |
|--------------|-------------|----------|
| **MAJOR** (`1.x.x` → `2.0.0`) | Incompatible changes to public API, CLI interface, output formats, or core algorithm behavior that breaks existing workflows | Renaming or removing CLI flags without backward compatibility; changing the format of `*_tilde.txt`; fundamental changes to the prosody realization algorithm that alter results |
| **MINOR** (`1.0.x` → `1.1.0`) | Backward-compatible new features | Adding optional CLI flags; introducing new output formats; adding optional modules or features; expanding documentation with new guides |
| **PATCH** (`1.0.0` → `1.0.1`) | Bug fixes and documentation updates that do not change public behavior | Fixing encoding issues; correcting CLI help text; minor internal bug fixes; updating citation metadata |

## Version Source of Truth

The package version is defined only in `src/akkapros/__init__.py` as
`__version__`.

- `pyproject.toml` must derive the package version dynamically from
  `akkapros.__version__`.
- CLI `--version` output must consume the shared helpers from the package.
- Library modules must not define independent `__version__` values.

## Public Contract

The following are considered part of the public interface and must be versioned
accordingly:

- CLI flag names and their behavior
- Output file naming conventions and formats (`*_syl.txt`, `*_tilde.txt`, `*_metrics.json`, etc.)
- The structure of generated output files
- Core algorithm behavior as documented in the prosody realization specification
- The meaning and interpretation of metrics (`%V`, `ΔC`, `VarcoC`)

## Release Workflow

### Preparation Phase

1. Freeze changes and decide what belongs in the release.
2. Update `src/akkapros/__init__.py` to the target version.
3. Update release metadata files that intentionally publish the release number:
   `CITATION.cff`, `README.md`, `CHANGELOG.md`, and `release-notes/vX.Y.Z.md`.
4. Keep `pyproject.toml` on dynamic versioning; do not hardcode a second version
   number there.
5. Reset `release-notes/unreleased.md` so future notes start from the new tag.

### Validation Phase

Run the release checks before tagging:

```bash
python scripts/sync_docs.py
python scripts/build_package.py --sdist --wheel
pytest -q
```

If you want the built-in CLI self-tests as an additional safety check, run:

```bash
python -m akkapros.cli.fullprosmaker --test-all
python -m akkapros.cli.printer --test
```

### Release Artifacts

For each release, prepare:

- `CHANGELOG.md` with a new released section
- `release-notes/vX.Y.Z.md` with user-facing highlights and upgrade notes
- `release-notes/unreleased.md` reset for the next cycle
- Updated citation metadata in `CITATION.cff`

### Post-Release

After tagging `vX.Y.Z`, the default base for `scripts/update_unreleased.py`
should be the newly released tag.