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
        """Get download link from book page and extract title from modal"""
        print(f"📖 Getting download link from: {book_url}")

        try:
            self.driver.get(book_url)
            random_delay(4, 6)

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
                return None, "", ".pdf", "Unknown Title"

            # Click download button
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", download_button)
            random_delay(1, 2)
            human_like_mouse_move(self.driver, download_button)
            random_delay(0.5, 1)
            self.driver.execute_script("arguments[0].click();", download_button)

            print("⏳ Waiting for download modal to appear...")
            random_delay(8, 12)

            # Extract title from modal
            title = "Unknown Title"
            try:
                modal_title = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-title, h4.modal-title"))
                )
                title = modal_title.text.strip()
                if title:
                    print(f"📚 Title from modal: {title}")
            except:
                print("⚠ Could not extract title from modal")

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
        """Extract book title and author"""
        try:
            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            title_tag = soup.find("h1", class_="book-title")
            title = title_tag.text.strip() if title_tag else "Unknown Title"

            author_tag = soup.find("a", class_="book-author")
            author = author_tag.text.strip() if author_tag else "Unknown Author"

            return title, author
        except:
            return "Unknown Title", "Unknown Author"


    def close(self):
        """Close browser"""
        try:
            self.driver.quit()
        except:
            pass


# =====================================================
# MAIN DOWNLOAD FUNCTION
# =====================================================

def download_books_from_category(scraper, category_url, max_pages=5, batch_size=10,
                                 download_dir="noor_books", metadata_file="metadata.csv"):

    os.makedirs(download_dir, exist_ok=True)

    csv_exists = os.path.exists(metadata_file)
    downloaded_count = 0
    failed_count = 0

    for page in range(1, max_pages + 1):
        print(f"\n{'='*60}")
        print(f"📄 Page {page}/{max_pages}")
        print(f"{'='*60}")

        # Build URL
        if page == 1:
            url = category_url
        else:
            url = f"{category_url}/page-{page}" if '?' not in category_url else f"{category_url}&page={page}"

        # Get page
        random_delay(2, 4)
        html = scraper.get_page_source(url)
        if not html:
            print("❌ Failed to load page")
            continue

        soup = BeautifulSoup(html, "html.parser")

        # Find books
        cards = soup.find_all("div", class_="book-restult")
        if not cards:
            cards = soup.find_all("div", class_="book-result")
        if not cards:
            cards = soup.find_all("div", class_="book-card")

        if not cards:
            print("⚠ No books found")
            break

        print(f"✅ Found {len(cards)} books")

        for idx, card in enumerate(cards, 1):
            book_link = card.find("a", href=True)
            if not book_link:
                continue

            book_page = "https://www.noor-book.com" + book_link["href"]
            print(f"\n[{idx}/{len(cards)}] 🔎 {book_page}")

            try:
                random_delay(2, 4)

                # Get download link and title from modal
                download_url, size_text, file_ext, title = scraper.get_download_link(book_page)

                if not download_url:
                    print("❌ No download link")
                    failed_count += 1
                    continue

                # Also get author from book page
                scraper.driver.get(book_page)
                random_delay(1, 2)
                _, author = scraper.extract_metadata(book_page)
                print(f"✍️  {author}")

                # Prepare filename using title from modal
                filename = sanitize_filename(title)
                local_path = os.path.join(download_dir, f"{downloaded_count+1:04d}_{filename}{file_ext}")

                # Skip if exists and valid
                if os.path.exists(local_path) and validate_file(local_path):
                    print(f"✅ Already exists: {local_path}")
                    downloaded_count += 1
                    continue

                print(f"⬇️  Downloading ({size_text})...")

                # Download
                if not scraper.download_file(download_url, local_path):
                    failed_count += 1
                    continue

                # Validate
                if not validate_file(local_path):
                    print("❌ File validation failed")
                    os.remove(local_path)
                    failed_count += 1
                    continue

                print(f"✅ Saved: {local_path}")
                downloaded_count += 1

                # Save metadata
                with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    if not csv_exists or downloaded_count == 1:
                        writer.writerow(["Title", "Author", "Size", "Download Link", "Page URL", "Local Filename"])
                        csv_exists = True
                    writer.writerow([title, author, size_text, download_url, book_page, local_path])

                if downloaded_count % batch_size == 0:
                    print(f"⏸  Batch pause...")
                    random_delay(10, 15)

            except Exception as e:
                print(f"❌ Error: {e}")
                failed_count += 1

        print(f"\n⏸  Page complete, waiting...")
        random_delay(5, 8)

    print(f"\n{'='*60}")
    print(f"🎉 Complete!")
    print(f"✅ Downloaded: {downloaded_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"{'='*60}")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    EMAIL = "n8n@bayaan.net"
    PASSWORD = "3Cc'#B9pig"
    CATEGORY_URL = "https://www.noor-book.com/tag/آداب-وأخلاق-إسلامية"

    print("="*60)
    print("🚀 NOOR-BOOK DOWNLOADER (SELENIUM-ONLY)")
    print("📌 Browser will stay VISIBLE so you can solve CAPTCHA")
    print("="*60)

    scraper = None

    try:
        # Initialize scraper (browser visible)
        scraper = NoorBookSeleniumScraper(headless=False, download_dir="noor_books")

        # Login
        print("\n📌 STEP 1: Logging in...")
        scraper.login(EMAIL, PASSWORD)

        # Resolve URL
        print("\n📌 STEP 2: Resolving category URL...")
        CATEGORY_URL = scraper.resolve_category_url(CATEGORY_URL)
        print(f"📂 Using URL: {CATEGORY_URL}")

        # Download
        print("\n📌 STEP 3: Downloading books...")
        download_books_from_category(
            scraper,
            CATEGORY_URL,
            max_pages=5,
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
