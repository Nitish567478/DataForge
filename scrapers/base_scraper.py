import logging
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


def create_session(
    user_agent: str = "ScrapingAssignment/1.0 (learning project; +https://github.com/example/scraper)",
    total_retries: int = 3,
    backoff_factor: float = 1.0,
    status_forcelist: Optional[list] = None,
) -> requests.Session:
    if status_forcelist is None:
        status_forcelist = [429, 500, 502, 503, 504]

    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    })

    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class BaseScraper:
    def __init__(
        self,
        base_url: str,
        source_name: str,
        session: Optional[requests.Session] = None,
        request_delay: float = 0.5,
        timeout: int = 15,
    ):
        self.base_url = base_url
        self.source_name = source_name
        self.session = session or create_session()
        self.request_delay = request_delay
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    def fetch_page(self, url: str) -> Optional[str]:
        try:
            self.logger.debug("Fetching URL: %s", url)
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as exc:
            self.logger.error("HTTP request error for %s: %s", url, exc)
            return None
        except Exception as exc:
            self.logger.error("Unexpected error fetching %s: %s", url, exc)
            return None

    def sleep_polite(self):
        if self.request_delay > 0:
            time.sleep(self.request_delay)

    def scrape(self, max_pages: Optional[int] = None) -> list:
        raise NotImplementedError("Subclasses must implement scrape()")
