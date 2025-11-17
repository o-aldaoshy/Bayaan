# Noor-Book Downloader - Bug Fixes & Anti-Bot Detection

## Issues Fixed

### 1. Bot Detection Evasion

**Problem**: The website was detecting automated browsers and blocking requests.

**Solutions Implemented**:

#### A. Selenium Stealth Mode
```python
# Hide webdriver property
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

# Mock Chrome runtime
window.navigator.chrome = { runtime: {} };
```

#### B. Human-Like Behavior
- **Random delays**: `random.uniform(min, max)` instead of fixed `time.sleep()`
- **Mouse movements**: ActionChains to move cursor naturally
- **Random scrolling**: Mimic human reading patterns
- **Character-by-character typing**: Simulate real typing speed

#### C. Browser Fingerprinting
- Random window sizes
- Proper user agent strings
- Disabled automation flags
- Randomized request timing

#### D. Enhanced Cloudscraper
- Automatic anti-bot challenge solving
- Proper cookie handling with domain attributes
- Realistic browser headers (Sec-Fetch-*)

### 2. Code Bugs Fixed

#### A. `resolve_real_category_url()` Was Fragile
**Before**:
```python
card = soup.find("div", class_="book-restult")  # Only first book
```

**After**:
```python
for i, card in enumerate(cards[:5]):  # Try first 5 books
    # Try each until one works
```

#### B. Missing Error Handling
**Before**:
```python
except:
    pass
```

**After**:
```python
except Exception as e:
    print(f"⚠ Could not add cookie {cookie['name']}: {e}")
```

#### C. Cookie Domain Issues
**Before**:
```python
scraper.cookies.set(cookie['name'], cookie['value'])
```

**After**:
```python
scraper.cookies.set(
    name=cookie['name'],
    value=cookie['value'],
    domain=cookie.get('domain', '.noor-book.com'),  # Explicit domain
    path=cookie.get('path', '/')
)
```

#### D. No File Validation
**Added**:
```python
def validate_file(file_path, min_size=1024):
    # Check file size
    # Verify PDF header (%PDF-)
    # Return False if invalid
```

#### E. Fixed File Extensions
**Before**: Always `.pdf`

**After**: Detect `.pdf`, `.epub`, `.mobi`, `.djvu` from URL

#### F. Better Pagination
**Before**: Only `/page-{N}`

**After**: Handle both `/page-{N}` and `?page={N}` patterns

### 3. Performance Improvements

- **Retry logic**: Try multiple selectors for elements
- **Timeout handling**: Proper WebDriverWait usage
- **Debug output**: Save screenshots and HTML on errors
- **Progress tracking**: Better logging and status updates

## Usage

### Installation
```bash
pip install -r requirements_noor.txt
```

### Run
```bash
python noor_book_downloader_stealth.py
```

### Key Features

1. **Non-headless login** (for CAPTCHA solving)
2. **Headless downloading** (faster, less resource-intensive)
3. **Random delays** (2-4 seconds between requests)
4. **Automatic retry** (tries multiple selectors)
5. **File validation** (ensures PDFs are valid)
6. **Metadata CSV** (tracks all downloads)

## Anti-Detection Techniques Summary

| Technique | Implementation | Purpose |
|-----------|----------------|---------|
| JavaScript injection | `inject_stealth_js()` | Hide automation markers |
| Random delays | `random_delay()` | Mimic human behavior |
| Mouse movements | `ActionChains` | Simulate real user |
| Random scrolling | `random_scroll()` | Natural page interaction |
| Cloudscraper | Auto challenge solver | Bypass Cloudflare/bot checks |
| Cookie handling | Proper domain/path | Maintain session |
| User agent rotation | Random UA strings | Avoid fingerprinting |
| Window size randomization | Random dimensions | Prevent browser fingerprinting |

## Troubleshooting

### Still Getting Detected?

1. **Use residential proxy**:
```python
options.add_argument('--proxy-server=http://your-proxy:port')
```

2. **Increase delays**:
```python
random_delay(5, 10)  # Slower but safer
```

3. **Manual CAPTCHA solving**:
The script will pause if CAPTCHA is detected - solve it manually

4. **Check cookies**:
Verify cookies are being saved properly in debug mode

### Common Errors

**"Email field not found"**
- Site layout changed, update selectors in code

**"Download link not found"**
- JavaScript timer might be longer, increase wait time
- Try additional selectors

**"Login failed"**
- Check credentials
- Look at `login_failed.png` for visual debugging
- Solve CAPTCHA if present

## Comparison: Original vs Fixed

| Issue | Original | Fixed |
|-------|----------|-------|
| Bot detection | ❌ Failed | ✅ Evaded |
| Error handling | ❌ Bare try/except | ✅ Detailed logging |
| Cookie handling | ⚠️ Basic | ✅ Full attributes |
| File validation | ❌ None | ✅ Header check |
| Category URL resolution | ⚠️ Fragile | ✅ Robust (tries 5 books) |
| Human behavior | ❌ Robot-like | ✅ Random delays, mouse moves |
| File extensions | ❌ Hardcoded .pdf | ✅ Auto-detect |
| Debug info | ⚠️ Limited | ✅ Screenshots + HTML |

## Files Created

- `noor_book_downloader_stealth.py` - Main script with all fixes
- `requirements_noor.txt` - Dependencies
- `NOOR_BOOK_FIXES.md` - This documentation

## Next Steps

If still facing issues:

1. **Use Selenium-Stealth library**:
```bash
pip install selenium-stealth
```

Add to code:
```python
from selenium_stealth import stealth
stealth(driver, ...)
```

2. **Implement CAPTCHA solver API** (2captcha, Anti-Captcha)

3. **Use residential proxies** (Bright Data, Oxylabs)

4. **Reduce scraping speed** (1 book per minute)

5. **Rotate user sessions** (login/logout periodically)
