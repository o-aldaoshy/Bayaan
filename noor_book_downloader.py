import requests
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
        self.session = requests.Session()
        # Headers to mimic a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
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
            # Many websites use ?page=N or /page/N for pagination
            if '?' in category_url:
                url = f"{category_url}&page={page}"
            else:
                url = f"{category_url}?page={page}"

            logger.info(f"Fetching category page {page}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching category page {page}: {e}")
            return None

    def extract_book_links(self, html_content):
        """
        Extract book page links from category page

        NOTE: You need to inspect the website and update the selectors below
        Common patterns:
        - Books might be in <div class="book-item"> or <article class="book">
        - Links might be in <a class="book-link"> or <h3><a href="...">
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        book_links = []

        # CUSTOMIZE THESE SELECTORS based on the actual website structure
        # Example patterns (you'll need to update these):

        # Option 1: Find all links with specific class
        # books = soup.find_all('a', class_='book-title-link')

        # Option 2: Find all articles/divs containing books
        # book_containers = soup.find_all('div', class_='book-item')
        # for container in book_containers:
        #     link = container.find('a')
        #     if link and link.get('href'):
        #         book_links.append(urljoin(self.base_url, link['href']))

        # Option 3: Generic approach - find all links that look like book pages
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            # Adjust this pattern based on actual book URL structure
            # e.g., /book/12345 or /كتاب/... or /en/book/...
            if '/كتاب/' in href or '/book/' in href or 'book-' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in book_links:
                    book_links.append(full_url)

        logger.info(f"Found {len(book_links)} book links")
        return book_links

    def get_download_link(self, book_page_url):
        """
        Extract the actual PDF/file download link from a book's page

        NOTE: You need to inspect individual book pages to find the download button/link
        """
        try:
            logger.info(f"Fetching book page: {book_page_url}")
            response = self.session.get(book_page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract book title
            # CUSTOMIZE: Update selector based on actual page structure
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown"

            # CUSTOMIZE: Find the download link
            # Common patterns:
            # - <a class="download-btn" href="...">
            # - <a href="..." download>
            # - <button onclick="download('url')">

            # Option 1: Direct download link
            download_link = soup.find('a', class_='download-button')
            if download_link and download_link.get('href'):
                return title, urljoin(self.base_url, download_link['href'])

            # Option 2: Find any link with 'download' in class or text
            download_links = soup.find_all('a', href=True)
            for link in download_links:
                link_text = link.get_text().lower()
                link_class = ' '.join(link.get('class', [])).lower()
                href = link.get('href', '')

                if 'تحميل' in link_text or 'download' in link_text or \
                   'download' in link_class or 'تحميل' in link_class or \
                   href.endswith('.pdf') or href.endswith('.epub'):
                    return title, urljoin(self.base_url, href)

            logger.warning(f"No download link found for: {book_page_url}")
            return title, None

        except Exception as e:
            logger.error(f"Error extracting download link from {book_page_url}: {e}")
            return "Unknown", None

    def download_file(self, url, filename):
        """Download a file from URL"""
        try:
            logger.info(f"Downloading: {filename}")
            response = self.session.get(url, timeout=60, stream=True)
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

    def download_category(self, category_url, max_pages=10, max_books=None, delay=2):
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

        for page in range(1, max_pages + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing page {page}/{max_pages}")
            logger.info(f"{'='*60}")

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
            for i, book_url in enumerate(book_links, 1):
                if max_books and downloaded_count >= max_books:
                    logger.info(f"Reached maximum book limit ({max_books})")
                    return

                logger.info(f"\n[{downloaded_count + 1}] Processing book {i}/{len(book_links)}")

                # Get download link
                title, download_url = self.get_download_link(book_url)

                if not download_url:
                    logger.warning(f"Skipping - no download link: {title}")
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
            logger.info(f"Page {page} complete. Waiting before next page...")
            time.sleep(delay * 2)

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Download complete! Total books downloaded: {downloaded_count}")
        logger.info(f"{'='*60}")


def main():
    """Main function to run the downloader"""

    # Initialize downloader
    downloader = NoorBookDownloader(download_dir='noor_books')

    # Category URL - the one you provided
    category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

    # Download books from category
    downloader.download_category(
        category_url=category_url,
        max_pages=10,        # Scrape up to 10 pages
        max_books=50,        # Download up to 50 books (set to None for all)
        delay=3              # 3 second delay between requests
    )


if __name__ == '__main__':
    main()
