"""IsThereAnyDeal (ITAD) entegrasyonu — Steam oyunları için tarihsel fiyat geçmişi.

API key: config.py içinde ITAD_API_KEY veya ITAD_API_KEY ortam değişkeni.
Ücretsiz kayıt: https://isthereanydeal.com/dev/
"""
import logging
import time
import requests
from datetime import datetime, timezone

from app import db
from app.models.external_price_history import ExternalPriceHistory

logger = logging.getLogger(__name__)

_BASE = 'https://api.isthereanydeal.com'
_HEADERS = {'Accept': 'application/json'}
_TIMEOUT = 15


def _get_api_key() -> str | None:
    import os
    key = os.environ.get('ITAD_API_KEY')
    if key:
        return key
    try:
        from config import Config
        return getattr(Config, 'ITAD_API_KEY', None)
    except Exception:
        return None


def lookup_itad_id(steam_appid: str) -> str | None:
    """Steam appid → ITAD game UUID çöz."""
    api_key = _get_api_key()
    if not api_key:
        return None
    try:
        r = requests.get(
            f'{_BASE}/games/lookup/v1/',
            params={'key': api_key, 'appid': steam_appid},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if data.get('found') and data.get('game'):
            return data['game']['id']
        return None
    except Exception as exc:
        logger.debug('ITAD lookup hatası appid=%s: %s', steam_appid, exc)
        return None


def fetch_itad_history(product) -> int:
    """Bir Steam oyunu için ITAD tarihsel indirim geçmişini çek ve kaydet.

    Mevcut ITAD kayıtları silinerek yenilenir.
    Döndürür: kaydedilen kayıt sayısı.
    """
    if product.vertical != 'gaming' or not product.external_id:
        return 0

    api_key = _get_api_key()
    if not api_key:
        logger.warning('ITAD API key eksik. config.py içine ITAD_API_KEY ekleyin.')
        return 0

    itad_id = lookup_itad_id(str(product.external_id))
    if not itad_id:
        logger.debug('ITAD ID bulunamadı: "%s" (appid=%s)', product.name, product.external_id)
        return 0

    try:
        r = requests.get(
            f'{_BASE}/games/history/v2/',
            params={'key': api_key, 'id': itad_id},
            headers=_HEADERS,
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        entries = r.json()
    except Exception as exc:
        logger.debug('ITAD history hatası "%s": %s', product.name, exc)
        return 0

    if not isinstance(entries, list):
        logger.debug('ITAD history beklenmeyen format: %s', type(entries))
        return 0

    # Mevcut ITAD kayıtlarını temizle
    ExternalPriceHistory.query.filter_by(product_id=product.id, source='itad').delete()

    count = 0
    for entry in entries:
        try:
            shop_name = (entry.get('shop') or {}).get('name', 'Steam')
            price_obj = entry.get('price') or {}
            price = price_obj.get('amount')
            currency = price_obj.get('currency', 'USD')
            regular_obj = entry.get('regular') or {}
            regular_price = regular_obj.get('amount')
            cut = entry.get('cut')
            url = entry.get('url', '')
            ts = entry.get('timestamp', '')

            if price is None:
                continue

            if ts:
                # ISO 8601 — "2023-11-22T00:00:00Z" veya "2023-11-22T00:00:00"
                recorded_at = datetime.fromisoformat(ts.rstrip('Z')).replace(tzinfo=timezone.utc)
            else:
                recorded_at = datetime.now(timezone.utc)

            db.session.add(ExternalPriceHistory(
                product_id=product.id,
                source='itad',
                shop=shop_name,
                price=price,
                regular_price=regular_price,
                currency=currency,
                cut=cut,
                url=url,
                recorded_at=recorded_at,
            ))
            count += 1
        except Exception as exc:
            logger.debug('ITAD entry parse hatası: %s — %s', exc, entry)
            continue

    db.session.commit()
    logger.debug('ITAD: "%s" için %d kayıt kaydedildi', product.name, count)
    return count


def fetch_all_itad_history(vertical: str = 'gaming') -> dict:
    """Gaming vertical'daki tüm ürünler için ITAD geçmişini çek."""
    from app.models.product import Product

    api_key = _get_api_key()
    if not api_key:
        logger.warning('ITAD API key eksik — fetch_all_itad_history çalıştırılamıyor.')
        return {'total': 0, 'updated': 0, 'error': 'no_api_key'}

    products = Product.query.filter_by(vertical=vertical).all()
    total = len(products)
    updated = 0

    logger.info('ITAD fetch başlıyor: %d ürün', total)

    for i, product in enumerate(products, 1):
        count = fetch_itad_history(product)
        if count:
            updated += 1
        time.sleep(0.5)
        if i % 20 == 0:
            logger.info('ITAD ilerleme: %d/%d', i, total)

    logger.info('ITAD fetch tamamlandı: %d/%d ürün güncellendi', updated, total)
    return {'total': total, 'updated': updated}
