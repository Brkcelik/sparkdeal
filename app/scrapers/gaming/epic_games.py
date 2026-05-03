"""Epic Games Store scraper — iki kaynak birleşimi:

1. freeGamesPromotions REST endpoint → bedava/promosyon oyunları
2. Playwright ile browse sayfası → genel indirimli oyunlar
   (browse sayfası __NEXT_DATA__ içinde oyun listesini JSON olarak gömüyor)
"""
import json
import logging
import time
import re
import requests
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_FREE_GAMES_URL = (
    'https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions'
    '?locale=tr&country=TR&allowCountries=TR'
)
_BROWSE_URL = (
    'https://store.epicgames.com/tr/browse'
    '?sortBy=discount&sortDir=DESC&onSale=true&count=40&start={start}'
)
_STORE_BASE = 'https://store.epicgames.com/tr/p/'

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Accept': 'application/json, text/html, */*',
    'Referer': 'https://store.epicgames.com/',
}

_IMAGE_PRIORITY = ('DieselGameBoxWide', 'OfferImageWide', 'DieselStoreFrontWide', 'Thumbnail')
_MAX_PAGES = 10
_PAGE_DELAY = 1.5


class EpicGamesScraper(BaseScraper):
    """Epic Games Store'dan indirimli oyunları çeker."""

    def scrape(self, target) -> list[dict]:
        products: list[dict] = []
        seen: set[str] = set()

        # 1. Önce bedava promo oyunları
        free = self._scrape_free_games()
        for p in free:
            if p['external_id'] not in seen:
                seen.add(p['external_id'])
                products.append(p)

        # 2. Playwright ile genel indirimli oyunlar
        pw_products = self._scrape_with_playwright(seen)
        products.extend(pw_products)

        logger.info('Epic Games: %d oyun bulundu (%d bedava, %d genel)',
                    len(products), len(free), len(pw_products))
        return products

    # ──────────────────────────────────────────────
    # 1. REST endpoint: bedava/promo oyunlar
    # ──────────────────────────────────────────────

    def _scrape_free_games(self) -> list[dict]:
        try:
            r = requests.get(_FREE_GAMES_URL, headers=_HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            logger.warning('Epic Games freeGamesPromotions hatasi: %s', exc)
            return []

        elements = (
            data.get('data', {})
                .get('Catalog', {})
                .get('searchStore', {})
                .get('elements', [])
        )

        products = []
        for item in elements:
            parsed = self._parse_promo_item(item)
            if parsed:
                products.append(parsed)

        return products

    def _parse_promo_item(self, item: dict) -> dict | None:
        title = (item.get('title') or '').strip()
        epic_id = item.get('id', '').strip()
        if not title or not epic_id:
            return None

        price_info = (item.get('price') or {}).get('totalPrice', {})
        discount_raw = price_info.get('discountPrice', -1)
        original_raw = price_info.get('originalPrice', 0)

        if discount_raw < 0 or original_raw <= 0:
            return None
        if discount_raw >= original_raw:
            return None  # indirim yok

        current_price = round(discount_raw / 100, 2)
        old_price = round(original_raw / 100, 2)
        discount_percent = round((original_raw - discount_raw) / original_raw * 100, 1)
        currency = price_info.get('currencyCode', 'TRY')

        slug = item.get('productSlug') or item.get('urlSlug') or ''
        product_url = (_STORE_BASE + slug) if slug else ''
        image_url = self._pick_image(item.get('keyImages') or [])
        brand = (item.get('seller') or {}).get('name') or None

        return {
            'name': title,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': discount_percent,
            'product_url': product_url,
            'image_url': image_url,
            'brand': brand,
            'category': 'Oyun',
            'stock_status': 'in_stock',
            'external_id': epic_id,
            'vertical': 'gaming',
            'platform': 'PC',
            'region': 'TR',
            'edition': 'Standard',
            'currency': currency,
        }

    # ──────────────────────────────────────────────
    # 2. Playwright: genel indirimli oyunlar
    # ──────────────────────────────────────────────

    def _scrape_with_playwright(self, seen: set) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning('Playwright kurulu degil — Epic Games genel indirimleri atlanacak')
            return []

        products = []

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox',
                          '--disable-blink-features=AutomationControlled'],
                )
                page = browser.new_page(
                    user_agent=_HEADERS['User-Agent'],
                    locale='tr-TR',
                )
                page.add_init_script(
                    "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
                )

                for page_num in range(_MAX_PAGES):
                    start = page_num * 40
                    url = _BROWSE_URL.format(start=start)
                    try:
                        page.goto(url, wait_until='networkidle', timeout=30_000)
                    except Exception:
                        try:
                            page.goto(url, wait_until='domcontentloaded', timeout=20_000)
                        except Exception as exc:
                            logger.debug('Epic browse sayfasi yuklenmedi (start=%d): %s', start, exc)
                            break

                    # __NEXT_DATA__ içinden JSON al
                    batch = self._extract_from_next_data(page.content(), seen)
                    if not batch:
                        break

                    products.extend(batch)
                    for p in batch:
                        seen.add(p['external_id'])

                    time.sleep(_PAGE_DELAY)

                browser.close()
        except Exception as exc:
            logger.error('Epic Games Playwright hatasi: %s', exc)

        return products

    def _extract_from_next_data(self, html: str, seen: set) -> list[dict]:
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not match:
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            return []

        # Epic Games Next.js sayfa yapısında ürünler farklı yerlerde olabilir
        elements = self._find_elements_in_data(data)
        if not elements:
            return []

        products = []
        for item in elements:
            if not isinstance(item, dict):
                continue
            epic_id = item.get('id', '') or item.get('offerId', '')
            if not epic_id or epic_id in seen:
                continue
            parsed = self._parse_promo_item(item)
            if parsed:
                products.append(parsed)

        return products

    def _find_elements_in_data(self, data) -> list:
        """Nested JSON içinde elements dizisini bul."""
        if isinstance(data, dict):
            if 'elements' in data and isinstance(data['elements'], list):
                return data['elements']
            for v in data.values():
                result = self._find_elements_in_data(v)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = self._find_elements_in_data(item)
                if result:
                    return result
        return []

    # ──────────────────────────────────────────────
    # Yardımcı
    # ──────────────────────────────────────────────

    @staticmethod
    def _pick_image(key_images: list[dict]) -> str:
        by_type = {
            img['type']: img['url']
            for img in key_images
            if img.get('type') and img.get('url')
        }
        for t in _IMAGE_PRIORITY:
            if t in by_type:
                return by_type[t]
        return next(iter(by_type.values()), '')
