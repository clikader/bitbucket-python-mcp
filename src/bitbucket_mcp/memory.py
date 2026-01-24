"""Memory system for storing workspace standards and learnings.

Stores key information from PR comments, user input, and API responses
to help maintain consistent standards across repositories.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default memory storage location
DEFAULT_MEMORY_DIR = Path.home() / ".bitbucket-python-mcp" / "memory"


@dataclass
class MemorySource:
    """Source information for a memory entry."""

    type: str  # "pr_comment", "user", "api_response"
    workspace: str | None = None
    repository: str | None = None
    pr_id: int | None = None
    comment_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemorySource":
        return cls(
            type=data.get("type", "unknown"),
            workspace=data.get("workspace"),
            repository=data.get("repository"),
            pr_id=data.get("pr_id"),
            comment_id=data.get("comment_id"),
        )


@dataclass
class Memory:
    """A single memory entry."""

    id: str
    content: str
    category: str  # "pipeline", "testing", "coding_style", "tools", "workflow", "general"
    tags: list[str]
    source: MemorySource
    created_at: str
    workspace: str | None = None  # None means global/all workspaces
    repository: str | None = None  # None means all repos in workspace

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "source": self.source.to_dict(),
            "created_at": self.created_at,
            "workspace": self.workspace,
            "repository": self.repository,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Memory":
        return cls(
            id=data["id"],
            content=data["content"],
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            source=MemorySource.from_dict(data.get("source", {"type": "unknown"})),
            created_at=data.get("created_at", ""),
            workspace=data.get("workspace"),
            repository=data.get("repository"),
        )

    def matches_context(self, workspace: str | None = None, repository: str | None = None) -> bool:
        """Check if this memory applies to the given context."""
        # Global memories apply everywhere
        if self.workspace is None:
            return True
        # Workspace-specific: must match workspace
        if workspace and self.workspace != workspace:
            return False
        # Repository-specific: must match repository
        return not (self.repository is not None and repository != self.repository)


@dataclass
class MemoryStore:
    """Storage for all memories."""

    memories: list[Memory] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "memories": [m.to_dict() for m in self.memories],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryStore":
        return cls(
            version=data.get("version", "1.0"),
            memories=[Memory.from_dict(m) for m in data.get("memories", [])],
        )


class MemoryManager:
    """Manages the memory storage system."""

    CATEGORIES = [
        "pipeline",
        "testing",
        "coding_style",
        "tools",
        "workflow",
        "general",
    ]

    def __init__(self, memory_dir: Path | None = None):
        """Initialize the memory manager.

        Args:
            memory_dir: Directory to store memories. Defaults to ~/.bitbucket-python-mcp/memory/
        """
        self._memory_dir = memory_dir or DEFAULT_MEMORY_DIR
        self._memory_file = self._memory_dir / "memories.json"
        self._store: MemoryStore | None = None

    @property
    def memory_dir(self) -> Path:
        return self._memory_dir

    def _ensure_dir(self) -> None:
        """Ensure the memory directory exists."""
        self._memory_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> MemoryStore:
        """Load memories from disk."""
        if self._store is not None:
            return self._store

        if self._memory_file.exists():
            try:
                with open(self._memory_file, encoding="utf-8") as f:
                    data = json.load(f)
                self._store = MemoryStore.from_dict(data)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load memories, starting fresh: {e}")
                self._store = MemoryStore()
        else:
            self._store = MemoryStore()

        return self._store

    def _save(self) -> None:
        """Save memories to disk."""
        self._ensure_dir()
        store = self._load()
        with open(self._memory_file, "w", encoding="utf-8") as f:
            json.dump(store.to_dict(), f, indent=2, ensure_ascii=False)

    def add_memory(
        self,
        content: str,
        category: str = "general",
        tags: list[str] | None = None,
        source_type: str = "user",
        workspace: str | None = None,
        repository: str | None = None,
        pr_id: int | None = None,
        comment_id: int | None = None,
    ) -> Memory:
        """Add a new memory.

        Args:
            content: The memory content/learning
            category: Category (pipeline, testing, coding_style, tools, workflow, general)
            tags: Optional tags for searching
            source_type: Source type (user, pr_comment, api_response)
            workspace: Workspace this applies to (None for global)
            repository: Repository this applies to (None for all in workspace)
            pr_id: Source PR ID if from a PR comment
            comment_id: Source comment ID if from a PR comment

        Returns:
            The created Memory object
        """
        store = self._load()

        # Validate category
        if category not in self.CATEGORIES:
            category = "general"

        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            category=category,
            tags=tags or [],
            source=MemorySource(
                type=source_type,
                workspace=workspace,
                repository=repository,
                pr_id=pr_id,
                comment_id=comment_id,
            ),
            created_at=datetime.now(UTC).isoformat(),
            workspace=workspace,
            repository=repository,
        )

        store.memories.append(memory)
        self._save()

        logger.info(f"Added memory: {memory.id}")
        return memory

    def get_memory(self, memory_id: str) -> Memory | None:
        """Get a memory by ID."""
        store = self._load()
        for memory in store.memories:
            if memory.id == memory_id:
                return memory
        return None

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        store = self._load()
        for i, memory in enumerate(store.memories):
            if memory.id == memory_id:
                del store.memories[i]
                self._save()
                logger.info(f"Deleted memory: {memory_id}")
                return True
        return False

    def list_memories(
        self,
        workspace: str | None = None,
        repository: str | None = None,
        category: str | None = None,
    ) -> list[Memory]:
        """List all memories, optionally filtered.

        Args:
            workspace: Filter by workspace (also includes global memories)
            repository: Filter by repository
            category: Filter by category

        Returns:
            List of matching memories
        """
        store = self._load()
        results = []

        for memory in store.memories:
            # Filter by context
            if (workspace or repository) and not memory.matches_context(workspace, repository):
                continue

            # Filter by category
            if category and memory.category != category:
                continue

            results.append(memory)

        return results

    def search_memories(
        self,
        query: str,
        workspace: str | None = None,
        repository: str | None = None,
    ) -> list[Memory]:
        """Search memories by keyword.

        Args:
            query: Search query (searches content and tags)
            workspace: Filter by workspace
            repository: Filter by repository

        Returns:
            List of matching memories
        """
        store = self._load()
        results = []
        query_lower = query.lower()

        for memory in store.memories:
            # Filter by context
            if (workspace or repository) and not memory.matches_context(workspace, repository):
                continue

            # Search in content and tags
            if query_lower in memory.content.lower() or any(
                query_lower in tag.lower() for tag in memory.tags
            ):
                results.append(memory)

        return results

    def get_relevant_memories(
        self,
        workspace: str | None = None,
        repository: str | None = None,
        categories: list[str] | None = None,
    ) -> list[Memory]:
        """Get all memories relevant to the current context.

        Args:
            workspace: Current workspace
            repository: Current repository
            categories: Filter by categories

        Returns:
            List of relevant memories
        """
        store = self._load()
        results = []

        for memory in store.memories:
            if not memory.matches_context(workspace, repository):
                continue

            if categories and memory.category not in categories:
                continue

            results.append(memory)

        return results

    def clear_all(self) -> int:
        """Clear all memories. Returns count of deleted memories."""
        store = self._load()
        count = len(store.memories)
        store.memories = []
        self._save()
        logger.info(f"Cleared {count} memories")
        return count


# Global memory manager instance
_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
