"""Tests for user tools in BitBucket MCP Server."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def sample_workspace_member():
    """Sample workspace member data for testing."""
    return {
        "user": {
            "account_id": "5b12345678901234567890ab",
            "uuid": "{12345678-1234-1234-1234-123456789012}",
            "display_name": "Boris Miller",
            "nickname": "boris",
            "type": "user",
            "links": {
                "avatar": {"href": "https://bitbucket.org/account/boris/avatar/"},
            },
        },
        "workspace": {"slug": "test-workspace"},
    }


@pytest.fixture
def sample_workspace_members(sample_workspace_member):
    """Sample list of workspace members for testing."""
    return [
        sample_workspace_member,
        {
            "user": {
                "account_id": "5b98765432109876543210cd",
                "uuid": "{87654321-4321-4321-4321-210987654321}",
                "display_name": "Mike Mucha",
                "nickname": "mike",
                "type": "user",
                "links": {},
            },
            "workspace": {"slug": "test-workspace"},
        },
        {
            "user": {
                "account_id": "5baaaabbbbccccddddeeeeef",
                "uuid": "{aaaabbbb-cccc-dddd-eeee-ffffffaaaaaa}",
                "display_name": "Mike Smith",
                "nickname": "mikes",
                "type": "user",
                "links": {},
            },
            "workspace": {"slug": "test-workspace"},
        },
    ]


@pytest.fixture
def sample_default_reviewer():
    """Sample default reviewer data for testing."""
    return {
        "account_id": "5b12345678901234567890ab",
        "uuid": "{12345678-1234-1234-1234-123456789012}",
        "display_name": "Default Reviewer",
        "nickname": "default_reviewer",
    }


class TestSearchWorkspaceUsers:
    """Tests for search_workspace_users tool."""

    @pytest.mark.asyncio
    async def test_search_users_single_match(self, mock_env_vars, sample_workspace_members):
        """Test searching for users with a single match returns correct user."""
        from bitbucket_mcp.tools.users import register_user_tools

        mock_mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_user_tools(mock_mcp)

        with (
            patch("bitbucket_mcp.tools.users.get_client") as mock_get_client,
            patch("bitbucket_mcp.tools.users._get_cached_user", return_value=None),
            patch("bitbucket_mcp.tools.users._cache_user"),
        ):
            mock_client = MagicMock()
            # Only Boris matches
            mock_client.search_workspace_users = AsyncMock(
                return_value=[
                    {
                        "account_id": "5b12345678901234567890ab",
                        "uuid": "{12345678-1234-1234-1234-123456789012}",
                        "display_name": "Boris Miller",
                        "nickname": "boris",
                        "type": "user",
                        "links": {},
                    }
                ]
            )
            mock_client.default_workspace = "test-workspace"
            mock_get_client.return_value = mock_client

            result = await tools["search_workspace_users"]("Boris")
            data = json.loads(result)

            assert data["status"] == "success"
            assert data["count"] == 1
            assert data["users"][0]["display_name"] == "Boris Miller"
            assert data["users"][0]["account_id"] == "5b12345678901234567890ab"

    @pytest.mark.asyncio
    async def test_search_users_multiple_matches(self, mock_env_vars):
        """Test searching for users with multiple matches returns all and signals ambiguity."""
        from bitbucket_mcp.tools.users import register_user_tools

        mock_mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_user_tools(mock_mcp)

        with (
            patch("bitbucket_mcp.tools.users.get_client") as mock_get_client,
            patch("bitbucket_mcp.tools.users._get_cached_user", return_value=None),
            patch("bitbucket_mcp.tools.users._cache_user"),
        ):
            mock_client = MagicMock()
            # Two Mikes match
            mock_client.search_workspace_users = AsyncMock(
                return_value=[
                    {
                        "account_id": "5b98765432109876543210cd",
                        "display_name": "Mike Mucha",
                        "nickname": "mike",
                    },
                    {
                        "account_id": "5baaaabbbbccccddddeeeeef",
                        "display_name": "Mike Smith",
                        "nickname": "mikes",
                    },
                ]
            )
            mock_client.default_workspace = "test-workspace"
            mock_get_client.return_value = mock_client

            result = await tools["search_workspace_users"]("Mike")
            data = json.loads(result)

            assert data["status"] == "multiple_matches"
            assert data["count"] == 2
            assert "Please specify" in data["message"]

    @pytest.mark.asyncio
    async def test_search_users_no_match(self, mock_env_vars):
        """Test searching for users with no match returns not_found status."""
        from bitbucket_mcp.tools.users import register_user_tools

        mock_mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_user_tools(mock_mcp)

        with (
            patch("bitbucket_mcp.tools.users.get_client") as mock_get_client,
            patch("bitbucket_mcp.tools.users._get_cached_user", return_value=None),
        ):
            mock_client = MagicMock()
            mock_client.search_workspace_users = AsyncMock(return_value=[])
            mock_client.default_workspace = "test-workspace"
            mock_get_client.return_value = mock_client

            result = await tools["search_workspace_users"]("Nonexistent")
            data = json.loads(result)

            assert data["status"] == "not_found"
            assert "Nonexistent" in data["message"]

    @pytest.mark.asyncio
    async def test_search_users_from_cache(self, mock_env_vars):
        """Test that cached users are returned without hitting the API."""
        from bitbucket_mcp.tools.users import register_user_tools

        mock_mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_user_tools(mock_mcp)

        cached_user = {
            "account_id": "cached-account-id",
            "display_name": "Cached User",
            "nickname": "cached",
        }

        with (
            patch("bitbucket_mcp.tools.users.get_client") as mock_get_client,
            patch("bitbucket_mcp.tools.users._get_cached_user", return_value=cached_user),
        ):
            mock_client = MagicMock()
            mock_client.search_workspace_users = AsyncMock()
            mock_client.default_workspace = "test-workspace"
            mock_get_client.return_value = mock_client

            result = await tools["search_workspace_users"]("Cached")
            data = json.loads(result)

            assert data["status"] == "success"
            assert data["source"] == "memory_cache"
            # API should not have been called
            mock_client.search_workspace_users.assert_not_called()


class TestGetCurrentGitBranch:
    """Tests for get_current_git_branch tool."""

    @pytest.mark.asyncio
    async def test_get_current_branch_success(self, mock_env_vars):
        """Test getting current branch when in a git repository."""
        from bitbucket_mcp.tools.users import register_user_tools

        mock_mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_user_tools(mock_mcp)

        with patch(
            "bitbucket_mcp.tools.users.get_current_branch", return_value="feature/test-branch"
        ):
            result = await tools["get_current_git_branch"]()
            data = json.loads(result)

            assert data["status"] == "success"
            assert data["branch"] == "feature/test-branch"

    @pytest.mark.asyncio
    async def test_get_current_branch_not_in_repo(self, mock_env_vars):
        """Test getting current branch when not in a git repository."""
        from bitbucket_mcp.tools.users import register_user_tools

        mock_mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_user_tools(mock_mcp)

        with patch("bitbucket_mcp.tools.users.get_current_branch", return_value=None):
            result = await tools["get_current_git_branch"]()
            data = json.loads(result)

            assert data["status"] == "error"
            assert "git repository" in data["message"]


class TestGetDefaultReviewers:
    """Tests for get_default_reviewers tool."""

    @pytest.mark.asyncio
    async def test_get_default_reviewers_success(self, mock_env_vars, sample_default_reviewer):
        """Test getting default reviewers for a repository."""
        from bitbucket_mcp.tools.users import register_user_tools

        mock_mcp = MagicMock()
        tools = {}

        def capture_tool():
            def decorator(func):
                tools[func.__name__] = func
                return func

            return decorator

        mock_mcp.tool = capture_tool
        register_user_tools(mock_mcp)

        with (
            patch("bitbucket_mcp.tools.users.get_client") as mock_get_client,
            patch(
                "bitbucket_mcp.tools.users.get_current_repo",
                return_value=MagicMock(repository="test-repo", workspace="test-workspace"),
            ),
        ):
            mock_client = MagicMock()
            mock_client.get_default_reviewers = AsyncMock(return_value=[sample_default_reviewer])
            mock_get_client.return_value = mock_client

            result = await tools["get_default_reviewers"]()
            data = json.loads(result)

            assert data["status"] == "success"
            assert data["count"] == 1
            assert data["default_reviewers"][0]["display_name"] == "Default Reviewer"
