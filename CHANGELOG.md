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
- **printer.py / print.py**: New accent rendering pipeline from `*_tilde.txt` to `<prefix>_accent_accute.txt` and `<prefix>_accent_bold.md`

### Changed
- Reorganized codebase into proper Python package structure (`src/akkapros/`)
- Moved CLI scripts to `akkapros/cli/` subpackage
- Separated library code into `akkapros/lib/` for future API development
- Added sample data file `erra-and-ishum-SB.atf` to `data/samples/`
- Standardized `HYPHEN` as an explicit variable in active library modules (`syllabify.py`, `repair.py`, `metrics.py`, `atfparse.py`, `print.py`) to reduce hardcoded separator usage

### Stable
- **atfparser.py**: Production-ready eBL ATF parser with comprehensive test suite
- **syllabify.py**: Fully functional syllabifier with 60+ passing unit tests
- **repair.py**: Complete moraic repair system with LOB/SOB accent models, all tests passing
- **metricser.py**: Comprehensive metrics calculator with acoustic analysis and pause metrics, all tests passing
- **format.py**: Currently under development (IPA, Markdown, LaTeX output)

### Fixed
- None (pre-release development)

### Notes
- Core algorithms (parser, syllabifier, repair, metrics) are stable and unit tested
- Package structure ready for implementation
- CLI tools will be installed as console scripts via pyproject.toml
- `format.py` still in active development