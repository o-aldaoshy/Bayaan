import cloudscraper
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, quote, unquote
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NoorBookDownloader:
    def __init__(self, download_dir='noor_books'):
        self.base_url = 'https://www.noor-book.com'
        self.download_dir = download_dir

        # Use cloudscraper to bypass Cloudflare protection
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

        # Additional headers to make requests more realistic
        self.scraper.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

    def sanitize_filename(self, title):
        """Remove invalid filename characters and limit length"""
        # Keep Arabic characters, alphanumeric, and basic punctuation
        valid_chars = []
        for c in title:
            if c.isalnum() or c in ' ._-' or '\u0600' <= c <= '\u06FF':
                valid_chars.append(c)
        return ''.join(valid_chars).strip()[:150]

    def get_category_page(self, category_url, page=1):
        """Fetch a category page"""
        try:
            # For noor-book.com, pagination might be in the URL or use AJAX
            # Check different pagination patterns
            if page == 1:
                url = category_url
            else:
                # Try common pagination patterns
                if '?' in category_url:
                    url = f"{category_url}&page={page}"
                else:
                    url = f"{category_url}?page={page}"

            logger.info(f"Fetching category page {page}: {url}")
            response = self.scraper.get(url, timeout=30)
            response.raise_for_status()

            if response.status_code == 200:
                logger.info(f"✅ Successfully fetched page {page} ({len(response.text)} bytes)")
                return response.text
            else:
                logger.error(f"❌ Failed with status code: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error fetching category page {page}: {e}")
            return None

    def extract_book_links(self, html_content):
        """
        Extract book page links from category page
        Based on noor-book.com structure analysis
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        book_links = []

        # Find all book containers (note the typo in the class name)
        book_containers = soup.find_all('div', class_='book-restult')

        logger.info(f"Found {len(book_containers)} book containers")

        for container in book_containers:
            # Find the link with class 'img-a'
            link = container.find('a', class_='img-a')
            if link and link.get('href'):
                book_url = urljoin(self.base_url, link['href'])
                title = link.get('title', 'Unknown')

                if book_url not in book_links:
                    book_links.append((book_url, title))
                    logger.debug(f"  Found: {title}")

        logger.info(f"Extracted {len(book_links)} unique book links")
        return book_links

    def get_download_link(self, book_page_url, book_title=None):
        """
        Extract the actual PDF/file download link from a book's page
        """
        try:
            logger.info(f"Fetching book page: {book_page_url}")
            response = self.scraper.get(book_page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract book title if not provided
            if not book_title:
                title_elem = soup.find('h1') or soup.find('title')
                title = title_elem.get_text().strip() if title_elem else "Unknown"
            else:
                title = book_title

            # Look for download links
            # Common patterns on noor-book.com:
            # 1. Direct download button/link
            # 2. Link with 'download' in class or text
            # 3. Link ending in .pdf, .epub, etc.

            # Try to find download button
            download_link = soup.find('a', class_='download-btn') or \
                           soup.find('a', class_='btn-download') or \
                           soup.find('a', class_='download')

            if download_link and download_link.get('href'):
                return title, urljoin(self.base_url, download_link['href'])

            # Look for links with 'download' or 'تحميل' in text
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                link_text = link.get_text().lower()
                link_class = ' '.join(link.get('class', [])).lower()
                href = link.get('href', '')

                # Check for download indicators
                if any(keyword in link_text for keyword in ['تحميل', 'download', 'pdf', 'read']):
                    if href.endswith(('.pdf', '.epub', '.mobi')) or 'download' in href or 'pdf' in href:
                        return title, urljoin(self.base_url, href)

                # Check class names
                if 'download' in link_class or 'تحميل' in link_class:
                    return title, urljoin(self.base_url, href)

            logger.warning(f"No download link found for: {book_page_url}")

            # Save HTML for debugging
            debug_file = f"debug_book_page_{int(time.time())}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response.text[:10000])  # First 10KB
            logger.info(f"📄 Saved page sample to: {debug_file}")

            return title, None

        except Exception as e:
            logger.error(f"Error extracting download link from {book_page_url}: {e}")
            return book_title or "Unknown", None

    def download_file(self, url, filename):
        """Download a file from URL"""
        try:
            logger.info(f"Downloading: {filename}")
            response = self.scraper.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Get total file size
            total_size = int(response.headers.get('content-length', 0))

            with open(filename, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # Simple progress indicator
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                if int(percent) % 10 == 0:
                                    logger.info(f"Progress: {int(percent)}%")

            logger.info(f"✅ Successfully downloaded: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to download {filename}: {e}")
            return False

    def download_category(self, category_url, max_pages=10, max_books=None, delay=3):
        """
        Download all books from a category

        Args:
            category_url: URL of the category page
            max_pages: Maximum number of pages to scrape
            max_books: Maximum number of books to download (None = all)
            delay: Delay between requests in seconds
        """
        downloaded_count = 0

        # Create category-specific subdirectory
        category_name = category_url.split('/')[-1].split('?')[0]
        category_dir = os.path.join(self.download_dir, self.sanitize_filename(unquote(category_name)))
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)

        logger.info(f"\n{'='*80}")
        logger.info(f"Starting download from: {unquote(category_url)}")
        logger.info(f"Saving to: {category_dir}")
        logger.info(f"{'='*80}\n")

        for page in range(1, max_pages + 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing page {page}/{max_pages}")
            logger.info(f"{'='*80}")

            # Fetch category page
            html_content = self.get_category_page(category_url, page)
            if not html_content:
                logger.warning(f"Failed to fetch page {page}, stopping.")
                break

            # Extract book links
            book_links = self.extract_book_links(html_content)
            if not book_links:
                logger.warning(f"No books found on page {page}, stopping.")
                break

            # Process each book
            for i, (book_url, book_title) in enumerate(book_links, 1):
                if max_books and downloaded_count >= max_books:
                    logger.info(f"\n✅ Reached maximum book limit ({max_books})")
                    return

                logger.info(f"\n[{downloaded_count + 1}] Processing book {i}/{len(book_links)}")
                logger.info(f"Title: {book_title}")

                # Get download link
                title, download_url = self.get_download_link(book_url, book_title)

                if not download_url:
                    logger.warning(f"⚠️  Skipping - no download link found")
                    time.sleep(delay / 2)
                    continue

                # Determine file extension
                file_ext = '.pdf'
                if download_url.endswith('.epub'):
                    file_ext = '.epub'
                elif download_url.endswith('.mobi'):
                    file_ext = '.mobi'

                # Create filename
                safe_title = self.sanitize_filename(title)
                filename = os.path.join(category_dir, f"{downloaded_count + 1:04d}_{safe_title}{file_ext}")

                # Skip if already exists
                if os.path.exists(filename):
                    logger.info(f"✅ Already exists: {safe_title}")
                    downloaded_count += 1
                    continue

                # Download the book
                if self.download_file(download_url, filename):
                    downloaded_count += 1

                # Respectful delay
                time.sleep(delay)

            # Delay between pages
            logger.info(f"\nPage {page} complete. Waiting before next page...")
            time.sleep(delay * 2)

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ Download complete! Total books processed: {downloaded_count}")
        logger.info(f"{'='*80}")


def main():
    """Main function to run the downloader"""

    # Initialize downloader with cloudscraper
    downloader = NoorBookDownloader(download_dir='noor_books')

    # Category URL - Islamic ethics and morals
    category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

    # Download books from category
    downloader.download_category(
        category_url=category_url,
        max_pages=5,         # Scrape up to 5 pages
        max_books=10,        # Download up to 10 books (set to None for all)
        delay=3              # 3 second delay between requests
    )


if __name__ == '__main__':
    main()
