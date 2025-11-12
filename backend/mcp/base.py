"""Base classes for MCP servers"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Callable, Optional
from pydantic import BaseModel, Field
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    """MCP Tool definition"""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    input_schema: Dict = Field(description="Input schema (JSON Schema)")
    output_schema: Dict = Field(description="Output schema (JSON Schema)")


class ToolResult(BaseModel):
    """Tool execution result"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = Field(description="Execution time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MCPServer(ABC):
    """Base MCP Server class"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, Callable] = {}
        self.tool_definitions: Dict[str, ToolDefinition] = {}
        logger.info(f"Initializing MCP Server: {name} v{version}")
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        input_schema: Dict,
        output_schema: Dict
    ):
        """Register a tool"""
        self.tools[name] = func
        self.tool_definitions[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema
        )
        logger.info(f"Registered tool: {name}")
    
    def tool(
        self,
        name: str,
        description: str,
        input_schema: Optional[type[BaseModel]] = None,
        output_schema: Optional[type[BaseModel]] = None
    ):
        """Decorator to register a tool"""
        def decorator(func: Callable):
            # Convert Pydantic models to JSON schema
            input_json_schema = input_schema.model_json_schema() if input_schema else {}
            output_json_schema = output_schema.model_json_schema() if output_schema else {}
            
            self.register_tool(
                name=name,
                func=func,
                description=description,
                input_schema=input_json_schema,
                output_schema=output_json_schema
            )
            return func
        return decorator
    
    async def call_tool(self, tool_name: str, params: Dict) -> ToolResult:
        """Call a tool by name"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if tool_name not in self.tools:
                raise ValueError(f"Tool not found: {tool_name}")
            
            tool_func = self.tools[tool_name]
            
            # Call tool (async or sync)
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**params)
            else:
                result = tool_func(**params)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return ToolResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"Tool execution error ({tool_name}): {e}")
            
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def list_tools(self) -> List[ToolDefinition]:
        """List all available tools"""
        return list(self.tool_definitions.values())
    
    def get_tool_definition(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get tool definition"""
        return self.tool_definitions.get(tool_name)
    
    @abstractmethod
    async def initialize(self):
        """Initialize server (override in subclass)"""
        pass
    
    async def health_check(self) -> Dict:
        """Health check endpoint"""
        return {
            "status": "healthy",
            "server": self.name,
            "version": self.version,
            "tools_count": len(self.tools),
            "timestamp": datetime.utcnow().isoformat()
        }
