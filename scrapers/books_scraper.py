from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BooksScraper(BaseScraper):
    DEFAULT_START_URL = "https://books.toscrape.com/index.html"
    SOURCE_NAME = "Books to Scrape"

    def __init__(
        self,
        start_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
        request_delay: float = 0.5,
        timeout: int = 15,
    ):
        super().__init__(
            base_url=start_url or self.DEFAULT_START_URL,
            source_name=self.SOURCE_NAME,
            session=session,
            request_delay=request_delay,
            timeout=timeout,
        )

    def parse_book_pod(self, article: BeautifulSoup, page_url: str) -> Optional[Dict]:
        try:
            link_tag = article.select_one("h3 > a")
            title = None
            href = None
            if link_tag:
                title = link_tag.get("title") or link_tag.get_text(strip=True)
                raw_href = link_tag.get("href")
                if raw_href:
                    href = urljoin(page_url, raw_href)

            price_tag = article.select_one("p.price_color")
            price_raw = price_tag.get_text(strip=True) if price_tag else None

            rating_tag = article.select_one("p.star-rating")
            rating_raw = " ".join(rating_tag.get("class", [])) if rating_tag else None

            return {
                "source": self.SOURCE_NAME,
                "source_url": href,
                "name_or_title": title,
                "category": None,
                "price": price_raw,
                "rating": rating_raw,
                "author": None,
                "tags": None,
                "description": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            self.logger.warning("Error parsing book pod on %s: %s", page_url, exc)
            return None

    def parse_page(self, html: str, page_url: str) -> tuple[List[Dict], Optional[str]]:
        soup = BeautifulSoup(html, "lxml")
        articles = soup.select("article.product_pod")
        records = []

        for article in articles:
            record = self.parse_book_pod(article, page_url)
            if record:
                records.append(record)

        next_tag = soup.select_one("li.next > a")
        next_url = None
        if next_tag and next_tag.get("href"):
            next_url = urljoin(page_url, next_tag["href"])

        return records, next_url

    def scrape(self, max_pages: Optional[int] = None) -> List[Dict]:
        records: List[Dict] = []
        current_url: Optional[str] = self.base_url
        page_num = 1

        self.logger.info("Starting crawl for %s at %s", self.source_name, current_url)

        while current_url:
            if max_pages is not None and page_num > max_pages:
                self.logger.info("Reached maximum page limit (%d). Stopping.", max_pages)
                break

            self.logger.info("Books Scraper -> Page %d: %s", page_num, current_url)
            html = self.fetch_page(current_url)
            if not html:
                self.logger.error("Failed to retrieve content for %s. Stopping source crawl.", current_url)
                break

            page_records, next_url = self.parse_page(html, current_url)
            records.extend(page_records)
            self.logger.info("Extracted %d records from page %d (Total so far: %d)", len(page_records), page_num, len(records))

            current_url = next_url
            page_num += 1

            if current_url:
                self.sleep_polite()

        self.logger.info("Completed crawl for %s. Total raw records: %d across %d pages", self.source_name, len(records), page_num - 1)
        return records
