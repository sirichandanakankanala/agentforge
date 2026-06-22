"""Test suite for AgentForge backend."""
import pytest
import asyncio
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.registry import ToolRegistry, ToolDefinition, ToolParameter, ToolResult, BaseTool
from tools.implementations import (
    MockWebSearchTool,
    MockNotificationSenderTool,
    MockSummarizerTool,
)


class TestToolRegistry:
    """Test tool registry functionality."""
    
    def test_registry_singleton(self):
        """Test that registry is a singleton."""
        from tools.registry import get_tool_registry
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()
        assert registry1 is registry2
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockWebSearchTool()
        registry.register(tool)
        
        retrieved = registry.get_tool("web_search")
        assert retrieved is not None
        assert retrieved.definition.name == "web_search"
    
    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.register(MockWebSearchTool())
        registry.register(MockNotificationSenderTool())
        registry.register(MockSummarizerTool())
        
        tools = registry.list_tools()
        assert len(tools) == 3
        assert any(t.name == "web_search" for t in tools)
    
    def test_list_tools_by_category(self):
        """Test filtering tools by category."""
        registry = ToolRegistry()
        registry.register(MockWebSearchTool())
        registry.register(MockNotificationSenderTool())
        registry.register(MockSummarizerTool())
        
        search_tools = registry.list_tools_by_category("search")
        assert len(search_tools) == 1
        assert search_tools[0].name == "web_search"
        
        notification_tools = registry.list_tools_by_category("notification")
        assert len(notification_tools) == 1
    
    def test_mock_mode(self):
        """Test mock mode toggle."""
        registry = ToolRegistry()
        assert registry.mock_mode is True
        
        registry.set_mock_mode(False)
        assert registry.mock_mode is False
        
        registry.set_mock_mode(True)
        assert registry.mock_mode is True


class TestMockWebSearchTool:
    """Test mock web search tool."""
    
    @pytest.mark.asyncio
    async def test_web_search_basic(self):
        """Test basic web search execution."""
        tool = MockWebSearchTool()
        result = await tool.execute(query="python programming")
        
        assert result.success is True
        assert "results" in result.output
        assert len(result.output["results"]) == 5
        assert all("title" in r and "url" in r for r in result.output["results"])
    
    @pytest.mark.asyncio
    async def test_web_search_custom_results(self):
        """Test web search with custom result count."""
        tool = MockWebSearchTool()
        result = await tool.execute(query="AI news", num_results=3)
        
        assert result.success is True
        assert len(result.output["results"]) == 3
    
    @pytest.mark.asyncio
    async def test_web_search_execution_time(self):
        """Test that execution time is recorded."""
        tool = MockWebSearchTool()
        result = await tool.execute(query="test")
        
        assert result.execution_time_ms >= 0
    
    def test_validate_required_params(self):
        """Test parameter validation."""
        tool = MockWebSearchTool()
        
        # Valid: has required 'query'
        assert tool.validate_params(query="test") is True
        
        # Invalid: missing required 'query'
        assert tool.validate_params() is False


class TestMockNotificationSenderTool:
    """Test mock notification sender tool."""
    
    @pytest.mark.asyncio
    async def test_send_notification(self):
        """Test sending a notification."""
        tool = MockNotificationSenderTool()
        result = await tool.execute(
            recipient="test@example.com",
            message="Test notification",
            channel="email"
        )
        
        assert result.success is True
        assert "notification_id" in result.output
        assert result.output["status"] == "sent"
    
    @pytest.mark.asyncio
    async def test_send_to_slack(self):
        """Test Slack notification."""
        tool = MockNotificationSenderTool()
        result = await tool.execute(
            recipient="@testuser",
            message="Slack test",
            channel="slack"
        )
        
        assert result.success is True
        assert result.output["channel"] == "slack"


class TestMockSummarizerTool:
    """Test mock summarizer tool."""
    
    @pytest.mark.asyncio
    async def test_summarize_text(self):
        """Test text summarization."""
        tool = MockSummarizerTool()
        long_text = "This is a very long text. " * 10
        result = await tool.execute(text=long_text, max_length=100)
        
        assert result.success is True
        assert "summary" in result.output
        assert len(result.output["summary"]) <= 104  # 100 + "..."
    
    @pytest.mark.asyncio
    async def test_summarize_short_text(self):
        """Test summarizing short text."""
        tool = MockSummarizerTool()
        short_text = "Short text"
        result = await tool.execute(text=short_text)
        
        assert result.success is True
        assert result.output["summary"] == short_text


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
