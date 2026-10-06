## 1. Objective

You will build a Python program that collects data from two websites, cleans it, checks it, removes duplicates, and saves one tidy CSV file plus a summary report. Nothing needs to be built beyond that: one command (`python main.py`) runs the whole job.

### 1.1 Project goal

The two sites are practice sites made for learning scraping: Books to Scrape (about 1,000 books over 50 pages) and Quotes to Scrape (100 quotes over 10 pages). Your program must:

- Fetch every page of both sites by following the "next" link, not by hard-coding page numbers.
- Convert two very different data shapes into one common table layout.
- Clean messy values (extra spaces, currency symbols, ratings written as words).
- Validate each record and reject the bad ones without crashing.
- Detect duplicates even when spacing or capitalization differs.
- Write `final_dataset.csv`, `summary_report.json`, and a log file.

### 1.2 The problem it solves

Real web data is rarely tidy. This project practices the three problems you will meet in almost every data job:

- **Different structures.** A book has a price and a star rating. A quote has an author and tags. They cannot share one table until you agree on common columns.
- **Messy values.** A price arrives as `£51.77`, a rating as the word `Three`, and text can contain stray spaces or non-breaking spaces. Numbers must be real numbers before anyone can sort or sum them.
- **Unreliable networks.** Requests can time out, pages can return errors, and an HTML element can be missing. A good scraper logs the problem and keeps going.

The design that solves this is a small **ETL pipeline** (Extract, Transform, Load). Each stage does one job and knows nothing about the others, so each can be tested and fixed on its own.

```
Scrape (both sites) -> Clean -> Validate -> Deduplicate -> Consolidate -> Save files
```

### 1.3 Expected final outcome

After `python main.py` finishes, these three files exist:

| File | What it contains |
| --- | --- |
| `output/final_dataset.csv` | One row per unique, valid record from both sites, with the same columns for every row |
| `output/summary_report.json` | Counts per source: scraped, cleaned, rejected (with reasons), duplicates, final total, and run time |
| `logs/scraper.log` | A time-stamped record of every request, page change, warning, and error |

A good result means: rows from both sources appear in the CSV, the JSON counts add up to the CSV row count, and the program survived a failed page without stopping.

## 2. Technical Requirements

You need Python 3.10 to 3.12, three small libraries, and an internet connection. No paid tools, accounts, or API keys are required.

### 2.1 System prerequisites

- **Operating system:** Windows, macOS, or Linux.
- **Python:** version 3.10, 3.11, or 3.12. Check with `python --version`.
- **Editor:** VS Code, PyCharm, or any text editor.
- **Browser:** Chrome or Firefox, for inspecting page structure with Developer Tools (F12).
- **Terminal basics:** you should be able to open a terminal and run `cd` and `python` commands.
- **Virtual environment (`venv`):** a private folder of packages for this project, so it does not clash with other Python projects.

### 2.2 Libraries to install

| Library | Version | Why you need it |
| --- | --- | --- |
| `requests` | 2.31 or newer | Downloads the HTML of each page |
| `beautifulsoup4` | 4.12 or newer | Lets you search the HTML for the pieces you want |
| `lxml` | 5.0 or newer | A fast engine that BeautifulSoup uses to read HTML |
| `pytest` (optional) | 8.0 or newer | Runs your unit tests |
| `pydantic` (optional) | 2.0 or newer | Optional data checking; plain Python dictionaries also work |

Pin the versions you actually used in `requirements.txt` so anyone can reproduce your setup.

### 2.3 Standard library modules (already installed with Python)

| Module | Used for |
| --- | --- |
| `csv` | Writing the final CSV file |
| `json` | Writing the summary report |
| `logging` | Writing the log file |
| `re` | Pulling numbers out of text such as `£51.77` |
| `urllib.parse` | Turning relative links into full URLs |
| `time` | Pausing between requests and measuring run time |
| `pathlib` | Creating folders and file paths that work on every OS |
| `hashlib` | Creating short fingerprints for duplicate detection |
| `datetime` | Creating the `scraped_at` timestamp |

### 2.4 Rules to follow

- Scrape only the two practice sites. Do not try to bypass logins, CAPTCHAs, or other protections.
- Pause about 0.5 seconds between requests so you do not overload the server.
- Never put passwords or API keys in your code or submission.
- You may use AI tools, but you must understand and be able to explain every line you submit.

## 3. Step-by-Step Implementation Guide

Build the project in the order below. Each stage lists what to do, why it matters, and what you should see when it works. Test each stage before starting the next.

### Stage 0: Set up your workspace

**What to do:**

1. Create the project folder and the subfolders from Section 4.
2. Create and activate a virtual environment, then install the libraries.
3. Save the libraries to `requirements.txt`.

```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install requests beautifulsoup4 lxml pytest
pip freeze > requirements.txt
```

**Why:** A virtual environment keeps your packages separate, and `requirements.txt` lets a reviewer recreate your exact setup.

**Expected result:** your terminal prompt shows `(venv)` and `pip list` shows the libraries.

### Stage 1: Explore the websites before coding

**What to do:** Open each site in your browser, right-click an item, and choose **Inspect**. Write down which HTML tag holds each piece of data. Also scroll to the bottom and inspect the "Next" button.

**Why:** A scraper is only as good as your understanding of the page. Ten minutes of inspection saves hours of debugging.

**What you should find:**

| Item | Books to Scrape | Quotes to Scrape |
| --- | --- | --- |
| One record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a` (full title is in the `title` attribute, because the visible text is cut off with `...`) | `span.text` (wrapped in curly quotes) |
| Price | `p.price_color` (e.g. `£51.77`) | none |
| Rating | class on `p.star-rating` (e.g. `Three`) | none |
| Author | none | `small.author` |
| Tags | none | `a.tag` (zero or more) |
| Link | `h3 > a[href]` (relative path) | `a[href^="/author/"]` (author page) |
| Next page | `li.next > a` | `li.next > a` |

Write these observations in your README. The assignment asks for them.

### Stage 2: Design one common data model

**What to do:** Decide the columns that both sources will share. Use `None` where a field does not apply.

**Why:** A CSV needs the same columns on every row. Inventing fake values (for example, giving quotes a price of 0) would corrupt the data, so leave those cells empty.

| Column | Books | Quotes |
| --- | --- | --- |
| `source` | Books to Scrape | Quotes to Scrape |
| `source_url` | Book detail page URL | Page URL where the quote appeared, or the author page URL (pick one and document it) |
| `name_or_title` | Book title | Quote text |
| `category` | From the book detail page, or empty | Empty (or a fixed label such as `Quotes`, documented) |
| `price` | Number, e.g. 51.77 | Empty |
| `rating` | Integer 1 to 5 | Empty |
| `author` | Empty | Author name |
| `tags` | Empty | `tag1;tag2` |
| `description` | From the book detail page, or empty | Empty |
| `scraped_at` | UTC timestamp | UTC timestamp |

**Expected result:** a written table (like this one) and a Python `dict` or `dataclass` that matches it.

**Beginner tip:** The book listing page does not show category or description. Either visit each book's detail page (about 1,000 extra requests, so keep the pause between requests) or leave those fields empty and explain the limitation in the README. Do not guess values.

### Stage 3: Build a shared HTTP helper

**What to do:** Write one function or class that creates a `requests.Session` with a User-Agent header, a timeout, and automatic retries for temporary errors (HTTP 429, 500, 502, 503, 504).

**Why:** Both scrapers need the same networking behavior. Writing it once avoids copy-paste bugs, and retries mean a brief network hiccup does not ruin the run.

**Expected result:** calling your helper on `https://books.toscrape.com/` returns status code 200. See snippet 5.1.

### Stage 4: Build one scraper per source with dynamic pagination

**What to do:** Create `BooksScraper` and `QuotesScraper`. Each one:

1. Starts at the home page.
2. Downloads the page and parses the HTML.
3. Loops over every record on the page and builds a raw dictionary (text exactly as found).
4. Looks for `li.next > a`. If found, converts its relative link to a full URL with `urljoin` and repeats. If not found, stops.

**Why:** Following the "next" link means the scraper keeps working if the site gains or loses pages. A hard-coded `range(1, 51)` would break silently.

**Handle failures:**

- Wrap each record's parsing in `try/except` so one bad record is logged and skipped.
- If a page fails after retries, log the error and stop that source (or skip the page if you can find the next link another way). The other source must still run.
- Use `.select_one()` and check for `None` before reading a field, because a missing element returns `None`.

**Expected result:** Books returns about 1,000 raw records over 50 pages; Quotes returns 100 records over 10 pages. The log shows each page URL. See snippets 5.2 and 5.3.

### Stage 5: Write cleaning functions

**What to do:** In `processing/cleaning.py`, write small, separate functions that each do one thing:

- `clean_text`: remove extra spaces, tabs, newlines, and non-breaking spaces (`\xa0`).
- `strip_quotes`: remove the curly quotation marks around quote text.
- `clean_price`: turn `£51.77` into `51.77`.
- `clean_rating`: turn `Three` into `3`.
- `clean_tags`: lowercase, sort, and join tags with `;`.
- `normalize_url`: make sure the URL is complete and starts with `http://` or `https://`.

**Why:** Keeping cleaning separate from scraping means you can test it with a plain string and no internet. If the website layout changes, you fix the scraper and the cleaning code stays untouched.

**Beginner tip:** Set `response.encoding = "utf-8"` before reading the page text. Otherwise `£` can appear as `Â£`.

**Expected result:** `clean_price("£51.77")` returns `51.77`, and `clean_text("  Hello \n World ")` returns `"Hello World"`. See snippet 5.4.

### Stage 6: Add validation

**What to do:** Write a function that checks one cleaned record and returns a list of problems. An empty list means the record is valid.

| Rule | Check |
| --- | --- |
| Known source | `source` is one of the two allowed names |
| Has a name | `name_or_title` is not empty |
| Valid URL | `source_url` starts with `http://` or `https://` |
| Valid price | If present, it is a number greater than or equal to 0 |
| Valid rating | If present, it is an integer from 1 to 5 |

**Why:** Validation stops bad data from reaching the final file. Returning the reasons (instead of just True or False) lets your summary report show why records were rejected.

**Expected result:** valid records move on; invalid ones are counted by reason and logged as warnings, and the program keeps running. See snippet 5.5.

### Stage 7: Implement duplicate detection

**What to do:** Build a **fingerprint** for each record: take the identifying fields, lowercase them, remove punctuation, collapse spaces, and hash the result. Keep a `set` of fingerprints already seen. If a new record's fingerprint is already in the set, it is a duplicate.

**Which fields identify a record:**

- Books: source + title.
- Quotes: source + author + the first 50 characters of the quote text.

Use the same rule in your code and your README. Mismatched rules are a common mistake.

**Why:** Exact comparison treats `"Example Book Title"`, `" Example Book Title "`, and `"EXAMPLE BOOK TITLE"` as three different records. The fingerprint treats them as one.

**Decide: remove or flag?** Either drop duplicates or keep them with an `is_duplicate` column. Explain your choice in the README.

**Important:** Both practice sites already contain unique items, so your real run will probably find **0 duplicates**. To prove your logic works, write a unit test with deliberately duplicated sample records. See snippet 5.6.

### Stage 8: Consolidate and write the outputs

**What to do:**

1. Join the valid, non-duplicate records from both sources into one list.
2. Write it to `output/final_dataset.csv` with `csv.DictWriter` (use `encoding="utf-8"` and a fixed column order).
3. Write `output/summary_report.json` with the metrics below.

**Metrics to include:**

- Raw records collected per source.
- Records after cleaning, per source.
- Records rejected, with a count for each reason.
- Duplicates found.
- Final record count.
- Start time, end time, and duration in seconds.

**Why:** The summary lets a reviewer check your work without reading code. The numbers must reconcile: raw minus rejected minus duplicates equals final.

**Expected result:** about 1,100 rows in the CSV (if nothing was rejected) and a JSON file whose final count matches the row count. See snippet 5.7.

### Stage 9: Add logging and the main entry point

**What to do:**

1. Configure `logging` once in `main.py` to write to both the console and `logs/scraper.log`.
2. Log an INFO line for each page, a WARNING for each rejected record, and an ERROR for each failed request.
3. In `main.py`, call the stages in order: scrape, clean, validate, deduplicate, write files. Wrap each source in its own `try/except` so one failure does not stop the other.

**Why:** When something goes wrong, the log is the only way to find out what happened and when.

**Expected result:** running `python main.py` prints progress and creates all three output files.

### Stage 10: Test and verify from a clean environment

**What to do:**

1. Write a few unit tests for cleaning, validation, and deduplication (these need no internet).
2. Delete your `venv`, create a fresh one, install from `requirements.txt`, and run `python main.py`.
3. Open the CSV and check that both sources appear, prices are numbers, and ratings are between 1 and 5.
4. Compare the JSON counts with the CSV row count.

**Why:** "It works on my machine" is not enough. A fresh run proves a reviewer can reproduce your result.

### Stage 11: Write the documentation

Create two required files:

- **README.md:** Python version, setup, how to run, how pagination works, the data model, and your cleaning, validation, deduplication, and error-handling approaches. Also list assumptions and known limitations.
- **AI_USAGE.md:** which AI tools you used, what for, a few real prompts, what you changed after reviewing the AI's output, any mistakes you found in its suggestions, and how you tested the final code.

**Be ready to answer in an interview:** Why Requests + BeautifulSoup? How does pagination work? How are failed requests handled? How does duplicate detection work? Which parts did AI write, and what did you fix? Requests + BeautifulSoup is a good answer to the first one, because both sites are plain server-rendered HTML, so a browser tool like Selenium would only add overhead.

## 4. Project Structure

The project is split into three layers: scrapers (talk to websites), processing (clean, validate, deduplicate), and `main.py` (connects everything). Each layer can change without breaking the others.

```
scraping_assignment/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py      # shared HTTP session, retries, timeout, delay
│   ├── books_scraper.py     # Books to Scrape selectors + pagination
│   └── quotes_scraper.py    # Quotes to Scrape selectors + pagination
├── processing/
│   ├── __init__.py
│   ├── cleaning.py          # text, price, rating, tag, URL cleaning
│   ├── validation.py        # record checks, returns a list of problems
│   └── deduplication.py     # fingerprint + duplicate detection
├── tests/
│   ├── test_cleaning.py
│   ├── test_validation.py
│   └── test_deduplication.py
├── output/
│   ├── final_dataset.csv
│   └── summary_report.json
├── logs/
│   └── scraper.log
├── main.py
├── requirements.txt
├── README.md
└── AI_USAGE.md
```

| Path | Purpose |
| --- | --- |
| `scrapers/base_scraper.py` | Holds the networking code (session, headers, retries, timeout, pause between requests) so the two scrapers do not repeat it |
| `scrapers/books_scraper.py`, `quotes_scraper.py` | Everything specific to one website: its selectors, its pagination, and the raw dictionaries it returns. Nothing else lives here |
| `processing/cleaning.py` | Small pure functions that take a value and return a cleaned value. No internet, no files |
| `processing/validation.py` | Applies the rules from Stage 6 and returns the reasons a record failed |
| `processing/deduplication.py` | Builds fingerprints and separates unique records from duplicates |
| `tests/` | Unit tests that run without internet. Proves your cleaning, validation, and deduplication work |
| `output/` | Generated results. Created by the program, so create the folder in code if it is missing (`Path.mkdir(exist_ok=True)`) |
| `logs/` | Generated log file, created the same way |
| `main.py` | The only file you run. It calls scraping, cleaning, validation, deduplication, and writing, in that order |
| `requirements.txt` | Exact library versions so the project can be reproduced |
| `README.md` | How to set up, run, and understand the project |
| `AI_USAGE.md` | Honest record of how AI helped, and what you verified or fixed |

**Why the `__init__.py` files?** An empty `__init__.py` marks a folder as a Python package, which lets you write `from processing.cleaning import clean_price`.

**Rule of thumb:** if a function touches the internet, it belongs in `scrapers/`. If it only transforms data, it belongs in `processing/`. If it connects the stages, it belongs in `main.py`.

## 5. Example Code Snippets

These short examples show the key ideas. They are not a complete solution: you must write, test, and understand the rest yourself.

### 5.1 A resilient HTTP session (Stage 3)

This creates one session that retries temporary failures with growing delays (1s, 2s, 4s).

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "ScrapingAssignment/1.0 (learning project)"})
    retries = Retry(total=3, backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

### 5.2 Dynamic pagination loop (Stage 4)

The loop keeps following the "next" link until there is none. It never needs to know the page count.

```python
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests, time, logging

logger = logging.getLogger(__name__)

def scrape_all_pages(session, start_url):
    url, page, records = start_url, 1, []
    while url:
        logger.info("Page %d: %s", page, url)
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()          # raises on 404, 500, etc.
            response.encoding = "utf-8"          # keeps the £ symbol correct
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            break                                # stop this source, keep the program alive

        soup = BeautifulSoup(response.text, "lxml")
        records.extend(parse_page(soup, url))    # your source-specific function

        next_link = soup.select_one("li.next > a")
        url = urljoin(url, next_link["href"]) if next_link else None
        page += 1
        time.sleep(0.5)                          # be polite to the server
    return records
```

### 5.3 Safely extracting one field (Stage 4)

A missing element returns `None`. Checking first prevents a crash.

```python
def parse_book(article, page_url):
    link = article.select_one("h3 > a")
    price = article.select_one("p.price_color")
    rating = article.select_one("p.star-rating")
    return {
        "title": link.get("title") if link else None,
        "href": urljoin(page_url, link["href"]) if link and link.get("href") else None,
        "price_raw": price.get_text() if price else None,
        "rating_raw": " ".join(rating.get("class", [])) if rating else None,
    }
```

BeautifulSoup returns the `class` attribute as a list (for example `['star-rating', 'Three']`), which is why the example joins it into a string first.

### 5.4 Cleaning functions (Stage 5)

```python
import re

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

def clean_text(value):
    if value is None:
        return None
    text = " ".join(value.replace("\xa0", " ").split())   # collapse all whitespace
    return text or None                                    # empty string becomes None

def clean_price(raw):
    if not raw:
        return None
    match = re.search(r"\d+(?:\.\d+)?", raw.replace(",", ""))
    return float(match.group()) if match else None

def clean_rating(raw):
    for word in (raw or "").lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None
```

Quick check you can run in a Python shell:

```python
clean_price("£51.77")                 # 51.77
clean_rating("star-rating Three")     # 3
clean_text("  Hello \n  World ")     # 'Hello World'
```

### 5.5 Validation that returns reasons (Stage 6)

```python
VALID_SOURCES = {"Books to Scrape", "Quotes to Scrape"}

def validate_record(rec):
    problems = []
    if rec.get("source") not in VALID_SOURCES:
        problems.append("unknown_source")
    if not rec.get("name_or_title"):
        problems.append("missing_name")
    if not str(rec.get("source_url") or "").startswith(("http://", "https://")):
        problems.append("invalid_url")
    price = rec.get("price")
    if price is not None and (not isinstance(price, (int, float)) or price < 0):
        problems.append("invalid_price")
    rating = rec.get("rating")
    if rating is not None and rating not in (1, 2, 3, 4, 5):
        problems.append("invalid_rating")
    return problems          # empty list = valid
```

### 5.6 Duplicate fingerprint and a test (Stage 7)

```python
import hashlib, re

def make_fingerprint(rec):
    if rec["source"] == "Books to Scrape":
        key = f'{rec["source"]} {rec["name_or_title"]}'
    else:                                           # quotes
        key = f'{rec["source"]} {rec["author"]} {rec["name_or_title"][:50]}'
    key = re.sub(r"[^\w\s]", "", key.lower())      # lowercase, drop punctuation
    key = " ".join(key.split())                     # collapse spaces
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def find_duplicates(records):
    seen, unique, dupes = set(), [], []
    for rec in records:
        fp = make_fingerprint(rec)
        (dupes if fp in seen else unique).append(rec)
        seen.add(fp)
    return unique, dupes
```

A test with deliberately duplicated data proves the logic works, even though the real sites contain no duplicates:

```python
def test_duplicates_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "Example Book Title"},
        {**base, "name_or_title": "  Example Book Title "},
        {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
    ]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1 and len(dupes) == 2
```

Note: the helper strips punctuation and collapses spaces, so the second record (with leading and trailing spaces) matches the first. If your cleaning step already trims whitespace, the test still passes.

### 5.7 Writing the summary report (Stage 8)

```python

```

## 1. Objective

You will build a Python program that collects data from two websites, cleans it, checks it, removes duplicates, and saves one tidy CSV file plus a summary report. Nothing needs to be built beyond that: one command (`python main.py`) runs the whole job.

### 1.1 Project goal

The two sites are practice sites made for learning scraping: Books to Scrape (about 1,000 books over 50 pages) and Quotes to Scrape (100 quotes over 10 pages). Your program must:

- Fetch every page of both sites by following the "next" link, not by hard-coding page numbers.
- Convert two very different data shapes into one common table layout.
- Clean messy values (extra spaces, currency symbols, ratings written as words).
- Validate each record and reject the bad ones without crashing.
- Detect duplicates even when spacing or capitalization differs.
- Write `final_dataset.csv`, `summary_report.json`, and a log file.

### 1.2 The problem it solves

Real web data is rarely tidy. This project practices the three problems you will meet in almost every data job:

- **Different structures.** A book has a price and a star rating. A quote has an author and tags. They cannot share one table until you agree on common columns.
- **Messy values.** A price arrives as `£51.77`, a rating as the word `Three`, and text can contain stray spaces or non-breaking spaces. Numbers must be real numbers before anyone can sort or sum them.
- **Unreliable networks.** Requests can time out, pages can return errors, and an HTML element can be missing. A good scraper logs the problem and keeps going.

The design that solves this is a small **ETL pipeline** (Extract, Transform, Load). Each stage does one job and knows nothing about the others, so each can be tested and fixed on its own.

```
Scrape (both sites) -> Clean -> Validate -> Deduplicate -> Consolidate -> Save files
```

### 1.3 Expected final outcome

After `python main.py` finishes, these three files exist:

| File | What it contains |
| --- | --- |
| `output/final_dataset.csv` | One row per unique, valid record from both sites, with the same columns for every row |
| `output/summary_report.json` | Counts per source: scraped, cleaned, rejected (with reasons), duplicates, final total, and run time |
| `logs/scraper.log` | A time-stamped record of every request, page change, warning, and error |

A good result means: rows from both sources appear in the CSV, the JSON counts add up to the CSV row count, and the program survived a failed page without stopping.

## 2. Technical Requirements

You need Python 3.10 to 3.12, three small libraries, and an internet connection. No paid tools, accounts, or API keys are required.

### 2.1 System prerequisites

- **Operating system:** Windows, macOS, or Linux.
- **Python:** version 3.10, 3.11, or 3.12. Check with `python --version`.
- **Editor:** VS Code, PyCharm, or any text editor.
- **Browser:** Chrome or Firefox, for inspecting page structure with Developer Tools (F12).
- **Terminal basics:** you should be able to open a terminal and run `cd` and `python` commands.
- **Virtual environment (`venv`):** a private folder of packages for this project, so it does not clash with other Python projects.

### 2.2 Libraries to install

| Library | Version | Why you need it |
| --- | --- | --- |
| `requests` | 2.31 or newer | Downloads the HTML of each page |
| `beautifulsoup4` | 4.12 or newer | Lets you search the HTML for the pieces you want |
| `lxml` | 5.0 or newer | A fast engine that BeautifulSoup uses to read HTML |
| `pytest` (optional) | 8.0 or newer | Runs your unit tests |
| `pydantic` (optional) | 2.0 or newer | Optional data checking; plain Python dictionaries also work |

Pin the versions you actually used in `requirements.txt` so anyone can reproduce your setup.

### 2.3 Standard library modules (already installed with Python)

| Module | Used for |
| --- | --- |
| `csv` | Writing the final CSV file |
| `json` | Writing the summary report |
| `logging` | Writing the log file |
| `re` | Pulling numbers out of text such as `£51.77` |
| `urllib.parse` | Turning relative links into full URLs |
| `time` | Pausing between requests and measuring run time |
| `pathlib` | Creating folders and file paths that work on every OS |
| `hashlib` | Creating short fingerprints for duplicate detection |
| `datetime` | Creating the `scraped_at` timestamp |

### 2.4 Rules to follow

- Scrape only the two practice sites. Do not try to bypass logins, CAPTCHAs, or other protections.
- Pause about 0.5 seconds between requests so you do not overload the server.
- Never put passwords or API keys in your code or submission.
- You may use AI tools, but you must understand and be able to explain every line you submit.

## 3. Step-by-Step Implementation Guide

Build the project in the order below. Each stage lists what to do, why it matters, and what you should see when it works. Test each stage before starting the next.

### Stage 0: Set up your workspace

**What to do:**

1. Create the project folder and the subfolders from Section 4.
2. Create and activate a virtual environment, then install the libraries.
3. Save the libraries to `requirements.txt`.

```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install requests beautifulsoup4 lxml pytest
pip freeze > requirements.txt
```

**Why:** A virtual environment keeps your packages separate, and `requirements.txt` lets a reviewer recreate your exact setup.

**Expected result:** your terminal prompt shows `(venv)` and `pip list` shows the libraries.

### Stage 1: Explore the websites before coding

**What to do:** Open each site in your browser, right-click an item, and choose **Inspect**. Write down which HTML tag holds each piece of data. Also scroll to the bottom and inspect the "Next" button.

**Why:** A scraper is only as good as your understanding of the page. Ten minutes of inspection saves hours of debugging.

**What you should find:**

| Item | Books to Scrape | Quotes to Scrape |
| --- | --- | --- |
| One record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a` (full title is in the `title` attribute, because the visible text is cut off with `...`) | `span.text` (wrapped in curly quotes) |
| Price | `p.price_color` (e.g. `£51.77`) | none |
| Rating | class on `p.star-rating` (e.g. `Three`) | none |
| Author | none | `small.author` |
| Tags | none | `a.tag` (zero or more) |
| Link | `h3 > a[href]` (relative path) | `a[href^="/author/"]` (author page) |
| Next page | `li.next > a` | `li.next > a` |

Write these observations in your README. The assignment asks for them.

### Stage 2: Design one common data model

**What to do:** Decide the columns that both sources will share. Use `None` where a field does not apply.

**Why:** A CSV needs the same columns on every row. Inventing fake values (for example, giving quotes a price of 0) would corrupt the data, so leave those cells empty.

| Column | Books | Quotes |
| --- | --- | --- |
| `source` | Books to Scrape | Quotes to Scrape |
| `source_url` | Book detail page URL | Page URL where the quote appeared, or the author page URL (pick one and document it) |
| `name_or_title` | Book title | Quote text |
| `category` | From the book detail page, or empty | Empty (or a fixed label such as `Quotes`, documented) |
| `price` | Number, e.g. 51.77 | Empty |
| `rating` | Integer 1 to 5 | Empty |
| `author` | Empty | Author name |
| `tags` | Empty | `tag1;tag2` |
| `description` | From the book detail page, or empty | Empty |
| `scraped_at` | UTC timestamp | UTC timestamp |

**Expected result:** a written table (like this one) and a Python `dict` or `dataclass` that matches it.

**Beginner tip:** The book listing page does not show category or description. Either visit each book's detail page (about 1,000 extra requests, so keep the pause between requests) or leave those fields empty and explain the limitation in the README. Do not guess values.

### Stage 3: Build a shared HTTP helper

**What to do:** Write one function or class that creates a `requests.Session` with a User-Agent header, a timeout, and automatic retries for temporary errors (HTTP 429, 500, 502, 503, 504).

**Why:** Both scrapers need the same networking behavior. Writing it once avoids copy-paste bugs, and retries mean a brief network hiccup does not ruin the run.

**Expected result:** calling your helper on `https://books.toscrape.com/` returns status code 200. See snippet 5.1.

### Stage 4: Build one scraper per source with dynamic pagination

**What to do:** Create `BooksScraper` and `QuotesScraper`. Each one:

1. Starts at the home page.
2. Downloads the page and parses the HTML.
3. Loops over every record on the page and builds a raw dictionary (text exactly as found).
4. Looks for `li.next > a`. If found, converts its relative link to a full URL with `urljoin` and repeats. If not found, stops.

**Why:** Following the "next" link means the scraper keeps working if the site gains or loses pages. A hard-coded `range(1, 51)` would break silently.

**Handle failures:**

- Wrap each record's parsing in `try/except` so one bad record is logged and skipped.
- If a page fails after retries, log the error and stop that source (or skip the page if you can find the next link another way). The other source must still run.
- Use `.select_one()` and check for `None` before reading a field, because a missing element returns `None`.

**Expected result:** Books returns about 1,000 raw records over 50 pages; Quotes returns 100 records over 10 pages. The log shows each page URL. See snippets 5.2 and 5.3.

### Stage 5: Write cleaning functions

**What to do:** In `processing/cleaning.py`, write small, separate functions that each do one thing:

- `clean_text`: remove extra spaces, tabs, newlines, and non-breaking spaces (`\xa0`).
- `strip_quotes`: remove the curly quotation marks around quote text.
- `clean_price`: turn `£51.77` into `51.77`.
- `clean_rating`: turn `Three` into `3`.
- `clean_tags`: lowercase, sort, and join tags with `;`.
- `normalize_url`: make sure the URL is complete and starts with `http://` or `https://`.

**Why:** Keeping cleaning separate from scraping means you can test it with a plain string and no internet. If the website layout changes, you fix the scraper and the cleaning code stays untouched.

**Beginner tip:** Set `response.encoding = "utf-8"` before reading the page text. 

**Expected result:** `clean_price("£51.77")` returns `51.77`, and `clean_text("  Hello \n World ")` returns `"Hello World"`. See snippet 5.4.

### Stage 6: Add validation

**What to do:** Write a function that checks one cleaned record and returns a list of problems. An empty list means the record is valid.

| Rule | Check |
| --- | --- |
| Known source | `source` is one of the two allowed names |
| Has a name | `name_or_title` is not empty |
| Valid URL | `source_url` starts with `http://` or `https://` |
| Valid price | If present, it is a number greater than or equal to 0 |
| Valid rating | If present, it is an integer from 1 to 5 |

**Why:** Validation stops bad data from reaching the final file. Returning the reasons (instead of just True or False) lets your summary report show why records were rejected.

**Expected result:** valid records move on; invalid ones are counted by reason and logged as warnings, and the program keeps running. See snippet 5.5.

### Stage 7: Implement duplicate detection

**What to do:** Build a **fingerprint** for each record: take the identifying fields, lowercase them, remove punctuation, collapse spaces, and hash the result. Keep a `set` of fingerprints already seen. If a new record's fingerprint is already in the set, it is a duplicate.

**Which fields identify a record:**

- Books: source + title.
- Quotes: source + author + the first 50 characters of the quote text.

Use the same rule in your code and your README. Mismatched rules are a common mistake.

**Why:** Exact comparison treats `"Example Book Title"`, `" Example Book Title "`, and `"EXAMPLE BOOK TITLE"` as three different records. The fingerprint treats them as one.

**Decide: remove or flag?** Either drop duplicates or keep them with an `is_duplicate` column. Explain your choice in the README.

**Important:** Both practice sites already contain unique items, so your real run will probably find **0 duplicates**. To prove your logic works, write a unit test with deliberately duplicated sample records. See snippet 5.6.

### Stage 8: Consolidate and write the outputs

**What to do:**

1. Join the valid, non-duplicate records from both sources into one list.
2. Write it to `output/final_dataset.csv` with `csv.DictWriter` (use `encoding="utf-8"` and a fixed column order).
3. Write `output/summary_report.json` with the metrics below.

**Metrics to include:**

- Raw records collected per source.
- Records after cleaning, per source.
- Records rejected, with a count for each reason.
- Duplicates found.
- Final record count.
- Start time, end time, and duration in seconds.

**Why:** The summary lets a reviewer check your work without reading code. The numbers must reconcile: raw minus rejected minus duplicates equals final.

**Expected result:** about 1,100 rows in the CSV (if nothing was rejected) and a JSON file whose final count matches the row count. See snippet 5.7.

### Stage 9: Add logging and the main entry point

**What to do:**

1. Configure `logging` once in `main.py` to write to both the console and `logs/scraper.log`.
2. Log an INFO line for each page, a WARNING for each rejected record, and an ERROR for each failed request.
3. In `main.py`, call the stages in order: scrape, clean, validate, deduplicate, write files. Wrap each source in its own `try/except` so one failure does not stop the other.

**Why:** When something goes wrong, the log is the only way to find out what happened and when.

**Expected result:** running `python main.py` prints progress and creates all three output files.

### Stage 10: Test and verify from a clean environment

**What to do:**

1. Write a few unit tests for cleaning, validation, and deduplication (these need no internet).
2. Delete your `venv`, create a fresh one, install from `requirements.txt`, and run `python main.py`.
3. Open the CSV and check that both sources appear, prices are numbers, and ratings are between 1 and 5.
4. Compare the JSON counts with the CSV row count.

**Why:** "It works on my machine" is not enough. A fresh run proves a reviewer can reproduce your result.

### Stage 11: Write the documentation

Create two required files:

- **README.md:** Python version, setup, how to run, how pagination works, the data model, and your cleaning, validation, deduplication, and error-handling approaches. Also list assumptions and known limitations.
- **AI_USAGE.md:** which AI tools you used, what for, a few real prompts, what you changed after reviewing the AI's output, any mistakes you found in its suggestions, and how you tested the final code.

**Be ready to answer in an interview:** Why Requests + BeautifulSoup? How does pagination work? How are failed requests handled? How does duplicate detection work? Which parts did AI write, and what did you fix? Requests + BeautifulSoup is a good answer to the first one, because both sites are plain server-rendered HTML, so a browser tool like Selenium would only add overhead.

## 4. Project Structure

The project is split into three layers: scrapers (talk to websites), processing (clean, validate, deduplicate), and `main.py` (connects everything). Each layer can change without breaking the others.

```
scraping_assignment/
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py      # shared HTTP session, retries, timeout, delay
│   ├── books_scraper.py     # Books to Scrape selectors + pagination
│   └── quotes_scraper.py    # Quotes to Scrape selectors + pagination
├── processing/
│   ├── __init__.py
│   ├── cleaning.py          # text, price, rating, tag, URL cleaning
│   ├── validation.py        # record checks, returns a list of problems
│   └── deduplication.py     # fingerprint + duplicate detection
├── tests/
│   ├── test_cleaning.py
│   ├── test_validation.py
│   └── test_deduplication.py
├── output/
│   ├── final_dataset.csv
│   └── summary_report.json
├── logs/
│   └── scraper.log
├── main.py
├── requirements.txt
├── README.md
└── AI_USAGE.md
```

| Path | Purpose |
| --- | --- |
| `scrapers/base_scraper.py` | Holds the networking code (session, headers, retries, timeout, pause between requests) so the two scrapers do not repeat it |
| `scrapers/books_scraper.py`, `quotes_scraper.py` | Everything specific to one website: its selectors, its pagination, and the raw dictionaries it returns. Nothing else lives here |
| `processing/cleaning.py` | Small pure functions that take a value and return a cleaned value. No internet, no files |
| `processing/validation.py` | Applies the rules from Stage 6 and returns the reasons a record failed |
| `processing/deduplication.py` | Builds fingerprints and separates unique records from duplicates |
| `tests/` | Unit tests that run without internet. Proves your cleaning, validation, and deduplication work |
| `output/` | Generated results. Created by the program, so create the folder in code if it is missing (`Path.mkdir(exist_ok=True)`) |
| `logs/` | Generated log file, created the same way |
| `main.py` | The only file you run. It calls scraping, cleaning, validation, deduplication, and writing, in that order |
| `requirements.txt` | Exact library versions so the project can be reproduced |
| `README.md` | How to set up, run, and understand the project |
| `AI_USAGE.md` | Honest record of how AI helped, and what you verified or fixed |

**Why the `__init__.py` files?** An empty `__init__.py` marks a folder as a Python package, which lets you write `from processing.cleaning import clean_price`.

**Rule of thumb:** if a function touches the internet, it belongs in `scrapers/`. If it only transforms data, it belongs in `processing/`. If it connects the stages, it belongs in `main.py`.

## 5. Example Code Snippets

These short examples show the key ideas. They are not a complete solution: you must write, test, and understand the rest yourself.

### 5.1 A resilient HTTP session (Stage 3)

This creates one session that retries temporary failures with growing delays (1s, 2s, 4s).

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "ScrapingAssignment/1.0 (learning project)"})
    retries = Retry(total=3, backoff_factor=1.0,
                    status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
```

### 5.2 Dynamic pagination loop (Stage 4)

The loop keeps following the "next" link until there is none. It never needs to know the page count.

```python
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests, time, logging

logger = logging.getLogger(__name__)

def scrape_all_pages(session, start_url):
    url, page, records = start_url, 1, []
    while url:
        logger.info("Page %d: %s", page, url)
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()          # raises on 404, 500, etc.
            response.encoding = "utf-8"          # keeps the £ symbol correct
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            break                                # stop this source, keep the program alive

        soup = BeautifulSoup(response.text, "lxml")
        records.extend(parse_page(soup, url))    # your source-specific function

        next_link = soup.select_one("li.next > a")
        url = urljoin(url, next_link["href"]) if next_link else None
        page += 1
        time.sleep(0.5)                          # be polite to the server
    return records
```

### 5.3 Safely extracting one field (Stage 4)

A missing element returns `None`. Checking first prevents a crash.

```python
def parse_book(article, page_url):
    link = article.select_one("h3 > a")
    price = article.select_one("p.price_color")
    rating = article.select_one("p.star-rating")
    return {
        "title": link.get("title") if link else None,
        "href": urljoin(page_url, link["href"]) if link and link.get("href") else None,
        "price_raw": price.get_text() if price else None,
        "rating_raw": " ".join(rating.get("class", [])) if rating else None,
    }
```

BeautifulSoup returns the `class` attribute as a list (for example `['star-rating', 'Three']`), which is why the example joins it into a string first.

### 5.4 Cleaning functions (Stage 5)

```python
import re

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}

def clean_text(value):
    if value is None:
        return None
    text = " ".join(value.replace("\xa0", " ").split())   # collapse all whitespace
    return text or None                                    # empty string becomes None

def clean_price(raw):
    if not raw:
        return None
    match = re.search(r"\d+(?:\.\d+)?", raw.replace(",", ""))
    return float(match.group()) if match else None

def clean_rating(raw):
    for word in (raw or "").lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None
```

Quick check you can run in a Python shell:

```python
clean_price("£51.77")                 # 51.77
clean_rating("star-rating Three")     # 3
clean_text("  Hello \n  World ")     # 'Hello World'
```

### 5.5 Validation that returns reasons (Stage 6)

```python
VALID_SOURCES = {"Books to Scrape", "Quotes to Scrape"}

def validate_record(rec):
    problems = []
    if rec.get("source") not in VALID_SOURCES:
        problems.append("unknown_source")
    if not rec.get("name_or_title"):
        problems.append("missing_name")
    if not str(rec.get("source_url") or "").startswith(("http://", "https://")):
        problems.append("invalid_url")
    price = rec.get("price")
    if price is not None and (not isinstance(price, (int, float)) or price < 0):
        problems.append("invalid_price")
    rating = rec.get("rating")
    if rating is not None and rating not in (1, 2, 3, 4, 5):
        problems.append("invalid_rating")
    return problems          # empty list = valid
```

### 5.6 Duplicate fingerprint and a test (Stage 7)

```python
import hashlib, re

def make_fingerprint(rec):
    if rec["source"] == "Books to Scrape":
        key = f'{rec["source"]} {rec["name_or_title"]}'
    else:                                           # quotes
        key = f'{rec["source"]} {rec["author"]} {rec["name_or_title"][:50]}'
    key = re.sub(r"[^\w\s]", "", key.lower())      # lowercase, drop punctuation
    key = " ".join(key.split())                     # collapse spaces
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def find_duplicates(records):
    seen, unique, dupes = set(), [], []
    for rec in records:
        fp = make_fingerprint(rec)
        (dupes if fp in seen else unique).append(rec)
        seen.add(fp)
    return unique, dupes
```

A test with deliberately duplicated data proves the logic works, even though the real sites contain no duplicates:

```python
def test_duplicates_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None}
    records = [
        {**base, "name_or_title": "Example Book Title"},
        {**base, "name_or_title": "  Example Book Title "},
        {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
    ]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1 and len(dupes) == 2
```

Note: the helper strips punctuation and collapses spaces, so the second record (with leading and trailing spaces) matches the first. If your cleaning step already trims whitespace, the test still passes.

### 5.7 Writing the summary report (Stage 8)

```python
import json
from pathlib import Path

def write_summary(stats: dict, path: Path):
    path.parent.mkdir(exist_ok=True)               # create output/ if missing
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)

stats = {
    "collected_per_source": {"Books to Scrape": 1000, "Quotes to Scrape": 100},
    "rejected_by_reason": {"invalid_url": 0, "missing_name": 0},
    "duplicates_detected": 0,
    "final_record_count": 1100,
    "duration_seconds": 612.4,
}
```

The numbers above are placeholders to show the shape. Your real report must contain the values from your own run.

1. Assignment Overview
Build a Python-based web scraping and data-processing pipeline that collects information from multiple public web sources, cleans and standardizes the collected data, identifies duplicates, validates the results, and produces one consolidated dataset.
This assignment is designed to evaluate practical Python, web scraping, data processing, problem-solving, error handling, and code-quality skills at a medium level.
2. Assignment Scenario
You are working as a Python Data Scraper responsible for collecting information from multiple websites. Each website presents information in a different structure. Your job is to build a reusable process that can collect the information, transform it into a common structure, validate it, and generate a final dataset.
The expected workflow is:
Website A ─┐
Website B ─┼─> Scraping ─> Cleaning ─> Validation ─> Deduplication ─> Consolidation ─> Final Dataset
           ┘
3. Data Sources
Use the following public scraping practice websites:
Source 1 – Books to Scrape: https://books.toscrape.com/
The site contains book records with fields such as title, price, availability, rating, category and product URL, distributed across multiple pages.
Source 2 – Quotes to Scrape: https://quotes.toscrape.com/
The site contains quotes, authors, tags and author-related information across multiple pages.
These are public scraping practice sites. Do not attempt to bypass authentication, CAPTCHAs, robots restrictions, access controls, or other security mechanisms.
4. Objective
The completed solution should be able to:
Collect data from both sources.
Handle pagination.
Normalize different source structures into a common data model.
Clean and validate the collected data.
Detect and remove or flag duplicates.
Preserve source and source URL information.
Handle failures without unnecessarily stopping the full process.
Generate a final consolidated dataset and summary.
Provide clear documentation and reproducible setup instructions.
5. Technical Requirements
5.1 Scraping
Use Python.
Use an appropriate scraping library such as Requests + BeautifulSoup, Scrapy, Playwright, or Selenium where justified.
Scrape multiple pages from each source.
Implement pagination rather than hard-coding a small number of pages.
Extract the required information from each source.
Capture the source name and original source URL.
Handle missing HTML elements without crashing the complete scraper.
5.2 Suggested Fields
Create a standardized schema suitable for both sources. For example:
source
source_url
name_or_title
category
price
rating
author
tags
description
scraped_at
Not every field will exist for every source. Use appropriate null/empty values when a field does not apply. Do not invent data.
5.3 Data Cleaning & Standardization
Remove unnecessary whitespace.
Normalize text where appropriate.
Convert prices to numeric values.
Standardize rating values.
Normalize missing values.
Normalize or validate URLs.
Remove clearly invalid records.
Keep the transformation logic separate from the scraping logic where practical.
5.4 Duplicate Detection
Implement a reasonable duplicate-detection strategy. Exact string comparison alone may not be sufficient because the same value can appear with differences in whitespace, capitalization, or formatting.
"Example Book Title"
" Example Book Title "
"EXAMPLE BOOK TITLE"
Explain in the README which fields or normalization rules you used to determine whether records are duplicates. If you choose to flag duplicates rather than delete them, explain why.
5.5 Validation
Add basic validation before writing the final dataset. Examples:
Required fields are present where applicable.
Price values are numeric when a price exists.
Ratings are within the expected range.
URLs are present and valid-looking.
Records have a recognizable source.
Duplicate counts are measurable.
5.6 Error Handling & Logging
Handle common scraping failures such as:
Connection failures
HTTP errors
Timeouts
Missing page elements
Unexpected data formats
Invalid values
Individual page failures
The scraper should continue processing other pages or sources when reasonably possible. Add logging so that a reviewer can understand what happened during execution.
6. Required Step-by-Step Implementation
Step 1 – Explore the Sources
Inspect both websites and understand their page structure, pagination mechanism, available fields, and differences between the sources. Document important observations.
Step 2 – Design the Data Model
Define a common output structure that can represent data from both sources. Decide how missing or source-specific fields will be handled.
Step 3 – Build Source Scrapers
Create separate scraper modules/classes/functions for Books to Scrape and Quotes to Scrape. Keep source-specific selectors and parsing logic isolated.
Step 4 – Implement Pagination
Automatically move through the available pages. Avoid manually listing every page URL.
Step 5 – Create Cleaning Functions
Create reusable functions for whitespace cleanup, numeric conversion, text normalization, URL handling, and missing-value handling.
Step 6 – Add Validation
Validate records before they enter the final dataset and record validation failures where useful.
Step 7 – Implement Deduplication
Create a repeatable method for identifying duplicate or equivalent records and document the logic.
Step 8 – Consolidate Data
Combine the cleaned records from both sources into one standardized dataset while preserving source information.
Step 9 – Add Logging and Error Handling
Add meaningful logs, exception handling, and reasonable retry behavior where appropriate.
Step 10 – Generate Output
Produce the final CSV and a summary report showing what was scraped, cleaned, rejected, and deduplicated.
Step 11 – Test the Solution
Run the complete pipeline from a clean environment and verify the output. Include tests if implemented.
7. Expected Output
The submission should produce at minimum:
output/
    final_dataset.csv
    summary_report.json
The final dataset should contain standardized records and, at minimum, enough information to identify the source and original URL.
The summary should include metrics such as:
Total records collected per source
Total records after cleaning
Records rejected during validation
Duplicate records detected/removed/flagged
Final record count
Execution time if available
8. Example Final Dataset
source | name_or_title | category | price | rating | author | tags | source_url | scraped_at
Books to Scrape | ... | ... | ... | ... | ... | ... | ... | ...
Quotes to Scrape | ... | ... | ... | ... | ... | ... | ... | ...rggth
9. Recommended Project Structure
scraping_assignment/
├── scrapers/
│   ├── books_scraper.py
│   └── quotes_scraper.py
├── processing/
│   ├── cleaning.py
│   ├── validation.py
│   └── deduplication.py
├── output/
├── logs/
├── tests/
├── main.py
├── requirements.txt
├── README.md
└── AI_USAGE.md
The structure above is only a recommendation. A different structure is acceptable if it is clean, logical, and explained.
10. AI Usage – Allowed and Expected
AI tools are explicitly allowed for this assignment. Candidates may use ChatGPT, Claude, GitHub Copilot, Cursor, Gemini, or another AI coding assistant.
AI may be used for:
Understanding HTML/page structure
Generating initial code
Debugging errors
Improving scraper logic
Designing data models
Generating tests
Improving documentation
Finding edge cases
Refactoring code
The candidate remains responsible for the final implementation. AI-generated code must be reviewed, tested, and corrected where necessary. The candidate should not submit code they cannot explain.
11. AI_USAGE.md – Required
Include an AI_USAGE.md file with the following:
AI tools used.
What each tool was used for.
A few representative prompts.
Which parts of the code were AI-assisted.
Important changes made after reviewing AI output.
Any incorrect or incomplete AI-generated suggestions discovered.
How the final solution was tested and verified.
Example:
Tool: ChatGPT
Used for: Initial pagination approach and debugging a selector issue.
Verification: Tested pagination against all available pages and manually checked sample records.
12. README.md – Required Content
Assignment/project overview
Python version
Installation/setup instructions
Dependencies
How to run the scraper
How pagination works
Data model
Cleaning approach
Validation approach
Deduplication approach
Error-handling approach
Output description
Assumptions
Known limitations
AI usage summary
13. Deliverables
Submit one ZIP file containing:
Complete Python source code
requirements.txt
README.md
AI_USAGE.md
Final consolidated dataset
Summary report
Sample execution logs
Tests, if implemented
Configuration files, if used
14. Bonus Features
The following are optional and can provide additional credit:
MongoDB or PostgreSQL integration
Retry mechanism with exponential backoff
Configurable settings
Unit tests
Parallel or asynchronous processing
Rate limiting
Incremental scraping
Checkpoint/resume functionality
Docker setup
Data-quality report
CLI arguments for controlling the scraper
15. Evaluation Criteria
Evaluation Area
Weight
Python & Code Quality
20%
Web Scraping
20%
Data Cleaning & Standardization
15%
Duplicate Detection
15%
Error Handling & Reliability
10%
Documentation & Project Structure
10%
AI Usage & Understanding
10%

16. Interview Follow-Up
After submission, the candidate may be asked to walk through the project and explain the implementation.
Why did you choose your scraping library?
How does pagination work?
How did you handle missing fields?
How did you handle failed requests?
How does your duplicate-detection logic work?
Why did you choose your standardized schema?
What assumptions did you make?
Which parts were AI-assisted?
Did AI-generated code create any problems?
How did you verify that the final result was correct?
What would you change if this scraper had to run regularly in production?
17. Important Rules
Use only publicly accessible information from the provided practice websites.
Do not bypass authentication, CAPTCHA, access controls, or security mechanisms.
Respect reasonable request rates and avoid unnecessarily aggressive traffic.
Do not include secrets, API keys, passwords, or personal credentials in the submission.
AI usage is allowed, but the candidate must understand and be able to explain the submitted work.
The final submission should be reproducible from the README instructions.
18. Expected Level
This is a medium-level assignment. You are not expected to build a large production scraping platform. The focus is on writing clean Python, correctly scraping multiple sources, handling different data structures, cleaning and consolidating data, dealing with failures, and demonstrating practical problem-solving. 
