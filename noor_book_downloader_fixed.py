import time
import random
import cloudscraper
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import os
import csv
import json


# =====================================================
# ANTI-BOT UTILITIES
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


def inject_stealth_js(driver):
    """Inject JavaScript to hide automation markers"""
    stealth_js = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en', 'ar']});
    window.navigator.chrome = {runtime: {}};
    """
    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': stealth_js})
    except:
        driver.execute_script(stealth_js)


# =====================================================
# 1) LOGIN USING SELENIUM (REAL BROWSER) - IMPROVED
# =====================================================

def selenium_login(email, password):
    print("🌐 Launching Chrome browser for login (STEALTH MODE)...")

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")

    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Random window size
    window_width = random.randint(1200, 1920)
    window_height = random.randint(800, 1080)
    options.add_argument(f"--window-size={window_width},{window_height}")

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        driver.set_page_load_timeout(30)

        # Inject stealth JavaScript
        inject_stealth_js(driver)

        login_url = "https://www.noor-book.com/login"
        driver.get(login_url)

        print("⏳ Waiting for JS to initialize...")
        random_delay(3, 5)

        print("📜 Scrolling down to reveal login form...")
        scroll_amount = random.randint(500, 700)
        driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
        random_delay(1.5, 2.5)

        print("📌 Trying to activate email login tab...")
        try:
            driver.execute_script("""
                if (document.querySelector('.show_email')) {
                    document.querySelector('.show_email').click();
                }
            """)
            random_delay(1, 2)
        except Exception as e:
            print(f"⚠ Could not click email tab: {e}")

        print("🔍 Searching for visible email field...")
        email_input = None

        # Try up to 3 times
        for attempt in range(3):
            inputs = driver.find_elements(By.CSS_SELECTOR, "input[name='email']")
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
                print(f"⚠ Email field not in view, scrolling more (attempt {attempt + 1}/3)...")
                scroll_amount = random.randint(800, 1000)
                driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
                random_delay(1, 2)

        if email_input is None:
            driver.save_screenshot("login_error.png")
            raise Exception("❌ Email field STILL not found after scroll — site changed layout.")

        print("📝 Entering email with human-like typing...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", email_input)
        random_delay(0.5, 1)

        human_like_mouse_move(driver, email_input)
        email_input.click()
        random_delay(0.3, 0.6)
        email_input.clear()

        # Type character by character
        for char in email:
            email_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        random_delay(0.5, 1)

        print("🔍 Finding password field...")
        password_input = None
        pw_fields = driver.find_elements(By.CSS_SELECTOR, "input[name='password']")
        for pf in pw_fields:
            try:
                if pf.is_displayed():
                    password_input = pf
                    break
            except:
                continue

        if password_input is None:
            driver.save_screenshot("login_error.png")
            raise Exception("❌ Password field not found.")

        print("🔑 Entering password...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", password_input)
        random_delay(0.5, 1)

        human_like_mouse_move(driver, password_input)
        password_input.click()
        random_delay(0.3, 0.6)
        password_input.clear()

        # Type character by character
        for char in password:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        random_delay(0.5, 1)

        print("🔧 Forcing type=email...")
        driver.execute_script("""
            if (document.querySelector("input[name='type']")) {
                document.querySelector("input[name='type']").value = "email";
            }
        """)

        print("🔒 Clicking login...")
        login_button = driver.find_element(By.CSS_SELECTOR, ".submit-login")

        human_like_mouse_move(driver, login_button)
        random_delay(0.3, 0.7)
        driver.execute_script("arguments[0].click();", login_button)

        print("⏳ Waiting for authentication...")
        random_delay(5, 8)

        # Check for CAPTCHA or bot detection
        page_text = driver.page_source.lower()
        if 'captcha' in page_text or 'robot' in page_text:
            print("⚠️  CAPTCHA detected! Please solve it manually if visible...")
            input("Press ENTER after solving CAPTCHA...")

        if "/login" in driver.current_url:
            print("❌ Login FAILED — still on login page.")
            driver.save_screenshot("login_failed.png")
            with open("login_failed.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise Exception("❌ Login failed. Check login_failed.png/html")

        print("✅ Login successful!")

        cookies = driver.get_cookies()
        print(f"🍪 Captured {len(cookies)} cookies")
        return cookies

    except Exception as e:
        print(f"❌ Login error: {e}")
        raise
    finally:
        if driver:
            driver.quit()


# =====================================================
# 2) AUTHENTICATED CLOUDSCRAPER - IMPROVED
# =====================================================

def get_authenticated_scraper(cookies):
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False},
        delay=10
    )

    # Add cookies with proper domain/path
    for cookie in cookies:
        scraper.cookies.set(
            name=cookie['name'],
            value=cookie['value'],
            domain=cookie.get('domain', '.noor-book.com'),
            path=cookie.get('path', '/')
        )

    # Enhanced headers
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    print("🔐 Session cookies imported into Cloudscraper!")
    return scraper


# =====================================================
# 3) GET DOWNLOAD LINK USING SELENIUM - IMPROVED
# =====================================================

def get_download_link_with_selenium(book_url, cookies):
    """
    Uses Selenium to click the download button and wait for the actual download link to appear in the modal
    IMPROVED: Anti-detection, multiple selectors, better error handling
    """
    print("🌐 Opening book page with Selenium to get download link...")

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")

    # Random window size
    window_width = random.randint(1200, 1920)
    window_height = random.randint(800, 1080)
    options.add_argument(f"--window-size={window_width},{window_height}")

    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)
        driver.set_page_load_timeout(40)

        # Inject stealth JS
        inject_stealth_js(driver)

        # Add cookies to maintain session
        driver.get("https://www.noor-book.com")
        for cookie in cookies:
            cookie_dict = {
                'name': cookie['name'],
                'value': cookie['value'],
                'path': cookie.get('path', '/'),
            }
            if 'domain' in cookie and 'noor-book.com' in cookie['domain']:
                cookie_dict['domain'] = cookie['domain']

            try:
                driver.add_cookie(cookie_dict)
            except Exception as e:
                print(f"⚠ Cookie {cookie['name']} not added: {e}")

        # Now go to the book page
        print(f"📖 Loading book page...")
        driver.get(book_url)
        print("⏳ Waiting for page JavaScript to initialize...")

        random_delay(4, 6)

        # Scroll down to make sure the download button is in view
        scroll_amount = random.randint(700, 900)
        driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
        random_delay(1.5, 2.5)

        wait = WebDriverWait(driver, 30)

        # Wait for download button to be present and clickable
        print("🔍 Looking for download button...")

        # Try multiple selectors
        download_button = None
        selectors = [
            "#download_circle a.download-btn",
            "a.download-btn",
            ".download-button",
            "a[href*='download']"
        ]

        for selector in selectors:
            try:
                download_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found download button with selector: {selector}")
                break
            except TimeoutException:
                continue

        if not download_button:
            raise Exception("❌ Download button not found with any selector")

        print("✅ Found download button, clicking...")

        # Scroll to the button and click it
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", download_button)
        random_delay(1, 2)

        human_like_mouse_move(driver, download_button)
        random_delay(0.5, 1)

        driver.execute_script("arguments[0].click();", download_button)

        print("✅ Clicked! Waiting for modal and download link (this takes ~10 seconds)...")

        # Wait longer for the JavaScript timer
        random_delay(8, 12)

        # Wait for the modal to appear and the download link inside it
        # Try multiple selectors for the download link
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
                download_link = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found download link with selector: {selector}")
                break
            except TimeoutException:
                continue

        if not download_link:
            raise Exception("❌ Download link not found with any selector")

        print("✅ Download link appeared!")

        download_url = download_link.get_attribute("href")

        if not download_url:
            raise Exception("❌ Download link has no href attribute")

        # Extract size if present
        size_text = ""
        try:
            link_text = download_link.text
            if "(" in link_text:
                size_text = link_text.split("(")[-1].replace(")", "").strip()
        except:
            pass

        # Determine file extension
        file_ext = ".pdf"  # Default
        url_lower = download_url.lower()
        if ".epub" in url_lower:
            file_ext = ".epub"
        elif ".mobi" in url_lower:
            file_ext = ".mobi"
        elif ".djvu" in url_lower:
            file_ext = ".djvu"

        print(f"✅ Download URL obtained: {download_url[:80]}...")
        return download_url, size_text, file_ext

    except Exception as e:
        print(f"❌ Error getting download link: {e}")
        # Save screenshot and page source for debugging
        if driver:
            try:
                driver.save_screenshot("debug_screenshot.png")
                with open("debug_page_source.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("📸 Saved screenshot to debug_screenshot.png")
                print("📄 Saved page source to debug_page_source.html")
            except:
                pass
        return None, "", ".pdf"
    finally:
        if driver:
            driver.quit()


# =====================================================
# 4) EXTRACT BOOK METADATA
# =====================================================

def extract_book_metadata(book_soup):
    title_tag = book_soup.find("h1", class_="book-title")
    title = title_tag.text.strip() if title_tag else "Unknown Title"

    author_tag = book_soup.find("a", class_="book-author")
    author = author_tag.text.strip() if author_tag else "Unknown Author"

    return title, author


# =====================================================
# 5) RESOLVE REAL HASHED CATEGORY URL - IMPROVED
# =====================================================

def resolve_real_category_url(scraper, fake_url):
    print(f"🔎 Resolving REAL category URL for: {fake_url}")

    try:
        r = scraper.get(fake_url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # FIXED: Look for div with class "book-restult" instead of "a" with "book-card"
        # Try multiple class names
        cards = soup.find_all("div", class_="book-restult")
        if not cards:
            cards = soup.find_all("div", class_="book-result")
        if not cards:
            cards = soup.find_all("div", class_="book-card")

        if not cards:
            print("❌ Could not find book cards on this Arabic URL!")
            return fake_url

        print(f"✅ Found {len(cards)} book cards, trying to extract real category URL...")

        # IMPROVED: Try multiple books (not just the first one)
        for i, card in enumerate(cards[:5]):  # Try first 5 books
            book_link = card.find("a", href=True)
            if not book_link:
                continue

            book_url = "https://www.noor-book.com" + book_link["href"]
            print(f"📘 Checking book {i+1}: {book_url}")

            try:
                random_delay(1, 2)  # Anti-bot delay
                r2 = scraper.get(book_url, timeout=30)
                r2.raise_for_status()
                bs = BeautifulSoup(r2.text, "html.parser")

                tag_link = bs.find("a", href=lambda x: x and x.startswith("/tag/"))
                if tag_link:
                    real_url = "https://www.noor-book.com" + tag_link["href"]
                    print(f"✅ REAL category URL: {real_url}")
                    return real_url
            except Exception as e:
                print(f"⚠ Error checking book {i+1}: {e}")
                continue

        print("⚠ Could not extract real tag URL from any book, using original URL")
        return fake_url

    except Exception as e:
        print(f"❌ Error resolving category URL: {e}")
        return fake_url


# =====================================================
# 6) DOWNLOAD FUNCTION - IMPROVED
# =====================================================

def sanitize_filename(title):
    """Clean filename and include Arabic characters"""
    valid_chars = []
    for c in title:
        if c.isalnum() or c in ' ._-' or '\u0600' <= c <= '\u06FF':  # Include Arabic
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

    # Check file header for PDF
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


def download_books_from_category(scraper, cookies, category_url, max_pages=5, batch_size=10,
                                 download_dir="noor_books", metadata_file="metadata.csv"):

    os.makedirs(download_dir, exist_ok=True)

    csv_exists = os.path.exists(metadata_file)

    downloaded_count = 0
    failed_count = 0

    for page in range(1, max_pages + 1):
        print(f"\n{'='*60}")
        print(f"📄 Fetching category page {page}/{max_pages}")
        print(f"{'='*60}")

        # Build page URL with support for different pagination patterns
        if page == 1:
            url = category_url
        else:
            # Handle different pagination patterns
            if '?' in category_url:
                url = f"{category_url}&page={page}"
            else:
                url = f"{category_url}/page-{page}"

        try:
            random_delay(2, 4)  # Anti-bot delay
            r = scraper.get(url, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to load page {page}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # FIXED: Look for divs with class "book-restult" instead of "a" with "book-card"
        cards = soup.find_all("div", class_="book-restult")
        if not cards:
            cards = soup.find_all("div", class_="book-result")
        if not cards:
            cards = soup.find_all("div", class_="book-card")

        if not cards:
            print("⚠ No books found.")
            break

        print(f"✅ Found {len(cards)} books on this page")

        for idx, card in enumerate(cards, 1):
            # Find the book link inside the div
            book_link = card.find("a", href=True)
            if not book_link:
                print(f"⚠ Skipping card {idx} with no link")
                continue

            book_page = "https://www.noor-book.com" + book_link["href"]
            print(f"\n[Book {idx}/{len(cards)}] 🔎 Opening: {book_page}")

            try:
                # Random delay to avoid detection
                random_delay(2, 4)

                # Get basic metadata using cloudscraper
                r2 = scraper.get(book_page, timeout=30)
                r2.raise_for_status()
                book_soup = BeautifulSoup(r2.text, "html.parser")
                title, author = extract_book_metadata(book_soup)

                print(f"📚 Title: {title}")
                print(f"✍️  Author: {author}")

                # Use Selenium to get the download link (handles JavaScript timer)
                download_url, size_text, file_ext = get_download_link_with_selenium(book_page, cookies)

                if not download_url:
                    print("❌ No download link found.")
                    failed_count += 1
                    continue

                filename = sanitize_filename(title)
                local_path = os.path.join(download_dir, f"{downloaded_count+1:04d}_{filename}{file_ext}")

                # Skip if already exists and valid
                if os.path.exists(local_path) and validate_file(local_path):
                    print(f"✅ Already exists and valid: {local_path}")
                    downloaded_count += 1
                    continue

                print(f"⬇️  Downloading: {title} ({size_text})")

                # Random delay before download
                random_delay(1, 2)

                pdf_file = scraper.get(download_url, timeout=120, stream=True)
                pdf_file.raise_for_status()

                with open(local_path, "wb") as outfile:
                    for chunk in pdf_file.iter_content(chunk_size=8192):
                        if chunk:
                            outfile.write(chunk)

                # Validate downloaded file
                if not validate_file(local_path):
                    print(f"❌ Downloaded file failed validation")
                    os.remove(local_path)
                    failed_count += 1
                    continue

                print(f"✅ Saved and validated: {local_path}")

                downloaded_count += 1

                # Save metadata
                with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    if not csv_exists or downloaded_count == 1:
                        writer.writerow(["Title", "Author", "Size", "Download Link", "Page URL", "Local Filename"])
                        csv_exists = True
                    writer.writerow([title, author, size_text, download_url, book_page, local_path])

                if downloaded_count % batch_size == 0:
                    print(f"⏸  Pausing (batch of {batch_size} complete)...")
                    random_delay(10, 15)

            except Exception as e:
                print(f"❌ Error downloading: {e}")
                failed_count += 1
                continue

        # Delay between pages
        print(f"\n⏸  Page {page} complete. Waiting before next page...")
        random_delay(5, 8)

    print(f"\n{'='*60}")
    print(f"🎉 Downloading complete!")
    print(f"✅ Successfully downloaded: {downloaded_count} books")
    print(f"❌ Failed: {failed_count} books")
    print(f"{'='*60}")


# =====================================================
# 7) MAIN
# =====================================================

if __name__ == "__main__":

    EMAIL = "n8n@bayaan.net"
    PASSWORD = "3Cc'#B9pig"

    CATEGORY_URL = "https://www.noor-book.com/tag/آداب-وأخلاق-إسلامية"

    print("="*60)
    print("🚀 NOOR-BOOK.COM DOWNLOADER (FIXED VERSION)")
    print("="*60)

    try:
        # Step 1: Login
        print("\n📌 STEP 1: Logging in...")
        cookies = selenium_login(EMAIL, PASSWORD)

        # Step 2: Create authenticated scraper
        print("\n📌 STEP 2: Creating authenticated session...")
        scraper = get_authenticated_scraper(cookies)

        # Step 3: Convert Arabic URL → real hashed URL
        print("\n📌 STEP 3: Resolving category URL...")
        CATEGORY_URL = resolve_real_category_url(scraper, CATEGORY_URL)
        print("📌 Using final category URL:", CATEGORY_URL)

        # Step 4: Download books
        print("\n📌 STEP 4: Starting downloads...")
        download_books_from_category(
            scraper,
            cookies,  # Pass cookies so Selenium can maintain session
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
