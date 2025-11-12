"""Web scraping utilities for legal content"""

import logging
from typing import Dict, List, Optional
import asyncio
import httpx
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper for legal documents and precedents"""
    
    def __init__(self):
        self.timeout = 30
        self.user_agent = "Mozilla/5.0 (HukukYZ Bot)"
    
    async def scrape_url(
        self,
        url: str,
        method: str = "trafilatura"
    ) -> Dict:
        """Scrape content from URL
        
        Args:
            url: URL to scrape
            method: Scraping method (trafilatura, beautifulsoup, unstructured)
        
        Returns:
            Scraped content dictionary
        """
        try:
            logger.info(f"Scraping {url} with {method}")
            
            # Fetch HTML
            html = await self._fetch_html(url)
            
            if not html:
                return {"success": False, "error": "Failed to fetch HTML"}
            
            # Extract content based on method
            if method == "trafilatura":
                content = self._extract_with_trafilatura(html, url)
            elif method == "beautifulsoup":
                content = self._extract_with_beautifulsoup(html, url)
            else:
                content = self._extract_with_trafilatura(html, url)
            
            return {
                "success": True,
                "url": url,
                "title": content.get("title", ""),
                "text": content.get("text", ""),
                "metadata": content.get("metadata", {}),
                "method": method
            }
            
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML from URL"""
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return None
    
    def _extract_with_trafilatura(self, html: str, url: str) -> Dict:
        """Extract content using Trafilatura (best for articles)"""
        try:
            # Extract main text
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            
            # Extract metadata
            metadata = trafilatura.extract_metadata(html)
            
            return {
                "text": text or "",
                "title": metadata.title if metadata else "",
                "metadata": {
                    "author": metadata.author if metadata else None,
                    "date": metadata.date if metadata else None,
                    "description": metadata.description if metadata else None,
                    "sitename": metadata.sitename if metadata else None
                }
            }
        except Exception as e:
            logger.error(f"Trafilatura error: {e}")
            # Fallback to BeautifulSoup
            return self._extract_with_beautifulsoup(html, url)
    
    def _extract_with_beautifulsoup(self, html: str, url: str) -> Dict:
        """Extract content using BeautifulSoup (backup method)"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Get title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Get main content
            # Try to find main content areas
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_='content') or
                soup.find('div', id='content') or
                soup.body
            )
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            return {
                "text": text,
                "title": title_text,
                "metadata": {
                    "domain": urlparse(url).netloc
                }
            }
        except Exception as e:
            logger.error(f"BeautifulSoup error: {e}")
            return {"text": "", "title": "", "metadata": {}}
    
    async def scrape_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[Dict]:
        """Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
        
        Returns:
            List of scraped content dictionaries
        """
        results = []
        
        # Process in batches
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            tasks = [self.scrape_url(url) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        return results
    
    def detect_legal_content(self, text: str) -> Dict:
        """Detect if content is legal-related
        
        Args:
            text: Text to analyze
        
        Returns:
            Detection results
        """
        legal_keywords = [
            "yargıtay", "danıştay", "anayasa mahkemesi",
            "karar", "içtihat", "dava", "hüküm",
            "madde", "kanun", "yasa", "mevzuat",
            "ttk", "tbk", "tmk", "iik",
            "esas", "karar no"
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in legal_keywords if kw in text_lower]
        
        is_legal = len(found_keywords) >= 2
        confidence = min(len(found_keywords) / 5, 1.0)
        
        return {
            "is_legal": is_legal,
            "confidence": confidence,
            "keywords_found": found_keywords
        }


# Global scraper instance
web_scraper = WebScraper()
