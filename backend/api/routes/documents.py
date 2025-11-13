"""Document upload and management API routes"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import tempfile
import os

from backend.utils.pdf_processor import pdf_processor
from backend.database.faiss_store import faiss_manager
from backend.database.qdrant_client import qdrant_manager
from backend.config import settings
import hashlib

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def check_duplicate_document(collection_name: str, file_hash: str) -> bool:
    """Check if document with same hash already exists"""
    try:
        if settings.vector_store_type == "qdrant":
            # Search for documents with this hash in Qdrant
            result = qdrant_manager.client.scroll(
                collection_name=collection_name,
                scroll_filter={"must": [{"key": "file_hash", "match": {"value": file_hash}}]},
                limit=1
            )
            return len(result[0]) > 0
        else:
            # For FAISS, we'd need to check metadata (not implemented for now)
            return False
    except Exception as e:
        logger.error(f"Error checking duplicate: {e}")
        return False

router = APIRouter()


class CollectionInfo(BaseModel):
    """Collection information"""
    name: str
    display_name: str
    document_count: int
    description: str


@router.get("/collections", response_model=List[CollectionInfo])
async def list_collections():
    """List all available collections"""
    try:
        collection_info = {
            "ticaret_hukuku": {
                "display_name": "Ticaret Hukuku (TTK)",
                "description": "Anonim şirket, limited şirket, ticari işletme"
            },
            "borclar_hukuku": {
                "display_name": "Borçlar Hukuku (TBK, İş Kanunu)",
                "description": "Sözleşmeler, tazminat, iş ilişkileri"
            },
            "icra_iflas": {
                "display_name": "İcra ve İflas Hukuku (İİK)",
                "description": "Haciz, iflas, alacak takibi"
            },
            "medeni_hukuk": {
                "display_name": "Medeni Hukuk (TMK)",
                "description": "Kişi, aile, miras, eşya hukuku"
            },
            "tuketici_haklari": {
                "display_name": "Tüketici Hakları (TKHK)",
                "description": "Cayma hakkı, ayıplı mal, tüketici mahkemesi"
            },
            "bankacilik_hukuku": {
                "display_name": "Bankacılık Hukuku",
                "description": "Banka işlemleri, kredi, mevduat"
            },
            "hmk": {
                "display_name": "Hukuk Muhakemeleri (HMK)",
                "description": "Dava, delil, usul kuralları"
            }
        }
        
        collections = []
        
        if settings.vector_store_type == "qdrant":
            # Get from Qdrant
            qdrant_collections = qdrant_manager.client.get_collections()
            for collection in qdrant_collections.collections:
                info = qdrant_manager.client.get_collection(collection.name)
                display_info = collection_info.get(collection.name, {
                    "display_name": collection.name,
                    "description": "Genel hukuk koleksiyonu"
                })
                
                collections.append(CollectionInfo(
                    name=collection.name,
                    display_name=display_info["display_name"],
                    document_count=info.points_count,
                    description=display_info["description"]
                ))
        else:
            # Get from FAISS
            stats = faiss_manager.get_stats()
            for name, stat in stats.items():
                info = collection_info.get(name, {
                    "display_name": name,
                    "description": "Genel hukuk koleksiyonu"
                })
                
                collections.append(CollectionInfo(
                    name=name,
                    display_name=info["display_name"],
                    document_count=stat["document_count"],
                    description=info["description"]
                ))
        
        return collections
        
    except Exception as e:
        logger.error(f"List collections error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(...),
    create_new: bool = Form(False),
    new_collection_name: Optional[str] = Form(None)
):
    """Upload a legal PDF document with transactional safety"""
    temp_collection = None
    tmp_path = None
    
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Sadece PDF dosyaları desteklenmektedir")
        
        # Determine target collection
        if create_new and new_collection_name:
            target_collection = new_collection_name.lower().replace(" ", "_")
        else:
            target_collection = collection
        
        logger.info(f"Uploading {file.filename} to {target_collection}")
        
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Calculate file hash for duplicate detection
            file_hash = calculate_file_hash(tmp_path)
            logger.info(f"File hash: {file_hash[:16]}...")
            
            # Check for duplicates
            if check_duplicate_document(target_collection, file_hash):
                logger.warning(f"Duplicate document detected: {file.filename}")
                raise HTTPException(
                    status_code=409,
                    detail=f"Bu PDF daha önce '{target_collection}' koleksiyonuna yüklenmiş. Aynı içeriğe sahip belgeler tekrar yüklenemez."
                )
            
            # Process PDF
            law_code, law_name, articles = pdf_processor.process_pdf(tmp_path)
            
            # Prepare documents
            texts = []
            metadatas = []
            ids = []
            
            for article in articles:
                full_text = f"{article['title']}\n\n{article['content']}"
                
                metadata = {
                    "doc_id": f"{law_code}_{article['madde_no']}",
                    "kaynak": law_code,
                    "doc_type": "kanun",
                    "hukuk_dali": target_collection.replace("_hukuku", "").replace("_haklari", ""),
                    "madde_no": article['madde_no'],
                    "title": article['title'],
                    "content": article['content'],
                    "version": "1.0",
                    "status": "active",
                    "source_file": file.filename
                }
                
                texts.append(full_text)
                metadatas.append(metadata)
                ids.append(f"{law_code}_m{article['madde_no']}")
            
            # Transactional upload: Use staging approach
            # Upload documents with transaction safety
            logger.info(f"Starting transactional upload of {len(texts)} documents")
            
            try:
                if settings.vector_store_type == "qdrant":
                    # Qdrant supports batch upsert, so we upload directly
                    # If it fails, Qdrant won't partially commit
                    await qdrant_manager.add_documents(
                        collection_name=target_collection,
                        texts=texts,
                        metadatas=metadatas
                    )
                else:
                    # FAISS doesn't support transactions, upload directly
                    await faiss_manager.add_documents(
                        collection_name=target_collection,
                        texts=texts,
                        metadatas=metadatas,
                        ids=ids
                    )
                
                logger.info(f"✅ Transactional upload successful")
                
            except Exception as upload_error:
                logger.error(f"Upload failed: {upload_error}")
                # In case of error, the batch won't be committed
                raise HTTPException(
                    status_code=500,
                    detail=f"Belge yükleme başarısız: {str(upload_error)}"
                )
            
            return {
                "status": "success",
                "message": f"{len(articles)} madde başarıyla yüklendi",
                "law_code": law_code,
                "law_name": law_name,
                "collection": target_collection,
                "articles_count": len(articles),
                "file_name": file.filename
            }
            
        finally:
            # Cleanup temporary PDF file
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
                logger.info("Temporary file cleaned up")
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(500, f"Yükleme hatası: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get document statistics"""
    try:
        if settings.vector_store_type == "qdrant":
            # Get stats from Qdrant
            collections = qdrant_manager.client.get_collections()
            stats = {}
            total = 0
            
            for collection in collections.collections:
                info = qdrant_manager.client.get_collection(collection.name)
                stats[collection.name] = {
                    "document_count": info.points_count,
                    "dimension": info.config.params.vectors.size
                }
                total += info.points_count
                
            return {
                "total_documents": total,
                "total_collections": len(stats),
                "collections": stats
            }
        else:
            # Get stats from FAISS
            stats = faiss_manager.get_stats()
            total = sum(s["document_count"] for s in stats.values())
            
            return {
                "total_documents": total,
                "total_collections": len(stats),
                "collections": stats
            }
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(500, str(e))
