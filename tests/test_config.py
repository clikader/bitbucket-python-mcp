"""Tests for the configuration module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from bitbucket_mcp.config import (
    BitBucketConfig,
    ConfigurationError,
    RepoContext,
    get_config,
    get_current_repo,
)


class TestBitBucketConfig:
    """Tests for BitBucketConfig class."""

    def test_from_env_success(self, mock_env_vars):
        """Test successful configuration loading from environment."""
        config = BitBucketConfig.from_env()

        assert config.username == "test-user"
        assert config.app_password == "test-password"
        assert config.workspace == "test-workspace"
        assert config.debug is False

    def test_from_env_with_debug(self, mock_env_vars, monkeypatch):
        """Test debug mode enabled via environment variable."""
        monkeypatch.setenv("BITBUCKET_MCP_DEBUG", "1")
        config = BitBucketConfig.from_env()

        assert config.debug is True

    def test_from_env_missing_username(self, monkeypatch):
        """Test error when username is missing."""
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-password")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-workspace")
        monkeypatch.delenv("BITBUCKET_USERNAME", raising=False)

        with pytest.raises(ConfigurationError) as exc_info:
            BitBucketConfig.from_env()

        assert "BITBUCKET_USERNAME" in str(exc_info.value)

    def test_from_env_missing_all(self, monkeypatch):
        """Test error when all required variables are missing."""
        monkeypatch.delenv("BITBUCKET_USERNAME", raising=False)
        monkeypatch.delenv("BITBUCKET_API_TOKEN", raising=False)
        monkeypatch.delenv("BITBUCKET_WORKSPACE", raising=False)

        with pytest.raises(ConfigurationError) as exc_info:
            BitBucketConfig.from_env()

        error_msg = str(exc_info.value)
        assert "BITBUCKET_USERNAME" in error_msg
        assert "BITBUCKET_API_TOKEN" in error_msg
        assert "BITBUCKET_WORKSPACE" in error_msg


class TestRepoContext:
    """Tests for RepoContext class."""

    def test_parse_ssh_url(self):
        """Test parsing SSH git URL."""
        url = "git@bitbucket.org:my-workspace/my-repo.git"
        context = RepoContext.parse_bitbucket_url(url)

        assert context is not None
        assert context.workspace == "my-workspace"
        assert context.repository == "my-repo"

    def test_parse_ssh_url_without_git_extension(self):
        """Test parsing SSH URL without .git extension."""
        url = "git@bitbucket.org:my-workspace/my-repo"
        context = RepoContext.parse_bitbucket_url(url)

        assert context is not None
        assert context.workspace == "my-workspace"
        assert context.repository == "my-repo"

    def test_parse_https_url(self):
        """Test parsing HTTPS git URL."""
        url = "https://bitbucket.org/my-workspace/my-repo.git"
        context = RepoContext.parse_bitbucket_url(url)

        assert context is not None
        assert context.workspace == "my-workspace"
        assert context.repository == "my-repo"

    def test_parse_https_url_with_username(self):
        """Test parsing HTTPS URL with username."""
        url = "https://username@bitbucket.org/my-workspace/my-repo.git"
        context = RepoContext.parse_bitbucket_url(url)

        assert context is not None
        assert context.workspace == "my-workspace"
        assert context.repository == "my-repo"

    def test_parse_non_bitbucket_url(self):
        """Test that non-BitBucket URLs return None."""
        url = "git@github.com:my-org/my-repo.git"
        context = RepoContext.parse_bitbucket_url(url)

        assert context is None

    def test_parse_invalid_url(self):
        """Test that invalid URLs return None."""
        url = "not-a-valid-url"
        context = RepoContext.parse_bitbucket_url(url)

        assert context is None

    @patch("subprocess.run")
    def test_from_git_remote_success(self, mock_run):
        """Test successful git remote detection."""
        mock_run.return_value = MagicMock(
            stdout="git@bitbucket.org:test-workspace/test-repo.git\n",
            returncode=0,
        )

        context = RepoContext.from_git_remote()

        assert context is not None
        assert context.workspace == "test-workspace"
        assert context.repository == "test-repo"

    @patch("subprocess.run")
    def test_from_git_remote_not_a_repo(self, mock_run):
        """Test when not in a git repository."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        context = RepoContext.from_git_remote()

        assert context is None

    @patch("subprocess.run")
    def test_from_git_remote_no_git(self, mock_run):
        """Test when git is not installed."""
        mock_run.side_effect = FileNotFoundError()

        context = RepoContext.from_git_remote()

        assert context is None


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_config(self, mock_env_vars):
        """Test get_config helper function."""
        config = get_config()

        assert config.username == "test-user"
        assert config.workspace == "test-workspace"

    @patch("subprocess.run")
    def test_get_current_repo(self, mock_run):
        """Test get_current_repo helper function."""
        mock_run.return_value = MagicMock(
            stdout="git@bitbucket.org:workspace/repo.git\n",
            returncode=0,
        )

        context = get_current_repo()

        assert context is not None
        assert context.workspace == "workspace"
        assert context.repository == "repo"
