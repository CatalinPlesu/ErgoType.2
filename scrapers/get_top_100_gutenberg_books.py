import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re

BASE_URL = "https://www.gutenberg.org"


def get_top_books_last30():
    url = f"{BASE_URL}/browse/scores/top#books-last30"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the "Last 30 days" header
    h2 = soup.find("h2", id="books-last30")
    if not h2:
        raise Exception("Could not find 'Last 30 days' section header")
    ol = h2.find_next_sibling("ol")
    if not ol:
        raise Exception(
            "Could not find ordered list after 'Last 30 days' header")
    books = []

    for li in ol.find_all("li"):
        a_tag = li.find("a")
        if a_tag and "href" in a_tag.attrs:
            href = a_tag["href"]
            match = re.search(r"/ebooks/(\d+)", href)
            if match:
                book_id = match.group(1)
                title = a_tag.text.strip()
                books.append((book_id, title))
    return books


def fetch_book_text(book_id: str):
    # Step 1: Get the book's main page
    book_page_url = f"{BASE_URL}/ebooks/{book_id}"
    page_response = requests.get(book_page_url)
    page_response.raise_for_status()
    page_soup = BeautifulSoup(page_response.text, "html.parser")

    # Step 2: Find the plain text UTF-8 download link
    # Look for the anchor tag with type 'text/plain' or text 'Plain Text UTF-8'
    download_link_tag = page_soup.select_one('a[type="text/plain"]')
    if not download_link_tag:
        download_link_tag = page_soup.find(
            'a', string=re.compile(r'Plain Text', re.I))

    if not download_link_tag or 'href' not in download_link_tag.attrs:
        raise Exception(
            f"Could not find Plain Text UTF-8 download link for book ID {book_id}")

    # Step 3: Construct the absolute URL for the text file
    txt_href = download_link_tag['href']
    if txt_href.startswith('//'):
        txt_url = 'https:' + txt_href
    elif txt_href.startswith('/'):
        txt_url = BASE_URL + txt_href
    else:
        txt_url = txt_href  # Assume it's already absolute or relative correctly

    # Step 4: Download the text
    response = requests.get(txt_url)
    response.raise_for_status()
    return response.text


def save_book(book_id: str, title: str, text: str, output_dir="data/gutenberg"):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    safe_title = re.sub(r"[^a-zA-Z0-9]+", "_", title)
    file_path = path / f"{book_id}_{safe_title}.txt"
    file_path.write_text(text, encoding="utf-8")
    print(f"Saved: {file_path}")


if __name__ == "__main__":
    top_books = get_top_books_last30()[:100]  # top 100
    for book_id, title in top_books:
        try:
            text = fetch_book_text(book_id)
            save_book(book_id, title, text)
        except Exception as e:
            print(f"Failed {book_id} - {title}: {e}")
