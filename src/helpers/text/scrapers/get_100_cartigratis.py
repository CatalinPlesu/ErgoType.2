import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import random
import re
from urllib.parse import urljoin
import pdfplumber # Import pdfplumber for PDF text extraction

# --- Configuration ---
BASE_URL = "https://cartigratis.com"
TOP100_BASE_URL = f"{BASE_URL}/categ/top-100"
MAX_BOOKS = 100
OUTPUT_DIR = Path("data/cartigratis")
SESSION = requests.Session()
# Add a User-Agent header to mimic a browser request
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# --- Helper Functions ---

def get_book_links_from_top100(start_url):
    """
    Iterates through the Top 100 pages and extracts links to individual book detail pages.
    Stops when MAX_BOOKS links are found.
    """
    book_links = []
    current_page = 1
    url = start_url

    while len(book_links) < MAX_BOOKS:
        print(f"Fetching Top 100 page: {url}")
        try:
            response = SESSION.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {url}: {e}")
            break # Stop if a page fails

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all book item divs
        # <div class="product-item"> ... </div>
        product_items = soup.find_all("div", class_="product-item")

        if not product_items:
            print(f"No product items found on page {url}. Might be the end or structure changed.")
            break # Likely no more items or structure is different

        for item in product_items:
            # Find the link to the book detail page within the item
            # Look for <a> with class 'product-item-name' or within 'product-item-image'
            detail_link_tag = item.find("a", class_="product-item-name")
            if not detail_link_tag:
                 detail_link_tag = item.find("div", class_="product-item-image").find("a")

            if detail_link_tag and detail_link_tag.get("href"):
                # Ensure the URL is absolute
                full_detail_url = urljoin(BASE_URL, detail_link_tag["href"].strip())
                book_links.append(full_detail_url)
                # print(f"Found book link: {full_detail_url}") # Optional debug print

                if len(book_links) >= MAX_BOOKS:
                    break # Stop collecting once we reach the limit

        if len(book_links) >= MAX_BOOKS:
            break # Stop pagination loop

        # Find the link to the next page
        # Check for a pagination element, e.g., <a> containing the next page number or 'Next'
        # This part might need adjustment based on the exact pagination HTML
        # A simple way: look for a link that contains '?page=' with an incremented number
        # Or find a specific 'next' button/link if available.
        # Let's try finding the next page link by looking for a pattern or the next number.

        # Example logic (adjust if pagination structure changes):
        # This looks for links that seem to be page numbers and picks the next one.
        # A more robust way is to parse the current page number and find the link for page+1.
        current_page_match = re.search(r'\?page=(\d+)', url)
        current_page_num = int(current_page_match.group(1)) if current_page_match else 1

        next_page_num = current_page_num + 1
        next_page_url = f"{TOP100_BASE_URL}?page={next_page_num}"

        # Check if the next page link actually exists on the current page
        # (e.g., by finding an <a> tag with that href)
        if soup.find("a", href=lambda href: href and f"?page={next_page_num}" in href):
            url = next_page_url
            print(f"Found link to next page: {next_page_num}")
        else:
            print("No link to next page found. Assuming end of list.")
            break # No more pages

        # Be polite with delays
        time.sleep(random.uniform(0.5, 1.0))

    print(f"Collected {len(book_links)} book detail page links.")
    return book_links[:MAX_BOOKS] # Ensure we don't exceed the limit


def get_pdf_download_url_from_detail_page(book_detail_url):
    """
    Fetches the book's detail page and extracts the direct PDF download URL.
    Looks for the button with class 'btn-add-to-cart' and 'data-href' attribute.
    """
    print(f"Parsing book detail page: {book_detail_url}")
    try:
        response = SESSION.get(book_detail_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching book detail page {book_detail_url}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the download button
    # <button data-href="..." class="btn btn-add-to-cart submit-add-to-cart-btn" ...>Descarca PDF</button>
    download_button = soup.find("button", class_="btn-add-to-cart", attrs={"data-href": True})

    if download_button:
        pdf_relative_url = download_button["data-href"].strip()
        # Ensure the URL is absolute
        full_pdf_url = urljoin(BASE_URL, pdf_relative_url)
        print(f"Found PDF URL: {full_pdf_url}")
        return full_pdf_url
    else:
        print(f"PDF download button not found on {book_detail_url}")
        # Debug: print a small part of the page structure
        # print(soup.prettify()[:2000])
        return None


def download_pdf(pdf_url, file_path: Path):
    """Downloads the PDF from the given URL to the specified path."""
    print(f"Starting download for: {pdf_url}")
    try:
        response = SESSION.get(pdf_url, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Successfully downloaded PDF to: {file_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF {pdf_url}: {e}")
        return False
    except IOError as e:
        print(f"Error saving PDF to {file_path}: {e}")
        return False

def pdf_to_text(pdf_path: Path, text_path: Path):
    """
    Converts a PDF file to text and saves it.
    Returns True if successful, False otherwise.
    """
    print(f"Converting PDF {pdf_path} to text...")
    try:
        text_content = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    # Add a newline after each page's text for basic separation
                    text_content += page_text + "\n"

        # Write the extracted text to the .txt file
        text_path.write_text(text_content, encoding='utf-8')
        print(f"Converted and saved text to: {text_path}")
        return True
    except Exception as e: # Catch general exceptions from pdfplumber or file I/O
        print(f"Error converting PDF {pdf_path} to text: {e}")
        return False
    # Note: The 'finally' block for deleting the PDF is now in the main execution loop
    # to ensure it only happens after a successful conversion attempt.

def extract_title_and_author(book_detail_url, soup=None):
    """
    Extracts the book title and author from the detail page URL or a provided soup object.
    If soup is not provided, it fetches the page.
    """
    if soup is None:
        try:
            response = SESSION.get(book_detail_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page for title/author {book_detail_url}: {e}")
            return "Unknown_Title", "Unknown_Author"

    # Extract title (from <a class="product-item-name"> or <title> tag if unique enough)
    title_tag = soup.find("a", class_="product-item-name")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown_Title"

    # Extract author (from <div class="product-item-author">)
    author_tag = soup.find("div", class_="product-item-author")
    author = author_tag.get_text(strip=True) if author_tag else "Unknown_Author"

    # Fallback if title wasn't found in the specific tag
    if title == "Unknown_Title":
         # Try getting it from the URL slug (last part before .html)
         path_parts = [p for p in book_detail_url.strip('/').split('/') if p]
         if path_parts:
             slug = path_parts[-1]
             if slug.endswith('.html'):
                 slug = slug[:-5] # Remove .html
             # Basic cleanup of slug to title
             title = slug.replace('-', ' ').title()

    return title, author

def sanitize_filename(name):
    """Removes or replaces invalid characters for filenames."""
    # Replace common invalid characters with underscores or nothing
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
    # Limit length and strip trailing spaces/dots (Windows limitation)
    sanitized = sanitized[:200].rstrip('. ')
    return sanitized if sanitized else "unnamed"

# --- Main Execution ---

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    successful_downloads = 0 # Count successful text conversions

    print("Starting CartiGratuit scraper for Top 100 (PDF -> TXT)...")
    book_detail_links = get_book_links_from_top100(TOP100_BASE_URL)

    if not book_detail_links:
        print("No book links found. Exiting.")
        exit(1)

    for detail_url in book_detail_links:
        if successful_downloads >= MAX_BOOKS:
            print(f"Reached the limit of {MAX_BOOKS} successful conversions.")
            break

        print("-" * 30)
        # Get title and author for filename
        title, author = extract_title_and_author(detail_url)
        print(f"Processing: '{title}' by {author}")

        # Create safe filenames
        safe_title = sanitize_filename(title)
        safe_author = sanitize_filename(author)
        pdf_filename = f"{safe_title}_{safe_author}.pdf"
        text_filename = f"{safe_title}_{safe_author}.txt"
        pdf_path = OUTPUT_DIR / pdf_filename
        text_path = OUTPUT_DIR / text_filename

        # Skip if text file already exists
        if text_path.exists():
            print(f"Skipping {title} (Text file already exists)")
            successful_downloads += 1 # Count existing text as successful
            continue

        # 1. Get the direct PDF download URL from the detail page
        pdf_url = get_pdf_download_url_from_detail_page(detail_url)
        if not pdf_url:
            print(f"Skipping {title} (PDF URL not found)")
            continue

        # 2. Download the PDF
        if not download_pdf(pdf_url, pdf_path):
            print(f"Failed to download PDF for {title}. Skipping...")
            pdf_path.unlink(missing_ok=True) # Clean up failed download
            continue # Move to the next book

        # 3. Convert PDF to Text
        conversion_success = pdf_to_text(pdf_path, text_path)

        # 4. Clean up the PDF file regardless of conversion success
        # (If conversion failed, we still don't need the PDF anymore)
        try:
            pdf_path.unlink() # Delete the PDF file
            print(f"Deleted temporary PDF file: {pdf_path}")
        except FileNotFoundError:
            # File might have been deleted by an error handler in download_pdf
            pass
        except OSError as e:
            print(f"Warning: Could not delete PDF file {pdf_path}: {e}")

        # 5. Update success counter and report
        if conversion_success:
            successful_downloads += 1
            print(f"Successfully processed: {title} ({successful_downloads}/{MAX_BOOKS})")
        else:
            # If conversion failed, clean up the potentially empty/failed text file
            try:
                text_path.unlink(missing_ok=True)
                print(f"Cleaned up failed text file: {text_path}")
            except OSError as e:
                print(f"Warning: Could not clean up failed text file {text_path}: {e}")
            print(f"Failed to convert PDF for {title}.")

        # Be polite: Add a small delay between requests
        time.sleep(random.uniform(1.0, 2.5))

    print("-" * 30)
    print(f"Scraping and conversion finished. Successfully processed {successful_downloads} books (PDF downloaded and converted to TXT).")
