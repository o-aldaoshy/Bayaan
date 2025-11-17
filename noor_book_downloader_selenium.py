import time
import cloudscraper
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
import csv
import json


# =====================================================
# 1) LOGIN USING SELENIUM (REAL BROWSER)
# =====================================================

def selenium_login(email, password, headless=False):
    """Login to noor-book.com using Selenium"""
    print("🌐 Launching Chrome browser for login...")

    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.set_page_load_timeout(30)

        login_url = "https://www.noor-book.com/login"
        driver.get(login_url)

        print("⏳ Waiting for JS to initialize...")
        time.sleep(4)

        print("📜 Scrolling down to reveal login form...")
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(2)

        print("📌 Trying to activate email login tab...")
        try:
            driver.execute_script("""
                if (document.querySelector('.show_email')) {
                    document.querySelector('.show_email').click();
                }
            """)
            time.sleep(1)
        except Exception as e:
            print(f"⚠ Could not click email tab: {e}")

        print("🔍 Searching for visible email field...")
        email_input = None

        # Try multiple times to find the email field
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
                print(f"⚠ Email field not found, scrolling more (attempt {attempt + 1}/3)...")
                driver.execute_script("window.scrollTo(0, 900);")
                time.sleep(1)

        if email_input is None:
            raise Exception("❌ Email field not found after 3 attempts — site layout may have changed")

        print("📝 Entering email...")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", email_input)
        time.sleep(0.5)
        email_input.click()
        time.sleep(0.3)
        email_input.clear()
        email_input.send_keys(email)

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
        time.sleep(0.5)
        password_input.click()
        password_input.clear()
        password_input.send_keys(password)

        print("🔧 Setting login type to email...")
        driver.execute_script("""
            var typeField = document.querySelector("input[name='type']");
            if (typeField) {
                typeField.value = "email";
            }
        """)

        print("🔒 Clicking login button...")
        login_button = driver.find_element(By.CSS_SELECTOR, ".submit-login")
        driver.execute_script("arguments[0].click();", login_button)

        print("⏳ Waiting for authentication...")
        time.sleep(6)

        # Check if login was successful
        current_url = driver.current_url
        if "/login" in current_url:
            # Save debug info
            driver.save_screenshot("login_failed.png")
            with open("login_failed.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise Exception("❌ Login failed — still on login page. Check login_failed.png/html for details")

        print("✅ Login successful!")

        # Get cookies
        cookies = driver.get_cookies()

        return cookies

    except Exception as e:
        print(f"❌ Login error: {e}")
        raise
    finally:
        if driver:
            driver.quit()



# =====================================================
# 2) AUTHENTICATED CLOUDSCRAPER
# =====================================================

def get_authenticated_scraper(cookies):
    """Create cloudscraper session with cookies from Selenium"""
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )

    # Add cookies to scraper
    for cookie in cookies:
        scraper.cookies.set(
            name=cookie['name'],
            value=cookie['value'],
            domain=cookie.get('domain', '.noor-book.com'),
            path=cookie.get('path', '/')
        )

    print("🔐 Session cookies imported into Cloudscraper!")
    return scraper



# =====================================================
# 3) GET DOWNLOAD LINK USING SELENIUM (handles JavaScript timer)
# =====================================================

def get_download_link_with_selenium(book_url, cookies, timeout=30):
    """
    Uses Selenium to click the download button and wait for the actual download link to appear in the modal
    Returns: (download_url, size_text, file_extension)
    """
    print("🌐 Opening book page with Selenium to get download link...")

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = None
    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.set_page_load_timeout(timeout)

        # Add cookies to maintain session
        driver.get("https://www.noor-book.com")

        # Add each cookie with proper domain
        for cookie in cookies:
            cookie_dict = {
                'name': cookie['name'],
                'value': cookie['value'],
                'path': cookie.get('path', '/'),
            }
            # Only add domain if it's valid for the current domain
            if 'domain' in cookie and 'noor-book.com' in cookie['domain']:
                cookie_dict['domain'] = cookie['domain']

            try:
                driver.add_cookie(cookie_dict)
            except Exception as e:
                print(f"⚠ Could not add cookie {cookie['name']}: {e}")

        # Now go to the book page
        print(f"📖 Loading book page: {book_url}")
        driver.get(book_url)

        # Wait for page to load
        wait = WebDriverWait(driver, timeout)

        # Wait for page JavaScript to initialize
        print("⏳ Waiting for page JavaScript to load...")
        time.sleep(5)

        # Scroll down to make download button visible
        driver.execute_script("window.scrollTo(0, 800);")
        time.sleep(2)

        # Find and click download button
        print("🔍 Looking for download button...")
        try:
            download_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#download_circle a.download-btn, a.download-btn, .download-button"))
            )

            print("✅ Found download button, clicking...")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", download_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", download_button)

            print("✅ Clicked! Waiting for modal and download link...")

            # Wait for the actual download link to appear (after JS timer)
            # Try multiple selectors as the site might use different ones
            download_link = None
            selectors = [
                "a.internal_download_link",
                ".download-modal a[href*='download']",
                "#download-modal a[href*='.pdf']",
                "a[href*='download'][href*='.pdf']"
            ]

            for selector in selectors:
                try:
                    download_link = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if download_link:
                        print(f"✅ Found download link with selector: {selector}")
                        break
                except TimeoutException:
                    continue

            if not download_link:
                raise Exception("❌ Download link not found with any selector")

            download_url = download_link.get_attribute("href")

            if not download_url:
                raise Exception("❌ Download link has no href attribute")

            # Extract size if present
            size_text = ""
            link_text = download_link.text
            if "(" in link_text:
                size_text = link_text.split("(")[-1].replace(")", "").strip()

            # Determine file extension
            file_ext = ".pdf"  # Default
            if ".epub" in download_url.lower():
                file_ext = ".epub"
            elif ".mobi" in download_url.lower():
                file_ext = ".mobi"
            elif ".djvu" in download_url.lower():
                file_ext = ".djvu"

            print(f"✅ Download URL: {download_url[:100]}...")
            return download_url, size_text, file_ext

        except TimeoutException as e:
            print(f"❌ Timeout waiting for download button or link: {e}")
            raise

    except Exception as e:
        print(f"❌ Error getting download link: {e}")
        # Save debug info
        if driver:
            try:
                driver.save_screenshot("debug_download_screenshot.png")
                with open("debug_download_page.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("📸 Saved debug_download_screenshot.png and debug_download_page.html")
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
    """Extract title and author from book page"""
    title_tag = book_soup.find("h1", class_="book-title")
    title = title_tag.text.strip() if title_tag else "Unknown Title"

    author_tag = book_soup.find("a", class_="book-author")
    author = author_tag.text.strip() if author_tag else "Unknown Author"

    return title, author



# =====================================================
# 5) RESOLVE REAL HASHED CATEGORY URL
# =====================================================

def resolve_real_category_url(scraper, fake_url):
    """
    Convert Arabic category URL to the real hashed URL
    IMPROVED: Tries multiple books if the first one fails
    """
    print(f"🔎 Resolving REAL category URL for: {fake_url}")

    try:
        r = scraper.get(fake_url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Find all book cards (try multiple possible class names)
        cards = soup.find_all("div", class_="book-restult")
        if not cards:
            cards = soup.find_all("div", class_="book-result")  # Try alternative spelling
        if not cards:
            cards = soup.find_all("div", class_="book-card")

        if not cards:
            print("❌ Could not find book cards on this Arabic URL!")
            return fake_url

        print(f"✅ Found {len(cards)} book cards, trying to extract real category URL...")

        # Try multiple books (not just the first one)
        for i, card in enumerate(cards[:5]):  # Try first 5 books
            book_link = card.find("a", href=True)
            if not book_link:
                continue

            book_url = "https://www.noor-book.com" + book_link["href"]
            print(f"📘 Checking book {i+1}: {book_url}")

            try:
                r2 = scraper.get(book_url, timeout=30)
                r2.raise_for_status()
                bs = BeautifulSoup(r2.text, "html.parser")

                # Look for the real tag/category link
                tag_link = bs.find("a", href=lambda x: x and x.startswith("/tag/"))
                if tag_link:
                    real_url = "https://www.noor-book.com" + tag_link["href"]
                    print(f"✅ REAL category URL found: {real_url}")
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
# 6) DOWNLOAD FUNCTION
# =====================================================

def sanitize_filename(title):
    """Clean filename and limit length"""
    valid_chars = []
    for c in title:
        if c.isalnum() or c in ' ._-' or '\u0600' <= c <= '\u06FF':  # Include Arabic chars
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
    """
    Download books from a category page
    IMPROVED: Better error handling, file validation, retry logic
    """
    os.makedirs(download_dir, exist_ok=True)

    # Initialize CSV
    csv_exists = os.path.exists(metadata_file)

    downloaded_count = 0
    failed_count = 0

    for page in range(1, max_pages + 1):
        print(f"\n{'='*60}")
        print(f"📄 Fetching category page {page}/{max_pages}")
        print(f"{'='*60}")

        # Build page URL
        if page == 1:
            url = category_url
        else:
            # Handle different pagination patterns
            if '?' in category_url:
                url = f"{category_url}&page={page}"
            else:
                url = f"{category_url}/page-{page}"

        try:
            r = scraper.get(url, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to load page {page}: {e}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Find book cards (try multiple class names)
        cards = soup.find_all("div", class_="book-restult")
        if not cards:
            cards = soup.find_all("div", class_="book-result")
        if not cards:
            cards = soup.find_all("div", class_="book-card")

        if not cards:
            print("⚠ No books found on this page")
            break

        print(f"✅ Found {len(cards)} books on page {page}")

        for idx, card in enumerate(cards, 1):
            book_link = card.find("a", href=True)
            if not book_link:
                print(f"⚠ Skipping card {idx} - no link found")
                continue

            book_page = "https://www.noor-book.com" + book_link["href"]
            print(f"\n[Book {idx}/{len(cards)}] 🔎 Opening: {book_page}")

            try:
                # Get basic metadata using cloudscraper
                r2 = scraper.get(book_page, timeout=30)
                r2.raise_for_status()
                book_soup = BeautifulSoup(r2.text, "html.parser")
                title, author = extract_book_metadata(book_soup)

                print(f"📚 Title: {title}")
                print(f"✍️  Author: {author}")

                # Use Selenium to get the download link
                download_url, size_text, file_ext = get_download_link_with_selenium(book_page, cookies)

                if not download_url:
                    print("❌ No download link found, skipping")
                    failed_count += 1
                    continue

                # Prepare filename
                filename = sanitize_filename(title)
                local_path = os.path.join(download_dir, f"{downloaded_count+1:04d}_{filename}{file_ext}")

                # Skip if already exists and valid
                if os.path.exists(local_path) and validate_file(local_path):
                    print(f"✅ Already exists and valid: {local_path}")
                    downloaded_count += 1
                    continue

                print(f"⬇️  Downloading: {title} ({size_text})")

                # Download file
                pdf_response = scraper.get(download_url, timeout=120, stream=True)
                pdf_response.raise_for_status()

                # Write file
                with open(local_path, "wb") as outfile:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
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

                # Batch pause
                if downloaded_count % batch_size == 0:
                    print(f"⏸  Pausing 10 seconds (batch of {batch_size} complete)...")
                    time.sleep(10)

                # Small delay between books
                time.sleep(2)

            except Exception as e:
                print(f"❌ Error processing book: {e}")
                failed_count += 1
                continue

        # Delay between pages
        print(f"\n⏸  Page {page} complete. Waiting 5 seconds before next page...")
        time.sleep(5)

    print(f"\n{'='*60}")
    print(f"🎉 Download complete!")
    print(f"✅ Successfully downloaded: {downloaded_count} books")
    print(f"❌ Failed: {failed_count} books")
    print(f"{'='*60}")



# =====================================================
# 7) MAIN
# =====================================================

if __name__ == "__main__":

    # LOGIN CREDENTIALS
    EMAIL = "n8n@bayaan.net"
    PASSWORD = "3Cc'#B9pig"

    # CATEGORY URL (Arabic or English)
    CATEGORY_URL = "https://www.noor-book.com/tag/آداب-وأخلاق-إسلامية"

    print("="*60)
    print("🚀 NOOR-BOOK.COM DOWNLOADER")
    print("="*60)

    # Step 1: Login
    print("\n📌 STEP 1: Logging in...")
    cookies = selenium_login(EMAIL, PASSWORD, headless=False)

    # Step 2: Create authenticated scraper
    print("\n📌 STEP 2: Creating authenticated session...")
    scraper = get_authenticated_scraper(cookies)

    # Step 3: Resolve real category URL
    print("\n📌 STEP 3: Resolving category URL...")
    CATEGORY_URL = resolve_real_category_url(scraper, CATEGORY_URL)
    print(f"📂 Final category URL: {CATEGORY_URL}")

    # Step 4: Download books
    print("\n📌 STEP 4: Starting download...")
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
