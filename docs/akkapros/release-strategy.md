# Release Strategy for akkapros

## Document Purpose
This document defines the versioning and release process for `akkapros`. It is informed by the actual experience of releasing v1.0.0 and the subsequent v1.0.1 patch release for documentation fixes.

## Versioning Strategy
We follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`) as defined at [semver.org](https://semver.org/).

| Version Bump | When to Use | Examples |
|--------------|-------------|----------|
| **MAJOR** (`1.x.x` → `2.0.0`) | Incompatible changes to public API, CLI interface, output formats, or core algorithm behavior that breaks existing workflows | • Renaming or removing CLI flags without backward compatibility<br>• Changing the format of `*_tilde.txt` or other output files<br>• Fundamental changes to the prosody realization algorithm that alter results |
| **MINOR** (`1.0.x` → `1.1.0`) | Backward-compatible new features | • Adding new CLI flags that are optional<br>• Introducing new output formats<br>• New optional modules or features<br>• Expanding documentation with new guides |
| **PATCH** (`1.0.0` → `1.0.1`) | Bug fixes and documentation updates that do not change functionality | • Fixing encoding issues in documentation (as in v1.0.1)<br>• Correcting CLI help text<br>• Minor bug fixes that do not alter expected behavior<br>• Updating `CITATION.cff` or metadata |

### What Constitutes the Public Contract
The following are considered part of the public interface and must be versioned accordingly:

- CLI flag names and their behavior
- Output file naming conventions and formats (`*_syl.txt`, `*_tilde.txt`, `*_metrics.json`, etc.)
- The structure of generated output files
- Core algorithm behavior as documented in the prosody realization specification
- The meaning and interpretation of metrics (%V, ΔC, VarcoC)

## Release Workflow

### Preparation Phase
1. **Freeze changes**: Decide what belongs in the release. For PATCH releases, only bug fixes and documentation updates are permitted.
2. **Update version**: Ensure `pyproject.toml` and `CITATION.cff` reflect the new version number.
3. **Update `CHANGELOG.md`**: Move all items from the "Unreleased" section to a new section for the upcoming version.
4. **Run full test suite**:
   ```bash
   python3 src/akkapros/cli/fullprosmaker.py --test-all
   python3 src/akkapros/cli/printer.py --test
   pytest -q