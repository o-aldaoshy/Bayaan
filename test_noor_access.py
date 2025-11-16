"""
Quick test to check if noor-book.com is accessible and what method works
"""

import requests
from urllib.parse import unquote

def test_access(url):
    """Test different methods to access the website"""

    print("="*80)
    print(f"Testing access to: {unquote(url)}")
    print("="*80)

    # Test 1: Simple request
    print("\n[Test 1] Simple GET request...")
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} bytes")
        if response.status_code == 200:
            print("   ✅ SUCCESS")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Test 2: With browser headers
    print("\n[Test 2] With browser-like headers...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} bytes")

        # Check for common bot detection patterns
        if 'cloudflare' in response.text.lower():
            print("   ⚠️  Cloudflare detected")
        if 'captcha' in response.text.lower():
            print("   ⚠️  CAPTCHA detected")
        if 'checking your browser' in response.text.lower():
            print("   ⚠️  Browser check detected")

        if response.status_code == 200:
            print("   ✅ SUCCESS")

            # Try to find some content
            if 'كتاب' in response.text or 'book' in response.text.lower():
                print("   ✅ Found book-related content")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Test 3: With session (maintains cookies)
    print("\n[Test 3] Using session with cookies...")
    try:
        session = requests.Session()
        session.headers.update(headers)

        # First request to get cookies
        response = session.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Cookies received: {len(session.cookies)}")

        if response.status_code == 200:
            print("   ✅ SUCCESS")

            # Save a sample to file
            with open('sample_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text[:5000])  # First 5000 chars
            print("   📄 Saved sample to: sample_page.html")
        else:
            print(f"   ❌ FAILED: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    print("\n" + "="*80)
    print("RECOMMENDATIONS:")
    print("="*80)
    print("""
If all tests failed:
- The site might be down or blocking your IP
- Try accessing it manually in a browser first
- Consider using a VPN or different network
- You might need Selenium with a real browser

If Test 2 or 3 succeeded:
- Use the method that worked in noor_book_downloader.py
- The current implementation should work
- Proceed with inspecting the HTML structure

If CAPTCHA or Cloudflare detected:
- You may need to use Selenium with undetected-chromedriver
- Or manually solve CAPTCHA and extract cookies
- This is more complex and may require additional setup
    """)


if __name__ == '__main__':
    # Test the category URL
    url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

    test_access(url)

    # Also test the main site
    print("\n\n")
    test_access('https://www.noor-book.com/')
