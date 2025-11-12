"""PDF Processing utilities for legal documents"""

import re
import logging
from typing import List, Dict, Optional, Tuple
import pdfplumber
from pathlib import Path

logger = logging.getLogger(__name__)


class LegalPDFProcessor:
    """Process legal PDF documents and extract structured information"""
    
    # Patterns for Turkish legal articles
    MADDE_PATTERN = r'(?:MADDE|Madde)\s*[:-]?\s*(\d+)'
    FIKRA_PATTERN = r'\((\d+)\)'
    BENT_PATTERN = r'([a-z])\)'
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract all text from PDF
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Extracted text
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise
    
    def detect_law_type(self, text: str) -> Tuple[str, str]:
        """Detect law type from PDF content
        
        Args:
            text: PDF text content
        
        Returns:
            (law_code, law_name) tuple
        """
        # Common Turkish law patterns
        law_patterns = {
            r'T[İI]CARET KANUNU|TTK': ('TTK', 'Türk Ticaret Kanunu'),
            r'BOR[ÇC]LAR KANUNU|TBK': ('TBK', 'Türk Borçlar Kanunu'),
            r'[İI]CRA VE [İI]FL[AÂ]S KANUNU|[İI][İI]K': ('İİK', 'İcra ve İflas Kanunu'),
            r'MEDEN[İI] KANUN|TMK': ('TMK', 'Türk Medeni Kanunu'),
            r'T[ÜU]KET[İI]C[İI].*?KORUNMASI|TKHK': ('TKHK', 'Tüketicinin Korunması Hakkında Kanun'),
            r'[İI][ŞS] KANUNU|[İI][ŞS]K': ('İşK', 'İş Kanunu'),
            r'HUKUK MUHAKEMELERI KANUNU|HMK': ('HMK', 'Hukuk Muhakemeleri Kanunu'),
        }
        
        text_upper = text[:2000].upper()  # Check first 2000 chars
        
        for pattern, (code, name) in law_patterns.items():
            if re.search(pattern, text_upper):
                logger.info(f"Detected law: {code} - {name}")
                return code, name
        
        logger.warning("Could not detect law type, defaulting to GENEL")
        return "GENEL", "Genel Mevzuat"
    
    def extract_articles(self, text: str, law_code: str) -> List[Dict]:
        """Extract individual articles from text
        
        Args:
            text: Full PDF text
            law_code: Law code (TTK, TBK, etc.)
        
        Returns:
            List of article dictionaries
        """
        articles = []
        
        # Split by article markers
        # Pattern: MADDE 123 or Madde 123
        parts = re.split(self.MADDE_PATTERN, text, flags=re.IGNORECASE)
        
        if len(parts) < 3:
            logger.warning("No articles found with standard pattern")
            # Try alternative chunking
            return self._chunk_by_size(text, law_code)
        
        # Skip first part (header/intro)
        for i in range(1, len(parts), 2):
            if i + 1 >= len(parts):
                break
            
            madde_no = parts[i].strip()
            content = parts[i + 1].strip()
            
            # Get title if exists (usually first line or until first period/colon)
            title_match = re.match(r'^[^\n\.]+', content)
            title = title_match.group(0).strip() if title_match else f"Madde {madde_no}"
            
            # Clean up content (remove excessive whitespace)
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Limit content length (take first 2000 chars for very long articles)
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            articles.append({
                "madde_no": madde_no,
                "title": title[:200],  # Limit title length
                "content": content,
                "kaynak": law_code
            })
        
        logger.info(f"Extracted {len(articles)} articles from PDF")
        return articles
    
    def _chunk_by_size(self, text: str, law_code: str, chunk_size: int = 1000) -> List[Dict]:
        """Fallback: chunk text by size when article detection fails
        
        Args:
            text: Full text
            law_code: Law code
            chunk_size: Characters per chunk
        
        Returns:
            List of chunks as pseudo-articles
        """
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        chunk_id = 1
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    "madde_no": f"chunk_{chunk_id}",
                    "title": f"{law_code} Bölüm {chunk_id}",
                    "content": chunk_text,
                    "kaynak": law_code
                })
                current_chunk = []
                current_size = 0
                chunk_id += 1
        
        # Add remaining
        if current_chunk:
            chunks.append({
                "madde_no": f"chunk_{chunk_id}",
                "title": f"{law_code} Bölüm {chunk_id}",
                "content": ' '.join(current_chunk),
                "kaynak": law_code
            })
        
        logger.info(f"Created {len(chunks)} chunks from PDF")
        return chunks
    
    def process_pdf(self, pdf_path: str) -> Tuple[str, str, List[Dict]]:
        """Complete PDF processing pipeline
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            (law_code, law_name, articles) tuple
        """
        try:
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text or len(text) < 100:
                raise ValueError("PDF appears to be empty or unreadable")
            
            # Detect law type
            law_code, law_name = self.detect_law_type(text)
            
            # Extract articles
            articles = self.extract_articles(text, law_code)
            
            if not articles:
                raise ValueError("No articles could be extracted")
            
            logger.info(f"Successfully processed PDF: {law_code} with {len(articles)} articles")
            
            return law_code, law_name, articles
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise


# Global instance
pdf_processor = LegalPDFProcessor()
