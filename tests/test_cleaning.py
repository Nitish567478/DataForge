from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_record,
    clean_tags,
    clean_text,
    normalize_url,
    strip_quotes,
)


def test_clean_text():
    assert clean_text("  Hello \n\t World  ") == "Hello World"
    assert clean_text("A\xa0non-breaking\xa0space") == "A non-breaking space"
    assert clean_text("   ") is None
    assert clean_text(None) is None
    assert clean_text(123) == "123"


def test_strip_quotes():
    assert strip_quotes('“The world is a book...”') == "The world is a book..."
    assert strip_quotes('"Hello World"') == "Hello World"
    assert strip_quotes("‘Single quoted’") == "Single quoted"
    assert strip_quotes("«French quotes»") == "French quotes"
    assert strip_quotes("No quotes here") == "No quotes here"
    assert strip_quotes(None) is None


def test_clean_price():
    assert clean_price("£51.77") == 51.77
    assert clean_price("$19.99") == 19.99
    assert clean_price("€ 1,234.50") == 1234.50
    assert clean_price("Free") is None
    assert clean_price(None) is None
    assert clean_price(42.5) == 42.5
    assert clean_price(-10) is None


def test_clean_rating():
    assert clean_rating("star-rating Three") == 3
    assert clean_rating("Three") == 3
    assert clean_rating("One") == 1
    assert clean_rating("FIVE") == 5
    assert clean_rating(4) == 4
    assert clean_rating("star-rating zero") is None
    assert clean_rating("invalid") is None
    assert clean_rating(None) is None


def test_clean_tags():
    assert clean_tags(["books", "LIFE", "  reading  "]) == "books;life;reading"
    assert clean_tags("philosophy, life, books") == "books;life;philosophy"
    assert clean_tags("tag1; tag2; TAG1") == "tag1;tag2"
    assert clean_tags([]) is None
    assert clean_tags(None) is None


def test_normalize_url():
    assert normalize_url("https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html") == (
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )
    assert normalize_url("catalogue/page-2.html", base_url="https://books.toscrape.com/index.html") == (
        "https://books.toscrape.com/catalogue/page-2.html"
    )
    assert normalize_url("javascript:void(0)") is None
    assert normalize_url(None) is None


def test_clean_record():
    raw = {
        "source": "Quotes to Scrape",
        "name_or_title": " “The truth will set you free.” ",
        "author": "  John Doe  ",
        "tags": ["Truth", "freedom", "TRUTH"],
        "source_url": "https://quotes.toscrape.com/author/John-Doe",
        "price": None,
        "rating": None,
        "category": None,
        "description": None,
        "scraped_at": "2026-10-06T12:00:00Z",
    }
    cleaned = clean_record(raw)
    assert cleaned["name_or_title"] == "The truth will set you free."
    assert cleaned["author"] == "John Doe"
    assert cleaned["tags"] == "freedom;truth"
    assert cleaned["source_url"] == "https://quotes.toscrape.com/author/John-Doe"
