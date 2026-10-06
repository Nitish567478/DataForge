from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class QuotesScraper(BaseScraper):
    DEFAULT_START_URL = "https://quotes.toscrape.com/"
    SOURCE_NAME = "Quotes to Scrape"

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

    def parse_quote_div(self, quote_div: BeautifulSoup, page_url: str) -> Optional[Dict]:
        try:
            text_tag = quote_div.select_one("span.text")
            raw_text = text_tag.get_text() if text_tag else None

            author_tag = quote_div.select_one("small.author")
            author = author_tag.get_text(strip=True) if author_tag else None

            author_link_tag = quote_div.select_one("a[href*='/author/']")
            source_url = page_url
            if author_link_tag and author_link_tag.get("href"):
                source_url = urljoin(page_url, author_link_tag["href"])

            tag_elements = quote_div.select("a.tag")
            raw_tags = [tag.get_text(strip=True) for tag in tag_elements if tag.get_text(strip=True)]

            return {
                "source": self.SOURCE_NAME,
                "source_url": source_url,
                "name_or_title": raw_text,
                "category": None,
                "price": None,
                "rating": None,
                "author": author,
                "tags": raw_tags,
                "description": None,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            self.logger.warning("Error parsing quote div on %s: %s", page_url, exc)
            return None

    def parse_page(self, html: str, page_url: str) -> tuple[List[Dict], Optional[str]]:
        soup = BeautifulSoup(html, "lxml")
        quotes = soup.select("div.quote")
        records = []

        for quote_div in quotes:
            record = self.parse_quote_div(quote_div, page_url)
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

            self.logger.info("Quotes Scraper -> Page %d: %s", page_num, current_url)
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
