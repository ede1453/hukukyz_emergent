"""Citation tracking and linking tool"""

from typing import List, Dict, Set
import logging
from backend.agents.tools.legal_parser import legal_parser, MaddeReference

logger = logging.getLogger(__name__)


class CitationTracker:
    """Track citations and cross-references in legal documents"""
    
    def __init__(self):
        self.parser = legal_parser
    
    def extract_citations(self, text: str) -> List[Dict]:
        """Extract all citations from text
        
        Args:
            text: Text to extract citations from
        
        Returns:
            List of citation dictionaries
        """
        references = self.parser.parse_madde_reference(text)
        
        citations = []
        for ref in references:
            citations.append({
                "type": "madde",
                "kanun": ref.kanun,
                "madde_no": ref.madde_no,
                "fikra_no": ref.fikra_no,
                "bent": ref.bent,
                "formatted": self.parser.format_reference(ref),
                "raw_text": ref.raw_text
            })
        
        return citations
    
    def build_citation_graph(self, documents: List[Dict]) -> Dict:
        """Build citation graph from documents
        
        Args:
            documents: List of document dictionaries
        
        Returns:
            Citation graph with nodes and edges
        """
        nodes = set()
        edges = []
        
        for doc in documents:
            payload = doc.get("payload", {})
            source = f"{payload.get('kaynak', 'Unknown')} m.{payload.get('madde_no', 0)}"
            nodes.add(source)
            
            # Extract citations from content
            content = payload.get("content", "")
            citations = self.extract_citations(content)
            
            for citation in citations:
                target = citation["formatted"]
                nodes.add(target)
                edges.append({
                    "from": source,
                    "to": target,
                    "type": "references"
                })
        
        return {
            "nodes": list(nodes),
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    
    def find_related_articles(self, madde_ref: str, documents: List[Dict]) -> List[Dict]:
        """Find articles related to given madde
        
        Args:
            madde_ref: Madde reference (e.g., "TTK m.11")
            documents: List of documents to search
        
        Returns:
            List of related articles
        """
        related = []
        
        for doc in documents:
            payload = doc.get("payload", {})
            content = payload.get("content", "")
            
            # Check if madde_ref is mentioned in content
            if madde_ref in content:
                related.append({
                    "kaynak": payload.get("kaynak"),
                    "madde_no": payload.get("madde_no"),
                    "content": content[:200] + "...",
                    "relation": "mentions"
                })
        
        return related
    
    def trace_citation_chain(self, start_ref: str, documents: List[Dict], max_depth: int = 3) -> List[List[str]]:
        """Trace citation chain from starting reference
        
        Args:
            start_ref: Starting madde reference
            documents: List of documents
            max_depth: Maximum depth to trace
        
        Returns:
            List of citation chains
        """
        chains = []
        
        def dfs(current_ref: str, chain: List[str], depth: int):
            if depth > max_depth:
                return
            
            # Find documents that cite current_ref
            for doc in documents:
                payload = doc.get("payload", {})
                content = payload.get("content", "")
                citations = self.extract_citations(content)
                
                for citation in citations:
                    if citation["formatted"] == current_ref:
                        source = f"{payload.get('kaynak')} m.{payload.get('madde_no')}"
                        new_chain = chain + [source]
                        chains.append(new_chain)
                        dfs(source, new_chain, depth + 1)
        
        dfs(start_ref, [start_ref], 0)
        return chains


# Global tracker instance
citation_tracker = CitationTracker()
