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

    async def list_repositories(
        self, workspace: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List repositories in a workspace.

        Args:
            workspace: Workspace slug.
            limit: Maximum number of repositories to return. Default 50.
        """
        ws = self.resolve_workspace(workspace)

        def _list():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}"
            pagelen = min(limit, 50)
            params = {"pagelen": pagelen}
            repos = []
            while url and len(repos) < limit:
                response = self.cloud._session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                repos.extend(data.get("values", []))
                url = data.get("next")
                params = None
            return repos[:limit]

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
        self, repository: str, workspace: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List branches in a repository.

        Args:
            repository: Repository slug.
            workspace: Workspace slug.
            limit: Maximum number of branches to return. Default 50.
        """
        ws = self.resolve_workspace(workspace)

        def _list():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/refs/branches"
            pagelen = min(limit, 50)
            params = {"pagelen": pagelen}
            branches = []
            while url and len(branches) < limit:
                response = self.cloud._session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                branches.extend(data.get("values", []))
                url = data.get("next")
                params = None
            return branches[:limit]

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
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List pull requests in a repository.

        Args:
            repository: Repository slug.
            workspace: Workspace slug.
            state: Filter by state - 'OPEN', 'MERGED', 'DECLINED', or 'SUPERSEDED'.
            limit: Maximum number of pull requests to return. Default 10.
        """
        ws = self.resolve_workspace(workspace)

        def _list():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/pullrequests"
            # Use pagelen to fetch efficiently, capped at 50 per BitBucket API limit
            pagelen = min(limit, 50)
            params = {"state": state, "pagelen": pagelen}
            prs = []
            while url and len(prs) < limit:
                response = self.cloud._session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                prs.extend(data.get("values", []))
                url = data.get("next")
                params = None  # Next URL includes params
            return prs[:limit]  # Ensure we don't exceed limit

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
        reviewers: list[dict[str, str]] | None = None,
        close_source_branch: bool = False,
    ) -> dict[str, Any]:
        """Create a new pull request.

        Args:
            repository: Repository slug.
            source_branch: Branch containing the changes to merge.
            destination_branch: Branch to merge into.
            title: Title of the pull request.
            workspace: Workspace slug. If None, uses default workspace.
            description: Optional description of the changes.
            reviewers: List of reviewer dicts with 'account_id' or 'uuid' key.
            close_source_branch: Whether to close the source branch after merge.

        Returns:
            The created pull request data.
        """
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
                # BitBucket API accepts reviewers with account_id or uuid
                pr_data["reviewers"] = reviewers

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
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search for code in a repository.

        Args:
            repository: Repository slug.
            query: Search query string.
            workspace: Workspace slug.
            limit: Maximum number of results to return. Default 20.
        """
        ws = self.resolve_workspace(workspace)

        def _search():
            # BitBucket's code search API
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/search/code"
            pagelen = min(limit, 50)
            params = {"search_query": query, "pagelen": pagelen}
            results = []
            while url and len(results) < limit:
                response = self.cloud._session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                results.extend(data.get("values", []))
                url = data.get("next")
                params = None
            return results[:limit]

        return await asyncio.to_thread(_search)

    # User operations

    async def get_current_user(self) -> dict[str, Any]:
        """Get the authenticated user's account information.

        Returns:
            User account details including display_name, account_id, uuid.
        """

        def _get():
            url = "https://api.bitbucket.org/2.0/user"
            response = self.cloud._session.get(url)
            response.raise_for_status()
            return response.json()

        return await asyncio.to_thread(_get)

    async def get_current_user_emails(self) -> list[dict[str, Any]]:
        """Get the authenticated user's email addresses.

        Returns:
            List of email addresses with is_primary and is_confirmed flags.
        """

        def _get():
            url = "https://api.bitbucket.org/2.0/user/emails"
            emails = []
            while url:
                response = self.cloud._session.get(url)
                response.raise_for_status()
                data = response.json()
                emails.extend(data.get("values", []))
                url = data.get("next")
            return emails

        return await asyncio.to_thread(_get)

    # Workspace member operations

    async def list_workspace_members(self, workspace: str | None = None) -> list[dict[str, Any]]:
        """List all members in a workspace.

        First tries the workspace members API (requires admin). Falls back to
        aggregating users from repository default reviewers and PR participants.

        Args:
            workspace: Workspace slug. If None, uses default workspace.

        Returns:
            List of workspace members with their details.
        """
        ws = self.resolve_workspace(workspace)

        # Try workspace members API first (requires admin permissions)
        def _list_members():
            url = f"https://api.bitbucket.org/2.0/workspaces/{ws}/members"
            members = []
            while url:
                response = self.cloud._session.get(url)
                response.raise_for_status()
                data = response.json()
                members.extend(data.get("values", []))
                url = data.get("next")
            return members

        try:
            return await asyncio.to_thread(_list_members)
        except Exception:
            # Fallback: aggregate users from repos if members API fails
            return await self._aggregate_workspace_users(ws)

    async def _aggregate_workspace_users(self, workspace: str) -> list[dict[str, Any]]:
        """Aggregate users from default reviewers and PR participants.

        This is a fallback when workspace members API is not accessible.
        """
        all_users: dict[str, dict[str, Any]] = {}

        # Get repositories
        repos = await self.list_repositories(workspace)

        for repo in repos[:15]:  # Limit to first 15 repos for performance
            repo_slug = repo.get("slug")
            if not repo_slug:
                continue

            # Get default reviewers
            try:
                reviewers = await self.get_default_reviewers(repo_slug, workspace)
                for r in reviewers:
                    aid = r.get("account_id")
                    if aid and aid not in all_users:
                        all_users[aid] = {"user": r}
            except Exception:
                pass

            # Get PR participants (check both open and recent merged)
            for state in ["OPEN", "MERGED"]:
                try:
                    prs = await self.list_pull_requests(repo_slug, workspace, state)
                    for pr in prs[:10]:  # Limit PRs per repo
                        # Check participants
                        for p in pr.get("participants", []):
                            user = p.get("user", {})
                            aid = user.get("account_id")
                            if aid and aid not in all_users:
                                all_users[aid] = {"user": user}

                        # Check author
                        author = pr.get("author", {})
                        aid = author.get("account_id")
                        if aid and aid not in all_users:
                            all_users[aid] = {"user": author}

                        # Check reviewers
                        for r in pr.get("reviewers", []):
                            aid = r.get("account_id")
                            if aid and aid not in all_users:
                                all_users[aid] = {"user": r}
                except Exception:
                    pass

        return list(all_users.values())

    async def search_workspace_users(
        self,
        query: str,
        workspace: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search for users in a workspace by name or email.

        Args:
            query: Search query (name or email substring).
            workspace: Workspace slug. If None, uses default workspace.

        Returns:
            List of matching users.
        """
        members = await self.list_workspace_members(workspace)
        query_lower = query.lower()

        results = []
        for member in members:
            user = member.get("user", {})
            display_name = user.get("display_name", "").lower()
            nickname = user.get("nickname", "").lower()
            account_id = user.get("account_id", "")

            # Check if query matches display name, nickname, or account_id
            if query_lower in display_name or query_lower in nickname or query_lower == account_id:
                results.append(
                    {
                        "account_id": account_id,
                        "uuid": user.get("uuid", ""),
                        "display_name": user.get("display_name", ""),
                        "nickname": user.get("nickname", ""),
                        "type": user.get("type", ""),
                        "links": user.get("links", {}),
                    }
                )

        return results

    async def get_default_reviewers(
        self, repository: str, workspace: str | None = None
    ) -> list[dict[str, Any]]:
        """Get default reviewers for a repository.

        Args:
            repository: Repository slug.
            workspace: Workspace slug. If None, uses default workspace.

        Returns:
            List of default reviewers with their details.
        """
        ws = self.resolve_workspace(workspace)

        def _get():
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/default-reviewers"
            reviewers = []
            while url:
                response = self.cloud._session.get(url)
                response.raise_for_status()
                data = response.json()
                reviewers.extend(data.get("values", []))
                url = data.get("next")
            return reviewers

        return await asyncio.to_thread(_get)

    async def get_file_content(
        self,
        repository: str,
        file_path: str,
        ref: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Get raw file content from a repository.

        Args:
            repository: Repository slug.
            file_path: Path to the file.
            ref: Branch, tag, or commit hash (default: HEAD).
            workspace: Workspace slug. If None, uses default workspace.

        Returns:
            The raw file content as a string.
        """
        ws = self.resolve_workspace(workspace)

        def _get():
            commit_ref = ref or "HEAD"
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/src/{commit_ref}/{file_path}"
            response = self.cloud._session.get(url)
            response.raise_for_status()
            return response.text

        return await asyncio.to_thread(_get)


# Global client instance (lazy initialization)
_client: BitBucketClient | None = None


def get_client() -> BitBucketClient:
    """Get the global BitBucket client instance."""
    global _client
    if _client is None:
        _client = BitBucketClient()
    return _client
