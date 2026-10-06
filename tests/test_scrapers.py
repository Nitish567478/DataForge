from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

HTML_BOOKS_SAMPLE = """
<html>
<body>
    <article class="product_pod">
        <div class="image_container">
            <a href="catalogue/a-light-in-the-attic_1000/index.html"><img src="media/cache.jpg" alt="A Light in the Attic"/></a>
        </div>
        <p class="star-rating Three"></p>
        <h3><a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the ...</a></h3>
        <div class="product_price">
            <p class="price_color">£51.77</p>
        </div>
    </article>
    <ul class="pager">
        <li class="next"><a href="catalogue/page-2.html">next</a></li>
    </ul>
</body>
</html>
"""

HTML_QUOTES_SAMPLE = """
<html>
<body>
    <div class="quote">
        <span class="text">“The world as we have created it is a process of our thinking.”</span>
        <span>by <small class="author">Albert Einstein</small>
        <a href="/author/Albert-Einstein">(about)</a>
        </span>
        <div class="tags">
            <a class="tag" href="/tag/change/page/1/">change</a>
            <a class="tag" href="/tag/deep-thoughts/page/1/">deep-thoughts</a>
        </div>
    </div>
    <ul class="pager">
        <li class="next"><a href="/page/2/">Next <span aria-hidden="true">&rarr;</span></a></li>
    </ul>
</body>
</html>
"""


def test_books_scraper_parsing():
    scraper = BooksScraper()
    records, next_url = scraper.parse_page(HTML_BOOKS_SAMPLE, "https://books.toscrape.com/index.html")

    assert len(records) == 1
    rec = records[0]
    assert rec["name_or_title"] == "A Light in the Attic"
    assert rec["price"] == "£51.77"
    assert "Three" in rec["rating"]
    assert rec["source"] == "Books to Scrape"
    assert rec["source_url"] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_quotes_scraper_parsing():
    scraper = QuotesScraper()
    records, next_url = scraper.parse_page(HTML_QUOTES_SAMPLE, "https://quotes.toscrape.com/")

    assert len(records) == 1
    rec = records[0]
    assert "“The world as we have created it" in rec["name_or_title"]
    assert rec["author"] == "Albert Einstein"
    assert rec["tags"] == ["change", "deep-thoughts"]
    assert rec["source"] == "Quotes to Scrape"
    assert rec["source_url"] == "https://quotes.toscrape.com/author/Albert-Einstein"
    assert next_url == "https://quotes.toscrape.com/page/2/"
