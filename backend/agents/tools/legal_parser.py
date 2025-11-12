"""Legal text parsing tools"""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class MaddeReference(BaseModel):
    """Madde reference structure"""
    kanun: str  # TTK, TBK, etc.
    madde_no: int
    fikra_no: Optional[int] = None
    bent: Optional[str] = None
    raw_text: str


class LegalParser:
    """Parser for Turkish legal text"""
    
    # Law abbreviations
    LAW_ABBREVIATIONS = [
        "TTK", "TBK", "İİK", "TMK", "TKHK", "HMK",
        "TCK", "CMK", "VUK", "KVK", "SGK"
    ]
    
    def parse_madde_reference(self, text: str) -> List[MaddeReference]:
        """Parse madde references from text
        
        Examples:
            - "TTK 11"
            - "TTK m.11"
            - "TTK madde 11"
            - "TTK m.11/2-c"
            - "TBK'nın 1. maddesi"
        
        Args:
            text: Text to parse
        
        Returns:
            List of MaddeReference objects
        """
        references = []
        
        # Pattern 1: TTK m.11/2-c
        pattern1 = r"\b(" + "|".join(self.LAW_ABBREVIATIONS) + r")\s*m\.(\d+)(?:/(\d+))?(?:-(\w+))?"
        for match in re.finditer(pattern1, text, re.IGNORECASE):
            ref = MaddeReference(
                kanun=match.group(1).upper(),
                madde_no=int(match.group(2)),
                fikra_no=int(match.group(3)) if match.group(3) else None,
                bent=match.group(4).lower() if match.group(4) else None,
                raw_text=match.group(0)
            )
            references.append(ref)
        
        # Pattern 2: TTK madde 11
        pattern2 = r"\b(" + "|".join(self.LAW_ABBREVIATIONS) + r")\s+(?:madde|md)\s+(\d+)"
        for match in re.finditer(pattern2, text, re.IGNORECASE):
            ref = MaddeReference(
                kanun=match.group(1).upper(),
                madde_no=int(match.group(2)),
                raw_text=match.group(0)
            )
            if ref not in references:  # Avoid duplicates
                references.append(ref)
        
        # Pattern 3: TTK 11 (without m. or madde)
        pattern3 = r"\b(" + "|".join(self.LAW_ABBREVIATIONS) + r")\s+(\d+)\b"
        for match in re.finditer(pattern3, text, re.IGNORECASE):
            ref = MaddeReference(
                kanun=match.group(1).upper(),
                madde_no=int(match.group(2)),
                raw_text=match.group(0)
            )
            # Check if not already found by other patterns
            if not any(r.kanun == ref.kanun and r.madde_no == ref.madde_no for r in references):
                references.append(ref)
        
        logger.info(f"Parsed {len(references)} madde references")
        return references
    
    def extract_madde_text(self, text: str, madde_no: int) -> Optional[str]:
        """Extract specific madde text from document
        
        Args:
            text: Full document text
            madde_no: Article number to extract
        
        Returns:
            Article text or None
        """
        # Pattern: MADDE 11 - [content until next MADDE]
        pattern = rf"(?:MADDE|Madde)\s+{madde_no}\s*[-–—]\s*(.+?)(?=(?:MADDE|Madde)\s+\d+|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        return None
    
    def split_into_fikralar(self, madde_text: str) -> List[Dict]:
        """Split madde text into fıkralar (paragraphs)
        
        Args:
            madde_text: Article text
        
        Returns:
            List of fıkra dictionaries
        """
        fikralar = []
        
        # Pattern: (1), (2), etc.
        pattern = r"\((\d+)\)\s*([^(]+)"
        matches = list(re.finditer(pattern, madde_text))
        
        if matches:
            for match in matches:
                fikralar.append({
                    "fikra_no": int(match.group(1)),
                    "text": match.group(2).strip()
                })
        else:
            # No numbered paragraphs, treat as single fıkra
            fikralar.append({
                "fikra_no": 1,
                "text": madde_text.strip()
            })
        
        return fikralar
    
    def extract_bentler(self, fikra_text: str) -> List[Dict]:
        """Extract bentler (subparagraphs) from fıkra
        
        Args:
            fikra_text: Paragraph text
        
        Returns:
            List of bent dictionaries
        """
        bentler = []
        
        # Pattern: a), b), c), etc.
        pattern = r"([a-zçğıöşü])\)\s*([^a-zçğıöşü)]+)"
        matches = list(re.finditer(pattern, fikra_text, re.IGNORECASE))
        
        for match in matches:
            bentler.append({
                "bent": match.group(1).lower(),
                "text": match.group(2).strip()
            })
        
        return bentler
    
    def format_reference(self, ref: MaddeReference) -> str:
        """Format madde reference as string
        
        Args:
            ref: MaddeReference object
        
        Returns:
            Formatted string (e.g., "TTK m.11/2-c")
        """
        result = f"{ref.kanun} m.{ref.madde_no}"
        if ref.fikra_no:
            result += f"/{ref.fikra_no}"
        if ref.bent:
            result += f"-{ref.bent}"
        return result


# Global parser instance
legal_parser = LegalParser()
