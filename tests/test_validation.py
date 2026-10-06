from processing.validation import is_valid_record, validate_record


def test_valid_book_record():
    valid_book = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "name_or_title": "A Light in the Attic",
        "price": 51.77,
        "rating": 3,
        "author": None,
        "tags": None,
        "category": "Poetry",
        "description": "It's hard to be a poet...",
        "scraped_at": "2026-10-06T12:00:00Z",
    }
    problems = validate_record(valid_book)
    assert problems == []
    assert is_valid_record(valid_book) is True


def test_valid_quote_record():
    valid_quote = {
        "source": "Quotes to Scrape",
        "source_url": "https://quotes.toscrape.com/author/Albert-Einstein",
        "name_or_title": "The world as we have created it is a process of our thinking.",
        "author": "Albert Einstein",
        "tags": "change;deep-thoughts;thinking;world",
        "price": None,
        "rating": None,
        "category": None,
        "description": None,
        "scraped_at": "2026-10-06T12:00:00Z",
    }
    problems = validate_record(valid_quote)
    assert problems == []
    assert is_valid_record(valid_quote) is True


def test_unknown_source():
    rec = {
        "source": "Unauthorized Source",
        "source_url": "https://example.com/item",
        "name_or_title": "Test Title",
        "price": None,
        "rating": None,
    }
    problems = validate_record(rec)
    assert "unknown_source" in problems


def test_missing_name():
    rec = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/book/1",
        "name_or_title": "",
        "price": 10.0,
        "rating": 4,
    }
    problems = validate_record(rec)
    assert "missing_name" in problems


def test_invalid_url():
    rec = {
        "source": "Books to Scrape",
        "source_url": "ftp://not-http.com/resource",
        "name_or_title": "Good Book",
        "price": 10.0,
        "rating": 4,
    }
    problems = validate_record(rec)
    assert "invalid_url" in problems


def test_invalid_price():
    rec = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/book/1",
        "name_or_title": "Negative Price Book",
        "price": -15.99,
        "rating": 4,
    }
    problems = validate_record(rec)
    assert "invalid_price" in problems


def test_invalid_rating():
    rec = {
        "source": "Books to Scrape",
        "source_url": "https://books.toscrape.com/book/1",
        "name_or_title": "Invalid Rating Book",
        "price": 15.99,
        "rating": 6,
    }
    problems = validate_record(rec)
    assert "invalid_rating" in problems
