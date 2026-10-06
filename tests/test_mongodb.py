import mongomock
from database.mongodb import MongoDBStorage


def test_mongodb_crud_operations():
    mock_client = mongomock.MongoClient()
    storage = MongoDBStorage(
        uri="mongodb://localhost:27017/",
        db_name="test_scraping_pipeline",
        custom_client=mock_client,
    )

    assert storage.connect() is True
    assert storage.connected is True

    raw_sample = [
        {"source": "Books to Scrape", "name_or_title": "Test Book 1", "price": "£10.00"},
        {"source": "Quotes to Scrape", "name_or_title": "Test Quote 1", "author": "Tester"},
    ]
    inserted_raw = storage.save_raw_records(raw_sample, batch_id="batch-001")
    assert inserted_raw == 2

    dataset_sample = [
        {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/1",
            "name_or_title": "Test Book 1",
            "price": 10.0,
            "rating": 5,
            "author": None,
            "tags": None,
        }
    ]
    inserted_final = storage.save_final_dataset(dataset_sample, batch_id="batch-001")
    assert inserted_final == 1

    docs = storage.get_dataset({"source": "Books to Scrape"})
    assert len(docs) == 1
    assert docs[0]["name_or_title"] == "Test Book 1"
    assert "fingerprint" in docs[0]

    rejections = [{"record": {"name_or_title": ""}, "reasons": ["missing_name"]}]
    inserted_rej = storage.save_rejected_records(rejections, batch_id="batch-001")
    assert inserted_rej == 1

    dupes = [{"source": "Books to Scrape", "name_or_title": "Duplicate Book"}]
    inserted_dupes = storage.save_duplicate_records(dupes, batch_id="batch-001")
    assert inserted_dupes == 1

    report = {"batch_id": "batch-001", "final_record_count": 1}
    assert storage.save_summary_report(report, batch_id="batch-001") is True

    storage.close()
    assert storage.connected is False
