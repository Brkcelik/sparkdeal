"""Bershka TR scraper — Playwright (Inditex altyapısı).

Bershka, Inditex grubuna aittir ve dinamik içerik yükler.
Sale/indirim sayfası Playwright ile açılır, ürünler parse edilir.
"""
import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.playwright_base import PlaywrightBaseScraper

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.bershka.com'

_CARD_SELECTORS = [
    '[class*="product-grid-item"]',
    '[class*="productitem"]',
    '[class*="product-item"]',
    '[data-product-id]',
    'article[class*="product"]',
    'li[class*="product"]',
]


class BershkaScraper(PlaywrightBaseScraper):

    def _scrape_page(self, page, target) -> list[dict]:
        self.load_page(page, target.url)
        self.scroll_load(page, times=5, pause=2)
        html = page.content()
        return _parse_inditex_html(html, target, BASE_URL, 'Bershka', self)


def _parse_inditex_html(html: str, target, base_url: str, brand_name: str, scraper) -> list[dict]:
    """Inditex HTML'inden ürün kartlarını parse et (Bershka ve Pull&Bear için ortak)."""
    soup = BeautifulSoup(html, 'lxml')

    cards = []
    for sel in _CARD_SELECTORS:
        cards = soup.select(sel)
        if cards:
            break

    if not cards:
        logger.warning("%s: ürün kartı bulunamadı (%s)", brand_name, target.url)
        return []

    category = getattr(target, 'category', None)
    products = [p for card in cards if (p := _parse_card(card, category, base_url, brand_name, scraper))]
    logger.info("%s: %d ürün", brand_name, len(products))
    return products


def _parse_card(card, category, base_url: str, brand_name: str, scraper) -> dict | None:
    link = card if card.name == 'a' else card.select_one('a[href]')
    if not link:
        return None
    product_url = urljoin(base_url, link.get('href', ''))
    external_id = card.get('data-product-id') or _extract_id(product_url)

    name_el = (
        card.select_one('[class*="product-name"]')
        or card.select_one('[class*="productName"]')
        or card.select_one('[class*="item-title"]')
        or card.select_one('h2')
        or card.select_one('h3')
    )
    name = name_el.get_text(strip=True) if name_el else link.get('title', '').strip()
    if not name:
        return None

    price_el = (
        card.select_one('[class*="price--sale"]')
        or card.select_one('[class*="sale-price"]')
        or card.select_one('[class*="current-price"]')
        or card.select_one('[class*="new-price"]')
    )
    old_el = (
        card.select_one('[class*="price--compare"]')
        or card.select_one('[class*="old-price"]')
        or card.select_one('[class*="regular-price"]')
        or card.select_one('del')
        or card.select_one('s')
    )

    current_price = scraper.normalize_price(price_el.get_text() if price_el else '')
    old_price = scraper.normalize_price(old_el.get_text() if old_el else '')
    if not current_price:
        return None

    discount = scraper.calc_discount(old_price, current_price)

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
        'brand': brand_name,
        'category': category or 'Giyim',
        'stock_status': 'in_stock',
        'external_id': external_id,
        'vertical': 'fashion',
        'gender': scraper.detect_gender(name, product_url),
        'platform': None,
        'region': None,
        'edition': None,
    }


def _extract_id(url: str) -> str:
    m = re.search(r'/(\d{6,})(?:[?/.]|$)', url)
    return m.group(1) if m else url.split('?')[0].rstrip('/').split('/')[-1]
