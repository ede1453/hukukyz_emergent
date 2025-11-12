# MCP (Model Context Protocol) Integration Guide

> **Version**: 1.0
> **Last Updated**: 2025-01-XX
> **Purpose**: Detailed MCP implementation for HukukYZ

---

## 🎯 What is MCP?

**Model Context Protocol (MCP)** is a standardized protocol for connecting AI models with external tools and data sources. It provides:

- **Standardized Interface**: Consistent API for tool interaction
- **Type Safety**: Strong typing with Pydantic models
- **Security**: Built-in authentication and authorization
- **Discoverability**: Tools are self-describing
- **Versioning**: Backward-compatible tool evolution

---

## 🏗️ MCP Architecture in HukukYZ

```
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agents                     │
│  (Meta-Controller, Planner, Researcher, Analyst, etc.)  │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ LangChain Tool Interface
                     │
┌────────────────────▼────────────────────────────────────┐
│               MCP Client (Tool Wrapper)                 │
│  - Tool Discovery                                       │
│  - Request Routing                                      │
│  - Response Handling                                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP/gRPC
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Legal   │    │Document │    │  Web    │
│Document │    │Processor│    │ Search  │
│ Server  │    │ Server  │    │ Server  │
└────┬────┘    └────┬────┘    └────┬────┘
     │              │              │
     ▼              ▼              ▼
  Qdrant        PyPDF2        Tavily API
```

---

## 📦 MCP Server Implementations

### 1. Legal Document Server

**Purpose**: Interface with Qdrant vector database for legal document retrieval

```python
# /app/backend/mcp/servers/legal_documents.py

from mcp import Server, Tool
from pydantic import BaseModel, Field
from typing import List, Optional
from qdrant_client import QdrantClient

class SearchDocumentsInput(BaseModel):
    """Input for search_documents tool"""
    query: str = Field(description="Search query")
    collection: str = Field(description="Qdrant collection name")
    filters: Optional[dict] = Field(default=None, description="Metadata filters")
    limit: int = Field(default=10, description="Number of results")
    strategy: str = Field(default="hybrid", description="vector, keyword, or hybrid")

class SearchDocumentsOutput(BaseModel):
    """Output for search_documents tool"""
    results: List[dict]
    total: int
    search_strategy: str

class GetArticleInput(BaseModel):
    """Input for get_article tool"""
    kanun_adi: str = Field(description="Law name (e.g., TTK, TBK)")
    madde_no: int = Field(description="Article number")
    fikra_no: Optional[int] = Field(default=None, description="Paragraph number")
    bent: Optional[str] = Field(default=None, description="Subparagraph letter")
    version: Optional[str] = Field(default="latest", description="Version")

class GetArticleOutput(BaseModel):
    """Output for get_article tool"""
    content: str
    metadata: dict
    version: str
    status: str

class LegalDocumentServer(Server):
    """MCP Server for legal document operations"""
    
    def __init__(self, qdrant_client: QdrantClient):
        super().__init__(name="legal_documents", version="1.0.0")
        self.qdrant = qdrant_client
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools"""
        
        @self.tool(
            name="search_documents",
            description="Search for legal documents using semantic/keyword/hybrid search",
            input_schema=SearchDocumentsInput,
            output_schema=SearchDocumentsOutput
        )
        async def search_documents(input: SearchDocumentsInput) -> SearchDocumentsOutput:
            """Search documents in Qdrant"""
            if input.strategy == "vector":
                results = await self._vector_search(input)
            elif input.strategy == "keyword":
                results = await self._keyword_search(input)
            else:
                results = await self._hybrid_search(input)
            
            return SearchDocumentsOutput(
                results=results,
                total=len(results),
                search_strategy=input.strategy
            )
        
        @self.tool(
            name="get_article",
            description="Get specific article from a legal document",
            input_schema=GetArticleInput,
            output_schema=GetArticleOutput
        )
        async def get_article(input: GetArticleInput) -> GetArticleOutput:
            """Retrieve specific article"""
            # Build filter
            filters = {
                "must": [
                    {"key": "kaynak", "match": {"value": input.kanun_adi}},
                    {"key": "madde_no", "match": {"value": input.madde_no}},
                    {"key": "status", "match": {"value": "active"}}
                ]
            }
            
            if input.fikra_no:
                filters["must"].append(
                    {"key": "fikra_no", "match": {"value": input.fikra_no}}
                )
            
            if input.bent:
                filters["must"].append(
                    {"key": "bent", "match": {"value": input.bent}}
                )
            
            # Search in appropriate collection
            collection = self._map_kanun_to_collection(input.kanun_adi)
            results = self.qdrant.scroll(
                collection_name=collection,
                scroll_filter=filters,
                limit=1
            )
            
            if not results[0]:
                raise ValueError(f"Article not found: {input.kanun_adi} m.{input.madde_no}")
            
            doc = results[0][0]
            return GetArticleOutput(
                content=doc.payload["content"],
                metadata=doc.payload,
                version=doc.payload.get("version", "unknown"),
                status=doc.payload.get("status", "unknown")
            )
        
        @self.tool(
            name="get_version_history",
            description="Get version history of a legal document",
            input_schema=dict,
            output_schema=dict
        )
        async def get_version_history(doc_id: str) -> dict:
            """Get all versions of a document"""
            # Query all versions (including deprecated)
            filters = {
                "must": [
                    {"key": "doc_id", "match": {"value": doc_id}}
                ]
            }
            
            results = self.qdrant.scroll(
                collection_name="all_collections",
                scroll_filter=filters,
                limit=100
            )
            
            versions = []
            for doc in results[0]:
                versions.append({
                    "version": doc.payload["version"],
                    "status": doc.payload["status"],
                    "yururluk_tarihi": doc.payload.get("yururluk_tarihi"),
                    "gecersiz_tarihi": doc.payload.get("gecersiz_tarihi"),
                    "replaces": doc.payload.get("replaces")
                })
            
            return {
                "doc_id": doc_id,
                "versions": versions,
                "total_versions": len(versions)
            }
    
    def _map_kanun_to_collection(self, kanun_adi: str) -> str:
        """Map law name to Qdrant collection"""
        mapping = {
            "TTK": "ticaret_hukuku",
            "TBK": "borclar_hukuku",
            "İİK": "icra_iflas",
            "TMK": "medeni_hukuk",
            "TKHK": "tuketici_haklari",
            "BK": "bankacilik_hukuku",
            "HMK": "hmk"
        }
        return mapping.get(kanun_adi, "genel")
    
    async def _vector_search(self, input: SearchDocumentsInput) -> List[dict]:
        """Vector similarity search"""
        # Implementation
        pass
    
    async def _keyword_search(self, input: SearchDocumentsInput) -> List[dict]:
        """BM25 keyword search"""
        # Implementation
        pass
    
    async def _hybrid_search(self, input: SearchDocumentsInput) -> List[dict]:
        """Hybrid search with RRF"""
        # Implementation
        pass
```

---

### 2. Document Processing Server

```python
# /app/backend/mcp/servers/document_processor.py

from mcp import Server, Tool
from pydantic import BaseModel, Field
from typing import List, Dict
import PyPDF2
import re

class ParsePDFInput(BaseModel):
    file_path: str = Field(description="Path to PDF file")
    doc_type: str = Field(description="kanun, yonetmelik, ictihat, etc.")
    hukuk_dali: str = Field(description="Legal domain")

class ParsePDFOutput(BaseModel):
    text: str
    metadata: dict
    page_count: int
    extracted_articles: List[dict]

class ChunkDocumentInput(BaseModel):
    text: str
    strategy: str = Field(default="madde_based", description="Chunking strategy")
    chunk_size: int = Field(default=1000, description="Max chunk size")
    overlap: int = Field(default=100, description="Chunk overlap")

class ChunkDocumentOutput(BaseModel):
    chunks: List[dict]
    total_chunks: int

class DocumentProcessorServer(Server):
    """MCP Server for document processing"""
    
    def __init__(self):
        super().__init__(name="document_processor", version="1.0.0")
        self._register_tools()
    
    def _register_tools(self):
        
        @self.tool(
            name="parse_pdf",
            description="Parse PDF and extract text and metadata",
            input_schema=ParsePDFInput,
            output_schema=ParsePDFOutput
        )
        async def parse_pdf(input: ParsePDFInput) -> ParsePDFOutput:
            """Parse PDF document"""
            with open(input.file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                
                # Extract metadata
                metadata = {
                    "title": reader.metadata.get('/Title', ''),
                    "author": reader.metadata.get('/Author', ''),
                    "subject": reader.metadata.get('/Subject', ''),
                    "doc_type": input.doc_type,
                    "hukuk_dali": input.hukuk_dali
                }
                
                # Extract articles
                articles = self._extract_articles_from_text(text, input.doc_type)
                
                return ParsePDFOutput(
                    text=text,
                    metadata=metadata,
                    page_count=len(reader.pages),
                    extracted_articles=articles
                )
        
        @self.tool(
            name="chunk_document",
            description="Chunk document into smaller pieces",
            input_schema=ChunkDocumentInput,
            output_schema=ChunkDocumentOutput
        )
        async def chunk_document(input: ChunkDocumentInput) -> ChunkDocumentOutput:
            """Chunk document based on strategy"""
            if input.strategy == "madde_based":
                chunks = self._chunk_by_madde(input.text)
            elif input.strategy == "semantic":
                chunks = self._chunk_semantic(input.text, input.chunk_size, input.overlap)
            else:
                chunks = self._chunk_recursive(input.text, input.chunk_size, input.overlap)
            
            return ChunkDocumentOutput(
                chunks=chunks,
                total_chunks=len(chunks)
            )
        
        @self.tool(
            name="extract_articles",
            description="Extract articles (madde) from legal text",
            input_schema=dict,
            output_schema=dict
        )
        async def extract_articles(text: str, doc_type: str) -> dict:
            """Extract structured articles"""
            return {
                "articles": self._extract_articles_from_text(text, doc_type)
            }
        
        @self.tool(
            name="extract_metadata",
            description="Extract metadata from legal document",
            input_schema=dict,
            output_schema=dict
        )
        async def extract_metadata(text: str) -> dict:
            """Extract metadata using regex and NLP"""
            metadata = {}
            
            # Extract law name
            law_pattern = r"(TÜRK\s+\w+\s+KANUNU|\d+\s+SAYILI\s+KANUN)"
            law_match = re.search(law_pattern, text)
            if law_match:
                metadata["kanun_adi"] = law_match.group(1)
            
            # Extract date
            date_pattern = r"(\d{1,2}[./]\d{1,2}[./]\d{4})"
            date_match = re.search(date_pattern, text)
            if date_match:
                metadata["tarih"] = date_match.group(1)
            
            # Extract number
            number_pattern = r"Kanun Numarası\s*:\s*(\d+)"
            number_match = re.search(number_pattern, text)
            if number_match:
                metadata["kanun_no"] = number_match.group(1)
            
            return metadata
    
    def _extract_articles_from_text(self, text: str, doc_type: str) -> List[dict]:
        """Extract articles with regex patterns"""
        articles = []
        
        if doc_type == "kanun":
            # Pattern: "MADDE 1-" or "Madde 1 –"
            pattern = r"(?:MADDE|Madde)\s+(\d+)\s*[–-]\s*([^(?:MADDE|Madde)]+)"
            matches = re.finditer(pattern, text, re.DOTALL)
            
            for match in matches:
                madde_no = int(match.group(1))
                content = match.group(2).strip()
                
                articles.append({
                    "madde_no": madde_no,
                    "content": content,
                    "fikralar": self._extract_fikralar(content)
                })
        
        return articles
    
    def _extract_fikralar(self, content: str) -> List[dict]:
        """Extract paragraphs (fıkra) from article content"""
        # Pattern: "(1)", "(2)", etc.
        pattern = r"\((\d+)\)\s*([^(]+)"
        matches = re.finditer(pattern, content)
        
        fikralar = []
        for match in matches:
            fikra_no = int(match.group(1))
            text = match.group(2).strip()
            
            fikralar.append({
                "fikra_no": fikra_no,
                "text": text,
                "bentler": self._extract_bentler(text)
            })
        
        return fikralar
    
    def _extract_bentler(self, text: str) -> List[dict]:
        """Extract subparagraphs (bent) from paragraph"""
        # Pattern: "a)", "b)", etc.
        pattern = r"([a-z])\)\s*([^a-z)]+)"
        matches = re.finditer(pattern, text)
        
        bentler = []
        for match in matches:
            bent = match.group(1)
            text = match.group(2).strip()
            
            bentler.append({
                "bent": bent,
                "text": text
            })
        
        return bentler
    
    def _chunk_by_madde(self, text: str) -> List[dict]:
        """Chunk by article (madde)"""
        articles = self._extract_articles_from_text(text, "kanun")
        chunks = []
        
        for article in articles:
            chunks.append({
                "content": article["content"],
                "metadata": {
                    "madde_no": article["madde_no"],
                    "chunk_type": "madde"
                }
            })
        
        return chunks
    
    def _chunk_semantic(self, text: str, chunk_size: int, overlap: int) -> List[dict]:
        """Semantic-aware chunking"""
        # Use sentence tokenization and semantic boundaries
        # Implementation
        pass
    
    def _chunk_recursive(self, text: str, chunk_size: int, overlap: int) -> List[dict]:
        """Recursive character-based chunking"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        chunks = splitter.split_text(text)
        return [{"content": chunk, "metadata": {}} for chunk in chunks]
```

---

### 3. Web Search Server

```python
# /app/backend/mcp/servers/web_search.py

from mcp import Server, Tool
from pydantic import BaseModel, Field
from typing import List
import httpx

class SearchLegalWebInput(BaseModel):
    query: str = Field(description="Search query")
    domain: str = Field(default=".gov.tr", description="Domain filter")
    limit: int = Field(default=10, description="Number of results")

class SearchLegalWebOutput(BaseModel):
    results: List[dict]
    total: int

class WebSearchServer(Server):
    """MCP Server for web search"""
    
    def __init__(self, tavily_api_key: str):
        super().__init__(name="web_search", version="1.0.0")
        self.api_key = tavily_api_key
        self._register_tools()
    
    def _register_tools(self):
        
        @self.tool(
            name="search_legal_web",
            description="Search Turkish legal websites",
            input_schema=SearchLegalWebInput,
            output_schema=SearchLegalWebOutput
        )
        async def search_legal_web(input: SearchLegalWebInput) -> SearchLegalWebOutput:
            """Search web for legal information"""
            # Use Tavily API
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.api_key,
                        "query": input.query,
                        "search_depth": "advanced",
                        "include_domains": [input.domain],
                        "max_results": input.limit
                    }
                )
                data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item["title"],
                    "url": item["url"],
                    "content": item["content"],
                    "score": item.get("score", 0)
                })
            
            return SearchLegalWebOutput(
                results=results,
                total=len(results)
            )
        
        @self.tool(
            name="search_precedents",
            description="Search for legal precedents (içtihat)",
            input_schema=dict,
            output_schema=dict
        )
        async def search_precedents(keywords: List[str], court_type: str) -> dict:
            """Search court decisions"""
            # Construct query for specific courts
            queries = {
                "yargitay": f"site:yargitay.gov.tr {' '.join(keywords)}",
                "danistay": f"site:danistay.gov.tr {' '.join(keywords)}",
                "aym": f"site:anayasa.gov.tr {' '.join(keywords)}"
            }
            
            query = queries.get(court_type.lower(), ' '.join(keywords))
            
            # Use search_legal_web
            result = await search_legal_web(
                SearchLegalWebInput(query=query, domain=".gov.tr", limit=10)
            )
            
            return {
                "precedents": result.results,
                "court_type": court_type
            }
```

---

### 4. Version Control Server

```python
# /app/backend/mcp/servers/version_control.py

from mcp import Server, Tool
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class AddVersionInput(BaseModel):
    doc_id: str
    new_version: str
    content: str
    metadata: dict
    replaces: Optional[str] = None
    yururluk_tarihi: Optional[str] = None

class AddVersionOutput(BaseModel):
    success: bool
    new_doc_id: str
    version: str
    previous_version_status: str

class VersionControlServer(Server):
    """MCP Server for document versioning"""
    
    def __init__(self, qdrant_client, mongo_client):
        super().__init__(name="version_control", version="1.0.0")
        self.qdrant = qdrant_client
        self.mongo = mongo_client
        self._register_tools()
    
    def _register_tools(self):
        
        @self.tool(
            name="add_version",
            description="Add new version of a legal document",
            input_schema=AddVersionInput,
            output_schema=AddVersionOutput
        )
        async def add_version(input: AddVersionInput) -> AddVersionOutput:
            """Add new document version"""
            new_doc_id = f"{input.doc_id}_{input.new_version}"
            
            # 1. Mark old version as deprecated
            if input.replaces:
                await self._deprecate_version(input.replaces)
            
            # 2. Insert new version to Qdrant
            # (Embedding generation and upload logic)
            
            # 3. Log to MongoDB
            await self.mongo.document_versions.insert_one({
                "doc_id": new_doc_id,
                "original_doc_id": input.doc_id,
                "version": input.new_version,
                "status": "active",
                "replaces": input.replaces,
                "yururluk_tarihi": input.yururluk_tarihi,
                "created_at": datetime.utcnow(),
                "metadata": input.metadata
            })
            
            return AddVersionOutput(
                success=True,
                new_doc_id=new_doc_id,
                version=input.new_version,
                previous_version_status="deprecated"
            )
        
        @self.tool(
            name="compare_versions",
            description="Compare two versions of a document",
            input_schema=dict,
            output_schema=dict
        )
        async def compare_versions(doc_id: str, v1: str, v2: str) -> dict:
            """Compare two versions"""
            # Fetch both versions
            # Generate diff
            # Return comparison
            pass
        
        @self.tool(
            name="get_active_version",
            description="Get currently active version of a document",
            input_schema=dict,
            output_schema=dict
        )
        async def get_active_version(doc_id: str) -> dict:
            """Get active version"""
            version = await self.mongo.document_versions.find_one({
                "original_doc_id": doc_id,
                "status": "active"
            })
            
            return version
    
    async def _deprecate_version(self, doc_id: str):
        """Mark version as deprecated"""
        await self.mongo.document_versions.update_one(
            {"doc_id": doc_id},
            {"$set": {"status": "deprecated", "deprecated_at": datetime.utcnow()}}
        )
        
        # Update Qdrant metadata
        # (Update status field in vector store)
```

---

## 🔌 MCP Client Integration

### LangChain Tool Wrapper

```python
# /app/backend/mcp/client.py

from typing import List, Dict, Any
from langchain.tools import Tool
from pydantic import BaseModel
import httpx

class MCPClient:
    """Client for interacting with MCP servers"""
    
    def __init__(self, server_urls: Dict[str, str]):
        """
        Args:
            server_urls: Dict mapping server names to URLs
                e.g., {"legal_documents": "http://localhost:8080"}
        """
        self.server_urls = server_urls
        self.tools_cache: Dict[str, List[dict]] = {}
    
    async def discover_tools(self, server_name: str) -> List[dict]:
        """Discover available tools from a server"""
        if server_name in self.tools_cache:
            return self.tools_cache[server_name]
        
        url = self.server_urls[server_name]
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/tools")
            tools = response.json()["tools"]
        
        self.tools_cache[server_name] = tools
        return tools
    
    async def call_tool(self, server_name: str, tool_name: str, params: dict) -> Any:
        """Call a tool on a specific server"""
        url = self.server_urls[server_name]
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{url}/tools/{tool_name}",
                json=params
            )
            return response.json()
    
    async def get_langchain_tools(self, server_name: str = None) -> List[Tool]:
        """Convert MCP tools to LangChain tools"""
        langchain_tools = []
        
        servers = [server_name] if server_name else self.server_urls.keys()
        
        for srv in servers:
            mcp_tools = await self.discover_tools(srv)
            
            for mcp_tool in mcp_tools:
                # Create LangChain tool
                tool = Tool(
                    name=mcp_tool["name"],
                    description=mcp_tool["description"],
                    func=self._create_tool_func(srv, mcp_tool["name"]),
                    args_schema=self._create_args_schema(mcp_tool["input_schema"])
                )
                langchain_tools.append(tool)
        
        return langchain_tools
    
    def _create_tool_func(self, server_name: str, tool_name: str):
        """Create callable function for LangChain tool"""
        async def tool_func(**kwargs):
            return await self.call_tool(server_name, tool_name, kwargs)
        return tool_func
    
    def _create_args_schema(self, input_schema: dict) -> BaseModel:
        """Create Pydantic model from MCP input schema"""
        # Dynamic Pydantic model creation
        # Implementation
        pass


# Usage Example
# /app/backend/agents/tools.py

from backend.mcp.client import MCPClient

# Initialize MCP client
mcp_client = MCPClient({
    "legal_documents": "http://localhost:8080",
    "document_processor": "http://localhost:8081",
    "web_search": "http://localhost:8082",
    "version_control": "http://localhost:8083"
})

# Get all LangChain tools
tools = await mcp_client.get_langchain_tools()

# Use in agent
from langchain.agents import create_react_agent
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
```

---

## 🚀 Deployment

### Docker Compose for MCP Servers

```yaml
# docker-compose.mcp.yml

version: '3.8'

services:
  legal-documents-server:
    build:
      context: ./backend/mcp/servers
      dockerfile: Dockerfile.legal_documents
    ports:
      - "8080:8080"
    environment:
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - qdrant
  
  document-processor-server:
    build:
      context: ./backend/mcp/servers
      dockerfile: Dockerfile.document_processor
    ports:
      - "8081:8081"
  
  web-search-server:
    build:
      context: ./backend/mcp/servers
      dockerfile: Dockerfile.web_search
    ports:
      - "8082:8082"
    environment:
      - TAVILY_API_KEY=${TAVILY_API_KEY}
  
  version-control-server:
    build:
      context: ./backend/mcp/servers
      dockerfile: Dockerfile.version_control
    ports:
      - "8083:8083"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - MONGO_URL=mongodb://mongodb:27017
    depends_on:
      - qdrant
      - mongodb
  
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
  
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

volumes:
  qdrant_data:
  mongo_data:
```

---

## 📊 Monitoring MCP Servers

### Health Checks

```python
# Each MCP server implements health endpoint

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "server": "legal_documents",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Metrics

```python
from prometheus_client import Counter, Histogram

tool_calls = Counter('mcp_tool_calls_total', 'Total tool calls', ['server', 'tool'])
tool_duration = Histogram('mcp_tool_duration_seconds', 'Tool duration', ['server', 'tool'])
tool_errors = Counter('mcp_tool_errors_total', 'Tool errors', ['server', 'tool', 'error_type'])
```

---

## 🔐 Security

### Authentication

```python
# API Key authentication for MCP servers

from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    api_key = credentials.credentials
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, params: dict, api_key = Depends(verify_api_key)):
    # Execute tool
    pass
```

---

## ✅ Benefits of MCP in HukukYZ

1. **Modularity**: Each server is independent and can be developed/deployed separately
2. **Scalability**: Scale individual servers based on load
3. **Maintainability**: Clear separation of concerns
4. **Testing**: Easy to test and mock individual tools
5. **Discoverability**: Agents can discover available tools dynamically
6. **Type Safety**: Strong typing with Pydantic
7. **Versioning**: Backward-compatible tool evolution
8. **Security**: Centralized authentication and authorization

---

**End of MCP Integration Guide**
