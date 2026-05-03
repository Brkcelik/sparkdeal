"""Rakip platform fiyat lookup servisi.

Steam/Epic oyunları için Eneba'da arama yapar,
bulunan fiyatları CompetitorPrice tablosuna kaydeder.

Eneba: React+Apollo SPA — ?text= parametresiyle SSR Apollo cache'de arama sonuçları gelir.
Bynogame: /tr/search?query= ile requests tabanlı arama.
"""
import json
import logging
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from app import db
from app.models.competitor_price import CompetitorPrice

logger = logging.getLogger(__name__)

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

_REQUEST_TIMEOUT = 12
_DELAY = 1.5

# Sadece oyun kategorisi — gift card, DLC, pass vs. filtrele
_SKIP_TYPES = {'TOP_UP', 'WALLET', 'GIFTCARD', 'SUBSCRIPTION', 'ADDON', 'DLC', 'GAME_POINTS'}


def _normalize_for_search(name: str) -> str:
    name = name.lower()
    name = re.sub(
        r'\b(edition|deluxe|ultimate|complete|goty|remastered|pc|ps5|ps4|xbox|definitive|standard)\b',
        '', name,
    )
    name = re.sub(r'[^\w\s]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip()[:80]


# ─────────────────────────────────────────────────────────
# Eneba — Apollo SSR cache parse (?text= parametresi ile)
# ─────────────────────────────────────────────────────────

def _lookup_eneba(game_name: str) -> dict | None:
    """Eneba'da oyun adına göre arama yap; Apollo SSR cache'den TRY fiyatını al.

    ?text= parametresi SSR'da oyun adına göre filtrelenmiş sonuçlar döndürür.
    ?q= parametresi sadece popüler ürünleri döndürür (çalışmaz).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.debug('Playwright kurulu degil — Eneba lookup atlanacak')
        return None

    query = _normalize_for_search(game_name)
    url = f'https://www.eneba.com/tr/search?text={requests.utils.quote(query)}'

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
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=20_000)
                page.wait_for_timeout(4000)
            except Exception as exc:
                logger.debug('Eneba sayfa hatasi "%s": %s', game_name, exc)
                browser.close()
                return None
            html = page.content()
            browser.close()
    except Exception as exc:
        logger.debug('Eneba Playwright hatasi "%s": %s', game_name, exc)
        return None

    return _parse_eneba_apollo(html, game_name)


def _parse_eneba_apollo(html: str, game_name: str) -> dict | None:
    """Apollo normalized cache'den en ucuz oyun fiyatını çıkar."""
    soup = BeautifulSoup(html, 'lxml')

    # En büyük script tag = Apollo cache
    cache_data = None
    for script in soup.find_all('script'):
        txt = script.get_text()
        if len(txt) > 50_000:
            try:
                cache_data = json.loads(txt)
                break
            except json.JSONDecodeError:
                continue

    if not cache_data:
        return None

    root = cache_data.get('ROOT_QUERY', {})
    # ?text= parametresiyle SSR'da text-based search key oluşur
    search_key = next((k for k in root if k.startswith('search') and '"text"' in k), None)
    if not search_key:
        logger.debug('Eneba: text-based search key bulunamadi "%s"', game_name)
        return None

    edges = root[search_key].get('results', {}).get('edges', [])
    if not edges:
        return None

    query_words = set(_normalize_for_search(game_name).split())
    best_price = None
    best_url = None

    for edge in edges:
        ref = (edge.get('node') or {}).get('__ref', '')
        product = cache_data.get(ref, {})
        if not product:
            continue

        # Gift card, DLC vb. filtrele
        product_type = (product.get('type') or {}).get('value', '')
        if product_type in _SKIP_TYPES:
            continue

        name = product.get('name', '').lower()

        # Başlık benzerliği kontrolü — arama kelimelerinin en az yarısı isimde olmalı
        if query_words:
            matched = sum(1 for w in query_words if len(w) > 3 and re.search(r'\b' + re.escape(w) + r'\b', name))
            if matched < max(1, len(query_words) // 2):
                continue

        # En ucuz auction'dan TRY fiyatını al
        auction_ref = (product.get('cheapestAuction') or {}).get('__ref', '')
        auction = cache_data.get(auction_ref, {})
        if not auction:
            continue

        price_obj = auction.get('price({"currency":"TRY"})')
        if not price_obj or not isinstance(price_obj, dict):
            continue

        amount = price_obj.get('amount')
        if amount is None or amount <= 0:
            continue

        # Eneba amount kuruş cinsinden (örn. 3071 = 30.71 TL)
        price = round(amount / 100, 2)

        slug = product.get('slug', '')
        product_url = f'https://www.eneba.com/tr/{slug}' if slug else ''

        if best_price is None or price < best_price:
            best_price = price
            best_url = product_url

    if best_price is None:
        return None

    return {'price': best_price, 'currency': 'TRY', 'url': best_url}


# ─────────────────────────────────────────────────────────
# Bynogame (requests)
# ─────────────────────────────────────────────────────────

def _lookup_bynogame(game_name: str) -> dict | None:
    """Bynogame'de oyun adına göre arama yap.

    Bynogame CD key/Steam key marketplace'idir. Doğru URL: /tr/search?query=...
    Sonuç kartları: div.list-group-item + span.searchhref[data-href] + p.font-weight-bolder
    """
    query = _normalize_for_search(game_name)
    # Daha iyi sonuç için "cd key" veya "steam key" ekle
    full_query = f'{query} cd key'
    search_url = f'https://www.bynogame.com/tr/search?query={requests.utils.quote(full_query)}'

    try:
        r = requests.get(search_url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        r.raise_for_status()
    except Exception as exc:
        logger.debug('Bynogame requests hatasi "%s": %s', game_name, exc)
        return None

    soup = BeautifulSoup(r.text, 'lxml')
    return _parse_bynogame_html(soup, game_name)


def _parse_bynogame_html(soup, game_name: str = '') -> dict | None:
    """Bynogame arama sonuç sayfasından en ucuz oyun fiyatını çıkar.

    Yapı: div.list-group-item > span.searchhref[data-href] + img[alt] + p.font-weight-bolder
    """
    query_words = set(_normalize_for_search(game_name).split()) if game_name else set()
    best_price = None
    best_url = None

    for card in soup.select('div.list-group-item'):
        # URL: span[data-href] veya a[href]
        link_el = card.select_one('span[data-href]') or card.select_one('a[href]')
        if not link_el:
            continue
        href = link_el.get('data-href') or link_el.get('href', '')
        if not href:
            continue

        # Blog yazıları ve DLC'leri atla
        href_lower = href.lower()
        if 'blog.' in href or '/news/' in href_lower:
            continue

        # Ürün adı: img[alt] veya p/span metin
        img_el = card.select_one('img[alt]')
        name = (img_el.get('alt', '') if img_el else card.get_text(' ', strip=True))
        name_lower = name.lower()

        # DLC filtresi
        if ' dlc' in name_lower or name_lower.endswith(' dlc'):
            continue

        # İsim benzerliği: sorgu kelimelerinin en az yarısı üründe olmalı (len>3 ile stop word filtresi)
        if query_words:
            matched = sum(1 for w in query_words if len(w) > 3 and re.search(r'\b' + re.escape(w) + r'\b', name_lower))
            if matched < max(1, len(query_words) // 2):
                continue

        # Fiyat: p.font-weight-bolder.h5.mb-0.ml-2
        price_el = card.select_one('p.font-weight-bolder.h5.mb-0.ml-2')
        if not price_el:
            continue
        price_text = price_el.get_text(strip=True)
        price = _parse_try_price(price_text.replace(' TL', '').replace('TL', ''))
        if price is None or price <= 0:
            continue

        if best_price is None or price < best_price:
            best_price = price
            best_url = href

    if best_price is None:
        return None
    return {'price': best_price, 'currency': 'TRY', 'url': best_url}


def _parse_try_price(text: str) -> float | None:
    cleaned = re.sub(r'[₺\s]', '', str(text)).strip()
    if not cleaned:
        return None
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        parts = cleaned.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


# ─────────────────────────────────────────────────────────
# Ana servis fonksiyonu
# ─────────────────────────────────────────────────────────

_LOOKUP_FUNCS = {
    'eneba': _lookup_eneba,
    'bynogame': _lookup_bynogame,
}


def update_competitor_prices(product) -> int:
    """Bir gaming ürünü için tüm rakip platform fiyatlarını güncelle."""
    if product.vertical != 'gaming':
        return 0

    updated = 0
    now = datetime.now(timezone.utc)

    for source_name, lookup_fn in _LOOKUP_FUNCS.items():
        result = lookup_fn(product.name)
        time.sleep(_DELAY)

        existing = (
            CompetitorPrice.query
            .filter_by(product_id=product.id, source_name=source_name)
            .first()
        )

        if result:
            if existing:
                existing.price = result['price']
                existing.currency = result['currency']
                existing.url = result['url']
                existing.checked_at = now
            else:
                db.session.add(CompetitorPrice(
                    product_id=product.id,
                    source_name=source_name,
                    price=result['price'],
                    currency=result['currency'],
                    url=result['url'],
                    checked_at=now,
                ))
            updated += 1
        else:
            if existing:
                existing.checked_at = now

    db.session.commit()
    return updated


def fetch_all_competitor_prices(vertical: str = 'gaming') -> dict:
    """Belirtilen vertical'daki tüm ürünler için rakip fiyatlarını güncelle."""
    from app.models.product import Product

    products = Product.query.filter_by(vertical=vertical).all()
    total = len(products)
    updated_products = 0

    logger.info('Rakip fiyat lookup basliyor: %d urun', total)

    for i, product in enumerate(products, 1):
        count = update_competitor_prices(product)
        if count:
            updated_products += 1
        if i % 10 == 0:
            logger.info('Ilerleme: %d/%d', i, total)

    logger.info('Rakip fiyat lookup tamamlandi: %d/%d guncellendi', updated_products, total)
    return {'total': total, 'updated': updated_products}
