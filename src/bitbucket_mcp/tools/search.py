"""Search and content tools for BitBucket MCP Server."""

import json

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.client import get_client
from bitbucket_mcp.config import get_current_repo


def register_search_tools(mcp: FastMCP) -> None:
    """Register search and content tools with the MCP server."""

    @mcp.tool()
    async def search_repositories(
        query: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Search for repositories in a BitBucket workspace.

        Use this tool to find repositories by name or other criteria. Searches
        within the specified workspace and returns matching repositories.

        Args:
            query: Search query to filter repositories by name. If not provided,
                   lists all repositories.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON list of matching repositories.
        """
        client = get_client()
        repos = await client.list_repositories(workspace)

        # Filter by query if provided
        if query:
            query_lower = query.lower()
            repos = [
                r
                for r in repos
                if query_lower in r.get("name", "").lower()
                or query_lower in r.get("description", "").lower()
                or query_lower in r.get("slug", "").lower()
            ]

        result = []
        for repo in repos:
            result.append(
                {
                    "name": repo.get("name"),
                    "slug": repo.get("slug"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description", ""),
                    "is_private": repo.get("is_private"),
                    "language": repo.get("language", ""),
                    "url": repo.get("links", {}).get("html", {}).get("href", ""),
                }
            )

        if not result:
            return json.dumps(
                {
                    "message": f"No repositories found matching '{query}'"
                    if query
                    else "No repositories found in workspace",
                    "results": [],
                },
                indent=2,
            )

        return json.dumps(
            {
                "count": len(result),
                "results": result,
            },
            indent=2,
        )

    @mcp.tool()
    async def get_repository_contents(
        path: str = "",
        repository: str | None = None,
        workspace: str | None = None,
        ref: str | None = None,
    ) -> str:
        """Get file or directory contents from a BitBucket repository.

        Use this tool to browse repository contents, view file structure, or
        read file contents. Can navigate to specific paths and refs (branches/tags).

        Args:
            path: Path to file or directory (empty string for root).
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.
            ref: Branch, tag, or commit hash (default: HEAD).

        Returns:
            JSON object with directory listing or file contents.
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

        contents = await client.get_repository_contents(repository, path, ref, workspace)

        # Check if it's a directory listing or file content
        if "values" in contents:
            # Directory listing
            items = []
            for item in contents.get("values", []):
                items.append(
                    {
                        "path": item.get("path"),
                        "type": item.get("type"),  # "commit_directory" or "commit_file"
                        "size": item.get("size"),
                    }
                )
            return json.dumps(
                {
                    "type": "directory",
                    "path": path or "/",
                    "items": items,
                },
                indent=2,
            )
        else:
            # File content - return as string
            return json.dumps(
                {
                    "type": "file",
                    "path": path,
                    "content": contents,
                },
                indent=2,
            )

    @mcp.tool()
    async def search_code(
        query: str,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Search for code patterns in a BitBucket repository.

        Use this tool to find specific code patterns, function names, or text
        within a repository's codebase.

        Args:
            query: Search query for code content.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON list of matching code locations with snippets.
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

        try:
            results = await client.search_code(repository, query, workspace)

            formatted = []
            for result in results:
                formatted.append(
                    {
                        "file": result.get("file", {}).get("path", ""),
                        "content_matches": result.get("content_matches", []),
                        "path_matches": result.get("path_matches", []),
                    }
                )

            return json.dumps(
                {
                    "query": query,
                    "count": len(formatted),
                    "results": formatted,
                },
                indent=2,
            )
        except Exception as e:
            # Code search might not be available for all repositories
            return json.dumps(
                {
                    "error": "Code search failed",
                    "message": str(e),
                    "suggestion": "Code search may not be available for this repository. "
                    "Try using get_repository_contents to browse files instead.",
                },
                indent=2,
            )

    @mcp.tool()
    async def get_file_content(
        file_path: str,
        repository: str | None = None,
        workspace: str | None = None,
        ref: str | None = None,
    ) -> str:
        """Get the raw content of a specific file from a BitBucket repository.

        Use this tool when you need to read the full content of a specific file.
        This is useful for reviewing code, configuration files, or documentation.

        Args:
            file_path: Path to the file in the repository.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.
            ref: Branch, tag, or commit hash (default: HEAD).

        Returns:
            The raw file content as a string.
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

        ws = client.resolve_workspace(workspace)

        # Construct the raw file URL
        import asyncio

        def _get_file():
            ref_part = ref if ref else "HEAD"
            url = f"https://api.bitbucket.org/2.0/repositories/{ws}/{repository}/src/{ref_part}/{file_path}"
            response = client.cloud._session.get(url)
            response.raise_for_status()
            return response.text

        try:
            content = await asyncio.to_thread(_get_file)
            return content
        except Exception as e:
            return json.dumps(
                {
                    "error": "Failed to get file content",
                    "message": str(e),
                    "file_path": file_path,
                },
                indent=2,
            )
