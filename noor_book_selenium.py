"""
Noor-book.com Downloader using Selenium (For Windows/Mac with Chrome installed)

This version uses Selenium with undetected-chromedriver to bypass Cloudflare protection.
Install requirements:
    pip install selenium undetected-chromedriver beautifulsoup4

Make sure you have Chrome browser installed on your system.
"""

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("ERROR: Please install required packages:")
    print("pip install selenium undetected-chromedriver beautifulsoup4")
    exit(1)

from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, unquote
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NoorBookSeleniumDownloader:
    def __init__(self, download_dir='noor_books', headless=False):
        """
        Initialize the Selenium-based downloader

        Args:
            download_dir: Directory to save downloaded books
            headless: Run browser in headless mode (not recommended for Cloudflare bypass)
        """
        self.base_url = 'https://www.noor-book.com'
        self.download_dir = download_dir

        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        # Setup Chrome options
        options = uc.ChromeOptions()
        if headless:
            options.add_argument('--headless')

        # Disable images to speed up loading
        prefs = {
            "download.default_directory": os.path.abspath(download_dir),
            "download.prompt_for_download": False,
            "profile.default_content_setting_values.images": 2  # Disable images
        }
        options.add_experimental_option("prefs", prefs)

        logger.info("Initializing Chrome browser...")
        try:
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(30)
            logger.info("✅ Browser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            logger.error("Make sure Chrome is installed on your system")
            raise

    def sanitize_filename(self, title):
        """Remove invalid filename characters and limit length"""
        valid_chars = []
        for c in title:
            if c.isalnum() or c in ' ._-' or '\u0600' <= c <= '\u06FF':
                valid_chars.append(c)
        return ''.join(valid_chars).strip()[:150]

    def get_category_page(self, category_url, page=1):
        """Fetch a category page"""
        try:
            if '?' in category_url:
                url = f"{category_url}&page={page}"
            else:
                url = f"{category_url}?page={page}"

            logger.info(f"Fetching category page {page}: {url}")
            self.driver.get(url)

            # Wait for page to load
            time.sleep(3)

            # Wait for content to load (adjust selector as needed)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except:
                pass

            return self.driver.page_source
        except Exception as e:
            logger.error(f"Error fetching category page {page}: {e}")
            return None

    def extract_book_links(self, html_content):
        """Extract book page links from category page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        book_links = []

        # Find all links that look like book pages
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            # Adjust pattern based on actual site structure
            if '/كتاب/' in href or '/book/' in href or 'book-' in href:
                full_url = urljoin(self.base_url, href)
                if full_url not in book_links:
                    book_links.append(full_url)

        logger.info(f"Found {len(book_links)} book links")
        return book_links

    def get_download_link(self, book_page_url):
        """Extract download link from a book's page"""
        try:
            logger.info(f"Fetching book page: {book_page_url}")
            self.driver.get(book_page_url)
            time.sleep(2)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Extract title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown"

            # Find download link
            download_links = soup.find_all('a', href=True)
            for link in download_links:
                link_text = link.get_text().lower()
                href = link.get('href', '')

                if 'تحميل' in link_text or 'download' in link_text or \
                   href.endswith('.pdf') or href.endswith('.epub'):
                    return title, urljoin(self.base_url, href)

            logger.warning(f"No download link found for: {book_page_url}")
            return title, None
        except Exception as e:
            logger.error(f"Error extracting download link: {e}")
            return "Unknown", None

    def download_category(self, category_url, max_pages=10, max_books=None, delay=2):
        """Download all books from a category"""
        downloaded_count = 0

        category_name = category_url.split('/')[-1].split('?')[0]
        category_dir = os.path.join(self.download_dir, self.sanitize_filename(unquote(category_name)))
        if not os.path.exists(category_dir):
            os.makedirs(category_dir)

        try:
            for page in range(1, max_pages + 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing page {page}/{max_pages}")
                logger.info(f"{'='*60}")

                html_content = self.get_category_page(category_url, page)
                if not html_content:
                    logger.warning(f"Failed to fetch page {page}, stopping.")
                    break

                book_links = self.extract_book_links(html_content)
                if not book_links:
                    logger.warning(f"No books found on page {page}, stopping.")
                    break

                for i, book_url in enumerate(book_links, 1):
                    if max_books and downloaded_count >= max_books:
                        logger.info(f"Reached maximum book limit ({max_books})")
                        return

                    logger.info(f"\n[{downloaded_count + 1}] Processing book {i}/{len(book_links)}")

                    title, download_url = self.get_download_link(book_url)

                    if download_url:
                        logger.info(f"✅ Found book: {title}")
                        logger.info(f"   Download URL: {download_url}")
                        # Note: You may need to handle the actual download separately
                        # depending on how the site serves files
                        downloaded_count += 1

                    time.sleep(delay)

                time.sleep(delay * 2)

        finally:
            self.close()

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Complete! Processed {downloaded_count} books")
        logger.info(f"{'='*60}")

    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            logger.info("Closing browser...")
            self.driver.quit()


def main():
    """Main function"""
    downloader = NoorBookSeleniumDownloader(download_dir='noor_books')

    category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

    downloader.download_category(
        category_url=category_url,
        max_pages=10,
        max_books=50,
        delay=3
    )


if __name__ == '__main__':
    main()
