"""Citation Tracker - Track and analyze legal citations

Tracks citations across documents and answers to:
- Ensure all citations are valid
- Detect circular references
- Build citation graphs
- Find most cited articles

Now with MongoDB persistence for tracking across sessions.
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import logging

from backend.tools.legal_parser import LegalParser, LegalReference, ReferenceType
from backend.database.mongodb import mongodb_client

logger = logging.getLogger(__name__)


@dataclass
class CitationNode:
    """A node in the citation graph"""
    reference: str  # Formatted reference (e.g., "TTK m.11")
    cited_by: Set[str] = field(default_factory=set)  # Who cites this
    cites: Set[str] = field(default_factory=set)  # What this cites
    citation_count: int = 0  # How many times cited
    
    def add_citation_from(self, source: str):
        """Add a citation from source"""
        self.cited_by.add(source)
        self.citation_count += 1
    
    def add_citation_to(self, target: str):
        """Add a citation to target"""
        self.cites.add(target)


class CitationTracker:
    """Track and analyze legal citations with MongoDB persistence"""
    
    def __init__(self):
        self.parser = LegalParser()
        self.citations: Dict[str, CitationNode] = {}  # reference -> node (memory cache)
        self.document_citations: Dict[str, List[str]] = defaultdict(list)  # doc_id -> citations (memory cache)
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure MongoDB connection and load existing data"""
        if self._initialized:
            return
        
        try:
            db = mongodb_client.get_database()
            
            # Create indexes
            await db.citations.create_index("reference", unique=True)
            await db.citations.create_index([("citation_count", -1)])
            await db.document_citations.create_index("doc_id")
            
            # Load existing citations into memory cache
            citations_cursor = db.citations.find()
            async for doc in citations_cursor:
                ref = doc["reference"]
                self.citations[ref] = CitationNode(
                    reference=ref,
                    cited_by=set(doc.get("cited_by", [])),
                    cites=set(doc.get("cites", [])),
                    citation_count=doc.get("citation_count", 0)
                )
            
            # Load document citations
            doc_citations_cursor = db.document_citations.find()
            async for doc in doc_citations_cursor:
                self.document_citations[doc["doc_id"]] = doc.get("citations", [])
            
            self._initialized = True
            logger.info(f"✅ Citation tracker initialized: {len(self.citations)} citations loaded")
            
        except Exception as e:
            logger.warning(f"Citation tracker initialization failed: {e}. Running in memory-only mode.")
            self._initialized = True  # Mark as initialized but with fallback mode
    
    async def track_document(self, doc_id: str, text: str) -> List[LegalReference]:
        """Track citations in a document
        
        Args:
            doc_id: Document identifier
            text: Document text
        
        Returns:
            List of parsed references
        """
        await self._ensure_initialized()
        
        # Parse references
        references = self.parser.parse(text)
        
        if not references:
            return []
        
        try:
            db = mongodb_client.get_database()
            
            # Track each reference
            for ref in references:
                formatted_ref = self.parser.format_reference(ref)
                
                # Create/update node in memory
                if formatted_ref not in self.citations:
                    self.citations[formatted_ref] = CitationNode(reference=formatted_ref)
                
                # Add citation from this document
                self.citations[formatted_ref].add_citation_from(doc_id)
                
                # Update in MongoDB
                await db.citations.update_one(
                    {"reference": formatted_ref},
                    {
                        "$set": {
                            "reference": formatted_ref,
                            "citation_count": self.citations[formatted_ref].citation_count,
                            "cited_by": list(self.citations[formatted_ref].cited_by),
                            "cites": list(self.citations[formatted_ref].cites),
                            "updated_at": datetime.utcnow()
                        },
                        "$setOnInsert": {
                            "created_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                
                # Track in document
                if formatted_ref not in self.document_citations[doc_id]:
                    self.document_citations[doc_id].append(formatted_ref)
            
            # Update document citations in MongoDB
            await db.document_citations.update_one(
                {"doc_id": doc_id},
                {
                    "$set": {
                        "doc_id": doc_id,
                        "citations": self.document_citations[doc_id],
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.debug(f"Tracked {len(references)} citations in document {doc_id}")
            
        except Exception as e:
            logger.error(f"Error persisting citations: {e}. Continuing with memory-only tracking.")
        
        return references
    
    async def get_most_cited(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most cited articles
        
        Args:
            limit: Number of results
        
        Returns:
            List of (reference, count) tuples
        """
        await self._ensure_initialized()
        
        try:
            db = mongodb_client.get_database()
            
            # Get from MongoDB (always fresh)
            cursor = db.citations.find(
                {},
                {"reference": 1, "citation_count": 1, "_id": 0}
            ).sort("citation_count", -1).limit(limit)
            
            results = []
            async for doc in cursor:
                results.append((doc["reference"], doc["citation_count"]))
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting most cited from DB: {e}. Using memory cache.")
            # Fallback to memory
            sorted_citations = sorted(
                self.citations.items(),
                key=lambda x: x[1].citation_count,
                reverse=True
            )
            return [(ref, node.citation_count) for ref, node in sorted_citations[:limit]]
    
    def get_citation_chain(self, reference: str, max_depth: int = 3) -> List[List[str]]:
        """Get citation chain (who cites what)
        
        Args:
            reference: Starting reference
            max_depth: Maximum chain depth
        
        Returns:
            List of citation chains
        """
        if reference not in self.citations:
            return []
        
        chains = []
        visited = set()
        
        def dfs(current: str, chain: List[str], depth: int):
            if depth > max_depth or current in visited:
                return
            
            visited.add(current)
            chain.append(current)
            
            node = self.citations.get(current)
            if node:
                if node.cites:
                    for cited in node.cites:
                        dfs(cited, chain.copy(), depth + 1)
                else:
                    chains.append(chain)
        
        dfs(reference, [], 0)
        return chains
    
    def detect_circular_references(self) -> List[List[str]]:
        """Detect circular citation references
        
        Returns:
            List of circular reference chains
        """
        circular = []
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in self.citations:
                for neighbor in self.citations[node].cites:
                    if neighbor not in visited:
                        if has_cycle(neighbor, path.copy()):
                            return True
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        circular.append(path[cycle_start:] + [neighbor])
                        return True
            
            rec_stack.remove(node)
            return False
        
        for ref in self.citations:
            if ref not in visited:
                has_cycle(ref, [])
        
        return circular
    
    def validate_citations(
        self, 
        citations: List[Dict],
        available_sources: List[Dict]
    ) -> Dict[str, bool]:
        """Validate if citations match available sources
        
        Args:
            citations: List of citation dicts
            available_sources: List of available source documents
        
        Returns:
            Dict of citation -> valid (bool)
        """
        validation = {}
        
        # Parse available sources
        available_refs = set()
        for source in available_sources:
            text = source.get("text", "")
            refs = self.parser.parse(text)
            for ref in refs:
                available_refs.add(self.parser.format_reference(ref))
        
        # Check each citation
        for citation in citations:
            source = citation.get("source", "")
            # Parse citation source
            parsed = self.parser.parse(source)
            
            if parsed:
                formatted = self.parser.format_reference(parsed[0])
                validation[source] = formatted in available_refs
            else:
                validation[source] = False
        
        return validation
    
    async def get_citation_stats(self) -> Dict:
        """Get overall citation statistics
        
        Returns:
            Statistics dict
        """
        await self._ensure_initialized()
        
        try:
            db = mongodb_client.get_database()
            
            # Get stats from MongoDB
            total_citations = 0
            unique_refs = 0
            
            cursor = db.citations.find({}, {"citation_count": 1})
            async for doc in cursor:
                total_citations += doc.get("citation_count", 0)
                unique_refs += 1
            
            doc_count = await db.document_citations.count_documents({})
            
            if unique_refs == 0:
                return {
                    "total_citations": 0,
                    "unique_references": 0,
                    "avg_citations_per_ref": 0,
                    "most_cited": [],
                    "documents_tracked": 0
                }
            
            return {
                "total_citations": total_citations,
                "unique_references": unique_refs,
                "avg_citations_per_ref": round(total_citations / unique_refs, 2),
                "most_cited": await self.get_most_cited(5),
                "documents_tracked": doc_count
            }
            
        except Exception as e:
            logger.error(f"Error getting citation stats: {e}. Using memory cache.")
            # Fallback to memory
            if not self.citations:
                return {
                    "total_citations": 0,
                    "unique_references": 0,
                    "avg_citations_per_ref": 0,
                    "most_cited": [],
                    "documents_tracked": 0
                }
            
            total = sum(node.citation_count for node in self.citations.values())
            
            return {
                "total_citations": total,
                "unique_references": len(self.citations),
                "avg_citations_per_ref": round(total / len(self.citations), 2),
                "most_cited": await self.get_most_cited(5),
                "documents_tracked": len(self.document_citations)
            }
    
    async def get_related_articles(
        self, 
        reference: str, 
        limit: int = 5
    ) -> List[Tuple[str, str]]:
        """Get related articles (co-cited)
        
        Args:
            reference: Reference to find related articles for
            limit: Maximum results
        
        Returns:
            List of (related_ref, relationship) tuples
        """
        await self._ensure_initialized()
        
        try:
            db = mongodb_client.get_database()
            
            # Get the reference node
            ref_doc = await db.citations.find_one({"reference": reference})
            if not ref_doc:
                return []
            
            related = []
            cited_by = set(ref_doc.get("cited_by", []))
            
            # Find co-cited articles (cited by same documents)
            if cited_by:
                async for doc in db.document_citations.find({"doc_id": {"$in": list(cited_by)}}):
                    for cited_ref in doc.get("citations", []):
                        if cited_ref != reference:
                            related.append((cited_ref, "co-cited"))
            
            # Find articles that this one cites
            for cited_ref in ref_doc.get("cites", []):
                related.append((cited_ref, "cites"))
            
            # Find articles that cite this one
            async for doc in db.citations.find({"cites": reference}):
                related.append((doc["reference"], "cited-by"))
            
            # Count and sort
            from collections import Counter
            related_counts = Counter(r[0] for r in related)
            sorted_related = sorted(
                related_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [(ref, "related") for ref, _ in sorted_related[:limit]]
            
        except Exception as e:
            logger.error(f"Error getting related articles: {e}")
            return []
    
    async def clear(self):
        """Clear all tracked citations (memory and database)"""
        await self._ensure_initialized()
        
        try:
            db = mongodb_client.get_database()
            
            # Clear MongoDB collections
            await db.citations.delete_many({})
            await db.document_citations.delete_many({})
            
            logger.info("✅ Citation tracker cleared from MongoDB")
            
        except Exception as e:
            logger.error(f"Error clearing citations from DB: {e}")
        
        # Clear memory cache
        self.citations.clear()
        self.document_citations.clear()
        logger.info("Citation tracker memory cleared")


# Global citation tracker instance
citation_tracker = CitationTracker()
