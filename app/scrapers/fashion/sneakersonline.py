"""Sneakersonline scraper — Playwright (ikas.com headless commerce platformu).

sneakersonline.com.tr, ikas.com altyapısını kullanır.
Ürün kartları JS ile render edilir; Playwright ile tam veri çekilir.

Kart yapısı (Playwright-rendered):
  div[data-id]
    └── a[href]           → ürün URL'si
         ├── img           → görsel (src), ürün adı (alt)
         └── .price-main
              ├── .discount-percent  → indirim %
              └── span, span         → eski fiyat, yeni fiyat
"""
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.playwright_base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://sneakersonline.com.tr'
_CARD_SEL = 'div[data-id]'
_READY_SEL = 'div[data-id] > a[href]'


class SneakersonlineScraper(PlaywrightBaseScraper):

    def _scrape_page(self, page, target) -> list[dict]:
        self.load_page(page, target.url)
        try:
            page.wait_for_selector(_READY_SEL, timeout=15_000)
        except Exception:
            logger.warning("Sneakersonline: ürün kartları yüklenmedi (%s)", target.url)

        self.scroll_load(page, times=8, pause=2)
        html = page.content()

        soup = BeautifulSoup(html, 'lxml')
        cards = soup.select(_CARD_SEL)

        if not cards:
            logger.warning("Sneakersonline: kart bulunamadı — %s", target.url)
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_card(card, category))]
        logger.info("Sneakersonline: %d ürün (%s)", len(products), target.url)
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        link = card.select_one('a[href]')
        if not link:
            return None
        product_url = urljoin(BASE_URL, link.get('href', ''))

        img = link.select_one('img.category-products-image, img[alt]')
        name = img.get('alt', '').strip() if img else ''
        if not name:
            return None

        image_url = img.get('src', '') if img else ''

        # Fiyat yapısı: .price-main içinde ilk iki span = eski fiyat, yeni fiyat
        price_main = link.select_one('.price-main, .discount-price-main')
        current_price = old_price = None
        if price_main:
            # discount-percent span'larını ve % içeren span'ları filtrele;
            # iç içe span'lardan kaynaklanan tekrarları kaldır (seen set ile)
            seen: set[str] = set()
            price_spans: list[str] = []
            for s in price_main.select('span'):
                cls = ' '.join(s.get('class') or [])
                t = s.get_text(strip=True)
                if t and 'discount-percent' not in cls and '%' not in t and t not in seen:
                    price_spans.append(t)
                    seen.add(t)
            if len(price_spans) >= 2:
                old_price = self.normalize_price(price_spans[0])
                current_price = self.normalize_price(price_spans[1])
            elif len(price_spans) == 1:
                current_price = self.normalize_price(price_spans[0])

        if not current_price:
            return None

        discount_pct = self.calc_discount(old_price, current_price)

        # İndirim rozeti
        disc_el = link.select_one('.discount-percent')
        if disc_el and discount_pct is None:
            m = re.search(r'(\d+)', disc_el.get_text())
            if m:
                discount_pct = float(m.group(1))

        # Sadece indirimli ürünler
        if discount_pct is None:
            return None

        external_id = card.get('data-id', '') or self._extract_id(product_url)

        # Marka: ürün adının ilk kelimesi (Nike, Adidas, New Balance vb.)
        brand = name.split()[0] if name else None

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': discount_pct,
            'product_url': product_url,
            'image_url': image_url,
            'brand': brand,
            'category': category or 'Sneaker',
            'stock_status': 'in_stock',
            'external_id': str(external_id),
            'vertical': 'fashion',
            'gender': self.detect_gender(name, product_url),
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _extract_id(self, url: str) -> str:
        return url.split('?')[0].rstrip('/').split('/')[-1]
