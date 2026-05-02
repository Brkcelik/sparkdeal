"""Trendyol scraper — Playwright (Cloudflare bot koruması için).

Trendyol çok agresif bot koruması kullanır. Playwright + stealth init
ile bypass denenir. Cloudflare engeline takılırsa found_count=0 dönecektir.
"""
import logging
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.playwright_base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.trendyol.com'
_CARD_SEL = '.p-card-chldrn-cntnr, [class*="product-card"], [class*="productCard"]'


class TrendyolScraper(PlaywrightBaseScraper):

    def _scrape_page(self, page, target) -> list[dict]:
        # Ana sayfayı önce ziyaret et — cookie ve Cloudflare handshake için
        try:
            page.goto(BASE_URL, wait_until='domcontentloaded', timeout=self.PAGE_TIMEOUT)
            time.sleep(3)
        except Exception:
            pass

        self.load_page(page, target.url, wait_selector=_CARD_SEL)
        self.scroll_load(page, times=3, pause=2)
        html = page.content()

        soup = BeautifulSoup(html, 'lxml')
        cards = (
            soup.select('.p-card-chldrn-cntnr')
            or soup.select('[class*="product-card"]')
            or soup.select('div[data-id]')
        )

        if not cards:
            logger.warning("Trendyol: ürün kartı bulunamadı — Cloudflare engeli olabilir")
            return []

        category = getattr(target, 'category', None)
        products = [p for card in cards if (p := self._parse_card(card, category))]
        logger.info("Trendyol: %d ürün", len(products))
        return products

    def _parse_card(self, card, category=None) -> dict | None:
        link = card.select_one('a[href]')
        if not link:
            return None

        href = link.get('href', '')
        product_url = href if href.startswith('http') else urljoin(BASE_URL, href)
        external_id = card.get('data-id', '') or self._extract_id(product_url)

        brand_el = (
            card.select_one('[class*="brand-name"]')
            or card.select_one('[class*="product-brand"]')
        )
        name_el = (
            card.select_one('[class*="product-name"]')
            or card.select_one('[class*="prdct-desc"]')
            or card.select_one('[class*="name"]')
            or card.select_one('h2')
            or card.select_one('h3')
        )
        brand = brand_el.get_text(strip=True) if brand_el else None
        name = name_el.get_text(strip=True) if name_el else ''
        if brand and name and not name.lower().startswith(brand.lower()):
            name = f"{brand} {name}"
        if not name:
            return None

        cur_el = (
            card.select_one('[class*="prc-box-dscntd"]')
            or card.select_one('[class*="discounted-price"]')
            or card.select_one('[class*="selling-price"]')
            or card.select_one('[class*="prc"]')
        )
        old_el = (
            card.select_one('[class*="prc-box-orgnl"]')
            or card.select_one('[class*="original-price"]')
            or card.select_one('s')
            or card.select_one('del')
        )
        current_price = self.normalize_price(cur_el.get_text() if cur_el else '')
        old_price = self.normalize_price(old_el.get_text() if old_el else '')
        if not current_price:
            return None

        discount = self.calc_discount(old_price, current_price)
        disc_el = (
            card.select_one('[class*="discount-badge"]')
            or card.select_one('[class*="badge-dscnt"]')
        )
        if disc_el and discount is None:
            m = re.search(r'(\d+)', disc_el.get_text())
            if m:
                discount = float(m.group(1))

        img = card.select_one('img[src], img[data-src]')
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
            'brand': brand,
            'category': category,
            'stock_status': 'in_stock',
            'external_id': external_id,
            'vertical': 'ecommerce',
            'platform': None,
            'region': None,
            'edition': None,
        }

    def _extract_id(self, url: str) -> str:
        m = re.search(r'-p-(\d+)', url)
        return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
