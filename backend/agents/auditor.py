"""Auditor Agent - Quality control and verification"""

from typing import List, Dict
from pydantic import BaseModel, Field
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.agents.state import VerificationResult

logger = logging.getLogger(__name__)


class AuditOutput(BaseModel):
    """Audit output"""
    passed: bool = Field(description="Whether audit passed")
    faithfulness_score: float = Field(description="Faithfulness score (0-1)")
    relevance_score: float = Field(description="Relevance score (0-1)")
    consistency_score: float = Field(description="Consistency score (0-1)")
    feedback: str = Field(description="Detailed feedback")
    issues: List[str] = Field(description="List of identified issues")
    recommendations: List[str] = Field(description="Recommendations")


class AuditorAgent:
    """Auditor Agent for quality control"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen hukuki yanıtların kalitesini denetleyen uzman bir yapay zeka asistanısın.

Değerlendirme Kriterleri:
1. Faithfulness (Sadakat): Cevap kaynaklara sadık mı?
2. Relevance (Uygunluk): Soruyu yanıtlıyor mu?
3. Consistency (Tutarlılık): Çelişki var mı?

Geçme Kriteri: Her skor >= 0.7"""),
            ("human", """Soru: {query}

Cevap:
{answer}

Kaynaklar:
{sources}

Bu cevabı denetle.""")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(AuditOutput)
    
    async def audit(
        self,
        query: str,
        answer: str,
        sources: List[Dict]
    ) -> VerificationResult:
        """Audit answer quality"""
        try:
            logger.info("Auditing answer quality...")
            
            formatted_sources = self._format_sources(sources)
            result = await self.chain.ainvoke({
                "query": query,
                "answer": answer,
                "sources": formatted_sources
            })
            
            # Validate citations
            citation_valid, citation_issues = self._validate_citations(answer, sources)
            
            avg_score = (
                result.faithfulness_score + 
                result.relevance_score + 
                result.consistency_score
            ) / 3
            
            # Adjust score based on citation validation
            if not citation_valid:
                avg_score *= 0.9  # 10% penalty for invalid citations
                logger.warning("Citation validation issues detected")
            
            passed = (
                result.faithfulness_score >= 0.7 and
                result.relevance_score >= 0.7 and
                result.consistency_score >= 0.8 and
                avg_score >= 0.75 and
                citation_valid
            )
            
            logger.info(f"Audit: {'PASSED' if passed else 'FAILED'} (Citations: {'VALID' if citation_valid else 'INVALID'})")
            
            # Merge issues
            all_issues = result.issues + citation_issues
            
            return VerificationResult(
                passed=passed,
                faithfulness_score=result.faithfulness_score,
                relevance_score=result.relevance_score,
                consistency_score=result.consistency_score,
                feedback=result.feedback,
                issues=all_issues
            )
            
        except Exception as e:
            logger.error(f"Audit error: {e}")
            return VerificationResult(
                passed=True,
                faithfulness_score=0.5,
                relevance_score=0.5,
                consistency_score=0.5,
                feedback=f"Audit error: {str(e)}",
                issues=["Audit failed"]
            )
    
    def _validate_citations(
        self, 
        answer: str, 
        sources: List[Dict]
    ) -> tuple[bool, List[str]]:
        """Validate if citations in answer match available sources
        
        Args:
            answer: Generated answer
            sources: Available source documents
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        try:
            from backend.tools.legal_parser import legal_parser
            
            issues = []
            
            # Parse references in answer
            answer_refs = legal_parser.parse(answer)
            if not answer_refs:
                return True, []  # No citations to validate
            
            # Parse references in sources
            source_refs = set()
            for source in sources:
                text = source.get("text", "")
                metadata = source.get("payload") or source.get("metadata", {})
                
                # Add references from source text
                refs = legal_parser.parse(text)
                for ref in refs:
                    source_refs.add(legal_parser.format_reference(ref))
                
                # Add source identifier
                if metadata.get("madde_no"):
                    source_refs.add(f"{metadata.get('kaynak', '')} m.{metadata.get('madde_no')}")
            
            # Check if answer references are in sources
            unmatched = 0
            for ref in answer_refs:
                formatted = legal_parser.format_reference(ref)
                if formatted not in source_refs:
                    unmatched += 1
                    logger.debug(f"Unmatched citation: {formatted}")
            
            if unmatched > 0:
                issues.append(f"{unmatched} citation(s) not found in sources")
                return False, issues
            
            logger.debug(f"✅ All {len(answer_refs)} citations validated")
            return True, []
            
        except Exception as e:
            logger.error(f"Citation validation error: {e}")
            return True, []  # Don't fail on validation error
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """Format sources for audit"""
        if not sources:
            return "Kaynak yok"
        formatted = []
        for i, source in enumerate(sources[:10], 1):
            # Support both payload (Qdrant) and metadata (FAISS)
            metadata = source.get("payload") or source.get("metadata", {})
            content = metadata.get('content') or source.get('text', '')
            formatted.append(f"{i}. {metadata.get('kaynak', 'Bilinmiyor')}: {content[:200]}...")
        return "\n".join(formatted)


# Global instance
auditor_agent = AuditorAgent()
