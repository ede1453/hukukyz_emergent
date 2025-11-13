"""Researcher Agent - Document retrieval specialist"""

from typing import List, Dict
import logging

from backend.agents.state import AgentState
from backend.retrieval.strategies import retrieval_pipeline, SearchStrategy
from backend.mcp.client.mcp_client import mcp_client

logger = logging.getLogger(__name__)


class ResearcherAgent:
    """Researcher Agent for document retrieval"""
    
    def __init__(self):
        self.retrieval = retrieval_pipeline
        self.mcp = mcp_client
    
    async def research(
        self,
        query: str,
        collections: List[str],
        filters: Dict = None,
        strategy: str = "hybrid"
    ) -> List[Dict]:
        """Execute research across collections
        
        Args:
            query: Search query
            collections: List of Qdrant collections
            filters: Metadata filters
            strategy: Search strategy
        
        Returns:
            List of retrieved documents
        """
        try:
            # Check cache first
            from backend.core.cache import cache_manager
            cached_docs = await cache_manager.get_document_cache(query, collections, limit=20)
            if cached_docs:
                logger.info(f"✅ Using cached documents: {len(cached_docs)} docs")
                return cached_docs
            
            logger.info(f"Researching: {query[:100]}...")
            logger.info(f"Collections: {collections}")
            
            all_results = []
            
            # Search each collection
            for collection in collections:
                try:
                    results = await self.retrieval.search(
                        query=query,
                        collection=collection,
                        strategy=SearchStrategy(strategy),
                        filters=filters
                    )
                    
                    # Add source collection to each result
                    for result in results:
                        result["source_collection"] = collection
                    
                    all_results.extend(results)
                    logger.info(f"Found {len(results)} docs in {collection}")
                    
                except Exception as e:
                    logger.error(f"Error searching {collection}: {e}")
                    continue
            
            # Sort all results by score
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Limit to top results
            top_results = all_results[:20]  # Keep top 20 across all collections
            
            # Cache results
            await cache_manager.set_document_cache(query, collections, top_results, limit=20)
            
            logger.info(f"Total research results: {len(top_results)}")
            return top_results
            
        except Exception as e:
            logger.error(f"Research error: {e}")
            return []
    
    async def get_article(
        self,
        kanun_adi: str,
        madde_no: int,
        fikra_no: int = None,
        bent: str = None
    ) -> Dict:
        """Get specific article using MCP tool
        
        Args:
            kanun_adi: Law name (e.g., TTK)
            madde_no: Article number
            fikra_no: Paragraph number (optional)
            bent: Subparagraph letter (optional)
        
        Returns:
            Article document
        """
        try:
            result = await self.mcp.call_tool(
                server_name="legal_documents",
                tool_name="get_article",
                params={
                    "kanun_adi": kanun_adi,
                    "madde_no": madde_no,
                    "fikra_no": fikra_no,
                    "bent": bent
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Get article error: {e}")
            return {}


# Global instance
researcher_agent = ResearcherAgent()
