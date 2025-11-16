# Noor Book Downloader

A web scraper to download books from noor-book.com by category, similar to the arXiv paper downloader.

## Files

- `noor_book_downloader.py` - Main downloader script
- `inspect_noor_book.py` - Helper script to inspect website structure
- `requirements.txt` - Python dependencies

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Inspect the Website Structure

Since websites change frequently and noor-book.com appears to have bot protection, you need to first understand its structure:

```bash
python inspect_noor_book.py
```

This will:
- Fetch the category page
- Analyze the HTML structure
- Save the full HTML to `noor_book_page_source.html`
- Display potential book links and pagination patterns

### Step 2: Update Selectors

Open `noor_book_downloader.py` and update the following methods based on the inspection results:

#### In `extract_book_links()` method (around line 63):
```python
def extract_book_links(self, html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    book_links = []

    # UPDATE THESE SELECTORS based on actual HTML structure
    # Example: if books are in <div class="book-card">
    book_containers = soup.find_all('div', class_='book-card')
    for container in book_containers:
        link = container.find('a')
        if link and link.get('href'):
            book_links.append(urljoin(self.base_url, link['href']))

    return book_links
```

#### In `get_download_link()` method (around line 97):
```python
def get_download_link(self, book_page_url):
    # ...

    # UPDATE: Find the actual download button/link
    # Example: <a class="btn-download" href="...">تحميل</a>
    download_btn = soup.find('a', class_='btn-download')
    if download_btn:
        return title, urljoin(self.base_url, download_btn['href'])
```

### Step 3: Run the Downloader

```bash
python noor_book_downloader.py
```

## Configuration

Edit the `main()` function in `noor_book_downloader.py`:

```python
def main():
    downloader = NoorBookDownloader(download_dir='noor_books')

    category_url = 'YOUR_CATEGORY_URL_HERE'

    downloader.download_category(
        category_url=category_url,
        max_pages=10,        # Number of category pages to scrape
        max_books=50,        # Max books to download (None = all)
        delay=3              # Delay between requests (seconds)
    )
```

## Features

- ✅ Browser-like headers to avoid bot detection
- ✅ Automatic pagination handling
- ✅ Resume support (skips already downloaded books)
- ✅ Arabic filename support
- ✅ Progress logging
- ✅ Rate limiting / respectful delays
- ✅ Error handling and retries
- ✅ Organized by category in subdirectories

## Troubleshooting

### 403/503 Errors
- The website might be blocking automated requests
- Try increasing the `delay` parameter
- Try accessing from a different IP or using a VPN
- Some sites require you to solve a CAPTCHA first

### No Books Found
- The HTML selectors need to be updated
- Run `inspect_noor_book.py` to see the actual structure
- Manually visit a category page in your browser and inspect the HTML

### Download Links Not Working
- Some sites use JavaScript to generate download links
- You may need to use Selenium for JavaScript-heavy sites
- The download link might be behind a login or CAPTCHA

## Advanced: Using with Multiple Categories

```python
categories = [
    'https://www.noor-book.com/tag/category1',
    'https://www.noor-book.com/tag/category2',
    'https://www.noor-book.com/tag/category3',
]

downloader = NoorBookDownloader()

for category in categories:
    print(f"\n\nProcessing category: {category}")
    downloader.download_category(
        category_url=category,
        max_pages=5,
        max_books=20,
        delay=3
    )
```

## Legal Notice

⚠️ **Important**:
- Respect the website's terms of service
- Use reasonable delays between requests
- Don't overwhelm the server with too many concurrent requests
- Only download content you have the right to access
- Consider the copyright status of the books you download

## Comparison with ArXiv Downloader

| Feature | ArXiv | Noor-Book |
|---------|-------|-----------|
| API | Official API | Web scraping |
| Rate Limit | Well-defined | Manual delays |
| Pagination | URL parameters | Needs inspection |
| Download Links | Direct PDF | Needs extraction |
| Complexity | Simple | Requires customization |
