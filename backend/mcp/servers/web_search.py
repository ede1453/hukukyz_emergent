"""Web Search MCP Server"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import logging
import httpx
import asyncio

from backend.mcp.base import MCPServer
from backend.config import settings

logger = logging.getLogger(__name__)


# Input/Output Schemas
class SearchLegalWebInput(BaseModel):
    """Input for search_legal_web tool"""
    query: str = Field(description="Search query")
    domain: str = Field(default=".gov.tr", description="Domain filter")
    limit: int = Field(default=10, description="Number of results")


class SearchLegalWebOutput(BaseModel):
    """Output for search_legal_web tool"""
    results: List[Dict]
    total: int


class SearchPrecedentsInput(BaseModel):
    """Input for search_precedents tool"""
    keywords: List[str] = Field(description="Search keywords")
    court_type: str = Field(description="Court type: yargitay, danistay, aym")
    limit: int = Field(default=10, description="Number of results")


class SearchPrecedentsOutput(BaseModel):
    """Output for search_precedents tool"""
    precedents: List[Dict]
    court_type: str
    total: int


class WebSearchServer(MCPServer):
    """MCP Server for web search operations"""
    
    def __init__(self):
        super().__init__(name="web_search", version="1.0.0")
        self.tavily_api_key = settings.tavily_api_key
        self.tavily_url = "https://api.tavily.com/search"
    
    async def initialize(self):
        """Initialize server"""
        logger.info("Web Search Server initialized")
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools"""
        
        @self.tool(
            name="search_legal_web",
            description="Search Turkish legal websites for information",
            input_schema=SearchLegalWebInput,
            output_schema=SearchLegalWebOutput
        )
        async def search_legal_web(input_data: SearchLegalWebInput) -> SearchLegalWebOutput:
            """Search web for legal information"""
            try:
                if isinstance(input_data, BaseModel):
                    params = input_data.model_dump()
                else:
                    params = input_data
                
                query = params["query"]
                domain = params.get("domain", ".gov.tr")
                limit = params.get("limit", 10)
                
                # Use Tavily API if available
                if self.tavily_api_key:
                    results = await self._search_with_tavily(query, domain, limit)
                else:
                    # Fallback to basic search (mock)
                    logger.warning("Tavily API key not set, using mock data")
                    results = []
                
                return SearchLegalWebOutput(
                    results=results,
                    total=len(results)
                )
                
            except Exception as e:
                logger.error(f"Web search error: {e}")
                return SearchLegalWebOutput(results=[], total=0)
        
        @self.tool(
            name="search_precedents",
            description="Search for legal precedents from Turkish courts",
            input_schema=SearchPrecedentsInput,
            output_schema=SearchPrecedentsOutput
        )
        async def search_precedents(input_data: SearchPrecedentsInput) -> SearchPrecedentsOutput:
            """Search court decisions"""
            try:
                if isinstance(input_data, BaseModel):
                    params = input_data.model_dump()
                else:
                    params = input_data
                
                keywords = params["keywords"]
                court_type = params["court_type"]
                limit = params.get("limit", 10)
                
                # Construct query for specific courts
                court_domains = {
                    "yargitay": "yargitay.gov.tr",
                    "danistay": "danistay.gov.tr",
                    "aym": "anayasa.gov.tr"
                }
                
                domain = court_domains.get(court_type.lower(), ".gov.tr")
                query = f"site:{domain} {' '.join(keywords)}"
                
                # Use web search
                if self.tavily_api_key:
                    results = await self._search_with_tavily(query, domain, limit)
                else:
                    logger.warning("Tavily API key not set, using mock data")
                    results = []
                
                return SearchPrecedentsOutput(
                    precedents=results,
                    court_type=court_type,
                    total=len(results)
                )
                
            except Exception as e:
                logger.error(f"Precedent search error: {e}")
                return SearchPrecedentsOutput(
                    precedents=[],
                    court_type=court_type,
                    total=0
                )
    
    async def _search_with_tavily(self, query: str, domain: str, limit: int) -> List[Dict]:
        """Search using Tavily API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.tavily_url,
                    json={
                        "api_key": self.tavily_api_key,
                        "query": query,
                        "search_depth": "advanced",
                        "include_domains": [domain] if domain else [],
                        "max_results": limit
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    results = []
                    for item in data.get("results", []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "content": item.get("content", ""),
                            "score": item.get("score", 0),
                            "published_date": item.get("published_date", "")
                        })
                    
                    return results
                else:
                    logger.error(f"Tavily API error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []


# Global server instance
web_search_server = WebSearchServer()
