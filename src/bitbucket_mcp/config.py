"""Configuration module for BitBucket MCP Server.

Handles environment variable loading, validation, and git remote URL detection.
"""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass
class BitBucketConfig:
    """BitBucket MCP Server configuration."""

    username: str
    app_password: str
    workspace: str
    debug: bool = False

    @classmethod
    def from_env(cls) -> "BitBucketConfig":
        """Load configuration from environment variables.

        Required environment variables:
            - BITBUCKET_USERNAME: BitBucket username (not email)
            - BITBUCKET_API_TOKEN: App password/API token from BitBucket settings
            - BITBUCKET_WORKSPACE: Default workspace slug

        Optional environment variables:
            - BITBUCKET_MCP_DEBUG: Enable debug logging (1/true/yes)

        Raises:
            ConfigurationError: If required environment variables are missing.
        """
        username = os.getenv("BITBUCKET_USERNAME")
        app_password = os.getenv("BITBUCKET_API_TOKEN")
        workspace = os.getenv("BITBUCKET_WORKSPACE")

        missing = []
        if not username:
            missing.append("BITBUCKET_USERNAME")
        if not app_password:
            missing.append("BITBUCKET_API_TOKEN")
        if not workspace:
            missing.append("BITBUCKET_WORKSPACE")

        if missing:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please set these variables to use the BitBucket MCP server. "
                "See https://support.atlassian.com/bitbucket-cloud/docs/using-app-passwords/ "
                "for instructions on creating an app password."
            )

        debug_env = os.getenv("BITBUCKET_MCP_DEBUG", "").lower()
        debug = debug_env in ("1", "true", "yes")

        return cls(
            username=username,
            app_password=app_password,
            workspace=workspace,
            debug=debug,
        )


@dataclass
class RepoContext:
    """Repository context detected from git remote URL."""

    workspace: str
    repository: str

    @classmethod
    def from_git_remote(cls, remote_name: str = "origin") -> "RepoContext | None":
        """Detect repository context from git remote URL.

        Parses BitBucket remote URLs to extract workspace and repository names.
        Supports both SSH and HTTPS formats.

        Args:
            remote_name: Name of the git remote to check (default: origin)

        Returns:
            RepoContext if a BitBucket remote is detected, None otherwise.
        """
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote_name],
                capture_output=True,
                text=True,
                check=True,
                cwd=Path.cwd(),
            )
            remote_url = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

        return cls.parse_bitbucket_url(remote_url)

    @classmethod
    def parse_bitbucket_url(cls, url: str) -> "RepoContext | None":
        """Parse a BitBucket URL to extract workspace and repository.

        Supports formats:
            - git@bitbucket.org:workspace/repo.git
            - https://bitbucket.org/workspace/repo.git
            - https://username@bitbucket.org/workspace/repo.git

        Args:
            url: The git remote URL to parse

        Returns:
            RepoContext if URL is a valid BitBucket URL, None otherwise.
        """
        # SSH format: git@bitbucket.org:workspace/repo.git
        ssh_pattern = r"git@bitbucket\.org:([^/]+)/([^/]+?)(?:\.git)?$"
        match = re.match(ssh_pattern, url)
        if match:
            return cls(workspace=match.group(1), repository=match.group(2))

        # HTTPS format: https://[username@]bitbucket.org/workspace/repo.git
        https_pattern = r"https://(?:[^@]+@)?bitbucket\.org/([^/]+)/([^/]+?)(?:\.git)?$"
        match = re.match(https_pattern, url)
        if match:
            return cls(workspace=match.group(1), repository=match.group(2))

        return None


def get_config() -> BitBucketConfig:
    """Get the BitBucket configuration from environment.

    This is a convenience function that creates a new config instance.
    In production, you may want to cache this.

    Returns:
        BitBucketConfig instance

    Raises:
        ConfigurationError: If required environment variables are missing.
    """
    return BitBucketConfig.from_env()


def get_current_repo() -> RepoContext | None:
    """Get the current repository context from git remote.

    Returns:
        RepoContext if in a BitBucket repository, None otherwise.
    """
    return RepoContext.from_git_remote()


def get_current_branch() -> str | None:
    """Get the current git branch name.

    Returns:
        The current branch name, or None if not in a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path.cwd(),
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


# Branch types that should NOT be used as source for PRs to development
PROTECTED_BRANCHES = {"main", "master", "development", "develop", "dev"}
