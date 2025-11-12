"""Planner Agent - Multi-step query decomposition"""

from typing import List, Dict
from pydantic import BaseModel, Field
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from backend.agents.state import AgentState, Step

logger = logging.getLogger(__name__)


class PlanOutput(BaseModel):
    """Planner output"""
    steps: List[Step] = Field(description="Ordered list of steps")
    reasoning: str = Field(description="Reasoning for the plan")
    estimated_complexity: str = Field(description="Query complexity: simple, medium, complex")


class PlannerAgent:
    """Planner Agent for query decomposition"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Slightly creative for planning
            api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen hukuki sorgular için stratejik planlama uzman bir yapay zeka asistanısın.

Görevin: Kullanıcı sorgusunu analiz edip, cevaplamak için gerekli adımları belirlemek.

Kullanılabilir Araçlar:
1. **researcher**: Qdrant vektör veritabanında semantik arama
   - Kanun metinleri, yönetmelikler için
   - Koleksiyonlar: {collections}

2. **web_scout**: İnternet'te güncel bilgi arama
   - İçtihatlar, mahkeme kararları için
   - Akademik makaleler için

3. **analyst**: Hukuki analiz ve çapraz referanslama
   - Bulunan bilgileri analiz etme
   - Madde-madde ilişkilendirme

Plan Oluşturma Kuralları:
- Basit sorgular: 1-2 adım (tek madde sorgusu)
- Orta sorgular: 2-4 adım (çapraz referans gerektiren)
- Karmaşık sorgular: 4-7 adım (çoklu kaynak, analiz gerektiren)

Her adım için belirt:
- action: Ne yapılacak (net açıklama)
- tool: Hangi araç kullanılacak
- params: Araç parametreleri
- justification: Neden bu adım gerekli

Örnek Plan (Basit):
{{
  "steps": [
    {{
      "step": 1,
      "action": "TTK madde 11'i bul",
      "tool": "researcher",
      "params": {{"collection": "ticaret_hukuku", "query": "TTK madde 11 kuruluş"}},
      "justification": "Doğrudan madde metni gerekli"
    }}
  ],
  "reasoning": "Tek madde sorgusu, direkt arama yeterli",
  "estimated_complexity": "simple"
}}

Örnek Plan (Karmaşık):
{{
  "steps": [
    {{
      "step": 1,
      "action": "TTK madde 11'i bul",
      "tool": "researcher",
      "params": {{"collection": "ticaret_hukuku", "query": "TTK madde 11"}},
      "justification": "Temel kanun maddesi"
    }},
    {{
      "step": 2,
      "action": "İlgili Yargıtay kararlarını ara",
      "tool": "web_scout",
      "params": {{"keywords": ["TTK", "madde 11", "Yargıtay"], "court_type": "yargitay"}},
      "justification": "Uygulamadaki yorumlar önemli"
    }},
    {{
      "step": 3,
      "action": "Madde ve içtihatları analiz et",
      "tool": "analyst",
      "params": {{"analysis_type": "cross_reference"}},
      "justification": "Birleştirilmiş bakış açısı için"
    }}
  ],
  "reasoning": "Kanun + içtihat + analiz = kapsamlı cevap",
  "estimated_complexity": "complex"
}}"""),
            ("human", """Sorgu: {query}

Tespit edilen hukuk dalı: {hukuk_dali}
Koleksiyonlar: {collections}

Bu sorguyu yanıtlamak için adım adım plan oluştur.""")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(PlanOutput)
    
    async def create_plan(self, state: AgentState) -> Dict:
        """Create execution plan
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with plan
        """
        try:
            query = state["query"]
            hukuk_dali = state.get("hukuk_dali", [])
            collections = state.get("collections", [])
            
            logger.info(f"Planning for query: {query[:100]}...")
            
            # Check if simple query (single article reference)
            if self._is_simple_query(query):
                plan = self._create_simple_plan(query, collections)
            else:
                # Use LLM for complex planning
                result = await self.chain.ainvoke({
                    "query": query,
                    "hukuk_dali": ", ".join(hukuk_dali),
                    "collections": ", ".join(collections)
                })
                plan = result.steps
            
            logger.info(f"Created plan with {len(plan)} steps")
            
            return {
                "plan": [step if isinstance(step, dict) else step.model_dump() for step in plan],
                "current_step_index": 0
            }
            
        except Exception as e:
            logger.error(f"Planning error: {e}")
            # Fallback: simple search plan
            return {
                "plan": [{
                    "step": 1,
                    "action": f"Search for: {state['query']}",
                    "tool": "researcher",
                    "params": {
                        "collection": collections[0] if collections else "ticaret_hukuku",
                        "query": state["query"]
                    },
                    "justification": "Fallback simple search"
                }],
                "current_step_index": 0
            }
    
    def _is_simple_query(self, query: str) -> bool:
        """Check if query is simple (single article reference)"""
        # Pattern: "TTK 11", "TTK madde 11", "TBK m.1"
        import re
        patterns = [
            r"\b(TTK|TBK|İİK|TMK|TKHK|HMK)\s+(?:madde\s+)?(\d+)\b",
            r"\b(TTK|TBK|İİK|TMK|TKHK|HMK)\s+m\.(\d+)\b"
        ]
        
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # Check if asking for just the article text
                simple_keywords = ["nedir", "ne demek", "metni", "içeriği", "tam metni"]
                if any(keyword in query.lower() for keyword in simple_keywords):
                    return True
        
        return False
    
    def _create_simple_plan(self, query: str, collections: List[str]) -> List[Dict]:
        """Create simple plan for straightforward queries"""
        return [
            {
                "step": 1,
                "action": f"Retrieve article for: {query}",
                "tool": "researcher",
                "params": {
                    "collection": collections[0] if collections else "ticaret_hukuku",
                    "query": query,
                    "limit": 5
                },
                "justification": "Direct article retrieval"
            }
        ]


# Global instance
planner_agent = PlannerAgent()
