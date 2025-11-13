"""Main FastAPI application for HukukYZ"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from backend.config import settings
from backend.database.mongodb import mongodb_client
from backend.database.qdrant_client import qdrant_manager
from backend.database.faiss_store import faiss_manager
from backend.core.cache import cache_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for FastAPI app"""
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.environment} mode")
    logger.info(f"Vector store type: {settings.vector_store_type}")
    
    # Initialize databases
    await mongodb_client.connect()
    
    # Initialize cache
    await cache_manager.connect()
    
    # Initialize vector store based on config
    if settings.vector_store_type == "qdrant":
        try:
            await qdrant_manager.initialize()
            logger.info("✅ Qdrant initialized")
        except Exception as e:
            logger.warning(f"Qdrant initialization failed: {e}")
            logger.info("Falling back to FAISS...")
            await faiss_manager.initialize()
    else:
        # Use FAISS by default
        await faiss_manager.initialize()
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await mongodb_client.close()
    await cache_manager.disconnect()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Advanced AI-Powered Legal Assistant for Turkish Law",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred"
        }
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": "0.1.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


# Import and include routers
from backend.api.routes import chat, documents
from backend.mcp.client.mcp_client import mcp_client

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
# app.include_router(admin.router, prefix="/api/admin", tags=["admin"])  # Phase 7


# Initialize MCP client on startup
@app.on_event("startup")
async def startup_mcp():
    """Initialize MCP servers"""
    try:
        await mcp_client.initialize()
        logger.info("MCP servers initialized")
    except Exception as e:
        logger.error(f"Failed to initialize MCP servers: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug
    )
