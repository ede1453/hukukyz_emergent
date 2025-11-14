"""Version Manager - Manage document versions and deprecation

Handles:
- Version tracking for legal documents
- Deprecation marking
- Version comparison
- Historical queries
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DocumentStatus(Enum):
    """Document status"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"
    ARCHIVED = "archived"


@dataclass
class DocumentVersion:
    """Document version information"""
    doc_id: str
    version: str
    status: DocumentStatus
    effective_date: Optional[str] = None
    deprecated_date: Optional[str] = None
    reason: Optional[str] = None
    replaced_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "doc_id": self.doc_id,
            "version": self.version,
            "status": self.status.value,
            "effective_date": self.effective_date,
            "deprecated_date": self.deprecated_date,
            "reason": self.reason,
            "replaced_by": self.replaced_by
        }


class VersionManager:
    """Manage document versions in Qdrant"""
    
    def __init__(self):
        self.version_format = "%Y.%m.%d"  # 2024.11.14
    
    def generate_version(self, date: Optional[datetime] = None) -> str:
        """Generate version string from date
        
        Args:
            date: Version date (default: now)
        
        Returns:
            Version string (e.g., "2024.11.14")
        """
        if date is None:
            date = datetime.now()
        return date.strftime(self.version_format)
    
    def parse_version(self, version_str: str) -> Optional[datetime]:
        """Parse version string to datetime
        
        Args:
            version_str: Version string
        
        Returns:
            Datetime or None if invalid
        """
        try:
            return datetime.strptime(version_str, self.version_format)
        except ValueError:
            logger.error(f"Invalid version format: {version_str}")
            return None
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two versions
        
        Args:
            version1: First version
            version2: Second version
        
        Returns:
            -1 if v1 < v2, 0 if equal, 1 if v1 > v2
        """
        date1 = self.parse_version(version1)
        date2 = self.parse_version(version2)
        
        if date1 is None or date2 is None:
            return 0
        
        if date1 < date2:
            return -1
        elif date1 > date2:
            return 1
        else:
            return 0
    
    def is_newer_version(self, version1: str, version2: str) -> bool:
        """Check if version1 is newer than version2"""
        return self.compare_versions(version1, version2) > 0
    
    async def create_version_metadata(
        self,
        doc_id: str,
        version: Optional[str] = None,
        status: DocumentStatus = DocumentStatus.ACTIVE,
        effective_date: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict:
        """Create version metadata for a document
        
        Args:
            doc_id: Document identifier
            version: Version string (auto-generated if None)
            status: Document status
            effective_date: When this version becomes effective
            reason: Reason for new version
        
        Returns:
            Version metadata dict
        """
        if version is None:
            version = self.generate_version()
        
        if effective_date is None:
            effective_date = datetime.now().isoformat()
        
        return {
            "version": version,
            "status": status.value,
            "effective_date": effective_date,
            "deprecated_date": None,
            "deprecation_reason": None,
            "replaced_by_version": None,
            "created_at": datetime.now().isoformat()
        }
    
    async def deprecate_version(
        self,
        qdrant_client,
        collection_name: str,
        doc_id: str,
        version: str,
        reason: str,
        replaced_by: Optional[str] = None
    ):
        """Mark a version as deprecated
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection name
            doc_id: Document ID
            version: Version to deprecate
            reason: Deprecation reason
            replaced_by: Version that replaces this one
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Find the document
            result = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                        FieldCondition(key="version", match=MatchValue(value=version))
                    ]
                ),
                limit=1,
                with_payload=True
            )
            
            if not result[0]:
                logger.warning(f"Document not found: {doc_id} v{version}")
                return
            
            point = result[0][0]
            
            # Update payload
            new_payload = point.payload.copy()
            new_payload["status"] = DocumentStatus.DEPRECATED.value
            new_payload["deprecated_date"] = datetime.now().isoformat()
            new_payload["deprecation_reason"] = reason
            if replaced_by:
                new_payload["replaced_by_version"] = replaced_by
            
            # Update in Qdrant
            qdrant_client.set_payload(
                collection_name=collection_name,
                payload=new_payload,
                points=[point.id]
            )
            
            logger.info(f"✅ Deprecated: {doc_id} v{version}")
            
        except Exception as e:
            logger.error(f"Error deprecating version: {e}", exc_info=True)
            raise
    
    async def get_versions(
        self,
        qdrant_client,
        collection_name: str,
        doc_id: str,
        include_deprecated: bool = False
    ) -> List[DocumentVersion]:
        """Get all versions of a document
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection name
            doc_id: Document ID
            include_deprecated: Include deprecated versions
        
        Returns:
            List of document versions
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # Build filter
            filter_conditions = [
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
            ]
            
            if not include_deprecated:
                filter_conditions.append(
                    FieldCondition(
                        key="status", 
                        match=MatchValue(value=DocumentStatus.ACTIVE.value)
                    )
                )
            
            # Query Qdrant
            result = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(must=filter_conditions),
                limit=100,
                with_payload=True
            )
            
            versions = []
            for point in result[0]:
                payload = point.payload
                versions.append(DocumentVersion(
                    doc_id=doc_id,
                    version=payload.get("version", "1.0.0"),
                    status=DocumentStatus(payload.get("status", "active")),
                    effective_date=payload.get("effective_date"),
                    deprecated_date=payload.get("deprecated_date"),
                    reason=payload.get("deprecation_reason"),
                    replaced_by=payload.get("replaced_by_version")
                ))
            
            # Sort by version (newest first)
            versions.sort(key=lambda v: v.version, reverse=True)
            
            logger.info(f"Found {len(versions)} versions for {doc_id}")
            return versions
            
        except Exception as e:
            logger.error(f"Error getting versions: {e}", exc_info=True)
            return []
    
    async def get_active_version(
        self,
        qdrant_client,
        collection_name: str,
        doc_id: str
    ) -> Optional[DocumentVersion]:
        """Get the active version of a document
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection name
            doc_id: Document ID
        
        Returns:
            Active version or None
        """
        versions = await self.get_versions(
            qdrant_client,
            collection_name,
            doc_id,
            include_deprecated=False
        )
        
        return versions[0] if versions else None
    
    async def get_version_at_date(
        self,
        qdrant_client,
        collection_name: str,
        doc_id: str,
        target_date: datetime
    ) -> Optional[DocumentVersion]:
        """Get the version that was active at a specific date
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Collection name
            doc_id: Document ID
            target_date: Target date
        
        Returns:
            Version that was active at that date
        """
        all_versions = await self.get_versions(
            qdrant_client,
            collection_name,
            doc_id,
            include_deprecated=True
        )
        
        # Find version active at target date
        for version in all_versions:
            effective = datetime.fromisoformat(version.effective_date) if version.effective_date else None
            deprecated = datetime.fromisoformat(version.deprecated_date) if version.deprecated_date else None
            
            if effective and effective <= target_date:
                if deprecated is None or deprecated > target_date:
                    return version
        
        return None
    
    def build_version_filter(
        self,
        include_deprecated: bool = False,
        version: Optional[str] = None,
        as_of_date: Optional[datetime] = None
    ) -> Dict:
        """Build Qdrant filter for version queries
        
        Args:
            include_deprecated: Include deprecated documents
            version: Specific version to query
            as_of_date: Get version as of this date
        
        Returns:
            Filter dict for Qdrant
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        conditions = []
        
        # Status filter
        if not include_deprecated:
            conditions.append(
                FieldCondition(
                    key="status",
                    match=MatchValue(value=DocumentStatus.ACTIVE.value)
                )
            )
        
        # Specific version
        if version:
            conditions.append(
                FieldCondition(
                    key="version",
                    match=MatchValue(value=version)
                )
            )
        
        # As-of date filtering would need custom logic
        # For now, we filter in Python after retrieval
        
        return Filter(must=conditions) if conditions else None


# Global version manager instance
version_manager = VersionManager()
