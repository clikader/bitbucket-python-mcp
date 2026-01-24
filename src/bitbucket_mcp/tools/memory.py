"""Memory tools for the BitBucket MCP server.

These tools allow AI agents to store and retrieve learnings, standards,
and patterns discovered from PR reviews and user input.
"""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.client import get_client
from bitbucket_mcp.memory import Memory, get_memory_manager


def _format_memory(memory: Memory) -> dict[str, Any]:
    """Format a memory for tool output."""
    return {
        "id": memory.id,
        "content": memory.content,
        "category": memory.category,
        "tags": memory.tags,
        "scope": {
            "workspace": memory.workspace or "all",
            "repository": memory.repository or "all",
        },
        "source": memory.source.to_dict(),
        "created_at": memory.created_at,
    }


def register_memory_tools(mcp: FastMCP) -> None:
    """Register memory management tools with the MCP server."""

    @mcp.tool()
    async def add_memory(
        content: str,
        category: str = "general",
        tags: str | None = None,
        workspace: str | None = None,
        repository: str | None = None,
        source_type: str = "user",
        pr_id: int | None = None,
    ) -> str:
        """Store a new memory/learning for future reference.

        Use this tool to remember important standards, patterns, or learnings
        discovered from PR comments, code reviews, or user instructions.
        These memories will be available when reviewing other PRs or repositories.

        Common use cases:
        - Workspace coding standards (e.g., "use uv for package management")
        - Pipeline requirements (e.g., "use shared-pipeline for SonarQube scans")
        - Testing standards (e.g., "mock all external API calls in tests")
        - Code style preferences (e.g., "use type hints for all function parameters")

        Args:
            content: The learning/standard to remember (be specific and actionable)
            category: Category - one of: pipeline, testing, coding_style, tools, workflow, general
            tags: Comma-separated tags for easier searching (e.g., "sonarqube,pipeline,ci")
            workspace: Workspace this applies to (omit for global/all workspaces)
            repository: Repository this applies to (omit for all repos in workspace)
            source_type: Source of this memory - user, pr_comment, or api_response
            pr_id: If from a PR comment, the PR ID

        Returns:
            Confirmation with the created memory details
        """
        manager = get_memory_manager()
        client = get_client()

        # Use default workspace if not specified but we want workspace-specific
        resolved_workspace = workspace or client.default_workspace

        # Parse tags
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        memory = manager.add_memory(
            content=content,
            category=category,
            tags=tag_list,
            source_type=source_type,
            workspace=resolved_workspace if workspace else None,  # None = global
            repository=repository,
            pr_id=pr_id,
        )

        return json.dumps(
            {
                "status": "success",
                "message": "Memory stored successfully",
                "memory": _format_memory(memory),
            },
            indent=2,
            ensure_ascii=True,
        )

    @mcp.tool()
    async def list_memories(
        workspace: str | None = None,
        repository: str | None = None,
        category: str | None = None,
    ) -> str:
        """List stored memories/learnings.

        Retrieves all stored memories, optionally filtered by scope or category.
        Global memories (workspace=None) are always included when filtering by workspace.

        Args:
            workspace: Filter by workspace (includes global memories too)
            repository: Filter by repository
            category: Filter by category (pipeline, testing, coding_style, tools, workflow, general)

        Returns:
            JSON list of memories matching the filters
        """
        manager = get_memory_manager()
        client = get_client()

        # Use default workspace if not specified
        resolved_workspace = workspace or client.default_workspace

        memories = manager.list_memories(
            workspace=resolved_workspace,
            repository=repository,
            category=category,
        )

        if not memories:
            return json.dumps(
                {
                    "status": "success",
                    "message": "No memories found matching the criteria",
                    "memories": [],
                    "count": 0,
                },
                indent=2,
                ensure_ascii=True,
            )

        return json.dumps(
            {
                "status": "success",
                "memories": [_format_memory(m) for m in memories],
                "count": len(memories),
            },
            indent=2,
            ensure_ascii=True,
        )

    @mcp.tool()
    async def search_memories(
        query: str,
        workspace: str | None = None,
        repository: str | None = None,
    ) -> str:
        """Search memories by keyword.

        Searches memory content and tags for the given query.
        Use this before reviewing PRs or making suggestions to check
        for existing standards or learnings.

        Args:
            query: Search keyword (searches content and tags)
            workspace: Filter by workspace
            repository: Filter by repository

        Returns:
            JSON list of matching memories
        """
        manager = get_memory_manager()
        client = get_client()

        resolved_workspace = workspace or client.default_workspace

        memories = manager.search_memories(
            query=query,
            workspace=resolved_workspace,
            repository=repository,
        )

        if not memories:
            return json.dumps(
                {
                    "status": "success",
                    "message": f"No memories found matching '{query}'",
                    "memories": [],
                    "count": 0,
                },
                indent=2,
                ensure_ascii=True,
            )

        return json.dumps(
            {
                "status": "success",
                "query": query,
                "memories": [_format_memory(m) for m in memories],
                "count": len(memories),
            },
            indent=2,
            ensure_ascii=True,
        )

    @mcp.tool()
    async def get_relevant_memories(
        workspace: str | None = None,
        repository: str | None = None,
        categories: str | None = None,
    ) -> str:
        """Get all memories relevant to the current context.

        Call this tool at the start of a PR review or when working with
        a repository to retrieve all applicable standards and learnings.

        Args:
            workspace: Current workspace (uses default if not specified)
            repository: Current repository
            categories: Comma-separated categories to filter (e.g., "pipeline,testing")

        Returns:
            JSON list of relevant memories for the context
        """
        manager = get_memory_manager()
        client = get_client()

        resolved_workspace = workspace or client.default_workspace

        # Parse categories
        category_list = None
        if categories:
            category_list = [c.strip() for c in categories.split(",")]

        memories = manager.get_relevant_memories(
            workspace=resolved_workspace,
            repository=repository,
            categories=category_list,
        )

        if not memories:
            return json.dumps(
                {
                    "status": "success",
                    "message": "No relevant memories found for this context",
                    "context": {
                        "workspace": resolved_workspace,
                        "repository": repository,
                    },
                    "memories": [],
                    "count": 0,
                },
                indent=2,
                ensure_ascii=True,
            )

        # Group by category for easier reading
        by_category: dict[str, list[dict]] = {}
        for m in memories:
            cat = m.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(_format_memory(m))

        return json.dumps(
            {
                "status": "success",
                "context": {
                    "workspace": resolved_workspace,
                    "repository": repository,
                },
                "memories_by_category": by_category,
                "total_count": len(memories),
            },
            indent=2,
            ensure_ascii=True,
        )

    @mcp.tool()
    async def delete_memory(memory_id: str) -> str:
        """Delete a stored memory by ID.

        Args:
            memory_id: The ID of the memory to delete

        Returns:
            Confirmation of deletion
        """
        manager = get_memory_manager()

        success = manager.delete_memory(memory_id)

        if success:
            return json.dumps(
                {
                    "status": "success",
                    "message": f"Memory {memory_id} deleted successfully",
                },
                indent=2,
                ensure_ascii=True,
            )
        else:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Memory {memory_id} not found",
                },
                indent=2,
                ensure_ascii=True,
            )

    @mcp.tool()
    async def remember_from_pr_comment(
        repository: str,
        pr_id: int,
        comment_content: str,
        learning: str,
        category: str = "general",
        tags: str | None = None,
        workspace: str | None = None,
        apply_to_all_repos: bool = True,
    ) -> str:
        """Extract and store a learning from a PR comment.

        Use this when you identify a standard or pattern in a PR comment
        that should be remembered for future reference.

        Args:
            repository: Repository where the PR comment was found
            pr_id: PR ID where the comment was found
            comment_content: The original comment content (for reference)
            learning: The extracted learning/standard to remember
            category: Category - pipeline, testing, coding_style, tools, workflow, general
            tags: Comma-separated tags
            workspace: Workspace (uses default if not specified)
            apply_to_all_repos: If True, applies to all repos in workspace; if False, only this repo

        Returns:
            Confirmation with the created memory
        """
        manager = get_memory_manager()
        client = get_client()

        resolved_workspace = workspace or client.default_workspace
        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        memory = manager.add_memory(
            content=learning,
            category=category,
            tags=tag_list,
            source_type="pr_comment",
            workspace=resolved_workspace,
            repository=None if apply_to_all_repos else repository,
            pr_id=pr_id,
        )

        return json.dumps(
            {
                "status": "success",
                "message": "Learning extracted and stored from PR comment",
                "source_comment": (
                    comment_content[:200] + "..." if len(comment_content) > 200 else comment_content
                ),
                "memory": _format_memory(memory),
            },
            indent=2,
            ensure_ascii=True,
        )
