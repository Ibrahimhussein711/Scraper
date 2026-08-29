import requests
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time


BASE_URL = "https://books.toscrape.com/"

CACHE_DIR = Path("cache")

HEADERS = {
    "User-Agent": (
        "FlyRankInternship-A9/1.0 "
        "(+https://github.com/Ibrahimhussein711/Scraper)"
    )
}


def fetch_page(url: str, cache_file: Path) -> str:
    """Fetch a page or read it from the local cache."""

    if cache_file.exists():
        print(f"CACHE HIT: {url}")

        return cache_file.read_text(
            encoding="utf-8"
        )

    print(f"FETCH: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed: HTTP {response.status_code}"
        )

    time.sleep(0.5)

    cache_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_file.write_text(
        response.text,
        encoding="utf-8"
    )

    return response.text


def extract_book_urls(
    html: str,
    page_url: str
) -> list[str]:
    """Extract all book URLs from one catalogue page."""

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    book_urls = []

    books = soup.select(
        "article.product_pod"
    )

    for book in books:
        link = book.select_one("h3 a")

        if link:
            href = link.get("href")

            if href:
                absolute_url = urljoin(
                    page_url,
                    href
                )

                book_urls.append(
                    absolute_url
                )

    return book_urls


def get_next_page(
    html: str,
    page_url: str
) -> str | None:
    """Find the catalogue's next page."""

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    next_link = soup.select_one(
        "li.next a"
    )

    if not next_link:
        return None

    href = next_link.get("href")

    if not href:
        return None

    return urljoin(
        page_url,
        href
    )


def main():
    current_url = BASE_URL

    all_book_urls = []
    catalogue_pages = 0

    while current_url:
        catalogue_pages += 1

        # Cache file for this catalogue page
        if current_url == BASE_URL:
            cache_file = CACHE_DIR / "catalogue-page-1.html"
        else:
            page_number = catalogue_pages
            cache_file = (
                CACHE_DIR
                / f"catalogue-page-{page_number}.html"
            )

        # Fetch page
        html = fetch_page(
            current_url,
            cache_file
        )

        # Extract books
        book_urls = extract_book_urls(
            html,
            current_url
        )

        print(
            f"page={catalogue_pages} "
            f"books={len(book_urls)}"
        )

        all_book_urls.extend(
            book_urls
        )

        # Stop after the first 3 catalogue pages
        if catalogue_pages == 3:
            break

        # Follow the site's own next link
        current_url = get_next_page(
            html,
            current_url
        )

        # Safety check
        if current_url is None:
            break

    # Remove duplicate URLs
    unique_book_urls = list(
        dict.fromkeys(all_book_urls)
    )

    print()
    print(
        f"catalogue_pages={catalogue_pages}"
    )
    print(
        f"discovered={len(all_book_urls)}"
    )
    print(
        f"unique_urls={len(unique_book_urls)}"
    )


if __name__ == "__main__":
    main()