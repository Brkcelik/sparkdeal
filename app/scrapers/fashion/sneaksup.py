"""Sneaksup scraper — Playwright (Inveon platformu, JS-rendered ürün kartları).

Sneaksup, Inveon altyapısını kullanır. Ürün kartları JS ile render edilir.
Her kartta `data-ga-impressions` JSON attribute'u fiyat, eski fiyat ve
indirim bilgisini içerir.
"""
import json
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.playwright_base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.sneaksup.com'
_CARD_SEL = '.product-grid-item-container'
_LINK_SEL = 'a.lnk-selector[href], a[class*="lnk-selector"][href], .product-image-container a[href]'


class SneaksupScraper(PlaywrightBaseScraper):

    MAX_PAGES = 5
    PAGINATION_PARAM = 'pagenumber'

    def _scrape_page(self, page, target) -> list[dict]:
        self.load_page(page, target.url)
        # Ürün kartlarının render edilmesini bekle
        try:
            page.wait_for_selector(_CARD_SEL + ' a[href]', timeout=15_000)
        except Exception:
            logger.warning("Sneaksup: ürün kartları yüklenmedi (%s)", target.url)

        self.scroll_load(page, times=3, pause=1.5)
        html = page.content()

        soup = BeautifulSoup(html, 'lxml')
        cards = soup.select(_CARD_SEL)

        if not cards:
            logger.warning("Sneaksup: kart bulunamadı — %s", target.url)
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_card(card, category))]
        logger.info("Sneaksup: %d ürün (%s)", len(products), target.url)
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        # Birincil veri kaynağı: data-ga-impressions JSON
        ga_raw = card.get('data-ga-impressions', '')
        if not ga_raw:
            ga_raw = card.get('data-enhanced-impressions', '')

        ga: dict = {}
        if ga_raw:
            try:
                ga = json.loads(ga_raw)
            except Exception:
                pass

        name = ga.get('item_name') or ga.get('name', '')
        if not name:
            return None

        current_price = None
        try:
            current_price = float(ga.get('price', ''))
        except (TypeError, ValueError):
            pass

        old_price = None
        try:
            old_price = float(ga.get('dimension5', '') or ga.get('original_price', ''))
        except (TypeError, ValueError):
            pass

        discount_pct = None
        try:
            d = ga.get('discount', '')
            if d:
                discount_pct = float(d)
        except (TypeError, ValueError):
            pass

        if not current_price:
            return None

        # Hesaplanmış indirim yok ama eski fiyat varsa hesapla
        if discount_pct is None and old_price:
            discount_pct = self.calc_discount(old_price, current_price)

        if discount_pct is None:
            return None  # İndirimde olmayan ürünü atla

        external_id = ga.get('item_id') or ga.get('dimension1') or ga.get('id', '')
        brand = ga.get('item_brand') or ga.get('brand')
        category_from_ga = ga.get('item_category') or ga.get('category') or category

        # URL
        link = card.select_one(_LINK_SEL) or card.select_one('a[href]')
        product_url = urljoin(BASE_URL, link.get('href', '')) if link else ''

        # Görsel
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
            'discount_percent': discount_pct,
            'product_url': product_url,
            'image_url': image_url,
            'brand': brand,
            'category': category_from_ga,
            'stock_status': 'in_stock',
            'external_id': str(external_id),
            'vertical': 'fashion',
            'gender': self.detect_gender(name, product_url),
            'platform': None,
            'region': None,
            'edition': None,
        }
