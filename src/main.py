import requests
from pathlib import Path

URL = "https://books.toscrape.com/"

CACHE_FILE = Path("cache/catalogue-page-1.html")

HEADERS = {
    "User-Agent": (
        "FlyRankInternship-A9/1.0 "
        "(+https://github.com/Ibrahimhussein711/Scraper)"
    )
}


def fetch_page(url: str, cache_file: Path) -> str:
    # 1. Check cache first
    if cache_file.exists():
        print("CACHE HIT")

        return cache_file.read_text(
            encoding="utf-8"
        )

    # 2. No cache → make real request
    print("FETCH")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    # 3. Check status before using HTML
    if response.status_code != 200:
        raise RuntimeError(
            f"Fetch failed: HTTP {response.status_code}"
        )

    # 4. Create cache directory if needed
    cache_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 5. Save HTML
    cache_file.write_text(
        response.text,
        encoding="utf-8"
    )

    return response.text


html = fetch_page(URL, CACHE_FILE)

print(f"response_size={len(html)} bytes")