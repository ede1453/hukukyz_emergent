"""Synthesizer Agent - Final answer generation"""

from typing import List, Dict
from pydantic import BaseModel, Field
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.agents.state import AgentState, Citation

logger = logging.getLogger(__name__)


class SynthesisOutput(BaseModel):
    """Synthesizer output"""
    answer: str = Field(description="Final synthesized answer")
    citations: List[Citation] = Field(description="Citations with sources")
    confidence: float = Field(description="Confidence score (0-1)")
    reasoning: str = Field(description="Reasoning and analysis")


class SynthesizerAgent:
    """Synthesizer Agent for final answer generation"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.2,  # Slightly creative for natural language
            api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Türk hukuku konusunda uzman bir yapay zeka asistanısın.
Görevin: Toplanan bilgileri sentezleyip kullanıcıya kapsamlı, doğru ve kaynak gösterimli bir cevap vermek.

Önemli Kurallar:
1. **Sadece verilen kaynaklara dayanarak yanıt ver** - Hallusinasyon yapma
2. **Her iddiayı kaynakla destekle** - Kaynak belirtmeden bilgi verme
3. **Madde metinlerini doğrudan alıntıla** - Özgün haliyle sun
4. **Çelişkiler varsa belirt** - Farklı kaynaklardaki farklılıkları açıkla
5. **Hukuki dil kullan** - Ancak anlaşılır olsun
6. **İçtihatları örnekle** - Varsa mahkeme kararlarını da ekle

Yanıt Yapısı:
1. **Giriş**: Kısa özet (1-2 cümle)
2. **Ana Bilgi**: Detaylı açıklama
   - Kanun maddeleri (tam metin)
   - İlgili hükümler
   - Örnekler
3. **İçtihatlar**: Mahkeme kararları (varsa)
4. **Sonuç**: Özet ve pratik notlar

Kaynak Gösterimi:
Her paragrafta ilgili kaynağı belirt: [Kaynak: TTK m.11]

Güven Skoru:
- 0.9-1.0: Çok net, birden fazla kaynak destekli
- 0.7-0.9: İyi, tek kaynak veya kısmi bilgi
- 0.5-0.7: Orta, sınırlı kaynak
- 0.0-0.5: Düşük, belirsiz veya eksik bilgi"""),
            ("human", """Kullanıcı Sorusu: {query}

Bulunan Bilgiler:
{documents}

Bu bilgileri kullanarak kapsamlı, kaynak gösterimli bir cevap hazırla.""")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(SynthesisOutput)
    
    async def synthesize(
        self,
        query: str,
        documents: List[Dict]
    ) -> Dict:
        """Synthesize final answer from retrieved documents
        
        Args:
            query: Original user query
            documents: Retrieved documents
        
        Returns:
            Synthesis output with answer, citations, confidence
        """
        try:
            logger.info(f"Synthesizing answer from {len(documents)} documents")
            
            if not documents:
                return self._empty_response(query)
            
            # Format documents for prompt
            formatted_docs = self._format_documents(documents)
            
            # Generate synthesis
            result = await self.chain.ainvoke({
                "query": query,
                "documents": formatted_docs
            })
            
            logger.info(f"Synthesized answer with {len(result.citations)} citations")
            
            return {
                "final_answer": result.answer,
                "citations": [c.model_dump() if hasattr(c, 'model_dump') else c for c in result.citations],
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return self._empty_response(query)
    
    def _format_documents(self, documents: List[Dict]) -> str:
        """Format documents for prompt"""
        formatted = []
        
        for i, doc in enumerate(documents, 1):
            # Support both 'payload' (Qdrant) and 'metadata' (FAISS) formats
            metadata = doc.get("payload") or doc.get("metadata", {})
            
            doc_str = f"\n--- Belge {i} ---\n"
            doc_str += f"Kaynak: {metadata.get('kaynak', 'Bilinmiyor')}\n"
            
            if "madde_no" in metadata:
                doc_str += f"Madde: {metadata['madde_no']}\n"
            
            if "title" in metadata:
                doc_str += f"Başlık: {metadata['title']}\n"
            
            # Get content from multiple possible locations
            content = metadata.get('content') or doc.get('text', '')
            doc_str += f"\n{content}\n"
            
            # Add score
            if "score" in doc:
                doc_str += f"\n(Alakalılık: {doc['score']:.2f})\n"
            
            formatted.append(doc_str)
        
        return "\n".join(formatted)
    
    def _empty_response(self, query: str) -> Dict:
        """Generate response when no documents found"""
        return {
            "final_answer": f"""Maalesef "{query}" ile ilgili veri tabanımızda yeterli bilgi bulamadım.

Sebebi:
- Aranan konu veri tabanında henüz bulunmuyor olabilir
- Sorgu çok özel veya nadir bir konu olabilir
- Kullanılan anahtar kelimeler uygun olmayabilir

Öneriler:
- Daha genel bir sorgu deneyin
- Kanun adlarını tam olarak belirtin (TTK, TBK, vb.)
- Madde numarası biliyorsanız belirtin
""",
            "citations": [],
            "confidence": 0.0,
            "reasoning": "No documents retrieved"
        }


# Global instance
synthesizer_agent = SynthesizerAgent()
