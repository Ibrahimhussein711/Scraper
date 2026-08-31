# Polite Book Scraper

A small, polite web-scraping pipeline built for the **FlyRank Internship — Backend Track — Week 5 — Assignment A9**.

The scraper collects book data from the first three catalogue pages of **Books to Scrape**, discovers 60 unique book pages, extracts their details, normalizes and validates the data, handles failures without crashing, and produces a run report.

## 🎯 What This Project Does

The pipeline follows this flow:

```text
Classify
   ↓
Fetch
   ↓
Cache
   ↓
Discover
   ↓
Extract
   ↓
Normalize
   ↓
Validate
   ↓
Store
   ↓
Report
```

The scraper:

* Processes exactly the first **3 catalogue pages**
* Discovers **60 unique book URLs**
* Fetches individual book pages politely
* Caches downloaded HTML during development
* Extracts structured book information
* Normalizes prices into numeric GBP values
* Validates every record using Pydantic
* Keeps invalid records separate
* Survives broken pages without stopping the whole run
* Produces `books.json`, `errors.json`, and `run-report.json`

---

## 🛡️ Target Classification

### Target

**Books to Scrape**

https://books.toscrape.com/

Books to Scrape is a public practice sandbox specifically intended for learning and practicing web scraping.

### Scope

This project processes only:

* Catalogue page 1
* Catalogue page 2
* Catalogue page 3

These pages contain **60 books in total**.

### Robots.txt Check

I requested:

```text
https://books.toscrape.com/robots.txt
```

The server returned:

```text
404 Not Found
nginx/1.21.6
```

Therefore, there was **no robots.txt file found**.

A missing robots.txt file was not treated as permission to scrape other websites.

I will not reuse this code on another site without checking its rules and terms first.

---

## 🧰 Technology

This project uses the **Python lane**:

* Python 3.10+
* Requests
* Beautiful Soup
* Pydantic
* Built-in `json` module

No database, proxy, paid API, cloud service, browser automation, or credit card is required.

---

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/Ibrahimhussein711/Scraper.git
cd Scraper
```

Create a virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Run

Run the scraper with:

```bash
python src/main.py
```

The results are written to:

```text
output/
├── books.json
├── errors.json
└── run-report.json
```

---

## 📦 Record Schema

Each validated book record contains:

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/",
  "fetched_at": "2026-08-31T10:00:00+00:00"
}
```

### Field types

| Field               | Type            | Required |
| ------------------- | --------------- | -------- |
| `title`             | string          | Yes      |
| `product_url`       | absolute URL    | Yes      |
| `price_text`        | string          | Yes      |
| `price_gbp`         | float           | Yes      |
| `availability_text` | string          | Yes      |
| `rating_text`       | string          | Yes      |
| `description`       | string or null  | No       |
| `source_page`       | absolute URL    | Yes      |
| `fetched_at`        | datetime string | Yes      |

The original `price_text` is kept alongside the normalized numeric `price_gbp`.

---

## 🤝 Politeness Rules

The scraper follows several rules to avoid unnecessary load:

### Identifying User-Agent

Every real HTTP request includes:

```text
FlyRankInternship-A9/1.0
```

with a link to this repository.

### Timeout

Every request has a timeout so the scraper never waits forever.

### Delay

The scraper waits at least **500 ms** between real requests.

Cached pages do not require a delay because they never leave the local machine.

### Status Checking

The HTTP status code is checked before parsing the response.

Only:

```text
200 OK
```

is treated as a successful page fetch.

### Caching

Downloaded pages are saved locally in:

```text
cache/
```

During development, cached HTML is reused instead of repeatedly requesting the website.

The cache directory is excluded from Git.

### Retry

Timeouts and server-side `5xx` errors receive one retry.

`404` and `403` responses are not retried.

---

## 🧹 Normalization

Raw scraped values are not trusted directly.

For example:

```text
£51.77
```

becomes:

```text
51.77
```

The original raw value is still preserved as:

```text
price_text
```

while the normalized value is stored as:

```text
price_gbp
```

---

## ✅ Validation

Every normalized record is validated using **Pydantic** before being stored.

Valid records are written to:

```text
output/books.json
```

Invalid records are written to:

```text
output/errors.json
```

along with the reason for validation failure.

---

## 🔁 Idempotency

The scraper removes duplicate product URLs before processing them.

The final output therefore contains one record per canonical product URL.

Running the scraper again does not append duplicate records to `books.json`.

The expected result remains:

```text
60 records
```

---

## 💥 Failure Handling

Each book page is processed independently.

If one page fails, the scraper:

1. Logs the failed URL
2. Records the reason
3. Skips that page
4. Continues processing the remaining pages

A deliberately broken URL was used to verify this behavior.

The successful records still survive:

```text
valid_records = 60
failed_pages = 1
```

---

## 📊 Run Report

Every run creates:

```text
output/run-report.json
```

Example:

```json
{
  "started_at": "2026-08-31T11:00:00+00:00",
  "duration_seconds": 12.5,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

The exact duration and cache statistics depend on whether the scraper is running against a fresh cache or an existing one.

---

## 🌐 Why No Browser?

A browser is not required for the core assignment because the book information is already present in the HTML returned by the server.

Using browser automation would add unnecessary execution cost and complexity.

A normal HTTP request is sufficient.

---

## ⚠️ Limitation

The scraper intentionally handles only the first three catalogue pages.

It is designed for this practice sandbox and should not automatically be reused against another website.

Different websites may have different terms, robots rules, authentication requirements, APIs, or technical structures.

---

## 🧪 Ethics

This project follows a simple scraping principle:

> Collect only what you need, and respect the website you are accessing.

When an official API exists, it should be preferred over scraping.

This scraper does not attempt to:

* Bypass authentication
* Bypass paywalls
* Bypass access blocks
* Circumvent security controls
* Hammer the target with requests

---

## 📁 Project Structure

```text
Scraper/
│
├── src/
│   ├── main.py
│   ├── normalize.py
│   └── schema.py
│
├── output/
│   ├── books.json
│   ├── errors.json
│   └── run-report.json
│
├── cache/
│   └── ignored by Git
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📈 Expected Result

A successful clean run should produce:

```text
catalogue_pages = 3
discovered_urls = 60
valid_records = 60
invalid_records = 0
failed_pages = 1
```

The deliberately broken page is used only to test failure handling.

The actual scraped books remain:

```text
60
```

---

## 📜 Assignment

**FlyRank Internship · Backend Track · Week 5 · Assignment A9**

**The Polite Scraper**

The project demonstrates:

* Target classification
* Polite HTTP fetching
* HTML extraction
* URL normalization
* Data normalization
* Schema validation
* Failure handling
* Caching
* Idempotent output
* Run reporting
