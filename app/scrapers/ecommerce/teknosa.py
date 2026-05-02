"""Teknosa scraper — requests + BeautifulSoup.

NOT: Teknosa'nın bot koruması aktif olduğunda HTTP 403 döner.
     Bu durumda scraper boş liste döndürür ve hatayı loglar.
     Tam destek için Faz 7'de Playwright entegre edilecek.
"""
import logging
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.teknosa.com'


class TeknosaScaper(BaseScraper):

    def scrape(self, target) -> list[dict]:
        session = self.make_session()
        self.warm_session(session, BASE_URL)

        try:
            r = session.get(target.url, timeout=15)
        except Exception as exc:
            logger.error("Teknosa bağlantı hatası: %s", exc)
            return []

        if r.status_code == 403:
            logger.warning("Teknosa bot koruması aktif (403). Playwright gerekebilir.")
            return []
        if r.status_code != 200:
            logger.error("Teknosa HTTP %s: %s", r.status_code, target.url)
            return []

        soup = BeautifulSoup(r.text, 'lxml')
        products = []

        # Teknosa React SSR — olası kart seçiciler (bot koruması kalkarsa çalışır)
        cards = (
            soup.select('li[class*="pr-item"]')
            or soup.select('[class*="productCard"]')
            or soup.select('[class*="product-card"]')
            or soup.select('div[class*="product-item"]')
        )

        if not cards:
            logger.warning("Teknosa: hiç ürün kartı bulunamadı — sayfa yapısı değişmiş olabilir")
            return []

        category = getattr(target, 'category', None)
        for card in cards:
            parsed = self._parse_card(card, category)
            if parsed:
                products.append(parsed)

        logger.info("Teknosa: %d ürün bulundu", len(products))
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        # Ürün linki ve external ID
        link = card.select_one('a[href*="/p-"]') or card.select_one('a[href]')
        if not link:
            return None
        product_url = urljoin(BASE_URL, link.get('href', ''))
        external_id = self._extract_id(product_url)

        # Ürün adı
        name_el = (
            card.select_one('[class*="pr-name"]')
            or card.select_one('[class*="product-title"]')
            or card.select_one('[class*="productName"]')
            or card.select_one('h3')
            or card.select_one('h2')
        )
        name = name_el.get_text(strip=True) if name_el else link.get('title', '').strip()
        if not name:
            return None

        # Fiyatlar
        current_el = (
            card.select_one('[class*="discounted-price"]')
            or card.select_one('[class*="currentPrice"]')
            or card.select_one('[class*="sale-price"]')
            or card.select_one('[class*="new-price"]')
        )
        old_el = (
            card.select_one('[class*="old-price"]')
            or card.select_one('[class*="oldPrice"]')
            or card.select_one('[class*="crossed"]')
        )
        current_price = self.normalize_price(current_el.get_text() if current_el else '')
        old_price = self.normalize_price(old_el.get_text() if old_el else '')

        if not current_price:
            return None

        discount = self.calc_discount(old_price, current_price)

        # İndirim rozeti (yazılı)
        disc_el = card.select_one('[class*="discount"]') or card.select_one('[class*="badge"]')
        if disc_el and discount is None:
            txt = disc_el.get_text(strip=True)
            m = re.search(r'(\d+)', txt)
            if m:
                discount = float(m.group(1))

        # Görsel
        img = card.select_one('img')
        image_url = ''
        if img:
            image_url = img.get('data-src') or img.get('data-lazy') or img.get('src') or ''

        # Stok
        out_el = card.select_one('[class*="out-of-stock"]') or card.select_one('[class*="outOfStock"]')
        stock_status = 'out_of_stock' if out_el else 'in_stock'

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': discount,
            'product_url': product_url,
            'image_url': image_url,
            'brand': None,
            'category': category,
            'stock_status': stock_status,
            'external_id': external_id,
            'vertical': 'ecommerce',
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _extract_id(self, url: str) -> str:
        m = re.search(r'-p-(\d+)', url)
        return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
