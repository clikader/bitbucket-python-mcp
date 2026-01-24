"""Tests for branch tools."""

import json
from unittest.mock import patch

import pytest

from bitbucket_mcp.config import RepoContext


class TestBranchTools:
    """Tests for branch management tools."""

    @pytest.mark.asyncio
    async def test_list_branches(self, mock_env_vars, mock_bitbucket_client, sample_branch):
        """Test listing branches returns formatted JSON."""
        with patch("bitbucket_mcp.tools.branches.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.branches import register_branch_tools

            mcp = FastMCP("test")
            register_branch_tools(mcp)

            list_branches = mcp._tool_manager._tools["list_branches"].fn

            result = await list_branches(repository="test-repo")
            data = json.loads(result)

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "feature-test"
            assert "commit_hash" in data[0]

    @pytest.mark.asyncio
    async def test_list_branches_no_repository(self, mock_env_vars, mock_bitbucket_client):
        """Test listing branches when no repository is specified and not in repo."""
        with patch("bitbucket_mcp.tools.branches.get_client", return_value=mock_bitbucket_client):
            with patch("bitbucket_mcp.tools.branches.get_current_repo", return_value=None):
                from mcp.server.fastmcp import FastMCP

                from bitbucket_mcp.tools.branches import register_branch_tools

                mcp = FastMCP("test")
                register_branch_tools(mcp)

                list_branches = mcp._tool_manager._tools["list_branches"].fn

                result = await list_branches()
                data = json.loads(result)

                assert "error" in data
                assert "No repository specified" in data["error"]

    @pytest.mark.asyncio
    async def test_list_branches_from_context(self, mock_env_vars, mock_bitbucket_client):
        """Test listing branches using git context."""
        repo_context = RepoContext(workspace="context-workspace", repository="context-repo")

        with patch("bitbucket_mcp.tools.branches.get_client", return_value=mock_bitbucket_client):
            with patch("bitbucket_mcp.tools.branches.get_current_repo", return_value=repo_context):
                from mcp.server.fastmcp import FastMCP

                from bitbucket_mcp.tools.branches import register_branch_tools

                mcp = FastMCP("test")
                register_branch_tools(mcp)

                list_branches = mcp._tool_manager._tools["list_branches"].fn

                result = await list_branches()
                data = json.loads(result)

                assert isinstance(data, list)
                # Verify the client was called with context values (including default limit)
                mock_bitbucket_client.list_branches.assert_called_with(
                    "context-repo", "context-workspace", 50
                )

    @pytest.mark.asyncio
    async def test_get_branch(self, mock_env_vars, mock_bitbucket_client, sample_branch):
        """Test getting branch details."""
        with patch("bitbucket_mcp.tools.branches.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.branches import register_branch_tools

            mcp = FastMCP("test")
            register_branch_tools(mcp)

            get_branch = mcp._tool_manager._tools["get_branch"].fn

            result = await get_branch(branch_name="feature-test", repository="test-repo")
            data = json.loads(result)

            assert data["name"] == "feature-test"
            assert "commit" in data
            assert data["commit"]["hash"] == "abc123def456"

    @pytest.mark.asyncio
    async def test_create_branch(self, mock_env_vars, mock_bitbucket_client, sample_branch):
        """Test creating a new branch."""
        with patch("bitbucket_mcp.tools.branches.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.branches import register_branch_tools

            mcp = FastMCP("test")
            register_branch_tools(mcp)

            create_branch = mcp._tool_manager._tools["create_branch"].fn

            result = await create_branch(
                branch_name="new-feature",
                source_branch="development",
                repository="test-repo",
            )
            data = json.loads(result)

            assert "message" in data
            assert "created successfully" in data["message"]
            assert "development" in data["message"]

    @pytest.mark.asyncio
    async def test_delete_branch_requires_confirmation(self, mock_env_vars, mock_bitbucket_client):
        """Test that delete branch requires explicit confirmation."""
        with patch("bitbucket_mcp.tools.branches.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.branches import register_branch_tools

            mcp = FastMCP("test")
            register_branch_tools(mcp)

            delete_branch = mcp._tool_manager._tools["delete_branch"].fn

            result = await delete_branch(
                branch_name="old-feature",
                confirm=False,
                repository="test-repo",
            )
            data = json.loads(result)

            assert "error" in data
            assert "not confirmed" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_branch_with_confirmation(self, mock_env_vars, mock_bitbucket_client):
        """Test deleting a branch with confirmation."""
        with patch("bitbucket_mcp.tools.branches.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.branches import register_branch_tools

            mcp = FastMCP("test")
            register_branch_tools(mcp)

            delete_branch = mcp._tool_manager._tools["delete_branch"].fn

            result = await delete_branch(
                branch_name="old-feature",
                confirm=True,
                repository="test-repo",
            )
            data = json.loads(result)

            assert "message" in data
            assert "deleted successfully" in data["message"]
