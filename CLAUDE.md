# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BitBucket MCP Server - A Model Context Protocol (MCP) server for BitBucket Cloud operations. Enables AI coding agents (Claude Code CLI, Codex CLI) to interact with BitBucket repositories, branches, and pull requests.

## Commands

```bash
# Install dependencies
just install-dev       # or: uv sync --all-extras

# Run tests
just test              # or: uv run pytest
uv run pytest tests/test_memory.py -v           # Run specific test file
uv run pytest tests/test_memory.py::test_name   # Run specific test

# Lint and format
just fmt               # Format and auto-fix
just lint              # Lint only (no fixes)

# Run the server
just run               # or: uv run bitbucket-python-mcp
just dev               # Run with debug logging

# Build and publish
just build             # Build package
just publish           # Publish to PyPI
just publish-test      # Publish to TestPyPI

# Version management
just bump-version patch   # 0.1.0 -> 0.1.1
just bump-version minor   # 0.1.0 -> 0.2.0
just bv patch             # Alias for bump-version
```

## Architecture

### Core Components

- **`server.py`**: FastMCP server entry point. Creates the MCP server instance and registers all tool modules.
- **`client.py`**: Async wrapper around `atlassian-python-api`. Uses `asyncio.to_thread` to wrap synchronous BitBucket Cloud API calls. Provides `BitBucketClient` class with lazy initialization.
- **`config.py`**: Environment configuration (`BitBucketConfig`) and git remote URL detection (`RepoContext`). Auto-detects workspace/repository from git remote.
- **`memory.py`**: Persistent memory system for storing workspace standards and learnings. Stores JSON in `~/.bitbucket-python-mcp/memory/`.

### Tool Modules (`tools/`)

Each module exports a `register_*_tools(mcp)` function that registers MCP tools:
- `repositories.py`: Repository CRUD operations
- `branches.py`: Branch management
- `pull_requests.py`: PR operations (create, review, approve, comment)
- `search.py`: Code search and file browsing
- `memory.py`: Memory system tools for storing/retrieving learnings
- `users.py`: User search, workspace member lookup, default reviewers

### Key Patterns

1. **Tool Registration**: Each tool module uses `@mcp.tool()` decorators. Tools are registered in `server.py` via `register_*_tools(mcp)`.

2. **Async Wrapping**: The `BitBucketClient` wraps synchronous `atlassian-python-api` calls with `asyncio.to_thread()` for async compatibility.

3. **Repository Resolution**: Tools accept optional `repository` parameter. If not provided, auto-detects from current git remote via `get_current_repo()`.

4. **Branch Detection**: `get_current_branch()` in `config.py` detects the current git branch. Protected branches (`main`, `master`, `development`, `develop`, `dev`) cannot be used as PR source.

5. **Memory Categories**: `pipeline`, `testing`, `coding_style`, `tools`, `workflow`, `general`

6. **User Caching**: When users are found via `search_workspace_users`, they are cached in memory for future lookups without hitting the API again.

## Creating Pull Requests with Reviewers

The workflow for creating PRs with specific reviewers:

1. **Auto-detect branch**: If `source_branch` is not provided, uses current git branch
2. **Protected branch validation**: Cannot create PR from `main`, `master`, `development`, `develop`, or `dev`
3. **Default destination**: If `destination_branch` is not provided, defaults to `development`
4. **Default reviewers**: Repository's default reviewers are automatically included unless `include_default_reviewers=False`

### Adding Reviewers by Name

```
User: "Create a PR and add Boris as reviewer"

1. Call search_workspace_users(query="Boris")
2. If single match: use the account_id
3. If multiple matches: ask user to choose (returns status="multiple_matches")
4. If no match: inform user (returns status="not_found")
5. Call create_pull_request(title="...", reviewer_account_ids="<account_id>")
```

### Mentioning Users in Comments

Use `@{mention_name}` format from search results:
```
User: "Tag Mike in a comment saying please review"

1. search_workspace_users(query="Mike") -> returns mention_name: "mike"
2. add_pull_request_comment(pr_id=123, comment="@mike please review this ASAP")
```

## Testing

Tests use `pytest-asyncio` with `asyncio_mode = "auto"`. The `conftest.py` provides:
- `mock_env_vars`: Sets test environment variables
- `mock_bitbucket_client`: Pre-configured mock with sample data fixtures
- Sample data fixtures: `sample_repository`, `sample_branch`, `sample_pull_request`, etc.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BITBUCKET_USERNAME` | Yes | BitBucket username |
| `BITBUCKET_API_TOKEN` | Yes | App password from BitBucket settings |
| `BITBUCKET_WORKSPACE` | Yes | Default workspace slug |
| `BITBUCKET_MCP_DEBUG` | No | Enable debug logging (1/true/yes) |
