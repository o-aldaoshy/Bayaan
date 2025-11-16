"""
Test the book extraction functionality without downloading
"""

import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

# Initialize cloudscraper
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

# Category URL
category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

print("="*80)
print(f"Testing book extraction from: {unquote(category_url)}")
print("="*80)

# Fetch the page
print("\n1. Fetching category page...")
response = scraper.get(category_url, timeout=30)
print(f"   Status: {response.status_code}")
print(f"   Content size: {len(response.text)} bytes")

if response.status_code == 200:
    print("   ✅ Successfully fetched page")

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find books
    print("\n2. Extracting book information...")
    book_containers = soup.find_all('div', class_='book-restult')
    print(f"   Found {len(book_containers)} books")

    # Display first 10 books
    print("\n3. First 10 books:")
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
    if book_containers:
        print("\n4. Testing book page fetch...")
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
    print(f"   ❌ Failed with status code: {response.status_code}")

print("\n" + "="*80)
