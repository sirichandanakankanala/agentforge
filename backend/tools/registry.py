"""Tool registry abstraction layer for extensible tool management."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from logger import get_logger

logger = get_logger("tools")


class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    name: str
    type: str  # "string", "number", "boolean", "array"
    description: str
    required: bool = True
    enum: Optional[List[str]] = None  # For restricted values


class ToolDefinition(BaseModel):
    """Definition of a tool that agents can use."""
    name: str
    description: str
    category: str  # "search", "notification", "data", "content", etc.
    parameters: List[ToolParameter]
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None  # e.g., "SERPAPI_API_KEY"


class ToolResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    definition: ToolDefinition
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """Validate that required parameters are provided."""
        required_params = {
            p.name for p in self.definition.parameters if p.required
        }
        provided_params = set(kwargs.keys())
        missing = required_params - provided_params
        if missing:
            logger.warning(f"Missing required parameters for {self.definition.name}: {missing}")
            return False
        return True


class ToolRegistry:
    """Central registry for all available tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._mock_mode = True
        logger.info("ToolRegistry initialized in mock mode")
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.definition.name] = tool
        logger.info(f"Registered tool: {tool.definition.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """List all available tools."""
        return [tool.definition for tool in self._tools.values()]
    
    def list_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """List tools in a specific category."""
        return [
            tool.definition 
            for tool in self._tools.values() 
            if tool.definition.category == category
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unknown tool: {tool_name}"
            )
        
        if not tool.validate_params(**kwargs):
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid parameters for {tool_name}"
            )
        
        try:
            logger.info(f"Executing tool: {tool_name} with params: {list(kwargs.keys())}")
            result = await tool.execute(**kwargs)
            logger.info(f"Tool {tool_name} completed: success={result.success}")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def set_mock_mode(self, mock: bool) -> None:
        """Toggle mock mode for all tools."""
        self._mock_mode = mock
        logger.info(f"Mock mode set to: {mock}")
    
    @property
    def mock_mode(self) -> bool:
        """Check if tools are in mock mode."""
        return self._mock_mode


# Global registry instance
_registry = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
