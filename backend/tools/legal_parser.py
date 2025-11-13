"""Legal Parser - Parse legal references and citations

Parses Turkish legal references like:
- TTK m.11
- TBK Madde 123
- İİK m.68/1
- Yargıtay 11. HD. 2019/1234 E., 2020/5678 K.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReferenceType(Enum):
    """Types of legal references"""
    KANUN = "kanun"  # Law article (e.g., TTK m.11)
    YONETMELIK = "yonetmelik"  # Regulation
    ICTIHAT = "ictihat"  # Case law (Yargıtay, Danıştay, AYM)
    MADDE = "madde"  # Article reference


@dataclass
class LegalReference:
    """Parsed legal reference"""
    raw_text: str  # Original text
    ref_type: ReferenceType
    kanun_kodu: Optional[str] = None  # Law code (TTK, TBK, etc.)
    madde_no: Optional[int] = None  # Article number
    fikra_no: Optional[int] = None  # Paragraph number
    bent: Optional[str] = None  # Subparagraph (a, b, c, etc.)
    mahkeme: Optional[str] = None  # Court name (for case law)
    esas_no: Optional[str] = None  # Case number
    karar_no: Optional[str] = None  # Decision number
    confidence: float = 1.0  # Parsing confidence


class LegalParser:
    """Parser for Turkish legal references"""
    
    # Known law codes
    LAW_CODES = {
        "TTK": "Türk Ticaret Kanunu",
        "TBK": "Türk Borçlar Kanunu",
        "TMK": "Türk Medeni Kanunu",
        "İİK": "İcra ve İflas Kanunu",
        "IIK": "İcra ve İflas Kanunu",  # ASCII version
        "TKHK": "Tüketici Kanunu",
        "HMK": "Hukuk Muhakemeleri Kanunu",
        "CMK": "Ceza Muhakemesi Kanunu",
        "TCK": "Türk Ceza Kanunu",
        "VUK": "Vergi Usul Kanunu",
        "GVK": "Gelir Vergisi Kanunu",
        "KVK": "Kurumlar Vergisi Kanunu"
    }
    
    # Regex patterns
    PATTERNS = {
        # TTK m.11, TBK Madde 123, İİK m.68/1-a
        "madde": re.compile(
            r'(TTK|TBK|TMK|İİK|IIK|TKHK|HMK|CMK|TCK|VUK|GVK|KVK)\s*'
            r'(?:m\.|madde|Madde|MADDE)?\s*'
            r'(\d+)'
            r'(?:/(\d+))?'  # Fikra
            r'(?:-([a-z]))?'  # Bent
            r'',
            re.IGNORECASE
        ),
        
        # Yargıtay 11. HD. 2019/1234 E., 2020/5678 K.
        "yargitay": re.compile(
            r'(Yargıtay|YARGITAY)\s+'
            r'(\d+)\.\s*(HD|Hukuk Dairesi|CD|Ceza Dairesi)\s*'
            r'(?:(\d{4})/(\d+)\s*E\.?)?\s*'  # Esas
            r'(?:,?\s*(\d{4})/(\d+)\s*K\.?)?'  # Karar
            r'',
            re.IGNORECASE
        ),
        
        # Danıştay references
        "danistay": re.compile(
            r'(Danıştay|DANIŞTAY)\s+'
            r'(\d+)\.\s*Daire\s*'
            r'(?:(\d{4})/(\d+)\s*E\.?)?\s*'
            r'(?:,?\s*(\d{4})/(\d+)\s*K\.?)?'
            r'',
            re.IGNORECASE
        ),
        
        # AYM (Anayasa Mahkemesi)
        "aym": re.compile(
            r'(AYM|Anayasa Mahkemesi)\s*'
            r'(?:(\d{4})/(\d+)\s*)?'
            r'',
            re.IGNORECASE
        )
    }
    
    def parse(self, text: str) -> List[LegalReference]:
        """Parse all legal references in text
        
        Args:
            text: Input text containing legal references
        
        Returns:
            List of parsed references
        """
        references = []
        
        # Parse law articles
        references.extend(self._parse_madde_references(text))
        
        # Parse case law
        references.extend(self._parse_yargitay_references(text))
        references.extend(self._parse_danistay_references(text))
        references.extend(self._parse_aym_references(text))
        
        logger.debug(f"Parsed {len(references)} legal references from text")
        return references
    
    def _parse_madde_references(self, text: str) -> List[LegalReference]:
        """Parse law article references"""
        references = []
        
        for match in self.PATTERNS["madde"].finditer(text):
            kanun_kodu = match.group(1).upper()
            madde_no = int(match.group(2))
            fikra_no = int(match.group(3)) if match.group(3) else None
            bent = match.group(4) if match.group(4) else None
            
            # Normalize İİK/IIK
            if kanun_kodu in ["İİK", "IIK"]:
                kanun_kodu = "İİK"
            
            ref = LegalReference(
                raw_text=match.group(0),
                ref_type=ReferenceType.MADDE,
                kanun_kodu=kanun_kodu,
                madde_no=madde_no,
                fikra_no=fikra_no,
                bent=bent,
                confidence=1.0
            )
            references.append(ref)
        
        return references
    
    def _parse_yargitay_references(self, text: str) -> List[LegalReference]:
        """Parse Yargıtay case law references"""
        references = []
        
        for match in self.PATTERNS["yargitay"].finditer(text):
            daire_no = match.group(2)
            daire_type = match.group(3)
            esas_yil = match.group(4)
            esas_no = match.group(5)
            karar_yil = match.group(6)
            karar_no = match.group(7)
            
            mahkeme = f"Yargıtay {daire_no}. {daire_type}"
            
            ref = LegalReference(
                raw_text=match.group(0),
                ref_type=ReferenceType.ICTIHAT,
                mahkeme=mahkeme,
                esas_no=f"{esas_yil}/{esas_no}" if esas_yil and esas_no else None,
                karar_no=f"{karar_yil}/{karar_no}" if karar_yil and karar_no else None,
                confidence=0.9
            )
            references.append(ref)
        
        return references
    
    def _parse_danistay_references(self, text: str) -> List[LegalReference]:
        """Parse Danıştay case law references"""
        references = []
        
        for match in self.PATTERNS["danistay"].finditer(text):
            daire_no = match.group(2)
            esas_yil = match.group(3)
            esas_no = match.group(4)
            karar_yil = match.group(5)
            karar_no = match.group(6)
            
            mahkeme = f"Danıştay {daire_no}. Daire"
            
            ref = LegalReference(
                raw_text=match.group(0),
                ref_type=ReferenceType.ICTIHAT,
                mahkeme=mahkeme,
                esas_no=f"{esas_yil}/{esas_no}" if esas_yil and esas_no else None,
                karar_no=f"{karar_yil}/{karar_no}" if karar_yil and karar_no else None,
                confidence=0.9
            )
            references.append(ref)
        
        return references
    
    def _parse_aym_references(self, text: str) -> List[LegalReference]:
        """Parse Anayasa Mahkemesi references"""
        references = []
        
        for match in self.PATTERNS["aym"].finditer(text):
            esas_yil = match.group(2)
            esas_no = match.group(3)
            
            ref = LegalReference(
                raw_text=match.group(0),
                ref_type=ReferenceType.ICTIHAT,
                mahkeme="Anayasa Mahkemesi",
                esas_no=f"{esas_yil}/{esas_no}" if esas_yil and esas_no else None,
                confidence=0.8
            )
            references.append(ref)
        
        return references
    
    def format_reference(self, ref: LegalReference) -> str:
        """Format reference for display
        
        Args:
            ref: Legal reference
        
        Returns:
            Formatted string
        """
        if ref.ref_type == ReferenceType.MADDE:
            parts = [f"{ref.kanun_kodu} m.{ref.madde_no}"]
            if ref.fikra_no:
                parts.append(f"/{ref.fikra_no}")
            if ref.bent:
                parts.append(f"-{ref.bent}")
            return "".join(parts)
        
        elif ref.ref_type == ReferenceType.ICTIHAT:
            parts = [ref.mahkeme]
            if ref.esas_no:
                parts.append(f"E.{ref.esas_no}")
            if ref.karar_no:
                parts.append(f"K.{ref.karar_no}")
            return " ".join(parts)
        
        return ref.raw_text
    
    def extract_law_codes(self, text: str) -> List[str]:
        """Extract all law codes mentioned in text
        
        Args:
            text: Input text
        
        Returns:
            List of unique law codes
        """
        codes = set()
        references = self.parse(text)
        
        for ref in references:
            if ref.kanun_kodu:
                codes.add(ref.kanun_kodu)
        
        return sorted(list(codes))
    
    def get_law_name(self, code: str) -> Optional[str]:
        """Get full name of law from code
        
        Args:
            code: Law code (e.g., TTK)
        
        Returns:
            Full law name or None
        """
        return self.LAW_CODES.get(code.upper())


# Global parser instance
legal_parser = LegalParser()
