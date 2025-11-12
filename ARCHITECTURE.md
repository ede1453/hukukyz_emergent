# HukukYZ - Technical Architecture

> **Version**: 1.0
> **Last Updated**: 2025-01-XX
> **Status**: Design Phase

---

## 🏗️ System Overview

**HukukYZ** is an advanced AI-powered legal assistant platform leveraging:
- **Multi-Agent Systems** for complex legal reasoning
- **RAG Pipeline** for accurate legal document retrieval
- **MCP (Model Context Protocol)** for standardized tool integration
- **Multi-Platform Support** (Web, Telegram Bot, Mobile)

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │   Web    │  │ Telegram │  │  Mobile  │                 │
│  │   App    │  │   Bot    │  │   App    │                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
└───────┼─────────────┼─────────────┼────────────────────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │      API Gateway          │
        │    (FastAPI + CORS)       │
        └─────────────┬─────────────┘
                      │
        ┌─────────────▼─────────────────────────────────┐
        │          Agent Orchestration Layer            │
        │                                               │
        │  ┌──────────────────────────────────────┐    │
        │  │      LangGraph StateGraph           │    │
        │  │  (Multi-Agent Workflow Engine)      │    │
        │  └──────────────────────────────────────┘    │
        │                                               │
        │  ┌────────┐ ┌────────┐ ┌────────┐           │
        │  │Meta-   │ │Planner │ │Research│           │
        │  │Control │ │ Agent  │ │ Agent  │  ...      │
        │  └───┬────┘ └───┬────┘ └───┬────┘           │
        └──────┼──────────┼──────────┼─────────────────┘
               │          │          │
        ┌──────▼──────────▼──────────▼─────────────────┐
        │        MCP (Model Context Protocol)          │
        │              Tool Layer                      │
        │                                              │
        │  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
        │  │ Legal   │ │Document │ │  Web    │       │
        │  │Document │ │Processor│ │ Search  │ ...   │
        │  │ Server  │ │ Server  │ │ Server  │       │
        │  └────┬────┘ └────┬────┘ └────┬────┘       │
        └───────┼───────────┼───────────┼─────────────┘
                │           │           │
        ┌───────▼───────────▼───────────▼─────────────┐
        │          Data & Storage Layer               │
        │                                             │
        │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
        │  │  Qdrant  │  │ MongoDB  │  │   Cache  │ │
        │  │ (Vector) │  │(Document)│  │  (Redis) │ │
        │  └──────────┘  └──────────┘  └──────────┘ │
        └─────────────────────────────────────────────┘
```

---

## 🧩 Component Architecture

### 1. Client Layer

#### 1.1 Web Application (React + TypeScript)
```
/frontend/
├── src/
│   ├── components/
│   │   ├── Chat/              # Chat interface
│   │   ├── Upload/            # Document upload
│   │   ├── Monitor/           # Agent activity monitor
│   │   ├── Admin/             # Admin dashboard
│   │   └── common/            # Shared components
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Chat.tsx
│   │   ├── Documents.tsx
│   │   └── Admin.tsx
│   ├── services/
│   │   ├── api.ts             # API client
│   │   ├── websocket.ts       # Real-time connection
│   │   └── auth.ts            # Authentication
│   ├── context/               # React Context
│   ├── hooks/                 # Custom hooks
│   └── utils/
```

#### 1.2 Telegram Bot
```python
# python-telegram-bot integration
Handlers:
- /start: Welcome message
- /search <query>: Legal search
- /upload: Document upload
- Message handler: Natural language queries
```

#### 1.3 Mobile App (React Native / Flutter)
```
- Cross-platform mobile client
- Features: Chat, Document scan (OCR), Offline mode
```

---

### 2. API Gateway (FastAPI)

```python
/backend/
├── main.py                    # FastAPI app
├── api/
│   ├── routes/
│   │   ├── chat.py            # Chat endpoints
│   │   ├── documents.py       # Document management
│   │   ├── upload.py          # Upload endpoints
│   │   ├── admin.py           # Admin APIs
│   │   └── auth.py            # Authentication
│   ├── middleware/
│   │   ├── auth.py            # JWT middleware
│   │   ├── rate_limit.py      # Rate limiting
│   │   └── error_handler.py   # Global error handler
│   └── schemas/               # Pydantic models
```

**Key Endpoints**:
```
POST   /api/chat/query              # Send query to agent
GET    /api/chat/stream             # SSE stream for real-time responses
POST   /api/documents/upload        # Upload legal document
GET    /api/documents/list          # List documents
POST   /api/documents/version       # Add new version
GET    /api/documents/compare       # Compare versions
GET    /api/admin/collections       # List Qdrant collections
POST   /api/admin/reindex           # Trigger reindexing
```

---

### 3. Agent Orchestration Layer

#### 3.1 LangGraph StateGraph

```python
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated

class AgentState(TypedDict):
    """Main state for agent workflow"""
    # Input
    query: str
    user_id: str
    session_id: str
    
    # Planning
    plan: list[dict]  # List of steps
    current_step_index: int
    
    # Execution
    history: list[dict]  # Past steps results
    current_findings: str
    
    # Metadata
    hukuk_dali: list[str]  # ["ticaret", "borclar"]
    kaynak_tipi: list[str]  # ["kanun", "ictihat"]
    madde_refs: list[str]   # ["TTK m.11", "TBK m.1"]
    
    # Control flow
    is_ambiguous: bool
    needs_clarification: bool
    clarification_question: str
    should_continue: bool
    
    # Output
    final_answer: str
    citations: list[dict]
    confidence: float

# Graph definition
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("gatekeeper", gatekeeper_node)
graph.add_node("meta_controller", meta_controller_node)
graph.add_node("planner", planner_node)
graph.add_node("query_optimizer", query_optimizer_node)
graph.add_node("retrieval_supervisor", retrieval_supervisor_node)
graph.add_node("researcher", researcher_node)
graph.add_node("web_scout", web_scout_node)
graph.add_node("analyst", analyst_node)
graph.add_node("auditor", auditor_node)
graph.add_node("synthesizer", synthesizer_node)
graph.add_node("reflection", reflection_node)

# Add edges
graph.set_entry_point("gatekeeper")
graph.add_conditional_edges(
    "gatekeeper",
    route_after_gate,
    {
        "clarify": END,  # Return clarification question
        "continue": "meta_controller"
    }
)
# ... more edges

app = graph.compile()
```

#### 3.2 Agent Implementations

**A. Meta-Controller Agent**
```python
Role: Task Router
Purpose: 
  - Detect legal domain (ticaret, borçlar, etc.)
  - Route to appropriate collections
  - Select specialist agents

Input: User query
Output: 
  - hukuk_dali: ["ticaret"]
  - koleksiyonlar: ["ticaret_hukuku/kanunlar"]
  - selected_agents: ["researcher", "analyst"]

Pattern: Meta-Controller Pattern
```

**B. Planner Agent**
```python
Role: Strategic Planner
Purpose:
  - Decompose complex query into steps
  - Plan tool usage
  - Create execution roadmap

Input: Optimized query + context
Output:
  plan: [
    {"step": 1, "action": "search_ttk", "tool": "researcher"},
    {"step": 2, "action": "find_precedents", "tool": "web_scout"},
    {"step": 3, "action": "analyze", "tool": "analyst"}
  ]

Pattern: Planning Pattern
```

**C. Researcher Agent (Librarian)**
```python
Role: Document Retriever
Purpose:
  - Search Qdrant collections
  - Multi-stage retrieval (vector → keyword → hybrid)
  - Cross-encoder reranking

MCP Tools:
  - search_documents(query, collection, filters)
  - get_article(kanun, madde_no)
  - get_version_history(doc_id)

Pattern: Tool Using + Multi-Stage Retrieval
```

**D. Auditor Agent**
```python
Role: Quality Controller
Purpose:
  - Verify faithfulness of findings
  - Check relevance and consistency
  - Trigger replanning if needed

Evaluation Criteria:
  - Faithfulness: Is output grounded in sources?
  - Relevance: Does it address the query?
  - Consistency: Any contradictions?
  - Legal accuracy: Correct article references?

Pattern: Reflection + Self-Correction
```

**E. Synthesizer Agent**
```python
Role: Final Answer Generator
Purpose:
  - Synthesize all findings
  - Generate causal inference
  - Format with citations

Output Format:
  {
    "answer": "...",
    "citations": [
      {"source": "TTK m.11", "text": "...", "relevance": 0.95}
    ],
    "confidence": 0.87,
    "reasoning": "..."
  }

Pattern: Synthesis with Causal Inference
```

---

### 4. MCP Tool Layer

#### 4.1 MCP Architecture

```python
# MCP Server Interface
from mcp import Server, Tool

class MCPServer:
    """Base MCP Server"""
    def __init__(self, name: str):
        self.name = name
        self.tools: list[Tool] = []
    
    def register_tool(self, tool: Tool):
        self.tools.append(tool)
    
    async def handle_request(self, tool_name: str, params: dict):
        # Route to appropriate tool
        pass
```

#### 4.2 MCP Servers

**A. Legal Document Server**
```python
Server: legal_documents
Tools:
  - search_documents(query, collection, filters, limit)
  - get_article(kanun_adi, madde_no)
  - get_document_by_id(doc_id)
  - get_version_history(doc_id)
  - get_related_articles(madde_no)

Connection: Qdrant vector DB
```

**B. Knowledge Management Server**
```python
Server: knowledge_base
Tools:
  - store_conversation(user_id, conversation)
  - retrieve_memory(user_id, context)
  - update_metadata(doc_id, metadata)
  - get_user_history(user_id)

Connection: MongoDB
```

**C. Document Processing Server**
```python
Server: document_processor
Tools:
  - parse_pdf(file_path, doc_type)
  - chunk_document(text, strategy="madde_based")
  - extract_articles(text)
  - extract_metadata(text)
  - validate_structure(doc)

Libraries: PyPDF2, pdfplumber, unstructured
```

**D. Web Search Server**
```python
Server: web_search
Tools:
  - search_legal_web(query, domain=".gov.tr")
  - search_precedents(keywords, court_type)
  - search_academic(query, source="scholar")

APIs: Tavily, SerpAPI, or custom scrapers
```

**E. Version Control Server**
```python
Server: version_control
Tools:
  - add_version(doc_id, new_version, metadata)
  - deprecate_version(doc_id, version)
  - compare_versions(doc_id, v1, v2)
  - rollback(doc_id, target_version)
  - get_active_version(doc_id)

Connection: MongoDB + Qdrant
```

#### 4.3 MCP Client Integration

```python
from langchain.tools import Tool
from mcp import MCPClient

class MCPToolWrapper:
    """Wrap MCP tools as LangChain tools"""
    def __init__(self, mcp_server_url: str):
        self.client = MCPClient(mcp_server_url)
    
    def get_langchain_tools(self) -> list[Tool]:
        """Convert MCP tools to LangChain tools"""
        tools = []
        for mcp_tool in self.client.list_tools():
            tool = Tool(
                name=mcp_tool.name,
                description=mcp_tool.description,
                func=lambda **kwargs: self.client.call_tool(
                    mcp_tool.name, kwargs
                )
            )
            tools.append(tool)
        return tools

# Usage in agents
mcp_wrapper = MCPToolWrapper("http://localhost:8080")
langchain_tools = mcp_wrapper.get_langchain_tools()

agent = create_react_agent(
    llm=llm,
    tools=langchain_tools
)
```

---

### 5. Data & Storage Layer

#### 5.1 Qdrant Vector Database

**Collection Structure**:
```python
collections = {
    "ticaret_hukuku": {
        "vectors": {"size": 1536, "distance": "Cosine"},
        "payload_schema": {
            "doc_id": "keyword",
            "doc_type": "keyword",  # kanun, yonetmelik, ictihat
            "kaynak": "keyword",    # TTK, TBK
            "madde_no": "integer",
            "fikra_no": "integer",
            "bent": "keyword",
            "content": "text",
            "summary": "text",
            "keywords": ["keyword"],
            "version": "keyword",
            "status": "keyword",    # active, deprecated
            "yururluk_tarihi": "datetime",
            "gecersiz_tarihi": "datetime"
        }
    },
    "borclar_hukuku": {...},
    "icra_iflas": {...},
    # ... other collections
}
```

**Search Strategies**:
```python
# 1. Vector Search (Semantic)
results = qdrant_client.search(
    collection_name="ticaret_hukuku",
    query_vector=embedding,
    query_filter={
        "must": [
            {"key": "status", "match": {"value": "active"}},
            {"key": "doc_type", "match": {"value": "kanun"}}
        ]
    },
    limit=20
)

# 2. Keyword Search (implemented via payload)
# 3. Hybrid (combine vector + keyword with RRF)
```

#### 5.2 MongoDB

**Collections**:
```javascript
// users
{
  _id: ObjectId,
  email: String,
  name: String,
  role: String,  // user, admin
  created_at: Date
}

// conversations
{
  _id: ObjectId,
  user_id: ObjectId,
  session_id: String,
  messages: [
    {
      role: String,  // user, assistant
      content: String,
      timestamp: Date,
      metadata: Object
    }
  ],
  created_at: Date
}

// documents (staging)
{
  _id: ObjectId,
  filename: String,
  doc_type: String,
  hukuk_dali: String,
  upload_status: String,  // pending, processing, completed, failed
  processed_chunks: Number,
  total_chunks: Number,
  error_log: String,
  created_at: Date
}

// upload_logs
{
  _id: ObjectId,
  upload_id: String,
  operation: String,  // insert, update, delete
  collection: String,
  status: String,
  details: Object,
  timestamp: Date
}

// document_versions
{
  _id: ObjectId,
  doc_id: String,
  version: String,
  status: String,  // active, deprecated, superseded
  replaces: String,  // previous version
  metadata: Object,
  created_at: Date
}
```

#### 5.3 Redis Cache (Optional)

```python
# Cache frequently accessed data
cache_keys = {
    f"article:{kanun}:{madde}": "Article content",
    f"query_result:{query_hash}": "Search results",
    f"embedding:{text_hash}": "Embedding vector"
}

TTL = 3600  # 1 hour
```

---

## 🔄 Data Flow

### Scenario 1: User Query

```
1. User sends query: "TTK 11. maddeye göre ticaret şirketlerinin kuruluşu"
   ↓
2. API Gateway → Agent Orchestration
   ↓
3. Gatekeeper: Check ambiguity (✓ Clear)
   ↓
4. Meta-Controller:
   - Detect: hukuk_dali = "ticaret"
   - Select: collection = "ticaret_hukuku/kanunlar"
   ↓
5. Planner:
   - Step 1: Search TTK m.11
   - Step 2: Find related precedents
   - Step 3: Synthesize answer
   ↓
6. Query Optimizer:
   - Extract: kanun="TTK", madde=11
   - Optimize: "Türk Ticaret Kanunu 11. madde ticari şirket kuruluşu"
   ↓
7. Retrieval Supervisor: Select strategy = "hybrid"
   ↓
8. Researcher Agent → MCP Legal Document Server:
   - search_documents(query, collection="ticaret_hukuku")
   - get_article(kanun="TTK", madde_no=11)
   ↓
9. Qdrant:
   - Vector search + Keyword search
   - Cross-encoder reranking
   - Return top 5 chunks
   ↓
10. Web Scout Agent → MCP Web Search Server:
    - search_precedents(keywords=["TTK", "madde 11", "kuruluş"])
    ↓
11. Analyst Agent:
    - Analyze findings
    - Cross-reference articles
    ↓
12. Auditor Agent:
    - Verify faithfulness ✓
    - Check relevance ✓
    ↓
13. Synthesizer Agent:
    - Generate final answer with citations
    ↓
14. API Gateway → Client:
    - Stream response via SSE
    - Return formatted answer
```

### Scenario 2: Document Upload

```
1. User uploads PDF: "yeni_ttk_2024.pdf"
   ↓
2. API Gateway → Upload Pipeline
   ↓
3. Staging (MongoDB):
   - Create upload record: status="pending"
   ↓
4. MCP Document Processor Server:
   - parse_pdf(file_path)
   - extract_articles(text)
   - chunk_document(text, strategy="madde_based")
   - extract_metadata(text)
   ↓
5. Validation:
   - Check structure ✓
   - Validate metadata ✓
   ↓
6. Shadow Collection (Qdrant):
   - Create temp collection: "ticaret_temp"
   - Generate embeddings (OpenAI)
   - Upload to shadow collection
   ↓
7. Test Search:
   - Run sample queries
   - Verify results ✓
   ↓
8. Merge Strategy:
   - If new document: Upsert to main collection
   - If update: Add new version, deprecate old
   ↓
9. Version Control:
   - Update document_versions in MongoDB
   - Set old version status="deprecated"
   ↓
10. Cleanup:
    - Delete shadow collection
    - Update upload status="completed"
    ↓
11. Notify user: Upload successful ✓
```

---

## 🔐 Security & Authentication

### Authentication
```python
# JWT-based authentication
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    token = credentials.credentials
    # Verify JWT
    user = decode_jwt(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

# Protected route
@app.post("/api/chat/query")
async def query(request: QueryRequest, user = Depends(verify_token)):
    # Process query
    pass
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat/query")
@limiter.limit("10/minute")
async def query(request: QueryRequest):
    pass
```

### Data Privacy
```
- User conversations encrypted at rest
- PII data anonymization
- GDPR compliance (data deletion requests)
- Audit logs for admin actions
```

---

## 📊 Monitoring & Observability

### Metrics
```python
from prometheus_client import Counter, Histogram

query_counter = Counter('queries_total', 'Total queries')
query_duration = Histogram('query_duration_seconds', 'Query duration')
token_usage = Counter('tokens_used_total', 'Total tokens used')
```

### Logging
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "query_processed",
    user_id=user_id,
    query=query,
    duration=duration,
    tokens=tokens
)
```

### Alerting
```yaml
alerts:
  - name: HighErrorRate
    condition: error_rate > 5%
    action: notify_slack
  
  - name: SlowQueries
    condition: p95_latency > 10s
    action: notify_email
```

---

## 🚀 Deployment Architecture

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hukukyz-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: hukukyz/backend:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
---
apiVersion: v1
kind: Service
metadata:
  name: hukukyz-backend
spec:
  type: LoadBalancer
  ports:
  - port: 8001
```

### Scaling Strategy
```
- Horizontal Pod Autoscaling (HPA)
- Target: CPU 70%, Memory 80%
- Min replicas: 2
- Max replicas: 10
```

---

## 📈 Performance Optimization

### Caching
```
- Embedding cache (Redis)
- Query result cache (15min TTL)
- Article content cache (1 hour TTL)
```

### Database Optimization
```
- Qdrant: HNSW index for fast vector search
- MongoDB: Indexes on user_id, session_id, timestamp
- Connection pooling
```

### Async Processing
```python
- FastAPI async routes
- Async DB operations (motor, qdrant-async)
- Background tasks for uploads
```

---

## 🔮 Future Enhancements

1. **Graph Memory**: Neo4j for legal knowledge graph
2. **Multi-Modal**: Vision for document images
3. **Voice Interface**: Speech-to-text integration
4. **Collaborative Features**: Team workspaces
5. **Export Options**: PDF reports, citations export
6. **Advanced Analytics**: Usage patterns, popular queries
7. **Fine-tuned Models**: Domain-specific Turkish legal LLM

---

**End of Architecture Document**
