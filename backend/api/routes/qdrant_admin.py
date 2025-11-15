"""Qdrant Admin API routes for collection management"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from backend.database.qdrant_client import qdrant_manager
from backend.api.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/qdrant", tags=["qdrant-admin"])


class CollectionAction(BaseModel):
    collection_name: str
    action: str  # "delete", "snapshot", "merge"
    target_collection: Optional[str] = None  # For merge operation


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Verify user has admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Bu işlem için admin yetkisi gereklidir"
        )
    return current_user


@router.delete("/collections/{collection_name}")
async def delete_collection(
    collection_name: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a collection (admin only)"""
    try:
        client = qdrant_manager.client
        
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name not in collection_names:
            raise HTTPException(status_code=404, detail="Koleksiyon bulunamadı")
        
        # Delete collection
        client.delete_collection(collection_name=collection_name)
        
        logger.info(f"Collection '{collection_name}' deleted by user {current_user['email']}")
        
        return {
            "success": True,
            "message": f"'{collection_name}' koleksiyonu başarıyla silindi"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        raise HTTPException(status_code=500, detail=f"Koleksiyon silinemedi: {str(e)}")


@router.post("/collections/{collection_name}/snapshot")
async def create_snapshot(
    collection_name: str,
    current_user: dict = Depends(require_admin)
):
    """Create a snapshot of a collection and get download URL (admin only)"""
    try:
        client = qdrant_manager.client
        
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name not in collection_names:
            raise HTTPException(status_code=404, detail="Koleksiyon bulunamadı")
        
        # Create snapshot
        snapshot_result = client.create_snapshot(collection_name=collection_name)
        
        # Get snapshot download URL
        from backend.config import settings
        download_url = f"{settings.qdrant_url}/collections/{collection_name}/snapshots/{snapshot_result.name}"
        
        logger.info(f"Snapshot created for '{collection_name}' by user {current_user['email']}")
        
        return {
            "success": True,
            "message": f"'{collection_name}' için snapshot oluşturuldu",
            "snapshot_name": snapshot_result.name,
            "download_url": download_url,
            "instructions": "Snapshot Qdrant Cloud'da oluşturuldu. İndirmek için aşağıdaki URL'yi kullanabilirsiniz."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        raise HTTPException(status_code=500, detail=f"Snapshot oluşturulamadı: {str(e)}")


@router.get("/collections/{collection_name}/info")
async def get_collection_info(
    collection_name: str,
    current_user: dict = Depends(require_admin)
):
    """Get detailed collection information (admin only)"""
    try:
        client = qdrant_manager.client
        
        # Get collection info
        info = client.get_collection(collection_name=collection_name)
        
        return {
            "success": True,
            "collection": {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status.value
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        raise HTTPException(status_code=500, detail=f"Koleksiyon bilgisi alınamadı: {str(e)}")


@router.post("/collections/recreate/{collection_name}")
async def recreate_collection(
    collection_name: str,
    current_user: dict = Depends(require_admin)
):
    """Recreate a collection (delete and create with same settings) - admin only"""
    try:
        client = qdrant_manager.client
        
        # Get current collection info before deleting
        try:
            info = client.get_collection(collection_name=collection_name)
            vectors_config = info.config.params.vectors
        except:
            raise HTTPException(status_code=404, detail="Koleksiyon bulunamadı")
        
        # Delete and recreate
        client.delete_collection(collection_name=collection_name)
        client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config
        )
        
        logger.info(f"Collection '{collection_name}' recreated by user {current_user['email']}")
        
        return {
            "success": True,
            "message": f"'{collection_name}' koleksiyonu yeniden oluşturuldu"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recreating collection: {e}")
        raise HTTPException(status_code=500, detail=f"Koleksiyon yeniden oluşturulamadı: {str(e)}")
