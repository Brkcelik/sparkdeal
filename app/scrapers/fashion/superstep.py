"""Superstep scraper — Playwright (Next.js SSR, Tailwind CSS).

Kart yapısı (Playwright-rendered):
  [data-testid*="product"]
    └── a[href]           → ürün URL'si
         ├── img           → görsel (src), ürün adı (alt)
         ├── span.line-through  → eski fiyat
         └── span[class*="text-primary"]  → güncel fiyat
"""
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.playwright_base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.superstep.com.tr'
_CARD_SEL = '[data-testid*="product"]'
_READY_SEL = '[data-testid*="product"] a[href]'


class SuperstepScraper(PlaywrightBaseScraper):

    MAX_PAGES = 10
    PAGINATION_PARAM = 'page'

    def _scrape_page(self, page, target) -> list[dict]:
        self.load_page(page, target.url)
        try:
            page.wait_for_selector(_READY_SEL, timeout=15_000)
        except Exception:
            logger.warning("Superstep: ürün kartları yüklenmedi (%s)", target.url)

        self.scroll_load(page, times=4, pause=2)
        html = page.content()

        soup = BeautifulSoup(html, 'lxml')
        cards = soup.select(_CARD_SEL)

        if not cards:
            logger.warning("Superstep: kart bulunamadı — %s", target.url)
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_card(card, category))]
        logger.info("Superstep: %d ürün (%s)", len(products), target.url)
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        link = card.select_one('a[href]')
        if not link:
            return None
        product_url = urljoin(BASE_URL, link.get('href', ''))

        img = card.select_one('img[alt]')
        name = img.get('alt', '').strip() if img else ''
        if not name:
            return None

        image_url = ''
        if img:
            image_url = img.get('src') or img.get('data-src') or ''
            if image_url.startswith('//'):
                image_url = 'https:' + image_url

        # Eski fiyat: line-through sınıflı span
        old_el = card.select_one('span.line-through')
        old_price = self.normalize_price(old_el.get_text() if old_el else '')

        # Güncel fiyat: text-primary sınıflı span
        price_el = card.select_one('span[class*="text-primary"]')
        current_price = self.normalize_price(price_el.get_text() if price_el else '')

        # İndirim yalnızca eski fiyat mevcutsa hesaplanır
        discount = self.calc_discount(old_price, current_price)

        if current_price is None or discount is None:
            return None

        external_id = self._extract_id(product_url)

        brand_el = card.select_one('[class*="brand"], [data-testid*="brand"]')
        brand = brand_el.get_text(strip=True) if brand_el else name.split()[0] if name else None

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': discount,
            'product_url': product_url,
            'image_url': image_url,
            'brand': brand,
            'category': category or 'Spor',
            'stock_status': 'in_stock',
            'external_id': external_id,
            'vertical': 'fashion',
            'gender': self.detect_gender(name, product_url),
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _extract_id(self, url: str) -> str:
        m = re.search(r'/(\d+)(?:[?/]|$)', url)
        return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
