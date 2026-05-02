"""Playwright tabanlı scraper base sınıfı.

Kurulum (bir kez çalıştır):
    pip install playwright
    playwright install chromium
"""
import logging
import time
from abc import abstractmethod
from typing import Optional

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en-US', 'en']});
window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}, app: {}};
"""

_BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
]


class PlaywrightBaseScraper(BaseScraper):
    """Playwright gerektiren scraper'lar bu sınıftan türetilir.

    Alt sınıflar `_scrape_page(page, target)` metodunu uygulamalıdır.
    """

    HEADLESS = True
    PAGE_TIMEOUT = 30_000  # ms

    def scrape(self, target) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error(
                "Playwright kurulu değil. "
                "'pip install playwright && playwright install chromium' çalıştırın."
            )
            return []

        results = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.HEADLESS, args=_BROWSER_ARGS)
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                ),
                locale='tr-TR',
                timezone_id='Europe/Istanbul',
                extra_http_headers={'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8'},
            )
            context.add_init_script(_STEALTH_SCRIPT)
            page = context.new_page()
            try:
                results = self._scrape_page(page, target)
            except Exception as exc:
                logger.error("%s Playwright hatası: %s", self.__class__.__name__, exc)
            finally:
                context.close()
                browser.close()
        return results

    @abstractmethod
    def _scrape_page(self, page, target) -> list[dict]:
        raise NotImplementedError

    def load_page(self, page, url: str, wait_selector: Optional[str] = None) -> str:
        """URL yükle, isteğe bağlı seçiciyi bekle, HTML döndür."""
        page.goto(url, wait_until='domcontentloaded', timeout=self.PAGE_TIMEOUT)
        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=self.PAGE_TIMEOUT)
            except Exception:
                logger.warning("Selector bekleme zaman aşımı: %s", wait_selector)
        time.sleep(self.delay)
        return page.content()

    def scroll_load(self, page, times: int = 3, pause: float = 1.5) -> None:
        """Lazy-loaded içerik için sayfayı aşağı kaydır."""
        for _ in range(times):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(pause)
