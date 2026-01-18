"""Repository management tools for BitBucket MCP Server."""

import json

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.client import get_client


def register_repository_tools(mcp: FastMCP) -> None:
    """Register repository management tools with the MCP server."""

    @mcp.tool()
    async def list_repositories(workspace: str | None = None) -> str:
        """List all repositories in a BitBucket workspace.

        This is the primary tool for discovering repositories. Use this when the user
        wants to see what repositories are available or when searching for a specific
        repository by browsing.

        Args:
            workspace: Workspace slug. If not provided, uses the default workspace
                      from BITBUCKET_WORKSPACE environment variable.

        Returns:
            JSON list of repositories with their names, descriptions, and URLs.
        """
        client = get_client()
        repos = await client.list_repositories(workspace)

        # Format the response with key information
        result = []
        for repo in repos:
            result.append(
                {
                    "name": repo.get("name"),
                    "slug": repo.get("slug"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description", ""),
                    "is_private": repo.get("is_private"),
                    "url": repo.get("links", {}).get("html", {}).get("href", ""),
                }
            )

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def get_repository(repository: str, workspace: str | None = None) -> str:
        """Get detailed information about a specific BitBucket repository.

        Use this tool when you need full details about a repository, including
        its settings, clone URLs, and metadata.

        Args:
            repository: Repository slug (the URL-friendly name of the repository).
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object with complete repository details.
        """
        client = get_client()
        repo = await client.get_repository(repository, workspace)

        return json.dumps(
            {
                "name": repo.get("name"),
                "slug": repo.get("slug"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description", ""),
                "is_private": repo.get("is_private"),
                "language": repo.get("language", ""),
                "created_on": repo.get("created_on"),
                "updated_on": repo.get("updated_on"),
                "size": repo.get("size"),
                "mainbranch": repo.get("mainbranch", {}).get("name"),
                "clone_urls": {
                    "https": next(
                        (
                            link["href"]
                            for link in repo.get("links", {}).get("clone", [])
                            if link.get("name") == "https"
                        ),
                        None,
                    ),
                    "ssh": next(
                        (
                            link["href"]
                            for link in repo.get("links", {}).get("clone", [])
                            if link.get("name") == "ssh"
                        ),
                        None,
                    ),
                },
                "url": repo.get("links", {}).get("html", {}).get("href", ""),
            },
            indent=2,
        )

    @mcp.tool()
    async def create_repository(
        name: str,
        description: str = "",
        is_private: bool = True,
        project_key: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Create a new repository in BitBucket.

        Use this tool when the user wants to create a new repository. The repository
        will be created in the specified workspace with the given settings.

        Args:
            name: Name of the new repository. Will also be used as the slug.
            description: Optional description of the repository.
            is_private: Whether the repository should be private (default: True).
            project_key: Optional project key to associate the repository with a project.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object with the created repository details.
        """
        client = get_client()
        repo = await client.create_repository(
            name=name,
            workspace=workspace,
            project_key=project_key,
            description=description,
            is_private=is_private,
        )

        return json.dumps(
            {
                "message": f"Repository '{name}' created successfully",
                "name": repo.get("name"),
                "slug": repo.get("slug"),
                "full_name": repo.get("full_name"),
                "url": repo.get("links", {}).get("html", {}).get("href", ""),
                "clone_urls": {
                    "https": next(
                        (
                            link["href"]
                            for link in repo.get("links", {}).get("clone", [])
                            if link.get("name") == "https"
                        ),
                        None,
                    ),
                    "ssh": next(
                        (
                            link["href"]
                            for link in repo.get("links", {}).get("clone", [])
                            if link.get("name") == "ssh"
                        ),
                        None,
                    ),
                },
            },
            indent=2,
        )

    @mcp.tool()
    async def delete_repository(
        repository: str,
        confirm: bool,
        workspace: str | None = None,
    ) -> str:
        """Delete a repository from BitBucket.

        WARNING: This is a destructive operation that cannot be undone.
        The confirm parameter MUST be set to true to proceed with deletion.

        Use this tool only when the user explicitly requests to delete a repository
        and has confirmed the deletion.

        Args:
            repository: Repository slug to delete.
            confirm: Must be True to proceed with deletion. This is a safety measure.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            Confirmation message or error if confirm is not True.
        """
        if not confirm:
            return json.dumps(
                {
                    "error": "Deletion not confirmed",
                    "message": "To delete this repository, you must set confirm=true. "
                    "This action cannot be undone.",
                },
                indent=2,
            )

        client = get_client()
        await client.delete_repository(repository, workspace)

        return json.dumps(
            {
                "message": f"Repository '{repository}' has been deleted successfully",
                "warning": "This action cannot be undone",
            },
            indent=2,
        )

    @mcp.tool()
    async def update_repository(
        repository: str,
        description: str | None = None,
        is_private: bool | None = None,
        workspace: str | None = None,
    ) -> str:
        """Update repository settings in BitBucket.

        Use this tool to modify repository metadata such as description or visibility.
        Only provide the parameters you want to change.

        Args:
            repository: Repository slug to update.
            description: New description for the repository.
            is_private: Whether the repository should be private.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object with the updated repository details.
        """
        if description is None and is_private is None:
            return json.dumps(
                {
                    "error": "No changes specified",
                    "message": "Please provide at least one parameter to update "
                    "(description or is_private)",
                },
                indent=2,
            )

        client = get_client()
        repo = await client.update_repository(
            repository=repository,
            workspace=workspace,
            description=description,
            is_private=is_private,
        )

        return json.dumps(
            {
                "message": f"Repository '{repository}' updated successfully",
                "name": repo.get("name"),
                "slug": repo.get("slug"),
                "description": repo.get("description", ""),
                "is_private": repo.get("is_private"),
                "url": repo.get("links", {}).get("html", {}).get("href", ""),
            },
            indent=2,
        )
