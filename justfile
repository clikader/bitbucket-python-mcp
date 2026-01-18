# BitBucket MCP Server - Justfile

# Default recipe
default:
    @just --list

# Install dependencies
install:
    uv sync

# Install with dev dependencies
install-dev:
    uv sync --all-extras

alias o := outdated
@outdated:
    # Show outdated packages, direct dependencies only, with headers, as long as uv is installed, uvx can be used, no need to install in repo
    uvx uv-outdated --direct --show-headers

# Run the MCP server
run:
    uv run bitbucket-python-mcp

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=bitbucket_mcp --cov-report=term-missing

# Format code with ruff
fmt:
    uv run ruff format src tests
    uv run ruff check --fix src tests

# Lint code with ruff
lint:
    uv run ruff check src tests

# Type check (if mypy is added)
# typecheck:
#     uv run mypy src

# Build package
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist build *.egg-info .pytest_cache .ruff_cache __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Publish to PyPI (requires PYPI_TOKEN)
publish:
    uv publish

# Publish to TestPyPI
publish-test:
    uv publish --index-url https://test.pypi.org/simple/

# Run server in development mode with debug logging
dev:
    BITBUCKET_MCP_DEBUG=1 uv run bitbucket-python-mcp

# Bump version (major, minor, or patch)
[doc("Bump version: just bump-version <major|minor|patch>")]
bump-version part:
    uv run bump-my-version bump {{part}}

# Alias for bump-version
alias bv := bump-version
