# Contributing to Akkadian Prosody Toolkit (akkapros)

Thank you for your interest in contributing to the Akkadian Prosody Toolkit! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Versioning](#versioning)
- [Reporting Issues](#reporting-issues)

---

## 📜 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct: be respectful, constructive, and collaborative. We welcome contributors from all backgrounds and experience levels.

---

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**:

       git clone https://github.com/YOUR-USERNAME/akkapros.git
       cd akkapros

3. **Set up upstream remote**:

       git remote add upstream https://github.com/samuelkabak/akkapros.git

4. **Create a branch** for your work:

       git checkout -b feature/your-feature-name

---

## 🔧 Development Environment

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- git

### Setting Up a Development Environment

1. **Create and activate a virtual environment**:

       python -m venv venv
       source venv/bin/activate  # On Windows: venv\Scripts\activate

2. **Install development dependencies**:

       pip install -r requirements-dev.txt

   This installs:
   - pytest for testing
   - black for code formatting
   - flake8 for linting
   - mypy for type checking

3. **Install the package in editable mode**:

       pip install -e .

4. **Verify the installation**:

       python -m akkapros.cli.fullprosmaker --help

---

## 💻 Coding Standards

We follow these coding standards to maintain consistency:

### Python Style

- **Formatting**: Use `black` with default settings
- **Linting**: Use `flake8` (max line length: 88, matching black)
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings

### Running Formatters and Linters

    # Format code
    black src/ tests/

    # Check style
    flake8 src/ tests/

    # Type check
    mypy src/

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | lowercase_with_underscores | `syllabifier.py` |
| Classes | CapWords | `Syllabifier` |
| Functions/Methods | lowercase_with_underscores | `syllabify_line()` |
| Constants | UPPERCASE_WITH_UNDERSCORES | `MAX_ITERATIONS` |
| Private members | _leading_underscore | `_internal_helper()` |

---

## 🧪 Testing

We use `pytest` for testing. All new features and bug fixes should include tests.

### Running Tests

    # Run all tests
    pytest

    # Run with coverage
    pytest --cov=akkapros tests/

    # Run specific test file
    pytest tests/test_syllabifier.py

    # Run built-in CLI tests
    python -m akkapros.cli.syllabifier --test
    python -m akkapros.cli.prosmaker --test
    python -m akkapros.cli.metricalc --test
    python -m akkapros.cli.printer --test
    python -m akkapros.cli.fullprosmaker --test-all

### Test Requirements

- **Unit tests**: For individual functions and classes
- **Integration tests**: For CLI workflows and pipeline stages
- **Regression tests**: For fixed bugs
- **Coverage target**: Aim for at least 80% code coverage

### Test Data

Place test files in `tests/data/`. Use small, representative samples.

---

## 📤 Pull Request Process

### Before Submitting

1. **Update your fork** with the latest upstream changes:

       git fetch upstream
       git rebase upstream/main

2. **Run the full test suite** to ensure everything passes
3. **Run formatters and linters** to ensure code quality
4. **Update documentation** if your changes affect user-facing behavior
5. **Update `CHANGELOG.md`** with your changes under the "Unreleased" section

### Submitting

1. **Push your branch** to your fork:

       git push origin feature/your-feature-name

2. **Open a pull request** on GitHub
3. **Fill out the PR template** with:
   - Description of changes
   - Related issue numbers
   - Testing performed
   - Documentation updates

### Review Process

1. Maintainers will review your PR
2. CI checks must pass (tests, formatting, linting)
3. Address review feedback with additional commits
4. Once approved, a maintainer will merge your PR

---

## 📌 Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0 → 2.0.0): Incompatible API/CLI changes
- **MINOR** (1.0.0 → 1.1.0): Backward-compatible new features
- **PATCH** (1.0.0 → 1.0.1): Bug fixes and documentation updates

### Versioning Guidelines

| Change Type | Version Bump | Examples |
|-------------|--------------|----------|
| Breaking change | MAJOR | Removing a CLI flag, changing output format |
| New feature | MINOR | Adding a new output format, new optional flag |
| Bug fix | PATCH | Fixing a crash, correcting documentation |
| Documentation | PATCH | README updates, docstring improvements |

See `docs/akkapros/release-strategy.md` for detailed release procedures.

---

## 🐛 Reporting Issues

### Bug Reports

When reporting a bug, please include:

- **Description**: What happened and what you expected
- **Steps to reproduce**: Minimal example that triggers the bug
- **Environment**:
  - Operating system
  - Python version
  - akkapros version
- **Error messages**: Full error output
- **Sample input**: If applicable, a small example that reproduces the issue

### Feature Requests

When requesting a feature, please include:

- **Problem**: What problem you're trying to solve
- **Proposed solution**: How you envision the feature working
- **Alternatives**: Other approaches you've considered
- **Relevance**: How this benefits Akkadian studies or computational linguistics

### Using Issue Templates

We provide issue templates for:

- Bug reports
- Feature requests

Please use them—they ensure we have all the information needed to help you.

---

## 🤝 Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Contact**: Reach out via ORCID: 0000-0001-7976-5038

---

## 🙏 Thank You

Your contributions help advance Akkadian linguistics and computational philology. Every contribution, no matter how small, is valued and appreciated.

**Happy coding!** 🏛️✨