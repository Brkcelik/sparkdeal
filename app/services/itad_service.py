"""IsThereAnyDeal (ITAD) entegrasyonu — Steam oyunları için tarihsel fiyat geçmişi.

Kimlik doğrulama: OAuth2 authorization_code akışı.
- `flask itad-auth` ile tek seferlik giriş yapılır, token .env'e kaydedilir.
- Access token süresi dolunca refresh_token ile otomatik yenilenir.

Credentials: .env dosyasında (git takibinin dışında).
"""
import logging
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

from app import db
from app.models.external_price_history import ExternalPriceHistory

logger = logging.getLogger(__name__)

_BASE = 'https://api.isthereanydeal.com'
_TOKEN_URL = 'https://isthereanydeal.com/oauth/token/'
_AUTH_URL = 'https://isthereanydeal.com/oauth/authorize/'
_HEADERS = {'Accept': 'application/json'}
_TIMEOUT = 15
_REDIRECT_URI = 'http://localhost:8888/callback'
_SCOPES = 'wait_read collection_read waitlist_read game_read'

# Bellek içi token cache
_token_cache: dict = {'token': None, 'expires_at': 0.0}


def _env_path() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    return base / '.env'


def _get_env(key: str) -> str:
    """Önce os.environ, sonra .env dosyasından oku."""
    val = os.environ.get(key, '')
    if val:
        return val
    env_file = _env_path()
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            if line.startswith(key + '='):
                return line.split('=', 1)[1].strip()
    return ''


def _set_env(key: str, value: str) -> None:
    """.env dosyasında bir değeri güncelle veya ekle."""
    env_file = _env_path()
    if env_file.exists():
        lines = env_file.read_text(encoding='utf-8').splitlines()
    else:
        lines = []

    updated = False
    for i, line in enumerate(lines):
        if line.startswith(key + '='):
            lines[i] = f'{key}={value}'
            updated = True
            break
    if not updated:
        lines.append(f'{key}={value}')

    env_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    os.environ[key] = value


def _has_credentials() -> bool:
    return bool(_get_env('ITAD_ACCESS_TOKEN') or _get_env('ITAD_REFRESH_TOKEN'))


def get_auth_url() -> str:
    """Kullanıcının tarayıcıda ziyaret edeceği ITAD yetkilendirme URL'ini döndür."""
    client_id = _get_env('ITAD_CLIENT_ID')
    import urllib.parse
    params = urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'scope': _SCOPES,
        'redirect_uri': _REDIRECT_URI,
    })
    return f'{_AUTH_URL}?{params}'


def exchange_code(code: str) -> bool:
    """Authorization code'u access + refresh token'a çevir."""
    client_id = _get_env('ITAD_CLIENT_ID')
    client_secret = _get_env('ITAD_CLIENT_SECRET')

    try:
        r = requests.post(
            _TOKEN_URL,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': _REDIRECT_URI,
                'client_id': client_id,
                'client_secret': client_secret,
            },
            headers={'Accept': 'application/json'},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        access_token = data.get('access_token', '')
        refresh_token = data.get('refresh_token', '')
        expires_in = data.get('expires_in', 86400)

        if access_token:
            _set_env('ITAD_ACCESS_TOKEN', access_token)
            _set_env('ITAD_TOKEN_EXPIRY', str(int(time.time()) + expires_in))
        if refresh_token:
            _set_env('ITAD_REFRESH_TOKEN', refresh_token)

        _token_cache['token'] = access_token
        _token_cache['expires_at'] = time.time() + expires_in
        return bool(access_token)
    except Exception as exc:
        logger.error('ITAD token exchange hatası: %s', exc)
        return False


def _refresh_access_token() -> str | None:
    """Refresh token ile yeni access token al."""
    refresh_token = _get_env('ITAD_REFRESH_TOKEN')
    client_id = _get_env('ITAD_CLIENT_ID')
    client_secret = _get_env('ITAD_CLIENT_SECRET')

    if not refresh_token:
        return None

    try:
        r = requests.post(
            _TOKEN_URL,
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret,
            },
            headers={'Accept': 'application/json'},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        access_token = data.get('access_token', '')
        expires_in = data.get('expires_in', 86400)

        if access_token:
            _set_env('ITAD_ACCESS_TOKEN', access_token)
            _set_env('ITAD_TOKEN_EXPIRY', str(int(time.time()) + expires_in))
            if data.get('refresh_token'):
                _set_env('ITAD_REFRESH_TOKEN', data['refresh_token'])
            _token_cache['token'] = access_token
            _token_cache['expires_at'] = time.time() + expires_in
            return access_token
        return None
    except Exception as exc:
        logger.debug('ITAD token refresh hatası: %s', exc)
        return None


def _get_access_token() -> str | None:
    """Geçerli bir access token döndür; expire olmuşsa refresh et."""
    global _token_cache

    if _token_cache['token'] and time.time() < _token_cache['expires_at'] - 60:
        return _token_cache['token']

    # .env'den oku
    stored_token = _get_env('ITAD_ACCESS_TOKEN')
    expiry_str = _get_env('ITAD_TOKEN_EXPIRY')

    if stored_token and expiry_str:
        try:
            expiry = float(expiry_str)
            if time.time() < expiry - 60:
                _token_cache['token'] = stored_token
                _token_cache['expires_at'] = expiry
                return stored_token
        except ValueError:
            pass

    # Expire olduysa refresh et
    return _refresh_access_token()


def _request(url: str, params: dict) -> requests.Response | None:
    """Bearer token ile API isteği at."""
    token = _get_access_token()
    if not token:
        # Fallback: eski ?key= stili dene
        api_key = _get_env('ITAD_API_KEY')
        if api_key:
            return requests.get(url, params={**params, 'key': api_key}, headers=_HEADERS, timeout=_TIMEOUT)
        return None

    hdrs = {**_HEADERS, 'Authorization': f'Bearer {token}'}
    return requests.get(url, params=params, headers=hdrs, timeout=_TIMEOUT)


def lookup_itad_id(steam_appid: str) -> str | None:
    """Steam appid → ITAD game UUID çöz."""
    try:
        r = _request(f'{_BASE}/games/lookup/v1/', {'appid': steam_appid})
        if r is None:
            return None
        r.raise_for_status()
        data = r.json()
        if data.get('found') and data.get('game'):
            return data['game']['id']
        return None
    except Exception as exc:
        logger.debug('ITAD lookup hatası appid=%s: %s', steam_appid, exc)
        return None


def fetch_itad_history(product) -> int:
    """Bir Steam oyunu için ITAD tarihsel indirim geçmişini çek ve kaydet."""
    if product.vertical != 'gaming' or not product.external_id:
        return 0

    if not _has_credentials():
        logger.warning('ITAD token yok — flask itad-auth çalıştırın.')
        return 0

    itad_id = lookup_itad_id(str(product.external_id))
    if not itad_id:
        logger.debug('ITAD ID bulunamadı: "%s" (appid=%s)', product.name, product.external_id)
        return 0

    try:
        r = _request(f'{_BASE}/games/history/v2/', {'id': itad_id})
        if r is None:
            return 0
        r.raise_for_status()
        entries = r.json()
    except Exception as exc:
        logger.debug('ITAD history hatası "%s": %s', product.name, exc)
        return 0

    if not isinstance(entries, list):
        logger.debug('ITAD history beklenmeyen format: %s', type(entries))
        return 0

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

    if not _has_credentials():
        logger.warning('ITAD token yok — flask itad-auth çalıştırın.')
        return {'total': 0, 'updated': 0, 'error': 'no_token'}

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
