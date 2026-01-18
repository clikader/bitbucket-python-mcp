"""Tests for repository tools."""

import json
from unittest.mock import patch

import pytest


class TestRepositoryTools:
    """Tests for repository management tools."""

    @pytest.mark.asyncio
    async def test_list_repositories(self, mock_env_vars, mock_bitbucket_client, sample_repository):
        """Test listing repositories returns formatted JSON."""
        with patch(
            "bitbucket_mcp.tools.repositories.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.repositories import register_repository_tools

            mcp = FastMCP("test")
            register_repository_tools(mcp)

            # Get the registered tool function
            list_repos = mcp._tool_manager._tools["list_repositories"].fn

            result = await list_repos()
            data = json.loads(result)

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "test-repo"
            assert data[0]["slug"] == "test-repo"
            assert "url" in data[0]

    @pytest.mark.asyncio
    async def test_get_repository(self, mock_env_vars, mock_bitbucket_client, sample_repository):
        """Test getting repository details."""
        with patch(
            "bitbucket_mcp.tools.repositories.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.repositories import register_repository_tools

            mcp = FastMCP("test")
            register_repository_tools(mcp)

            get_repo = mcp._tool_manager._tools["get_repository"].fn

            result = await get_repo(repository="test-repo")
            data = json.loads(result)

            assert data["name"] == "test-repo"
            assert data["description"] == "A test repository"
            assert "clone_urls" in data

    @pytest.mark.asyncio
    async def test_create_repository(self, mock_env_vars, mock_bitbucket_client, sample_repository):
        """Test creating a new repository."""
        with patch(
            "bitbucket_mcp.tools.repositories.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.repositories import register_repository_tools

            mcp = FastMCP("test")
            register_repository_tools(mcp)

            create_repo = mcp._tool_manager._tools["create_repository"].fn

            result = await create_repo(name="new-repo", description="New repository")
            data = json.loads(result)

            assert "message" in data
            assert "created successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_delete_repository_requires_confirmation(
        self, mock_env_vars, mock_bitbucket_client
    ):
        """Test that delete repository requires explicit confirmation."""
        with patch(
            "bitbucket_mcp.tools.repositories.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.repositories import register_repository_tools

            mcp = FastMCP("test")
            register_repository_tools(mcp)

            delete_repo = mcp._tool_manager._tools["delete_repository"].fn

            # Without confirmation
            result = await delete_repo(repository="test-repo", confirm=False)
            data = json.loads(result)

            assert "error" in data
            assert "not confirmed" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_repository_with_confirmation(self, mock_env_vars, mock_bitbucket_client):
        """Test deleting a repository with confirmation."""
        with patch(
            "bitbucket_mcp.tools.repositories.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.repositories import register_repository_tools

            mcp = FastMCP("test")
            register_repository_tools(mcp)

            delete_repo = mcp._tool_manager._tools["delete_repository"].fn

            result = await delete_repo(repository="test-repo", confirm=True)
            data = json.loads(result)

            assert "message" in data
            assert "deleted successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_update_repository_no_changes(self, mock_env_vars, mock_bitbucket_client):
        """Test that update repository requires at least one change."""
        with patch(
            "bitbucket_mcp.tools.repositories.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.repositories import register_repository_tools

            mcp = FastMCP("test")
            register_repository_tools(mcp)

            update_repo = mcp._tool_manager._tools["update_repository"].fn

            result = await update_repo(repository="test-repo")
            data = json.loads(result)

            assert "error" in data
            assert "No changes specified" in data["error"]
