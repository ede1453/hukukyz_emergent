"""Document management API routes"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
import uuid
from datetime import datetime
import os

from backend.mcp.client.mcp_client import mcp_client
from backend.database.qdrant_client import qdrant_manager
from backend.database.mongodb import get_documents_collection, get_upload_logs_collection
from backend.utils.embeddings import get_embeddings_batch
from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    upload_id: str
    status: str
    message: str
    chunks_processed: int = 0


class DocumentInfo(BaseModel):
    """Document information"""
    id: str
    filename: str
    doc_type: str
    hukuk_dali: str
    status: str
    chunks_count: int
    uploaded_at: str


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    hukuk_dali: str = Form(...),
    kaynak: str = Form(...),
    version: str = Form(default="1.0")
):
    """Upload and process legal document
    
    Args:
        file: PDF file
        doc_type: Document type (kanun, yonetmelik, ictihat, etc.)
        hukuk_dali: Legal domain
        kaynak: Source name (TTK, TBK, etc.)
        version: Document version
    """
    upload_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Processing upload: {file.filename}")
        
        # Save file temporarily
        upload_dir = settings.upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{upload_id}_{file.filename}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Log upload start
        upload_logs = get_upload_logs_collection()
        await upload_logs.insert_one({
            "upload_id": upload_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "hukuk_dali": hukuk_dali,
            "status": "processing",
            "timestamp": datetime.utcnow()
        })
        
        # Parse PDF using MCP
        await mcp_client.initialize()
        
        parse_result = await mcp_client.call_tool(
            server_name="document_processor",
            tool_name="parse_pdf",
            params={
                "file_path": file_path,
                "doc_type": doc_type,
                "hukuk_dali": hukuk_dali
            }
        )
        
        text = parse_result["text"]
        metadata = parse_result["metadata"]
        
        # Chunk document
        chunk_result = await mcp_client.call_tool(
            server_name="document_processor",
            tool_name="chunk_document",
            params={
                "text": text,
                "strategy": "madde_based" if doc_type == "kanun" else "recursive"
            }
        )
        
        chunks = chunk_result["chunks"]
        logger.info(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = await get_embeddings_batch(chunk_texts)
        
        # Prepare points for Qdrant
        collection_map = {
            "ticaret": "ticaret_hukuku",
            "borclar": "borclar_hukuku",
            "icra": "icra_iflas",
            "medeni": "medeni_hukuk",
            "tuketici": "tuketici_haklari",
            "bankacilik": "bankacilik_hukuku",
            "hmk": "hmk"
        }
        
        collection_name = collection_map.get(hukuk_dali, "ticaret_hukuku")
        
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is None:
                continue
            
            point_id = f"{upload_id}_{i}"
            payload = {
                "doc_id": upload_id,
                "kaynak": kaynak,
                "doc_type": doc_type,
                "hukuk_dali": hukuk_dali,
                "version": version,
                "status": "active",
                "content": chunk["content"],
                "chunk_index": i,
                **chunk.get("metadata", {}),
                **metadata
            }
            
            points.append({
                "id": point_id,
                "vector": embedding,
                "payload": payload
            })
        
        # Upload to Qdrant
        success = qdrant_manager.upsert_points(collection_name, points)
        
        if not success:
            raise Exception("Failed to upload to Qdrant")
        
        # Save document info to MongoDB
        documents = get_documents_collection()
        await documents.insert_one({
            "upload_id": upload_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "hukuk_dali": hukuk_dali,
            "kaynak": kaynak,
            "version": version,
            "collection": collection_name,
            "chunks_count": len(points),
            "status": "completed",
            "uploaded_at": datetime.utcnow()
        })
        
        # Update upload log
        await upload_logs.update_one(
            {"upload_id": upload_id},
            {"$set": {"status": "completed", "chunks_processed": len(points)}}
        )
        
        # Cleanup temp file
        os.remove(file_path)
        
        logger.info(f"Upload completed: {upload_id}")
        
        return DocumentUploadResponse(
            upload_id=upload_id,
            status="completed",
            message=f"Successfully uploaded {len(points)} chunks",
            chunks_processed=len(points)
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        
        # Log error
        upload_logs = get_upload_logs_collection()
        await upload_logs.update_one(
            {"upload_id": upload_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[DocumentInfo])
async def list_documents(
    hukuk_dali: Optional[str] = None,
    doc_type: Optional[str] = None,
    limit: int = 50
):
    """List uploaded documents"""
    try:
        documents = get_documents_collection()
        
        # Build query
        query = {}
        if hukuk_dali:
            query["hukuk_dali"] = hukuk_dali
        if doc_type:
            query["doc_type"] = doc_type
        
        # Fetch documents
        cursor = documents.find(query).limit(limit).sort("uploaded_at", -1)
        docs = await cursor.to_list(length=limit)
        
        # Format response
        result = []
        for doc in docs:
            result.append(DocumentInfo(
                id=doc["upload_id"],
                filename=doc["filename"],
                doc_type=doc["doc_type"],
                hukuk_dali=doc["hukuk_dali"],
                status=doc["status"],
                chunks_count=doc["chunks_count"],
                uploaded_at=doc["uploaded_at"].isoformat()
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{upload_id}")
async def delete_document(upload_id: str):
    """Delete document from system"""
    try:
        logger.info(f"Deleting document: {upload_id}")
        
        # Get document info
        documents = get_documents_collection()
        doc = await documents.find_one({"upload_id": upload_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from Qdrant
        collection = doc["collection"]
        chunks_count = doc["chunks_count"]
        
        # Get point IDs
        point_ids = [f"{upload_id}_{i}" for i in range(chunks_count)]
        
        qdrant_manager.delete_points(collection, point_ids)
        
        # Delete from MongoDB
        await documents.delete_one({"upload_id": upload_id})
        
        logger.info(f"Document deleted: {upload_id}")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
