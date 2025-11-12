"""FAISS Vector Store - In-memory alternative to Qdrant"""

import logging
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss
from dataclasses import dataclass, asdict

from backend.utils.embeddings import embedding_service

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document with embeddings and metadata"""
    id: str
    text: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FAISSCollection:
    """Single FAISS collection for a legal domain"""
    
    def __init__(self, name: str, dimension: int = 1536):
        self.name = name
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents: List[Document] = []
        self.id_to_idx: Dict[str, int] = {}
    
    def add_documents(self, documents: List[Document]):
        """Add documents to collection"""
        try:
            # Prepare embeddings
            embeddings = []
            valid_docs = []
            
            for doc in documents:
                if doc.embedding is not None:
                    embeddings.append(doc.embedding)
                    valid_docs.append(doc)
                else:
                    logger.warning(f"Document {doc.id} has no embedding, skipping")
            
            if not embeddings:
                logger.warning("No valid documents to add")
                return
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Add to FAISS index
            start_idx = len(self.documents)
            self.index.add(embeddings_array)
            
            # Store documents and create ID mapping
            for i, doc in enumerate(valid_docs):
                idx = start_idx + i
                self.documents.append(doc)
                self.id_to_idx[doc.id] = idx
            
            logger.info(f"Added {len(valid_docs)} documents to {self.name}")
            
        except Exception as e:
            logger.error(f"Error adding documents to {self.name}: {e}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents
        
        Args:
            query_embedding: Query vector
            limit: Number of results
            metadata_filter: Filter by metadata fields
        
        Returns:
            List of (document, distance) tuples
        """
        try:
            if self.index.ntotal == 0:
                logger.warning(f"Collection {self.name} is empty")
                return []
            
            # Reshape query for FAISS
            query_vector = query_embedding.reshape(1, -1).astype(np.float32)
            
            # Search more than needed if filtering
            search_limit = limit * 3 if metadata_filter else limit
            search_limit = min(search_limit, self.index.ntotal)
            
            # Perform search
            distances, indices = self.index.search(query_vector, search_limit)
            
            # Collect results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.documents):
                    continue
                
                doc = self.documents[idx]
                
                # Apply metadata filter
                if metadata_filter:
                    if not self._matches_filter(doc.metadata, metadata_filter):
                        continue
                
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + float(dist))
                results.append((doc, similarity))
                
                if len(results) >= limit:
                    break
            
            logger.info(f"Found {len(results)} results in {self.name}")
            return results
            
        except Exception as e:
            logger.error(f"Search error in {self.name}: {e}")
            return []
    
    def get_by_id(self, doc_id: str) -> Optional[Document]:
        """Get document by ID"""
        idx = self.id_to_idx.get(doc_id)
        if idx is not None and 0 <= idx < len(self.documents):
            return self.documents[idx]
        return None
    
    def _matches_filter(self, metadata: Dict, filter_dict: Dict) -> bool:
        """Check if metadata matches filter"""
        for key, value in filter_dict.items():
            if key not in metadata:
                return False
            
            meta_value = metadata[key]
            
            # Handle list values (e.g., hukuk_dali: ["ticaret", "borclar"])
            if isinstance(meta_value, list):
                if isinstance(value, list):
                    if not any(v in meta_value for v in value):
                        return False
                else:
                    if value not in meta_value:
                        return False
            else:
                if meta_value != value:
                    return False
        
        return True
    
    def count(self) -> int:
        """Get document count"""
        return len(self.documents)
    
    def save(self, directory: Path):
        """Save collection to disk"""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            index_path = directory / f"{self.name}.index"
            faiss.write_index(self.index, str(index_path))
            
            # Save documents (without embeddings to save space)
            docs_data = []
            for doc in self.documents:
                doc_dict = {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata
                }
                docs_data.append(doc_dict)
            
            docs_path = directory / f"{self.name}.json"
            with open(docs_path, "w", encoding="utf-8") as f:
                json.dump(docs_data, f, ensure_ascii=False, indent=2)
            
            # Save ID mapping
            mapping_path = directory / f"{self.name}_mapping.pkl"
            with open(mapping_path, "wb") as f:
                pickle.dump(self.id_to_idx, f)
            
            logger.info(f"Saved collection {self.name} to {directory}")
            
        except Exception as e:
            logger.error(f"Error saving collection {self.name}: {e}")
    
    def load(self, directory: Path) -> bool:
        """Load collection from disk"""
        try:
            # Load FAISS index
            index_path = directory / f"{self.name}.index"
            if not index_path.exists():
                return False
            
            self.index = faiss.read_index(str(index_path))
            
            # Load documents
            docs_path = directory / f"{self.name}.json"
            with open(docs_path, "r", encoding="utf-8") as f:
                docs_data = json.load(f)
            
            self.documents = [
                Document(
                    id=d["id"],
                    text=d["text"],
                    metadata=d.get("metadata", {}),
                    embedding=None  # Don't load embeddings
                )
                for d in docs_data
            ]
            
            # Load ID mapping
            mapping_path = directory / f"{self.name}_mapping.pkl"
            with open(mapping_path, "rb") as f:
                self.id_to_idx = pickle.load(f)
            
            logger.info(f"Loaded collection {self.name} from {directory}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading collection {self.name}: {e}")
            return False


class FAISSManager:
    """Manager for FAISS vector store"""
    
    def __init__(self, persist_directory: str = "/app/backend/data/faiss"):
        self.persist_directory = Path(persist_directory)
        self.collections: Dict[str, FAISSCollection] = {}
        self.dimension = 1536  # OpenAI embedding dimension
        
    async def initialize(self):
        """Initialize FAISS collections"""
        try:
            logger.info("Initializing FAISS vector store...")
            
            # Define legal domain collections
            collection_names = [
                "ticaret_hukuku",
                "borclar_hukuku",
                "icra_iflas",
                "medeni_hukuk",
                "tuketici_haklari",
                "bankacilik_hukuku",
                "hmk"
            ]
            
            # Try to load existing collections or create new ones
            for name in collection_names:
                collection = FAISSCollection(name, self.dimension)
                
                # Try to load from disk
                if self.persist_directory.exists():
                    loaded = collection.load(self.persist_directory)
                    if loaded:
                        logger.info(f"Loaded collection: {name} ({collection.count()} docs)")
                    else:
                        logger.info(f"Created new collection: {name}")
                else:
                    logger.info(f"Created new collection: {name}")
                
                self.collections[name] = collection
            
            logger.info(f"✅ FAISS initialized with {len(self.collections)} collections")
            
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            raise
    
    def get_collection(self, name: str) -> Optional[FAISSCollection]:
        """Get collection by name"""
        return self.collections.get(name)
    
    async def add_documents(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict],
        ids: List[str]
    ):
        """Add documents to collection"""
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                logger.error(f"Collection {collection_name} not found")
                return
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} documents...")
            embeddings = await embedding_service.embed_batch(texts)
            
            # Create documents
            documents = [
                Document(
                    id=ids[i],
                    text=texts[i],
                    embedding=np.array(embeddings[i], dtype=np.float32),
                    metadata=metadatas[i]
                )
                for i in range(len(texts))
            ]
            
            # Add to collection
            collection.add_documents(documents)
            
            # Persist to disk
            collection.save(self.persist_directory)
            
            logger.info(f"✅ Added {len(documents)} documents to {collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {e}")
            raise
    
    async def search(
        self,
        collection_name: str,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """Search in collection"""
        try:
            collection = self.get_collection(collection_name)
            if not collection:
                logger.error(f"Collection {collection_name} not found")
                return []
            
            # Generate query embedding
            query_embedding = await embedding_service.embed_single(query)
            query_vector = np.array(query_embedding, dtype=np.float32)
            
            # Search
            results = collection.search(query_vector, limit, metadata_filter)
            
            # Format results
            formatted = []
            for doc, score in results:
                formatted.append({
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "score": score
                })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Search error in {collection_name}: {e}")
            return []
    
    async def search_multiple(
        self,
        collection_names: List[str],
        query: str,
        limit_per_collection: int = 5,
        metadata_filter: Optional[Dict] = None
    ) -> Dict[str, List[Dict]]:
        """Search across multiple collections"""
        results = {}
        
        for name in collection_names:
            collection_results = await self.search(
                name, query, limit_per_collection, metadata_filter
            )
            if collection_results:
                results[name] = collection_results
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about collections"""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = {
                "document_count": collection.count(),
                "dimension": collection.dimension
            }
        return stats


# Global FAISS manager instance
faiss_manager = FAISSManager()
