"""
Test the book extraction functionality with gradual approach
"""

import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import time

# Initialize cloudscraper with delay
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    },
    delay=10  # Add delay for Cloudflare challenge
)

scraper.headers.update({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
})

print("="*80)
print("Testing book extraction with gradual approach")
print("="*80)

# Step 1: Visit homepage first to establish session
print("\n1. Establishing session by visiting homepage...")
try:
    home_response = scraper.get('https://www.noor-book.com/', timeout=30)
    print(f"   Homepage status: {home_response.status_code}")
    if home_response.status_code == 200:
        print("   ✅ Successfully accessed homepage")
        print(f"   Cookies: {len(scraper.cookies)}")
    else:
        print(f"   ⚠️  Homepage returned: {home_response.status_code}")
except Exception as e:
    print(f"   ❌ Error accessing homepage: {e}")
    exit(1)

# Wait a bit
print("\n2. Waiting 5 seconds before accessing category page...")
time.sleep(5)

# Step 2: Now try the category page
category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

print(f"\n3. Fetching category page: {unquote(category_url)}")
try:
    response = scraper.get(category_url, timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Content size: {len(response.text)} bytes")

    if response.status_code == 200:
        print("   ✅ Successfully fetched category page")

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find books
        print("\n4. Extracting book information...")
        book_containers = soup.find_all('div', class_='book-restult')
        print(f"   Found {len(book_containers)} books")

        if book_containers:
            # Display first 10 books
            print("\n5. First 10 books:")
            print("-"*80)

            for i, container in enumerate(book_containers[:10], 1):
                link = container.find('a', class_='img-a')
                if link:
                    title = link.get('title', 'No title')
                    url = urljoin('https://www.noor-book.com', link.get('href', ''))
                    print(f"\n{i}. {title}")
                    print(f"   URL: {url}")

            print("\n" + "="*80)
            print("✅ Test successful! Book extraction is working.")
            print("="*80)

            # Test fetching one book page
            print("\n6. Testing book page fetch...")
            time.sleep(3)

            first_book = book_containers[0].find('a', class_='img-a')
            if first_book:
                book_url = urljoin('https://www.noor-book.com', first_book.get('href'))
                book_title = first_book.get('title')

                print(f"   Fetching: {book_title}")
                print(f"   URL: {book_url}")

                book_response = scraper.get(book_url, timeout=30)
                print(f"   Status: {book_response.status_code}")

                if book_response.status_code == 200:
                    print("   ✅ Successfully fetched book page")

                    # Save for inspection
                    with open('sample_book_page.html', 'w', encoding='utf-8') as f:
                        f.write(book_response.text)
                    print("   📄 Saved to: sample_book_page.html")

                    # Look for download links
                    book_soup = BeautifulSoup(book_response.text, 'html.parser')
                    all_links = book_soup.find_all('a', href=True)

                    download_links = []
                    for link in all_links:
                        link_text = link.get_text().lower()
                        href = link.get('href', '')

                        if any(keyword in link_text for keyword in ['تحميل', 'download', 'pdf', 'read']):
                            download_links.append({
                                'text': link.get_text().strip()[:50],
                                'href': href
                            })

                    if download_links:
                        print(f"\n   Found {len(download_links)} potential download links:")
                        for i, dl in enumerate(download_links[:5], 1):
                            print(f"   {i}. {dl['text']}")
                            print(f"      {dl['href']}")
                    else:
                        print("   ⚠️  No obvious download links found")
                        print("   💡 You may need to inspect sample_book_page.html manually")
                else:
                    print(f"   ❌ Book page returned: {book_response.status_code}")
        else:
            print("   ❌ No books found on page")

    elif response.status_code == 403:
        print("   ❌ Access forbidden (403)")
        print("   💡 The website might be rate limiting or blocking automated requests")

        # Save error page
        with open('error_403.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("   📄 Saved error page to: error_403.html")

    else:
        print(f"   ❌ Failed with status code: {response.status_code}")

except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*80)
