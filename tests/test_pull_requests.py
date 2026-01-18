"""Tests for pull request tools."""

import json
from unittest.mock import patch

import pytest


class TestPullRequestTools:
    """Tests for pull request tools."""

    @pytest.mark.asyncio
    async def test_list_pull_requests(
        self, mock_env_vars, mock_bitbucket_client, sample_pull_request
    ):
        """Test listing pull requests."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            list_prs = mcp._tool_manager._tools["list_pull_requests"].fn

            result = await list_prs(repository="test-repo")
            data = json.loads(result)

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["id"] == 42
            assert data[0]["title"] == "Test Pull Request"
            assert data[0]["state"] == "OPEN"

    @pytest.mark.asyncio
    async def test_get_pull_request(
        self, mock_env_vars, mock_bitbucket_client, sample_pull_request
    ):
        """Test getting pull request details."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            get_pr = mcp._tool_manager._tools["get_pull_request"].fn

            result = await get_pr(pr_id=42, repository="test-repo")
            data = json.loads(result)

            assert data["id"] == 42
            assert data["title"] == "Test Pull Request"
            assert "description" in data
            assert "participants" in data

    @pytest.mark.asyncio
    async def test_get_pull_request_newest(self, mock_env_vars, mock_bitbucket_client):
        """Test getting the newest pull request when no ID specified."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            get_pr = mcp._tool_manager._tools["get_pull_request"].fn

            result = await get_pr(repository="test-repo")
            data = json.loads(result)

            # Should get the first (newest) PR
            assert data["id"] == 42

    @pytest.mark.asyncio
    async def test_get_pull_request_diff(self, mock_env_vars, mock_bitbucket_client):
        """Test getting pull request diff."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            get_diff = mcp._tool_manager._tools["get_pull_request_diff"].fn

            result = await get_diff(pr_id=42, repository="test-repo")

            assert "diff --git" in result
            assert "+new line" in result

    @pytest.mark.asyncio
    async def test_get_pull_request_comments(
        self, mock_env_vars, mock_bitbucket_client, sample_comment
    ):
        """Test getting pull request comments."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            get_comments = mcp._tool_manager._tools["get_pull_request_comments"].fn

            result = await get_comments(pr_id=42, repository="test-repo")
            data = json.loads(result)

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["content"] == "This is a test comment"
            assert data[0]["is_inline"] is False

    @pytest.mark.asyncio
    async def test_add_pull_request_comment(self, mock_env_vars, mock_bitbucket_client):
        """Test adding a comment to a pull request."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            add_comment = mcp._tool_manager._tools["add_pull_request_comment"].fn

            result = await add_comment(
                pr_id=42,
                comment="Great work!",
                repository="test-repo",
            )
            data = json.loads(result)

            assert data["message"] == "Comment added successfully"
            assert "comment_id" in data

    @pytest.mark.asyncio
    async def test_approve_pull_request(self, mock_env_vars, mock_bitbucket_client):
        """Test approving a pull request."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            approve = mcp._tool_manager._tools["approve_pull_request"].fn

            result = await approve(pr_id=42, repository="test-repo")
            data = json.loads(result)

            assert "approved successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_request_changes(self, mock_env_vars, mock_bitbucket_client):
        """Test requesting changes on a pull request."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            request_changes = mcp._tool_manager._tools["request_changes"].fn

            result = await request_changes(
                pr_id=42,
                comment="Please fix the tests",
                repository="test-repo",
            )
            data = json.loads(result)

            assert "Changes requested" in data["message"]
            assert data["comment_added"] is True

    @pytest.mark.asyncio
    async def test_create_pull_request(self, mock_env_vars, mock_bitbucket_client):
        """Test creating a new pull request."""
        with patch(
            "bitbucket_mcp.tools.pull_requests.get_client", return_value=mock_bitbucket_client
        ):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.pull_requests import register_pull_request_tools

            mcp = FastMCP("test")
            register_pull_request_tools(mcp)

            create_pr = mcp._tool_manager._tools["create_pull_request"].fn

            result = await create_pr(
                title="New Feature",
                source_branch="feature-new",
                destination_branch="development",
                repository="test-repo",
            )
            data = json.loads(result)

            assert data["message"] == "Pull request created successfully"
            assert "id" in data
            assert "url" in data
