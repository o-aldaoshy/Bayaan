# Noor-Book.com Downloader - Fixing 403 Forbidden Error

## Problem
The website `noor-book.com` uses **Cloudflare protection** which blocks automated requests, resulting in 403 Forbidden errors.

## Solutions

### Solution 1: Use Selenium (RECOMMENDED for Windows)

The Selenium version bypasses Cloudflare by using a real Chrome browser.

#### Installation on Windows:

```powershell
# Install Python packages
pip install selenium undetected-chromedriver beautifulsoup4
```

**Requirements:**
- Chrome browser must be installed on your system
- Internet connection

#### Usage:

```powershell
python noor_book_selenium.py
```

**Advantages:**
- ✅ Bypasses Cloudflare protection effectively
- ✅ Works like a real browser
- ✅ Most reliable method

**Disadvantages:**
- ❌ Opens a browser window (you'll see it working)
- ❌ Slower than direct HTTP requests
- ❌ Requires Chrome to be installed

---

### Solution 2: Use Cloudscraper (Updated version)

The updated `noor_book_downloader.py` now uses `cloudscraper` which attempts to bypass Cloudflare.

#### Installation:

```powershell
pip install requests cloudscraper beautifulsoup4 lxml
```

#### Usage:

```powershell
python noor_book_downloader.py
```

**Advantages:**
- ✅ No browser required
- ✅ Faster than Selenium
- ✅ Works in background

**Disadvantages:**
- ❌ May not work if Cloudflare protection is too strong
- ❌ Requires updates when Cloudflare changes

---

### Solution 3: Use a VPN or Proxy

Sometimes Cloudflare blocks specific IP ranges. Using a VPN might help.

---

### Solution 4: Manual Testing

You can test if the site is accessible in your browser:

1. Open Chrome and go to: https://www.noor-book.com
2. If you see a "Checking your browser" page, that's Cloudflare
3. Wait for it to complete, then try the scraper

---

## File Descriptions

| File | Purpose | Best For |
|------|---------|----------|
| `noor_book_selenium.py` | Uses Selenium with Chrome | **Windows users** - Most reliable |
| `noor_book_downloader.py` | Uses cloudscraper library | Servers, headless environments |
| `test_noor_connection.py` | Quick connection test | Testing if site is accessible |

---

## Troubleshooting

### Error: "ModuleNotFoundError"
**Solution:** Install the required package
```powershell
pip install [package-name]
```

### Error: "ChromeDriver not found"
**Solution:** Make sure Chrome browser is installed, or let undetected-chromedriver download it automatically

### Error: "403 Forbidden" persists
**Solutions:**
1. Use the Selenium version (`noor_book_selenium.py`)
2. Try from a different network/VPN
3. Wait a few hours and try again (Cloudflare may temporarily block your IP)
4. Check if the website is accessible in your browser first

### Browser opens but nothing happens
**Solution:** The site may be loading slowly. Increase the `delay` parameter:
```python
downloader.download_category(
    category_url=category_url,
    max_pages=10,
    max_books=50,
    delay=5  # Increase this number
)
```

---

## Recommended Workflow for Windows

1. **Install Chrome** (if not already installed)

2. **Install Python packages:**
   ```powershell
   pip install selenium undetected-chromedriver beautifulsoup4
   ```

3. **Run the Selenium version:**
   ```powershell
   python noor_book_selenium.py
   ```

4. **Monitor the browser window** that opens to ensure it's working

5. **Be patient** - Bypassing Cloudflare takes time

---

## Important Notes

⚠️ **Respect the Website:**
- Use appropriate delays between requests (3-5 seconds recommended)
- Don't download excessively
- Check the site's Terms of Service
- Consider rate limiting your downloads

⚠️ **Legal Notice:**
- This tool is for educational purposes
- Ensure you have the right to download the content
- Respect copyright laws in your jurisdiction

---

## Advanced Configuration

### Running in Headless Mode (No Browser Window)

Edit `noor_book_selenium.py`:
```python
downloader = NoorBookSeleniumDownloader(
    download_dir='noor_books',
    headless=True  # Change this to True
)
```

**Note:** Headless mode may not bypass Cloudflare as effectively.

### Customizing Download Settings

```python
downloader.download_category(
    category_url=category_url,
    max_pages=5,      # Fewer pages
    max_books=20,     # Limit books
    delay=5           # Longer delay (more polite)
)
```

---

## Still Having Issues?

If you continue to get 403 errors:

1. **Test in browser first:** Open https://www.noor-book.com in Chrome
2. **Check your IP:** The site might be blocking your region/IP
3. **Try a VPN:** Connect to a different country
4. **Wait and retry:** Cloudflare blocks may be temporary
5. **Contact site support:** Ask if automated access is allowed

---

## Credits

This scraper uses:
- `undetected-chromedriver` - To bypass Cloudflare detection
- `cloudscraper` - Alternative Cloudflare bypass method
- `BeautifulSoup4` - HTML parsing
- `Selenium` - Browser automation
