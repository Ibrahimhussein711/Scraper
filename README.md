# The Polite Scraper

## Target Classification

**Target:** Books to Scrape
**URL:** https://books.toscrape.com/

Books to Scrape is a public practice sandbox designed for learning and practicing web scraping.

### Scope

This scraper will process only the first three catalogue pages and discover the book pages linked from them. The expected result is 60 unique book URLs.

### Robots Check

I requested:

`https://books.toscrape.com/robots.txt`

The server returned:

`404 Not Found`

No robots.txt file was found.

A missing robots.txt file is not treated as permission to scrape other websites or ignore their rules. This project is limited to the public Books to Scrape practice sandbox and follows the requirements of this assignment.

### Data Collected

For each book, the scraper will collect:

* title
* product URL
* price text
* availability text
* rating text
* description
* source catalogue page
* fetched timestamp

The scraper will also normalize the price into a numeric `price_gbp` value and validate the final records before storing them.

### Responsible Scraping

I will not reuse this code on another site without checking its rules and terms first.
