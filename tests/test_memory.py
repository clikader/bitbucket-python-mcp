"""Tests for the memory module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from bitbucket_mcp.memory import Memory, MemoryManager, MemorySource


class TestMemorySource:
    """Tests for MemorySource class."""

    def test_to_dict(self):
        """Test converting MemorySource to dict."""
        source = MemorySource(
            type="pr_comment",
            workspace="test-workspace",
            repository="test-repo",
            pr_id=123,
        )
        result = source.to_dict()

        assert result["type"] == "pr_comment"
        assert result["workspace"] == "test-workspace"
        assert result["repository"] == "test-repo"
        assert result["pr_id"] == 123
        assert "comment_id" not in result  # None values excluded

    def test_from_dict(self):
        """Test creating MemorySource from dict."""
        data = {
            "type": "user",
            "workspace": "my-workspace",
        }
        source = MemorySource.from_dict(data)

        assert source.type == "user"
        assert source.workspace == "my-workspace"
        assert source.repository is None


class TestMemory:
    """Tests for Memory class."""

    def test_to_dict(self):
        """Test converting Memory to dict."""
        memory = Memory(
            id="test-id",
            content="Use uv for package management",
            category="tools",
            tags=["uv", "python", "packages"],
            source=MemorySource(type="user"),
            created_at="2025-01-18T00:00:00Z",
            workspace="test-workspace",
        )
        result = memory.to_dict()

        assert result["id"] == "test-id"
        assert result["content"] == "Use uv for package management"
        assert result["category"] == "tools"
        assert result["tags"] == ["uv", "python", "packages"]
        assert result["workspace"] == "test-workspace"

    def test_from_dict(self):
        """Test creating Memory from dict."""
        data = {
            "id": "test-id",
            "content": "Mock API calls in tests",
            "category": "testing",
            "tags": ["testing", "mocking"],
            "source": {"type": "pr_comment", "pr_id": 195},
            "created_at": "2025-01-18T00:00:00Z",
            "workspace": None,
        }
        memory = Memory.from_dict(data)

        assert memory.id == "test-id"
        assert memory.content == "Mock API calls in tests"
        assert memory.category == "testing"
        assert memory.source.pr_id == 195

    def test_matches_context_global(self):
        """Test global memories match any context."""
        memory = Memory(
            id="test",
            content="test",
            category="general",
            tags=[],
            source=MemorySource(type="user"),
            created_at="",
            workspace=None,  # Global
        )

        assert memory.matches_context("any-workspace", "any-repo")
        assert memory.matches_context(None, None)

    def test_matches_context_workspace_specific(self):
        """Test workspace-specific memories."""
        memory = Memory(
            id="test",
            content="test",
            category="general",
            tags=[],
            source=MemorySource(type="user"),
            created_at="",
            workspace="my-workspace",
        )

        assert memory.matches_context("my-workspace", "any-repo")
        assert not memory.matches_context("other-workspace", "any-repo")

    def test_matches_context_repo_specific(self):
        """Test repository-specific memories."""
        memory = Memory(
            id="test",
            content="test",
            category="general",
            tags=[],
            source=MemorySource(type="user"),
            created_at="",
            workspace="my-workspace",
            repository="my-repo",
        )

        assert memory.matches_context("my-workspace", "my-repo")
        assert not memory.matches_context("my-workspace", "other-repo")


class TestMemoryManager:
    """Tests for MemoryManager class."""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create a temporary directory for memory storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_memory_dir):
        """Create a MemoryManager with temp storage."""
        return MemoryManager(memory_dir=temp_memory_dir)

    def test_add_memory(self, manager):
        """Test adding a memory."""
        memory = manager.add_memory(
            content="Use shared-pipeline for SonarQube",
            category="pipeline",
            tags=["sonarqube", "ci"],
            source_type="pr_comment",
            workspace="test-workspace",
            pr_id=195,
        )

        assert memory.id is not None
        assert memory.content == "Use shared-pipeline for SonarQube"
        assert memory.category == "pipeline"
        assert "sonarqube" in memory.tags
        assert memory.source.type == "pr_comment"
        assert memory.source.pr_id == 195

    def test_add_memory_invalid_category(self, manager):
        """Test adding memory with invalid category defaults to general."""
        memory = manager.add_memory(
            content="test",
            category="invalid_category",
        )

        assert memory.category == "general"

    def test_get_memory(self, manager):
        """Test retrieving a memory by ID."""
        added = manager.add_memory(content="test memory")
        retrieved = manager.get_memory(added.id)

        assert retrieved is not None
        assert retrieved.content == "test memory"

    def test_get_memory_not_found(self, manager):
        """Test retrieving non-existent memory."""
        result = manager.get_memory("non-existent-id")
        assert result is None

    def test_delete_memory(self, manager):
        """Test deleting a memory."""
        added = manager.add_memory(content="to be deleted")

        success = manager.delete_memory(added.id)
        assert success

        retrieved = manager.get_memory(added.id)
        assert retrieved is None

    def test_delete_memory_not_found(self, manager):
        """Test deleting non-existent memory."""
        success = manager.delete_memory("non-existent-id")
        assert not success

    def test_list_memories_all(self, manager):
        """Test listing all memories."""
        manager.add_memory(content="memory 1")
        manager.add_memory(content="memory 2")
        manager.add_memory(content="memory 3")

        memories = manager.list_memories()
        assert len(memories) == 3

    def test_list_memories_by_category(self, manager):
        """Test filtering memories by category."""
        manager.add_memory(content="pipeline memory", category="pipeline")
        manager.add_memory(content="testing memory", category="testing")
        manager.add_memory(content="another pipeline", category="pipeline")

        memories = manager.list_memories(category="pipeline")
        assert len(memories) == 2
        assert all(m.category == "pipeline" for m in memories)

    def test_list_memories_by_workspace(self, manager):
        """Test filtering memories by workspace."""
        manager.add_memory(content="global", workspace=None)
        manager.add_memory(content="ws1", workspace="workspace1")
        manager.add_memory(content="ws2", workspace="workspace2")

        # Workspace filter includes global memories
        memories = manager.list_memories(workspace="workspace1")
        assert len(memories) == 2  # global + ws1

    def test_search_memories_content(self, manager):
        """Test searching memories by content."""
        manager.add_memory(content="Use uv for Python packages")
        manager.add_memory(content="Use pytest for testing")
        manager.add_memory(content="Mock external API calls")

        results = manager.search_memories("pytest")
        assert len(results) == 1
        assert "pytest" in results[0].content

    def test_search_memories_tags(self, manager):
        """Test searching memories by tags."""
        manager.add_memory(content="memory 1", tags=["sonarqube", "ci"])
        manager.add_memory(content="memory 2", tags=["testing"])
        manager.add_memory(content="memory 3", tags=["sonarqube", "pipeline"])

        results = manager.search_memories("sonarqube")
        assert len(results) == 2

    def test_search_memories_case_insensitive(self, manager):
        """Test case-insensitive search."""
        manager.add_memory(content="Use SonarQube for analysis")

        results = manager.search_memories("sonarqube")
        assert len(results) == 1

    def test_get_relevant_memories(self, manager):
        """Test getting relevant memories for context."""
        manager.add_memory(content="global standard", workspace=None)
        manager.add_memory(content="workspace standard", workspace="my-workspace")
        manager.add_memory(content="other workspace", workspace="other")

        results = manager.get_relevant_memories(workspace="my-workspace")
        assert len(results) == 2  # global + my-workspace

    def test_get_relevant_memories_with_categories(self, manager):
        """Test filtering relevant memories by category."""
        manager.add_memory(content="pipeline", category="pipeline")
        manager.add_memory(content="testing", category="testing")
        manager.add_memory(content="workflow", category="workflow")

        results = manager.get_relevant_memories(categories=["pipeline", "testing"])
        assert len(results) == 2

    def test_clear_all(self, manager):
        """Test clearing all memories."""
        manager.add_memory(content="memory 1")
        manager.add_memory(content="memory 2")

        count = manager.clear_all()
        assert count == 2

        memories = manager.list_memories()
        assert len(memories) == 0

    def test_persistence(self, temp_memory_dir):
        """Test memories persist across manager instances."""
        manager1 = MemoryManager(memory_dir=temp_memory_dir)
        manager1.add_memory(content="persistent memory")

        # Create new manager instance
        manager2 = MemoryManager(memory_dir=temp_memory_dir)
        memories = manager2.list_memories()

        assert len(memories) == 1
        assert memories[0].content == "persistent memory"


class TestMemoryTools:
    """Tests for memory tools."""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create a temporary directory for memory storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_manager(self, temp_memory_dir):
        """Create a mock memory manager."""
        manager = MemoryManager(memory_dir=temp_memory_dir)
        return manager

    @pytest.mark.asyncio
    async def test_add_memory_tool(self, mock_env_vars, mock_manager):
        """Test add_memory tool."""
        from mcp.server.fastmcp import FastMCP

        from bitbucket_mcp.tools.memory import register_memory_tools

        with patch("bitbucket_mcp.tools.memory.get_memory_manager", return_value=mock_manager):
            mcp = FastMCP("test")
            register_memory_tools(mcp)

            # Get the registered tool
            tools = {t.name: t for t in mcp._tool_manager._tools.values()}
            add_memory_fn = tools["add_memory"].fn

            result = await add_memory_fn(
                content="Test standard",
                category="testing",
                tags="test,unit",
            )

            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["memory"]["content"] == "Test standard"

    @pytest.mark.asyncio
    async def test_list_memories_tool(self, mock_env_vars, mock_manager):
        """Test list_memories tool."""
        from mcp.server.fastmcp import FastMCP

        from bitbucket_mcp.tools.memory import register_memory_tools

        # Add some memories first
        mock_manager.add_memory(content="Memory 1")
        mock_manager.add_memory(content="Memory 2")

        with patch("bitbucket_mcp.tools.memory.get_memory_manager", return_value=mock_manager):
            mcp = FastMCP("test")
            register_memory_tools(mcp)

            tools = {t.name: t for t in mcp._tool_manager._tools.values()}
            list_memories_fn = tools["list_memories"].fn

            result = await list_memories_fn()

            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["count"] == 2

    @pytest.mark.asyncio
    async def test_search_memories_tool(self, mock_env_vars, mock_manager):
        """Test search_memories tool."""
        from mcp.server.fastmcp import FastMCP

        from bitbucket_mcp.tools.memory import register_memory_tools

        mock_manager.add_memory(content="Use pytest for testing")
        mock_manager.add_memory(content="Use uv for packages")

        with patch("bitbucket_mcp.tools.memory.get_memory_manager", return_value=mock_manager):
            mcp = FastMCP("test")
            register_memory_tools(mcp)

            tools = {t.name: t for t in mcp._tool_manager._tools.values()}
            search_fn = tools["search_memories"].fn

            result = await search_fn(query="pytest")

            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["count"] == 1

    @pytest.mark.asyncio
    async def test_delete_memory_tool(self, mock_env_vars, mock_manager):
        """Test delete_memory tool."""
        from mcp.server.fastmcp import FastMCP

        from bitbucket_mcp.tools.memory import register_memory_tools

        memory = mock_manager.add_memory(content="To delete")

        with patch("bitbucket_mcp.tools.memory.get_memory_manager", return_value=mock_manager):
            mcp = FastMCP("test")
            register_memory_tools(mcp)

            tools = {t.name: t for t in mcp._tool_manager._tools.values()}
            delete_fn = tools["delete_memory"].fn

            result = await delete_fn(memory_id=memory.id)

            result_data = json.loads(result)
            assert result_data["status"] == "success"

            # Verify deletion
            assert mock_manager.get_memory(memory.id) is None
