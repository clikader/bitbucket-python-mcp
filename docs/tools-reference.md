# Tools Reference

Complete reference for all available tools in the BitBucket MCP Server.

## Repository Tools

### list_repositories

List all repositories in a BitBucket workspace.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON array of repositories with name, slug, description, and URL.

**Example:**
```
List all repositories in my workspace
```

---

### get_repository

Get detailed information about a specific repository.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `repository` | string | Yes | - | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON object with complete repository details including clone URLs.

**Example:**
```
Get details for the "backend-api" repository
```

---

### create_repository

Create a new repository in BitBucket.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `name` | string | Yes | - | Repository name |
| `description` | string | No | "" | Repository description |
| `is_private` | boolean | No | true | Whether repo is private |
| `project_key` | string | No | None | Project to associate with |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON object with created repository details.

**Example:**
```
Create a new private repository named "new-service" with description "New microservice"
```

---

### delete_repository

Delete a repository from BitBucket.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `repository` | string | Yes | - | Repository slug |
| `confirm` | boolean | Yes | - | Must be true to proceed |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** Confirmation message.

**Example:**
```
Delete the repository "old-project" (confirm: true)
```

---

### update_repository

Update repository settings.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `repository` | string | Yes | - | Repository slug |
| `description` | string | No | None | New description |
| `is_private` | boolean | No | None | New visibility setting |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON object with updated repository details.

**Example:**
```
Update the description of "backend-api" to "Main backend service"
```

---

## Branch Tools

### list_branches

List all branches in a repository.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON array of branches with commit info.

**Example:**
```
List all branches in the current repository
```

---

### get_branch

Get detailed information about a specific branch.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `branch_name` | string | Yes | - | Branch name |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON object with branch details and commit info.

**Example:**
```
Get details for the "feature-auth" branch
```

---

### create_branch

Create a new branch from an existing one.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `branch_name` | string | Yes | - | New branch name |
| `source_branch` | string | No | "development" | Source branch |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON object with created branch details.

**Example:**
```
Create a branch named "feature-login" from "development"
```

---

### delete_branch

Delete a branch from the repository.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `branch_name` | string | Yes | - | Branch to delete |
| `confirm` | boolean | Yes | - | Must be true to proceed |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** Confirmation message.

**Example:**
```
Delete the branch "old-feature" (confirm: true)
```

---

## Pull Request Tools

### list_pull_requests

List pull requests in a repository.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |
| `state` | string | No | "OPEN" | Filter: OPEN/MERGED/DECLINED |

**Returns:** JSON array of pull requests.

**Example:**
```
List all open pull requests
Show me merged pull requests
```

---

### get_pull_request

Get detailed information about a pull request.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `pr_id` | integer | No | Newest open | Pull request ID |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON object with complete PR details.

**Example:**
```
Show me the newest pull request
Get details for PR #42
```

---

### get_pull_request_diff

Get the diff/changes for a pull request.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `pr_id` | integer | Yes | - | Pull request ID |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** Raw diff text.

**Example:**
```
Show me the changes in PR #42
```

---

### get_pull_request_comments

Get all comments on a pull request.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `pr_id` | integer | Yes | - | Pull request ID |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON array of comments.

**Example:**
```
What are the comments on PR #42?
```

---

### add_pull_request_comment

Add a comment to a pull request.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `pr_id` | integer | Yes | - | Pull request ID |
| `comment` | string | Yes | - | Comment text |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |
| `file_path` | string | No | None | Path for inline comment |
| `line_number` | integer | No | None | Line for inline comment |

**Returns:** Confirmation with comment ID.

**Example:**
```
Add comment "Looks good!" to PR #42
Add inline comment "Consider using a constant here" on line 25 of src/config.py in PR #42
```

---

### approve_pull_request

Approve a pull request.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `pr_id` | integer | Yes | - | Pull request ID |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** Confirmation message.

**Example:**
```
Approve PR #42
```

---

### request_changes

Request changes on a pull request.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `pr_id` | integer | Yes | - | Pull request ID |
| `comment` | string | Yes | - | Explanation of needed changes |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** Confirmation message.

**Example:**
```
Request changes on PR #42 with comment "Please add unit tests"
```

---

### create_pull_request

Create a new pull request.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | string | Yes | - | PR title |
| `source_branch` | string | Yes | - | Branch with changes |
| `destination_branch` | string | No | "development" | Target branch |
| `description` | string | No | "" | PR description |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |
| `reviewers` | string | No | None | Comma-separated usernames |
| `close_source_branch` | boolean | No | false | Delete source after merge |

**Returns:** JSON object with created PR details.

**Example:**
```
Create a pull request titled "Add user authentication" from "feature-auth" to "development"
```

---

## Search Tools

### search_repositories

Search for repositories by name.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | No | None | Search query |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON object with matching repositories.

**Example:**
```
Find repositories containing "api" in the name
```

---

### get_repository_contents

Browse repository files and directories.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `path` | string | No | "" | Path to browse |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |
| `ref` | string | No | HEAD | Branch/tag/commit |

**Returns:** JSON object with directory listing or file info.

**Example:**
```
Show me the contents of the src directory
What files are in the root of the repository?
```

---

### search_code

Search for code patterns in a repository.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search pattern |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |

**Returns:** JSON array of matching code locations.

**Example:**
```
Search for "def authenticate" in the codebase
Find all occurrences of "TODO"
```

---

### get_file_content

Get the raw content of a specific file.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `file_path` | string | Yes | - | Path to file |
| `repository` | string | No | Auto-detect | Repository slug |
| `workspace` | string | No | Config default | Workspace slug |
| `ref` | string | No | HEAD | Branch/tag/commit |

**Returns:** Raw file content as string.

**Example:**
```
Show me the contents of src/main.py
Read the README.md file
```

---

## Memory Tools

The memory system stores learnings, standards, and patterns discovered from PR comments, code reviews, and user instructions. Memories persist across sessions in `~/.bitbucket-python-mcp/memory/`.

### add_memory

Store a new memory/learning for future reference.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `content` | string | Yes | - | The learning/standard to remember |
| `category` | string | No | "general" | Category: pipeline, testing, coding_style, tools, workflow, general |
| `tags` | string | No | None | Comma-separated tags for searching |
| `workspace` | string | No | None | Workspace this applies to (None = global) |
| `repository` | string | No | None | Repository this applies to |
| `source_type` | string | No | "user" | Source: user, pr_comment, api_response |
| `pr_id` | integer | No | None | Source PR ID if from a comment |

**Returns:** Confirmation with created memory details.

**Example:**
```
Remember that we should use uv for package management
Add memory: "Use shared-pipeline for SonarQube scans" with category "pipeline" and tags "sonarqube,ci"
```

---

### list_memories

List stored memories/learnings.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `workspace` | string | No | Config default | Filter by workspace |
| `repository` | string | No | None | Filter by repository |
| `category` | string | No | None | Filter by category |

**Returns:** JSON list of memories matching the filters.

**Example:**
```
List all stored memories
Show me pipeline-related memories
```

---

### search_memories

Search memories by keyword.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search keyword |
| `workspace` | string | No | Config default | Filter by workspace |
| `repository` | string | No | None | Filter by repository |

**Returns:** JSON list of matching memories.

**Example:**
```
Search memories for "sonarqube"
Find memories about testing
```

---

### get_relevant_memories

Get all memories relevant to the current context.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `workspace` | string | No | Config default | Current workspace |
| `repository` | string | No | None | Current repository |
| `categories` | string | No | None | Comma-separated categories to filter |

**Returns:** JSON list of relevant memories grouped by category.

**Example:**
```
Get relevant memories for this repository
What standards apply to this workspace?
```

---

### delete_memory

Delete a stored memory by ID.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `memory_id` | string | Yes | - | The ID of the memory to delete |

**Returns:** Confirmation of deletion.

**Example:**
```
Delete memory with ID "abc123"
```

---

### remember_from_pr_comment

Extract and store a learning from a PR comment.

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `repository` | string | Yes | - | Repository where comment was found |
| `pr_id` | integer | Yes | - | PR ID where comment was found |
| `comment_content` | string | Yes | - | Original comment content |
| `learning` | string | Yes | - | Extracted learning to remember |
| `category` | string | No | "general" | Category for the memory |
| `tags` | string | No | None | Comma-separated tags |
| `workspace` | string | No | Config default | Workspace |
| `apply_to_all_repos` | boolean | No | true | Apply to all repos or just this one |

**Returns:** Confirmation with created memory.

**Example:**
```
Remember from PR #195: "Use shared-pipeline for SonarQube" - category: pipeline, tags: sonarqube,ci
```
