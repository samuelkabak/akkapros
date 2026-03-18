# Changelog

All notable changes to the akkapros project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.1] - 2026-03-14

### Fixed
- UTF-8 encoding issues in documentation files
- Markdown formatting in multiple docs (arrows, code blocks)
- Broken text boxes in documentation files

### Added
- CITATION.cff with DOI and ORCID
- SUPPORT.md with user guidance
- CONTRIBUTING.md with development guidelines
- Issue templates for bug reports and feature requests
- SHOWCASE.md for research promotion
- .gitattributes for consistent line endings
 - Packaging helpers: `scripts/sync_docs.py` and `scripts/build_package.py`
 - Architectural Decision Records: `docs/adr/` (MADR bootstrap, 15 ADRs)
 - Centralized package metadata: `src/akkapros/__init__.py` with `__version__` and standardized `--version` output for CLIs
 - Synced documentation into package path `src/akkapros/docs/` for inclusion in sdist/wheel

### Changed
- Updated README.md with professional badges and structure
- Standardized all documentation to 4-space indentation for commands
- Replaced triple backticks with indented code blocks in all docs
 - Removed POSIX/PowerShell sync scripts in favor of a single Python sync tool (`scripts/sync_docs.py`)
 - Reverted an attempted PEP 517 build-backend wrapper; build flow uses `scripts/build_package.py` pre-build wrapper and `setuptools.build_meta` for isolated builds

### Documentation
- Comprehensive review and cleanup of all 15+ documentation files
- Consistent formatting across all CLI docs
- Fixed special character rendering issues
 - Added package-level docs mirror at `src/akkapros/docs/` (kept in sync by `scripts/sync_docs.py`)
 - Added ADRs under `docs/adr/` documenting major architectural decisions and release rationale

### Fixed
- Fixed a small CLI startup banner regression introduced during refactor (restored stable `--version` behavior across CLIs)

## [1.0.0] - 2026-03-13

### Added
- Initial public release of `akkapros`

### Core Components
- **ATF Parser** (`atfparser.py`): Converts eBL ATF files to clean phonological text
- **Syllabifier** (`syllabifier.py`): Adds syllable boundaries following Huehnergard (2011)
- **Prosody Realization Engine** (`prosmaker.py`): Implements LOB and SOB accent styles with moraic prosody realization
- **Metrics Calculator** (`metricalc.py`): Computes %V, ΔC, VarcoC, and related rhythmic metrics
- **Printer** (`printer.py`): Generates multiple output formats (acute, bold, IPA, XAR, MBROLA)
- **Full Pipeline** (`fullprosmaker.py`): End-to-end orchestration of all stages

### Features
- Two accent styles: LOB (Literary Old Babylonian) and SOB (Standard Old Babylonian)
- Diphthong processing pipeline with split/restore logic
- Pause modeling with configurable ratios (30%, 35%, 40%)
- Pause duration correction to align short pauses with bimoraic rhythm
- IPA output with:
  - Post-emphatic vowel coloring
  - Configurable pharyngeal/glottal mapping (`--ipa-proto-semitic`)
  - Speculative circumflex hiatus mode (`--circ-hiatus`)
- XAR practical reading orthography with:
  - Marked emphatic consonants (`ꝗ`, `ꞓ`, `ɉ`)
  - Doubled long vowels
  - Two-vowel circumflex memory forms
  - Grave accent for emphatic coloring
- MBROLA recording script generator (`phoneprep.py`) with 878-word coverage
- Interactive HTML recording helper for speech synthesis preparation

### Documentation
- Comprehensive CLI documentation under `docs/akkapros/`
- Detailed algorithm explanations:
  - `prosody-realization-algorithm.md`
  - `diphthong-processing.md`
  - `metrics-computation.md`
  - `xar-script.md`
- Release strategy and checklist (`release-strategy.md`)
- Getting started guide (`GETTING_STARTED.md`)

### Validation
- Corpus: 4,917 words from Standard Babylonian literary texts
  - Enūma Eliš (tablets II, IV, VI, VII)
  - Erra and Išum (tablet I)
  - Marduk's Address to the Demons
- Key results:
  - Original VarcoC: 69.09 (compatible with stress-timing)
  - Prominence rate: 13.63% (emerges from data, not design)
  - Accentuated VarcoC: 70.67 (remains consistent with stress-timing)
  - 49.9% of words participate in prosodic merging

### Testing
- Built-in test suites for all components (`--test` flags)
- Demo scripts for Windows (PowerShell) and Unix systems
- Self-validating CLI options

---

## [Unreleased]

### Breaking Changes
- CR-004 renamed terminology across code, outputs, and docs:
  - `repaired` -> `accentuated`
  - `repair` -> `accentuation`
  - `repairs` -> `accentuations`
- JSON/CSV consumers must migrate legacy keys, for example:
  - `result['repaired']` -> `result['accentuated']`
  - `rep_total_morae` -> `accentuated_total_morae`
  - `rep_sps_speech` -> `accentuated_sps_speech`
  - `rep_ΔC_seconds` -> `accentuated_ΔC_seconds`
- CR-005 changed escaped non-Akkadian chunk syntax:
  - `[text]` style escapes are replaced by `{{text}}` and `{tag{text}}`
  - Tag regex is `[0-9a-z_]{1,16}` and tags starting with `_` are internal-only
  - Nested escape blocks are intentionally unsupported
  - Migration helper script: `scripts/migrate-escapes.py`

### Planned
- Segmentation tool for MBROLA voice creation
- Additional corpus validation on other genres
- Enhanced visualization tools for metrics
- Web-based demo interface

---

## Versioning Notes

This project follows Semantic Versioning:

- **MAJOR**: Incompatible CLI/API/output contract changes
- **MINOR**: Backwards-compatible new features
- **PATCH**: Bug fixes and documentation updates

For detailed release procedure, see `docs/akkapros/release-strategy.md`.