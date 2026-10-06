# Web Scraping & ETL Data Pipeline (with MongoDB Integration)

A robust, modular, and production-grade Python ETL (Extract, Transform, Load) web scraping pipeline that extracts data from multiple public web sources ([Books to Scrape](https://books.toscrape.com/) and [Quotes to Scrape](https://quotes.toscrape.com/)), normalizes diverse structures into a unified schema, cleans and validates records, eliminates duplicates via cryptographic fingerprinting, and persists the dataset directly into **MongoDB** while exporting a tidy CSV dataset and execution summary report.

---

## 1. Project Overview & Architecture

Real-world web data arrives in heterogeneous formats, often with missing fields, messy encodings, and network unpredictability. This pipeline solves these challenges by isolating responsibilities into distinct, decoupled stages:

```
┌─────────────────────────────────────────────────────────────┐
│                       EXTRACT (Scrapers)                    │
│   Books to Scrape (50 pages)   Quotes to Scrape (10 pages)  │
│   Dynamic Pagination via 'li.next > a' + urllib.parse       │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Raw dictionaries)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      TRANSFORM (Processing)                 │
│   - Unicode & Whitespace Normalization (\\xa0, tabs, newlines)│
│   - Currency & Price Parsing to Floats                      │
│   - Star Rating to Integer (1 to 5)                         │
│   - Curly/Straight Quote Stripping                          │
│   - Tag Lowercasing, Deduplicating, Sorting, Semicolon Join │
│   - Absolute URL Normalization                              │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Cleaned dictionaries)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      VALIDATE (Business Rules)              │
│   Check source, mandatory title/text, valid URL, valid price│
│   and rating range. Rejections cataloged by reason code.    │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Valid records)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     DEDUPLICATE (Fingerprinting)            │
│   Deterministic SHA-256 fingerprint from normalized fields. │
│   Identifies duplicates across varied spacing/casing.       │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Unique consolidated records)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       LOAD & PERSISTENCE                    │
│   ├── MongoDB Database (raw, dataset, rejections, reports)  │
│   ├── output/final_dataset.csv (UTF-8 standard CSV)         │
│   ├── output/summary_report.json (Audit metrics & timing)   │
│   └── logs/scraper.log (Detailed timestamped trace)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Technical Stack & Prerequisites

- **Python Version:** `3.10`, `3.11`, `3.12`, or `3.13`
- **Database:** MongoDB Community Server (v5.0+ or v6.0+), MongoDB Atlas, or MongoDB in Docker.
- **Core Dependencies:**
  - `requests` (>= 2.31.0): Network requests with HTTP pooling and retry adapters.
  - `beautifulsoup4` (>= 4.12.3): HTML parsing and DOM navigation.
  - `lxml` (>= 5.3.0): High-speed C-based parser backend.
  - `pymongo` (>= 4.18.0): MongoDB driver.
  - `pytest` (>= 8.0.0): Automated test runner.
  - `mongomock` (>= 4.3.0): In-memory MongoDB mock for isolated testing.

---

## 3. Local Setup & Installation

### Step 1: Clone or Navigate to the Project Directory

```bash
cd "c:/Users/HP/OneDrive/Desktop/Realisieren Technologies"
```

### Step 2: Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Packages

```bash
pip install -r requirements.txt
```

---

## 4. MongoDB Setup Instructions

The pipeline is configured to persist all scraped data into **MongoDB**. You can run MongoDB locally in one of three ways:

### Option A: Local MongoDB Community Service (Windows/Mac/Linux)
1. Download and install [MongoDB Community Server](https://www.mongodb.com/try/download/community).
2. Ensure MongoDB service is running on default port `27017`:
   - **Windows:** Check Services -> `MongoDB Server` -> Running (or run `net start MongoDB`).
   - **Linux:** `sudo systemctl start mongod`
   - **macOS:** `brew services start mongodb-community`

### Option B: Run MongoDB with Docker (Quickest)
```bash
docker run -d --name mongo-scraper -p 27017:27017 -e MONGO_INITDB_DATABASE=scraping_pipeline mongo:latest
```

### Option C: MongoDB Atlas (Cloud)
Set your connection string via environment variable or CLI flag:
```bash
# Windows PowerShell:
$env:MONGODB_URI="mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"

# Linux/macOS:
export MONGODB_URI="mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"
```

> **Note on Offline Fallback:** If MongoDB is offline or unavailable during execution, the scraper will log a warning and proceed gracefully with CSV and JSON report exports without crashing.

---

## 5. How to Run the Project

### 5.1 Run the Web Dashboard (localhost:5173 or localhost:3000)
To start the interactive modern Web Dashboard on `http://localhost:5173`:
```bash
python app.py
```
Or run on port 3000:
```bash
python app.py --port 3000
```
Open your browser at:
👉 **[http://localhost:5173](http://localhost:5173)** (or `http://localhost:3000`)

Features available on the Web Dashboard:
- 📊 **Real-Time Metrics Overview:** Total records, books count, quotes count, duplicates detected, and duration.
- ⚡ **One-Click Scraper Runner:** Trigger the ETL pipeline directly from the UI with live progress indicators.
- 🔍 **Live Search & Filters:** Search by title/quote text, author, or tags; filter by source, star rating, and price.
- 💾 **MongoDB Status & Counts:** Monitor database connectivity and collections.
- 📥 **Instant CSV Download:** Download `final_dataset.csv` directly from the browser.
- 📝 **Live Logs Console:** View real-time timestamped scraping logs.

---

### 5.2 Run Scraper via CLI (Headless Mode)
To run the scraping pipeline directly in the terminal:
```bash
python main.py
```

### CLI Options:
| Flag | Type | Default | Description |
| --- | --- | --- | --- |
| `--max-pages-books` | `int` | `None` (All pages) | Limit number of pages to scrape from Books to Scrape |
| `--max-pages-quotes` | `int` | `None` (All pages) | Limit number of pages to scrape from Quotes to Scrape |
| `--mongo-uri` | `str` | `mongodb://localhost:27017/` | Custom MongoDB connection URI |
| `--mongo-db` | `str` | `scraping_pipeline` | MongoDB database name |
| `--output-dir` | `str` | `output` | Directory for CSV and JSON report |
| `--log-file` | `str` | `logs/scraper.log` | Destination file for logs |
| `--skip-mongo` | `flag` | `False` | Run file exports only without attempting DB connection |

### Examples:
```bash
# Quick test scrape (first 2 pages of each source):
python main.py --max-pages-books 2 --max-pages-quotes 2

# Scrape using custom MongoDB Atlas connection:
python main.py --mongo-uri "mongodb://admin:secret@localhost:27017/" --mongo-db custom_db
```

---

## 6. Unified Data Model

The pipeline maps the disparate structures from both websites into a single, standardized schema:

| Column Name | Type | Books to Scrape | Quotes to Scrape | Description |
| --- | --- | --- | --- | --- |
| `source` | `String` | `"Books to Scrape"` | `"Quotes to Scrape"` | Origin website name |
| `source_url` | `String` | Book detail page URL | Author bio URL or page URL | Absolute HTTP(S) URL |
| `name_or_title` | `String` | Full Book Title | Quote Text | Main item identifier |
| `category` | `String` | `null` (or category name) | `null` | Book genre / category |
| `price` | `Float` | Float (e.g. `51.77`) | `null` | Item price in GBP |
| `rating` | `Integer` | Integer `1` to `5` | `null` | Star rating scale |
| `author` | `String` | `null` | Author Full Name | Quote creator |
| `tags` | `String` | `null` | Semicolon-delimited (`change;life`) | Lowercased & sorted tags |
| `description` | `String` | `null` | `null` | Long-form description |
| `scraped_at` | `String` | ISO 8601 UTC Timestamp | ISO 8601 UTC Timestamp | Timestamp of extraction |

---

## 7. Dynamic Pagination Mechanism

Instead of hardcoding page URLs like `range(1, 51)`, both scrapers employ **dynamic next-link traversal**:
1. Scraper starts at root page (`https://books.toscrape.com/index.html` or `https://quotes.toscrape.com/`).
2. Parses records on current page.
3. Queries DOM for the next page anchor element: `li.next > a`.
4. If found, resolves the relative path into a fully qualified absolute URL using `urllib.parse.urljoin(current_url, next_tag["href"])`.
5. Pauses for 0.5s (`sleep_polite()`) to respect server rate limits.
6. Terminates dynamically when no `li.next > a` element is present.

---

## 8. Data Cleaning & Standardization

Implemented in [processing/cleaning.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/processing/cleaning.py) as pure, side-effect-free functions:
- **`clean_text`**: Strips Unicode non-breaking spaces (`\xa0`), tabs, and converts multiple whitespace sequences into a single space.
- **`strip_quotes`**: Removes surrounding typographical curly quotes (`“... ”`), single quotes, and double quotes.
- **`clean_price`**: Uses regex `\d+(?:\.\d+)?` to extract pure floating-point numbers from currency strings (e.g. `£51.77` -> `51.77`).
- **`clean_rating`**: Maps word-based rating classes (`star-rating Three` -> `3`, `Five` -> `5`).
- **`clean_tags`**: Normalizes tags by trimming, converting to lowercase, removing duplicates, alphabetically sorting, and joining with semicolons (`;`).
- **`normalize_url`**: Verifies URL validity and transforms relative links into absolute `http://` / `https://` URLs.

---

## 9. Validation Rules

Implemented in [processing/validation.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/processing/validation.py). Every record is validated before loading:

| Rule Code | Description | Condition for Rejection |
| --- | --- | --- |
| `unknown_source` | Source verification | `source` is not in `{"Books to Scrape", "Quotes to Scrape"}` |
| `missing_name` | Name/Title completeness | `name_or_title` is missing or blank |
| `invalid_url` | URL structure check | `source_url` does not start with `http://` or `https://` |
| `invalid_price` | Price integrity | `price` is present but negative or not numeric |
| `invalid_rating` | Rating boundary check | `rating` is present but outside integer range `1..5` |

Rejected records are isolated, cataloged by reason code, and logged without interrupting pipeline execution.

---

## 10. Duplicate Detection & Cryptographic Fingerprints

Implemented in [processing/deduplication.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/processing/deduplication.py).

To ensure deterministic duplicate matching regardless of extraneous whitespace, capitalization, or punctuation:
1. **Identifier Extraction:**
   - **Books:** `source` + `name_or_title`
   - **Quotes:** `source` + `author` + first 50 characters of `name_or_title`
2. **Normalization:** Convert to lowercase, remove all punctuation (`[^\w\s]`), and collapse whitespace.
3. **Hashing:** Compute a SHA-256 hex digest (`make_fingerprint`).
4. **Partitioning:** Records matching a previously seen fingerprint are partitioned into duplicates, while unique records move forward.

---

## 11. MongoDB Persistence Schema

Implemented in [database/mongodb.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/database/mongodb.py). The pipeline maintains the following collections in the database (`scraping_pipeline`):

1. **`raw_scraped`**: Complete raw payloads captured per scrape batch.
2. **`consolidated_dataset`**: Validated, cleaned, unique records with indexed `fingerprint`, `source`, and `scraped_at`.
3. **`rejected_records`**: Invalid records stored along with list of `rejection_reasons` for auditability.
4. **`duplicate_records`**: Detected duplicates with their matching fingerprint.
5. **`summary_reports`**: Detailed execution run metadata, counts, duration, and timestamp.

---

## 12. Running Unit Tests

The test suite validates cleaning, validation, fingerprinting, scrapers parsing, and MongoDB CRUD operations (using `mongomock`):

```bash
python -m pytest -v
```

Output:
```
tests/test_cleaning.py::test_clean_text PASSED
tests/test_cleaning.py::test_strip_quotes PASSED
tests/test_cleaning.py::test_clean_price PASSED
tests/test_cleaning.py::test_clean_rating PASSED
tests/test_cleaning.py::test_clean_tags PASSED
tests/test_cleaning.py::test_normalize_url PASSED
tests/test_cleaning.py::test_clean_record PASSED
tests/test_deduplication.py::test_fingerprint_deterministic PASSED
tests/test_deduplication.py::test_duplicates_ignore_case_and_spaces PASSED
tests/test_deduplication.py::test_quote_deduplication_author_and_text PASSED
tests/test_mongodb.py::test_mongodb_crud_operations PASSED
tests/test_scrapers.py::test_books_scraper_parsing PASSED
tests/test_scrapers.py::test_quotes_scraper_parsing PASSED
tests/test_validation.py::test_valid_book_record PASSED
tests/test_validation.py::test_valid_quote_record PASSED
tests/test_validation.py::test_unknown_source PASSED
tests/test_validation.py::test_missing_name PASSED
tests/test_validation.py::test_invalid_url PASSED
tests/test_validation.py::test_invalid_price PASSED
tests/test_validation.py::test_invalid_rating PASSED
======================= 20 passed in 0.50s =======================
```

---

## 13. Output Files & Verification

After executing `python main.py`, the following output files are created:

1. **[output/final_dataset.csv](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/output/final_dataset.csv)**: Consolidated dataset containing standardized rows from both sources.
2. **[output/summary_report.json](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/output/summary_report.json)**: Audit metrics confirming reconciliation (`raw_total - rejected_total - duplicates_detected == final_count`).
3. **[logs/scraper.log](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/logs/scraper.log)**: Full execution logs.

---

## 14. Assumptions & Known Limitations

1. **Book Description & Category:** On Books to Scrape, book categories and descriptions are located on individual product detail pages rather than the catalogue index pods. To maintain respectful request volumes (~50 pages rather than ~1,050 HTTP requests), these fields are safely defaulted to `None`.
2. **Author Bio URL:** For Quotes to Scrape, `source_url` points to the author profile page when available (`/author/...`), or the quote page URL.
3. **Network Resilience:** The scraper includes exponential backoff retries on transient errors (HTTP 429, 500, 502, 503, 504), but will stop an individual source after retries are exhausted to safeguard pipeline continuation.
