import time
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import os
import csv
import requests


# =====================================================
# UTILITIES
# =====================================================

def random_delay(min_sec=1, max_sec=3):
    """Random delay to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))


def human_like_mouse_move(driver, element):
    """Move mouse in a human-like way"""
    try:
        action = ActionChains(driver)
        action.move_to_element(element).perform()
        random_delay(0.2, 0.5)
    except:
        pass


def sanitize_filename(title):
    """Clean filename and include Arabic characters"""
    valid_chars = []
    for c in title:
        if c.isalnum() or c in ' ._-' or '\u0600' <= c <= '\u06FF':
            valid_chars.append(c)
    return ''.join(valid_chars).strip()[:100]


def validate_file(file_path, min_size=1024):
    """Validate that downloaded file is valid"""
    if not os.path.exists(file_path):
        return False

    file_size = os.path.getsize(file_path)
    if file_size < min_size:
        print(f"⚠ File too small ({file_size} bytes), likely invalid")
        return False

    if file_path.endswith('.pdf'):
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    print("⚠ File does not have PDF header")
                    return False
        except:
            return False

    return True


def create_book_folder(base_dir, number):
    """Create a numbered folder for a book"""
    folder_path = os.path.join(base_dir, str(number))
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def extract_image_url(soup):
    """Extract cover image URL from page"""
    try:
        # Find img with itemprop="image" or class="media-object"
        img_tag = soup.find("img", itemprop="image")
        if not img_tag:
            img_tag = soup.find("img", class_="media-object")

        if img_tag and img_tag.get("src"):
            img_url = img_tag["src"]
            # Make absolute URL if relative
            if img_url.startswith("/"):
                img_url = "https://www.noor-book.com" + img_url
            return img_url
    except Exception as e:
        print(f"⚠ Error extracting image URL: {e}")
    return None


def download_image(url, filepath, cookies=None):
    """Download image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.noor-book.com/'
        }

        session = requests.Session()
        if cookies:
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])

        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"⚠ Error downloading image: {e}")
        return False


def get_image_extension(url):
    """Get image extension from URL"""
    url_lower = url.lower()
    if '.png' in url_lower:
        return '.png'
    elif '.gif' in url_lower:
        return '.gif'
    elif '.webp' in url_lower:
        return '.webp'
    else:
        return '.jpg'  # Default to jpg


def check_book_restrictions(soup):
    """
    Check if book has copyright restrictions that should cause it to be skipped.
    Returns tuple: (should_skip, reason)
    """
    # Find restriction divs with the specific styling
    restriction_divs = soup.find_all("div", class_="the-box text-center")

    for div in restriction_divs:
        div_text = div.get_text()

        # Check for "الناشر بالمكتبة هو المؤلف" (Publisher is the author - personal use only)
        if "الناشر بالمكتبة هو المؤلف" in div_text:
            return True, "الناشر بالمكتبة هو المؤلف (personal use only)"

        # Check for "حقوق النشر محفوظة" (Copyright reserved - cannot download)
        if "حقوق النشر محفوظة" in div_text:
            return True, "حقوق النشر محفوظة (copyright reserved)"

    return False, ""


# =====================================================
# SELENIUM-ONLY SCRAPER CLASS
# =====================================================

class NoorBookSeleniumScraper:
    def __init__(self, headless=False, download_dir="noor_books"):
        """Initialize Selenium driver that stays alive for entire session"""
        print("🌐 Launching Chrome browser (VISIBLE MODE - You can see CAPTCHA)...")

        options = uc.ChromeOptions()

        if not headless:  # Show browser so user can see CAPTCHA
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--headless=new")

        options.add_argument("--disable-blink-features=AutomationControlled")

        # Random window size
        window_width = random.randint(1200, 1920)
        window_height = random.randint(800, 1080)
        options.add_argument(f"--window-size={window_width},{window_height}")

        # Set download directory
        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)

        # Configure Chrome to download files automatically
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,  # Don't open PDFs in browser
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = uc.Chrome(options=options, use_subprocess=True)
        self.driver.set_page_load_timeout(60)
        self.wait = WebDriverWait(self.driver, 30)

        # Enable downloads (especially important for headless mode)
        try:
            self.driver.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": self.download_dir
            })
        except Exception as e:
            print(f"⚠ Could not set download behavior: {e}")


    def login(self, email, password):
        """Login to noor-book.com"""
        print("🔐 Logging in...")

        try:
            login_url = "https://www.noor-book.com/login"
            self.driver.get(login_url)

            print("⏳ Waiting for page to load...")
            random_delay(3, 5)

            # Scroll to reveal form
            scroll_amount = random.randint(500, 700)
            self.driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
            random_delay(1.5, 2.5)

            # Try to click email tab
            print("📌 Activating email login...")
            try:
                self.driver.execute_script("""
                    if (document.querySelector('.show_email')) {
                        document.querySelector('.show_email').click();
                    }
                """)
                random_delay(1, 2)
            except:
                pass

            # Find email field
            print("🔍 Finding email field...")
            email_input = None
            for attempt in range(3):
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[name='email']")
                for field in inputs:
                    try:
                        if field.is_displayed() and field.size["height"] > 0:
                            email_input = field
                            break
                    except:
                        continue

                if email_input:
                    break

                if attempt < 2:
                    scroll_amount = random.randint(800, 1000)
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
                    random_delay(1, 2)

            if not email_input:
                raise Exception("❌ Email field not found")

            # Enter email
            print("📝 Entering email...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", email_input)
            random_delay(0.5, 1)
            human_like_mouse_move(self.driver, email_input)
            email_input.click()
            random_delay(0.3, 0.6)
            email_input.clear()

            for char in email:
                email_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            random_delay(0.5, 1)

            # Find password field
            print("🔍 Finding password field...")
            password_input = None
            pw_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[name='password']")
            for pf in pw_fields:
                try:
                    if pf.is_displayed():
                        password_input = pf
                        break
                except:
                    continue

            if not password_input:
                raise Exception("❌ Password field not found")

            # Enter password
            print("🔑 Entering password...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", password_input)
            random_delay(0.5, 1)
            human_like_mouse_move(self.driver, password_input)
            password_input.click()
            random_delay(0.3, 0.6)
            password_input.clear()

            for char in password:
                password_input.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))

            random_delay(0.5, 1)

            # Set login type
            self.driver.execute_script("""
                if (document.querySelector("input[name='type']")) {
                    document.querySelector("input[name='type']").value = "email";
                }
            """)

            # Click login button
            print("🔒 Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, ".submit-login")
            human_like_mouse_move(self.driver, login_button)
            random_delay(0.3, 0.7)
            self.driver.execute_script("arguments[0].click();", login_button)

            print("⏳ Waiting for authentication...")
            random_delay(5, 8)

            # Check for CAPTCHA
            page_text = self.driver.page_source.lower()
            if 'captcha' in page_text or 'robot' in page_text:
                print("\n" + "="*60)
                print("⚠️  CAPTCHA DETECTED!")
                print("🖐️  The browser window should be visible now.")
                print("👀 Look at the Chrome window and solve the CAPTCHA")
                print("="*60 + "\n")
                input("Press ENTER after you've solved the CAPTCHA...")
                random_delay(2, 3)

            # Check if login successful
            if "/login" in self.driver.current_url:
                self.driver.save_screenshot("login_failed.png")
                raise Exception("❌ Login failed. Still on login page. Check login_failed.png")

            print("✅ Login successful!")
            return True

        except Exception as e:
            print(f"❌ Login error: {e}")
            raise


    def get_page_source(self, url):
        """Navigate to URL and return page source"""
        try:
            self.driver.get(url)
            random_delay(2, 4)
            return self.driver.page_source
        except Exception as e:
            print(f"❌ Error loading {url}: {e}")
            return None


    def resolve_category_url(self, fake_url):
        """Resolve Arabic category URL to real hashed URL"""
        print(f"🔎 Resolving category URL...")

        try:
            html = self.get_page_source(fake_url)
            if not html:
                return fake_url

            soup = BeautifulSoup(html, "html.parser")

            # Find book cards
            cards = soup.find_all("div", class_="book-restult")
            if not cards:
                cards = soup.find_all("div", class_="book-result")
            if not cards:
                cards = soup.find_all("div", class_="book-card")

            if not cards:
                print("⚠ No book cards found, using original URL")
                return fake_url

            print(f"✅ Found {len(cards)} books")

            # Try first 5 books
            for i, card in enumerate(cards[:5]):
                book_link = card.find("a", href=True)
                if not book_link:
                    continue

                book_url = "https://www.noor-book.com" + book_link["href"]
                print(f"📘 Checking book {i+1}...")

                random_delay(1, 2)
                book_html = self.get_page_source(book_url)
                if not book_html:
                    continue

                bs = BeautifulSoup(book_html, "html.parser")
                tag_link = bs.find("a", href=lambda x: x and x.startswith("/tag/"))

                if tag_link:
                    real_url = "https://www.noor-book.com" + tag_link["href"]
                    print(f"✅ Real category URL: {real_url}")
                    return real_url

            print("⚠ Could not resolve, using original URL")
            return fake_url

        except Exception as e:
            print(f"❌ Error resolving URL: {e}")
            return fake_url


    def get_download_link(self, book_url):
        """Get download link from book page and extract title"""
        print(f"📖 Getting download link from: {book_url}")

        try:
            self.driver.get(book_url)
            random_delay(4, 6)

            # Extract title from book page FIRST
            title = "Unknown Title"
            try:
                # Try to find title in span#trans_title_here
                title_element = self.driver.find_element(By.CSS_SELECTOR, "span#trans_title_here")
                title = title_element.text.strip()
                if title:
                    print(f"📚 Title from page: {title}")
            except:
                # Fallback to h2.under_img_title
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, "h2.under_img_title")
                    title = title_element.text.strip()
                    if title:
                        print(f"📚 Title from page (fallback): {title}")
                except:
                    print("⚠ Could not extract title from page")

            # Scroll to download area
            scroll_amount = random.randint(700, 900)
            self.driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
            random_delay(1.5, 2.5)

            # Try multiple selectors for download button
            download_button = None
            selectors = [
                "#download_circle a.download-btn",
                "a.download-btn",
                ".download-button",
                "a[href*='download']"
            ]

            for selector in selectors:
                try:
                    download_button = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Found button: {selector}")
                    break
                except TimeoutException:
                    continue

            if not download_button:
                print("❌ Download button not found")
                return None, "", ".pdf", title

            # Click download button
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", download_button)
            random_delay(1, 2)
            human_like_mouse_move(self.driver, download_button)
            random_delay(0.5, 1)
            self.driver.execute_script("arguments[0].click();", download_button)

            print("⏳ Waiting for download link to appear...")
            random_delay(8, 12)

            # Try multiple selectors for download link
            download_link = None
            link_selectors = [
                "a.internal_download_link",
                ".download-modal a[href*='download']",
                "#download-modal a[href*='.pdf']",
                "a[href*='download'][href*='.pdf']",
                ".modal a[href$='.pdf']"
            ]

            for selector in link_selectors:
                try:
                    download_link = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Found link: {selector}")
                    break
                except TimeoutException:
                    continue

            if not download_link:
                print("❌ Download link not found")
                return None, "", ".pdf", title

            download_url = download_link.get_attribute("href")

            # Extract size
            size_text = ""
            try:
                link_text = download_link.text
                if "(" in link_text:
                    size_text = link_text.split("(")[-1].replace(")", "").strip()
            except:
                pass

            # Determine extension
            file_ext = ".pdf"
            url_lower = download_url.lower()
            if ".epub" in url_lower:
                file_ext = ".epub"
            elif ".mobi" in url_lower:
                file_ext = ".mobi"
            elif ".djvu" in url_lower:
                file_ext = ".djvu"

            return download_url, size_text, file_ext, title

        except Exception as e:
            print(f"❌ Error getting download link: {e}")
            self.driver.save_screenshot("download_error.png")
            return None, "", ".pdf", "Unknown Title"


    def download_file(self, url, target_filepath):
        """Download file using Selenium browser (avoids 403 errors)"""
        try:
            print(f"🔗 Initiating download via browser...")

            # Get list of files before download
            files_before = set(os.listdir(self.download_dir))

            # Navigate to download URL - browser will download automatically
            self.driver.get(url)

            print("⏳ Waiting for download to complete...")

            # Wait for new file to appear (max 120 seconds)
            max_wait = 120
            waited = 0
            new_file = None

            while waited < max_wait:
                time.sleep(1)
                waited += 1

                files_after = set(os.listdir(self.download_dir))
                new_files = files_after - files_before

                # Filter out .crdownload and .tmp files (incomplete downloads)
                complete_files = [f for f in new_files if not f.endswith('.crdownload') and not f.endswith('.tmp')]

                if complete_files:
                    new_file = complete_files[0]
                    break

                # Progress indicator every 10 seconds
                if waited % 10 == 0:
                    print(f"⏳ Still waiting... ({waited}s)")

            if not new_file:
                print("❌ Download timeout - file did not appear")
                return False

            # Path to downloaded file
            downloaded_path = os.path.join(self.download_dir, new_file)

            # Wait a bit more to ensure file is completely written
            time.sleep(2)

            # Rename to target filename
            if downloaded_path != target_filepath:
                # If target already exists, remove it
                if os.path.exists(target_filepath):
                    os.remove(target_filepath)
                os.rename(downloaded_path, target_filepath)
                print(f"✅ Downloaded and renamed to: {os.path.basename(target_filepath)}")
            else:
                print(f"✅ Downloaded: {os.path.basename(target_filepath)}")

            return True

        except Exception as e:
            print(f"❌ Download error: {e}")
            return False


    def extract_metadata(self, book_url):
        """Extract book title, author, description, category, and image URL"""
        try:
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            # Title
            title = "Unknown Title"
            title_tag = soup.find("span", id="trans_title_here")
            if title_tag:
                title = title_tag.text.strip()
            else:
                title_tag = soup.find("h1", class_="book-title")
                if title_tag:
                    title = title_tag.text.strip()

            # Author
            author = "Unknown Author"
            author_tag = soup.find("span", id="book-writer")
            if author_tag:
                author = author_tag.text.strip()
            else:
                author_tag = soup.find("span", itemprop="name")
                if author_tag:
                    author = author_tag.text.strip()

            # Description
            description = ""
            desc_tag = soup.find("p", itemprop="description")
            if desc_tag:
                # Get text from span.more inside or full text
                more_span = desc_tag.find("span", class_="more")
                if more_span:
                    description = more_span.text.strip()
                else:
                    description = desc_tag.text.strip()

            # Category
            category = ""
            cat_tag = soup.find("span", id="book-category")
            if cat_tag:
                category = cat_tag.text.strip()

            # Image URL
            image_url = extract_image_url(soup)

            return {
                'title': title,
                'author': author,
                'description': description,
                'category': category,
                'image_url': image_url
            }
        except Exception as e:
            print(f"⚠ Error extracting metadata: {e}")
            return {
                'title': "Unknown Title",
                'author': "Unknown Author",
                'description': "",
                'category': "",
                'image_url': None
            }


    def close(self):
        """Close browser"""
        try:
            self.driver.quit()
        except:
            pass


# =====================================================
# MAIN DOWNLOAD FUNCTION
# =====================================================

def download_books_from_category(scraper, category_url, max_scrolls=100, batch_size=10,
                                 download_dir="noor_books", metadata_file="metadata.csv"):
    """
    Download books from a category with infinite scroll

    Args:
        max_scrolls: Maximum number of times to scroll down (default 100)
    """
    os.makedirs(download_dir, exist_ok=True)

    csv_exists = os.path.exists(metadata_file)
    downloaded_count = 0
    failed_count = 0

    print(f"\n{'='*60}")
    print(f"📄 Loading category with infinite scroll")
    print(f"🔗 URL: {category_url}")
    print(f"{'='*60}")

    # Navigate to category page
    scraper.driver.get(category_url)
    random_delay(3, 5)

    # ===== PHASE 1: Scroll and collect ALL book URLs =====
    print("\n📜 PHASE 1: Scrolling to load all books...")

    all_book_urls = set()
    scroll_attempts = 0
    last_count = 0

    while scroll_attempts < max_scrolls:
        scroll_attempts += 1

        # Get current page HTML
        html = scraper.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # Find all books currently visible
        cards = soup.find_all("div", class_="book-restult")
        if not cards:
            cards = soup.find_all("div", class_="book-result")
        if not cards:
            cards = soup.find_all("div", class_="book-card")

        # Extract book URLs
        for card in cards:
            book_link = card.find("a", href=True)
            if book_link:
                book_url = "https://www.noor-book.com" + book_link["href"]
                all_book_urls.add(book_url)

        current_count = len(all_book_urls)
        new_found = current_count - last_count

        print(f"📜 Scroll {scroll_attempts}/{max_scrolls} - Total books: {current_count} (+{new_found} new)")

        # Check for "no more results" element
        no_more_results = soup.find("div", class_="no_more_result_scroll")
        if no_more_results:
            print("✅ Reached end of results - 'لا يوجد المزيد من النتائج'")
            break

        last_count = current_count

        # Try multiple scroll methods to trigger infinite scroll

        # Method 1: Try clicking "load more" button if it exists
        try:
            load_more_selectors = [
                ".load-more",
                ".loadmore",
                "#load-more",
                "button.more",
                "a.more",
                ".btn-load-more",
                "[data-load-more]"
            ]
            for selector in load_more_selectors:
                try:
                    load_more_btn = scraper.driver.find_element(By.CSS_SELECTOR, selector)
                    if load_more_btn.is_displayed():
                        scraper.driver.execute_script("arguments[0].click();", load_more_btn)
                        print(f"🖱️ Clicked load more button: {selector}")
                        random_delay(3, 5)
                        break
                except:
                    continue
        except:
            pass

        # Method 2: Scroll to the last book card (more reliable than page bottom)
        try:
            last_card = scraper.driver.find_elements(By.CSS_SELECTOR, "div.book-restult, div.book-result, div.book-card")
            if last_card:
                scraper.driver.execute_script("arguments[0].scrollIntoView(true);", last_card[-1])
                random_delay(1, 2)
        except:
            pass

        # Method 3: Scroll to page bottom
        scraper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Method 4: Scroll down by increments (sometimes works better)
        current_scroll = scraper.driver.execute_script("return window.pageYOffset;")
        scraper.driver.execute_script(f"window.scrollTo(0, {current_scroll + 1000});")

        # Wait longer for content to load
        random_delay(3, 5)

    print(f"\n✅ Found {len(all_book_urls)} total books to download")

    # ===== PHASE 2: Download each book =====
    print("\n📥 PHASE 2: Downloading books...")

    book_list = list(all_book_urls)
    total_books = len(book_list)

    # Initialize CSV with headers
    if not csv_exists:
        with open(metadata_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["book_number", "title", "author", "description", "category", "status"])

    # Get cookies for image downloads
    cookies = scraper.driver.get_cookies()

    skipped_count = 0

    for idx, book_page in enumerate(book_list, 1):
        book_number = idx
        print(f"\n[{book_number}/{total_books}] 🔎 {book_page}")

        try:
            random_delay(2, 4)

            # Navigate to book page first to check for restrictions
            scraper.driver.get(book_page)
            random_delay(2, 3)

            # Check for copyright restrictions
            html = scraper.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            should_skip, skip_reason = check_book_restrictions(soup)

            if should_skip:
                print(f"⏭️  Skipping book: {skip_reason}")
                # Extract metadata for restricted book
                metadata = scraper.extract_metadata(book_page)
                # Save to CSV with restricted status
                with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        book_number,
                        metadata['title'],
                        metadata['author'],
                        metadata['description'],
                        metadata['category'],
                        "restricted"
                    ])
                skipped_count += 1
                continue

            # Get download link and title
            download_url, size_text, file_ext, title = scraper.get_download_link(book_page)

            if not download_url:
                print("❌ No download link")
                # Extract metadata for failed book
                metadata = scraper.extract_metadata(book_page)
                # Save to CSV with failed status
                with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        book_number,
                        metadata['title'],
                        metadata['author'],
                        metadata['description'],
                        metadata['category'],
                        "failed"
                    ])
                failed_count += 1
                continue

            # Get all metadata from book page
            scraper.driver.get(book_page)
            random_delay(1, 2)
            metadata = scraper.extract_metadata(book_page)

            # Use title from get_download_link (more reliable) if available
            if title and title != "Unknown Title":
                metadata['title'] = title

            print(f"📚 Title: {metadata['title']}")
            print(f"✍️  Author: {metadata['author']}")
            print(f"📁 Category: {metadata['category']}")

            # Create numbered folder for this book
            book_folder = create_book_folder(download_dir, book_number)

            # Sanitize filename
            safe_filename = sanitize_filename(metadata['title'])
            if not safe_filename:
                safe_filename = f"book_{book_number}"

            # Download PDF
            pdf_path = os.path.join(book_folder, f"{safe_filename}{file_ext}")

            # Skip if PDF already exists and valid
            if os.path.exists(pdf_path) and validate_file(pdf_path):
                print(f"✅ PDF already exists: {pdf_path}")
            else:
                print(f"⬇️  Downloading PDF ({size_text})...")

                if not scraper.download_file(download_url, pdf_path):
                    # Save to CSV with failed status
                    with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            book_number,
                            metadata['title'],
                            metadata['author'],
                            metadata['description'],
                            metadata['category'],
                            "failed"
                        ])
                    failed_count += 1
                    continue

                # Validate PDF
                if not validate_file(pdf_path):
                    print("❌ PDF validation failed")
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    # Save to CSV with failed status
                    with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            book_number,
                            metadata['title'],
                            metadata['author'],
                            metadata['description'],
                            metadata['category'],
                            "failed"
                        ])
                    failed_count += 1
                    continue

                print(f"✅ PDF saved: {os.path.basename(pdf_path)}")

            # Download cover image
            if metadata['image_url']:
                img_ext = get_image_extension(metadata['image_url'])
                img_path = os.path.join(book_folder, f"{safe_filename}{img_ext}")

                if os.path.exists(img_path):
                    print(f"✅ Image already exists: {os.path.basename(img_path)}")
                else:
                    print(f"🖼️  Downloading cover image...")
                    if download_image(metadata['image_url'], img_path, cookies):
                        print(f"✅ Image saved: {os.path.basename(img_path)}")
                    else:
                        print("⚠ Could not download cover image")
            else:
                print("⚠ No cover image URL found")

            # Save metadata to CSV
            with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    book_number,
                    metadata['title'],
                    metadata['author'],
                    metadata['description'],
                    metadata['category'],
                    "downloaded"
                ])

            downloaded_count += 1
            print(f"✅ Book {book_number} complete: {book_folder}")

            if downloaded_count % batch_size == 0:
                print(f"⏸  Batch pause...")
                random_delay(10, 15)

        except Exception as e:
            print(f"❌ Error: {e}")
            failed_count += 1

    print(f"\n{'='*60}")
    print(f"🎉 Complete!")
    print(f"✅ Downloaded: {downloaded_count}")
    print(f"⏭️  Skipped (restricted): {skipped_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Metadata saved to: {metadata_file}")
    print(f"{'='*60}")


def extract_categories_from_page(scraper, categories_page_url):
    """
    Extract all category URLs from a categories listing page

    Args:
        categories_page_url: URL to the page with category listings

    Returns:
        List of tuples: [(category_name, category_url), ...]
    """
    print(f"\n{'='*60}")
    print(f"📑 Extracting categories from page")
    print(f"🔗 URL: {categories_page_url}")
    print(f"{'='*60}")

    try:
        scraper.driver.get(categories_page_url)
        random_delay(3, 5)

        html = scraper.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        categories = []

        # Find all category links in the format /tag/...
        category_links = soup.find_all("a", href=lambda x: x and x.startswith("/tag/"))

        for link in category_links:
            href = link.get("href")
            # Get category name from the h3 tag inside the link
            h3_tag = link.find("h3")
            if h3_tag:
                category_name = h3_tag.text.strip()
            else:
                # Fallback: extract name from URL
                category_name = href.replace("/tag/", "").replace("-", " ")

            category_url = "https://www.noor-book.com" + href

            # Avoid duplicates
            if (category_name, category_url) not in categories:
                categories.append((category_name, category_url))

        print(f"\n✅ Found {len(categories)} categories")
        for idx, (name, url) in enumerate(categories[:10], 1):
            print(f"  {idx}. {name}")
        if len(categories) > 10:
            print(f"  ... and {len(categories) - 10} more")

        return categories

    except Exception as e:
        print(f"❌ Error extracting categories: {e}")
        return []


def download_all_categories(scraper, categories, max_scrolls=100, batch_size=10,
                           download_dir="noor_books", metadata_file="metadata.csv",
                           category_delay_min=30, category_delay_max=60):
    """
    Download books from multiple categories with delays between each

    Args:
        categories: List of tuples [(category_name, category_url), ...]
        category_delay_min: Minimum seconds to wait between categories
        category_delay_max: Maximum seconds to wait between categories
    """
    total_categories = len(categories)
    overall_downloaded = 0
    overall_skipped = 0
    overall_failed = 0

    print(f"\n{'='*60}")
    print(f"🚀 Starting multi-category download")
    print(f"📚 Total categories: {total_categories}")
    print(f"{'='*60}")

    for idx, (category_name, category_url) in enumerate(categories, 1):
        print(f"\n{'#'*60}")
        print(f"📂 CATEGORY {idx}/{total_categories}: {category_name}")
        print(f"🔗 {category_url}")
        print(f"{'#'*60}")

        try:
            # Resolve URL (in case it's a fake URL)
            resolved_url = scraper.resolve_category_url(category_url)

            # Download books from this category
            # Note: We don't pass return values, just track progress in output
            download_books_from_category(
                scraper,
                resolved_url,
                max_scrolls=max_scrolls,
                batch_size=batch_size,
                download_dir=download_dir,
                metadata_file=metadata_file
            )

            # If not the last category, wait before moving to next
            if idx < total_categories:
                wait_time = random.randint(category_delay_min, category_delay_max)
                print(f"\n⏳ Waiting {wait_time} seconds before next category...")
                time.sleep(wait_time)

        except Exception as e:
            print(f"\n❌ Error processing category '{category_name}': {e}")
            print(f"⏭️  Skipping to next category...")
            continue

    print(f"\n{'='*60}")
    print(f"🎉 ALL CATEGORIES COMPLETE!")
    print(f"📊 Processed {total_categories} categories")
    print(f"{'='*60}")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    EMAIL = "n8n@bayaan.net"
    PASSWORD = "3Cc'#B9pig"

    # ========== CONFIGURATION ==========
    # Set to True to download ALL categories from a page, False for single category
    MULTI_CATEGORY_MODE = True

    # For multi-category mode: URL of the page with category listings
    CATEGORIES_PAGE_URL = "https://www.noor-book.com/"

    # For single category mode: specific category URL
    SINGLE_CATEGORY_URL = "https://www.noor-book.com/tag/آداب-وأخلاق-إسلامية"

    # Delay between categories (in seconds) to avoid detection
    CATEGORY_DELAY_MIN = 30  # Minimum wait time
    CATEGORY_DELAY_MAX = 60  # Maximum wait time
    # ===================================

    print("="*60)
    print("🚀 NOOR-BOOK DOWNLOADER (SELENIUM-ONLY)")
    print("📌 Browser will stay VISIBLE so you can solve CAPTCHA")
    if MULTI_CATEGORY_MODE:
        print("📚 MODE: Multi-category (downloading from ALL categories)")
    else:
        print("📚 MODE: Single category")
    print("="*60)

    scraper = None

    try:
        # Initialize scraper (browser visible)
        scraper = NoorBookSeleniumScraper(headless=False, download_dir="noor_books")

        # Login
        print("\n📌 STEP 1: Logging in...")
        scraper.login(EMAIL, PASSWORD)

        if MULTI_CATEGORY_MODE:
            # Multi-category mode: extract all categories and download from each
            print("\n📌 STEP 2: Extracting all categories...")
            categories = extract_categories_from_page(scraper, CATEGORIES_PAGE_URL)

            if not categories:
                print("❌ No categories found!")
            else:
                print(f"\n📌 STEP 3: Downloading books from {len(categories)} categories...")
                download_all_categories(
                    scraper,
                    categories,
                    max_scrolls=100,
                    batch_size=10,
                    download_dir="noor_books",
                    metadata_file="metadata.csv",
                    category_delay_min=CATEGORY_DELAY_MIN,
                    category_delay_max=CATEGORY_DELAY_MAX
                )
        else:
            # Single category mode: download from one category only
            print("\n📌 STEP 2: Resolving category URL...")
            resolved_url = scraper.resolve_category_url(SINGLE_CATEGORY_URL)
            print(f"📂 Using URL: {resolved_url}")

            print("\n📌 STEP 3: Downloading books...")
            download_books_from_category(
                scraper,
                resolved_url,
                max_scrolls=100,
                batch_size=10,
                download_dir="noor_books",
                metadata_file="metadata.csv"
            )

        print("\n✨ All done!")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        if scraper:
            print("\n🔒 Closing browser...")
            scraper.close()
