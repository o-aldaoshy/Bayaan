import time
import random
import cloudscraper
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import os
import csv
import json


# =====================================================
# ANTI-BOT DETECTION UTILITIES
# =====================================================

def random_delay(min_sec=1, max_sec=3):
    """Random delay to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))


def human_like_mouse_move(driver, element):
    """Move mouse in a human-like way to an element"""
    try:
        action = ActionChains(driver)
        action.move_to_element(element).perform()
        random_delay(0.2, 0.5)
    except:
        pass


def random_scroll(driver):
    """Scroll randomly like a human"""
    scroll_amount = random.randint(300, 800)
    driver.execute_script(f"window.scrollTo(0, {scroll_amount});")
    random_delay(0.5, 1.5)


def inject_stealth_js(driver):
    """Inject JavaScript to hide automation markers"""
    stealth_js = """
    // Overwrite the `navigator.webdriver` property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });

    // Overwrite the `plugins` property to use a fake PluginArray
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });

    // Overwrite the `languages` property
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en', 'ar']
    });

    // Remove Selenium/WebDriver traces
    window.navigator.chrome = {
        runtime: {}
    };

    // Mock permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({state: Notification.permission}) :
            originalQuery(parameters)
    );
    """

    try:
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_js
        })
    except:
        # Fallback for older versions
        driver.execute_script(stealth_js)


# =====================================================
# 1) LOGIN USING SELENIUM (REAL BROWSER) - STEALTH MODE
# =====================================================

def selenium_login(email, password, headless=False):
    """Login to noor-book.com using Selenium with anti-detection"""
    print("🌐 Launching Chrome browser for login (STEALTH MODE)...")

    options = uc.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")

    # Anti-detection arguments
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument(f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Additional stealth options
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Random window size to avoid fingerprinting
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
        print(f"🔗 Navigating to: {login_url}")
        driver.get(login_url)

        print("⏳ Waiting for page to load naturally...")
        random_delay(3, 5)

        # Random scroll to mimic human behavior
        print("🖱️  Scrolling like a human...")
        random_scroll(driver)
        random_delay(1, 2)

        print("📌 Activating email login tab...")
        try:
            driver.execute_script("""
                var emailTab = document.querySelector('.show_email');
                if (emailTab) {
                    emailTab.click();
                }
            """)
            random_delay(1, 2)
        except Exception as e:
            print(f"⚠ Could not click email tab: {e}")

        print("🔍 Searching for email field...")
        email_input = None

        # Try multiple times with random delays
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
                print(f"⚠ Attempt {attempt + 1}/3 - scrolling more...")
                random_scroll(driver)
                random_delay(1, 2)

        if email_input is None:
            raise Exception("❌ Email field not found after 3 attempts")

        print("📝 Entering email with human-like typing...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", email_input)
        random_delay(0.5, 1)

        # Click and type like a human
        human_like_mouse_move(driver, email_input)
        email_input.click()
        random_delay(0.3, 0.6)
        email_input.clear()

        # Type character by character with random delays
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
            raise Exception("❌ Password field not found")

        print("🔑 Entering password...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", password_input)
        random_delay(0.5, 1)

        human_like_mouse_move(driver, password_input)
        password_input.click()
        random_delay(0.3, 0.6)
        password_input.clear()

        # Type password character by character
        for char in password:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        random_delay(0.5, 1)

        print("🔧 Setting login type...")
        driver.execute_script("""
            var typeField = document.querySelector("input[name='type']");
            if (typeField) {
                typeField.value = "email";
            }
        """)

        print("🔒 Clicking login button...")
        login_button = driver.find_element(By.CSS_SELECTOR, ".submit-login")

        # Move mouse to button before clicking
        human_like_mouse_move(driver, login_button)
        random_delay(0.3, 0.7)

        driver.execute_script("arguments[0].click();", login_button)

        print("⏳ Waiting for authentication...")
        random_delay(5, 8)

        # Check for CAPTCHA or bot detection
        page_text = driver.page_source.lower()
        if 'captcha' in page_text or 'robot' in page_text or 'bot' in page_text:
            print("⚠️  CAPTCHA or bot detection detected!")
            print("🖐️  Please solve the CAPTCHA manually if visible...")
            input("Press ENTER after solving CAPTCHA...")

        # Check if login was successful
        current_url = driver.current_url
        if "/login" in current_url:
            driver.save_screenshot("login_failed.png")
            with open("login_failed.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise Exception("❌ Login failed. Check login_failed.png/html")

        print("✅ Login successful!")

        # Get cookies
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
# 2) AUTHENTICATED CLOUDSCRAPER - ENHANCED
# =====================================================

def get_authenticated_scraper(cookies):
    """Create cloudscraper session with cookies from Selenium"""
    # Cloudscraper automatically handles many anti-bot measures
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        },
        delay=10,  # Add delay to solve challenges
        captcha={
            'provider': '2captcha'  # Can be configured if you have API key
        }
    )

    # Copy cookies from Selenium
    for cookie in cookies:
        scraper.cookies.set(
            name=cookie['name'],
            value=cookie['value'],
            domain=cookie.get('domain', '.noor-book.com'),
            path=cookie.get('path', '/')
        )

    # Set headers to match browser
    scraper.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })

    print("🔐 Session cookies and headers configured!")
    return scraper


# =====================================================
# 3) GET DOWNLOAD LINK - STEALTH MODE
# =====================================================

def get_download_link_with_selenium(book_url, cookies, timeout=40):
    """
    Uses Selenium to get download link with anti-detection measures
    """
    print("🌐 Opening book page (STEALTH MODE)...")

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
        driver.set_page_load_timeout(timeout)

        # Inject stealth JS
        inject_stealth_js(driver)

        # Add cookies
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

        # Navigate to book page
        print(f"📖 Loading: {book_url}")
        driver.get(book_url)

        # Wait naturally
        print("⏳ Waiting for page load...")
        random_delay(4, 6)

        # Random scroll
        random_scroll(driver)
        random_delay(1, 2)

        wait = WebDriverWait(driver, timeout)

        # Find download button
        print("🔍 Looking for download button...")
        selectors = [
            "#download_circle a.download-btn",
            "a.download-btn",
            ".download-button",
            "a[href*='download']"
        ]

        download_button = None
        for selector in selectors:
            try:
                download_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found button with: {selector}")
                break
            except TimeoutException:
                continue

        if not download_button:
            raise Exception("❌ Download button not found")

        # Scroll to button naturally
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", download_button)
        random_delay(1, 2)

        # Move mouse and click
        human_like_mouse_move(driver, download_button)
        random_delay(0.5, 1)

        print("🖱️  Clicking download button...")
        driver.execute_script("arguments[0].click();", download_button)

        print("⏳ Waiting for download link to appear...")
        random_delay(8, 12)  # Sites often have JS timers

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
                download_link = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found download link: {selector}")
                break
            except TimeoutException:
                continue

        if not download_link:
            raise Exception("❌ Download link not found")

        download_url = download_link.get_attribute("href")
        if not download_url:
            raise Exception("❌ Download link has no href")

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

        print(f"✅ Download URL obtained: {download_url[:80]}...")
        return download_url, size_text, file_ext

    except Exception as e:
        print(f"❌ Error: {e}")
        if driver:
            try:
                driver.save_screenshot("debug_download.png")
                with open("debug_download.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("📸 Debug files saved")
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
    """Extract title and author"""
    title_tag = book_soup.find("h1", class_="book-title")
    title = title_tag.text.strip() if title_tag else "Unknown Title"

    author_tag = book_soup.find("a", class_="book-author")
    author = author_tag.text.strip() if author_tag else "Unknown Author"

    return title, author


# =====================================================
# 5) RESOLVE CATEGORY URL
# =====================================================

def resolve_real_category_url(scraper, fake_url):
    """Convert Arabic URL to real hashed URL"""
    print(f"🔎 Resolving category URL...")

    try:
        r = scraper.get(fake_url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Find book cards
        cards = soup.find_all("div", class_="book-restult") or \
                soup.find_all("div", class_="book-result") or \
                soup.find_all("div", class_="book-card")

        if not cards:
            print("⚠ No book cards found")
            return fake_url

        print(f"✅ Found {len(cards)} books, checking for real URL...")

        # Try first 5 books
        for i, card in enumerate(cards[:5]):
            book_link = card.find("a", href=True)
            if not book_link:
                continue

            book_url = "https://www.noor-book.com" + book_link["href"]

            try:
                random_delay(1, 2)  # Anti-bot delay
                r2 = scraper.get(book_url, timeout=30)
                r2.raise_for_status()
                bs = BeautifulSoup(r2.text, "html.parser")

                tag_link = bs.find("a", href=lambda x: x and x.startswith("/tag/"))
                if tag_link:
                    real_url = "https://www.noor-book.com" + tag_link["href"]
                    print(f"✅ Real URL: {real_url}")
                    return real_url
            except:
                continue

        print("⚠ Using original URL")
        return fake_url

    except Exception as e:
        print(f"❌ Error: {e}")
        return fake_url


# =====================================================
# 6) UTILITIES
# =====================================================

def sanitize_filename(title):
    """Clean filename"""
    valid_chars = []
    for c in title:
        if c.isalnum() or c in ' ._-' or '\u0600' <= c <= '\u06FF':
            valid_chars.append(c)
    return ''.join(valid_chars).strip()[:100]


def validate_file(file_path, min_size=1024):
    """Validate downloaded file"""
    if not os.path.exists(file_path):
        return False

    file_size = os.path.getsize(file_path)
    if file_size < min_size:
        return False

    # Check PDF header
    if file_path.endswith('.pdf'):
        try:
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return False
        except:
            return False

    return True


# =====================================================
# 7) MAIN DOWNLOAD FUNCTION
# =====================================================

def download_books_from_category(scraper, cookies, category_url, max_pages=5, batch_size=10,
                                 download_dir="noor_books", metadata_file="metadata.csv"):
    """Download books with anti-detection measures"""
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

        try:
            # Random delay to avoid detection
            random_delay(2, 4)

            r = scraper.get(url, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Find books
        cards = soup.find_all("div", class_="book-restult") or \
                soup.find_all("div", class_="book-result") or \
                soup.find_all("div", class_="book-card")

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
                # Random delay
                random_delay(2, 4)

                # Get metadata
                r2 = scraper.get(book_page, timeout=30)
                r2.raise_for_status()
                book_soup = BeautifulSoup(r2.text, "html.parser")
                title, author = extract_book_metadata(book_soup)

                print(f"📚 {title}")
                print(f"✍️  {author}")

                # Get download link with Selenium
                download_url, size_text, file_ext = get_download_link_with_selenium(book_page, cookies)

                if not download_url:
                    print("❌ No download link")
                    failed_count += 1
                    continue

                # Prepare filename
                filename = sanitize_filename(title)
                local_path = os.path.join(download_dir, f"{downloaded_count+1:04d}_{filename}{file_ext}")

                # Skip if exists
                if os.path.exists(local_path) and validate_file(local_path):
                    print(f"✅ Already downloaded")
                    downloaded_count += 1
                    continue

                print(f"⬇️  Downloading ({size_text})...")

                # Download with random delay
                random_delay(1, 2)
                pdf_response = scraper.get(download_url, timeout=120, stream=True)
                pdf_response.raise_for_status()

                # Save file
                with open(local_path, "wb") as outfile:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        if chunk:
                            outfile.write(chunk)

                # Validate
                if not validate_file(local_path):
                    print(f"❌ File validation failed")
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

                # Batch pause
                if downloaded_count % batch_size == 0:
                    print(f"⏸  Batch complete, pausing...")
                    random_delay(10, 15)

            except Exception as e:
                print(f"❌ Error: {e}")
                failed_count += 1

        # Page delay
        print(f"\n⏸  Page complete, waiting...")
        random_delay(5, 8)

    print(f"\n{'='*60}")
    print(f"🎉 Complete!")
    print(f"✅ Downloaded: {downloaded_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"{'='*60}")


# =====================================================
# 8) MAIN
# =====================================================

if __name__ == "__main__":

    EMAIL = "n8n@bayaan.net"
    PASSWORD = "3Cc'#B9pig"
    CATEGORY_URL = "https://www.noor-book.com/tag/آداب-وأخلاق-إسلامية"

    print("="*60)
    print("🚀 NOOR-BOOK DOWNLOADER - STEALTH MODE")
    print("="*60)

    try:
        # Login
        print("\n📌 STEP 1: Login...")
        cookies = selenium_login(EMAIL, PASSWORD, headless=False)

        # Create scraper
        print("\n📌 STEP 2: Creating session...")
        scraper = get_authenticated_scraper(cookies)

        # Resolve URL
        print("\n📌 STEP 3: Resolving URL...")
        CATEGORY_URL = resolve_real_category_url(scraper, CATEGORY_URL)
        print(f"📂 Final URL: {CATEGORY_URL}")

        # Download
        print("\n📌 STEP 4: Downloading...")
        download_books_from_category(
            scraper,
            cookies,
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
