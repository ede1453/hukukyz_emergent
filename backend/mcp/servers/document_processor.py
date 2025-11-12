"""Document Processing MCP Server"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import logging
import re
import PyPDF2
from pathlib import Path

from backend.mcp.base import MCPServer

logger = logging.getLogger(__name__)


# Input/Output Schemas
class ParsePDFInput(BaseModel):
    """Input for parse_pdf tool"""
    file_path: str = Field(description="Path to PDF file")
    doc_type: str = Field(description="Document type: kanun, yonetmelik, ictihat, etc.")
    hukuk_dali: str = Field(description="Legal domain")


class ParsePDFOutput(BaseModel):
    """Output for parse_pdf tool"""
    text: str
    metadata: Dict
    page_count: int
    extracted_articles: List[Dict]


class ChunkDocumentInput(BaseModel):
    """Input for chunk_document tool"""
    text: str
    strategy: str = Field(default="madde_based", description="Chunking strategy")
    chunk_size: int = Field(default=1000, description="Max chunk size")
    overlap: int = Field(default=100, description="Chunk overlap")


class ChunkDocumentOutput(BaseModel):
    """Output for chunk_document tool"""
    chunks: List[Dict]
    total_chunks: int


class ExtractArticlesInput(BaseModel):
    """Input for extract_articles tool"""
    text: str
    doc_type: str = Field(description="Document type")


class ExtractArticlesOutput(BaseModel):
    """Output for extract_articles tool"""
    articles: List[Dict]
    total_articles: int


class DocumentProcessorServer(MCPServer):
    """MCP Server for document processing operations"""
    
    def __init__(self):
        super().__init__(name="document_processor", version="1.0.0")
    
    async def initialize(self):
        """Initialize server"""
        logger.info("Document Processor Server initialized")
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools"""
        
        @self.tool(
            name="parse_pdf",
            description="Parse PDF and extract text and metadata",
            input_schema=ParsePDFInput,
            output_schema=ParsePDFOutput
        )
        async def parse_pdf(input_data: ParsePDFInput) -> ParsePDFOutput:
            """Parse PDF document"""
            try:
                if isinstance(input_data, BaseModel):
                    params = input_data.model_dump()
                else:
                    params = input_data
                
                file_path = params["file_path"]
                doc_type = params["doc_type"]
                hukuk_dali = params["hukuk_dali"]
                
                # Read PDF
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                    
                    # Extract metadata
                    metadata = {
                        "title": reader.metadata.get('/Title', '') if reader.metadata else '',
                        "author": reader.metadata.get('/Author', '') if reader.metadata else '',
                        "subject": reader.metadata.get('/Subject', '') if reader.metadata else '',
                        "doc_type": doc_type,
                        "hukuk_dali": hukuk_dali,
                        "page_count": len(reader.pages)
                    }
                    
                    # Extract articles
                    articles = self._extract_articles_from_text(text, doc_type)
                    
                    return ParsePDFOutput(
                        text=text,
                        metadata=metadata,
                        page_count=len(reader.pages),
                        extracted_articles=articles
                    )
                    
            except Exception as e:
                logger.error(f"PDF parse error: {e}")
                raise
        
        @self.tool(
            name="chunk_document",
            description="Chunk document into smaller pieces",
            input_schema=ChunkDocumentInput,
            output_schema=ChunkDocumentOutput
        )
        async def chunk_document(input_data: ChunkDocumentInput) -> ChunkDocumentOutput:
            """Chunk document based on strategy"""
            try:
                if isinstance(input_data, BaseModel):
                    params = input_data.model_dump()
                else:
                    params = input_data
                
                text = params["text"]
                strategy = params.get("strategy", "madde_based")
                chunk_size = params.get("chunk_size", 1000)
                overlap = params.get("overlap", 100)
                
                if strategy == "madde_based":
                    chunks = self._chunk_by_madde(text)
                else:
                    chunks = self._chunk_recursive(text, chunk_size, overlap)
                
                return ChunkDocumentOutput(
                    chunks=chunks,
                    total_chunks=len(chunks)
                )
                
            except Exception as e:
                logger.error(f"Chunk error: {e}")
                raise
        
        @self.tool(
            name="extract_articles",
            description="Extract articles (madde) from legal text",
            input_schema=ExtractArticlesInput,
            output_schema=ExtractArticlesOutput
        )
        async def extract_articles(input_data: ExtractArticlesInput) -> ExtractArticlesOutput:
            """Extract structured articles"""
            try:
                if isinstance(input_data, BaseModel):
                    params = input_data.model_dump()
                else:
                    params = input_data
                
                text = params["text"]
                doc_type = params["doc_type"]
                
                articles = self._extract_articles_from_text(text, doc_type)
                
                return ExtractArticlesOutput(
                    articles=articles,
                    total_articles=len(articles)
                )
                
            except Exception as e:
                logger.error(f"Extract articles error: {e}")
                raise
    
    def _extract_articles_from_text(self, text: str, doc_type: str) -> List[Dict]:
        """Extract articles with regex patterns"""
        articles = []
        
        if doc_type == "kanun":
            # Pattern: "MADDE 1-" or "Madde 1 –"
            pattern = r"(?:MADDE|Madde)\s+(\d+)\s*[–-]\s*([^(?:MADDE|Madde)]+)"
            matches = re.finditer(pattern, text, re.DOTALL)
            
            for match in matches:
                madde_no = int(match.group(1))
                content = match.group(2).strip()
                
                # Limit content length for very long articles
                if len(content) > 5000:
                    content = content[:5000] + "..."
                
                articles.append({
                    "madde_no": madde_no,
                    "content": content,
                    "fikralar": self._extract_fikralar(content)
                })
        
        return articles
    
    def _extract_fikralar(self, content: str) -> List[Dict]:
        """Extract paragraphs (fıkra) from article content"""
        # Pattern: "(1)", "(2)", etc.
        pattern = r"\((\d+)\)\s*([^(]+)"
        matches = re.finditer(pattern, content)
        
        fikralar = []
        for match in matches:
            fikra_no = int(match.group(1))
            text = match.group(2).strip()
            
            fikralar.append({
                "fikra_no": fikra_no,
                "text": text
            })
        
        return fikralar
    
    def _chunk_by_madde(self, text: str) -> List[Dict]:
        """Chunk by article (madde)"""
        articles = self._extract_articles_from_text(text, "kanun")
        chunks = []
        
        for article in articles:
            chunks.append({
                "content": article["content"],
                "metadata": {
                    "madde_no": article["madde_no"],
                    "chunk_type": "madde"
                }
            })
        
        return chunks
    
    def _chunk_recursive(self, text: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Recursive character-based chunking"""
        chunks = []
        separators = ["\n\n", "\n", ".", " ", ""]
        
        def split_text(text: str, sep_index: int = 0) -> List[str]:
            if not text or sep_index >= len(separators):
                return [text] if text else []
            
            separator = separators[sep_index]
            parts = text.split(separator)
            
            result = []
            current_chunk = ""
            
            for part in parts:
                if len(current_chunk) + len(part) + len(separator) <= chunk_size:
                    current_chunk += part + separator
                else:
                    if current_chunk:
                        result.append(current_chunk.strip())
                    
                    if len(part) > chunk_size:
                        # Part too large, try next separator
                        sub_parts = split_text(part, sep_index + 1)
                        result.extend(sub_parts)
                        current_chunk = ""
                    else:
                        current_chunk = part + separator
            
            if current_chunk:
                result.append(current_chunk.strip())
            
            return result
        
        text_chunks = split_text(text)
        
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "content": chunk,
                "metadata": {
                    "chunk_index": i,
                    "chunk_type": "recursive"
                }
            })
        
        return chunks


# Global server instance
document_processor_server = DocumentProcessorServer()
