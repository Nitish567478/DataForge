import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
}

QUOTE_CHARS = '“"\'”«»‘’`'


def clean_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    
    normalized = value.replace("\xa0", " ")
    collapsed = " ".join(normalized.split())
    return collapsed if collapsed else None


def strip_quotes(value: Optional[str]) -> Optional[str]:
    text = clean_text(value)
    if not text:
        return None
    
    cleaned = text.strip(QUOTE_CHARS).strip()
    return cleaned if cleaned else None


def clean_price(raw: Any) -> Optional[float]:
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw) if raw >= 0 else None
    
    raw_str = str(raw).replace(",", "").strip()
    match = re.search(r"\d+(?:\.\d+)?", raw_str)
    if match:
        try:
            val = float(match.group())
            return round(val, 2)
        except (ValueError, TypeError):
            return None
    return None


def clean_rating(raw: Any) -> Optional[int]:
    if raw is None or raw == "":
        return None
    if isinstance(raw, int) and 1 <= raw <= 5:
        return raw

    words = str(raw).lower().replace("-", " ").replace("_", " ").split()
    for word in words:
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None


def clean_tags(tags: Union[List[str], str, None]) -> Optional[str]:
    if tags is None:
        return None

    tag_list: List[str] = []
    if isinstance(tags, list):
        tag_list = [str(t) for t in tags]
    elif isinstance(tags, str):
        tag_list = re.split(r"[,;]", tags)

    cleaned_set = set()
    for t in tag_list:
        c = clean_text(t)
        if c:
            cleaned_set.add(c.lower())

    if not cleaned_set:
        return None

    return ";".join(sorted(cleaned_set))


def normalize_url(url: Optional[str], base_url: Optional[str] = None) -> Optional[str]:
    cleaned = clean_text(url)
    if not cleaned:
        return None

    if base_url:
        cleaned = urljoin(base_url, cleaned)

    parsed = urlparse(cleaned)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return cleaned
    return None


def clean_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    source = clean_text(raw.get("source"))
    name_or_title = raw.get("name_or_title")

    if source == "Quotes to Scrape":
        name_or_title = strip_quotes(name_or_title)
    else:
        name_or_title = clean_text(name_or_title)

    category = clean_text(raw.get("category"))
    description = clean_text(raw.get("description"))
    author = clean_text(raw.get("author"))
    price = clean_price(raw.get("price"))
    rating = clean_rating(raw.get("rating"))
    tags = clean_tags(raw.get("tags"))
    source_url = normalize_url(raw.get("source_url"))
    scraped_at = clean_text(raw.get("scraped_at"))

    return {
        "source": source,
        "source_url": source_url,
        "name_or_title": name_or_title,
        "category": category,
        "price": price,
        "rating": rating,
        "author": author,
        "tags": tags,
        "description": description,
        "scraped_at": scraped_at,
    }
