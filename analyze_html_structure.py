"""
Analyze the HTML structure of noor-book.com to find proper selectors
"""

from bs4 import BeautifulSoup

# Read the saved HTML
with open('sample_page_cloudscraper.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("="*80)
print("ANALYZING HTML STRUCTURE")
print("="*80)

# Find all book containers
books = soup.find_all('div', class_='book-restult')
print(f"\n1. Found {len(books)} books on this page")

# Analyze first few books
print("\n2. Analyzing first 5 books:")
print("-"*80)

for i, book in enumerate(books[:5], 1):
    # Find the link
    link = book.find('a', class_='img-a')
    if link:
        url = link.get('href', '')
        title = link.get('title', 'No title')
        print(f"\nBook {i}:")
        print(f"  Title: {title}")
        print(f"  URL: {url}")
        print(f"  Full URL: https://www.noor-book.com{url}")

# Check pagination
print("\n" + "="*80)
print("3. Checking for pagination:")
print("-"*80)

# Look for pagination elements
pagination = soup.find('ul', class_='pagination')
if pagination:
    print("✅ Pagination found!")
    page_links = pagination.find_all('a')
    print(f"  Number of page links: {len(page_links)}")
    for link in page_links[:5]:
        print(f"  Page link: {link.get('href', 'No href')}")
else:
    print("❌ No pagination found (might use infinite scroll)")

# Look for "load more" or infinite scroll indicators
load_more = soup.find('button', class_='load-more') or soup.find('div', class_='load-more')
if load_more:
    print("✅ Load more button found")

# Check for infinite scroll indicators
scroll_container = soup.find('div', class_='book_results')
if scroll_container:
    print("✅ Found book_results container (might use AJAX/infinite scroll)")

print("\n" + "="*80)
print("4. SUMMARY - Selectors to use:")
print("-"*80)
print("""
Book container: div.book-restult
Book link: a.img-a (inside book container)
Book title: title attribute of the link
Book URL: href attribute of the link (relative URL, needs base URL)

Example code:
    books = soup.find_all('div', class_='book-restult')
    for book in books:
        link = book.find('a', class_='img-a')
        if link:
            title = link.get('title')
            url = urljoin(base_url, link.get('href'))
""")

print("="*80)
