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

logger = logging.getLogger(__name__)

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
        stats = faiss_manager.get_stats()
        
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
        logger.error(f"List collections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(...),
    create_new: bool = Form(False),
    new_collection_name: Optional[str] = Form(None)
):
    """Upload a legal PDF document"""
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
            # Process PDF
            law_code, law_name, articles = pdf_processor.process_pdf(tmp_path)
            
            # Prepare for FAISS
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
            
            # Upload to FAISS
            await faiss_manager.add_documents(
                collection_name=target_collection,
                texts=texts,
                metadatas=metadatas,
                ids=ids
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
            os.unlink(tmp_path)
        
    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(500, f"Yükleme hatası: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get document statistics"""
    try:
        stats = faiss_manager.get_stats()
        total = sum(s["document_count"] for s in stats.values())
        
        return {
            "total_documents": total,
            "total_collections": len(stats),
            "collections": stats
        }
    except Exception as e:
        raise HTTPException(500, str(e))
