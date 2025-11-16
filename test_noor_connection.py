#!/usr/bin/env python3
"""Quick test script to verify noor-book.com connection works"""

import sys
sys.path.insert(0, '/home/user/Bayaan')

from noor_book_downloader import NoorBookDownloader
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Test if we can fetch a category page"""
    logger.info("Testing connection to noor-book.com...")

    # Initialize downloader
    downloader = NoorBookDownloader(download_dir='test_downloads')

    # Test category URL
    category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

    # Try to fetch just the first page
    html = downloader.get_category_page(category_url, page=1)

    if html:
        logger.info(f"✅ SUCCESS! Fetched {len(html)} bytes of HTML")
        logger.info(f"First 200 characters: {html[:200]}")

        # Try to extract book links
        book_links = downloader.extract_book_links(html)
        logger.info(f"✅ Found {len(book_links)} book links")

        if book_links:
            logger.info(f"Sample book link: {book_links[0]}")

        return True
    else:
        logger.error("❌ FAILED to fetch category page")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
