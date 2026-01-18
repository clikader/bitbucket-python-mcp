# BitBucket MCP Server

A Model Context Protocol (MCP) server for BitBucket Cloud operations. This server enables AI coding agents like Claude Code CLI and Codex CLI to interact with BitBucket repositories, branches, and pull requests.

## Features

- **Repository Management**: Create, delete, update, and list repositories
- **Branch Management**: Create, delete, and list branches
- **Pull Request Operations**: Create, review, approve, comment on pull requests
- **Code Search**: Search repositories and browse file contents
- **Memory System**: Store and retrieve workspace standards and learnings from PR reviews
- **Auto-detection**: Automatically detects current BitBucket repository from git remote

## Installation

### Using uvx (Recommended)

```bash
uvx bitbucket-python-mcp
```

### Using pip

```bash
pip install bitbucket-python-mcp
```

### From Source

```bash
git clone https://github.com/yourusername/bitbucket-python-mcp.git
cd bitbucket-python-mcp
uv sync
```

## Configuration

The server requires the following environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `BITBUCKET_USERNAME` | Yes | Your BitBucket username (not email) |
| `BITBUCKET_API_TOKEN` | Yes | App password/API token from BitBucket settings |
| `BITBUCKET_WORKSPACE` | Yes | Default workspace slug |
| `BITBUCKET_MCP_DEBUG` | No | Enable debug logging (1/true/yes) |

### Creating an App Password

1. Go to [BitBucket App Passwords](https://bitbucket.org/account/settings/app-passwords/)
2. Click "Create app password"
3. Give it a descriptive name (e.g., "MCP Server")
4. Select the required permissions:
   - Repositories: Read, Write, Admin (for create/delete)
   - Pull requests: Read, Write
5. Click "Create" and copy the generated password

## Usage with AI Agents

### Claude Code CLI

Add to your `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "uvx",
      "args": ["bitbucket-python-mcp"],
      "env": {
        "BITBUCKET_USERNAME": "your-username",
        "BITBUCKET_API_TOKEN": "your-api-token",
        "BITBUCKET_WORKSPACE": "your-workspace"
      }
    }
  }
}
```

### OpenAI Codex CLI

Add to your `~/.codex/config.toml`:

```toml
[mcp_servers.bitbucket]
command = "uvx"
args = ["bitbucket-python-mcp"]

[mcp_servers.bitbucket.env]
BITBUCKET_USERNAME = "your-username"
BITBUCKET_API_TOKEN = "your-api-token"
BITBUCKET_WORKSPACE = "your-workspace"
```

Alternatively, use the Codex CLI to add the server:

```bash
codex mcp add bitbucket \
  --env BITBUCKET_USERNAME=your-username \
  --env BITBUCKET_API_TOKEN=your-api-token \
  --env BITBUCKET_WORKSPACE=your-workspace \
  -- uvx bitbucket-python-mcp
```

Verify the server is configured:

```bash
codex mcp list
```

### Running Locally

```bash
# Set environment variables
export BITBUCKET_USERNAME="your-username"
export BITBUCKET_API_TOKEN="your-api-token"
export BITBUCKET_WORKSPACE="your-workspace"

# Run the server
uvx bitbucket-python-mcp
# or
uv run bitbucket-python-mcp
```

## Available Tools

### Repository Tools

| Tool | Description |
|------|-------------|
| `list_repositories` | List all repositories in a workspace |
| `get_repository` | Get detailed repository information |
| `create_repository` | Create a new repository |
| `delete_repository` | Delete a repository (requires confirmation) |
| `update_repository` | Update repository settings |

### Branch Tools

| Tool | Description |
|------|-------------|
| `list_branches` | List all branches in a repository |
| `get_branch` | Get branch details |
| `create_branch` | Create a new branch |
| `delete_branch` | Delete a branch (requires confirmation) |

### Pull Request Tools

| Tool | Description |
|------|-------------|
| `list_pull_requests` | List pull requests (open/merged/declined) |
| `get_pull_request` | Get PR details (defaults to newest) |
| `get_pull_request_diff` | Get the diff for a PR |
| `get_pull_request_comments` | Get all comments on a PR |
| `add_pull_request_comment` | Add a comment (general or inline) |
| `approve_pull_request` | Approve a PR |
| `request_changes` | Request changes on a PR |
| `create_pull_request` | Create a new PR |

### Search Tools

| Tool | Description |
|------|-------------|
| `search_repositories` | Search for repositories by name |
| `get_repository_contents` | Browse repository files/directories |
| `search_code` | Search for code patterns |
| `get_file_content` | Get raw file content |

### Memory Tools

| Tool | Description |
|------|-------------|
| `add_memory` | Store a new learning/standard for future reference |
| `list_memories` | List stored memories filtered by workspace/category |
| `search_memories` | Search memories by keyword |
| `get_relevant_memories` | Get memories relevant to current context |
| `delete_memory` | Delete a stored memory |
| `remember_from_pr_comment` | Extract and store learning from a PR comment |

Memories are stored in `~/.bitbucket-python-mcp/memory/` and persist across sessions.

## Examples

### Create a Repository

```
User: Create a new private repository named "my-new-project" with description "My awesome project"
```

### Create a Branch

```
User: Create a new branch named "feature-login" from development
```

### Review a Pull Request

```
User: Show me the details of the newest pull request
User: What are the comments on PR #42?
User: Approve PR #42
```

### Search Code

```
User: Search for "authentication" in the project-api repository
User: Show me the contents of src/main.py
```

### Store and Retrieve Memories

```
User: Remember that we should use shared-pipeline for SonarQube scans
User: What standards should I follow for this workspace?
User: Search memories for "pipeline"
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/bitbucket-python-mcp.git
cd bitbucket-python-mcp

# Install dependencies
uv sync --all-extras

# or using just
just install-dev
```

### Running Tests

```bash
uv run pytest

# or using just
just test
```

### Linting

```bash
uv run ruff check src tests
uv run ruff format src tests

# or using just
just fmt
just lint
```

### Building

```bash
uv build

# or using just
just build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) - The protocol specification
- [atlassian-python-api](https://github.com/atlassian-api/atlassian-python-api) - BitBucket API client
