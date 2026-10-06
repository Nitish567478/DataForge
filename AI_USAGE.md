# AI Usage Disclosure & Verification Log

In compliance with Section 11 of the Project Specification, this document provides a comprehensive and transparent record of AI assistance utilized during the development, refactoring, and testing of this web scraping & ETL data pipeline.

---

## 1. Overview of AI Tools Used

| AI Tool | Purpose | Components Assisted |
| --- | --- | --- |
| **Google Gemini / Antigravity Agentic Assistant** | Architecture planning, boilerplate generation, unit test scaffolding, debugging edge cases | `scrapers/`, `processing/`, `database/`, `tests/`, `main.py` |

---

## 2. Representative Prompts Used

### Prompt 1: Resilient HTTP Client Architecture
> *"Design a robust Requests HTTP session wrapper in Python with urllib3 Retry adapter handling HTTP 429, 500, 502, 503, 504 with exponential backoff and polite delay for web scraping practice sites."*

### Prompt 2: Dynamic Next-Link Pagination
> *"Implement dynamic pagination for Books to Scrape and Quotes to Scrape using BeautifulSoup and urllib.parse.urljoin that stops automatically when no 'li.next > a' exists."*

### Prompt 3: Deterministic Cryptographic Fingerprinting
> *"Write a duplicate detection module in Python that generates a SHA-256 fingerprint from normalized fields (source, title/quote text, author) ignoring case, punctuation, and extraneous whitespace."*

### Prompt 4: Isolated MongoDB Testing with Mocking
> *"Generate unit tests for a MongoDB persistence module using mongomock so tests can run without needing an active MongoDB daemon."*

---

## 3. Which Parts of the Code Were AI-Assisted

1. **Scraper Selectors & Extraction:** Initial mapping of CSS selectors (`article.product_pod`, `div.quote`, `li.next > a`, `span.text`, `small.author`, `p.price_color`, `p.star-rating`).
2. **Data Cleaning Module:** Regex pattern for currency parsing (`\d+(?:\.\d+)?`), star rating mapping dictionary, tag list sorting and semicolon concatenation.
3. **Validation Functions:** Checking mandatory business rules and returning problem codes list.
4. **Deduplication:** SHA-256 fingerprint generation logic.
5. **MongoDB Integration:** Connection pooling, database collections creation, index creation, document insertion for raw records, dataset, rejected items, and execution reports.
6. **Unit Tests:** Pytest test cases covering edge cases across cleaning, validation, deduplication, scrapers, and MongoDB CRUD.

---

## 4. Critical Corrections & Improvements Made After Human Review

During review and test execution, several important edge cases and corrections were identified and resolved:

### 1. Duplicate Detection Character Slicing Bug
- **Initial AI Output:** Sliced the quote text (`title_or_text[:50]`) *before* stripping punctuation and collapsing whitespace.
- **Problem:** If one record had leading spaces or punctuation marks (e.g. `.` or `"`), the 50-character slice ended at different words, causing equivalent quotes to generate mismatched fingerprints.
- **Correction:** Refactored [processing/deduplication.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/processing/deduplication.py) so that field-level lowercase conversion, punctuation stripping (`[^\w\s]`), and whitespace collapsing are executed *prior* to extracting the 50-character slice.

### 2. Character Encoding (`Â£` corruption)
- **Problem:** When fetching pages from Books to Scrape, default ASCII decoding occasionally corrupted the British Pound symbol `£` into `Â£`.
- **Correction:** Explicitly enforced `response.encoding = "utf-8"` in [scrapers/base_scraper.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/scrapers/base_scraper.py) before reading response content.

### 3. Graceful Offline Database Handling
- **Problem:** If a local MongoDB instance was not running, the application risked crashing on startup.
- **Correction:** Implemented connection testing with timeout and graceful fallback in [database/mongodb.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/database/mongodb.py) and [main.py](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/main.py) so the pipeline logs a warning and successfully produces CSV and JSON reports while remaining fully functional.

---

## 5. Testing & Verification Methodology

The completed implementation was rigorously verified through:
1. **Automated Unit Testing:** Running all 20 tests across 5 test suites (`pytest -v`) with 100% pass rate.
2. **Live Scraping & Extraction Verification:** Running `python main.py` to scrape real pages from both target websites, verifying that dynamic pagination transitions through pages and stops correctly.
3. **Data Quality & Reconciliation Checks:** Inspecting [output/summary_report.json](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/output/summary_report.json) to verify the reconciliation formula:
   $$\text{raw\_total} - \text{rejected\_total} - \text{duplicates\_detected} == \text{final\_count}$$
4. **CSV & Encoding Audit:** Opening [output/final_dataset.csv](file:///c:/Users/HP/OneDrive/Desktop/Realisieren%20Technologies/output/final_dataset.csv) and verifying column order, float conversion of prices, rating integers, and curly quote removal.
