"""Meta-Controller Agent - Task Router"""

from typing import Dict, List
from pydantic import BaseModel, Field
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.agents.state import AgentState

logger = logging.getLogger(__name__)


class MetaControllerOutput(BaseModel):
    """Meta-Controller output"""
    hukuk_dali: List[str] = Field(description="Detected legal domains")
    kaynak_tipi: List[str] = Field(description="Source types needed")
    collections: List[str] = Field(description="Qdrant collections to search")
    reasoning: str = Field(description="Reasoning for decisions")


class MetaControllerAgent:
    """Meta-Controller Agent for task routing"""
    
    # Mapping from legal domain to Qdrant collection
    # Including both Turkish and ASCII versions for LLM compatibility
    DOMAIN_TO_COLLECTION = {
        "ticaret": "ticaret_hukuku",
        "ticaret hukuku": "ticaret_hukuku",
        "ttk": "ticaret_hukuku",
        "borçlar": "borclar_hukuku",
        "borclar": "borclar_hukuku",  # ASCII version
        "borçlar hukuku": "borclar_hukuku",
        "borclar hukuku": "borclar_hukuku",  # ASCII version
        "tbk": "borclar_hukuku",
        "icra": "icra_iflas",
        "iflas": "icra_iflas",
        "icra iflas": "icra_iflas",
        "iik": "icra_iflas",
        "medeni": "medeni_hukuk",
        "medeni hukuk": "medeni_hukuk",
        "tmk": "medeni_hukuk",
        "tüketici": "tuketici_haklari",
        "tuketici": "tuketici_haklari",  # ASCII version
        "tüketici hakları": "tuketici_haklari",
        "tuketici haklari": "tuketici_haklari",  # ASCII version
        "tkhk": "tuketici_haklari",
        "bankacılık": "bankacilik_hukuku",
        "bankacilik": "bankacilik_hukuku",  # ASCII version
        "bankacılık hukuku": "bankacilik_hukuku",
        "bankacilik hukuku": "bankacilik_hukuku",  # ASCII version
        "hmk": "hmk",
        "hukuk muhakemeleri": "hmk"
    }
    
    # Known law abbreviations
    LAW_ABBREVIATIONS = [
        "TTK", "TBK", "İİK", "TMK", "TKHK", "HMK",
        "TCK", "CMK", "VUK"
    ]
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Türk hukuku konusunda uzman bir yapay zeka asistanısın.
Görevin, kullanıcı sorgusunu analiz edip hangi hukuk dalı ve kaynak tiplerinin gerekli olduğunu belirlemek.

Hukuk Dalları:
- ticaret: Ticaret hukuku (TTK - anonim şirket, limited şirket, ticari işletme)
- borclar: Borçlar hukuku (TBK - sözleşmeler, tazminat, iş hukuku)
- icra: İcra ve İflas hukuku (İİK - haciz, iflas, alacak takibi)
- medeni: Medeni hukuk (TMK - kişi, aile, miras, eşya hukuku)
- tuketici: Tüketici hakları (TKHK - cayma hakkı, ayıplı mal, tüketici mahkemesi)
- bankacilik: Bankacılık hukuku
- hmk: Hukuk Muhakemeleri Kanunu (HMK - dava, delil, usul)

Kaynak Tipleri:
- kanun: Kanun metinleri
- yonetmelik: Yönetmelikler
- ictihat: Yargı kararları (Yargıtay, Danıştay, AYM)
- akademik: Akademik makaleler ve dergiler

JSON formatında yanıt ver:
{{
  "hukuk_dali": ["ticaret"],
  "kaynak_tipi": ["kanun", "ictihat"],
  "reasoning": "Sorgu TTK ile ilgili, bu yüzden ticaret hukuku koleksiyonunda arama yapılmalı"
}}"""),
            ("human", "Sorgu: {query}")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(MetaControllerOutput)
    
    async def analyze(self, state: AgentState) -> Dict:
        """Analyze query and determine routing
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state fields
        """
        try:
            query = state["query"]
            logger.info(f"Meta-Controller analyzing query: {query[:100]}...")
            
            # Quick pattern matching for common cases
            collections = self._quick_match(query)
            
            if collections:
                logger.info(f"Quick match found: {collections}")
                return {
                    "hukuk_dali": list(set([self._get_domain_from_collection(c) for c in collections])),
                    "collections": collections
                }
            
            # Use LLM for complex queries
            result = await self.chain.ainvoke({"query": query})
            
            # Map domains to collections
            collections = []
            for domain in result.hukuk_dali:
                if domain.lower() in self.DOMAIN_TO_COLLECTION:
                    collections.append(self.DOMAIN_TO_COLLECTION[domain.lower()])
            
            logger.info(f"LLM analysis: domains={result.hukuk_dali}, collections={collections}")
            
            return {
                "hukuk_dali": result.hukuk_dali,
                "kaynak_tipi": result.kaynak_tipi,
                "collections": collections
            }
            
        except Exception as e:
            logger.error(f"Meta-Controller error: {e}")
            # Fallback: search all collections
            return {
                "hukuk_dali": ["genel"],
                "kaynak_tipi": ["kanun"],
                "collections": list(self.DOMAIN_TO_COLLECTION.values())
            }
    
    def _quick_match(self, query: str) -> List[str]:
        """Quick pattern matching for law abbreviations"""
        query_upper = query.upper()
        collections = []
        
        for abbr in self.LAW_ABBREVIATIONS:
            if abbr in query_upper:
                # Map abbreviation to collection
                domain_key = abbr.lower()
                if domain_key in self.DOMAIN_TO_COLLECTION:
                    collection = self.DOMAIN_TO_COLLECTION[domain_key]
                    if collection not in collections:
                        collections.append(collection)
        
        return collections
    
    def _get_domain_from_collection(self, collection: str) -> str:
        """Get domain name from collection name"""
        mapping = {
            "ticaret_hukuku": "ticaret",
            "borclar_hukuku": "borclar",
            "icra_iflas": "icra",
            "medeni_hukuk": "medeni",
            "tuketici_haklari": "tuketici",
            "bankacilik_hukuku": "bankacilik",
            "hmk": "hmk"
        }
        return mapping.get(collection, "genel")


# Global instance
meta_controller = MetaControllerAgent()
