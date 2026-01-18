# Installation Guide

This guide covers all the ways to install and configure the BitBucket MCP Server.

## Prerequisites

- Python 3.12 or higher
- A BitBucket Cloud account
- An app password with appropriate permissions

## Installation Methods

### Method 1: Using uvx (Recommended)

The simplest way to run the BitBucket MCP server is using `uvx`, which handles installation automatically:

```bash
uvx bitbucket-python-mcp
```

This will download and run the latest version from PyPI.

### Method 2: Using pip

Install the package globally or in a virtual environment:

```bash
pip install bitbucket-python-mcp
```

Then run:

```bash
bitbucket-python-mcp
```

### Method 3: Using uv

```bash
uv add bitbucket-python-mcp
uv run bitbucket-python-mcp
```

### Method 4: From Source

For development or to run the latest unreleased version:

```bash
# Clone the repository
git clone https://github.com/yourusername/bitbucket-python-mcp.git
cd bitbucket-python-mcp

# Install dependencies
uv sync

# Run the server
uv run bitbucket-python-mcp
```

## Setting Up BitBucket App Password

1. Log in to BitBucket Cloud
2. Click on your profile icon → **Personal settings**
3. Navigate to **App passwords** under **Access management**
4. Click **Create app password**
5. Enter a label (e.g., "MCP Server")
6. Select the following permissions:
   - **Repositories**: Read, Write, Admin
   - **Pull requests**: Read, Write
7. Click **Create**
8. Copy the generated password immediately (it won't be shown again)

## Configuring AI Agents

### Claude Code CLI

Create or edit `~/.claude/claude_desktop_config.json`:

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

### Environment Variables

You can also set environment variables in your shell profile:

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export BITBUCKET_USERNAME="your-username"
export BITBUCKET_API_TOKEN="your-api-token"
export BITBUCKET_WORKSPACE="your-workspace"
```

Then configure the MCP server without inline env vars:

```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "uvx",
      "args": ["bitbucket-python-mcp"]
    }
  }
}
```

## Verifying Installation

To verify the installation is working:

1. Set the required environment variables
2. Run `uvx bitbucket-python-mcp` or `bitbucket-python-mcp`
3. The server should start without errors

If you see an error about missing environment variables, ensure all required variables are set.

## Troubleshooting

### "Missing required environment variables" Error

Ensure all three required variables are set:
- `BITBUCKET_USERNAME`
- `BITBUCKET_API_TOKEN`
- `BITBUCKET_WORKSPACE`

### Authentication Failures

1. Verify your username is correct (it's your BitBucket username, not email)
2. Ensure the app password hasn't expired
3. Check that the app password has the required permissions

### Connection Issues

1. Check your internet connection
2. Verify BitBucket Cloud is accessible
3. Check for any firewall or proxy issues

## Next Steps

- Read the [Configuration Guide](configuration.md) for advanced options
- See the [Tools Reference](tools-reference.md) for available commands
