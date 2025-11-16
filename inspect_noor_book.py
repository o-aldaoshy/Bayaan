"""
Helper script to inspect noor-book.com structure
This will help you understand the HTML structure and update the selectors in noor_book_downloader.py
"""

import requests
from bs4 import BeautifulSoup

def inspect_website(url):
    """Fetch and display the HTML structure of a page"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ar,en;q=0.9',
    }

    try:
        print(f"Fetching: {url}\n")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        print("="*80)
        print("PAGE TITLE:")
        print("="*80)
        print(soup.title.string if soup.title else "No title found")

        print("\n" + "="*80)
        print("MAIN CONTENT STRUCTURE:")
        print("="*80)

        # Find potential book containers
        print("\n1. Looking for common book container patterns...")

        # Check for divs with 'book' in class name
        book_divs = soup.find_all('div', class_=lambda x: x and 'book' in x.lower())
        print(f"   - Divs with 'book' in class: {len(book_divs)}")
        if book_divs:
            print(f"     Example class: {book_divs[0].get('class')}")

        # Check for articles
        articles = soup.find_all('article')
        print(f"   - Articles found: {len(articles)}")
        if articles:
            print(f"     Example class: {articles[0].get('class')}")

        # Check for list items
        list_items = soup.find_all('li', class_=lambda x: x and ('book' in str(x).lower() or 'item' in str(x).lower()))
        print(f"   - List items with 'book' or 'item': {len(list_items)}")

        print("\n2. Looking for links that might be books...")
        all_links = soup.find_all('a', href=True)
        book_like_links = []

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().strip()

            # Look for Arabic word for book or 'book' in URL
            if '/كتاب/' in href or '/book/' in href or 'book-' in href:
                book_like_links.append({
                    'href': href,
                    'text': text[:50],
                    'class': link.get('class', [])
                })

        print(f"   - Found {len(book_like_links)} potential book links")
        if book_like_links:
            print("\n   First 5 examples:")
            for i, link in enumerate(book_like_links[:5], 1):
                print(f"   {i}. Text: {link['text']}")
                print(f"      URL: {link['href']}")
                print(f"      Class: {link['class']}\n")

        print("\n3. Looking for pagination...")
        pagination = soup.find_all('a', href=True, string=lambda x: x and any(word in str(x) for word in ['next', 'التالي', '»', '>', 'صفحة']))
        print(f"   - Potential pagination links: {len(pagination)}")
        if pagination:
            for pag in pagination[:3]:
                print(f"     Text: '{pag.get_text().strip()}' | URL: {pag.get('href')}")

        print("\n" + "="*80)
        print("FULL HTML (first 3000 characters):")
        print("="*80)
        print(response.text[:3000])

        # Save full HTML for manual inspection
        with open('noor_book_page_source.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\n✅ Full HTML saved to: noor_book_page_source.html")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # Test with the category URL
    category_url = 'https://www.noor-book.com/tag/%D8%A2%D8%AF%D8%A7%D8%A8-%D9%88%D8%A3%D8%AE%D9%84%D8%A7%D9%82-%D8%A5%D8%B3%D9%84%D8%A7%D9%85%D9%8A%D8%A9'

    print("INSPECTING CATEGORY PAGE")
    print("="*80)
    inspect_website(category_url)

    print("\n\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("""
1. Review the output above and the saved HTML file
2. Identify the correct CSS selectors for:
   - Book containers/cards
   - Book title links
   - Pagination links
3. Update noor_book_downloader.py with the correct selectors in:
   - extract_book_links() method
   - get_download_link() method
4. Test on a single book page to find download button selectors
    """)
