"""
Test accessing the English version of the page
"""

import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import time

# Initialize cloudscraper
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

scraper.headers.update({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
})

print("="*80)
print("Testing with English URL")
print("="*80)

# Try the English version of the URL
category_url_en = 'https://www.noor-book.com/en/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

print(f"\n1. Fetching English version: {unquote(category_url_en)}")
try:
    response = scraper.get(category_url_en, timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Content size: {len(response.text)} bytes")

    if response.status_code == 200:
        print("   ✅ Successfully fetched page")

        # Save the page
        with open('sample_page_english.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("   📄 Saved to: sample_page_english.html")

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find books
        print("\n2. Extracting book information...")
        book_containers = soup.find_all('div', class_='book-restult')
        print(f"   Found {len(book_containers)} books with class 'book-restult'")

        if book_containers:
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
            print("✅ SUCCESS! The English URL works!")
            print("="*80)
        else:
            print("\n3. No books found with 'book-restult' class")
            print("   Checking for alternative patterns...")

            # Check for other possible book containers
            possible_containers = [
                ('div', 'book-result'),
                ('div', 'book_result'),
                ('article', None),
                ('div', 'item'),
            ]

            for tag, class_name in possible_containers:
                if class_name:
                    containers = soup.find_all(tag, class_=class_name)
                    if containers:
                        print(f"   Found {len(containers)} elements with {tag}.{class_name}")
                else:
                    containers = soup.find_all(tag)
                    print(f"   Found {len(containers)} {tag} elements")

            # Look for any links that might be books
            print("\n   Searching for book-related links...")
            all_links = soup.find_all('a', href=True)
            book_links = [link for link in all_links if '/ebook-' in link.get('href', '') or '/كتاب/' in link.get('href', '')]
            print(f"   Found {len(book_links)} links that look like book links")

            if book_links:
                print("\n   First 5 book-like links:")
                for i, link in enumerate(book_links[:5], 1):
                    print(f"   {i}. {link.get('title', link.get_text().strip()[:50])}")
                    print(f"      {link.get('href')}")

    else:
        print(f"   ❌ Failed with status code: {response.status_code}")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
