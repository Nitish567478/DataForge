import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time
import uuid

from database.mongodb import MongoDBStorage
from processing.cleaning import clean_record
from processing.deduplication import find_duplicates
from processing.validation import validate_record
from scrapers.base_scraper import create_session
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

CSV_FIELDNAMES = [
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "scraped_at",
]


def setup_logging(log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    return root_logger


def save_to_csv(records: list, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = {k: ("" if rec.get(k) is None else rec.get(k)) for k in CSV_FIELDNAMES}
            writer.writerow(row)


def save_summary_report(report_data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)


def run_pipeline(
    max_pages_books: int = None,
    max_pages_quotes: int = None,
    output_dir: Path = Path("output"),
    log_file: Path = Path("logs/scraper.log"),
    mongo_uri: str = None,
    mongo_db_name: str = "scraping_pipeline",
    skip_mongo: bool = False,
) -> dict:
    setup_logging(log_file)
    logger = logging.getLogger("ETLPipeline")

    batch_id = str(uuid.uuid4())
    start_time = time.time()
    start_iso = datetime.now(timezone.utc).isoformat()
    logger.info("==================================================")
    logger.info("Starting ETL Pipeline Run (Batch ID: %s)", batch_id)
    logger.info("==================================================")

    session = create_session()

    mongo = MongoDBStorage(uri=mongo_uri, db_name=mongo_db_name)
    mongo_connected = False
    if not skip_mongo:
        logger.info("Connecting to MongoDB at %s (DB: %s)...", mongo.uri, mongo.db_name)
        mongo_connected = mongo.connect()
        if not mongo_connected:
            logger.warning("MongoDB is currently offline or unreachable. Proceeding with CSV/JSON exports.")
    else:
        logger.info("Skipping MongoDB connection as per configuration flag.")

    raw_books = []
    raw_quotes = []

    try:
        logger.info(">>> Stage 1A: Scraping Books to Scrape...")
        books_scraper = BooksScraper(session=session)
        raw_books = books_scraper.scrape(max_pages=max_pages_books)
        logger.info("Books scraping completed: %d raw items collected.", len(raw_books))
    except Exception as exc:
        logger.error("Failed scraping Books to Scrape: %s", exc, exc_info=True)

    try:
        logger.info(">>> Stage 1B: Scraping Quotes to Scrape...")
        quotes_scraper = QuotesScraper(session=session)
        raw_quotes = quotes_scraper.scrape(max_pages=max_pages_quotes)
        logger.info("Quotes scraping completed: %d raw items collected.", len(raw_quotes))
    except Exception as exc:
        logger.error("Failed scraping Quotes to Scrape: %s", exc, exc_info=True)

    total_raw_records = raw_books + raw_quotes
    logger.info("Total raw records collected across all sources: %d", len(total_raw_records))

    if mongo_connected:
        mongo.save_raw_records(total_raw_records, batch_id=batch_id)

    logger.info(">>> Stage 2: Cleaning and Standardizing Records...")
    cleaned_records = []
    cleaned_per_source = Counter()

    for r in total_raw_records:
        cleaned = clean_record(r)
        cleaned_records.append(cleaned)
        cleaned_per_source[cleaned.get("source", "Unknown")] += 1

    logger.info(">>> Stage 3: Validating Records against Business Rules...")
    valid_records = []
    rejected_records = []
    rejected_reasons_counter = Counter()

    for rec in cleaned_records:
        problems = validate_record(rec)
        if problems:
            for p in problems:
                rejected_reasons_counter[p] += 1
            rejected_records.append({"record": rec, "reasons": problems})
            logger.warning("Record rejected: %s | Reasons: %s", rec.get("name_or_title"), problems)
        else:
            valid_records.append(rec)

    logger.info(
        "Validation complete: %d valid, %d rejected (Problem breakdown: %s)",
        len(valid_records),
        len(rejected_records),
        dict(rejected_reasons_counter),
    )

    if mongo_connected and rejected_records:
        mongo.save_rejected_records(rejected_records, batch_id=batch_id)

    logger.info(">>> Stage 4: Detecting and Isolating Duplicates...")
    unique_records, duplicate_records = find_duplicates(valid_records)
    logger.info(
        "Deduplication complete: %d unique records, %d duplicates detected.",
        len(unique_records),
        len(duplicate_records),
    )

    if mongo_connected and duplicate_records:
        mongo.save_duplicate_records(duplicate_records, batch_id=batch_id)

    logger.info(">>> Stage 5: Loading Final Dataset & Exporting...")
    csv_file = output_dir / "final_dataset.csv"
    save_to_csv(unique_records, csv_file)
    logger.info("Saved final dataset CSV to %s (%d rows)", csv_file, len(unique_records))

    mongo_saved_count = 0
    if mongo_connected:
        mongo_saved_count = mongo.save_final_dataset(unique_records, batch_id=batch_id)

    end_time = time.time()
    end_iso = datetime.now(timezone.utc).isoformat()
    duration = round(end_time - start_time, 2)

    summary_report = {
        "batch_id": batch_id,
        "start_time": start_iso,
        "end_time": end_iso,
        "duration_seconds": duration,
        "collected_per_source": {
            "Books to Scrape": len(raw_books),
            "Quotes to Scrape": len(raw_quotes),
            "Total": len(total_raw_records),
        },
        "cleaned_per_source": dict(cleaned_per_source),
        "validation": {
            "valid_records": len(valid_records),
            "rejected_records": len(rejected_records),
            "rejected_by_reason": dict(rejected_reasons_counter),
        },
        "deduplication": {
            "duplicates_detected": len(duplicate_records),
            "unique_records": len(unique_records),
        },
        "final_record_count": len(unique_records),
        "reconciliation_check": {
            "formula": "raw_total - rejected_total - duplicates_detected == final_count",
            "is_reconciled": (len(total_raw_records) - len(rejected_records) - len(duplicate_records)) == len(unique_records),
        },
        "mongodb_storage": {
            "connected": mongo_connected,
            "database": mongo.db_name if mongo_connected else None,
            "records_persisted": mongo_saved_count,
        },
    }

    report_file = output_dir / "summary_report.json"
    save_summary_report(summary_report, report_file)
    logger.info("Saved execution summary report to %s", report_file)

    if mongo_connected:
        mongo.save_summary_report(summary_report, batch_id=batch_id)
        mongo.close()

    logger.info("==================================================")
    logger.info("ETL Pipeline finished successfully in %.2f seconds.", duration)
    logger.info("Final Clean Dataset: %d records", len(unique_records))
    logger.info("==================================================")

    return summary_report


def main():
    parser = argparse.ArgumentParser(
        description="Unified ETL Web Scraper for Books to Scrape & Quotes to Scrape (with MongoDB persistence)"
    )
    parser.add_argument(
        "--max-pages-books",
        type=int,
        default=None,
        help="Maximum pages to scrape for Books to Scrape (default: None, scrape all pages dynamically)",
    )
    parser.add_argument(
        "--max-pages-quotes",
        type=int,
        default=None,
        help="Maximum pages to scrape for Quotes to Scrape (default: None, scrape all pages dynamically)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save CSV and JSON outputs (default: output)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="logs/scraper.log",
        help="Log file path (default: logs/scraper.log)",
    )
    parser.add_argument(
        "--mongo-uri",
        type=str,
        default=None,
        help="MongoDB Connection URI (e.g. mongodb://localhost:27017/ or MONGODB_URI env var)",
    )
    parser.add_argument(
        "--mongo-db",
        type=str,
        default="scraping_pipeline",
        help="MongoDB Database name (default: scraping_pipeline)",
    )
    parser.add_argument(
        "--skip-mongo",
        action="store_true",
        help="Disable MongoDB storage and run file exports only",
    )

    args = parser.parse_args()

    run_pipeline(
        max_pages_books=args.max_pages_books,
        max_pages_quotes=args.max_pages_quotes,
        output_dir=Path(args.output_dir),
        log_file=Path(args.log_file),
        mongo_uri=args.mongo_uri,
        mongo_db_name=args.mongo_db,
        skip_mongo=args.skip_mongo,
    )


if __name__ == "__main__":
    main()
