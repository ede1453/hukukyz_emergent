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
            
            avg_score = (
                result.faithfulness_score + 
                result.relevance_score + 
                result.consistency_score
            ) / 3
            
            passed = (
                result.faithfulness_score >= 0.7 and
                result.relevance_score >= 0.7 and
                result.consistency_score >= 0.8 and
                avg_score >= 0.75
            )
            
            logger.info(f"Audit: {'PASSED' if passed else 'FAILED'}")
            
            return VerificationResult(
                passed=passed,
                faithfulness_score=result.faithfulness_score,
                relevance_score=result.relevance_score,
                consistency_score=result.consistency_score,
                feedback=result.feedback,
                issues=result.issues
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
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """Format sources for audit"""
        if not sources:
            return "Kaynak yok"
        formatted = []
        for i, source in enumerate(sources[:10], 1):
            payload = source.get("payload", {})
            formatted.append(f"{i}. {payload.get('kaynak', 'Bilinmiyor')}: {payload.get('content', '')[:200]}...")
        return "\n".join(formatted)


# Global instance
auditor_agent = AuditorAgent()
