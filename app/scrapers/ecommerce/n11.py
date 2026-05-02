"""N11 scraper — Playwright (Vue.js SPA, fiyatlar JS ile render edilir).

Faz 3'te statik HTML'den fiyat alınamıyordu. Playwright ile JS render sonrası
tam veri çekilir.
"""
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.playwright_base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.n11.com'
_CARD_SEL = 'a.product-card, [class*="product-card"], [class*="productCard"]'


class N11Scraper(PlaywrightBaseScraper):

    def _scrape_page(self, page, target) -> list[dict]:
        self.load_page(page, target.url, wait_selector=_CARD_SEL)
        self.scroll_load(page, times=2)
        html = page.content()

        soup = BeautifulSoup(html, 'lxml')
        cards = soup.select('a.product-card') or soup.select('[class*="product-card"]')

        if not cards:
            logger.warning("N11: ürün kartı bulunamadı")
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_card(card, category))]
        logger.info("N11: %d ürün", len(products))
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        href = card.get('href', '')
        if not href:
            return None
        product_url = urljoin(BASE_URL, href)
        external_id = self._extract_id(product_url)

        name_el = (
            card.select_one('.product-card__detail-title')
            or card.select_one('[class*="product-title"]')
            or card.select_one('[class*="productTitle"]')
        )
        name = name_el.get_text(strip=True) if name_el else card.get('title', '').strip()
        if not name:
            return None

        price_el = (
            card.select_one('.product-card__detail-prices-price')
            or card.select_one('[class*="prices-price"]')
            or card.select_one('[class*="current-price"]')
            or card.select_one('[class*="salePrice"]')
        )
        old_el = (
            card.select_one('.product-card__detail-prices-old-price')
            or card.select_one('[class*="old-price"]')
            or card.select_one('[class*="oldPrice"]')
            or card.select_one('del')
            or card.select_one('s')
        )
        current_price = self.normalize_price(price_el.get_text() if price_el else '')
        old_price = self.normalize_price(old_el.get_text() if old_el else '')
        if not current_price:
            return None

        discount = self.calc_discount(old_price, current_price)
        disc_el = card.select_one('[class*="discount"]')
        if disc_el and discount is None:
            m = re.search(r'(\d+)', disc_el.get_text())
            if m:
                discount = float(m.group(1))

        img = card.select_one('img')
        image_url = ''
        if img:
            image_url = img.get('src') or img.get('data-src') or ''
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
        m = re.search(r'-(\d{8,})(?:[?/]|$)', url)
        return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
