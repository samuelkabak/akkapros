## [Unreleased]

### Added
- Project repository initialized
- MIT License added
- README.md with project overview and quick start
- pyproject.toml for project configuration
- CONTRIBUTING.md with development guidelines
- requirements.txt (empty, no runtime dependencies)
- requirements-dev.txt with development tools (pytest, black, ruff, mypy, build, twine)
- .gitignore for Python projects
- Basic directory structure: src/ and tests/
- Placeholder __init__.py files
- **fullreparer.py**: New combined CLI pipeline (syllabify → repair → metrics) with deduplicated shared options and unified outputs
- **printer.py / print.py**: Added IPA output path (`<prefix>_accent_ipa.txt`) with punctuation/pause tagging and bracket escape tags
- **repairer.py**: Added `-r/--relax-last` to enable non-tail propagation for explicit `+` links
- **repair.py tests**: Added strict-default and relaxed-mode regression cases for explicit `+` groups

### Changed
- Reorganized codebase into proper Python package structure (`src/akkapros/`)
- Moved CLI scripts to `akkapros/cli/` subpackage
- Separated library code into `akkapros/lib/` for future API development
- Added sample data file `erra-and-ishum-SB.atf` to `data/samples/`
- Standardized `HYPHEN` as an explicit variable in active library modules (`syllabify.py`, `repair.py`, `metrics.py`, `atfparse.py`, `print.py`) to reduce hardcoded separator usage
- **repair.py explicit `+` behavior**: `RepairEngine` default is now strict tail-only (`only_last=True`)
- **repairer.py CLI behavior**: strict tail-only linked repair is now the default; use `--relax-last` to allow propagation
- **print.py IPA behavior**: punctuation clusters emit one `(..)` pause, spaces emit `⟨pause⟩ (.)`, and bracketed chunks emit `⟨escape:[...]⟩`
- **phonetic constants scope**: extra-long vowels (`àìùè`) are now metrics-internal only

### Stable
- **atfparser.py**: Production-ready eBL ATF parser with comprehensive test suite
- **syllabify.py**: Fully functional syllabifier with 60+ passing unit tests
- **repair.py**: Complete moraic repair system with LOB/SOB accent models, all tests passing
- **metricser.py**: Comprehensive metrics calculator with acoustic analysis and pause metrics, all tests passing
- **printer.py / print.py**: Accent/IPA rendering path and tests are stable

### Removed
- **src/akkapros/cli/format.py** (obsolete CLI formatter)

### Fixed
- None (pre-release development)

### Notes
- Core algorithms (parser, syllabifier, repair, metrics) are stable and unit tested
- Package structure ready for implementation
- CLI tools will be installed as console scripts via pyproject.toml
- `format.py` still in active development