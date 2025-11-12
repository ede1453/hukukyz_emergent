"""Analyst Agent - Legal analysis and cross-referencing"""

from typing import List, Dict
from pydantic import BaseModel, Field
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings

logger = logging.getLogger(__name__)


class AnalysisOutput(BaseModel):
    """Analysis output"""
    analysis: str = Field(description="Detailed legal analysis")
    cross_references: List[Dict] = Field(description="Cross-referenced articles")
    relationships: List[str] = Field(description="Relationships between documents")
    insights: List[str] = Field(description="Key insights")


class AnalystAgent:
    """Analyst Agent for legal analysis and cross-referencing"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Türk hukuku konusunda uzman bir hukuk analisti yapay zeka asistanısın.
Görevin: Bulunan hukuki belgeleri analiz edip, aralarındaki ilişkileri belirlemek.

Analiz Yapısı:
1. Genel Değerlendirme
2. Madde Bazlı Analiz
3. İçtihat Uygulaması
4. Önemli Noktalar"""),
            ("human", """Belgeler:
{documents}

Bu belgeleri analiz et.""")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(AnalysisOutput)
    
    async def analyze(
        self,
        documents: List[Dict],
        analysis_type: str = "comprehensive"
    ) -> Dict:
        """Analyze legal documents"""
        try:
            logger.info(f"Analyzing {len(documents)} documents")
            
            if not documents:
                return self._empty_analysis()
            
            formatted_docs = self._format_documents(documents)
            result = await self.chain.ainvoke({"documents": formatted_docs})
            
            return {
                "analysis": result.analysis,
                "cross_references": result.cross_references,
                "relationships": result.relationships,
                "insights": result.insights
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return self._empty_analysis()
    
    def _format_documents(self, documents: List[Dict]) -> str:
        """Format documents for analysis"""
        formatted = []
        for i, doc in enumerate(documents, 1):
            payload = doc.get("payload", {})
            doc_str = f"\n=== Belge {i} ===\n"
            doc_str += f"Kaynak: {payload.get('kaynak', 'Bilinmiyor')}\n"
            doc_str += f"\n{payload.get('content', '')[:500]}...\n"
            formatted.append(doc_str)
        return "\n".join(formatted)
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis"""
        return {
            "analysis": "Analiz için yeterli belge bulunamadı.",
            "cross_references": [],
            "relationships": [],
            "insights": []
        }


# Global instance
analyst_agent = AnalystAgent()
