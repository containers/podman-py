# AGENTS.md

## Project Overview

podman-py is a Python library providing bindings for the Podman RESTful API. It allows Python applications to interact with Podman containers, images, pods, and other resources programmatically. The library provides Docker API compatibility, making it a drop-in replacement for Docker-based applications.

- **Language**: Python 3.9+
- **Package Manager**: pip/setuptools
- **Build System**: setuptools with pyproject.toml
- **Testing Framework**: pytest with tox for multi-version testing, unittest for test execution
- **Code Coverage**: coverage.py - https://coverage.readthedocs.io/
- **Linting/Formatting**: ruff (replaces black + flake8) - https://docs.astral.sh/ruff/
- **Type Checking**: mypy
- **Documentation**: Sphinx

## Setup Commands

**Important**: This project uses a Makefile for common development tasks. Always prefer `make` commands over calling `tox` directly when available.

**Note for AI Agents**: The `.cursorignore` file specifies directories and files to exclude from indexing (build artifacts, caches, virtual environments, etc.). Respect these exclusions to focus on source code.

### Development Environment

```bash
# Clone and setup
git clone https://github.com/containers/podman-py.git
cd podman-py

# Install in development mode with test dependencies
pip install -e .[test]

# Or use tox for isolated environments
pip install tox
```

### Install Dependencies

```bash
# Runtime dependencies only
pip install -e .

# With optional dependencies
pip install -e .[progress_bar,docs,test]

# Install tox for testing (make targets use tox internally)
make tox

# Using tox directly for development environment
tox --devenv venv  # Creates development environment
```

## Build and Test Commands

### Available Make Targets

```bash
# View all available make targets
make help  # (if available) or check Makefile

# Build and Package:
make podman                           # Build package
make clean                            # Clean build artifacts
make docs                             # Build documentation

# Testing:
make tests                            # Run all tests with coverage
make unittest                         # Run unit tests only
make integration                      # Run integration tests only

# Code Quality:
make lint                             # Run linting, formatting, and type checks
make validate                         # Run git validation and linting

# Release:
make test-release                     # Test release to TestPyPI
make release                          # Production release to PyPI
make rpm                              # Build rpm packages

# Setup and Cleanup:
make tox                              # Install tox and Python versions
make uninstall                        # Uninstall podman package
make clobber                          # Uninstall and clean everything
```

### Building

```bash
# Build package
make podman
# or
python -m build
```

### Testing

```bash
# Run all tests with coverage (recommended)
make tests

# Run unit tests only
make unittest

# Run integration tests only
make integration

# Advanced: Run specific test (use tox directly when make doesn't cover the use case)
tox -e py -- podman/tests/integration/test_container_create.py -k test_specific

# Test against specific Python version
tox -e py312 -- podman/tests/unit/

# Test with custom Podman binary
PODMAN_BINARY=/path/to/podman tox -e py

# Test future features (requires podman-next)
tox -e py -- --pnext -m pnext
```

### Linting and Formatting

```bash
# Run all linting checks (includes format, lint, mypy)
make lint

# For individual checks, use tox directly if needed:
# Check formatting only
tox -e format

# Check linting only
tox -e lint

# Type checking only
tox -e mypy

# Auto-fix formatting and linting (use ruff directly)
ruff format
ruff check --fix
```

## Code Style Guidelines

### Formatting (ruff)

- Line length: 100 characters
- Quote style: preserve existing (mix of single/double quotes)
- Use ruff for both formatting and linting (replaces black + flake8)
- Ruff documentation: https://docs.astral.sh/ruff/
- Ruff formatter: https://docs.astral.sh/ruff/formatter/
- Ruff linter: https://docs.astral.sh/ruff/linter/

### Linting Rules

- Pyflakes (F), Pycodestyle (E/W), PEP8 Naming (N)
- Pyupgrade (UP), Bugbear (B), flake8-builtins (A)
- Pylint Convention/Error/Warning (PLC/PLE/PLW)
- Complete ruff rules reference: https://docs.astral.sh/ruff/rules/

### Documentation

- Use Google style docstrings
- Exception: kwargs documented as "Keyword Arguments" section
- Format: `kwarg1 (int): Description of kwarg1`

### Type Hints

- mypy configuration in pyproject.toml
- Some modules have `ignore_errors = true` (legacy code)
- New code should include proper type hints

## Testing Guidelines

### Test Structure

- Unit tests: `podman/tests/unit/`
- Integration tests: `podman/tests/integration/`
- Test configuration: `pyproject.toml` [tool.pytest.ini_options]
- Uses Python's built-in unittest framework: https://docs.python.org/3/library/unittest.html
- unittest discovery documentation: https://docs.python.org/3/library/unittest.html#test-discovery

### Coverage Requirements

- Minimum 85% coverage (enforced by tox -e coverage)
- Code will not be merged if coverage drops below 85%
- Exclude test files from coverage: `--omit=podman/tests/*`
- Uses coverage.py: https://coverage.readthedocs.io/
- Configuration in `.coveragerc` and `pyproject.toml`: https://coverage.readthedocs.io/en/latest/config.html

### Test Environment Variables

```bash
PODMAN_LOG_LEVEL=INFO  # Default log level
PODMAN_BINARY=podman   # Podman binary to test against
DEBUG=0                # Debug mode
```

### Version-Specific Testing

```python
# Skip tests based on Podman version
@pytest.mark.skipif(
    PODMAN_VERSION < (5, 6, 0),
    reason="Feature introduced in Podman 5.6.0"
)

# Skip tests based on OS
@pytest.mark.skipif(
    OS_RELEASE["ID"] == "fedora" and int(OS_RELEASE["VERSION_ID"]) < 42,
    reason="Feature patched in F42 or later"
)

# Mark tests for future features
@pytest.mark.pnext
```

## Development Workflow

### Pre-commit Setup

```bash
pip install pre-commit
pre-commit install
# Run manually: pre-commit run -a
```

### SSH Testing Requirements

Tests establish SSH connections to localhost. Ensure you can run:

```bash
ssh localhost exit
```

### Commit Guidelines

- Use `git commit -s` for signed-off commits
- Include `Signed-off-by: Your Name <email@example.com>`
- Follow conventional commit format when possible

## Security Considerations

### SSH Connection Security

- **CRITICAL**: The current SSH implementation in `podman/api/ssh.py` has a security vulnerability
- Line 66 uses `"StrictHostKeyChecking no"` which disables host key verification
- This makes connections vulnerable to man-in-the-middle attacks
- When modifying SSH code, always enable proper host key checking

### Identity File Validation

- SSH identity files should have restrictive permissions (0600)
- Validate file existence and permissions before use
- Use absolute paths for identity files

## File Structure

### Core Modules

- `podman/client.py` - Main PodmanClient class
- `podman/api/` - Low-level API adapters (HTTP, SSH, UDS)
- `podman/domain/` - High-level domain objects (containers, images, etc.)
- `podman/errors/` - Exception classes

### Configuration Files

- `Makefile` - Build and development commands
- `pyproject.toml` - Project metadata, dependencies, tool configuration
- `tox.ini` - Testing environments and commands
- `setup.py` - Legacy build configuration (minimal)
- `.coveragerc` - Coverage configuration
- `.cursorignore` - Files and directories to exclude from AI agent indexing

### Files to Exclude from Indexing

The `.cursorignore` file specifies files and directories that AI agents should avoid indexing or processing. **Note**: Items already covered by `.gitignore` should not be duplicated in `.cursorignore` to avoid redundancy. Key exclusions include:

**Build Artifacts:**

- `build/`, `dist/`, `*.egg-info/`, `__pycache__/`
- `_build/`, `docs/_build/` (documentation builds)

**Development Environment:**

- `venv/`, `.venv/`, `.tox/` (virtual environments)
- `.pytest_cache/`, `.mypy_cache/`, `.coverage` (tool caches)

**IDE and System Files:**

- `.vscode/`, `.idea/` (editor configurations)
- `.DS_Store`, `Thumbs.db` (OS-generated files)

**Binary and Log Files:**

- `*.so`, `*.dylib`, `*.dll` (compiled binaries)
- `*.log`, `*.tmp` (logs and temporary files)

Agents should respect these exclusions to focus on source code and avoid processing generated or temporary files.

## Documentation

### Building Docs

```bash
# Build documentation (preferred)
make docs

# Manual documentation build (if needed)
sphinx-apidoc --separate --no-toc --force -o docs/source/ podman podman/tests
cd docs/source && python3 -m sphinx -T -E -W --keep-going -b html -d _build/doctrees -D language=en . _build/html
```

### API Documentation

- Auto-generated from docstrings using Sphinx
- Available at: https://podman-py.readthedocs.io/en/latest/
- Libpod API reference: https://docs.podman.io/en/latest/_static/api.html
- Docker API compatibility: https://docs.docker.com/engine/api/latest/

## Release Process

### Version Management

- Version defined in `pyproject.toml` (currently 5.6.0)
- Note: Future versions may use dynamic versioning from `podman.version.__version__`

### Publishing

See "Available Make Targets" section above for release commands (`make test-release`, `make release`, `make rpm`).

## Cleanup and Maintenance

See "Available Make Targets" section above for cleanup commands (`make clean`, `make uninstall`, `make clobber`, `make validate`).

## Common Issues

### SSH Connection Problems

If tests hang with repeated "Waiting on socket" messages:

```log
DEBUG] Waiting on /run/user/1000/podman/podman-forward-*.sock
```

Fix SSH localhost connectivity: `ssh localhost exit` should work without prompts.

### Tox Environment Issues

```bash
# Clean tox environments
tox --recreate

# Install missing Python versions - use `make tox` (handles platform differences)
make tox
```
