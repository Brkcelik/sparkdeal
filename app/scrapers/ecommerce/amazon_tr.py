"""Amazon TR scraper — requests + BeautifulSoup.

Bot koruması aktifse (captcha / 503) sessizce [] döner ve uyarı loglar.
Playwright entegrasyonu gerekirse PlaywrightBaseScraper'a taşınabilir.
"""
import logging
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.amazon.com.tr'

_AMAZON_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
}


class AmazonTRScraper(BaseScraper):

    def scrape(self, target) -> list[dict]:
        session = self.make_session()
        session.headers.update(_AMAZON_HEADERS)

        try:
            session.get(BASE_URL, timeout=15)
            time.sleep(2)
        except Exception:
            pass

        try:
            r = session.get(target.url, timeout=20)
        except Exception as exc:
            logger.error("Amazon TR bağlantı hatası: %s", exc)
            return []

        if r.status_code == 503 or 'Robot Check' in r.text or 'captcha' in r.text.lower():
            logger.warning("Amazon TR: bot koruması aktif — Playwright ile deneyebilirsiniz.")
            return []

        if r.status_code != 200:
            logger.error("Amazon TR HTTP %s: %s", r.status_code, target.url)
            return []

        soup = BeautifulSoup(r.text, 'lxml')
        cards = (
            soup.select('[data-asin][data-component-type="s-search-result"]')
            or soup.select('.s-result-item[data-asin]')
        )

        if not cards:
            logger.warning("Amazon TR: ürün kartı bulunamadı — sayfa yapısı değişmiş veya bot koruması aktif")
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_card(card, category))]
        logger.info("Amazon TR: %d ürün", len(products))
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        asin = card.get('data-asin', '').strip()
        if not asin:
            return None

        link = card.select_one('h2 a') or card.select_one('a.a-link-normal')
        if not link:
            return None

        href = link.get('href', '')
        product_url = (BASE_URL + href.split('?')[0]) if href.startswith('/') else href.split('?')[0]

        name_el = card.select_one('h2 span') or card.select_one('.a-size-medium')
        name = name_el.get_text(strip=True) if name_el else ''
        if not name:
            return None

        # Amazon fiyat: .a-price-whole + .a-price-fraction
        price_whole = card.select_one('.a-price-whole')
        price_frac = card.select_one('.a-price-fraction')
        current_price = None
        if price_whole:
            whole = price_whole.get_text(strip=True).replace('.', '').replace(',', '')
            frac = price_frac.get_text(strip=True) if price_frac else '00'
            try:
                current_price = round(float(f"{whole}.{frac}"), 2)
            except ValueError:
                current_price = self.normalize_price(price_whole.get_text())
        if not current_price:
            return None

        old_price_el = (
            card.select_one('.a-text-strike')
            or card.select_one('[data-a-strike="true"] span')
        )
        old_price = self.normalize_price(old_price_el.get_text()) if old_price_el else None

        discount = self.calc_discount(old_price, current_price)
        badge_el = card.select_one('.s-coupon-unclipped span') or card.select_one('[class*="badge"]')
        if badge_el and discount is None:
            m = re.search(r'(\d+)\s*%', badge_el.get_text())
            if m:
                discount = float(m.group(1))

        img = card.select_one('img.s-image') or card.select_one('img[src]')
        image_url = img.get('src', '') if img else ''

        brand_el = card.select_one('.a-size-base-plus')
        brand = brand_el.get_text(strip=True) if brand_el else None

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': discount,
            'product_url': product_url,
            'image_url': image_url,
            'brand': brand,
            'category': category,
            'stock_status': 'in_stock',
            'external_id': asin,
            'vertical': 'ecommerce',
            'platform': None,
            'region': None,
            'edition': None,
        }
