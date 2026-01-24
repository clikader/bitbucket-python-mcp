"""User tools for BitBucket MCP Server.

Provides tools for searching workspace users and caching user info in memory.
"""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.client import get_client
from bitbucket_mcp.config import get_current_branch, get_current_repo
from bitbucket_mcp.memory import get_memory_manager

# Memory category for storing user information
USER_MEMORY_CATEGORY = "workflow"
USER_MEMORY_TAG = "workspace_user"


def _format_user(user: dict[str, Any]) -> dict[str, Any]:
    """Format user data for output."""
    return {
        "account_id": user.get("account_id", ""),
        "uuid": user.get("uuid", ""),
        "display_name": user.get("display_name", ""),
        "nickname": user.get("nickname", ""),
        "mention_name": user.get("nickname") or user.get("account_id", ""),
    }


def _get_cached_user(name: str, workspace: str | None = None) -> dict[str, Any] | None:
    """Check memory for a cached user matching the given name.

    Args:
        name: User name to search for.
        workspace: Workspace to filter by.

    Returns:
        Cached user dict if found, None otherwise.
    """
    manager = get_memory_manager()
    memories = manager.search_memories(name, workspace=workspace)

    for memory in memories:
        if USER_MEMORY_TAG in memory.tags:
            # Parse the stored user JSON from the memory content
            try:
                # Memory content format: "User: {display_name} | {json_data}"
                if "|" in memory.content:
                    json_part = memory.content.split("|", 1)[1].strip()
                    return json.loads(json_part)
            except (json.JSONDecodeError, IndexError):
                continue
    return None


def _cache_user(user: dict[str, Any], workspace: str | None = None) -> None:
    """Store user info in memory for future lookups.

    Args:
        user: User data to cache.
        workspace: Workspace this user belongs to.
    """
    manager = get_memory_manager()
    display_name = user.get("display_name", "")
    nickname = user.get("nickname", "")

    # Create searchable content with JSON data embedded
    content = f"User: {display_name} | {json.dumps(user)}"

    # Create tags including name parts for better searchability
    tags = [USER_MEMORY_TAG]
    if display_name:
        tags.extend([part.lower() for part in display_name.split()])
    if nickname:
        tags.append(nickname.lower())

    manager.add_memory(
        content=content,
        category=USER_MEMORY_CATEGORY,
        tags=tags,
        source_type="api_response",
        workspace=workspace,
    )


def register_user_tools(mcp: FastMCP) -> None:
    """Register user-related tools with the MCP server."""

    @mcp.tool()
    async def get_current_user() -> str:
        """Get the authenticated user's account information including email addresses.

        Use this tool to get information about the currently authenticated BitBucket
        user, including their email addresses. This is useful for:
        - Verifying which account is being used
        - Getting the user's email addresses
        - Getting the user's account_id for self-assignment

        Returns:
            JSON object with the authenticated user's details and email addresses.
        """
        client = get_client()

        try:
            user = await client.get_current_user()
            emails = await client.get_current_user_emails()

            # Format emails
            email_list = []
            for email in emails:
                email_list.append(
                    {
                        "email": email.get("email"),
                        "is_primary": email.get("is_primary", False),
                        "is_confirmed": email.get("is_confirmed", False),
                    }
                )

            return json.dumps(
                {
                    "status": "success",
                    "user": {
                        "display_name": user.get("display_name"),
                        "account_id": user.get("account_id"),
                        "uuid": user.get("uuid"),
                        "nickname": user.get("nickname"),
                        "username": user.get("username"),
                    },
                    "emails": email_list,
                },
                indent=2,
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Failed to get current user: {e!s}",
                },
                indent=2,
            )

    @mcp.tool()
    async def get_current_git_branch() -> str:
        """Get the current git branch name.

        Use this tool to detect what branch you're currently on before creating
        a pull request. This is useful for auto-detecting the source branch.

        Returns:
            JSON object with the current branch name, or error if not in a git repository.
        """
        branch = get_current_branch()

        if branch:
            return json.dumps(
                {
                    "status": "success",
                    "branch": branch,
                },
                indent=2,
            )
        else:
            return json.dumps(
                {
                    "status": "error",
                    "message": "Not in a git repository or unable to detect current branch.",
                },
                indent=2,
            )

    @mcp.tool()
    async def search_workspace_users(
        query: str,
        workspace: str | None = None,
        check_memory_first: bool = True,
    ) -> str:
        """Search for users in a BitBucket workspace by name.

        Use this tool to find users by their name or nickname. It first checks
        the memory cache for previously found users, then searches BitBucket
        if needed. Found users are automatically cached for future lookups.

        This is useful when:
        - Adding reviewers to a pull request
        - Mentioning users in comments (@username)
        - Finding user account IDs for API operations

        Args:
            query: User name or nickname to search for (partial match supported).
            workspace: Workspace slug. If not provided, uses the default workspace.
            check_memory_first: If True, checks memory cache before searching BitBucket.

        Returns:
            JSON object with matching users. If multiple matches found, returns all
            so the caller can ask the user to choose.
        """
        client = get_client()
        resolved_workspace = workspace or client.default_workspace

        # Check memory cache first
        if check_memory_first:
            cached = _get_cached_user(query, resolved_workspace)
            if cached:
                return json.dumps(
                    {
                        "status": "success",
                        "source": "memory_cache",
                        "message": f"Found cached user matching '{query}'",
                        "users": [_format_user(cached)],
                        "count": 1,
                    },
                    indent=2,
                )

        # Search BitBucket workspace members
        try:
            users = await client.search_workspace_users(query, workspace)
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Failed to search workspace users: {e!s}",
                },
                indent=2,
            )

        if not users:
            return json.dumps(
                {
                    "status": "not_found",
                    "message": f"No users found matching '{query}' in workspace '{resolved_workspace}'.",
                    "query": query,
                    "workspace": resolved_workspace,
                },
                indent=2,
            )

        # Cache found users for future lookups
        for user in users:
            _cache_user(user, resolved_workspace)

        if len(users) == 1:
            return json.dumps(
                {
                    "status": "success",
                    "source": "bitbucket_api",
                    "message": f"Found user matching '{query}'",
                    "users": [_format_user(u) for u in users],
                    "count": 1,
                },
                indent=2,
            )

        # Multiple users found - caller should ask user to choose
        return json.dumps(
            {
                "status": "multiple_matches",
                "message": f"Found {len(users)} users matching '{query}'. Please specify which one.",
                "users": [_format_user(u) for u in users],
                "count": len(users),
            },
            indent=2,
        )

    @mcp.tool()
    async def list_workspace_members(workspace: str | None = None) -> str:
        """List all members in a BitBucket workspace.

        Use this tool to see all users who have access to a workspace.
        Useful for finding reviewers or understanding team membership.

        Args:
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON list of all workspace members with their details.
        """
        client = get_client()

        try:
            members = await client.list_workspace_members(workspace)
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Failed to list workspace members: {e!s}",
                },
                indent=2,
            )

        users = []
        for member in members:
            user = member.get("user", {})
            users.append(
                {
                    "account_id": user.get("account_id", ""),
                    "uuid": user.get("uuid", ""),
                    "display_name": user.get("display_name", ""),
                    "nickname": user.get("nickname", ""),
                }
            )

        return json.dumps(
            {
                "status": "success",
                "workspace": workspace or client.default_workspace,
                "members": users,
                "count": len(users),
            },
            indent=2,
        )

    @mcp.tool()
    async def get_default_reviewers(
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Get default reviewers configured for a repository.

        Use this tool to see which users are automatically added as reviewers
        when creating pull requests. These reviewers will be included unless
        explicitly excluded.

        Args:
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON list of default reviewers with their details.
        """
        client = get_client()

        # Resolve repository from context if not provided
        if repository is None:
            repo_context = get_current_repo()
            if repo_context:
                repository = repo_context.repository
                if workspace is None:
                    workspace = repo_context.workspace
            else:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "No repository specified and not in a BitBucket repository.",
                    },
                    indent=2,
                )

        try:
            reviewers = await client.get_default_reviewers(repository, workspace)
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Failed to get default reviewers: {e!s}",
                },
                indent=2,
            )

        formatted = []
        for reviewer in reviewers:
            formatted.append(
                {
                    "account_id": reviewer.get("account_id", ""),
                    "uuid": reviewer.get("uuid", ""),
                    "display_name": reviewer.get("display_name", ""),
                    "nickname": reviewer.get("nickname", ""),
                }
            )

        return json.dumps(
            {
                "status": "success",
                "repository": repository,
                "default_reviewers": formatted,
                "count": len(formatted),
            },
            indent=2,
        )
