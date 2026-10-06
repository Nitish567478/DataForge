from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError

from processing.deduplication import make_fingerprint

logger = logging.getLogger(__name__)


class MongoDBStorage:
    DEFAULT_URI = "mongodb://localhost:27017/"
    DEFAULT_DB_NAME = "scraping_pipeline"

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        timeout_ms: int = 4000,
        custom_client: Optional[MongoClient] = None,
    ):
        self.uri = uri or os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or self.DEFAULT_URI
        self.db_name = db_name or os.getenv("MONGO_DB_NAME") or self.DEFAULT_DB_NAME
        self.timeout_ms = timeout_ms
        self._custom_client = custom_client
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self.connected = False

    def connect(self) -> bool:
        try:
            if self._custom_client is not None:
                self._client = self._custom_client
            else:
                self._client = MongoClient(
                    self.uri,
                    serverSelectionTimeoutMS=self.timeout_ms,
                    connectTimeoutMS=self.timeout_ms,
                )
            self._client.admin.command("ping")
            self._db = self._client[self.db_name]
            self.connected = True
            logger.info("Successfully connected to MongoDB at %s (Database: %s)", self.uri, self.db_name)
            self._setup_indexes()
            return True
        except (ConnectionFailure, PyMongoError, Exception) as exc:
            logger.warning("MongoDB connection failed or unavailable at %s: %s", self.uri, exc)
            self.connected = False
            return False

    def _setup_indexes(self):
        if not self.connected or self._db is None:
            return
        try:
            dataset_col: Collection = self._db["consolidated_dataset"]
            dataset_col.create_index("fingerprint", unique=False)
            dataset_col.create_index("source")
            dataset_col.create_index("scraped_at")

            raw_col: Collection = self._db["raw_scraped"]
            raw_col.create_index("batch_id")
            raw_col.create_index("source")

            reports_col: Collection = self._db["summary_reports"]
            reports_col.create_index("batch_id")
            reports_col.create_index("generated_at")
        except Exception as exc:
            logger.warning("Could not create MongoDB indexes: %s", exc)

    def save_raw_records(self, records: List[Dict[str, Any]], batch_id: str) -> int:
        if not self.connected or self._db is None or not records:
            return 0
        try:
            docs = []
            for r in records:
                doc = dict(r)
                doc["batch_id"] = batch_id
                doc["stored_at"] = datetime.now(timezone.utc).isoformat()
                docs.append(doc)
            res = self._db["raw_scraped"].insert_many(docs)
            inserted = len(res.inserted_ids)
            logger.info("Saved %d raw records to MongoDB collection 'raw_scraped'", inserted)
            return inserted
        except Exception as exc:
            logger.error("Failed to save raw records to MongoDB: %s", exc)
            return 0

    def save_final_dataset(self, records: List[Dict[str, Any]], batch_id: str) -> int:
        if not self.connected or self._db is None or not records:
            return 0
        try:
            docs = []
            for r in records:
                doc = dict(r)
                doc["fingerprint"] = make_fingerprint(doc)
                doc["batch_id"] = batch_id
                doc["stored_at"] = datetime.now(timezone.utc).isoformat()
                docs.append(doc)
            res = self._db["consolidated_dataset"].insert_many(docs)
            inserted = len(res.inserted_ids)
            logger.info("Saved %d consolidated records to MongoDB collection 'consolidated_dataset'", inserted)
            return inserted
        except Exception as exc:
            logger.error("Failed to save consolidated records to MongoDB: %s", exc)
            return 0

    def save_rejected_records(self, rejected: List[Dict[str, Any]], batch_id: str) -> int:
        if not self.connected or self._db is None or not rejected:
            return 0
        try:
            docs = []
            for item in rejected:
                doc = {
                    "batch_id": batch_id,
                    "record": item.get("record"),
                    "reasons": item.get("reasons", []),
                    "stored_at": datetime.now(timezone.utc).isoformat(),
                }
                docs.append(doc)
            res = self._db["rejected_records"].insert_many(docs)
            inserted = len(res.inserted_ids)
            logger.info("Saved %d rejected records to MongoDB collection 'rejected_records'", inserted)
            return inserted
        except Exception as exc:
            logger.error("Failed to save rejected records to MongoDB: %s", exc)
            return 0

    def save_duplicate_records(self, duplicates: List[Dict[str, Any]], batch_id: str) -> int:
        if not self.connected or self._db is None or not duplicates:
            return 0
        try:
            docs = []
            for r in duplicates:
                doc = {
                    "batch_id": batch_id,
                    "record": dict(r),
                    "fingerprint": make_fingerprint(r),
                    "stored_at": datetime.now(timezone.utc).isoformat(),
                }
                docs.append(doc)
            res = self._db["duplicate_records"].insert_many(docs)
            inserted = len(res.inserted_ids)
            logger.info("Saved %d duplicate records to MongoDB collection 'duplicate_records'", inserted)
            return inserted
        except Exception as exc:
            logger.error("Failed to save duplicate records to MongoDB: %s", exc)
            return 0

    def save_summary_report(self, report: Dict[str, Any], batch_id: str) -> bool:
        if not self.connected or self._db is None:
            return False
        try:
            doc = dict(report)
            doc["batch_id"] = batch_id
            doc["generated_at"] = datetime.now(timezone.utc).isoformat()
            self._db["summary_reports"].insert_one(doc)
            logger.info("Saved summary report to MongoDB collection 'summary_reports'")
            return True
        except Exception as exc:
            logger.error("Failed to save summary report to MongoDB: %s", exc)
            return False

    def get_dataset(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.connected or self._db is None:
            return []
        try:
            cursor = self._db["consolidated_dataset"].find(query or {}, {"_id": 0})
            return list(cursor)
        except Exception as exc:
            logger.error("Failed to query MongoDB dataset: %s", exc)
            return []

    def close(self):
        if self._client:
            self._client.close()
            self.connected = False
            logger.debug("Closed MongoDB connection.")
