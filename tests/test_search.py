"""Tests for search tools."""

import json
from unittest.mock import patch

import pytest


class TestSearchTools:
    """Tests for search and content tools."""

    @pytest.mark.asyncio
    async def test_search_repositories(
        self, mock_env_vars, mock_bitbucket_client, sample_repository
    ):
        """Test searching for repositories."""
        with patch("bitbucket_mcp.tools.search.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.search import register_search_tools

            mcp = FastMCP("test")
            register_search_tools(mcp)

            search_repos = mcp._tool_manager._tools["search_repositories"].fn

            result = await search_repos(query="test")
            data = json.loads(result)

            assert "count" in data
            assert data["count"] == 1
            assert data["results"][0]["name"] == "test-repo"

    @pytest.mark.asyncio
    async def test_search_repositories_no_match(self, mock_env_vars, mock_bitbucket_client):
        """Test searching with no matches."""
        with patch("bitbucket_mcp.tools.search.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.search import register_search_tools

            mcp = FastMCP("test")
            register_search_tools(mcp)

            search_repos = mcp._tool_manager._tools["search_repositories"].fn

            result = await search_repos(query="nonexistent")
            data = json.loads(result)

            assert "message" in data
            assert "No repositories found" in data["message"]

    @pytest.mark.asyncio
    async def test_get_repository_contents(self, mock_env_vars, mock_bitbucket_client):
        """Test getting repository contents."""
        mock_bitbucket_client.get_repository_contents.return_value = {
            "values": [
                {"path": "src", "type": "commit_directory", "size": None},
                {"path": "README.md", "type": "commit_file", "size": 1024},
            ]
        }

        with patch("bitbucket_mcp.tools.search.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.search import register_search_tools

            mcp = FastMCP("test")
            register_search_tools(mcp)

            get_contents = mcp._tool_manager._tools["get_repository_contents"].fn

            result = await get_contents(path="", repository="test-repo")
            data = json.loads(result)

            assert data["type"] == "directory"
            assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_repository_contents_no_repo(self, mock_env_vars, mock_bitbucket_client):
        """Test getting contents when no repository specified."""
        with patch("bitbucket_mcp.tools.search.get_client", return_value=mock_bitbucket_client):
            with patch("bitbucket_mcp.tools.search.get_current_repo", return_value=None):
                from mcp.server.fastmcp import FastMCP

                from bitbucket_mcp.tools.search import register_search_tools

                mcp = FastMCP("test")
                register_search_tools(mcp)

                get_contents = mcp._tool_manager._tools["get_repository_contents"].fn

                result = await get_contents(path="")
                data = json.loads(result)

                assert "error" in data

    @pytest.mark.asyncio
    async def test_search_code(self, mock_env_vars, mock_bitbucket_client):
        """Test searching for code."""
        mock_bitbucket_client.search_code.return_value = [
            {
                "file": {"path": "src/main.py"},
                "content_matches": ["def main():"],
                "path_matches": [],
            }
        ]

        with patch("bitbucket_mcp.tools.search.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.search import register_search_tools

            mcp = FastMCP("test")
            register_search_tools(mcp)

            search_code = mcp._tool_manager._tools["search_code"].fn

            result = await search_code(query="def main", repository="test-repo")
            data = json.loads(result)

            assert data["query"] == "def main"
            assert data["count"] == 1
            assert data["results"][0]["file"] == "src/main.py"

    @pytest.mark.asyncio
    async def test_get_file_content(self, mock_env_vars, mock_bitbucket_client):
        """Test getting file content."""
        # Mock the cloud._session.get for file content
        mock_response = type(
            "Response",
            (),
            {"text": "print('Hello, World!')", "raise_for_status": lambda self: None},
        )()
        mock_bitbucket_client.cloud = type(
            "Cloud",
            (),
            {"_session": type("Session", (), {"get": lambda self, url: mock_response})()},
        )()

        with patch("bitbucket_mcp.tools.search.get_client", return_value=mock_bitbucket_client):
            from mcp.server.fastmcp import FastMCP

            from bitbucket_mcp.tools.search import register_search_tools

            mcp = FastMCP("test")
            register_search_tools(mcp)

            get_file = mcp._tool_manager._tools["get_file_content"].fn

            result = await get_file(file_path="main.py", repository="test-repo")

            assert "Hello, World!" in result
