import time
import random
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import os
import csv
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from arabic_reshaper import reshape
from bidi.algorithm import get_display


# =====================================================
# UTILITIES
# =====================================================

def random_delay(min_sec=1, max_sec=3):
    """Random delay to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))


def human_like_mouse_move(driver, element):
    """Move mouse in a human-like way"""
    try:
        action = ActionChains(driver)
        action.move_to_element(element).perform()
        random_delay(0.2, 0.5)
    except:
        pass


def sanitize_filename(title):
    """Clean filename and include Arabic characters"""
    valid_chars = []
    for c in title:
        if c.isalnum() or c in ' ._-' or '\u0600' <= c <= '\u06FF':
            valid_chars.append(c)
    return ''.join(valid_chars).strip()[:100]


def format_arabic_text(text):
    """Format Arabic text for PDF display"""
    try:
        reshaped_text = reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except:
        return text


# =====================================================
# PDF GENERATION
# =====================================================

def create_pdf_from_content(content_dict, output_path, title="Document"):
    """
    Create a PDF from extracted content

    Args:
        content_dict: Dictionary with structure {
            'title': str,
            'author': str,
            'sections': [
                {'heading': str, 'paragraphs': [str, str, ...]},
                ...
            ]
        }
        output_path: Path to save the PDF
        title: Document title
    """
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Register Arabic font (you may need to provide path to Arabic TTF font)
        # Uncomment and modify if you have an Arabic font file:
        # try:
        #     pdfmetrics.registerFont(TTFont('Arabic', 'path/to/arabic-font.ttf'))
        # except:
        #     pass

        # Create styles
        styles = getSampleStyleSheet()

        # Title style (centered, large)
        title_style = ParagraphStyle(
            'ArabicTitle',
            parent=styles['Title'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30,
        )

        # Heading style (right-aligned for Arabic)
        heading_style = ParagraphStyle(
            'ArabicHeading',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_RIGHT,
            spaceAfter=12,
        )

        # Body text style (right-aligned for Arabic)
        body_style = ParagraphStyle(
            'ArabicBody',
            parent=styles['BodyText'],
            fontSize=12,
            alignment=TA_RIGHT,
            spaceAfter=12,
            leading=18,
        )

        # Build PDF content
        story = []

        # Add title
        if 'title' in content_dict:
            title_text = format_arabic_text(content_dict['title'])
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 0.2 * inch))

        # Add author
        if 'author' in content_dict:
            author_text = format_arabic_text(f"المؤلف: {content_dict['author']}")
            story.append(Paragraph(author_text, body_style))
            story.append(Spacer(1, 0.3 * inch))

        # Add sections
        if 'sections' in content_dict:
            for section in content_dict['sections']:
                # Add section heading
                if 'heading' in section:
                    heading_text = format_arabic_text(section['heading'])
                    story.append(Paragraph(heading_text, heading_style))
                    story.append(Spacer(1, 0.1 * inch))

                # Add paragraphs
                if 'paragraphs' in section:
                    for para in section['paragraphs']:
                        if para.strip():
                            para_text = format_arabic_text(para)
                            story.append(Paragraph(para_text, body_style))

                story.append(Spacer(1, 0.2 * inch))

        # Build PDF
        doc.build(story)
        print(f"✅ PDF created: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return False


# =====================================================
# SELENIUM SCRAPER CLASS
# =====================================================

class ShamelaScraper:
    def __init__(self, headless=False, output_dir="shamela_pdfs"):
        """Initialize Selenium driver"""
        print("🌐 Launching Chrome browser...")

        options = uc.ChromeOptions()

        if not headless:
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--headless=new")

        options.add_argument("--disable-blink-features=AutomationControlled")

        # Random window size
        window_width = random.randint(1200, 1920)
        window_height = random.randint(800, 1080)
        options.add_argument(f"--window-size={window_width},{window_height}")

        # Set output directory
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        self.driver = uc.Chrome(options=options, use_subprocess=True)
        self.driver.set_page_load_timeout(60)
        self.wait = WebDriverWait(self.driver, 30)


    def login(self, email, password, login_url):
        """Login to website (customize based on target site)"""
        print("🔐 Logging in...")

        try:
            self.driver.get(login_url)
            random_delay(3, 5)

            # TODO: Customize login logic based on target website
            # Example:
            # email_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='email']")
            # email_input.send_keys(email)
            # password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            # password_input.send_keys(password)
            # login_button = self.driver.find_element(By.CSS_SELECTOR, ".submit-button")
            # login_button.click()

            print("✅ Login successful!")
            return True

        except Exception as e:
            print(f"❌ Login error: {e}")
            raise


    def extract_text_content(self, page_url):
        """
        Extract text content from a page

        Returns:
            Dictionary with structure {
                'title': str,
                'author': str,
                'sections': [...]
            }
        """
        print(f"📖 Extracting content from: {page_url}")

        try:
            self.driver.get(page_url)
            random_delay(3, 5)

            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            content = {
                'title': '',
                'author': '',
                'sections': []
            }

            # TODO: Customize extraction based on target website
            # Example:
            # title_elem = soup.find("h1", class_="title")
            # if title_elem:
            #     content['title'] = title_elem.text.strip()

            # author_elem = soup.find("span", class_="author")
            # if author_elem:
            #     content['author'] = author_elem.text.strip()

            # sections = soup.find_all("div", class_="section")
            # for section in sections:
            #     heading = section.find("h2")
            #     paragraphs = section.find_all("p")
            #
            #     content['sections'].append({
            #         'heading': heading.text.strip() if heading else '',
            #         'paragraphs': [p.text.strip() for p in paragraphs]
            #     })

            return content

        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return None


    def close(self):
        """Close browser"""
        try:
            self.driver.quit()
        except:
            pass


# =====================================================
# MAIN PROCESSING FUNCTION
# =====================================================

def process_pages(scraper, page_urls, output_dir="shamela_pdfs", metadata_file="shamela_metadata.csv"):
    """
    Process multiple pages and create PDFs

    Args:
        scraper: ShamelaScraper instance
        page_urls: List of URLs to process
        output_dir: Directory to save PDFs
        metadata_file: CSV file to track processed pages
    """
    os.makedirs(output_dir, exist_ok=True)

    csv_exists = os.path.exists(metadata_file)
    processed_count = 0
    failed_count = 0

    # Initialize CSV
    if not csv_exists:
        with open(metadata_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["page_number", "title", "author", "url", "pdf_path", "status"])

    total_pages = len(page_urls)

    for idx, page_url in enumerate(page_urls, 1):
        print(f"\n[{idx}/{total_pages}] 🔎 {page_url}")

        try:
            random_delay(2, 4)

            # Extract content
            content = scraper.extract_text_content(page_url)

            if not content:
                print("❌ No content extracted")
                failed_count += 1
                continue

            # Create safe filename
            safe_title = sanitize_filename(content.get('title', f"page_{idx}"))
            pdf_filename = f"{idx:04d}_{safe_title}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)

            # Create PDF
            if create_pdf_from_content(content, pdf_path, title=content.get('title', '')):
                processed_count += 1

                # Save to CSV
                with open(metadata_file, "a", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        idx,
                        content.get('title', ''),
                        content.get('author', ''),
                        page_url,
                        pdf_path,
                        "success"
                    ])

                print(f"✅ Page {idx} complete: {pdf_filename}")
            else:
                failed_count += 1

        except Exception as e:
            print(f"❌ Error processing page {idx}: {e}")
            failed_count += 1

    print(f"\n{'='*60}")
    print(f"🎉 Complete!")
    print(f"✅ Processed: {processed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Metadata saved to: {metadata_file}")
    print(f"{'='*60}")


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    # ========== CONFIGURATION ==========
    # TODO: Customize these settings for your target website

    # Login credentials (if needed)
    EMAIL = "your_email@example.com"
    PASSWORD = "your_password"
    LOGIN_URL = "https://example.com/login"

    # Pages to process (URLs)
    PAGE_URLS = [
        "https://example.com/page1",
        "https://example.com/page2",
        # Add more URLs...
    ]

    # Or use a function to get URLs from a category/list
    # PAGE_URLS = get_page_urls_from_category(scraper, category_url)

    OUTPUT_DIR = "shamela_pdfs"
    METADATA_FILE = "shamela_metadata.csv"
    # ===================================

    print("="*60)
    print("🚀 SHAMELA TEXT SCRAPER & PDF GENERATOR")
    print("📄 Extracts text content and creates PDFs")
    print("="*60)

    scraper = None

    try:
        # Initialize scraper
        scraper = ShamelaScraper(headless=False, output_dir=OUTPUT_DIR)

        # Login (if needed)
        # print("\n📌 STEP 1: Logging in...")
        # scraper.login(EMAIL, PASSWORD, LOGIN_URL)

        # Process pages
        print("\n📌 STEP 1: Processing pages...")
        process_pages(
            scraper,
            PAGE_URLS,
            output_dir=OUTPUT_DIR,
            metadata_file=METADATA_FILE
        )

        print("\n✨ All done!")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        if scraper:
            print("\n🔒 Closing browser...")
            scraper.close()
