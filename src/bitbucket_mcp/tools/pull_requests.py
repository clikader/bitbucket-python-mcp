"""Pull request tools for BitBucket MCP Server."""

import json

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.client import get_client
from bitbucket_mcp.config import get_current_repo


def register_pull_request_tools(mcp: FastMCP) -> None:
    """Register pull request tools with the MCP server."""

    @mcp.tool()
    async def list_pull_requests(
        repository: str | None = None,
        workspace: str | None = None,
        state: str = "OPEN",
    ) -> str:
        """List pull requests in a BitBucket repository.

        Use this tool to see pull requests in a repository. By default, shows
        only open pull requests.

        Args:
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.
            state: Filter by state - 'OPEN', 'MERGED', 'DECLINED', or 'SUPERSEDED'.
                   Default is 'OPEN'.

        Returns:
            JSON list of pull requests with their titles, authors, and status.
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

        prs = await client.list_pull_requests(repository, workspace, state)

        result = []
        for pr in prs:
            result.append(
                {
                    "id": pr.get("id"),
                    "title": pr.get("title"),
                    "state": pr.get("state"),
                    "author": pr.get("author", {}).get("display_name", ""),
                    "source_branch": pr.get("source", {}).get("branch", {}).get("name", ""),
                    "destination_branch": pr.get("destination", {})
                    .get("branch", {})
                    .get("name", ""),
                    "created_on": pr.get("created_on"),
                    "updated_on": pr.get("updated_on"),
                    "url": pr.get("links", {}).get("html", {}).get("href", ""),
                }
            )

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def get_pull_request(
        pr_id: int | None = None,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Get detailed information about a specific pull request.

        Use this tool to get complete details about a pull request, including
        its description, reviewers, and approval status.

        Args:
            pr_id: Pull request ID. If not provided, returns the newest open PR.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object with complete pull request details.
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

        # If no PR ID, get the newest open PR
        if pr_id is None:
            prs = await client.list_pull_requests(repository, workspace, "OPEN")
            if not prs:
                return json.dumps(
                    {
                        "message": "No open pull requests found in this repository.",
                    },
                    indent=2,
                )
            pr_id = prs[0].get("id")

        pr = await client.get_pull_request(repository, pr_id, workspace)

        return json.dumps(
            {
                "id": pr.get("id"),
                "title": pr.get("title"),
                "description": pr.get("description", ""),
                "state": pr.get("state"),
                "author": {
                    "display_name": pr.get("author", {}).get("display_name", ""),
                    "username": pr.get("author", {}).get("username", ""),
                },
                "source": {
                    "branch": pr.get("source", {}).get("branch", {}).get("name", ""),
                    "repository": pr.get("source", {}).get("repository", {}).get("full_name", ""),
                },
                "destination": {
                    "branch": pr.get("destination", {}).get("branch", {}).get("name", ""),
                },
                "reviewers": [r.get("display_name", "") for r in pr.get("reviewers", [])],
                "participants": [
                    {
                        "name": p.get("user", {}).get("display_name", ""),
                        "role": p.get("role", ""),
                        "approved": p.get("approved", False),
                    }
                    for p in pr.get("participants", [])
                ],
                "created_on": pr.get("created_on"),
                "updated_on": pr.get("updated_on"),
                "close_source_branch": pr.get("close_source_branch"),
                "url": pr.get("links", {}).get("html", {}).get("href", ""),
            },
            indent=2,
        )

    @mcp.tool()
    async def get_pull_request_diff(
        pr_id: int,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Get the diff/changes for a pull request.

        Use this tool to see what code changes are included in a pull request.
        Returns the raw diff output.

        Args:
            pr_id: Pull request ID.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            The diff text showing all changes in the pull request.
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

        diff = await client.get_pull_request_diff(repository, pr_id, workspace)
        return diff

    @mcp.tool()
    async def get_pull_request_comments(
        pr_id: int,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Get all comments on a pull request.

        Use this tool to review comments, feedback, and discussions on a pull request.
        Includes both general comments and inline code review comments.

        Args:
            pr_id: Pull request ID.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON list of comments with their content, authors, and locations.
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

        comments = await client.get_pull_request_comments(repository, pr_id, workspace)

        result = []
        for comment in comments:
            inline = comment.get("inline")
            result.append(
                {
                    "id": comment.get("id"),
                    "content": comment.get("content", {}).get("raw", ""),
                    "author": comment.get("user", {}).get("display_name", ""),
                    "created_on": comment.get("created_on"),
                    "updated_on": comment.get("updated_on"),
                    "is_inline": inline is not None,
                    "inline_location": {
                        "path": inline.get("path") if inline else None,
                        "line": inline.get("to") if inline else None,
                    }
                    if inline
                    else None,
                }
            )

        return json.dumps(result, indent=2)

    @mcp.tool()
    async def add_pull_request_comment(
        pr_id: int,
        comment: str,
        repository: str | None = None,
        workspace: str | None = None,
        file_path: str | None = None,
        line_number: int | None = None,
    ) -> str:
        """Add a comment to a pull request.

        Use this tool to add feedback or discussion to a pull request. Can add
        general comments or inline comments on specific lines of code.

        Args:
            pr_id: Pull request ID.
            comment: The comment text to add.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.
            file_path: Path to file for inline comment (optional).
            line_number: Line number for inline comment (optional, requires file_path).

        Returns:
            JSON object confirming the comment was added.
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

        inline = None
        if file_path and line_number:
            inline = {"path": file_path, "to": line_number}

        result = await client.add_pull_request_comment(
            repository, pr_id, comment, workspace, inline
        )

        return json.dumps(
            {
                "message": "Comment added successfully",
                "comment_id": result.get("id"),
                "content": result.get("content", {}).get("raw", ""),
                "is_inline": inline is not None,
            },
            indent=2,
        )

    @mcp.tool()
    async def approve_pull_request(
        pr_id: int,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Approve a pull request.

        Use this tool to approve a pull request, indicating the changes are
        acceptable and ready to merge.

        Args:
            pr_id: Pull request ID to approve.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object confirming the approval.
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

        result = await client.approve_pull_request(repository, pr_id, workspace)

        return json.dumps(
            {
                "message": f"Pull request #{pr_id} approved successfully",
                "approved": result.get("approved", True),
                "user": result.get("user", {}).get("display_name", ""),
            },
            indent=2,
        )

    @mcp.tool()
    async def request_changes(
        pr_id: int,
        comment: str,
        repository: str | None = None,
        workspace: str | None = None,
    ) -> str:
        """Request changes on a pull request.

        Use this tool to indicate that changes are needed before the pull request
        can be approved. Always include a comment explaining what needs to change.

        Args:
            pr_id: Pull request ID.
            comment: Explanation of what changes are needed.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.

        Returns:
            JSON object confirming the change request.
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

        # First request changes
        result = await client.request_changes(repository, pr_id, workspace)

        # Then add the comment explaining why
        await client.add_pull_request_comment(repository, pr_id, comment, workspace)

        return json.dumps(
            {
                "message": f"Changes requested on pull request #{pr_id}",
                "comment_added": True,
                "user": result.get("user", {}).get("display_name", ""),
            },
            indent=2,
        )

    @mcp.tool()
    async def create_pull_request(
        title: str,
        source_branch: str,
        destination_branch: str = "development",
        description: str = "",
        repository: str | None = None,
        workspace: str | None = None,
        reviewers: str | None = None,
        close_source_branch: bool = False,
    ) -> str:
        """Create a new pull request.

        Use this tool to create a pull request for merging changes from one branch
        to another.

        Args:
            title: Title of the pull request.
            source_branch: Branch containing the changes to merge.
            destination_branch: Branch to merge into (default: 'development').
            description: Optional description of the changes.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.
            reviewers: Comma-separated list of reviewer usernames (optional).
            close_source_branch: Whether to close the source branch after merge.

        Returns:
            JSON object with the created pull request details.
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

        reviewer_list = None
        if reviewers:
            reviewer_list = [r.strip() for r in reviewers.split(",")]

        pr = await client.create_pull_request(
            repository=repository,
            source_branch=source_branch,
            destination_branch=destination_branch,
            title=title,
            workspace=workspace,
            description=description,
            reviewers=reviewer_list,
            close_source_branch=close_source_branch,
        )

        return json.dumps(
            {
                "message": "Pull request created successfully",
                "id": pr.get("id"),
                "title": pr.get("title"),
                "source_branch": pr.get("source", {}).get("branch", {}).get("name", ""),
                "destination_branch": pr.get("destination", {}).get("branch", {}).get("name", ""),
                "url": pr.get("links", {}).get("html", {}).get("href", ""),
            },
            indent=2,
        )
