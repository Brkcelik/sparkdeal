"""Superstep scraper — requests + BeautifulSoup.

Superstep, Next.js + Tailwind CSS kullanır.
Ürün verileri client-side fetch ile yüklenir; statik HTML'de ürün kartı yoktur.
Bu scraper gelecekte Playwright veya XHR endpoint keşfiyle tamamlanacak (Faz 7/8).
"""
import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.superstep.com.tr'

# Superstep'in dahili API'si — keşfedilirse buraya eklenir
_LISTING_API = None


class SuperstepScraper(BaseScraper):

    def scrape(self, target) -> list[dict]:
        # Eğer dahili API endpoint'i keşfedilmişse onu kullan
        if _LISTING_API:
            return self._scrape_api(target)
        return self._scrape_html(target)

    def _scrape_html(self, target) -> list[dict]:
        session = self.make_session()
        self.warm_session(session, BASE_URL)

        try:
            r = session.get(target.url, timeout=15)
        except Exception as exc:
            logger.error("Superstep bağlantı hatası: %s", exc)
            return []

        if r.status_code != 200:
            logger.error("Superstep HTTP %s: %s", r.status_code, target.url)
            return []

        soup = BeautifulSoup(r.text, 'lxml')

        # Next.js + Tailwind: sabit class isimleri yok — data-* attribute veya
        # yapısal selektörlerle dene
        cards = (
            soup.select('[data-product-id]')
            or soup.select('[data-testid*="product"]')
            or soup.select('article')
        )

        if not cards:
            logger.warning(
                "Superstep: ürün kartı bulunamadı — Next.js client-side render. "
                "Playwright gerekiyor (Faz 8)."
            )
            return []

        category = getattr(target, 'category', None)
        products = []
        for card in cards:
            parsed = self._parse_card(card, category)
            if parsed:
                products.append(parsed)

        logger.info("Superstep: %d ürün bulundu", len(products))
        return products

    def _scrape_api(self, target) -> list[dict]:
        try:
            r = requests.get(_LISTING_API, timeout=15)
            r.raise_for_status()
            items = r.json()
        except Exception as exc:
            logger.error("Superstep API hatası: %s", exc)
            return []
        return [self._parse_api_item(item) for item in items if item]

    def _parse_card(self, card, category=None) -> dict | None:
        link = card.select_one('a[href]')
        if not link:
            return None
        product_url = urljoin(BASE_URL, link.get('href', ''))
        external_id = card.get('data-product-id') or self._extract_id(product_url)

        name_el = card.select_one('h2') or card.select_one('h3') or card.select_one('[data-testid*="name"]')
        name = name_el.get_text(strip=True) if name_el else link.get('title', '').strip()
        if not name:
            return None

        img = card.select_one('img')
        image_url = img.get('src') or img.get('data-src') or '' if img else ''

        return {
            'name': name,
            'current_price': None,
            'old_price': None,
            'discount_percent': None,
            'product_url': product_url,
            'image_url': image_url,
            'brand': None,
            'category': category,
            'stock_status': 'in_stock',
            'external_id': external_id,
            'vertical': 'fashion',
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _parse_api_item(self, item: dict) -> dict | None:
        return None  # API keşfedilince doldurulacak

    def _extract_id(self, url: str) -> str:
        m = re.search(r'/(\d+)(?:[?/]|$)', url)
        return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
