"""Pytest configuration and fixtures for BitBucket MCP Server tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("BITBUCKET_USERNAME", "test-user")
    monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-password")
    monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-workspace")


@pytest.fixture
def sample_repository() -> dict[str, Any]:
    """Sample repository data for testing."""
    return {
        "name": "test-repo",
        "slug": "test-repo",
        "full_name": "test-workspace/test-repo",
        "description": "A test repository",
        "is_private": True,
        "language": "python",
        "created_on": "2025-01-01T00:00:00.000000+00:00",
        "updated_on": "2025-01-15T00:00:00.000000+00:00",
        "size": 1024,
        "mainbranch": {"name": "main"},
        "links": {
            "html": {"href": "https://bitbucket.org/test-workspace/test-repo"},
            "clone": [
                {"name": "https", "href": "https://bitbucket.org/test-workspace/test-repo.git"},
                {"name": "ssh", "href": "git@bitbucket.org:test-workspace/test-repo.git"},
            ],
        },
    }


@pytest.fixture
def sample_branch() -> dict[str, Any]:
    """Sample branch data for testing."""
    return {
        "name": "feature-test",
        "target": {
            "hash": "abc123def456",
            "message": "Test commit message",
            "date": "2025-01-15T12:00:00.000000+00:00",
            "author": {
                "user": {"display_name": "Test User"},
                "raw": "Test User <test@example.com>",
            },
        },
        "links": {
            "html": {"href": "https://bitbucket.org/test-workspace/test-repo/branch/feature-test"},
            "commits": {
                "href": "https://api.bitbucket.org/2.0/repositories/test-workspace/test-repo/commits/feature-test"
            },
        },
    }


@pytest.fixture
def sample_pull_request() -> dict[str, Any]:
    """Sample pull request data for testing."""
    return {
        "id": 42,
        "title": "Test Pull Request",
        "description": "This is a test PR",
        "state": "OPEN",
        "author": {
            "display_name": "Test Author",
            "username": "test-author",
        },
        "source": {
            "branch": {"name": "feature-test"},
            "repository": {"full_name": "test-workspace/test-repo"},
        },
        "destination": {
            "branch": {"name": "development"},
        },
        "reviewers": [
            {"display_name": "Reviewer One"},
        ],
        "participants": [
            {
                "user": {"display_name": "Test Author"},
                "role": "AUTHOR",
                "approved": False,
            },
        ],
        "created_on": "2025-01-14T00:00:00.000000+00:00",
        "updated_on": "2025-01-15T00:00:00.000000+00:00",
        "close_source_branch": False,
        "links": {
            "html": {"href": "https://bitbucket.org/test-workspace/test-repo/pull-requests/42"},
        },
    }


@pytest.fixture
def sample_comment() -> dict[str, Any]:
    """Sample comment data for testing."""
    return {
        "id": 123,
        "content": {"raw": "This is a test comment"},
        "user": {"display_name": "Test Commenter"},
        "created_on": "2025-01-15T10:00:00.000000+00:00",
        "updated_on": "2025-01-15T10:00:00.000000+00:00",
        "inline": None,
    }


@pytest.fixture
def sample_inline_comment() -> dict[str, Any]:
    """Sample inline comment data for testing."""
    return {
        "id": 124,
        "content": {"raw": "This is an inline comment"},
        "user": {"display_name": "Test Reviewer"},
        "created_on": "2025-01-15T11:00:00.000000+00:00",
        "updated_on": "2025-01-15T11:00:00.000000+00:00",
        "inline": {
            "path": "src/main.py",
            "to": 42,
        },
    }


@pytest.fixture
def mock_bitbucket_client(
    sample_repository,
    sample_branch,
    sample_pull_request,
    sample_comment,
):
    """Create a mock BitBucket client for testing."""
    mock = MagicMock()

    # Configure async methods
    mock.list_repositories = AsyncMock(return_value=[sample_repository])
    mock.get_repository = AsyncMock(return_value=sample_repository)
    mock.create_repository = AsyncMock(return_value=sample_repository)
    mock.delete_repository = AsyncMock(return_value=True)
    mock.update_repository = AsyncMock(return_value=sample_repository)

    mock.list_branches = AsyncMock(return_value=[sample_branch])
    mock.get_branch = AsyncMock(return_value=sample_branch)
    mock.create_branch = AsyncMock(return_value=sample_branch)
    mock.delete_branch = AsyncMock(return_value=True)

    mock.list_pull_requests = AsyncMock(return_value=[sample_pull_request])
    mock.get_pull_request = AsyncMock(return_value=sample_pull_request)
    mock.get_pull_request_diff = AsyncMock(return_value="diff --git a/file.py b/file.py\n+new line")
    mock.get_pull_request_comments = AsyncMock(return_value=[sample_comment])
    mock.add_pull_request_comment = AsyncMock(return_value=sample_comment)
    mock.approve_pull_request = AsyncMock(
        return_value={"approved": True, "user": {"display_name": "Test User"}}
    )
    mock.request_changes = AsyncMock(return_value={"user": {"display_name": "Test User"}})
    mock.create_pull_request = AsyncMock(return_value=sample_pull_request)

    mock.get_repository_contents = AsyncMock(return_value={"values": []})
    mock.search_code = AsyncMock(return_value=[])

    mock.default_workspace = "test-workspace"
    mock.resolve_workspace = MagicMock(side_effect=lambda w: w or "test-workspace")
    mock.resolve_repository = MagicMock(side_effect=lambda r: r)

    # User/member operations
    mock.list_workspace_members = AsyncMock(return_value=[])
    mock.search_workspace_users = AsyncMock(return_value=[])
    mock.get_default_reviewers = AsyncMock(return_value=[])

    return mock
