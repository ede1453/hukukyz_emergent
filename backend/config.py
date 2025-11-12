"""Configuration management for HukukYZ backend"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    app_name: str = "HukukYZ"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # API
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8001"))
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # LLM
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0"))
    
    # Embeddings
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    
    # Databases
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    
    mongo_url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name: str = os.getenv("DB_NAME", "hukukyz_db")
    
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # MCP Servers
    mcp_legal_documents_url: str = os.getenv("MCP_LEGAL_DOCUMENTS_URL", "http://localhost:8080")
    mcp_document_processor_url: str = os.getenv("MCP_DOCUMENT_PROCESSOR_URL", "http://localhost:8081")
    mcp_web_search_url: str = os.getenv("MCP_WEB_SEARCH_URL", "http://localhost:8082")
    mcp_version_control_url: str = os.getenv("MCP_VERSION_CONTROL_URL", "http://localhost:8083")
    
    # External APIs
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # Retrieval Config
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "20"))
    rerank_top_k: int = int(os.getenv("RERANK_TOP_K", "5"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    
    # Agent Config
    max_agent_iterations: int = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))
    agent_timeout: int = int(os.getenv("AGENT_TIMEOUT", "300"))
    
    # Cache
    cache_ttl_embeddings: int = int(os.getenv("CACHE_TTL_EMBEDDINGS", "86400"))
    cache_ttl_queries: int = int(os.getenv("CACHE_TTL_QUERIES", "900"))
    
    # Upload
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
    upload_dir: str = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
