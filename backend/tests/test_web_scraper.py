"""Test script for web scraper functionality"""

import asyncio
import sys
sys.path.insert(0, '/app')

from backend.utils.web_scraper import web_scraper
from backend.agents.web_scout import web_scout_agent


async def test_scraper_basic():
    """Test basic scraping functionality"""
    print("\n=== Testing Basic Web Scraper ===")
    
    # Test URL - a Turkish legal website
    test_url = "https://www.mevzuat.gov.tr/"
    
    result = await web_scraper.scrape_url(test_url, method="trafilatura")
    
    print(f"Success: {result.get('success')}")
    print(f"URL: {result.get('url')}")
    print(f"Title: {result.get('title', '')[:100]}")
    print(f"Text length: {len(result.get('text', ''))}")
    print(f"Method: {result.get('method')}")
    
    return result.get('success')


async def test_legal_detection():
    """Test legal content detection"""
    print("\n=== Testing Legal Content Detection ===")
    
    legal_text = """
    Türk Ticaret Kanunu Madde 11
    Ticaret şirketleri, kollektif şirket, komandit şirket, 
    anonim şirket, limited şirket ve kooperatiflerdir.
    Yargıtay kararı gereğince bu madde uygulanacaktır.
    """
    
    detection = web_scraper.detect_legal_content(legal_text)
    
    print(f"Is Legal: {detection['is_legal']}")
    print(f"Confidence: {detection['confidence']:.2f}")
    print(f"Keywords Found: {detection['keywords_found']}")
    
    return detection['is_legal']


async def test_web_scout_scraping():
    """Test Web Scout agent scraping"""
    print("\n=== Testing Web Scout Agent ===")
    
    # Test scraping a single URL
    test_url = "https://www.mevzuat.gov.tr/"
    
    result = await web_scout_agent.scrape_url(test_url)
    
    if result:
        print(f"Success: True")
        print(f"Title: {result.get('title', '')[:100]}")
        print(f"Text length: {len(result.get('text', ''))}")
        
        legal_det = result.get('legal_detection', {})
        print(f"Legal Content: {legal_det.get('is_legal')}")
        print(f"Confidence: {legal_det.get('confidence', 0):.2f}")
        return True
    else:
        print("Scraping failed")
        return False


async def main():
    """Run all tests"""
    print("Starting Web Scraper Tests...\n")
    
    tests = [
        ("Basic Scraper", test_scraper_basic),
        ("Legal Detection", test_legal_detection),
        ("Web Scout Scraping", test_web_scout_scraping),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = "✅ PASSED" if result else "❌ FAILED"
        except Exception as e:
            results[test_name] = f"❌ ERROR: {str(e)}"
    
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    for test_name, result in results.items():
        print(f"{test_name}: {result}")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
