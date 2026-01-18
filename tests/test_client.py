"""Tests for the BitBucket client wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from bitbucket_mcp.client import BitBucketClient, get_client


class TestBitBucketClient:
    """Tests for BitBucketClient class."""

    @pytest.fixture
    def client(self, mock_env_vars):
        """Create a client instance for testing."""
        return BitBucketClient()

    def test_default_workspace(self, client):
        """Test default workspace property."""
        assert client.default_workspace == "test-workspace"

    def test_resolve_workspace_with_value(self, client):
        """Test workspace resolution with explicit value."""
        result = client.resolve_workspace("custom-workspace")
        assert result == "custom-workspace"

    def test_resolve_workspace_without_value(self, client):
        """Test workspace resolution falls back to default."""
        result = client.resolve_workspace(None)
        assert result == "test-workspace"

    @patch("bitbucket_mcp.client.get_current_repo")
    def test_resolve_repository_with_value(self, mock_get_repo, client):
        """Test repository resolution with explicit value."""
        result = client.resolve_repository("my-repo")
        assert result == "my-repo"
        mock_get_repo.assert_not_called()

    @patch("bitbucket_mcp.client.get_current_repo")
    def test_resolve_repository_from_context(self, mock_get_repo, client):
        """Test repository resolution from git context."""
        mock_context = MagicMock()
        mock_context.repository = "detected-repo"
        mock_get_repo.return_value = mock_context

        result = client.resolve_repository(None)
        assert result == "detected-repo"

    @patch("bitbucket_mcp.client.get_current_repo")
    def test_resolve_repository_no_context(self, mock_get_repo, client):
        """Test repository resolution when no context available."""
        mock_get_repo.return_value = None

        result = client.resolve_repository(None)
        assert result is None


class TestBitBucketClientAsync:
    """Tests for async methods of BitBucketClient."""

    @pytest.fixture
    def client_with_mock_cloud(self, mock_env_vars):
        """Create a client with mocked Cloud instance."""
        client = BitBucketClient()
        client._cloud = MagicMock()
        return client

    @pytest.mark.asyncio
    async def test_list_repositories(self, client_with_mock_cloud, sample_repository):
        """Test listing repositories using direct REST API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"values": [sample_repository], "next": None}
        mock_response.raise_for_status = MagicMock()
        client_with_mock_cloud._cloud._session.get.return_value = mock_response

        repos = await client_with_mock_cloud.list_repositories()

        assert len(repos) == 1
        assert repos[0]["name"] == "test-repo"
        client_with_mock_cloud._cloud._session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_repository(self, client_with_mock_cloud, sample_repository):
        """Test getting a single repository using direct REST API."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_repository
        mock_response.raise_for_status = MagicMock()
        client_with_mock_cloud._cloud._session.get.return_value = mock_response

        repo = await client_with_mock_cloud.get_repository("test-repo")

        assert repo["name"] == "test-repo"
        assert repo["slug"] == "test-repo"
        client_with_mock_cloud._cloud._session.get.assert_called_once()


class TestGetClient:
    """Tests for the get_client function."""

    def test_get_client_returns_same_instance(self, mock_env_vars):
        """Test that get_client returns the same instance (singleton)."""
        # Reset the global client
        import bitbucket_mcp.client as client_module

        client_module._client = None

        client1 = get_client()
        client2 = get_client()

        assert client1 is client2

        # Clean up
        client_module._client = None
