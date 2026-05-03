"""Hepsiburada scraper — Playwright (bot koruması bypass).

Faz 3'te HTTP 403 alıyordu. Playwright ile tam çalışır hale getirildi.
"""
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.playwright_base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.hepsiburada.com'
_CARD_SEL = 'li[data-test-id="product-card"], li[data-pid], [class*="productListContent-item"]'


class HepsiburadaScraper(PlaywrightBaseScraper):

    MAX_PAGES = 5
    PAGINATION_PARAM = 'sayfa'

    def _scrape_page(self, page, target) -> list[dict]:
        self.load_page(page, target.url, wait_selector=_CARD_SEL)
        self.scroll_load(page, times=3, pause=2)
        html = page.content()

        soup = BeautifulSoup(html, 'lxml')
        cards = (
            soup.select('[data-test-id="product-card"]')
            or soup.select('li[data-pid]')
            or soup.select('[class*="productListContent-item"]')
            or soup.select('[class*="productCard"]')
            or soup.select('[class*="product-card"]')
        )

        if not cards:
            logger.warning("Hepsiburada: ürün kartı bulunamadı — sayfa yapısı değişmiş olabilir")
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_card(card, category))]
        logger.info("Hepsiburada: %d ürün", len(products))
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        external_id = card.get('data-pid', '')

        link = (
            card.select_one('a[href*="/p-"]')
            or card.select_one('a[href*="hepsiburada.com"]')
            or card.select_one('a[href]')
        )
        if not link:
            return None

        product_url = urljoin(BASE_URL, link.get('href', ''))
        if not external_id:
            external_id = self._extract_id(product_url)

        name_el = (
            card.select_one('[data-test-id="product-card-name"]')
            or card.select_one('[class*="product-name"]')
            or card.select_one('[class*="productName"]')
            or card.select_one('h3')
            or card.select_one('h2')
        )
        name = name_el.get_text(strip=True) if name_el else link.get('title', '').strip()
        if not name:
            return None

        cur_el = (
            card.select_one('[data-test-id="price-current-price"]')
            or card.select_one('[class*="price-value"]')
            or card.select_one('[class*="currentPrice"]')
            or card.select_one('[itemprop="price"]')
        )
        old_el = (
            card.select_one('[data-test-id="price-original-price"]')
            or card.select_one('[class*="old-price"]')
            or card.select_one('[class*="originalPrice"]')
            or card.select_one('del')
            or card.select_one('s')
        )
        current_price = self.normalize_price(cur_el.get_text() if cur_el else '')
        old_price = self.normalize_price(old_el.get_text() if old_el else '')
        if not current_price:
            return None

        discount = self.calc_discount(old_price, current_price)
        disc_el = card.select_one('[class*="discount"]') or card.select_one('[class*="Discount"]')
        if disc_el and discount is None:
            m = re.search(r'(\d+)', disc_el.get_text())
            if m:
                discount = float(m.group(1))

        img = card.select_one('img[src], img[data-src]')
        image_url = ''
        if img:
            image_url = img.get('data-src') or img.get('src') or ''
            if image_url.startswith('//'):
                image_url = 'https:' + image_url

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': discount,
            'product_url': product_url,
            'image_url': image_url,
            'brand': None,
            'category': category,
            'stock_status': 'in_stock',
            'external_id': external_id,
            'vertical': 'ecommerce',
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _extract_id(self, url: str) -> str:
        m = re.search(r'-p-([A-Z0-9]+)', url)
        return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
