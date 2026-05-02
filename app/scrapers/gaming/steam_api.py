"""Steam Store scraper — arama sayfasini HTML olarak parse eder.

Steam'in indirim sayfasi (`search/?specials=1&cc=tr`) statik HTML'de
isim, gorsel, fiyat ve indirim bilgilerini dogrudan icerir.
appdetails API'si gerekli degil — sayfa basina 50 urun, max 3 sayfa.
"""
import logging
import re
import time
import requests
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_SEARCH_URL = 'https://store.steampowered.com/search/?specials=1&cc=tr&l=turkish&start={start}'
_FEATURED_URL = 'https://store.steampowered.com/api/featuredcategories/?cc=tr&l=turkish'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'tr-TR,tr;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

MAX_PAGES = 3      # 3 x 50 = max 150 urun
PAGE_DELAY = 1.5   # Steam rate limit icin bekleme (saniye)


class SteamScraper(BaseScraper):
    """Steam arama sayfasindan indirimli oyunlari ceker."""

    def scrape(self, target) -> list[dict]:
        products = self._scrape_search_pages()

        if not products:
            logger.warning("Steam HTML bos dondu, featuredcategories yedegine geciliyor")
            return self._scrape_featured()

        logger.info("Steam: %d indirimli oyun bulundu", len(products))
        return products

    # ------------------------------------------------------------------
    # Birincil: HTML arama sayfasi
    # ------------------------------------------------------------------
    def _scrape_search_pages(self) -> list[dict]:
        products = []
        seen: set[str] = set()

        for page in range(MAX_PAGES):
            start = page * 50
            url = _SEARCH_URL.format(start=start)
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                r.raise_for_status()
            except Exception as exc:
                logger.error("Steam HTML hatasi (start=%d): %s", start, exc)
                break

            soup = BeautifulSoup(r.text, 'lxml')
            cards = soup.select('a.search_result_row[data-ds-appid]')
            if not cards:
                break

            for card in cards:
                parsed = self._parse_card(card)
                if parsed and parsed['external_id'] not in seen:
                    seen.add(parsed['external_id'])
                    products.append(parsed)

            if len(cards) < 50:
                break  # son sayfa

            time.sleep(PAGE_DELAY)

        return products

    def _parse_card(self, card) -> dict | None:
        appid = card.get('data-ds-appid', '').strip()
        if not appid:
            return None

        # Indirim blogu yoksa veya indirim 0 ise atla
        discount_block = card.select_one('.discount_block')
        if not discount_block:
            return None
        discount_str = discount_block.get('data-discount', '0')
        try:
            discount = int(discount_str)
        except ValueError:
            return None
        if not discount:
            return None

        # Isim
        title_el = card.select_one('.title') or card.select_one('.search_name span')
        if not title_el:
            return None
        name = title_el.get_text(strip=True)
        if not name:
            return None

        # Gorsel
        img = card.select_one('img')
        image_url = (img.get('src') or img.get('data-src') or '') if img else ''

        # Fiyat: data-price-final en kucuk birim cinsinden
        final_cents = int(discount_block.get('data-price-final', 0) or 0)

        # Eski fiyat metinden al
        orig_el = card.select_one('.discount_original_price')
        orig_text = orig_el.get_text(strip=True) if orig_el else ''

        # Para birimini belirle: TL veya $ veya EUR
        final_el = card.select_one('.discount_final_price')
        final_text = (final_el.get_text(strip=True) if final_el else '').replace(' ', ' ')

        currency, current_price, old_price = self._parse_price(
            final_text, orig_text, final_cents
        )

        if not current_price:
            return None

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': float(discount),
            'product_url': f'https://store.steampowered.com/app/{appid}/',
            'image_url': image_url,
            'brand': None,
            'category': 'Oyun',
            'stock_status': 'in_stock',
            'external_id': appid,
            'vertical': 'gaming',
            'platform': 'PC',
            'region': 'TR',
            'edition': 'Standard',
            'currency': currency,
        }

    def _parse_price(
        self, final_text: str, orig_text: str, final_cents: int
    ) -> tuple[str, float | None, float | None]:
        """Para birimini belirle ve decimal degerlere donustur."""
        # Para birimini metin uzerinden tespit et
        if '₺' in final_text or ' TL' in final_text or final_text.endswith('TL'):
            currency = 'TRY'
        elif final_text.startswith('$') or 'USD' in final_text:
            currency = 'USD'
        elif final_text.startswith('€') or 'EUR' in final_text:
            currency = 'EUR'
        else:
            currency = 'USD'  # Steam TR varsayilan

        # final_cents / 100 → ondalikli deger
        current_price = round(final_cents / 100, 2) if final_cents else None

        # Eski fiyat metinden parse et
        old_price = self._extract_amount(orig_text)

        return currency, current_price, old_price

    def _extract_amount(self, text: str) -> float | None:
        """'$19.99', '199,00 TL', '€14,99' gibi metinlerden float cikart."""
        cleaned = re.sub(r'[₺$€TLUSDAEUReur\s]', '', text).strip()
        if not cleaned:
            return None
        # Hem Turk formatina (1.299,90) hem US formatina ($14.99) karsilik gelsin
        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned and '.' not in cleaned:
            # 19,99 → US format olabilir (kusuratli) ya da TR kusuratli
            # Virgulden sonra 2 hane varsa kusuratli say
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Yedek: featuredcategories (az urun, USD)
    # ------------------------------------------------------------------
    def _scrape_featured(self) -> list[dict]:
        try:
            r = requests.get(
                _FEATURED_URL,
                headers={**HEADERS, 'Accept': 'application/json'},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            logger.error("Steam featuredcategories hatasi: %s", exc)
            return []

        products = []
        seen: set[str] = set()

        for section_key in ('specials', 'top_sellers', 'new_releases', 'coming_soon'):
            for item in data.get(section_key, {}).get('items', []):
                parsed = self._parse_featured_item(item)
                if parsed and parsed['external_id'] not in seen:
                    seen.add(parsed['external_id'])
                    products.append(parsed)

        logger.info("Steam featured (yedek): %d urun", len(products))
        return products

    def _parse_featured_item(self, item: dict) -> dict | None:
        discount = item.get('discount_percent', 0)
        if not discount:
            return None

        final_raw = item.get('final_price', 0)
        original_raw = item.get('original_price', 0)

        current_price = round(final_raw / 100, 2) if final_raw else None
        old_price = round(original_raw / 100, 2) if original_raw else None

        if not current_price:
            return None

        appid = item.get('id')
        name = (item.get('name') or '').strip()
        if not name:
            return None

        image_url = item.get('header_image') or item.get('large_capsule_image') or ''

        return {
            'name': name,
            'current_price': current_price,
            'old_price': old_price,
            'discount_percent': float(discount),
            'product_url': f'https://store.steampowered.com/app/{appid}/',
            'image_url': image_url,
            'brand': None,
            'category': 'Oyun',
            'stock_status': 'in_stock',
            'external_id': str(appid),
            'vertical': 'gaming',
            'platform': 'PC',
            'region': 'TR',
            'edition': 'Standard',
            'currency': 'USD',
        }
