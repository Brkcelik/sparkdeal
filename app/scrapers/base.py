"""Base scraper — tüm scraper'ların ortak arayüzü ve yardımcı metodları."""
import time
import logging
from abc import ABC, abstractmethod

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/125.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


class BaseScraper(ABC):
    """Her scraper bu sınıftan türetilir."""

    # Alt sınıflar kendi varsayılanlarını geçersiz kılabilir
    DEFAULT_DELAY = 2

    def __init__(self, source):
        self.source = source
        self.delay = getattr(source, 'crawl_delay_seconds', self.DEFAULT_DELAY)

    def make_session(self) -> requests.Session:
        return _make_session()

    def warm_session(self, session: requests.Session, base_url: str) -> None:
        """Ana sayfayı ziyaret ederek session cookie al."""
        try:
            session.get(base_url, timeout=10)
            time.sleep(1)
        except Exception:
            pass

    @abstractmethod
    def scrape(self, target) -> list[dict]:
        """
        Verilen tarama hedefini tara ve ürün listesi döndür.
        Her sözlük şu alanları içermelidir:
          name, current_price, old_price, discount_percent,
          product_url, image_url, brand, category,
          stock_status, external_id, vertical, platform, region, edition
        """
        raise NotImplementedError

    # ── Yardımcılar ─────────────────────────────────────────────────────────

    def normalize_price(self, raw: str) -> float | None:
        """'1.299,90 TL' veya '1,299.90' → float."""
        if not raw:
            return None
        cleaned = (
            raw.replace('TL', '')
               .replace('₺', '')
               .replace('\xa0', '')
               .replace(' ', '')
               .strip()
        )
        # Türkçe format: nokta=binlik ayırıcı, virgül=ondalık
        if ',' in cleaned and '.' in cleaned:
            # "1.299,90" → 1299.90
            cleaned = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned and '.' not in cleaned:
            # "1299,90" → 1299.90
            cleaned = cleaned.replace(',', '.')
        elif '.' in cleaned and ',' not in cleaned:
            # "2.399" — son noktadan sonra tam 3 rakam varsa binlik ayırıcıdır
            after_dot = cleaned.rsplit('.', 1)[-1]
            if len(after_dot) == 3 and after_dot.isdigit():
                cleaned = cleaned.replace('.', '')  # "2.399" → "2399"
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None

    def calc_discount(self, old: float | None, current: float | None) -> float | None:
        if old and current and old > current:
            return round((1 - current / old) * 100, 1)
        return None
