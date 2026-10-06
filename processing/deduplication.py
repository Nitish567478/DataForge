import hashlib
import re
from typing import Any, Dict, List, Set, Tuple


def make_fingerprint(rec: Dict[str, Any]) -> str:
    source = " ".join(str(rec.get("source") or "").split())
    raw_title = str(rec.get("name_or_title") or "")
    raw_author = str(rec.get("author") or "")

    norm_title = " ".join(re.sub(r"[^\w\s]", "", raw_title.lower()).split())
    norm_author = " ".join(re.sub(r"[^\w\s]", "", raw_author.lower()).split())
    norm_source = " ".join(re.sub(r"[^\w\s]", "", source.lower()).split())

    if source == "Books to Scrape":
        key = f"{norm_source} {norm_title}"
    else:
        key = f"{norm_source} {norm_author} {norm_title[:50]}"

    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    seen: Set[str] = set()
    unique: List[Dict[str, Any]] = []
    dupes: List[Dict[str, Any]] = []

    for rec in records:
        fp = make_fingerprint(rec)
        if fp in seen:
            dupes.append(rec)
        else:
            seen.add(fp)
            unique.append(rec)

    return unique, dupes
