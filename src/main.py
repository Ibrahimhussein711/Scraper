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


# ==========================================
# Run statistics
# ==========================================

stats = {
    "pages_fetched": 0,
    "cache_hits": 0
}


def fetch_page(
    url: str,
    cache_file: Path
) -> str:

    if cache_file.exists():

        print(
            f"CACHE HIT: {url}"
        )

        stats["cache_hits"] += 1

        return cache_file.read_text(
            encoding="utf-8"
        )

    print(
        f"FETCH: {url}"
    )

    max_attempts = 2

    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=10
            )

            status = response.status_code

            print(
                f"status={status} "
                f"attempt={attempt}"
            )

            if status == 200:

                response.encoding = "utf-8"

                html = response.text

                stats["pages_fetched"] += 1

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

            if status in (403, 404):

                raise RuntimeError(
                    f"Fetch failed: HTTP {status}"
                )

            if 500 <= status <= 599:

                if attempt < max_attempts:

                    print(
                        "Server error. "
                        "Retrying..."
                    )

                    time.sleep(1)

                    continue

                raise RuntimeError(
                    f"Fetch failed after retry: "
                    f"HTTP {status}"
                )

            raise RuntimeError(
                f"Fetch failed: HTTP {status}"
            )

        except requests.Timeout:

            print(
                f"TIMEOUT attempt={attempt}"
            )

            if attempt < max_attempts:

                print(
                    "Retrying after timeout..."
                )

                time.sleep(1)

                continue

            raise RuntimeError(
                "Fetch failed after timeout retry"
            )

        except requests.RequestException as error:

            raise RuntimeError(
                f"Request failed: {error}"
            )


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

    current_url = BASE_URL

    discovered_books = []

    catalogue_pages = 0

    while (
        current_url
        and catalogue_pages < 3
    ):

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

    # Remove duplicates
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

    product = soup.select_one(
        "div.product_main"
    )

    if product is None:

        raise ValueError(
            "Product area not found"
        )

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

    run_started_at = datetime.now(
        timezone.utc
    )

    run_start_time = time.perf_counter()

    # ==========================================
    # Discover
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
    # Failure test
    # ==========================================

    books.append(
        {
            "product_url": (
                "https://books.toscrape.com/"
                "catalogue/this-book-does-not-exist_999999/"
                "index.html"
            ),
            "source_page": BASE_URL
        }
    )

    print()
    print(
        "Added one deliberately broken URL "
        "for failure testing."
    )

    # ==========================================
    # Extract
    # ==========================================

    records = []

    failed_pages = []

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
            f"[{index}/{len(books)}] "
            f"Processing book"
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

            failed_pages.append(
                {
                    "url": product_url,
                    "reason": str(error)
                }
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

    print(
        f"failed_pages={len(failed_pages)}"
    )

    print("=" * 50)

    # ==========================================
    # Normalize + Validate
    # ==========================================

    valid_records = []

    invalid_records = []

    for record in records:

        try:

            normalized_record = normalize_record(
                record
            )

            validated_book = Book(
                **normalized_record
            )

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
    # Validation summary
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
    # Run report
    # ==========================================

    duration = (
        time.perf_counter()
        - run_start_time
    )

    run_report = {
        "started_at": run_started_at.isoformat(),
        "duration_seconds": round(
            duration,
            2
        ),
        "catalogue_pages": 3,
        "discovered_urls": len(books) - 1,
        "pages_fetched": stats[
            "pages_fetched"
        ],
        "cache_hits": stats[
            "cache_hits"
        ],
        "valid_records": len(
            valid_records
        ),
        "invalid_records": len(
            invalid_records
        ),
        "failed_pages": len(
            failed_pages
        )
    }

    report_file = (
        OUTPUT_DIR
        / "run-report.json"
    )

    with report_file.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            run_report,
            file,
            ensure_ascii=False,
            indent=2
        )

    # ==========================================
    # Final summary
    # ==========================================

    print()
    print("=" * 50)

    print("RUN REPORT")

    print("=" * 50)

    for key, value in run_report.items():

        print(
            f"{key}: {value}"
        )

    print()
    print(
        f"books.json: {len(valid_records)} records"
    )

    print(
        f"errors.json: {len(invalid_records)} records"
    )

    print(
        f"run-report.json: created"
    )


if __name__ == "__main__":
    main()