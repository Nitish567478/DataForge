from processing.deduplication import find_duplicates, make_fingerprint


def test_fingerprint_deterministic():
    rec1 = {
        "source": "Books to Scrape",
        "name_or_title": "Clean Code",
        "author": None,
    }
    rec2 = {
        "source": "Books to Scrape",
        "name_or_title": "Clean Code",
        "author": None,
    }
    assert make_fingerprint(rec1) == make_fingerprint(rec2)


def test_duplicates_ignore_case_and_spaces():
    base = {"source": "Books to Scrape", "author": None, "source_url": "https://books.toscrape.com/1"}
    records = [
        {**base, "name_or_title": "Example Book Title"},
        {**base, "name_or_title": "  Example Book Title "},
        {**base, "name_or_title": "EXAMPLE BOOK TITLE"},
    ]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1
    assert len(dupes) == 2


def test_quote_deduplication_author_and_text():
    base = {"source": "Quotes to Scrape", "author": "Albert Einstein", "source_url": "https://quotes.toscrape.com/1"}
    records = [
        {**base, "name_or_title": "Life is like riding a bicycle. To keep your balance you must keep moving."},
        {**base, "name_or_title": "  life is like riding a bicycle to keep your balance you must keep moving  "},
        {**base, "name_or_title": "A different quote by Einstein entirely."},
    ]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 2
    assert len(dupes) == 1
