import requests
import time
import json
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from normalize import normalize_record
from schema import Book


BASE_URL = "https://books.toscrape.com/"

CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")

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

    response.encoding = "utf-8"

    html = response.text

    # Polite delay after a real request
    time.sleep(0.5)

    cache_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    cache_file.write_text(
        html,
        encoding="utf-8"
    )

    return html


def extract_book_urls(
    html: str,
    page_url: str
) -> list[str]:

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    book_urls = []

    books = soup.select(
        "article.product_pod"
    )

    for book in books:

        link = book.select_one(
            "h3 a"
        )

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


def discover_books():
    """Discover books from the first three catalogue pages."""

    current_url = BASE_URL

    discovered_books = []
    catalogue_pages = 0

    while current_url and catalogue_pages < 3:

        catalogue_pages += 1

        cache_file = (
            CACHE_DIR
            / f"catalogue-page-{catalogue_pages}.html"
        )

        html = fetch_page(
            current_url,
            cache_file
        )

        book_urls = extract_book_urls(
            html,
            current_url
        )

        print(
            f"page={catalogue_pages} "
            f"books={len(book_urls)}"
        )

        for url in book_urls:

            discovered_books.append(
                {
                    "product_url": url,
                    "source_page": current_url
                }
            )

        current_url = get_next_page(
            html,
            current_url
        )

    # Remove duplicate URLs
    unique_books = {}

    for book in discovered_books:

        unique_books[
            book["product_url"]
        ] = book["source_page"]

    return [
        {
            "product_url": url,
            "source_page": source_page
        }
        for url, source_page
        in unique_books.items()
    ]


def extract_book_record(
    html: str,
    product_url: str,
    source_page: str
) -> dict:

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Product area
    product = soup.select_one(
        "div.product_main"
    )

    if product is None:
        raise ValueError(
            "Product area not found"
        )

    # -------------------------
    # Title
    # -------------------------

    title_element = product.select_one(
        "h1"
    )

    title = (
        title_element.get_text(
            strip=True
        )
        if title_element
        else None
    )

    # -------------------------
    # Price
    # -------------------------

    price_element = product.select_one(
        "p.price_color"
    )

    price_text = (
        price_element.get_text(
            strip=True
        )
        if price_element
        else None
    )

    # -------------------------
    # Availability
    # -------------------------

    availability_element = product.select_one(
        "p.instock.availability"
    )

    availability_text = (
        availability_element.get_text(
            " ",
            strip=True
        )
        if availability_element
        else None
    )

    # -------------------------
    # Rating
    # -------------------------

    rating_element = product.select_one(
        "p.star-rating"
    )

    rating_text = None

    if rating_element:

        classes = rating_element.get(
            "class",
            []
        )

        if len(classes) > 1:
            rating_text = classes[-1]

    # -------------------------
    # Description
    # -------------------------

    description = None

    description_section = soup.select_one(
        "#product_description"
    )

    if description_section:

        description_element = (
            description_section.find_next_sibling(
                "p"
            )
        )

        if description_element:

            description = (
                description_element.get_text(
                    " ",
                    strip=True
                )
            )

    # -------------------------
    # Provenance
    # -------------------------

    fetched_at = datetime.now(
        timezone.utc
    ).isoformat()

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at
    }


def main():

    # ==========================================
    # Stage 2
    # Discover the 60 books
    # ==========================================

    books = discover_books()

    print()
    print(
        f"discovered={len(books)}"
    )

    print(
        f"unique_urls={len(books)}"
    )

    # ==========================================
    # Stage 3
    # Extract all book records
    # ==========================================

    records = []

    for index, book in enumerate(
        books,
        start=1
    ):

        product_url = book[
            "product_url"
        ]

        source_page = book[
            "source_page"
        ]

        print()
        print(
            f"[{index}/{len(books)}] Processing book"
        )

        detail_cache = (
            CACHE_DIR
            / f"book-{index}.html"
        )

        try:

            html = fetch_page(
                product_url,
                detail_cache
            )

            record = extract_book_record(
                html,
                product_url,
                source_page
            )

            records.append(
                record
            )

        except Exception as error:

            print(
                f"FAILED: {product_url}"
            )

            print(
                f"REASON: {error}"
            )

    # ==========================================
    # Stage 3 summary
    # ==========================================

    print()
    print("=" * 50)

    print(
        f"detail_pages={len(records)}"
    )

    print(
        f"raw_records={len(records)}"
    )

    print("=" * 50)

    # ==========================================
    # Stage 4
    # Normalize + Validate
    # ==========================================

    valid_records = []

    invalid_records = []

    for record in records:

        try:

            # Normalize raw data
            normalized_record = normalize_record(
                record
            )

            # Validate using Pydantic
            validated_book = Book(
                **normalized_record
            )

            # Convert Pydantic model to dictionary
            valid_records.append(
                validated_book.model_dump(
                    mode="json"
                )
            )

        except Exception as error:

            invalid_records.append(
                {
                    "record": record,
                    "reason": str(error)
                }
            )

    # ==========================================
    # Stage 4 validation summary
    # ==========================================

    print()
    print("=" * 50)
    print("STAGE 4 VALIDATION")
    print("=" * 50)

    print(
        f"valid_records={len(valid_records)}"
    )

    print(
        f"invalid_records={len(invalid_records)}"
    )

    # ==========================================
    # Save output
    # ==========================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    books_file = (
        OUTPUT_DIR / "books.json"
    )

    errors_file = (
        OUTPUT_DIR / "errors.json"
    )

    # Save valid records
    with books_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            valid_records,
            file,
            ensure_ascii=False,
            indent=2
        )

    # Save invalid records
    with errors_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            invalid_records,
            file,
            ensure_ascii=False,
            indent=2
        )

    # ==========================================
    # Output summary
    # ==========================================

    print()
    print("OUTPUT")
    print("-" * 50)

    print(
        f"books.json: {len(valid_records)} records"
    )

    print(
        f"errors.json: {len(invalid_records)} records"
    )

    # ==========================================
    # Show one validated record
    # ==========================================

    if valid_records:

        print()
        print(
            "NORMALIZED + VALIDATED RECORD"
        )

        print("-" * 50)

        for key, value in valid_records[0].items():

            print(
                f"{key}: {value}"
            )


if __name__ == "__main__":
    main()