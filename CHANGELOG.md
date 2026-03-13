## [Unreleased]

### Added
- Project repository initialized
- MIT License added
- README.md with project overview and quick start
- pyproject.toml for project configuration
- CONTRIBUTING.md with development guidelines
- requirements.txt (empty, no runtime dependencies)
- requirements-dev.txt with development tools (pytest, black, flake8, sox)
- .gitignore for Python projects
- Basic directory structure: src/ and tests/
- Placeholder __init__.py files
- **fullreparer.py**: New combined CLI pipeline (syllabify → repair → metrics → print) with deduplicated shared options and unified outputs
- **printer.py / print.py**: Added IPA output path (`<prefix>_accent_ipa.txt`) with punctuation/pause tagging and bracket escape tags
- **printer.py / print.py**: Added speculative circumflex hiatus mode (`--circ-hiatus`) for IPA splitting (e.g., `qû -> qʊ.ʊ`)
- **fullreparer.py**: Added `--print-circ-hiatus` and propagated it through the print stage
- **repairer.py**: Added `-r/--relax-last` to enable non-tail propagation for explicit `+` links
- **repair.py tests**: Added strict-default and relaxed-mode regression cases for explicit `+` groups
- **syllabifier.py / fullreparer.py**: Line handling now preserves original lines by default; use `--merge-lines` to normalize single newlines to spaces (and 2+ to paragraph breaks)
- **syllabify.py tests**: Added preprocessing regression tests for newline normalization, connector split-merge, and Markdown structural boundaries
- **printer.py / fullreparer.py**: Added `--ipa-pharyngeal {preserve,remove}` policy option (default `preserve`) for IPA output
- **phoneprep.py**: Added `--with-html-recording-helper` and `--recording-max-words` for chunked recording guidance and logging helper generation
- **docs/akkapros**: Added CLI docs for `repairer.py`, `metricser.py`, `fullreparer.py`, `atfparser.py`, `syllabifier.py`, and `printer.py`
 - **demo/**: Added `demo/README.md` describing demo scripts and example outputs under `akkapros`.
- **fullreparer.py CLI namespaced options**: stage-prefixed flags now disambiguate pipeline stages:
	- syllabify: `--syl-merge-hyphens`, `--syl-merge-lines`
	- repair: `--repair-style`, `--repair-relax-last`
	- metrics: `--metrics-*`
	- printer: `--print-*`
	- removed diphthong restoration toggles; restoration is now systematic in repair output

### Changed
- Reorganized codebase into proper Python package structure (`src/akkapros/`)
- Moved CLI scripts to `akkapros/cli/` subpackage
- Separated library code into `akkapros/lib/` for future API development
- Added sample data file `erra-and-ishum-SB.atf` to `data/samples/`
- Standardized `HYPHEN` as an explicit variable in active library modules (`syllabify.py`, `repair.py`, `metrics.py`, `atfparse.py`, `print.py`) to reduce hardcoded separator usage
- **repair.py explicit `+` behavior**: `RepairEngine` default is now strict tail-only (`only_last=True`)
- **repairer.py CLI behavior**: strict tail-only linked repair is now the default; use `--relax-last` to allow propagation
- **print.py IPA behavior**: punctuation clusters emit one `(..)` pause, spaces emit `⟨pause⟩ (.)`, and bracketed chunks emit `⟨escape:[...]⟩`
- **acute naming standardization**: renamed `accute` to `acute` across printer/fullreparer CLI flags, printer library API, tests, and output filename suffix (`_accent_acute.txt`)
- **phonetic constants scope**: extra-long vowels (`àìùè`) are now metrics-internal only
- **XAR circumflex mapping readability**: circumflex series now keeps the circumflex on the second member of mixed pairs (`â -> eâ`, `î -> eî`, `û -> iû`, `ê -> aê`; emphatic: `èâ`, `èî`, `ìû`, `àê`) to make second-vowel dominance visually explicit
- **IPA mode test coverage moved to internal tests**: key `--ipa-ob` / `--ipa-strict` checks are now in `print.py run_tests()`, with CLI option-resolution tests in `printer.py --test` and `fullreparer.py --test-cli`
- **IPA CLI interface simplified**: IPA output is now enabled with `--ipa`, and pharyngeal handling is selected via `--ipa-pharyngeal preserve|remove` (Old Akkadian strict mapping vs Old Babylonian merger mapping)
- **syllabify.py line preprocessing**: default mode now normalizes single newlines to spaces and collapses 2+ newlines to a single paragraph newline
- **syllabify.py Markdown-aware normalization**: default line normalization now preserves single-newline boundaries for Markdown structure (headings, lists, blockquotes, horizontal rules, tables, fenced code blocks)
- **Connector split-merge safety**: cross-line `-` / `+` rejoin now applies only when connector is attached to the previous Akkadian letter (prevents spaced punctuation false merges)
- **metrics.py / metricser.py**: `%V` reporting now exposes two values: articulate (`percent_v_articulate`) and pause-inclusive speech (`percent_v_speech`); CSV/table outputs were updated accordingly
- **atfparse.py / atfparser.py**: `||` and `‡` now normalize to `:`, editorial dashes normalize to `:`, and broken-sign `x` sequences collapse to a single ellipsis (`…`)
- **docs/akkapros/metrics-computation.md**: `%V` section updated to document articulate vs normal-speech formulas
- Updated and fixed files in demo/ and all modified Python scripts. See commit for details.

### Stable
- **atfparser.py**: Production-ready eBL ATF parser with comprehensive test suite
- **syllabify.py**: Fully functional syllabifier with 60+ passing unit tests
- **repair.py**: Complete moraic repair system with LOB/SOB accent models, all tests passing
- **metricser.py**: Comprehensive metrics calculator with acoustic analysis and pause metrics, all tests passing
- **printer.py / print.py**: Accent/IPA rendering path and tests are stable

### Removed
- **src/akkapros/cli/format.py** (obsolete CLI formatter)

### Notes
- Core algorithms (parser, syllabifier, repair, metrics) are stable and unit tested
- Package structure ready for implementation
- CLI tools will be installed as console scripts via pyproject.toml
- `format.py` still in active development