"""Pull&Bear TR scraper — Playwright (Inditex altyapısı).

Bershka ile aynı Inditex altyapısını kullanır; parse mantığı paylaşılır.
"""
import logging

from app.scrapers.playwright_base import PlaywrightBaseScraper
from app.scrapers.fashion.bershka import _parse_inditex_html

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.pullandbear.com'


class PullandbearScraper(PlaywrightBaseScraper):

    def _scrape_page(self, page, target) -> list[dict]:
        self.load_page(page, target.url)
        self.scroll_load(page, times=5, pause=2)
        html = page.content()
        return _parse_inditex_html(html, target, BASE_URL, 'Pull&Bear', self)
