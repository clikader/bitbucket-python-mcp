# Configuration Guide

This guide covers all configuration options for the BitBucket MCP Server.

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BITBUCKET_USERNAME` | Your BitBucket username | `johndoe` |
| `BITBUCKET_API_TOKEN` | App password/API token for authentication | `ATBBxxxxx` |
| `BITBUCKET_WORKSPACE` | Default workspace slug | `my-company` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BITBUCKET_MCP_DEBUG` | Enable debug logging | `false` |

## Finding Your Configuration Values

### BitBucket Username

Your username is **not** your email address. To find it:
1. Go to BitBucket Cloud
2. Click your profile icon → **Personal settings**
3. Your username is shown under **Atlassian account settings**

### Workspace Slug

The workspace slug is the URL-friendly identifier for your workspace:
1. Go to your workspace in BitBucket
2. Look at the URL: `https://bitbucket.org/WORKSPACE_SLUG/`
3. The slug is the part after `bitbucket.org/`

## Auto-Detection Features

### Repository Context

When you're working in a git repository with a BitBucket remote, the server can automatically detect:
- The workspace from the remote URL
- The repository name from the remote URL

This means you don't need to specify the repository for most operations when working locally.

**Supported Remote URL Formats:**
- SSH: `git@bitbucket.org:workspace/repo.git`
- HTTPS: `https://bitbucket.org/workspace/repo.git`
- HTTPS with username: `https://user@bitbucket.org/workspace/repo.git`

## Security Best Practices

### App Password Permissions

Only grant the minimum permissions needed:

| Permission | When Needed |
|------------|-------------|
| Repositories: Read | Always (for listing and viewing) |
| Repositories: Write | For updating repositories |
| Repositories: Admin | For creating/deleting repositories |
| Pull requests: Read | For viewing PRs and comments |
| Pull requests: Write | For creating/commenting/approving PRs |

### Storing Credentials

**Do NOT** commit credentials to version control. Options for secure storage:

1. **Environment Variables**: Set in your shell profile
2. **Secret Manager**: Use a secrets manager like 1Password CLI
3. **MCP Config**: Store in the MCP configuration file (user-specific)

### Rotating App Passwords

Periodically rotate your app passwords:
1. Create a new app password
2. Update your configuration
3. Revoke the old password

## Advanced Configuration

### Multiple Workspaces

If you work with multiple workspaces, you can:
1. Set a default workspace in `BITBUCKET_WORKSPACE`
2. Override per-command by specifying the `workspace` parameter

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export BITBUCKET_MCP_DEBUG=1
uvx bitbucket-python-mcp
```

This will output detailed information about:
- API requests being made
- Response data
- Error details

## Configuration Examples

### Minimal Configuration

```bash
export BITBUCKET_USERNAME="johndoe"
export BITBUCKET_API_TOKEN="ATBBxxxxxxxx"
export BITBUCKET_WORKSPACE="my-workspace"
```

### Claude Code CLI Configuration

```json
{
  "mcpServers": {
    "bitbucket": {
      "command": "uvx",
      "args": ["bitbucket-python-mcp"],
      "env": {
        "BITBUCKET_USERNAME": "johndoe",
        "BITBUCKET_API_TOKEN": "ATBBxxxxxxxx",
        "BITBUCKET_WORKSPACE": "my-workspace"
      }
    }
  }
}
```

### Development Configuration

For local development with debug logging:

```bash
export BITBUCKET_USERNAME="johndoe"
export BITBUCKET_APP_PASSWORD="ATBBxxxxxxxx"
export BITBUCKET_WORKSPACE="my-workspace"
export BITBUCKET_MCP_DEBUG="1"

# Run from source
cd bitbucket-python-mcp
uv run bitbucket-python-mcp
```
