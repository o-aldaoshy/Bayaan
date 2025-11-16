"""
Advanced test to bypass anti-bot protection on noor-book.com
Using cloudscraper to bypass Cloudflare protection
"""

import cloudscraper
from fake_useragent import UserAgent
from urllib.parse import unquote
import time

def test_with_cloudscraper(url):
    """Test access using cloudscraper (bypasses Cloudflare)"""

    print("="*80)
    print(f"Testing access to: {unquote(url)}")
    print("="*80)

    # Test 1: Basic cloudscraper
    print("\n[Test 1] Using cloudscraper (basic)...")
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

        response = scraper.get(url, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} bytes")

        # Check for Cloudflare or CAPTCHA
        response_lower = response.text.lower()
        if 'cloudflare' in response_lower:
            print("   ⚠️  Cloudflare detected")
        if 'captcha' in response_lower:
            print("   ⚠️  CAPTCHA detected")
        if 'checking your browser' in response_lower:
            print("   ⚠️  Browser check detected")

        if response.status_code == 200:
            print("   ✅ SUCCESS")

            # Check for book content
            if 'كتاب' in response.text or 'book' in response_lower:
                print("   ✅ Found book-related content")

                # Save sample
                with open('sample_page_cloudscraper.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("   📄 Saved full page to: sample_page_cloudscraper.html")

                # Show some snippets
                print("\n   Sample content (first 500 chars):")
                print("   " + "-"*76)
                print("   " + response.text[:500].replace('\n', '\n   '))
                print("   " + "-"*76)

                return True
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
            # Save error page for debugging
            with open('error_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:5000])
            print("   📄 Saved error page sample to: error_page.html")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    time.sleep(2)

    # Test 2: Cloudscraper with custom headers
    print("\n[Test 2] Using cloudscraper with custom headers...")
    try:
        ua = UserAgent()
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

        scraper.headers.update({
            'User-Agent': ua.chrome,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })

        response = scraper.get(url, timeout=30)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} bytes")
        print(f"   Cookies received: {len(scraper.cookies)}")

        if response.status_code == 200:
            print("   ✅ SUCCESS")
            return True
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    return False


def test_with_delays(url):
    """Test with gradual approach (first homepage, then target)"""

    print("\n[Test 3] Using gradual approach (visit homepage first)...")
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10  # Add delay for Cloudflare challenge
        )

        # First visit homepage to establish session
        print("   Step 1: Visiting homepage...")
        home_response = scraper.get('https://www.noor-book.com/', timeout=30)
        print(f"   Homepage status: {home_response.status_code}")

        if home_response.status_code == 200:
            print("   ✅ Homepage accessible")

            # Wait a bit
            time.sleep(3)

            # Now try the target URL
            print("   Step 2: Visiting target page...")
            response = scraper.get(url, timeout=30)
            print(f"   Target status: {response.status_code}")

            if response.status_code == 200:
                print("   ✅ SUCCESS - Both pages accessible")
                return True
            else:
                print(f"   ❌ Target page failed: {response.status_code}")
        else:
            print(f"   ❌ Homepage failed: {home_response.status_code}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    return False


def main():
    """Main test function"""

    # Test the category URL
    category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

    success = test_with_cloudscraper(category_url)

    if not success:
        success = test_with_delays(category_url)

    print("\n" + "="*80)
    print("FINAL RESULTS & RECOMMENDATIONS:")
    print("="*80)

    if success:
        print("""
✅ SUCCESS! The cloudscraper method works!

Next steps:
1. Update noor_book_downloader.py to use cloudscraper instead of requests
2. Use the same browser configuration and headers
3. You can now proceed with scraping the book links
4. Remember to add delays between requests to be respectful

The updated downloader will:
- Bypass Cloudflare protection automatically
- Maintain cookies and session state
- Work just like a real browser
        """)
    else:
        print("""
❌ All methods failed. Possible reasons:

1. The website has very strict protection (likely Cloudflare with CAPTCHA)
2. Your IP might be blocked or rate-limited
3. The website might be down or restricted in your region

Alternative solutions:
1. Use Selenium with undetected-chromedriver (requires browser installation)
2. Use a VPN or proxy to change your IP
3. Try from a different network
4. Manual cookie extraction from browser
5. Contact the website administrators for API access

Would you like me to create a Selenium-based solution?
        """)

    print("="*80)


if __name__ == '__main__':
    main()
