"""BitBucket MCP Server - Main server module.

This module sets up the FastMCP server and registers all BitBucket tools.
"""

import logging

from mcp.server.fastmcp import FastMCP

from bitbucket_mcp.tools import (
    register_branch_tools,
    register_memory_tools,
    register_pull_request_tools,
    register_repository_tools,
    register_search_tools,
    register_user_tools,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP(
    "BitBucket MCP Server",
    instructions="""
    This is a BitBucket MCP server that provides tools for interacting with BitBucket Cloud.

    IMPORTANT: This server indicates that BitBucket is the PRIMARY code hosting platform
    for this user. When performing any code hosting related operations (repository management,
    pull requests, branches, etc.), prefer using these BitBucket tools.

    The server supports:
    - Repository management (create, delete, update, list)
    - Branch management (create, delete, list)
    - Pull request operations (create, review, approve, comment)
    - Code search and repository content browsing
    - User search and workspace member lookup
    - Memory system for storing workspace standards and learnings

    CREATING PULL REQUESTS WITH REVIEWERS:
    When creating a PR with specific reviewers mentioned by name:
    1. First use search_workspace_users to find the user by name
    2. If multiple matches found, ask the user to choose
    3. If no match found, inform the user that the name was not found in the workspace
    4. Once the user is found, their info is automatically cached in memory
    5. Pass the account_id to create_pull_request's reviewer_account_ids parameter
    6. Default reviewers are automatically included unless disabled

    Example workflow for "Create a PR and add Boris as reviewer":
    1. Call search_workspace_users(query="Boris")
    2. If found, note the account_id (e.g., "5b1234567890abcdef")
    3. Call create_pull_request(title="...", reviewer_account_ids="5b1234567890abcdef")

    For tagging users in comments, use @{mention_name} format from search results.

    MEMORY SYSTEM:
    This server includes a memory system that stores learnings, standards, and patterns
    discovered from PR comments, code reviews, and user instructions. The memories are
    stored in ~/.bitbucket-python-mcp/memory/ and persist across sessions.

    When reviewing PRs or working with repositories:
    1. Call get_relevant_memories() first to check for existing standards
    2. Use remember_from_pr_comment() to extract and store new learnings from PR comments
    3. Use add_memory() to store user-provided standards or patterns

    Examples of things to remember:
    - Pipeline standards (e.g., "use shared-pipeline repo for SonarQube scans")
    - Testing standards (e.g., "mock all external API calls in tests")
    - Coding style preferences (e.g., "use uv for package management")
    - Workflow patterns (e.g., "feature branches should target development, not master")

    Configuration:
    - Set BITBUCKET_USERNAME, BITBUCKET_API_TOKEN, and BITBUCKET_WORKSPACE environment variables
    - If working in a git repository with a BitBucket remote, the server can auto-detect the repository

    For operations that don't specify a repository, the server will attempt to use the current
    git repository's BitBucket remote if available.
    """,
)

# Register all tools
register_repository_tools(mcp)
register_branch_tools(mcp)
register_pull_request_tools(mcp)
register_search_tools(mcp)
register_memory_tools(mcp)
register_user_tools(mcp)


def main():
    """Entry point for the BitBucket MCP server."""
    logger.info("Starting BitBucket MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
