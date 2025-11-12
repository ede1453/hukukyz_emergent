"""MCP Client for interacting with MCP servers"""

from typing import List, Dict, Any, Optional
import logging
import asyncio

from backend.mcp.servers.legal_documents import legal_document_server
from backend.mcp.servers.document_processor import document_processor_server
from backend.mcp.servers.web_search import web_search_server

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with MCP servers"""
    
    def __init__(self):
        self.servers = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize all MCP servers"""
        if self._initialized:
            return
        
        try:
            # Initialize servers
            logger.info("Initializing MCP servers...")
            
            # Legal Documents Server
            await legal_document_server.initialize()
            self.servers["legal_documents"] = legal_document_server
            
            # Document Processor Server
            await document_processor_server.initialize()
            self.servers["document_processor"] = document_processor_server
            
            # Web Search Server
            await web_search_server.initialize()
            self.servers["web_search"] = web_search_server
            
            self._initialized = True
            logger.info(f"Initialized {len(self.servers)} MCP servers")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP servers: {e}")
            raise
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """Call a tool on a specific server
        
        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool
            params: Tool parameters
        
        Returns:
            Tool execution result
        """
        if not self._initialized:
            await self.initialize()
        
        if server_name not in self.servers:
            raise ValueError(f"Server not found: {server_name}")
        
        server = self.servers[server_name]
        result = await server.call_tool(tool_name, params)
        
        if not result.success:
            logger.error(f"Tool execution failed: {result.error}")
            raise RuntimeError(f"Tool error: {result.error}")
        
        return result.data
    
    def list_servers(self) -> List[str]:
        """List all available servers"""
        return list(self.servers.keys())
    
    def list_tools(self, server_name: Optional[str] = None) -> Dict[str, List[str]]:
        """List all available tools
        
        Args:
            server_name: Specific server name (optional)
        
        Returns:
            Dict mapping server names to tool lists
        """
        if server_name:
            if server_name not in self.servers:
                return {}
            server = self.servers[server_name]
            return {server_name: [tool.name for tool in server.list_tools()]}
        
        # List all tools from all servers
        result = {}
        for name, server in self.servers.items():
            result[name] = [tool.name for tool in server.list_tools()]
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all servers"""
        if not self._initialized:
            await self.initialize()
        
        health_status = {}
        for name, server in self.servers.items():
            try:
                health = await server.health_check()
                health_status[name] = health
            except Exception as e:
                health_status[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status


# Global MCP client instance
mcp_client = MCPClient()
