"""Web Scout Agent - Live web search for legal precedents"""

from typing import List, Dict
import logging

from backend.mcp.client.mcp_client import mcp_client

logger = logging.getLogger(__name__)


class WebScoutAgent:
    """Web Scout Agent for searching legal precedents online"""
    
    def __init__(self):
        self.mcp = mcp_client
    
    async def search_precedents(
        self,
        keywords: List[str],
        court_type: str = "yargitay",
        limit: int = 10
    ) -> List[Dict]:
        """Search for legal precedents
        
        Args:
            keywords: Search keywords
            court_type: Court type (yargitay, danistay, aym)
            limit: Number of results
        
        Returns:
            List of precedent documents
        """
        try:
            logger.info(f"Searching {court_type} precedents: {keywords}")
            
            result = await self.mcp.call_tool(
                server_name="web_search",
                tool_name="search_precedents",
                params={
                    "keywords": keywords,
                    "court_type": court_type,
                    "limit": limit
                }
            )
            
            precedents = result.get("precedents", [])
            logger.info(f"Found {len(precedents)} precedents")
            
            return precedents
            
        except Exception as e:
            logger.error(f"Precedent search error: {e}")
            return []
    
    async def search_web(
        self,
        query: str,
        domain: str = ".gov.tr",
        limit: int = 10
    ) -> List[Dict]:
        """General web search for legal information
        
        Args:
            query: Search query
            domain: Domain filter
            limit: Number of results
        
        Returns:
            List of web results
        """
        try:
            logger.info(f"Web search: {query[:100]}...")
            
            result = await self.mcp.call_tool(
                server_name="web_search",
                tool_name="search_legal_web",
                params={
                    "query": query,
                    "domain": domain,
                    "limit": limit
                }
            )
            
            results = result.get("results", [])
            logger.info(f"Found {len(results)} web results")
            
            return results
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []


# Global instance
web_scout_agent = WebScoutAgent()
