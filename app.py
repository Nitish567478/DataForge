import csv
import json
import logging
from pathlib import Path
import threading
import time
from typing import Optional

from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from database.mongodb import MongoDBStorage
from main import run_pipeline

app = FastAPI(title="Web Scraping ETL Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "scraper.log"
CSV_FILE = OUTPUT_DIR / "final_dataset.csv"
REPORT_FILE = OUTPUT_DIR / "summary_report.json"

pipeline_state = {
    "is_running": False,
    "status": "idle",
    "last_run": None,
    "current_step": "Ready",
    "progress_percent": 0,
    "error": None,
}


def load_dataset_from_csv() -> list:
    if not CSV_FILE.exists():
        return []
    records = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_price = row.get("price")
            price_val = None
            if raw_price:
                try:
                    price_val = float(raw_price)
                except ValueError:
                    price_val = None
            
            raw_rating = row.get("rating")
            rating_val = None
            if raw_rating:
                try:
                    rating_val = int(raw_rating)
                except ValueError:
                    rating_val = None

            records.append({
                "source": row.get("source"),
                "source_url": row.get("source_url"),
                "name_or_title": row.get("name_or_title"),
                "category": row.get("category") or None,
                "price": price_val,
                "rating": rating_val,
                "author": row.get("author") or None,
                "tags": row.get("tags") or None,
                "description": row.get("description") or None,
                "scraped_at": row.get("scraped_at"),
            })
    return records


def execute_scrape_task(max_books: Optional[int], max_quotes: Optional[int]):
    global pipeline_state
    pipeline_state["is_running"] = True
    pipeline_state["status"] = "running"
    pipeline_state["error"] = None
    pipeline_state["current_step"] = "Extracting data from web sources..."
    pipeline_state["progress_percent"] = 15

    try:
        time.sleep(0.5)
        pipeline_state["current_step"] = "Running dynamic pagination & parsing..."
        pipeline_state["progress_percent"] = 45

        report = run_pipeline(
            max_pages_books=max_books,
            max_pages_quotes=max_quotes,
            output_dir=OUTPUT_DIR,
            log_file=LOG_FILE,
        )

        pipeline_state["current_step"] = "Deduplicating & persisting dataset..."
        pipeline_state["progress_percent"] = 90
        time.sleep(0.5)

        pipeline_state["is_running"] = False
        pipeline_state["status"] = "completed"
        pipeline_state["current_step"] = "Pipeline completed successfully!"
        pipeline_state["progress_percent"] = 100
        pipeline_state["last_run"] = report
    except Exception as exc:
        pipeline_state["is_running"] = False
        pipeline_state["status"] = "failed"
        pipeline_state["error"] = str(exc)
        pipeline_state["current_step"] = f"Failed: {exc}"
        pipeline_state["progress_percent"] = 0


@app.get("/api/stats")
def get_stats():
    report = None
    if REPORT_FILE.exists():
        try:
            with open(REPORT_FILE, "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception:
            report = None

    dataset = load_dataset_from_csv()
    books_count = sum(1 for r in dataset if r.get("source") == "Books to Scrape")
    quotes_count = sum(1 for r in dataset if r.get("source") == "Quotes to Scrape")

    return {
        "report": report,
        "total_records": len(dataset),
        "books_count": books_count,
        "quotes_count": quotes_count,
        "pipeline_state": pipeline_state,
    }


@app.get("/api/data")
def get_data(
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search keyword in title, author, or tags"),
    rating: Optional[int] = Query(None, description="Filter by rating (1-5)"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=200, description="Items per page"),
):
    dataset = load_dataset_from_csv()
    filtered = dataset

    if source and source != "all":
        filtered = [r for r in filtered if r.get("source") == source]

    if search:
        s = search.lower().strip()
        filtered = [
            r for r in filtered
            if (s in str(r.get("name_or_title") or "").lower())
            or (s in str(r.get("author") or "").lower())
            or (s in str(r.get("tags") or "").lower())
        ]

    if rating is not None:
        filtered = [r for r in filtered if r.get("rating") == rating]

    if min_price is not None:
        filtered = [r for r in filtered if r.get("price") is not None and r.get("price") >= min_price]

    if max_price is not None:
        filtered = [r for r in filtered if r.get("price") is not None and r.get("price") <= max_price]

    total_matches = len(filtered)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = filtered[start_idx:end_idx]

    return {
        "total": total_matches,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total_matches + page_size - 1) // page_size),
        "items": paged_items,
    }


@app.post("/api/scrape")
def trigger_scrape(
    background_tasks: BackgroundTasks,
    max_pages_books: Optional[int] = None,
    max_pages_quotes: Optional[int] = None,
):
    global pipeline_state
    if pipeline_state["is_running"]:
        return JSONResponse(status_code=409, content={"message": "Pipeline is already running."})

    thread = threading.Thread(
        target=execute_scrape_task,
        args=(max_pages_books, max_pages_quotes),
        daemon=True,
    )
    thread.start()

    return {"message": "Scraping pipeline initiated.", "status": "running"}


@app.get("/api/scrape/status")
def get_scrape_status():
    return pipeline_state


@app.get("/api/logs")
def get_logs(lines: int = Query(80, ge=10, le=500)):
    if not LOG_FILE.exists():
        return {"logs": ["No logs recorded yet."]}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:]
            return {"logs": [line.rstrip() for line in recent]}
    except Exception as exc:
        return {"logs": [f"Error reading logs: {exc}"]}


@app.get("/api/export/csv")
def export_csv():
    if not CSV_FILE.exists():
        return JSONResponse(status_code=404, content={"message": "CSV dataset not generated yet."})
    return FileResponse(
        CSV_FILE,
        media_type="text/csv",
        filename="final_dataset.csv",
    )


@app.get("/api/mongodb/status")
def get_mongodb_status():
    storage = MongoDBStorage(timeout_ms=2000)
    connected = storage.connect()
    info = {"connected": connected, "database": storage.db_name, "collections": {}}

    if connected and storage._db is not None:
        try:
            for col_name in ["raw_scraped", "consolidated_dataset", "rejected_records", "duplicate_records", "summary_reports"]:
                info["collections"][col_name] = storage._db[col_name].count_documents({})
        except Exception as exc:
            info["error"] = str(exc)
        storage.close()

    return info


STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start Web Scraping ETL Dashboard")
    parser.add_argument("--port", type=int, default=5173, help="Port to bind server (e.g. 5173 or 3000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    args = parser.parse_args()

    print(f"\n=======================================================")
    print(f"ETL Scraping Web Dashboard running at:")
    print(f">> http://localhost:{args.port}")
    print(f">> http://127.0.0.1:{args.port}")
    print(f"=======================================================\n")

    uvicorn.run("app:app", host=args.host, port=args.port, reload=False)
