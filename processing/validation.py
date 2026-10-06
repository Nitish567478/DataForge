from typing import Any, Dict, List

VALID_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(rec: Dict[str, Any]) -> List[str]:
    problems: List[str] = []

    source = rec.get("source")
    if source not in VALID_SOURCES:
        problems.append("unknown_source")

    name_or_title = rec.get("name_or_title")
    if not name_or_title or not str(name_or_title).strip():
        problems.append("missing_name")

    source_url = str(rec.get("source_url") or "").strip()
    if not source_url.startswith(("http://", "https://")):
        problems.append("invalid_url")

    price = rec.get("price")
    if price is not None:
        if not isinstance(price, (int, float)) or price < 0:
            problems.append("invalid_price")

    rating = rec.get("rating")
    if rating is not None:
        if not isinstance(rating, int) or rating not in (1, 2, 3, 4, 5):
            problems.append("invalid_rating")

    return problems


def is_valid_record(rec: Dict[str, Any]) -> bool:
    return len(validate_record(rec)) == 0
