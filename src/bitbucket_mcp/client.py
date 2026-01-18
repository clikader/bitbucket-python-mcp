"""BitBucket client wrapper for async operations.

Wraps the synchronous atlassian-python-api with asyncio.to_thread for
async compatibility in the MCP server.
"""

import asyncio
import logging
from functools import wraps
from typing import Any

from atlassian.bitbucket import Cloud

from bitbucket_mcp.config import BitBucketConfig, get_config, get_current_repo

logger = logging.getLogger(__name__)


class BitBucketClientError(Exception):
    """Raised when BitBucket API operations fail."""


def async_wrap(func):
    """Decorator to wrap a synchronous function for async execution."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


class BitBucketClient:
    """Async-friendly wrapper around the BitBucket Cloud API."""

    def __init__(self, config: BitBucketConfig | None = None):
        """Initialize the BitBucket client.

        Args:
            config: BitBucket configuration. If None, loads from environment.
        """
        self._config = config or get_config()
        self._cloud: Cloud | None = None

    @property
    def cloud(self) -> Cloud:
        """Get the BitBucket Cloud client instance (lazy initialization)."""
        if self._cloud is None:
            self._cloud = Cloud(
                url="https://api.bitbucket.org/",
                username=self._config.username,
                password=self._config.app_password,
            )
        return self._cloud

    @property
    def default_workspace(self) -> str:
        """Get the default workspace from configuration."""
        return self._config.workspace

    def resolve_workspace(self, workspace: str | None) -> str:
        """Resolve workspace, using default if not provided."""
        return workspace or self.default_workspace

    def resolve_repository(self, repository: str | None) -> str | None:
        """Resolve repository, detecting from git remote if not provided."""
        if repository:
            return repository
        repo_context = get_current_repo()
        return repo_context.repository if repo_context else None

    # Workspace operations

    async def get_workspace(self, workspace: str | None = None) -> dict[str, Any]:
        """Get workspace details."""
        ws = self.resolve_workspace(workspace)
        return await asyncio.to_thread(lambda: self.cloud.workspaces.get(ws).data)

    async def list_workspaces(self) -> list[dict[str, Any]]:
        """List all accessible workspaces."""
        return await asyncio.to_thread(lambda: [w.data for w in self.cloud.workspaces.each()])

    # Repository operations

    async def list_repositories(self, workspace: str | None = None) -> list[dict[str, Any]]:
        """List all repositories in a workspace."""
        ws = self.resolve_workspace(workspace)

        def _list():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}"
            repos = []
            while url:
                response = self.cloud._session.get(url)
                response.raise_for_status()
                data = response.json()
                repos.extend(data.get("values", []))
                url = data.get("next")
            return repos

        return await asyncio.to_thread(_list)

    async def get_repository(self, repository: str, workspace: str | None = None) -> dict[str, Any]:
        """Get repository details."""
        ws = self.resolve_workspace(workspace)

        def _get():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}"
            response = self.cloud._session.get(url)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_get)

    async def create_repository(
        self,
        name: str,
        workspace: str | None = None,
        project_key: str | None = None,
        description: str = "",
        is_private: bool = True,
        fork_policy: str = "allow_forks",
    ) -> dict[str, Any]:
        """Create a new repository."""
        ws = self.resolve_workspace(workspace)

        def _create():
            repo_data = {
                "scm": "git",
                "name": name,
                "is_private": is_private,
                "description": description,
                "fork_policy": fork_policy,
            }
            if project_key:
                repo_data["project"] = {"key": project_key}

            # Use the REST API directly for creation
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{name}"
            response = self.cloud._session.post(url, json=repo_data)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_create)

    async def delete_repository(self, repository: str, workspace: str | None = None) -> bool:
        """Delete a repository."""
        ws = self.resolve_workspace(workspace)

        def _delete():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}"
            response = self.cloud._session.delete(url)
            response.raise_for_status()
            return True

        return await asyncio.to_thread(_delete)

    async def update_repository(
        self,
        repository: str,
        workspace: str | None = None,
        description: str | None = None,
        is_private: bool | None = None,
    ) -> dict[str, Any]:
        """Update repository settings."""
        ws = self.resolve_workspace(workspace)

        def _update():
            update_data = {}
            if description is not None:
                update_data["description"] = description
            if is_private is not None:
                update_data["is_private"] = is_private

            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}"
            response = self.cloud._session.put(url, json=update_data)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_update)

    # Branch operations

    async def list_branches(
        self, repository: str, workspace: str | None = None
    ) -> list[dict[str, Any]]:
        """List all branches in a repository."""
        ws = self.resolve_workspace(workspace)

        def _list():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/refs/branches"
            branches = []
            while url:
                response = self.cloud._session.get(url)
                response.raise_for_status()
                data = response.json()
                branches.extend(data.get("values", []))
                url = data.get("next")
            return branches

        return await asyncio.to_thread(_list)

    async def get_branch(
        self, repository: str, branch_name: str, workspace: str | None = None
    ) -> dict[str, Any]:
        """Get branch details."""
        ws = self.resolve_workspace(workspace)

        def _get():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/refs/branches/{branch_name}"
            response = self.cloud._session.get(url)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_get)

    async def create_branch(
        self,
        repository: str,
        branch_name: str,
        source_branch: str = "development",
        workspace: str | None = None,
    ) -> dict[str, Any]:
        """Create a new branch from a source branch."""
        ws = self.resolve_workspace(workspace)

        def _create():
            # First get the source branch to find its commit hash
            source_url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/refs/branches/{source_branch}"
            response = self.cloud._session.get(source_url)
            response.raise_for_status()
            source_data = response.json()
            target_hash = source_data["target"]["hash"]

            # Create the new branch
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/refs/branches"
            branch_data = {"name": branch_name, "target": {"hash": target_hash}}
            response = self.cloud._session.post(url, json=branch_data)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_create)

    async def delete_branch(
        self, repository: str, branch_name: str, workspace: str | None = None
    ) -> bool:
        """Delete a branch."""
        ws = self.resolve_workspace(workspace)

        def _delete():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/refs/branches/{branch_name}"
            response = self.cloud._session.delete(url)
            response.raise_for_status()
            return True

        return await asyncio.to_thread(_delete)

    # Pull Request operations

    async def list_pull_requests(
        self,
        repository: str,
        workspace: str | None = None,
        state: str = "OPEN",
    ) -> list[dict[str, Any]]:
        """List pull requests in a repository."""
        ws = self.resolve_workspace(workspace)

        def _list():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests"
            params = {"state": state}
            prs = []
            while url:
                response = self.cloud._session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                prs.extend(data.get("values", []))
                url = data.get("next")
                params = None  # Next URL includes params
            return prs

        return await asyncio.to_thread(_list)

    async def get_pull_request(
        self, repository: str, pr_id: int, workspace: str | None = None
    ) -> dict[str, Any]:
        """Get pull request details."""
        ws = self.resolve_workspace(workspace)

        def _get():
            url = (
                f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests/{pr_id}"
            )
            response = self.cloud._session.get(url)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_get)

    async def get_pull_request_diff(
        self, repository: str, pr_id: int, workspace: str | None = None
    ) -> str:
        """Get pull request diff."""
        ws = self.resolve_workspace(workspace)

        def _get():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests/{pr_id}/diff"
            response = self.cloud._session.get(url)
            response.raise_for_status()
            return response.text

        return await asyncio.to_thread(_get)

    async def get_pull_request_comments(
        self, repository: str, pr_id: int, workspace: str | None = None
    ) -> list[dict[str, Any]]:
        """Get pull request comments."""
        ws = self.resolve_workspace(workspace)

        def _list():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests/{pr_id}/comments"
            comments = []
            while url:
                response = self.cloud._session.get(url)
                response.raise_for_status()
                data = response.json()
                comments.extend(data.get("values", []))
                url = data.get("next")
            return comments

        return await asyncio.to_thread(_list)

    async def add_pull_request_comment(
        self,
        repository: str,
        pr_id: int,
        comment: str,
        workspace: str | None = None,
        inline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a comment to a pull request."""
        ws = self.resolve_workspace(workspace)

        def _add():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests/{pr_id}/comments"
            comment_data: dict[str, Any] = {"content": {"raw": comment}}
            if inline:
                comment_data["inline"] = inline
            response = self.cloud._session.post(url, json=comment_data)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_add)

    async def approve_pull_request(
        self, repository: str, pr_id: int, workspace: str | None = None
    ) -> dict[str, Any]:
        """Approve a pull request."""
        ws = self.resolve_workspace(workspace)

        def _approve():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests/{pr_id}/approve"
            response = self.cloud._session.post(url)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_approve)

    async def request_changes(
        self, repository: str, pr_id: int, workspace: str | None = None
    ) -> dict[str, Any]:
        """Request changes on a pull request."""
        ws = self.resolve_workspace(workspace)

        def _request():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests/{pr_id}/request-changes"
            response = self.cloud._session.post(url)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_request)

    async def create_pull_request(
        self,
        repository: str,
        source_branch: str,
        destination_branch: str,
        title: str,
        workspace: str | None = None,
        description: str = "",
        reviewers: list[str] | None = None,
        close_source_branch: bool = False,
    ) -> dict[str, Any]:
        """Create a new pull request."""
        ws = self.resolve_workspace(workspace)

        def _create():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests"
            pr_data: dict[str, Any] = {
                "title": title,
                "description": description,
                "source": {"branch": {"name": source_branch}},
                "destination": {"branch": {"name": destination_branch}},
                "close_source_branch": close_source_branch,
            }
            if reviewers:
                pr_data["reviewers"] = [{"username": r} for r in reviewers]

            response = self.cloud._session.post(url, json=pr_data)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_create)

    # Search and content operations

    async def get_repository_contents(
        self,
        repository: str,
        path: str = "",
        ref: str | None = None,
        workspace: str | None = None,
    ) -> dict[str, Any]:
        """Get file or directory contents from a repository."""
        ws = self.resolve_workspace(workspace)

        def _get():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/src"
            if ref:
                url = f"{url}/{ref}/{path}"
            elif path:
                url = f"{url}/HEAD/{path}"
            else:
                url = f"{url}/HEAD/"

            response = self.cloud._session.get(url)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_get)

    async def search_code(
        self,
        repository: str,
        query: str,
        workspace: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for code in a repository."""
        ws = self.resolve_workspace(workspace)

        def _search():
            # BitBucket's code search API
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/search/code"
            params = {"search_query": query}
            results = []
            while url:
                response = self.cloud._session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                results.extend(data.get("values", []))
                url = data.get("next")
                params = None
            return results

        return await asyncio.to_thread(_search)


# Global client instance (lazy initialization)
_client: BitBucketClient | None = None


def get_client() -> BitBucketClient:
    """Get the global BitBucket client instance."""
    global _client
    if _client is None:
        _client = BitBucketClient()
    return _client
