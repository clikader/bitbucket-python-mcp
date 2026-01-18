"""Branch management tools for BitBucket MCP Server."""

import json

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.client import get_client
from bitbucket_mcp.config import get_current_repo


def register_branch_tools(mcp: FastMCP) -> None:
    """Register branch management tools with the MCP server."""

    @mcp.tool()
    async def list_branches(
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """List all branches in a BitBucket repository.

        Use this tool to see all available branches in a repository, including
        their names and latest commit information.

        Args:
            repository: Repository slug. If not provided and working in a git repo
                       with a BitBucket remote, will use the current repository.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON list of branches with their names and target commit info.
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
                        "error": "No repository specified",
                        "message": "Please provide a repository name, or run this command "
                        "from within a git repository with a BitBucket remote.",
                    },
                    indent=2,
                )

        branches = await client.list_branches(repository, workspace)

        result = []
        for branch in branches:
            target = branch.get("target", {})
            result.append(
                {
                    "name": branch.get("name"),
                    "commit_hash": target.get("hash", "")[:12],
                    "commit_message": target.get("message", "").split("\n")[0][:80],
                    "author": target.get("author", {}).get("user", {}).get("display_name", ""),
                    "date": target.get("date"),
                }
            )

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def get_branch(
        branch_name: str,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Get detailed information about a specific branch.

        Use this tool when you need complete details about a branch, including
        its latest commit information.

        Args:
            branch_name: Name of the branch to get details for.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object with branch details including commit information.
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
                        "error": "No repository specified",
                        "message": "Please provide a repository name.",
                    },
                    indent=2,
                )

        branch = await client.get_branch(repository, branch_name, workspace)
        target = branch.get("target", {})

        return json.dumps(
            {
                "name": branch.get("name"),
                "commit": {
                    "hash": target.get("hash"),
                    "message": target.get("message", ""),
                    "author": {
                        "name": target.get("author", {}).get("user", {}).get("display_name", ""),
                        "email": target.get("author", {}).get("raw", ""),
                    },
                    "date": target.get("date"),
                },
                "links": {
                    "html": branch.get("links", {}).get("html", {}).get("href", ""),
                    "commits": branch.get("links", {}).get("commits", {}).get("href", ""),
                },
            },
            indent=2,
        )

    @mcp.tool()
    async def create_branch(
        branch_name: str,
        source_branch: str = "development",
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Create a new branch in a BitBucket repository.

        Use this tool when the user wants to create a new branch. By default,
        branches are created from the 'development' branch.

        Args:
            branch_name: Name for the new branch.
            source_branch: Source branch to create from (default: 'development').
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object with the created branch details.
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
                        "error": "No repository specified",
                        "message": "Please provide a repository name.",
                    },
                    indent=2,
                )

        branch = await client.create_branch(
            repository=repository,
            branch_name=branch_name,
            source_branch=source_branch,
            workspace=workspace,
        )

        return json.dumps(
            {
                "message": f"Branch '{branch_name}' created successfully from '{source_branch}'",
                "name": branch.get("name"),
                "commit_hash": branch.get("target", {}).get("hash", "")[:12],
                "url": branch.get("links", {}).get("html", {}).get("href", ""),
            },
            indent=2,
        )

    @mcp.tool()
    async def delete_branch(
        branch_name: str,
        confirm: bool,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Delete a branch from a BitBucket repository.

        WARNING: This is a destructive operation. The confirm parameter MUST be
        set to true to proceed with deletion.

        Use this tool only when the user explicitly requests to delete a branch
        and has confirmed the deletion.

        Args:
            branch_name: Name of the branch to delete.
            confirm: Must be True to proceed with deletion. This is a safety measure.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            Confirmation message or error if confirm is not True.
        """
        if not confirm:
            return json.dumps(
                {
                    "error": "Deletion not confirmed",
                    "message": f"To delete branch '{branch_name}', you must set confirm=true. "
                    "This action cannot be undone.",
                },
                indent=2,
            )

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
                        "error": "No repository specified",
                        "message": "Please provide a repository name.",
                    },
                    indent=2,
                )

        await client.delete_branch(repository, branch_name, workspace)

        return json.dumps(
            {
                "message": f"Branch '{branch_name}' has been deleted successfully",
                "warning": "This action cannot be undone",
            },
            indent=2,
        )
