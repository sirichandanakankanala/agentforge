"""Mock and Real implementations of tools."""
import time
import os
from typing import List
from datetime import datetime
from tools.registry import (
    BaseTool, ToolDefinition, ToolParameter, ToolResult, get_logger
)

logger = get_logger("tools.implementations")


class MockWebSearchTool(BaseTool):
    """Mock web search tool - returns deterministic results."""
    
    definition = ToolDefinition(
        name="web_search",
        description="Search the web for information",
        category="search",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True
            ),
            ToolParameter(
                name="num_results",
                type="number",
                description="Number of results to return",
                required=False
            ),
        ],
    )
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        """Execute mock web search."""
        start_time = time.time()
        
        # Mock results
        mock_results = [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/result-{i+1}",
                "snippet": f"This is a mock search result about {query}. Retrieved at {datetime.now().isoformat()}",
            }
            for i in range(min(num_results, 5))
        ]
        
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Mock web search executed for query: {query}")
        
        return ToolResult(
            success=True,
            output={"results": mock_results},
            execution_time_ms=execution_time
        )


class RealWebSearchTool(BaseTool):
    """Real web search tool using SerpAPI."""
    
    definition = ToolDefinition(
        name="web_search",
        description="Search the web for information using SerpAPI",
        category="search",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True
            ),
            ToolParameter(
                name="num_results",
                type="number",
                description="Number of results to return (max 10)",
                required=False
            ),
        ],
        requires_api_key=True,
        api_key_env_var="SERPAPI_API_KEY"
    )
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        """Execute real web search via SerpAPI."""
        start_time = time.time()
        
        try:
            import httpx
            
            api_key = os.getenv("SERPAPI_API_KEY")
            if not api_key:
                return ToolResult(
                    success=False,
                    output=None,
                    error="SERPAPI_API_KEY not set. Set it to enable real web search."
                )
            
            # Make API call
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": query,
                        "api_key": api_key,
                        "num": min(num_results, 10),
                    },
                    timeout=10.0
                )
                response.raise_for_status()
            
            data = response.json()
            
            # Extract results
            results = []
            for item in data.get("organic_results", [])[:num_results]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet"),
                })
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"Real web search executed for query: {query} ({len(results)} results)")
            
            return ToolResult(
                success=True,
                output={"results": results},
                execution_time_ms=execution_time
            )
        
        except Exception as e:
            logger.error(f"Real web search failed: {str(e)}")
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )


class MockNotificationSenderTool(BaseTool):
    """Mock notification sender - logs instead of sending."""
    
    definition = ToolDefinition(
        name="notification_sender",
        description="Send notifications via email or Slack",
        category="notification",
        parameters=[
            ToolParameter(
                name="recipient",
                type="string",
                description="Email or Slack user ID",
                required=True
            ),
            ToolParameter(
                name="message",
                type="string",
                description="Message to send",
                required=True
            ),
            ToolParameter(
                name="channel",
                type="string",
                description="Notification channel",
                required=True,
                enum=["email", "slack", "sms"]
            ),
        ],
    )
    
    async def execute(self, recipient: str, message: str, channel: str, **kwargs) -> ToolResult:
        """Execute mock notification send."""
        start_time = time.time()
        
        logger.info(f"Mock notification via {channel} to {recipient}: {message[:50]}...")
        
        execution_time = (time.time() - start_time) * 1000
        return ToolResult(
            success=True,
            output={
                "notification_id": f"mock_{recipient}_{int(time.time())}",
                "status": "sent",
                "channel": channel,
            },
            execution_time_ms=execution_time
        )


class MockSummarizerTool(BaseTool):
    """Mock text summarizer - returns shortened version."""
    
    definition = ToolDefinition(
        name="summarizer",
        description="Summarize text content",
        category="content",
        parameters=[
            ToolParameter(
                name="text",
                type="string",
                description="Text to summarize",
                required=True
            ),
            ToolParameter(
                name="max_length",
                type="number",
                description="Maximum length of summary",
                required=False
            ),
        ],
    )
    
    async def execute(self, text: str, max_length: int = 100, **kwargs) -> ToolResult:
        """Execute mock summarization."""
        start_time = time.time()
        
        # Simple mock: take first sentence or truncate
        summary = text[:max_length] + "..." if len(text) > max_length else text
        
        logger.info(f"Mock summarizer: {len(text)} -> {len(summary)} chars")
        
        execution_time = (time.time() - start_time) * 1000
        return ToolResult(
            success=True,
            output={"summary": summary},
            execution_time_ms=execution_time
        )
