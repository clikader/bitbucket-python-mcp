"""Pull request tools for BitBucket MCP Server."""

import json

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.client import get_client
from bitbucket_mcp.config import PROTECTED_BRANCHES, get_current_branch, get_current_repo


def register_pull_request_tools(mcp: FastMCP) -> None:
    """Register pull request tools with the MCP server."""

    @mcp.tool()
    async def list_pull_requests(
        repository: str | None = None,
        workspace: str | None = None,
        state: str = "OPEN",
        limit: int = 10,
    ) -> str:
        """List pull requests in a BitBucket repository.

        Use this tool to see pull requests in a repository. By default, shows
        only open pull requests.

        Args:
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.
            state: Filter by state - 'OPEN', 'MERGED', 'DECLINED', or 'SUPERSEDED'.
                   Default is 'OPEN'.
            limit: Maximum number of pull requests to return. Default 10.

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

        prs = await client.list_pull_requests(repository, workspace, state, limit)

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
        source_branch: str | None = None,
        destination_branch: str | None = None,
        description: str = "",
        repository: str | None = None,
        workspace: str | None = None,
        reviewer_account_ids: str | None = None,
        include_default_reviewers: bool = True,
        close_source_branch: bool = False,
    ) -> str:
        """Create a new pull request.

        Use this tool to create a pull request for merging changes from one branch
        to another. Supports auto-detection of source branch and smart destination
        selection.

        Workflow for adding reviewers:
        1. First use search_workspace_users to find users by name
        2. Pass the account_id(s) from the search results to reviewer_account_ids
        3. Default reviewers are automatically included unless disabled

        Args:
            title: Title of the pull request.
            source_branch: Branch containing the changes. If not provided, uses the
                current git branch. Cannot be main/master/development.
            destination_branch: Branch to merge into. If not provided, defaults to
                'development' for feature/bugfix branches.
            description: Optional description of the changes.
            repository: Repository slug. If not provided, uses current repository context.
            workspace: Workspace slug. If not provided, uses the default workspace.
            reviewer_account_ids: Comma-separated list of reviewer account_ids to add
                as additional reviewers (use search_workspace_users to find these).
            include_default_reviewers: If True (default), includes repository's default
                reviewers in addition to any specified reviewers.
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
                        "message": "Please provide a repository name, or run this command "
                        "from within a git repository with a BitBucket remote.",
                    },
                    indent=2,
                )

        # Auto-detect source branch if not provided
        if source_branch is None:
            source_branch = get_current_branch()
            if source_branch is None:
                return json.dumps(
                    {
                        "error": "Cannot detect source branch",
                        "message": "Please provide a source_branch parameter or run this "
                        "command from within a git repository.",
                    },
                    indent=2,
                )

        # Validate source branch is not a protected branch
        if source_branch.lower() in PROTECTED_BRANCHES:
            return json.dumps(
                {
                    "error": "Invalid source branch",
                    "message": f"Cannot create PR from protected branch '{source_branch}'. "
                    f"Protected branches are: {', '.join(sorted(PROTECTED_BRANCHES))}",
                },
                indent=2,
            )

        # Auto-select destination branch if not provided
        if destination_branch is None:
            destination_branch = "development"

        # Collect reviewers
        reviewers: list[dict[str, str]] = []

        # Add default reviewers if requested
        if include_default_reviewers:
            try:
                default_reviewers = await client.get_default_reviewers(repository, workspace)
                for reviewer in default_reviewers:
                    account_id = reviewer.get("account_id")
                    if account_id:
                        reviewers.append({"account_id": account_id})
            except Exception:
                # Default reviewers might not be configured, continue without them
                pass

        # Add additional specified reviewers
        if reviewer_account_ids:
            for account_id in reviewer_account_ids.split(","):
                account_id = account_id.strip()
                # Avoid duplicates
                if account_id and not any(r.get("account_id") == account_id for r in reviewers):
                    reviewers.append({"account_id": account_id})

        pr = await client.create_pull_request(
            repository=repository,
            source_branch=source_branch,
            destination_branch=destination_branch,
            title=title,
            workspace=workspace,
            description=description,
            reviewers=reviewers if reviewers else None,
            close_source_branch=close_source_branch,
        )

        # Format reviewer info for response
        pr_reviewers = [
            {
                "display_name": r.get("display_name", ""),
                "account_id": r.get("account_id", ""),
            }
            for r in pr.get("reviewers", [])
        ]

        return json.dumps(
            {
                "message": "Pull request created successfully",
                "id": pr.get("id"),
                "title": pr.get("title"),
                "source_branch": pr.get("source", {}).get("branch", {}).get("name", ""),
                "destination_branch": pr.get("destination", {}).get("branch", {}).get("name", ""),
                "reviewers": pr_reviewers,
                "url": pr.get("links", {}).get("html", {}).get("href", ""),
            },
            indent=2,
        )
