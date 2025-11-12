"""Web Scout Agent - Live web search for legal precedents"""

from typing import List, Dict, Optional
import logging

from backend.mcp.client.mcp_client import mcp_client
from backend.utils.web_scraper import web_scraper

logger = logging.getLogger(__name__)


class WebScoutAgent:
    """Web Scout Agent for searching legal precedents online"""
    
    def __init__(self):
        self.mcp = mcp_client
        self.scraper = web_scraper
    
    async def search_precedents(
        self,
        keywords: List[str],
        court_type: str = "yargitay",
        limit: int = 10,
        scrape_results: bool = False
    ) -> List[Dict]:
        """Search for legal precedents
        
        Args:
            keywords: Search keywords
            court_type: Court type (yargitay, danistay, aym)
            limit: Number of results
            scrape_results: Whether to scrape content from result URLs
        
        Returns:
            List of precedent documents
        """
        try:
            logger.info(f"Searching {court_type} precedents: {keywords}")
            
            result = await self.mcp.call_tool(
                server_name="web_search",
                tool_name="search_precedents",
                params={
                    "keywords": keywords,
                    "court_type": court_type,
                    "limit": limit
                }
            )
            
            precedents = result.get("precedents", [])
            logger.info(f"Found {len(precedents)} precedents")
            
            # Scrape content if requested
            if scrape_results and precedents:
                precedents = await self._enrich_with_content(precedents)
            
            return precedents
            
        except Exception as e:
            logger.error(f"Precedent search error: {e}")
            return []
    
    async def search_web(
        self,
        query: str,
        domain: str = ".gov.tr",
        limit: int = 10,
        scrape_results: bool = True
    ) -> List[Dict]:
        """General web search for legal information
        
        Args:
            query: Search query
            domain: Domain filter
            limit: Number of results
            scrape_results: Whether to scrape content from result URLs
        
        Returns:
            List of web results with scraped content
        """
        try:
            logger.info(f"Web search: {query[:100]}...")
            
            result = await self.mcp.call_tool(
                server_name="web_search",
                tool_name="search_legal_web",
                params={
                    "query": query,
                    "domain": domain,
                    "limit": limit
                }
            )
            
            results = result.get("results", [])
            logger.info(f"Found {len(results)} web results")
            
            # Scrape content if requested
            if scrape_results and results:
                results = await self._enrich_with_content(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    async def scrape_url(
        self,
        url: str,
        method: str = "trafilatura"
    ) -> Optional[Dict]:
        """Scrape content from a single URL
        
        Args:
            url: URL to scrape
            method: Scraping method (trafilatura, beautifulsoup)
        
        Returns:
            Scraped content or None if failed
        """
        try:
            result = await self.scraper.scrape_url(url, method)
            
            if result.get("success"):
                # Check if content is legal-related
                text = result.get("text", "")
                detection = self.scraper.detect_legal_content(text)
                result["legal_detection"] = detection
                
                logger.info(
                    f"Scraped {url} - Legal: {detection['is_legal']} "
                    f"(confidence: {detection['confidence']:.2f})"
                )
                return result
            else:
                logger.warning(f"Failed to scrape {url}: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    async def scrape_multiple_urls(
        self,
        urls: List[str],
        max_concurrent: int = 3,
        filter_legal: bool = True
    ) -> List[Dict]:
        """Scrape content from multiple URLs
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
            filter_legal: Only return legal-related content
        
        Returns:
            List of scraped content dictionaries
        """
        try:
            results = await self.scraper.scrape_multiple(urls, max_concurrent)
            
            # Filter successful scrapes
            successful = [r for r in results if r.get("success")]
            
            # Add legal detection to each result
            for result in successful:
                text = result.get("text", "")
                detection = self.scraper.detect_legal_content(text)
                result["legal_detection"] = detection
            
            # Filter by legal content if requested
            if filter_legal:
                successful = [
                    r for r in successful 
                    if r.get("legal_detection", {}).get("is_legal", False)
                ]
            
            logger.info(
                f"Scraped {len(successful)}/{len(urls)} URLs "
                f"(legal filter: {filter_legal})"
            )
            
            return successful
            
        except Exception as e:
            logger.error(f"Error scraping multiple URLs: {e}")
            return []
    
    async def _enrich_with_content(self, search_results: List[Dict]) -> List[Dict]:
        """Enrich search results with scraped content
        
        Args:
            search_results: Search results with URLs
        
        Returns:
            Enriched results with full text content
        """
        try:
            # Extract URLs from search results
            urls = []
            for result in search_results:
                url = result.get("url") or result.get("link")
                if url:
                    urls.append(url)
            
            if not urls:
                logger.warning("No URLs found in search results")
                return search_results
            
            # Scrape content from URLs
            scraped_contents = await self.scraper.scrape_multiple(
                urls, max_concurrent=3
            )
            
            # Create URL to content mapping
            url_to_content = {
                sc.get("url"): sc for sc in scraped_contents 
                if sc.get("success")
            }
            
            # Enrich original results
            enriched = []
            for result in search_results:
                url = result.get("url") or result.get("link")
                
                if url and url in url_to_content:
                    content = url_to_content[url]
                    
                    # Add scraped content to result
                    result["scraped_content"] = content.get("text", "")
                    result["scraped_metadata"] = content.get("metadata", {})
                    
                    # Add legal detection
                    detection = self.scraper.detect_legal_content(
                        content.get("text", "")
                    )
                    result["is_legal_content"] = detection.get("is_legal", False)
                    result["legal_confidence"] = detection.get("confidence", 0.0)
                    result["legal_keywords"] = detection.get("keywords_found", [])
                    
                    enriched.append(result)
                else:
                    # Keep original result even if scraping failed
                    result["scraped_content"] = None
                    result["is_legal_content"] = False
                    enriched.append(result)
            
            logger.info(
                f"Enriched {len([r for r in enriched if r.get('scraped_content')])}"
                f"/{len(search_results)} results with content"
            )
            
            return enriched
            
        except Exception as e:
            logger.error(f"Error enriching results: {e}")
            return search_results


# Global instance
web_scout_agent = WebScoutAgent()
