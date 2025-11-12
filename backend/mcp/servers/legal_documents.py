"""Legal Documents MCP Server - Interface with Qdrant vector database"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import logging

from backend.mcp.base import MCPServer
from backend.database.qdrant_client import qdrant_manager
from backend.utils.embeddings import get_embedding

logger = logging.getLogger(__name__)


# Input/Output Schemas
class SearchDocumentsInput(BaseModel):
    """Input for search_documents tool"""
    query: str = Field(description="Search query")
    collection: str = Field(description="Qdrant collection name")
    filters: Optional[Dict] = Field(default=None, description="Metadata filters")
    limit: int = Field(default=10, description="Number of results")
    strategy: str = Field(default="hybrid", description="Search strategy: vector, keyword, or hybrid")


class SearchDocumentsOutput(BaseModel):
    """Output for search_documents tool"""
    results: List[Dict]
    total: int
    search_strategy: str


class GetArticleInput(BaseModel):
    """Input for get_article tool"""
    kanun_adi: str = Field(description="Law name (e.g., TTK, TBK)")
    madde_no: int = Field(description="Article number")
    fikra_no: Optional[int] = Field(default=None, description="Paragraph number")
    bent: Optional[str] = Field(default=None, description="Subparagraph letter")
    version: str = Field(default="latest", description="Version")


class GetArticleOutput(BaseModel):
    """Output for get_article tool"""
    content: str
    metadata: Dict
    version: str
    status: str


class LegalDocumentServer(MCPServer):
    """MCP Server for legal document operations"""
    
    def __init__(self):
        super().__init__(name="legal_documents", version="1.0.0")
        self.qdrant = qdrant_manager
        
        # Mapping from law abbreviation to collection
        self.kanun_to_collection = {
            "TTK": "ticaret_hukuku",
            "TBK": "borclar_hukuku",
            "İİK": "icra_iflas",
            "TMK": "medeni_hukuk",
            "TKHK": "tuketici_haklari",
            "BK": "bankacilik_hukuku",
            "HMK": "hmk"
        }
    
    async def initialize(self):
        """Initialize server"""
        logger.info("Legal Documents Server initialized")
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools"""
        
        @self.tool(
            name="search_documents",
            description="Search for legal documents using semantic/keyword/hybrid search",
            input_schema=SearchDocumentsInput,
            output_schema=SearchDocumentsOutput
        )
        async def search_documents(input_data: SearchDocumentsInput) -> SearchDocumentsOutput:
            """Search documents in Qdrant"""
            try:
                # Convert input to dict if it's a Pydantic model
                if isinstance(input_data, BaseModel):
                    params = input_data.model_dump()
                else:
                    params = input_data
                
                query = params["query"]
                collection = params["collection"]
                filters = params.get("filters")
                limit = params.get("limit", 10)
                strategy = params.get("strategy", "hybrid")
                
                # Generate embedding for query
                query_vector = await get_embedding(query)
                
                # Search based on strategy
                if strategy == "vector":
                    results = self.qdrant.search(
                        collection_name=collection,
                        query_vector=query_vector,
                        limit=limit,
                        filters=filters
                    )
                elif strategy == "keyword":
                    # For keyword search, we'll use scroll with payload filter
                    # (Qdrant doesn't have native keyword search, this is a placeholder)
                    results = self.qdrant.search(
                        collection_name=collection,
                        query_vector=query_vector,
                        limit=limit,
                        filters=filters
                    )
                else:  # hybrid
                    results = self.qdrant.search(
                        collection_name=collection,
                        query_vector=query_vector,
                        limit=limit,
                        filters=filters
                    )
                
                return SearchDocumentsOutput(
                    results=results,
                    total=len(results),
                    search_strategy=strategy
                )
                
            except Exception as e:
                logger.error(f"Search error: {e}")
                return SearchDocumentsOutput(
                    results=[],
                    total=0,
                    search_strategy=strategy
                )
        
        @self.tool(
            name="get_article",
            description="Get specific article from a legal document",
            input_schema=GetArticleInput,
            output_schema=GetArticleOutput
        )
        async def get_article(input_data: GetArticleInput) -> GetArticleOutput:
            """Retrieve specific article"""
            try:
                if isinstance(input_data, BaseModel):
                    params = input_data.model_dump()
                else:
                    params = input_data
                
                kanun_adi = params["kanun_adi"]
                madde_no = params["madde_no"]
                fikra_no = params.get("fikra_no")
                bent = params.get("bent")
                
                # Map law to collection
                collection = self.kanun_to_collection.get(kanun_adi, "genel")
                
                # Build filter
                filters = {
                    "kaynak": kanun_adi,
                    "madde_no": madde_no,
                    "status": "active"
                }
                
                if fikra_no:
                    filters["fikra_no"] = fikra_no
                if bent:
                    filters["bent"] = bent
                
                # Search with embedding (using a generic query)
                query_text = f"{kanun_adi} madde {madde_no}"
                query_vector = await get_embedding(query_text)
                
                results = self.qdrant.search(
                    collection_name=collection,
                    query_vector=query_vector,
                    limit=1,
                    filters=filters
                )
                
                if not results:
                    raise ValueError(f"Article not found: {kanun_adi} m.{madde_no}")
                
                doc = results[0]
                payload = doc["payload"]
                
                return GetArticleOutput(
                    content=payload.get("content", ""),
                    metadata=payload,
                    version=payload.get("version", "unknown"),
                    status=payload.get("status", "unknown")
                )
                
            except Exception as e:
                logger.error(f"Get article error: {e}")
                raise


# Global server instance
legal_document_server = LegalDocumentServer()
